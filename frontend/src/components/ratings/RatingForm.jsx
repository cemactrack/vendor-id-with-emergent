import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { 
  Star,
  StarHalf,
  Package,
  MessageSquare,
  Clock,
  DollarSign,
  Shield,
  FileText,
  CheckCircle,
  AlertTriangle,
  Camera,
  ThumbsUp
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';

const RATING_CATEGORIES = [
  {
    key: 'product_service_quality',
    label: 'Product/Service Quality',
    description: 'Accuracy, durability, effectiveness, presentation',
    icon: Package,
    color: 'text-blue-600'
  },
  {
    key: 'customer_service', 
    label: 'Customer Service',
    description: 'Responsiveness, professionalism, issue resolution',
    icon: MessageSquare,
    color: 'text-green-600'
  },
  {
    key: 'delivery_timeliness',
    label: 'Delivery & Timeliness',
    description: 'On-time delivery, tracking, handling of delays',
    icon: Clock,
    color: 'text-orange-600'
  },
  {
    key: 'pricing_transparency',
    label: 'Pricing & Transparency', 
    description: 'Fair pricing, no hidden charges, clear billing',
    icon: DollarSign,
    color: 'text-purple-600'
  },
  {
    key: 'trust_reliability',
    label: 'Trust & Reliability',
    description: 'Honesty, consistency, positive transaction history',
    icon: Shield,
    color: 'text-emerald-600'
  },
  {
    key: 'escrow_dispute_handling',
    label: 'Escrow & Dispute Handling',
    description: 'Smooth escrow transactions, dispute cooperation',
    icon: FileText,
    color: 'text-indigo-600'
  },
  {
    key: 'compliance_documentation',
    label: 'Compliance & Documentation',
    description: 'Valid documents, policy adherence, ethical practices',
    icon: CheckCircle,
    color: 'text-teal-600'
  }
];

const StarRating = ({ rating, onRatingChange, size = 'w-6 h-6' }) => {
  const [hoverRating, setHoverRating] = useState(0);

  return (
    <div className="flex items-center space-x-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className="focus:outline-none"
          onMouseEnter={() => setHoverRating(star)}
          onMouseLeave={() => setHoverRating(0)}
          onClick={() => onRatingChange(star)}
        >
          <Star
            className={`${size} ${
              star <= (hoverRating || rating)
                ? 'text-yellow-400 fill-current'
                : 'text-gray-300'
            } transition-colors duration-150`}
          />
        </button>
      ))}
      <span className="ml-2 text-sm text-gray-600 font-medium">
        {rating > 0 ? `${rating}/5` : 'Not rated'}
      </span>
    </div>
  );
};

const RatingForm = ({ order, vendor, onSubmitSuccess, onCancel }) => {
  const [ratings, setRatings] = useState({
    product_service_quality: 0,
    customer_service: 0,
    delivery_timeliness: 0,
    pricing_transparency: 0,
    trust_reliability: 0,
    escrow_dispute_handling: 0,
    compliance_documentation: 0
  });
  
  const [reviewData, setReviewData] = useState({
    title: '',
    comment: '',
    wouldRecommend: true,
    photos: []
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const updateRating = (category, value) => {
    setRatings(prev => ({
      ...prev,
      [category]: value
    }));
  };

  const calculateOverallRating = () => {
    const values = Object.values(ratings).filter(r => r > 0);
    if (values.length === 0) return 0;
    return (values.reduce((sum, r) => sum + r, 0) / values.length).toFixed(1);
  };

  const getCompletionPercentage = () => {
    const completedRatings = Object.values(ratings).filter(r => r > 0).length;
    return Math.round((completedRatings / RATING_CATEGORIES.length) * 100);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validate ratings
      const incompleteCategories = RATING_CATEGORIES.filter(
        cat => ratings[cat.key] === 0
      );

      if (incompleteCategories.length > 0) {
        throw new Error(`Please rate all categories. Missing: ${incompleteCategories.map(c => c.label).join(', ')}`);
      }

      // Prepare rating data
      const ratingData = {
        order_id: order.order_id,
        vendor_id: order.vendor_id,
        ratings: ratings,
        review_title: reviewData.title.trim() || null,
        review_comment: reviewData.comment.trim() || null,
        would_recommend: reviewData.wouldRecommend,
        photos: reviewData.photos
      };

      // Submit rating
      const result = await vendorEcosystemAPI.submitRating(ratingData);
      
      setSuccess('Rating submitted successfully! Thank you for your feedback.');
      
      if (onSubmitSuccess) {
        setTimeout(() => {
          onSubmitSuccess(result);
        }, 2000);
      }
      
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to submit rating';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount, currency) => {
    const symbols = {
      USD: '$', NGN: '₦', GHS: '₵', KES: 'KSh', 
      ZAR: 'R', GBP: '£', EUR: '€', CAD: 'C$'
    };
    return `${symbols[currency] || currency} ${amount?.toFixed(2) || '0.00'}`;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <Star className="w-6 h-6 text-yellow-400 mr-2" />
              Rate Your Experience
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-yellow-600">
                {calculateOverallRating()}/5
              </div>
              <div className="text-sm text-gray-600">
                {getCompletionPercentage()}% Complete
              </div>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Order Details</h3>
                <p className="text-sm text-gray-600">Order ID: {order.order_id}</p>
                <p className="text-sm text-gray-600">
                  Amount: {formatCurrency(order.total_amount, order.currency)}
                </p>
                <p className="text-sm text-gray-600">
                  Completed: {new Date(order.completed_at).toLocaleDateString()}
                </p>
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Vendor</h3>
                <p className="text-sm text-gray-600">{vendor?.business_name}</p>
                <p className="text-sm text-gray-600">{vendor?.category}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">{success}</AlertDescription>
          </Alert>
        )}

        {/* Rating Categories */}
        <Card>
          <CardHeader>
            <CardTitle>Rate Each Category</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {RATING_CATEGORIES.map((category) => {
              const IconComponent = category.icon;
              return (
                <div key={category.key} className="border-b border-gray-200 last:border-b-0 pb-6 last:pb-0">
                  <div className="flex items-start space-x-4">
                    <div className={`p-2 rounded-lg bg-gray-50 ${category.color}`}>
                      <IconComponent className="w-5 h-5" />
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-medium text-gray-900">{category.label}</h3>
                          <p className="text-sm text-gray-600">{category.description}</p>
                        </div>
                        
                        <div className="text-right">
                          {ratings[category.key] > 0 && (
                            <Badge 
                              variant={ratings[category.key] >= 4 ? 'default' : ratings[category.key] >= 3 ? 'secondary' : 'destructive'}
                              className="mb-2"
                            >
                              {ratings[category.key] >= 4 ? 'Excellent' : 
                               ratings[category.key] >= 3 ? 'Good' : 
                               ratings[category.key] >= 2 ? 'Fair' : 'Poor'}
                            </Badge>
                          )}
                        </div>
                      </div>
                      
                      <StarRating 
                        rating={ratings[category.key]}
                        onRatingChange={(value) => updateRating(category.key, value)}
                        size="w-7 h-7"
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Written Review */}
        <Card>
          <CardHeader>
            <CardTitle>Written Review (Optional)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="review_title">Review Title</Label>
              <Input
                id="review_title"
                value={reviewData.title}
                onChange={(e) => setReviewData(prev => ({...prev, title: e.target.value}))}
                placeholder="Summarize your experience in a few words"
                maxLength={100}
              />
              <p className="text-xs text-gray-500">{reviewData.title.length}/100 characters</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="review_comment">Detailed Review</Label>
              <Textarea
                id="review_comment"
                value={reviewData.comment}
                onChange={(e) => setReviewData(prev => ({...prev, comment: e.target.value}))}
                placeholder="Share details about your experience to help other customers..."
                rows={4}
                maxLength={1000}
              />
              <p className="text-xs text-gray-500">{reviewData.comment.length}/1000 characters</p>
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="would_recommend"
                checked={reviewData.wouldRecommend}
                onChange={(e) => setReviewData(prev => ({...prev, wouldRecommend: e.target.checked}))}
                className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
              />
              <label htmlFor="would_recommend" className="flex items-center text-sm text-gray-700">
                <ThumbsUp className="w-4 h-4 mr-2 text-emerald-600" />
                I would recommend this vendor to others
              </label>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start">
                <Camera className="w-5 h-5 text-blue-600 mt-0.5 mr-3" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">Add Photos (Coming Soon)</p>
                  <p className="text-xs">You'll be able to upload photos to support your review</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-between">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
          
          <Button
            type="submit"
            disabled={loading || getCompletionPercentage() < 100}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Submitting Rating...
              </>
            ) : (
              <>
                <Star className="w-4 h-4 mr-2" />
                Submit Rating
              </>
            )}
          </Button>
        </div>

        {getCompletionPercentage() < 100 && (
          <div className="text-center text-sm text-gray-600">
            Please rate all categories to submit your review
          </div>
        )}
      </form>
    </div>
  );
};

export default RatingForm;