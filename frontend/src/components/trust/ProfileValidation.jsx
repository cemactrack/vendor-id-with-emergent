import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  CheckCircle, 
  AlertCircle, 
  Shield, 
  Phone,
  MapPin,
  Building,
  Camera,
  Award,
  Clock,
  TrendingUp,
  Loader2
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';

const ProfileValidation = () => {
  const [validationResult, setValidationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('validation');
  
  // Form states for enhancements
  const [addressData, setAddressData] = useState({
    address: '',
    city: '',
    state: '',
    country: 'Nigeria',
    postal_code: ''
  });
  
  const [phoneData, setPhoneData] = useState({
    phone_number: '',
    country_code: '+234',
    verification_method: 'sms'
  });

  useEffect(() => {
    validateProfile();
  }, []);

  const validateProfile = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/trust/profile/validate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('vendor_ecosystem_token')}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      
      if (data.success) {
        setValidationResult(data.validation);
      } else {
        setError('Failed to validate profile');
      }
    } catch (err) {
      console.error('Profile validation error:', err);
      setError('Failed to validate profile');
    } finally {
      setLoading(false);
    }
  };

  const verifyAddress = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/trust/address/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('vendor_ecosystem_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(addressData)
      });

      const data = await response.json();
      
      if (data.success) {
        if (data.verification.is_verified) {
          alert('Address verified successfully!');
          validateProfile(); // Refresh validation
        } else {
          setError('Address could not be verified');
        }
      } else {
        setError('Address verification failed');
      }
    } catch (err) {
      console.error('Address verification error:', err);
      setError('Address verification failed');
    } finally {
      setLoading(false);
    }
  };

  const verifyPhone = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/trust/phone/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('vendor_ecosystem_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(phoneData)
      });

      const data = await response.json();
      
      if (data.success) {
        if (data.verification.is_verified) {
          alert('Phone verified successfully!');
          validateProfile(); // Refresh validation
        } else {
          alert(`Verification code sent via ${data.verification.verification_method}`);
        }
      } else {
        setError('Phone verification failed');
      }
    } catch (err) {
      console.error('Phone verification error:', err);
      setError('Phone verification failed');
    } finally {
      setLoading(false);
    }
  };

  const getCompletionColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCompletionStatus = (score) => {
    if (score >= 90) return 'Comprehensive';
    if (score >= 75) return 'Complete';
    if (score >= 60) return 'Basic';
    return 'Incomplete';
  };

  const renderValidationOverview = () => (
    <div className="space-y-6">
      {validationResult && (
        <>
          {/* Completion Score */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Profile Completion Score
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">
                  {validationResult.completion_score.toFixed(1)}%
                </span>
                <Badge variant={validationResult.completion_score >= 75 ? "default" : "secondary"}>
                  {getCompletionStatus(validationResult.completion_score)}
                </Badge>
              </div>
              <Progress value={validationResult.completion_score} className="w-full" />
              <p className="text-sm text-gray-600">
                A higher completion score improves your visibility and trustworthiness
              </p>
            </CardContent>
          </Card>

          {/* Trust Score */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Trust Score
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-blue-600">
                  {validationResult.trust_score.toFixed(1)}/100
                </span>
                <Badge variant={validationResult.trust_score >= 75 ? "default" : "secondary"}>
                  {validationResult.trust_score >= 75 ? "High Trust" : "Building Trust"}
                </Badge>
              </div>
              <Progress value={validationResult.trust_score} className="w-full" />
              <p className="text-sm text-gray-600">
                Trust score is based on verifications, completeness, and activity
              </p>
            </CardContent>
          </Card>

          {/* Missing Fields */}
          {validationResult.missing_mandatory_fields.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-orange-500" />
                  Missing Required Fields
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {validationResult.missing_mandatory_fields.map((field, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-orange-500" />
                      <span className="text-sm">{field.replace('_', ' ')}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recommendations */}
          {validationResult.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {validationResult.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm">{recommendation}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );

  const renderAddressVerification = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MapPin className="w-5 h-5" />
          Address Verification
        </CardTitle>
        <CardDescription>
          Verify your business address to increase trust and visibility
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="address">Street Address</Label>
            <Input
              id="address"
              value={addressData.address}
              onChange={(e) => setAddressData({...addressData, address: e.target.value})}
              placeholder="123 Business Street"
            />
          </div>
          <div>
            <Label htmlFor="city">City</Label>
            <Input
              id="city"
              value={addressData.city}
              onChange={(e) => setAddressData({...addressData, city: e.target.value})}
              placeholder="Lagos"
            />
          </div>
          <div>
            <Label htmlFor="state">State</Label>
            <Input
              id="state"
              value={addressData.state}
              onChange={(e) => setAddressData({...addressData, state: e.target.value})}
              placeholder="Lagos State"
            />
          </div>
          <div>
            <Label htmlFor="country">Country</Label>
            <Input
              id="country"
              value={addressData.country}
              onChange={(e) => setAddressData({...addressData, country: e.target.value})}
              placeholder="Nigeria"
            />
          </div>
        </div>
        
        <Button 
          onClick={verifyAddress} 
          disabled={loading || !addressData.address || !addressData.city}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Verifying...
            </>
          ) : (
            <>
              <MapPin className="mr-2 h-4 w-4" />
              Verify Address
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );

  const renderPhoneVerification = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Phone className="w-5 h-5" />
          Phone Verification
        </CardTitle>
        <CardDescription>
          Verify your phone number to enable direct customer contact
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor="country_code">Country Code</Label>
            <select
              id="country_code"
              value={phoneData.country_code}
              onChange={(e) => setPhoneData({...phoneData, country_code: e.target.value})}
              className="w-full p-2 border rounded"
            >
              <option value="+234">+234 (Nigeria)</option>
              <option value="+1">+1 (US)</option>
              <option value="+44">+44 (UK)</option>
              <option value="+27">+27 (South Africa)</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="phone_number">Phone Number</Label>
            <Input
              id="phone_number"
              value={phoneData.phone_number}
              onChange={(e) => setPhoneData({...phoneData, phone_number: e.target.value})}
              placeholder="8012345678"
            />
          </div>
        </div>
        
        <div>
          <Label htmlFor="verification_method">Verification Method</Label>
          <select
            id="verification_method"
            value={phoneData.verification_method}
            onChange={(e) => setPhoneData({...phoneData, verification_method: e.target.value})}
            className="w-full p-2 border rounded"
          >
            <option value="sms">SMS</option>
            <option value="call">Phone Call</option>
            <option value="whatsapp">WhatsApp</option>
          </select>
        </div>
        
        <Button 
          onClick={verifyPhone} 
          disabled={loading || !phoneData.phone_number}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Verifying...
            </>
          ) : (
            <>
              <Phone className="mr-2 h-4 w-4" />
              Verify Phone
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Profile Validation & Trust</h1>
        <p className="text-gray-600">Enhance your profile completeness and build customer trust</p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="validation">
            <Shield className="w-4 h-4 mr-2" />
            Validation
          </TabsTrigger>
          <TabsTrigger value="address">
            <MapPin className="w-4 h-4 mr-2" />
            Address
          </TabsTrigger>
          <TabsTrigger value="phone">
            <Phone className="w-4 h-4 mr-2" />
            Phone
          </TabsTrigger>
        </TabsList>

        <TabsContent value="validation">
          {loading && !validationResult ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mr-2" />
              <span>Validating profile...</span>
            </div>
          ) : (
            renderValidationOverview()
          )}
        </TabsContent>

        <TabsContent value="address">
          {renderAddressVerification()}
        </TabsContent>

        <TabsContent value="phone">
          {renderPhoneVerification()}
        </TabsContent>
      </Tabs>

      <div className="mt-8">
        <Button 
          onClick={validateProfile} 
          disabled={loading}
          variant="outline"
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Refreshing...
            </>
          ) : (
            <>
              <Shield className="mr-2 h-4 w-4" />
              Refresh Validation
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default ProfileValidation;