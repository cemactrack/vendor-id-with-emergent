import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.fraud_detection_models import *
from models.biometric_models import BiometricType
import numpy as np
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class FraudDetectionService:
    """Advanced fraud detection and duplicate prevention service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.duplicates_collection = db.duplicate_detections
        self.biometric_similarity_collection = db.biometric_similarities
        self.document_similarity_collection = db.document_similarities  
        self.behavioral_patterns_collection = db.behavioral_patterns
        self.network_analysis_collection = db.network_analysis
        self.investigations_collection = db.fraud_investigations
        self.synthetic_identity_collection = db.synthetic_identity_indicators
        self.review_manipulation_collection = db.review_manipulation_detections
        self.device_fingerprints_collection = db.device_fingerprints_fraud
        self.fraud_alerts_collection = db.fraud_alerts
        self.fraud_statistics_collection = db.fraud_statistics
        
    async def check_duplicate_registration(self, vendor_id: str, biometric_templates: List[str],
                                         documents: List[Dict[str, Any]], 
                                         device_info: Dict[str, Any]) -> DuplicateDetectionResult:
        """Comprehensive duplicate detection check"""
        try:
            duplicate_vendor_ids = []
            evidence = {}
            risk_score = RiskScore(overall_score=0.0)
            max_confidence = 0.0
            detection_methods = []
            
            # 1. Biometric duplicate detection
            biometric_duplicates, bio_confidence = await self._check_biometric_duplicates(
                vendor_id, biometric_templates
            )
            if biometric_duplicates:
                duplicate_vendor_ids.extend(biometric_duplicates)
                evidence["biometric_matches"] = biometric_duplicates
                risk_score.biometric_risk = bio_confidence * 100
                max_confidence = max(max_confidence, bio_confidence)
                detection_methods.append("biometric")
            
            # 2. Document duplicate detection
            document_duplicates, doc_confidence = await self._check_document_duplicates(
                vendor_id, documents
            )
            if document_duplicates:
                duplicate_vendor_ids.extend(document_duplicates)
                evidence["document_matches"] = document_duplicates
                risk_score.document_risk = doc_confidence * 100
                max_confidence = max(max_confidence, doc_confidence)
                detection_methods.append("document")
            
            # 3. Device fingerprint analysis
            device_duplicates, device_confidence = await self._check_device_duplicates(
                vendor_id, device_info
            )
            if device_duplicates:
                duplicate_vendor_ids.extend(device_duplicates)
                evidence["device_matches"] = device_duplicates
                risk_score.device_risk = device_confidence * 100
                max_confidence = max(max_confidence, device_confidence)
                detection_methods.append("device")
            
            # 4. Network analysis
            network_duplicates, network_confidence = await self._check_network_patterns(
                vendor_id, device_info
            )
            if network_duplicates:
                duplicate_vendor_ids.extend(network_duplicates)
                evidence["network_matches"] = network_duplicates
                risk_score.network_risk = network_confidence * 100
                max_confidence = max(max_confidence, network_confidence)
                detection_methods.append("network")
            
            # Remove duplicates and self-references
            duplicate_vendor_ids = list(set(duplicate_vendor_ids))
            if vendor_id in duplicate_vendor_ids:
                duplicate_vendor_ids.remove(vendor_id)
            
            # Calculate overall risk score
            risk_score.overall_score = self._calculate_overall_risk(risk_score)
            
            # Determine fraud type
            fraud_type = self._determine_fraud_type(detection_methods, evidence)
            
            # Create detection result
            detection_result = DuplicateDetectionResult(
                primary_vendor_id=vendor_id,
                duplicate_vendor_ids=duplicate_vendor_ids,
                fraud_type=fraud_type,
                confidence_score=max_confidence,
                evidence=evidence,
                risk_score=risk_score,
                detection_method=", ".join(detection_methods),
                status=DetectionStatus.SUSPECTED if duplicate_vendor_ids else DetectionStatus.RESOLVED
            )
            
            # Store detection result
            if duplicate_vendor_ids or risk_score.overall_score > 50:
                detection_dict = detection_result.dict()
                await self.duplicates_collection.insert_one(detection_dict)
                detection_dict.pop("_id", None)
                
                # Create fraud alert if high risk
                if risk_score.overall_score > 75:
                    await self._create_fraud_alert(detection_result)
            
            logger.info(f"Duplicate check completed for vendor {vendor_id}: "
                       f"{len(duplicate_vendor_ids)} duplicates found")
            
            return detection_result
            
        except Exception as e:
            logger.error(f"Failed to check duplicates: {e}")
            raise
    
    async def analyze_synthetic_identity(self, vendor_id: str, 
                                       profile_data: Dict[str, Any],
                                       registration_metadata: Dict[str, Any]) -> SyntheticIdentityIndicators:
        """Detect synthetic identity fraud"""
        try:
            indicators = {
                "recently_created_identity": False,
                "limited_digital_footprint": False, 
                "inconsistent_personal_data": False,
                "new_phone_number": False,
                "new_email_domain": False,
                "rapid_account_setup": False,
                "minimal_document_history": False
            }
            
            # Check email domain age
            email = profile_data.get("email", "")
            if email:
                domain = email.split("@")[-1]
                if await self._is_new_email_domain(domain):
                    indicators["new_email_domain"] = True
            
            # Check phone number patterns
            phone = profile_data.get("phone", "")
            if phone and await self._is_new_phone_number(phone):
                indicators["new_phone_number"] = True
            
            # Check registration speed (completed in suspiciously short time)
            registration_duration = registration_metadata.get("completion_time_minutes", 0)
            if registration_duration < 5:  # Less than 5 minutes
                indicators["rapid_account_setup"] = True
            
            # Check data consistency
            if await self._check_data_inconsistencies(profile_data):
                indicators["inconsistent_personal_data"] = True
            
            # Check document history
            document_count = await self.db.documents.count_documents({"vendor_id": vendor_id})
            if document_count < 2:  # Minimal documentation
                indicators["minimal_document_history"] = True
            
            # Calculate confidence score
            positive_indicators = sum(1 for v in indicators.values() if v)
            confidence_score = min(positive_indicators / len(indicators), 1.0)
            
            synthetic_indicators = SyntheticIdentityIndicators(
                vendor_id=vendor_id,
                indicators=indicators,
                confidence_score=confidence_score
            )
            
            # Store indicators
            indicators_dict = synthetic_indicators.dict()
            await self.synthetic_identity_collection.insert_one(indicators_dict)
            indicators_dict.pop("_id", None)
            
            # Create alert if high confidence
            if confidence_score > 0.6:
                await self._create_synthetic_identity_alert(synthetic_indicators)
            
            return synthetic_indicators
            
        except Exception as e:
            logger.error(f"Failed to analyze synthetic identity: {e}")
            raise
    
    async def detect_review_manipulation(self, vendor_id: str) -> ReviewManipulationDetection:
        """Detect review manipulation and fake reviews"""
        try:
            # Get all reviews for vendor
            reviews = await self.db.vendor_ratings.find(
                {"vendor_id": vendor_id}
            ).to_list(length=None)
            
            if len(reviews) < 5:  # Not enough data
                return ReviewManipulationDetection(
                    vendor_id=vendor_id,
                    manipulation_type="insufficient_data",
                    confidence_score=0.0
                )
            
            suspicious_patterns = []
            
            # 1. Temporal clustering analysis
            temporal_clustering = await self._analyze_review_timing(reviews)
            if temporal_clustering["is_suspicious"]:
                suspicious_patterns.append(temporal_clustering)
            
            # 2. Reviewer network analysis
            reviewer_network = await self._analyze_reviewer_network(reviews)
            if reviewer_network["network_detected"]:
                suspicious_patterns.append(reviewer_network)
            
            # 3. Linguistic similarity analysis
            linguistic_similarity = await self._analyze_review_text_similarity(reviews)
            if linguistic_similarity["similarity_score"] > 0.7:
                suspicious_patterns.append(linguistic_similarity)
            
            # 4. Velocity anomaly detection
            velocity_anomaly = await self._analyze_review_velocity(vendor_id, reviews)
            if velocity_anomaly["is_anomalous"]:
                suspicious_patterns.append(velocity_anomaly)
            
            # Calculate confidence score
            confidence_score = min(len(suspicious_patterns) / 4.0, 1.0)
            
            # Determine manipulation type
            manipulation_type = self._determine_manipulation_type(suspicious_patterns)
            
            detection = ReviewManipulationDetection(
                vendor_id=vendor_id,
                manipulation_type=manipulation_type,
                suspicious_patterns=suspicious_patterns,
                affected_reviews=[r["rating_id"] for r in reviews],
                confidence_score=confidence_score,
                temporal_clustering=temporal_clustering.get("is_suspicious", False),
                reviewer_network_detected=reviewer_network.get("network_detected", False),
                linguistic_similarity=linguistic_similarity.get("similarity_score", 0.0),
                velocity_anomaly=velocity_anomaly.get("is_anomalous", False)
            )
            
            # Store detection result
            detection_dict = detection.dict()
            await self.review_manipulation_collection.insert_one(detection_dict)
            detection_dict.pop("_id", None)
            
            # Create alert if suspicious
            if confidence_score > 0.5:
                await self._create_review_manipulation_alert(detection)
            
            return detection
            
        except Exception as e:
            logger.error(f"Failed to detect review manipulation: {e}")
            raise
    
    async def _check_biometric_duplicates(self, vendor_id: str, 
                                        templates: List[str]) -> Tuple[List[str], float]:
        """Check for biometric duplicates across the platform"""
        try:
            duplicate_vendors = []
            max_similarity = 0.0
            
            # Get all existing biometric templates
            existing_templates = await self.db.biometric_templates.find({
                "vendor_id": {"$ne": vendor_id},
                "is_active": True
            }).to_list(length=None)
            
            for new_template_id in templates:
                # Get template data
                new_template = await self.db.biometric_templates.find_one({
                    "template_id": new_template_id
                })
                
                if not new_template:
                    continue
                
                for existing_template in existing_templates:
                    if existing_template["biometric_type"] != new_template["biometric_type"]:
                        continue
                    
                    # Calculate similarity (simplified - in production use proper algorithms)
                    similarity = await self._calculate_biometric_similarity(
                        new_template, existing_template
                    )
                    
                    if similarity > 0.85:  # High similarity threshold
                        duplicate_vendors.append(existing_template["vendor_id"])
                        max_similarity = max(max_similarity, similarity)
                        
                        # Store similarity record
                        await self._store_biometric_similarity(
                            vendor_id, existing_template["vendor_id"], 
                            similarity, new_template["biometric_type"]
                        )
            
            return list(set(duplicate_vendors)), max_similarity
            
        except Exception as e:
            logger.error(f"Failed to check biometric duplicates: {e}")
            return [], 0.0
    
    async def _check_document_duplicates(self, vendor_id: str, 
                                       documents: List[Dict[str, Any]]) -> Tuple[List[str], float]:
        """Check for document duplicates (same documents used by different vendors)"""
        try:
            duplicate_vendors = []
            max_similarity = 0.0
            
            for doc in documents:
                # Calculate document hash/fingerprint
                doc_hash = await self._calculate_document_hash(doc)
                
                # Check for exact matches
                existing_docs = await self.db.documents.find({
                    "vendor_id": {"$ne": vendor_id},
                    "document_hash": doc_hash
                }).to_list(length=None)
                
                for existing_doc in existing_docs:
                    duplicate_vendors.append(existing_doc["vendor_id"])
                    max_similarity = 1.0  # Exact match
                
                # Check for similar documents (OCR text similarity)
                if max_similarity < 0.9:  # If no exact match found
                    similar_docs = await self._find_similar_documents(vendor_id, doc)
                    for similar_doc, similarity in similar_docs:
                        if similarity > 0.8:
                            duplicate_vendors.append(similar_doc["vendor_id"])
                            max_similarity = max(max_similarity, similarity)
            
            return list(set(duplicate_vendors)), max_similarity
            
        except Exception as e:
            logger.error(f"Failed to check document duplicates: {e}")
            return [], 0.0
    
    async def _check_device_duplicates(self, vendor_id: str, 
                                     device_info: Dict[str, Any]) -> Tuple[List[str], float]:
        """Check for device fingerprint duplicates"""
        try:
            device_hash = self._create_device_fingerprint(device_info)
            
            # Check for exact device fingerprint matches
            existing_devices = await self.db.device_fingerprints.find({
                "vendor_id": {"$ne": vendor_id},
                "device_hash": device_hash
            }).to_list(length=None)
            
            duplicate_vendors = [dev["vendor_id"] for dev in existing_devices]
            confidence = 1.0 if duplicate_vendors else 0.0
            
            return duplicate_vendors, confidence
            
        except Exception as e:
            logger.error(f"Failed to check device duplicates: {e}")
            return [], 0.0
    
    async def _check_network_patterns(self, vendor_id: str, 
                                    device_info: Dict[str, Any]) -> Tuple[List[str], float]:
        """Check for suspicious network patterns (same IP, timing correlations)"""
        try:
            duplicate_vendors = []
            ip_address = device_info.get("ip_address", "")
            
            if not ip_address:
                return [], 0.0
            
            # Check for same IP registrations in short time period
            recent_registrations = await self.db.vendor_profiles.find({
                "vendor_id": {"$ne": vendor_id},
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=24)},
                "registration_ip": ip_address
            }).to_list(length=None)
            
            if len(recent_registrations) > 2:  # More than 2 registrations from same IP
                duplicate_vendors = [reg["vendor_id"] for reg in recent_registrations]
                confidence = min(len(recent_registrations) / 5.0, 1.0)
                return duplicate_vendors, confidence
            
            return [], 0.0
            
        except Exception as e:
            logger.error(f"Failed to check network patterns: {e}")
            return [], 0.0
    
    async def _calculate_biometric_similarity(self, template1: Dict[str, Any], 
                                            template2: Dict[str, Any]) -> float:
        """Calculate similarity between biometric templates"""
        try:
            # Simplified similarity calculation
            # In production, use proper biometric matching algorithms
            
            # Compare quality scores
            quality_diff = abs(template1.get("quality_score", 0) - template2.get("quality_score", 0))
            quality_similarity = 1.0 - quality_diff
            
            # Compare confidence levels
            confidence_diff = abs(template1.get("confidence_level", 0) - template2.get("confidence_level", 0))
            confidence_similarity = 1.0 - confidence_diff
            
            # Weighted average
            similarity = (quality_similarity * 0.6 + confidence_similarity * 0.4)
            
            return max(0.0, min(1.0, similarity))
            
        except Exception:
            return 0.0
    
    async def _store_biometric_similarity(self, vendor_id_1: str, vendor_id_2: str,
                                        similarity_score: float, biometric_type: str):
        """Store biometric similarity record"""
        try:
            similarity_record = BiometricSimilarity(
                vendor_id_1=vendor_id_1,
                vendor_id_2=vendor_id_2,
                similarity_score=similarity_score,
                biometric_type=biometric_type,
                quality_score_1=0.8,  # Placeholder
                quality_score_2=0.8,  # Placeholder
                processing_algorithm="simplified_comparison",
                threshold_used=0.85,
                match_confirmed=similarity_score > 0.85
            )
            
            similarity_dict = similarity_record.dict()
            await self.biometric_similarity_collection.insert_one(similarity_dict)
            
        except Exception as e:
            logger.error(f"Failed to store biometric similarity: {e}")
    
    async def _calculate_document_hash(self, document: Dict[str, Any]) -> str:
        """Calculate hash for document identification"""
        try:
            # Create hash from document content/metadata
            content = json.dumps(document, sort_keys=True)
            return hashlib.sha256(content.encode()).hexdigest()
        except Exception:
            return ""
    
    async def _find_similar_documents(self, vendor_id: str, 
                                    document: Dict[str, Any]) -> List[Tuple[Dict[str, Any], float]]:
        """Find documents with similar content"""
        # Simplified implementation - in production use advanced text similarity
        return []
    
    def _create_device_fingerprint(self, device_info: Dict[str, Any]) -> str:
        """Create unique device fingerprint"""
        fingerprint_data = {
            "user_agent": device_info.get("user_agent", ""),
            "screen_resolution": device_info.get("screen_resolution", ""),
            "timezone": device_info.get("timezone", ""),
            "language": device_info.get("language", ""),
            "platform": device_info.get("platform", "")
        }
        
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    def _calculate_overall_risk(self, risk_score: RiskScore) -> float:
        """Calculate overall risk score from individual components"""
        weights = {
            "biometric_risk": 0.3,
            "document_risk": 0.25,
            "behavioral_risk": 0.15,
            "network_risk": 0.15,
            "device_risk": 0.1,
            "temporal_risk": 0.05
        }
        
        overall = (
            risk_score.biometric_risk * weights["biometric_risk"] +
            risk_score.document_risk * weights["document_risk"] +
            risk_score.behavioral_risk * weights["behavioral_risk"] +
            risk_score.network_risk * weights["network_risk"] +
            risk_score.device_risk * weights["device_risk"] +
            risk_score.temporal_risk * weights["temporal_risk"]
        )
        
        return min(100.0, overall)
    
    def _determine_fraud_type(self, detection_methods: List[str], 
                            evidence: Dict[str, Any]) -> FraudType:
        """Determine the type of fraud based on detection methods"""
        if "biometric" in detection_methods:
            return FraudType.DUPLICATE_REGISTRATION
        elif "document" in detection_methods:
            return FraudType.DOCUMENT_FORGERY  
        elif "device" in detection_methods and "network" in detection_methods:
            return FraudType.COLLUSION
        else:
            return FraudType.DUPLICATE_REGISTRATION
    
    async def _create_fraud_alert(self, detection_result: DuplicateDetectionResult):
        """Create high-priority fraud alert"""
        try:
            alert = FraudAlert(
                vendor_ids=[detection_result.primary_vendor_id] + detection_result.duplicate_vendor_ids,
                fraud_type=detection_result.fraud_type,
                severity="high" if detection_result.risk_score.overall_score > 85 else "medium",
                alert_title=f"Potential {detection_result.fraud_type.value} detected",
                description=f"High confidence ({detection_result.confidence_score:.2f}) fraud detection",
                evidence_summary=detection_result.evidence,
                risk_score=detection_result.risk_score,
                requires_immediate_action=detection_result.risk_score.overall_score > 90
            )
            
            alert_dict = alert.dict()
            await self.fraud_alerts_collection.insert_one(alert_dict)
            
        except Exception as e:
            logger.error(f"Failed to create fraud alert: {e}")
    
    # Additional helper methods for review manipulation detection
    async def _analyze_review_timing(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze timing patterns in reviews for clustering"""
        # Simplified implementation
        return {"is_suspicious": False, "cluster_score": 0.0}
    
    async def _analyze_reviewer_network(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze if reviewers are part of a manipulation network"""
        # Simplified implementation
        return {"network_detected": False, "network_size": 0}
    
    async def _analyze_review_text_similarity(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze similarity in review text content"""
        # Simplified implementation
        return {"similarity_score": 0.0, "similar_pairs": []}
    
    async def _analyze_review_velocity(self, vendor_id: str, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze review velocity for anomalies"""
        # Simplified implementation
        return {"is_anomalous": False, "velocity_score": 0.0}
    
    def _determine_manipulation_type(self, patterns: List[Dict[str, Any]]) -> str:
        """Determine type of review manipulation"""
        if not patterns:
            return "none_detected"
        return "fake_reviews"  # Simplified
    
    async def _create_review_manipulation_alert(self, detection: ReviewManipulationDetection):
        """Create alert for review manipulation"""
        # Implementation for creating manipulation alerts
        pass
    
    async def _create_synthetic_identity_alert(self, indicators: SyntheticIdentityIndicators):
        """Create alert for synthetic identity"""
        # Implementation for creating synthetic identity alerts
        pass
    
    async def _is_new_email_domain(self, domain: str) -> bool:
        """Check if email domain is recently created"""
        # Simplified implementation
        return False
    
    async def _is_new_phone_number(self, phone: str) -> bool:
        """Check if phone number is recently issued"""
        # Simplified implementation  
        return False
    
    async def _check_data_inconsistencies(self, profile_data: Dict[str, Any]) -> bool:
        """Check for inconsistencies in personal data"""
        # Simplified implementation
        return False