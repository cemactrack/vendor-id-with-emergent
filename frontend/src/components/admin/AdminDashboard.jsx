import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Shield, 
  Users,
  FileText,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  Flag,
  BarChart3,
  Settings,
  LogOut,
  Search,
  Filter,
  Download
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useNavigate } from 'react-router-dom';
import VerificationQueue from './VerificationQueue';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [pendingVerifications, setPendingVerifications] = useState([]);
  const [selectedVerification, setSelectedVerification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [verificationNotes, setVerificationNotes] = useState('');
  const [updating, setUpdating] = useState(false);
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, verificationsData] = await Promise.all([
        vendorEcosystemAPI.getEcosystemStats(),
        vendorEcosystemAPI.getPendingVerifications(50)
      ]);
      
      setStats(statsData);
      setPendingVerifications(verificationsData);
    } catch (error) {
      console.error('Failed to load admin dashboard:', error);
      setError(error.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleVerificationAction = async (verificationId, status) => {
    try {
      setUpdating(true);
      await vendorEcosystemAPI.updateVerificationStatus(
        verificationId, 
        status, 
        verificationNotes || null
      );
      
      // Refresh data
      await loadDashboardData();
      setSelectedVerification(null);
      setVerificationNotes('');
      
    } catch (error) {
      console.error('Failed to update verification:', error);
      setError('Failed to update verification status');
    } finally {
      setUpdating(false);
    }
  };

  const getVerificationStatusColor = (status) => {
    switch (status) {
      case 'verified': return 'bg-green-500';
      case 'pending': return 'bg-yellow-500';
      case 'under_review': return 'bg-blue-500';
      case 'rejected': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  const getStatusIcon = (status) => {
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
          <p className="text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Admin Dashboard</h1>
              <p className="text-sm text-gray-600">Vendor Verification & Trust Management</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <Badge variant="outline" className="capitalize">
              {user?.role?.replace('_', ' ')}
            </Badge>
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
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Vendors</p>
                  <p className="text-2xl font-bold text-gray-900">{stats?.total_vendors || 0}</p>
                </div>
                <Users className="w-8 h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Verified Vendors</p>
                  <p className="text-2xl font-bold text-gray-900">{stats?.verified_vendors || 0}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Pending Reviews</p>
                  <p className="text-2xl font-bold text-gray-900">{stats?.verification_requests_pending || 0}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Trust Score</p>
                  <p className="text-2xl font-bold text-gray-900">{stats?.trust_score_average || 0}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Dashboard Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="verifications">
              Verification Queue
              {stats?.verification_requests_pending > 0 && (
                <Badge className="ml-2 bg-red-500 text-white text-xs">
                  {stats.verification_requests_pending}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="vendors">Vendors</TabsTrigger>
            <TabsTrigger value="fraud">Fraud Reports</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Quick Stats */}
              <Card>
                <CardHeader>
                  <CardTitle>System Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Active Listings</span>
                      <span className="font-semibold">{stats?.active_listings || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Total Documents</span>
                      <span className="font-semibold">{stats?.total_documents || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Countries Represented</span>
                      <span className="font-semibold">{stats?.countries_represented || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Business Categories</span>
                      <span className="font-semibold">{stats?.categories_covered || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-red-600">Open Fraud Reports</span>
                      <span className="font-semibold text-red-600">{stats?.fraud_reports_open || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <div>
                        <p className="text-sm font-medium">Vendor Verified</p>
                        <p className="text-xs text-gray-600">VID-NG-1234 completed verification</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-yellow-50 rounded-lg">
                      <Clock className="w-5 h-5 text-yellow-600" />
                      <div>
                        <p className="text-sm font-medium">New Verification Request</p>
                        <p className="text-xs text-gray-600">VID-CM-5678 submitted documents</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                      <Eye className="w-5 h-5 text-blue-600" />
                      <div>
                        <p className="text-sm font-medium">Under Review</p>
                        <p className="text-xs text-gray-600">VID-US-9012 documents being reviewed</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Verifications Tab */}
          <TabsContent value="verifications" className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Pending Verifications</h3>
              <div className="flex space-x-2">
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-2" />
                  Filter
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              </div>
            </div>

            <div className="grid gap-6">
              {pendingVerifications.length > 0 ? (
                pendingVerifications.map((verification) => (
                  <Card key={verification.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <Badge className={`${getVerificationStatusColor(verification.status)} text-white`}>
                              {getStatusIcon(verification.status)}
                              <span className="ml-1 capitalize">
                                {verification.status?.replace('_', ' ')}
                              </span>
                            </Badge>
                            <span className="text-sm text-gray-600">
                              Priority: {verification.priority}/5
                            </span>
                          </div>
                          
                          <h4 className="font-semibold text-gray-900 mb-1">
                            Vendor ID: {verification.vendor_id}
                          </h4>
                          <p className="text-sm text-gray-600 mb-2">
                            Requested: {new Date(verification.created_at).toLocaleDateString()}
                          </p>
                          <p className="text-sm text-gray-600">
                            Type: {verification.verification_type?.replace('_', ' ')}
                          </p>
                          
                          {verification.notes && (
                            <div className="mt-2 p-2 bg-gray-50 rounded text-sm text-gray-700">
                              {verification.notes}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex space-x-2">
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => setSelectedVerification(verification)}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            Review
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center py-8">
                      <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">All caught up!</h3>
                      <p className="text-gray-600">No pending verifications at the moment</p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Verification Modal */}
            {selectedVerification && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                <Card className="max-w-2xl w-full max-h-[80vh] overflow-y-auto">
                  <CardHeader>
                    <CardTitle>Review Verification Request</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="font-semibold mb-2">Vendor ID: {selectedVerification.vendor_id}</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Status:</span>
                          <Badge className={`ml-2 ${getVerificationStatusColor(selectedVerification.status)} text-white`}>
                            {selectedVerification.status}
                          </Badge>
                        </div>
                        <div>
                          <span className="text-gray-600">Priority:</span>
                          <span className="ml-2 font-medium">{selectedVerification.priority}/5</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Created:</span>
                          <span className="ml-2">{new Date(selectedVerification.created_at).toLocaleDateString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Type:</span>
                          <span className="ml-2">{selectedVerification.verification_type}</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Verification Notes
                      </label>
                      <Textarea
                        value={verificationNotes}
                        onChange={(e) => setVerificationNotes(e.target.value)}
                        placeholder="Add notes about this verification..."
                        rows={3}
                      />
                    </div>

                    <div className="flex justify-between space-x-4">
                      <div className="flex space-x-2">
                        <Button
                          onClick={() => handleVerificationAction(selectedVerification.id, 'verified')}
                          disabled={updating}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Approve
                        </Button>
                        <Button
                          onClick={() => handleVerificationAction(selectedVerification.id, 'rejected')}
                          disabled={updating}
                          variant="destructive"
                        >
                          <AlertTriangle className="w-4 h-4 mr-2" />
                          Reject
                        </Button>
                        <Button
                          onClick={() => handleVerificationAction(selectedVerification.id, 'under_review')}
                          disabled={updating}
                          variant="outline"
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          Review Later
                        </Button>
                      </div>
                      <Button
                        variant="outline"
                        onClick={() => setSelectedVerification(null)}
                        disabled={updating}
                      >
                        Cancel
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Fraud Reports Tab */}
          <TabsContent value="fraud" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Flag className="w-5 h-5 mr-2 text-red-600" />
                  Fraud Reports
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <Flag className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No active fraud reports</h3>
                  <p className="text-gray-600">All reports have been resolved</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BarChart3 className="w-5 h-5 mr-2" />
                    Verification Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>Total Processed</span>
                      <span className="font-semibold">{stats?.verified_vendors || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Success Rate</span>
                      <span className="font-semibold text-green-600">
                        {stats?.total_vendors > 0 
                          ? Math.round((stats.verified_vendors / stats.total_vendors) * 100) 
                          : 0}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Average Processing Time</span>
                      <span className="font-semibold">2.3 days</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Geographic Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Countries Active</span>
                      <span className="font-semibold">{stats?.countries_represented || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Business Categories</span>
                      <span className="font-semibold">{stats?.categories_covered || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Average Trust Score</span>
                      <span className="font-semibold">{stats?.trust_score_average || 0}</span>
                    </div>
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

export default AdminDashboard;