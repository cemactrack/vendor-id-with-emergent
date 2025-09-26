import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Shield, 
  Building2, 
  FileText, 
  Eye,
  Plus,
  Upload,
  CheckCircle,
  Clock,
  AlertTriangle,
  TrendingUp,
  Users,
  Star,
  QrCode,
  Settings,
  LogOut,
  CreditCard
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useNavigate } from 'react-router-dom';
import VendorIDCard from '../vendor/VendorIDCard';

const VendorEcosystemDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await vendorEcosystemAPI.getVendorDashboard();
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setError(error.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getVerificationStatusColor = (status) => {
    switch (status) {
      case 'verified': return 'bg-green-500';
      case 'pending': return 'bg-yellow-500';
      case 'under_review': return 'bg-blue-500';
      case 'rejected': return 'bg-red-500';
      case 'suspended': return 'bg-gray-500';
      default: return 'bg-gray-400';
    }
  };

  const getVerificationStatusIcon = (status) => {
    switch (status) {
      case 'verified': return <CheckCircle className="w-4 h-4" />;
      case 'pending': return <Clock className="w-4 h-4" />;
      case 'under_review': return <Eye className="w-4 h-4" />;
      case 'rejected': return <AlertTriangle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <Alert className="border-red-200 bg-red-50">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                {error}
              </AlertDescription>
            </Alert>
            <Button 
              onClick={loadDashboardData}
              className="w-full mt-4"
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!dashboardData?.profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle>Profile Not Found</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              You haven't created a vendor profile yet.
            </p>
            <Button 
              onClick={() => navigate('/onboarding')}
              className="w-full"
            >
              Create Profile
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { profile, analytics, active_listings = [], verification_status, trust_events = [] } = dashboardData;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Vendor Dashboard</h1>
              <p className="text-sm text-gray-600">Welcome back, {user?.full_name}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Vendor Profile Header */}
        <Card className="mb-8">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between">
              <div className="flex items-start space-x-4 mb-4 md:mb-0">
                <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center text-white text-xl font-bold">
                  {profile.business_name?.charAt(0)?.toUpperCase() || 'V'}
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{profile.business_name}</h2>
                  <p className="text-gray-600">{profile.category?.replace('_', ' ')}</p>
                  <div className="flex items-center mt-2">
                    <Badge className={`${getVerificationStatusColor(profile.verification_status)} text-white mr-2`}>
                      {getVerificationStatusIcon(profile.verification_status)}
                      <span className="ml-1 capitalize">{profile.verification_status?.replace('_', ' ')}</span>
                    </Badge>
                    <span className="text-sm text-gray-600">ID: {profile.vendor_id}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col items-end space-y-2">
                <div className="text-right">
                  <div className="text-2xl font-bold text-emerald-600">{profile.trust_score || 0}</div>
                  <div className="text-sm text-gray-600">Trust Score</div>
                </div>
                <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700">
                  <QrCode className="w-4 h-4 mr-2" />
                  View QR Code
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Dashboard Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="vendor-id">Vendor ID</TabsTrigger>
            <TabsTrigger value="verification">Verification</TabsTrigger>
            <TabsTrigger value="listings">Services</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Profile Views</p>
                      <p className="text-2xl font-bold text-gray-900">{analytics?.profile_views || 0}</p>
                    </div>
                    <Eye className="w-8 h-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Active Listings</p>
                      <p className="text-2xl font-bold text-gray-900">{active_listings?.length || 0}</p>
                    </div>
                    <Building2 className="w-8 h-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">QR Scans</p>
                      <p className="text-2xl font-bold text-gray-900">{analytics?.qr_scans || 0}</p>
                    </div>
                    <QrCode className="w-8 h-8 text-purple-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Verification Level</p>
                      <p className="text-2xl font-bold text-gray-900">{profile.verification_level || 0}</p>
                    </div>
                    <Star className="w-8 h-8 text-yellow-600" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Profile Completion */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Profile Completion
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Profile Information</span>
                    <span className="text-sm text-gray-600">{Math.round(profile.profile_completion || 0)}%</span>
                  </div>
                  <Progress value={profile.profile_completion || 0} className="h-2" />
                  <p className="text-sm text-gray-600">
                    Complete your profile to improve trust score and visibility
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Recent Activities */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Trust Events</CardTitle>
              </CardHeader>
              <CardContent>
                {trust_events.length > 0 ? (
                  <div className="space-y-4">
                    {trust_events.slice(0, 5).map((event, index) => (
                      <div key={index} className="flex items-center justify-between py-2 border-b last:border-b-0">
                        <div>
                          <p className="font-medium text-gray-900">{event.description}</p>
                          <p className="text-sm text-gray-600">{new Date(event.created_at).toLocaleDateString()}</p>
                        </div>
                        <Badge variant={event.impact_score > 0 ? "success" : "secondary"}>
                          {event.impact_score > 0 ? '+' : ''}{event.impact_score}
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600 text-center py-4">No trust events recorded yet</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Vendor ID Tab */}
          <TabsContent value="vendor-id">
            <VendorIDCard />
          </TabsContent>

          {/* Verification Tab */}
          <TabsContent value="verification" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Verification Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      {getVerificationStatusIcon(profile.verification_status)}
                      <div className="ml-3">
                        <p className="font-medium capitalize">
                          {profile.verification_status?.replace('_', ' ')}
                        </p>
                        <p className="text-sm text-gray-600">
                          {verification_status?.notes || 'No additional notes'}
                        </p>
                      </div>
                    </div>
                    <Badge className={getVerificationStatusColor(profile.verification_status) + ' text-white'}>
                      Level {profile.verification_level}
                    </Badge>
                  </div>

                  {profile.verification_status === 'pending' && (
                    <Alert>
                      <Upload className="h-4 w-4" />
                      <AlertDescription>
                        Upload required documents to start the verification process.
                      </AlertDescription>
                    </Alert>
                  )}

                  <Button className="w-full">
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Documents
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Services Tab */}
          <TabsContent value="listings" className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Service Listings</h3>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Add Service
              </Button>
            </div>

            {active_listings.length > 0 ? (
              <div className="grid gap-6">
                {active_listings.map((listing, index) => (
                  <Card key={index}>
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-semibold text-gray-900">{listing.title}</h4>
                          <p className="text-gray-600 mt-1">{listing.description}</p>
                          <div className="flex items-center mt-2 space-x-4">
                            <Badge variant="outline">{listing.category}</Badge>
                            <span className="text-sm text-gray-600">
                              {listing.price_range || 'Contact for pricing'}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-600">Views</p>
                          <p className="font-semibold">{listing.views_count || 0}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-8">
                    <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No services listed yet</h3>
                    <p className="text-gray-600 mb-4">Create your first service listing to attract customers</p>
                    <Button onClick={() => navigate('/documents')}>
                      <Plus className="w-4 h-4 mr-2" />
                      Add First Service
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Documents</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No documents uploaded</h3>
                  <p className="text-gray-600 mb-4">Upload verification documents to complete your profile</p>
                  <Button>
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Documents
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Profile Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>Profile Views</span>
                      <span className="font-semibold">{analytics?.profile_views || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Listing Views</span>
                      <span className="font-semibold">{analytics?.listing_views || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>QR Code Scans</span>
                      <span className="font-semibold">{analytics?.qr_scans || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Verification Checks</span>
                      <span className="font-semibold">{analytics?.verification_checks || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Trust Score History</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8">
                    <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">Trust score tracking coming soon</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default VendorEcosystemDashboard;