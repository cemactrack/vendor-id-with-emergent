import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Shield, 
  CheckCircle,
  AlertTriangle,
  Clock,
  Building2,
  MapPin,
  Globe,
  Star,
  QrCode,
  ArrowLeft,
  Flag,
  Calendar,
  Users
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';

const PublicVendorVerification = () => {
  const { vendorId } = useParams();
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (vendorId) {
      loadVerificationData();
    }
  }, [vendorId]);

  const loadVerificationData = async () => {
    try {
      setLoading(true);
      const data = await vendorEcosystemAPI.verifyVendorPublic(vendorId);
      setVerification(data);
    } catch (error) {
      console.error('Failed to load verification:', error);
      setError('Vendor not found or verification failed');
    } finally {
      setLoading(false);
    }
  };

  const getVerificationStatusConfig = (status) => {
    switch (status) {
      case 'verified':
        return {
          icon: <CheckCircle className="w-6 h-6" />,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          label: 'Verified',
          description: 'This vendor has been fully verified and meets all security requirements.'
        };
      case 'pending':
        return {
          icon: <Clock className="w-6 h-6" />,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          label: 'Pending Verification',
          description: 'Verification is in progress. Please check back later.'
        };
      case 'under_review':
        return {
          icon: <Clock className="w-6 h-6" />,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          label: 'Under Review',
          description: 'Documents are being reviewed by our verification team.'
        };
      default:
        return {
          icon: <AlertTriangle className="w-6 h-6" />,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          label: 'Not Verified',
          description: 'This vendor has not completed the verification process.'
        };
    }
  };

  const getTrustScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrustScoreDescription = (score) => {
    if (score >= 80) return 'Excellent trust rating';
    if (score >= 60) return 'Good trust rating';
    if (score >= 40) return 'Fair trust rating';
    return 'Low trust rating';
  };

  const getCountryFromVendorId = (vendorId) => {
    const countryCode = vendorId?.split('-')[1];
    const countries = {
      'NG': 'Nigeria',
      'CM': 'Cameroon', 
      'GH': 'Ghana',
      'KE': 'Kenya',
      'ZA': 'South Africa',
      'US': 'United States',
      'GB': 'United Kingdom',
      'CA': 'Canada'
    };
    return countries[countryCode] || 'Unknown';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying vendor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Vendor Not Found</h2>
              <p className="text-gray-600 mb-6">{error}</p>
              <Link to="/search">
                <Button>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Search
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!verification) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="text-center">
              <Building2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">No Data Available</h2>
              <p className="text-gray-600 mb-6">Unable to load verification data</p>
              <Link to="/search">
                <Button>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Search
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const statusConfig = getVerificationStatusConfig(verification.verification_status);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center space-x-4">
            <Link to="/search">
              <Button variant="outline" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Search
              </Button>
            </Link>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <QrCode className="w-4 h-4" />
              <span>Vendor Verification</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Main Verification Card */}
        <Card className="shadow-lg mb-8">
          <CardContent className="pt-8">
            {/* Verification Status Banner */}
            <div className={`${statusConfig.bgColor} ${statusConfig.borderColor} border rounded-lg p-6 mb-8`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className={statusConfig.color}>
                    {statusConfig.icon}
                  </div>
                  <div>
                    <h2 className={`text-xl font-bold ${statusConfig.color}`}>
                      {statusConfig.label}
                    </h2>
                    <p className="text-gray-700">
                      {statusConfig.description}
                    </p>
                  </div>
                </div>
                <Badge className={`${statusConfig.color} ${statusConfig.bgColor} border-0 text-sm px-3 py-1`}>
                  Level {verification.verification_level}
                </Badge>
              </div>
            </div>

            {/* Vendor Information */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Main Info */}
              <div className="lg:col-span-2 space-y-6">
                <div>
                  <div className="flex items-start space-x-4 mb-6">
                    <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center text-white text-2xl font-bold">
                      {verification.business_name?.charAt(0)?.toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        {verification.business_name}
                      </h1>
                      <div className="flex items-center space-x-4 text-gray-600">
                        <div className="flex items-center">
                          <Building2 className="w-4 h-4 mr-1" />
                          <span className="capitalize">
                            {verification.categories?.[0]?.replace('_', ' ') || 'Business'}
                          </span>
                        </div>
                        <div className="flex items-center">
                          <MapPin className="w-4 h-4 mr-1" />
                          <span>{getCountryFromVendorId(verification.vendor_id)}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">Vendor ID</h3>
                    <div className="flex items-center justify-between">
                      <code className="text-lg font-mono text-emerald-600 bg-white px-3 py-2 rounded border">
                        {verification.vendor_id}
                      </code>
                      <Button size="sm" variant="outline">
                        <QrCode className="w-4 h-4 mr-2" />
                        QR Code
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Business Address */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Business Location</h3>
                  <div className="flex items-start">
                    <MapPin className="w-5 h-5 text-gray-400 mr-2 mt-0.5" />
                    <p className="text-gray-700">{verification.location}</p>
                  </div>
                </div>

                {/* Verification Timeline */}
                {verification.verified_since && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Verification History</h3>
                    <div className="flex items-center space-x-2 text-gray-600">
                      <Calendar className="w-4 h-4" />
                      <span>
                        Verified on {new Date(verification.verified_since).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Trust Score Panel */}
              <div className="lg:col-span-1">
                <Card className="bg-gradient-to-br from-gray-50 to-gray-100">
                  <CardContent className="pt-6">
                    <div className="text-center mb-6">
                      <div className={`text-5xl font-bold ${getTrustScoreColor(verification.trust_score)} mb-2`}>
                        {Math.round(verification.trust_score)}
                      </div>
                      <div className="text-lg font-semibold text-gray-900 mb-1">Trust Score</div>
                      <div className="text-sm text-gray-600">
                        {getTrustScoreDescription(verification.trust_score)}
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Verification Level</span>
                        <div className="flex items-center">
                          {[...Array(5)].map((_, index) => (
                            <Star 
                              key={index}
                              className={`w-4 h-4 ${
                                index < verification.verification_level 
                                  ? 'text-yellow-400 fill-current' 
                                  : 'text-gray-300'
                              }`}
                            />
                          ))}
                        </div>
                      </div>

                      <div className="border-t pt-4">
                        <p className="text-xs text-gray-600 leading-relaxed">
                          Trust scores are calculated based on verification completeness, 
                          business documentation, and community feedback.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Report Issues */}
                <Card className="mt-4 border-red-200">
                  <CardContent className="pt-4">
                    <div className="text-center">
                      <Flag className="w-6 h-6 text-red-500 mx-auto mb-2" />
                      <h4 className="font-semibold text-gray-900 mb-2">Report Issues</h4>
                      <p className="text-sm text-gray-600 mb-3">
                        Found something suspicious or fraudulent?
                      </p>
                      <Button variant="outline" size="sm" className="text-red-600 border-red-200 hover:bg-red-50">
                        Report Fraud
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Additional Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Security Features */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="w-5 h-5 mr-2 text-emerald-600" />
                Security Features
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Identity Verification</span>
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Business Registration</span>
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Address Verification</span>
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Tax ID Validation</span>
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* QR Code Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <QrCode className="w-5 h-5 mr-2 text-blue-600" />
                Verification QR Code
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <div className="w-24 h-24 bg-gray-200 rounded-lg mx-auto mb-4 flex items-center justify-center">
                  <QrCode className="w-12 h-12 text-gray-400" />
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  Scan to verify this vendor's authenticity
                </p>
                <p className="text-xs text-gray-500">
                  QR Code URL: {verification.qr_verification_url}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer Actions */}
        <div className="text-center bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Verification Complete
          </h3>
          <p className="text-gray-600 mb-4">
            This verification was performed by the Vendor ID Trust Ecosystem
          </p>
          <div className="flex justify-center space-x-4">
            <Link to="/search">
              <Button variant="outline">
                Search More Vendors
              </Button>
            </Link>
            <Button>
              Contact Vendor
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PublicVendorVerification;