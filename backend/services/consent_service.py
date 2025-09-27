import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.consent_models import *
import logging
import json

logger = logging.getLogger(__name__)

class ConsentService:
    """GDPR-compliant consent management service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.consents_collection = db.consent_records
        self.withdrawals_collection = db.consent_withdrawals
        self.deletions_collection = db.data_deletions
        self.audits_collection = db.biometric_audits
        self.reports_collection = db.compliance_reports
        
    async def request_consent(self, vendor_id: str, consent_types: List[ConsentType], 
                            ip_address: str, user_agent: str) -> List[ConsentRecord]:
        """Request consent for specific data processing activities"""
        try:
            consent_records = []
            current_time = datetime.now(timezone.utc)
            
            for consent_type in consent_types:
                # Get current consent text and version
                consent_text, version = await self._get_consent_text(consent_type)
                
                # Calculate retention period
                retention_until = self._calculate_retention_date(consent_type)
                
                consent_record = ConsentRecord(
                    vendor_id=vendor_id,
                    consent_type=consent_type,
                    consent_text=consent_text,
                    consent_version=version,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    retention_until=retention_until
                )
                
                # Store consent record
                consent_dict = consent_record.dict()
                await self.consents_collection.insert_one(consent_dict)
                consent_dict.pop("_id", None)
                
                consent_records.append(ConsentRecord(**consent_dict))
            
            logger.info(f"Consent requested for vendor {vendor_id}: {len(consent_records)} types")
            return consent_records
            
        except Exception as e:
            logger.error(f"Failed to request consent: {e}")
            raise
    
    async def grant_consent(self, consent_ids: List[str], vendor_id: str, 
                          ip_address: str, user_agent: str) -> bool:
        """Grant consent for specific processing activities"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Update consent records
            result = await self.consents_collection.update_many(
                {
                    "consent_id": {"$in": consent_ids},
                    "vendor_id": vendor_id,
                    "status": ConsentStatus.PENDING.value
                },
                {
                    "$set": {
                        "status": ConsentStatus.GRANTED.value,
                        "granted_at": current_time,
                        "updated_at": current_time
                    }
                }
            )
            
            # Audit consent granting
            for consent_id in consent_ids:
                await self._audit_consent_action(
                    vendor_id, consent_id, "consent_granted", 
                    ip_address, user_agent
                )
            
            logger.info(f"Consent granted for vendor {vendor_id}: {result.modified_count} consents")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to grant consent: {e}")
            raise
    
    async def withdraw_consent(self, withdrawal_request: ConsentWithdrawalRequest) -> str:
        """Process consent withdrawal and initiate data deletion if requested"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Create withdrawal record
            withdrawal_dict = withdrawal_request.dict()
            await self.withdrawals_collection.insert_one(withdrawal_dict)
            
            # Update consent records
            await self.consents_collection.update_many(
                {
                    "consent_id": {"$in": withdrawal_request.consent_ids},
                    "vendor_id": withdrawal_request.vendor_id
                },
                {
                    "$set": {
                        "status": ConsentStatus.WITHDRAWN.value,
                        "withdrawn_at": current_time,
                        "updated_at": current_time
                    }
                }
            )
            
            # If data deletion requested, create deletion request
            if withdrawal_request.data_deletion_requested:
                deletion_request = DataDeletionRequest(
                    vendor_id=withdrawal_request.vendor_id,
                    request_type="consent_withdrawal",
                    reason=withdrawal_request.withdrawal_reason or "Consent withdrawn",
                    verification_method="authenticated_session",
                    deadline=withdrawal_request.deletion_deadline
                )
                
                deletion_dict = deletion_request.dict()
                await self.deletions_collection.insert_one(deletion_dict)
                
                # Schedule automatic deletion if required
                await self._schedule_data_deletion(deletion_request.deletion_id)
            
            # Audit withdrawal
            await self._audit_consent_action(
                withdrawal_request.vendor_id, 
                ",".join(withdrawal_request.consent_ids),
                "consent_withdrawn",
                withdrawal_request.ip_address,
                withdrawal_request.user_agent
            )
            
            logger.info(f"Consent withdrawn for vendor {withdrawal_request.vendor_id}")
            return withdrawal_request.withdrawal_id
            
        except Exception as e:
            logger.error(f"Failed to withdraw consent: {e}")
            raise
    
    async def check_consent_status(self, vendor_id: str, consent_type: ConsentType) -> Optional[ConsentRecord]:
        """Check current consent status for a specific type"""
        try:
            consent_data = await self.consents_collection.find_one(
                {
                    "vendor_id": vendor_id,
                    "consent_type": consent_type.value,
                    "status": {"$in": [ConsentStatus.GRANTED.value, ConsentStatus.PENDING.value]}
                },
                sort=[("created_at", -1)]
            )
            
            if consent_data:
                consent_data.pop("_id", None)
                return ConsentRecord(**consent_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check consent status: {e}")
            return None
    
    async def process_data_deletion(self, deletion_id: str, admin_user_id: str) -> bool:
        """Process approved data deletion request"""
        try:
            # Get deletion request
            deletion_data = await self.deletions_collection.find_one({"deletion_id": deletion_id})
            if not deletion_data:
                return False
            
            deletion_request = DataDeletionRequest(**deletion_data)
            current_time = datetime.now(timezone.utc)
            
            # Update status to processing
            await self.deletions_collection.update_one(
                {"deletion_id": deletion_id},
                {
                    "$set": {
                        "status": "processing",
                        "processed_by": admin_user_id,
                        "updated_at": current_time
                    }
                }
            )
            
            # Delete data based on categories
            deletion_evidence = {}
            
            if "biometric_templates" in deletion_request.data_categories:
                # Delete biometric templates
                result = await self.db.biometric_templates.delete_many(
                    {"vendor_id": deletion_request.vendor_id}
                )
                deletion_evidence["biometric_templates"] = f"{result.deleted_count} templates deleted"
                
                # Delete biometric sessions
                result = await self.db.biometric_sessions.delete_many(
                    {"vendor_id": deletion_request.vendor_id}
                )
                deletion_evidence["biometric_sessions"] = f"{result.deleted_count} sessions deleted"
            
            if "documents" in deletion_request.data_categories:
                # Delete uploaded documents
                result = await self.db.documents.delete_many(
                    {"vendor_id": deletion_request.vendor_id}
                )
                deletion_evidence["documents"] = f"{result.deleted_count} documents deleted"
            
            if "profile_data" in deletion_request.data_categories:
                # Anonymize profile data instead of full deletion for audit trail
                await self.db.vendor_profiles.update_one(
                    {"vendor_id": deletion_request.vendor_id},
                    {
                        "$set": {
                            "business_name": "DELETED",
                            "business_description": "DELETED",
                            "business_address": "DELETED",
                            "anonymized_at": current_time
                        }
                    }
                )
                deletion_evidence["profile_data"] = "Profile anonymized"
            
            # Mark deletion as completed
            await self.deletions_collection.update_one(
                {"deletion_id": deletion_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": current_time,
                        "completion_evidence": json.dumps(deletion_evidence)
                    }
                }
            )
            
            # Audit deletion
            await self._audit_consent_action(
                deletion_request.vendor_id,
                deletion_id,
                "data_deleted",
                "system",
                "deletion_service"
            )
            
            logger.info(f"Data deletion completed for vendor {deletion_request.vendor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process data deletion: {e}")
            return False
    
    async def generate_compliance_report(self, vendor_id: str) -> ComplianceReport:
        """Generate GDPR compliance report for a vendor"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Get consent summary
            consent_summary = {}
            for consent_type in ConsentType:
                count = await self.consents_collection.count_documents({
                    "vendor_id": vendor_id,
                    "consent_type": consent_type.value,
                    "status": ConsentStatus.GRANTED.value
                })
                consent_summary[consent_type.value] = count
            
            # Check retention compliance
            retention_compliance = {}
            overdue_consents = await self.consents_collection.count_documents({
                "vendor_id": vendor_id,
                "retention_until": {"$lt": current_time},
                "status": {"$ne": ConsentStatus.WITHDRAWN.value}
            })
            retention_compliance["retention_overdue"] = overdue_consents == 0
            
            # Calculate compliance score
            score = 100.0
            issues = []
            
            if overdue_consents > 0:
                score -= 30
                issues.append({
                    "type": "retention_violation",
                    "severity": "high",
                    "description": f"{overdue_consents} consents past retention period"
                })
            
            # Check for missing consents
            required_consents = [ConsentType.BIOMETRIC_PROCESSING, ConsentType.DATA_PROCESSING]
            for consent_type in required_consents:
                if consent_summary.get(consent_type.value, 0) == 0:
                    score -= 20
                    issues.append({
                        "type": "missing_consent",
                        "severity": "medium",
                        "description": f"Missing {consent_type.value} consent"
                    })
            
            # Generate recommendations
            recommendations = []
            if overdue_consents > 0:
                recommendations.append("Delete or anonymize data past retention period")
            if any(consent_summary.get(ct.value, 0) == 0 for ct in required_consents):
                recommendations.append("Obtain required consents for data processing")
            
            report = ComplianceReport(
                vendor_id=vendor_id,
                compliance_score=max(0, score),
                issues_found=issues,
                recommendations=recommendations,
                consent_summary=consent_summary,
                retention_compliance=retention_compliance,
                generated_by="system",
                valid_until=current_time + timedelta(days=30)
            )
            
            # Store report
            report_dict = report.dict()
            await self.reports_collection.insert_one(report_dict)
            report_dict.pop("_id", None)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            raise
    
    async def _get_consent_text(self, consent_type: ConsentType) -> tuple[str, str]:
        """Get current consent text and version for a consent type"""
        consent_texts = {
            ConsentType.BIOMETRIC_PROCESSING: (
                "I consent to the processing of my biometric data (facial features, fingerprints) "
                "for identity verification purposes. This includes capturing, analyzing, and storing "
                "encrypted biometric templates. Data will be retained for 7 years for compliance purposes.",
                "v2.1"
            ),
            ConsentType.BIOMETRIC_STORAGE: (
                "I consent to the secure storage of my encrypted biometric templates in compliance "
                "with data protection regulations. Templates will be stored with enterprise-grade "
                "encryption and access controls.",
                "v2.1"
            ),
            ConsentType.BIOMETRIC_MATCHING: (
                "I consent to the use of my biometric data for identity matching and duplicate "
                "detection to prevent fraud and ensure platform integrity.",
                "v2.1"
            ),
            ConsentType.DATA_PROCESSING: (
                "I consent to the processing of my personal and business data for vendor "
                "verification, trust scoring, and platform services.",
                "v2.1"
            )
        }
        
        return consent_texts.get(consent_type, ("Generic consent text", "v1.0"))
    
    def _calculate_retention_date(self, consent_type: ConsentType) -> datetime:
        """Calculate data retention deadline based on consent type"""
        current_time = datetime.now(timezone.utc)
        
        # GDPR compliance: 7 years for biometric data, 3 years for other data
        if consent_type in [ConsentType.BIOMETRIC_PROCESSING, ConsentType.BIOMETRIC_STORAGE]:
            return current_time + timedelta(days=7*365)  # 7 years
        else:
            return current_time + timedelta(days=3*365)  # 3 years
    
    async def _audit_consent_action(self, vendor_id: str, consent_id: str, action: str,
                                  ip_address: str, user_agent: str):
        """Audit consent-related actions"""
        try:
            audit_record = BiometricDataAudit(
                vendor_id=vendor_id,
                data_type="consent_record",
                operation=action,
                operator_id=vendor_id,
                operator_role="vendor",
                purpose="consent_management",
                legal_basis="consent",
                data_location="primary_server",
                encryption_status="encrypted",
                consent_reference=consent_id,
                metadata={
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
            )
            
            audit_dict = audit_record.dict()
            await self.audits_collection.insert_one(audit_dict)
            
        except Exception as e:
            logger.error(f"Failed to audit consent action: {e}")
    
    async def _schedule_data_deletion(self, deletion_id: str):
        """Schedule automatic data deletion (placeholder for task queue)"""
        # In production, this would integrate with a task queue like Celery
        logger.info(f"Data deletion scheduled for request {deletion_id}")
        pass