import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Shield, 
  QrCode,
  Download,
  CreditCard,
  CheckCircle,
  Star,
  Calendar,
  MapPin,
  Building2,
  Copy,
  ExternalLink,
  Truck
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useAuth } from '../../contexts/AuthContext';

const VendorIDCard = () => {
  const [vendorId, setVendorId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [showPhysicalCardForm, setShowPhysicalCardForm] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    loadVendorId();
  }, []);

  const loadVendorId = async () => {
    try {
      setLoading(true);
      const vendorIdData = await vendorEcosystemAPI.getVendorIdInfo();
      setVendorId(vendorIdData);
    } catch (error) {
      console.error('Failed to load vendor ID:', error);
      setError('Failed to load vendor ID information');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const getTrustScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrustScoreBg = (score) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getVerificationLevelStars = (level) => {
    return [...Array(5)].map((_, index) => (
      <Star 
        key={index}
        className={`w-4 h-4 ${
          index < level 
            ? 'text-yellow-400 fill-current' 
            : 'text-gray-300'
        }`}
      />
    ));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertTriangle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-800">{error}</AlertDescription>
      </Alert>
    );
  }

  if (!vendorId) {
    return (
      <Card className="text-center">
        <CardContent className="pt-6 pb-8">
          <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Vendor ID Not Assigned</h3>
          <p className="text-gray-600 mb-4">
            Your Vendor ID will be generated once all verification documents are approved.
          </p>
          <Badge variant="outline" className="text-yellow-600 border-yellow-200">
            Pending Verification
          </Badge>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Digital Vendor ID Card */}
      <Card className="overflow-hidden bg-gradient-to-br from-emerald-600 to-teal-700 text-white">
        <CardContent className="p-8">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                <Shield className="w-7 h-7 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold">VENDOR ID CARD</h2>
                <p className="text-emerald-100 text-sm">Verified • Trusted • Secure Trade</p>
              </div>
            </div>
            
            <Badge className="bg-white/20 text-white border-white/30">
              Level {vendorId.verification_level}
            </Badge>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Information */}
            <div className="lg:col-span-2 space-y-4">
              <div>
                <h3 className="text-2xl font-bold mb-1">{vendorId.business_name}</h3>
                <p className="text-emerald-100 capitalize">{vendorId.business_category?.replace('_', ' ')}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-emerald-200">Vendor ID</p>
                  <p className="font-mono font-semibold text-lg">{vendorId.vendor_id_number}</p>
                </div>
                <div>
                  <p className="text-emerald-200">Country</p>
                  <p className="font-semibold">{vendorId.country}</p>
                </div>
                <div>
                  <p className="text-emerald-200">Issued Date</p>
                  <p className="font-semibold">
                    {new Date(vendorId.issued_date).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-emerald-200">Status</p>
                  <p className="font-semibold capitalize">{vendorId.status}</p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-1">
                  <span className="text-emerald-200 text-sm">Verification Level:</span>
                  <div className="flex">{getVerificationLevelStars(vendorId.verification_level)}</div>
                </div>
                
                <div className={`px-3 py-1 rounded-full ${getTrustScoreBg(vendorId.trust_score)} ${getTrustScoreColor(vendorId.trust_score)} bg-opacity-20`}>
                  <span className="text-sm font-semibold">
                    Trust Score: {Math.round(vendorId.trust_score)}
                  </span>
                </div>
              </div>
            </div>

            {/* QR Code */}
            <div className="flex flex-col items-center justify-center">
              <div className="w-32 h-32 bg-white rounded-lg p-3 mb-3">
                {vendorId.qr_code_url ? (
                  <img 
                    src={vendorId.qr_code_url} 
                    alt="Vendor ID QR Code"
                    className="w-full h-full"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-100 rounded">
                    <QrCode className="w-16 h-16 text-gray-400" />
                  </div>
                )}
              </div>
              <p className="text-xs text-emerald-200 text-center">
                Scan to verify authenticity
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Card Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center mb-3">
              <Copy className="w-5 h-5 text-blue-600 mr-2" />
              <h4 className="font-semibold">Share Vendor ID</h4>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Copy your Vendor ID for marketplace integrations
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(vendorId.vendor_id_number)}
              className="w-full"
            >
              {copied ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-2" />
                  Copy ID
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center mb-3">
              <QrCode className="w-5 h-5 text-purple-600 mr-2" />
              <h4 className="font-semibold">Download QR Code</h4>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Get QR code for your marketing materials
            </p>
            <Button variant="outline" size="sm" className="w-full">
              <Download className="w-4 h-4 mr-2" />
              Download QR
            </Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-center mb-3">
              <CreditCard className="w-5 h-5 text-green-600 mr-2" />
              <h4 className="font-semibold">Physical Card</h4>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Order a physical Vendor ID card with chip
            </p>
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full"
              onClick={() => setShowPhysicalCardForm(true)}
            >
              <Truck className="w-4 h-4 mr-2" />
              Order Card
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Verification Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="w-5 h-5 mr-2 text-emerald-600" />
            Verification Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-3">Verified Information</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span>Business Registration Verified</span>
                </div>
                <div className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span>Tax ID Validated</span>
                </div>
                <div className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span>Owner Identity Confirmed</span>
                </div>
                <div className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span>Address Verification Complete</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-3">Public Profile</h4>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <MapPin className="w-4 h-4 text-gray-400 mr-2" />
                  <span>{vendorId.location}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                  <span>Verified since {new Date(vendorId.verified_since).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center text-sm">
                  <Building2 className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="capitalize">{vendorId.business_category?.replace('_', ' ')}</span>
                </div>
              </div>
              
              <Button variant="outline" size="sm" className="mt-4">
                <ExternalLink className="w-4 h-4 mr-2" />
                View Public Profile
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Guidelines */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <h4 className="font-semibold text-blue-900 mb-3">How to Use Your Vendor ID</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <h5 className="font-medium mb-2">Marketplace Integration</h5>
              <ul className="space-y-1">
                <li>• Add your Vendor ID to marketplace profiles</li>
                <li>• Display the verification badge on your listings</li>
                <li>• Include QR code in your marketing materials</li>
              </ul>
            </div>
            <div>
              <h5 className="font-medium mb-2">Customer Verification</h5>
              <ul className="space-y-1">
                <li>• Share QR code with potential customers</li>
                <li>• Include Vendor ID in proposals and contracts</li>
                <li>• Display physical card at trade shows</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VendorIDCard;