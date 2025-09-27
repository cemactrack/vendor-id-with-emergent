import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Star,
  Award,
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  MessageSquare,
  ThumbsUp,
  Calendar,
  Shield,
  AlertCircle,
  BarChart3
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';

const VendorRatingDisplay = ({ vendorId, showAnalytics = false }) => {
  const [ratings, setRatings] = useState([]);
  const [score, setScore] = useState(null);
  const [summary, setSummary] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadRatingData();
  }, [vendorId]);

  const loadRatingData = async () => {
    try {
      setLoading(true);
      
      // Load rating summary
      const summaryData = await vendorEcosystemAPI.getVendorRatingSummary(vendorId);
      setSummary(summaryData);
      
      // Load detailed score if available
      if (summaryData.total_ratings > 0) {
        const scoreData = await vendorEcosystemAPI.getVendorScore(vendorId);
        setScore(scoreData);
        
        // Load recent ratings
        const ratingsData = await vendorEcosystemAPI.getVendorRatings(vendorId, 10, 0);
        setRatings(ratingsData.ratings);
        
        // Load analytics if requested and user has access
        if (showAnalytics) {
          try {
            const analyticsData = await vendorEcosystemAPI.getVendorRatingAnalytics(vendorId);
            setAnalytics(analyticsData);
          } catch (error) {
            // User may not have access to analytics
            console.log('Analytics not available');
          }
        }
      }
      
    } catch (error) {
      console.error('Failed to load rating data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getBadgeInfo = (badge) => {
    const badgeConfig = {
      gold_verified: {
        label: 'Gold Verified',
        color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        icon: Award,
        description: 'Consistently excellent performance'
      },
      trusted_vendor: {
        label: 'Trusted Vendor', 
        color: 'bg-blue-100 text-blue-800 border-blue-200',
        icon: Shield,
        description: 'Reliable and trustworthy'
      },
      under_review: {
        label: 'Under Review',
        color: 'bg-red-100 text-red-800 border-red-200', 
        icon: AlertCircle,
        description: 'Performance being evaluated'
      },
      new_vendor: {
        label: 'New Vendor',
        color: 'bg-gray-100 text-gray-800 border-gray-200',
        icon: Users,
        description: 'Recently joined platform'
      }
    };

    return badgeConfig[badge] || badgeConfig.new_vendor;
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'declining':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  const renderStars = (rating, size = 'w-4 h-4') => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    
    return (
      <div className="flex items-center">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            className={`${size} ${
              i < fullStars
                ? 'text-yellow-400 fill-current'
                : i === fullStars && hasHalfStar
                ? 'text-yellow-400 fill-current opacity-50'
                : 'text-gray-300'
            }`}
          />
        ))}
        <span className="ml-1 text-sm font-medium">{rating.toFixed(1)}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!summary || summary.total_ratings === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <Star className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Ratings Yet</h3>
            <p className="text-gray-600">This vendor hasn't received any ratings yet.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const badgeInfo = getBadgeInfo(summary.badge);
  const BadgeIcon = badgeInfo.icon;

  return (
    <div className="space-y-6">
      {/* Rating Overview */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <div className="text-3xl font-bold text-gray-900">
                  {summary.overall_score.toFixed(1)}
                </div>
                <div>
                  {renderStars(summary.overall_score, 'w-6 h-6')}
                  <p className="text-sm text-gray-600 mt-1">
                    Based on {summary.total_ratings} review{summary.total_ratings !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2 mb-3">
                <Badge className={badgeInfo.color}>
                  <BadgeIcon className="w-3 h-3 mr-1" />
                  {badgeInfo.label}
                </Badge>
                <div className="flex items-center">
                  {getTrendIcon(summary.recent_score_trend)}
                  <span className="text-xs text-gray-600 ml-1 capitalize">
                    {summary.recent_score_trend}
                  </span>
                </div>
              </div>
              
              <p className="text-sm text-gray-600">{badgeInfo.description}</p>
            </div>
            
            {summary.top_categories.length > 0 && (
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900 mb-1">Top Strengths</p>
                <div className="space-y-1">
                  {summary.top_categories.slice(0, 2).map((category, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {category}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Rating Data */}
      {score && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="categories">Categories</TabsTrigger>
            <TabsTrigger value="reviews">Reviews</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <Card>
              <CardHeader>
                <CardTitle>Rating Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[5, 4, 3, 2, 1].map((stars) => {
                    const percentage = score[`${stars === 1 ? 'one' : stars === 2 ? 'two' : stars === 3 ? 'three' : stars === 4 ? 'four' : 'five'}_star_percentage`] || 0;
                    return (
                      <div key={stars} className="flex items-center space-x-3">
                        <div className="flex items-center space-x-1 w-16">
                          <span className="text-sm font-medium">{stars}</span>
                          <Star className="w-3 h-3 text-yellow-400 fill-current" />
                        </div>
                        <Progress value={percentage} className="flex-1" />
                        <span className="text-sm text-gray-600 w-12 text-right">
                          {percentage.toFixed(0)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
                
                <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-emerald-600">
                      {score.recommendation_percentage.toFixed(0)}%
                    </div>
                    <p className="text-sm text-gray-600">Would Recommend</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {score.total_reviews}
                    </div>
                    <p className="text-sm text-gray-600">Written Reviews</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Categories Tab */}
          <TabsContent value="categories">
            <Card>
              <CardHeader>
                <CardTitle>Category Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {score.category_scores.map((category) => (
                    <div key={category.category} className="flex items-center justify-between py-3 border-b last:border-b-0">
                      <div>
                        <p className="font-medium text-gray-900 capitalize">
                          {category.category.replace(/_/g, ' ')}
                        </p>
                        <p className="text-sm text-gray-600">
                          {category.total_ratings} rating{category.total_ratings !== 1 ? 's' : ''}
                        </p>
                      </div>
                      <div className="text-right">
                        {renderStars(category.average_rating)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Reviews Tab */}
          <TabsContent value="reviews">
            <Card>
              <CardHeader>
                <CardTitle>Recent Reviews</CardTitle>
              </CardHeader>
              <CardContent>
                {ratings.length > 0 ? (
                  <div className="space-y-6">
                    {ratings.map((rating) => (
                      <div key={rating.rating_id} className="border-b pb-6 last:border-b-0">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center space-x-3">
                            {renderStars(rating.overall_rating)}
                            {rating.verified_purchase && (
                              <Badge variant="outline" className="text-xs">
                                <Shield className="w-3 h-3 mr-1" />
                                Verified Purchase
                              </Badge>
                            )}
                          </div>
                          <div className="text-right text-sm text-gray-600">
                            <div className="flex items-center">
                              <Calendar className="w-4 h-4 mr-1" />
                              {new Date(rating.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        
                        {rating.review_title && (
                          <h4 className="font-medium text-gray-900 mb-2">
                            {rating.review_title}
                          </h4>
                        )}
                        
                        {rating.review_comment && (
                          <p className="text-gray-700 mb-3">{rating.review_comment}</p>
                        )}
                        
                        <div className="flex items-center justify-between">
                          {rating.would_recommend && (
                            <div className="flex items-center text-sm text-emerald-600">
                              <ThumbsUp className="w-4 h-4 mr-1" />
                              Recommends this vendor
                            </div>
                          )}
                          
                          {rating.helpful_votes > 0 && (
                            <div className="text-sm text-gray-600">
                              {rating.helpful_votes} found this helpful
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Written Reviews</h3>
                    <p className="text-gray-600">Ratings available but no detailed reviews yet.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Analytics Tab (if available) */}
      {analytics && showAnalytics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Rating Analytics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {analytics.trending_direction === 'up' ? '+' : analytics.trending_direction === 'down' ? '-' : ''}
                  {analytics.average_rating.toFixed(1)}
                </div>
                <p className="text-sm text-gray-600">30-Day Average</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {analytics.total_ratings}
                </div>
                <p className="text-sm text-gray-600">Recent Ratings</p>
              </div>
              <div className="text-center">
                <div className={`text-2xl font-bold ${
                  analytics.trending_direction === 'up' ? 'text-green-600' : 
                  analytics.trending_direction === 'down' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {analytics.trending_direction.toUpperCase()}
                </div>
                <p className="text-sm text-gray-600">Trend</p>
              </div>
            </div>
            
            {analytics.improvement_areas.length > 0 && (
              <div className="mt-6 pt-4 border-t">
                <h4 className="font-medium text-gray-900 mb-2">Areas for Improvement</h4>
                <div className="flex flex-wrap gap-2">
                  {analytics.improvement_areas.map((area, index) => (
                    <Badge key={index} variant="outline" className="text-orange-600 border-orange-200">
                      {area}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default VendorRatingDisplay;