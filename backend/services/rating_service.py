from typing import Dict, List, Optional, Tuple, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.rating_models import *
from models.escrow_models import OrderStatus
from datetime import datetime, timedelta, timezone
import uuid
import logging
from decimal import Decimal, ROUND_HALF_UP
import statistics

logger = logging.getLogger(__name__)

class RatingService:
    """Service for managing vendor ratings and reviews"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.ratings_collection = db.vendor_ratings
        self.vendor_scores_collection = db.vendor_scores
        self.badge_history_collection = db.vendor_badge_history
        self.review_responses_collection = db.review_responses
        self.review_flags_collection = db.review_flags
        self.rating_analytics_collection = db.rating_analytics
        
        # Default rating weights
        self.rating_weights = RatingWeights()
        
        # Badge requirements
        self.badge_requirements = BadgeRequirements()
    
    # ===== RATING SUBMISSION =====
    
    async def submit_rating(self, customer_id: str, rating_data: RatingCreate) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Submit a rating for a vendor after order completion"""
        try:
            # Verify order exists and is completed
            order = await self.db.escrow_orders.find_one({
                "order_id": rating_data.order_id,
                "customer_id": customer_id,
                "status": OrderStatus.COMPLETED
            })
            
            if not order:
                return False, None, "Order not found, not completed, or unauthorized"
            
            # Check if rating already exists
            existing_rating = await self.ratings_collection.find_one({
                "order_id": rating_data.order_id,
                "customer_id": customer_id
            })
            
            if existing_rating:
                return False, None, "Rating already submitted for this order"
            
            # Calculate overall rating using weighted average
            overall_rating = self._calculate_weighted_average(rating_data.ratings)
            
            # Create rating record
            rating_id = f"RAT-{uuid.uuid4().hex[:10].upper()}"
            
            rating = VendorRating(
                rating_id=rating_id,
                order_id=rating_data.order_id,
                customer_id=customer_id,
                vendor_id=rating_data.vendor_id,
                ratings=rating_data.ratings,
                overall_rating=overall_rating,
                review_title=rating_data.review_title,
                review_comment=rating_data.review_comment,
                would_recommend=rating_data.would_recommend,
                photos=rating_data.photos,
                status=ReviewStatus.PUBLISHED,  # Auto-publish for verified purchases
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                verified_purchase=True
            )
            
            # Save rating
            rating_dict = rating.dict()
            await self.ratings_collection.insert_one(rating_dict)
            rating_dict.pop('_id', None)
            
            # Update vendor score
            vendor_score = await self._update_vendor_score(rating_data.vendor_id)
            
            logger.info(f"Rating submitted successfully: {rating_id}")
            
            return True, {
                "rating": rating_dict,
                "vendor_score": vendor_score
            }, None
            
        except Exception as e:
            logger.error(f"Failed to submit rating: {e}")
            return False, None, f"Rating submission failed: {str(e)}"
    
    def _calculate_weighted_average(self, ratings: RatingCriteria) -> float:
        """Calculate weighted average rating"""
        weights = self.rating_weights
        
        total_score = (
            ratings.product_service_quality * weights.product_service_quality +
            ratings.customer_service * weights.customer_service +
            ratings.delivery_timeliness * weights.delivery_timeliness +
            ratings.pricing_transparency * weights.pricing_transparency +
            ratings.trust_reliability * weights.trust_reliability +
            ratings.escrow_dispute_handling * weights.escrow_dispute_handling +
            ratings.compliance_documentation * weights.compliance_documentation
        )
        
        return round(total_score, 2)
    
    # ===== VENDOR SCORE MANAGEMENT =====
    
    async def _update_vendor_score(self, vendor_id: str) -> Dict[str, Any]:
        """Update vendor's overall score and badge"""
        try:
            # Get all ratings for vendor
            cursor = self.ratings_collection.find({
                "vendor_id": vendor_id,
                "status": ReviewStatus.PUBLISHED
            })
            ratings = await cursor.to_list(length=None)
            
            if not ratings:
                # No ratings yet - assign new vendor badge
                return await self._create_initial_vendor_score(vendor_id)
            
            # Calculate category scores
            category_scores = self._calculate_category_scores(ratings)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(category_scores)
            
            # Calculate additional metrics
            total_ratings = len(ratings)
            total_reviews = len([r for r in ratings if r.get('review_comment')])
            recommendation_percentage = (len([r for r in ratings if r.get('would_recommend', True)]) / total_ratings) * 100
            
            # Calculate rating distribution
            rating_distribution = self._calculate_rating_distribution(ratings)
            
            # Calculate historical scores
            historical_scores = await self._calculate_historical_scores(vendor_id)
            
            # Determine badge
            badge, badge_earned_at = await self._determine_vendor_badge(vendor_id, overall_score, total_ratings, ratings)
            
            # Create score details
            vendor_score = VendorScoreDetails(
                vendor_id=vendor_id,
                overall_score=overall_score,
                category_scores=category_scores,
                total_ratings=total_ratings,
                total_reviews=total_reviews,
                recommendation_percentage=recommendation_percentage,
                badge=badge,
                badge_earned_at=badge_earned_at,
                last_updated=datetime.now(timezone.utc),
                score_30_days=historical_scores.get('30_days'),
                score_90_days=historical_scores.get('90_days'),
                score_1_year=historical_scores.get('1_year'),
                five_star_percentage=rating_distribution.get(5, 0),
                four_star_percentage=rating_distribution.get(4, 0),
                three_star_percentage=rating_distribution.get(3, 0),
                two_star_percentage=rating_distribution.get(2, 0),
                one_star_percentage=rating_distribution.get(1, 0)
            )
            
            # Update or create vendor score record
            score_dict = vendor_score.dict()
            await self.vendor_scores_collection.replace_one(
                {"vendor_id": vendor_id},
                score_dict,
                upsert=True
            )
            
            # Update badge history if badge changed
            await self._update_badge_history(vendor_id, badge, overall_score, total_ratings)
            
            score_dict.pop('_id', None)
            return score_dict
            
        except Exception as e:
            logger.error(f"Failed to update vendor score for {vendor_id}: {e}")
            raise
    
    async def _create_initial_vendor_score(self, vendor_id: str) -> Dict[str, Any]:
        """Create initial score record for new vendor"""
        vendor_score = VendorScoreDetails(
            vendor_id=vendor_id,
            overall_score=0.0,
            category_scores=[],
            total_ratings=0,
            total_reviews=0,
            recommendation_percentage=0.0,
            badge=VendorBadge.NEW_VENDOR,
            badge_earned_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            five_star_percentage=0.0,
            four_star_percentage=0.0,
            three_star_percentage=0.0,
            two_star_percentage=0.0,
            one_star_percentage=0.0
        )
        
        score_dict = vendor_score.dict()
        await self.vendor_scores_collection.replace_one(
            {"vendor_id": vendor_id},
            score_dict,
            upsert=True
        )
        
        score_dict.pop('_id', None)
        return score_dict
    
    def _calculate_category_scores(self, ratings: List[Dict]) -> List[CategoryScore]:
        """Calculate average scores for each category"""
        category_scores = []
        
        for category in RatingCategory:
            category_ratings = []
            for rating in ratings:
                if 'ratings' in rating and category.value in rating['ratings']:
                    category_ratings.append(rating['ratings'][category.value])
            
            if category_ratings:
                avg_rating = statistics.mean(category_ratings)
                weight = getattr(self.rating_weights, category.value, 0.0)
                
                category_scores.append(CategoryScore(
                    category=category,
                    average_rating=round(avg_rating, 2),
                    total_ratings=len(category_ratings),
                    weight=weight
                ))
        
        return category_scores
    
    def _calculate_overall_score(self, category_scores: List[CategoryScore]) -> float:
        """Calculate weighted overall score"""
        if not category_scores:
            return 0.0
        
        weighted_sum = sum(score.average_rating * score.weight for score in category_scores)
        return round(weighted_sum, 2)
    
    def _calculate_rating_distribution(self, ratings: List[Dict]) -> Dict[int, float]:
        """Calculate percentage distribution of ratings"""
        total_ratings = len(ratings)
        if total_ratings == 0:
            return {}
        
        distribution = {}
        for i in range(1, 6):  # 1 to 5 stars
            count = len([r for r in ratings if round(r.get('overall_rating', 0)) == i])
            distribution[i] = round((count / total_ratings) * 100, 1)
        
        return distribution
    
    async def _calculate_historical_scores(self, vendor_id: str) -> Dict[str, Optional[float]]:
        """Calculate historical scores for different time periods"""
        now = datetime.now(timezone.utc)
        
        periods = {
            '30_days': now - timedelta(days=30),
            '90_days': now - timedelta(days=90),
            '1_year': now - timedelta(days=365)
        }
        
        historical_scores = {}
        
        for period_name, start_date in periods.items():
            cursor = self.ratings_collection.find({
                "vendor_id": vendor_id,
                "status": ReviewStatus.PUBLISHED,
                "created_at": {"$gte": start_date}
            })
            period_ratings = await cursor.to_list(length=None)
            
            if period_ratings:
                avg_score = statistics.mean([r['overall_rating'] for r in period_ratings])
                historical_scores[period_name] = round(avg_score, 2)
            else:
                historical_scores[period_name] = None
        
        return historical_scores
    
    async def _determine_vendor_badge(self, vendor_id: str, overall_score: float, 
                                    total_ratings: int, ratings: List[Dict]) -> Tuple[VendorBadge, Optional[datetime]]:
        """Determine appropriate badge for vendor"""
        
        # Get current badge
        current_score_record = await self.vendor_scores_collection.find_one({"vendor_id": vendor_id})
        current_badge = VendorBadge.NEW_VENDOR
        if current_score_record:
            current_badge = VendorBadge(current_score_record.get('badge', 'new_vendor'))
        
        # Check for suspension or under review conditions
        if overall_score < 3.0 and total_ratings >= 5:
            return VendorBadge.UNDER_REVIEW, datetime.now(timezone.utc)
        
        # Calculate dispute ratio
        dispute_count = await self._get_vendor_dispute_count(vendor_id)
        dispute_ratio = dispute_count / max(total_ratings, 1)
        
        # Check compliance status
        compliance_ok = await self._check_vendor_compliance(vendor_id)
        
        # Determine badge based on requirements
        gold_req = self.badge_requirements.gold_verified
        trusted_req = self.badge_requirements.trusted_vendor
        
        # Gold Verified Vendor
        if (overall_score >= gold_req["min_score"] and 
            total_ratings >= gold_req["min_ratings"] and
            dispute_ratio <= gold_req["max_disputes_ratio"] and
            compliance_ok and
            await self._check_score_consistency(vendor_id, gold_req["min_score"], gold_req["consistency_period_days"])):
            
            new_badge_time = datetime.now(timezone.utc) if current_badge != VendorBadge.GOLD_VERIFIED else None
            return VendorBadge.GOLD_VERIFIED, new_badge_time
        
        # Trusted Vendor
        elif (overall_score >= trusted_req["min_score"] and 
              total_ratings >= trusted_req["min_ratings"] and
              dispute_ratio <= trusted_req["max_disputes_ratio"] and
              compliance_ok and
              await self._check_score_consistency(vendor_id, trusted_req["min_score"], trusted_req["consistency_period_days"])):
            
            new_badge_time = datetime.now(timezone.utc) if current_badge not in [VendorBadge.TRUSTED_VENDOR, VendorBadge.GOLD_VERIFIED] else None
            return VendorBadge.TRUSTED_VENDOR, new_badge_time
        
        # New Vendor (less than minimum ratings)
        elif total_ratings < 10:
            return VendorBadge.NEW_VENDOR, None
        
        # Default to no special badge
        else:
            return current_badge, None
    
    async def _get_vendor_dispute_count(self, vendor_id: str) -> int:
        """Get number of disputes for vendor"""
        dispute_count = await self.db.disputes.count_documents({
            "vendor_id": vendor_id,
            "status": {"$in": ["open", "resolved"]}
        })
        return dispute_count
    
    async def _check_vendor_compliance(self, vendor_id: str) -> bool:
        """Check if vendor meets compliance requirements"""
        # Check if vendor has valid documents and verification
        vendor = await self.db.vendor_profiles.find_one({"vendor_id": vendor_id})
        if not vendor:
            return False
        
        # Check verification status
        if vendor.get('verification_status') != 'verified':
            return False
        
        # Check for recent policy violations (this would be tracked separately)
        violations_count = await self.db.vendor_violations.count_documents({
            "vendor_id": vendor_id,
            "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=90)}
        })
        
        return violations_count < 2
    
    async def _check_score_consistency(self, vendor_id: str, min_score: float, days: int) -> bool:
        """Check if vendor maintains consistent score over period"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        cursor = self.ratings_collection.find({
            "vendor_id": vendor_id,
            "status": ReviewStatus.PUBLISHED,
            "created_at": {"$gte": start_date}
        })
        recent_ratings = await cursor.to_list(length=None)
        
        if not recent_ratings:
            return False
        
        # Calculate average for the period
        avg_score = statistics.mean([r['overall_rating'] for r in recent_ratings])
        return avg_score >= min_score
    
    async def _update_badge_history(self, vendor_id: str, new_badge: VendorBadge, 
                                   score: float, total_ratings: int):
        """Update badge history when badge changes"""
        try:
            # Get current badge from history
            current_badge_record = await self.badge_history_collection.find_one({
                "vendor_id": vendor_id,
                "lost_at": None
            })
            
            # If badge is changing, close current record and create new one
            if current_badge_record and current_badge_record['badge'] != new_badge.value:
                # Close current badge
                await self.badge_history_collection.update_one(
                    {"badge_history_id": current_badge_record["badge_history_id"]},
                    {
                        "$set": {
                            "lost_at": datetime.now(timezone.utc),
                            "reason": f"Score changed to {score}, upgraded to {new_badge.value}"
                        }
                    }
                )
                
                # Create new badge record
                await self._create_badge_record(vendor_id, new_badge, score, total_ratings)
            
            elif not current_badge_record:
                # First badge assignment
                await self._create_badge_record(vendor_id, new_badge, score, total_ratings)
                
        except Exception as e:
            logger.error(f"Failed to update badge history: {e}")
    
    async def _create_badge_record(self, vendor_id: str, badge: VendorBadge, 
                                  score: float, total_ratings: int):
        """Create new badge history record"""
        badge_record = VendorBadgeHistory(
            badge_history_id=str(uuid.uuid4()),
            vendor_id=vendor_id,
            badge=badge,
            earned_at=datetime.now(timezone.utc),
            reason=f"Earned based on score {score} with {total_ratings} ratings",
            score_at_time=score,
            total_ratings_at_time=total_ratings
        )
        
        await self.badge_history_collection.insert_one(badge_record.dict())
    
    # ===== QUERY METHODS =====
    
    async def get_vendor_ratings(self, vendor_id: str, limit: int = 50, 
                               offset: int = 0) -> Tuple[List[Dict], int]:
        """Get ratings for a vendor with pagination"""
        try:
            # Get total count
            total = await self.ratings_collection.count_documents({
                "vendor_id": vendor_id,
                "status": ReviewStatus.PUBLISHED
            })
            
            # Get ratings with pagination
            cursor = self.ratings_collection.find({
                "vendor_id": vendor_id,
                "status": ReviewStatus.PUBLISHED
            }).sort("created_at", -1).skip(offset).limit(limit)
            
            ratings = await cursor.to_list(length=None)
            
            # Remove MongoDB ObjectIds
            for rating in ratings:
                rating.pop('_id', None)
            
            return ratings, total
            
        except Exception as e:
            logger.error(f"Failed to get vendor ratings: {e}")
            return [], 0
    
    async def get_vendor_score(self, vendor_id: str) -> Optional[Dict]:
        """Get vendor's current score and badge"""
        try:
            score = await self.vendor_scores_collection.find_one({"vendor_id": vendor_id})
            if score:
                score.pop('_id', None)
            return score
        except Exception as e:
            logger.error(f"Failed to get vendor score: {e}")
            return None
    
    async def get_vendor_rating_summary(self, vendor_id: str) -> Optional[VendorRatingSummary]:
        """Get summary of vendor ratings for display"""
        try:
            score_record = await self.get_vendor_score(vendor_id)
            if not score_record:
                return None
            
            # Determine trend
            trend = "stable"
            if score_record.get('score_30_days') and score_record.get('overall_score'):
                if score_record['score_30_days'] > score_record['overall_score']:
                    trend = "improving"
                elif score_record['score_30_days'] < score_record['overall_score']:
                    trend = "declining"
            
            # Get top performing categories
            category_scores = score_record.get('category_scores', [])
            top_categories = sorted(category_scores, key=lambda x: x['average_rating'], reverse=True)[:3]
            top_category_names = [cat['category'].replace('_', ' ').title() for cat in top_categories]
            
            return VendorRatingSummary(
                vendor_id=vendor_id,
                overall_score=score_record['overall_score'],
                total_ratings=score_record['total_ratings'],
                badge=VendorBadge(score_record['badge']),
                recent_score_trend=trend,
                top_categories=top_category_names
            )
            
        except Exception as e:
            logger.error(f"Failed to get vendor rating summary: {e}")
            return None
    
    async def get_customer_rating_eligibility(self, customer_id: str, vendor_id: str) -> List[Dict]:
        """Get orders eligible for rating by customer"""
        try:
            # Find completed orders without ratings
            pipeline = [
                {
                    "$match": {
                        "customer_id": customer_id,
                        "vendor_id": vendor_id,
                        "status": OrderStatus.COMPLETED
                    }
                },
                {
                    "$lookup": {
                        "from": "vendor_ratings",
                        "localField": "order_id",
                        "foreignField": "order_id",
                        "as": "rating"
                    }
                },
                {
                    "$match": {
                        "rating": {"$size": 0}  # No existing rating
                    }
                },
                {
                    "$project": {
                        "order_id": 1,
                        "vendor_id": 1,
                        "completed_at": 1,
                        "total_amount": 1,
                        "currency": 1,
                        "items": 1
                    }
                }
            ]
            
            cursor = self.db.escrow_orders.aggregate(pipeline)
            eligible_orders = await cursor.to_list(length=None)
            
            # Remove MongoDB ObjectIds
            for order in eligible_orders:
                order.pop('_id', None)
            
            return eligible_orders
            
        except Exception as e:
            logger.error(f"Failed to get rating eligibility: {e}")
            return []
    
    # ===== ANALYTICS =====
    
    async def get_rating_analytics(self, vendor_id: str, period: str = "30d") -> Optional[RatingAnalytics]:
        """Get rating analytics for a vendor"""
        try:
            # Define period
            period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365, "all": None}
            days = period_days.get(period)
            
            query = {"vendor_id": vendor_id, "status": ReviewStatus.PUBLISHED}
            if days:
                start_date = datetime.now(timezone.utc) - timedelta(days=days)
                query["created_at"] = {"$gte": start_date}
            
            # Get ratings for period
            cursor = self.ratings_collection.find(query)
            ratings = await cursor.to_list(length=None)
            
            if not ratings:
                return None
            
            # Calculate analytics
            total_ratings = len(ratings)
            avg_rating = statistics.mean([r['overall_rating'] for r in ratings])
            
            # Rating distribution
            rating_dist = {}
            for i in range(1, 6):
                count = len([r for r in ratings if round(r['overall_rating']) == i])
                rating_dist[i] = count
            
            # Category averages
            category_avgs = {}
            for category in RatingCategory:
                category_ratings = []
                for rating in ratings:
                    if 'ratings' in rating and category.value in rating['ratings']:
                        category_ratings.append(rating['ratings'][category.value])
                if category_ratings:
                    category_avgs[category.value] = statistics.mean(category_ratings)
            
            # Trending direction (compare with previous period)
            trending_direction = "stable"
            if days and days > 7:
                prev_start = start_date - timedelta(days=days)
                prev_cursor = self.ratings_collection.find({
                    "vendor_id": vendor_id,
                    "status": ReviewStatus.PUBLISHED,
                    "created_at": {"$gte": prev_start, "$lt": start_date}
                })
                prev_ratings = await prev_cursor.to_list(length=None)
                
                if prev_ratings:
                    prev_avg = statistics.mean([r['overall_rating'] for r in prev_ratings])
                    if avg_rating > prev_avg + 0.1:
                        trending_direction = "up"
                    elif avg_rating < prev_avg - 0.1:
                        trending_direction = "down"
            
            # Improvement areas (lowest scoring categories)
            improvement_areas = sorted(
                [(cat, avg) for cat, avg in category_avgs.items()],
                key=lambda x: x[1]
            )[:3]
            improvement_areas = [cat.replace('_', ' ').title() for cat, _ in improvement_areas]
            
            return RatingAnalytics(
                period=period,
                total_ratings=total_ratings,
                average_rating=round(avg_rating, 2),
                rating_distribution=rating_dist,
                category_averages=category_avgs,
                trending_direction=trending_direction,
                improvement_areas=improvement_areas
            )
            
        except Exception as e:
            logger.error(f"Failed to get rating analytics: {e}")
            return None