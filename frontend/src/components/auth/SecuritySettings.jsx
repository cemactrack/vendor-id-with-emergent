import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Shield, 
  Mail, 
  Smartphone,
  Key,
  Clock,
  CheckCircle,
  AlertTriangle,
  Settings,
  Eye,
  RefreshCw
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useAuth } from '../../contexts/AuthContext';
import TwoFactorSetup from './TwoFactorSetup';

const SecuritySettings = () => {
  const [securityInfo, setSecurityInfo] = useState(null);
  const [securityEvents, setSecurityEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [showTwoFactorSetup, setShowTwoFactorSetup] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    loadSecurityData();
  }, []);

  const loadSecurityData = async () => {
    try {
      setLoading(true);
      const [securityData, eventsData] = await Promise.all([
        vendorEcosystemAPI.getSecurityInfo(),
        vendorEcosystemAPI.getSecurityEvents(10)
      ]);
      
      setSecurityInfo(securityData);
      setSecurityEvents(eventsData);
    } catch (error) {
      console.error('Failed to load security data:', error);
      setMessage('Failed to load security information');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const resendEmailVerification = async () => {
    try {
      setActionLoading('email');
      await vendorEcosystemAPI.resendEmailVerification();
      setMessage('Verification email sent! Please check your inbox.');
      setMessageType('success');
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Failed to send verification email');
      setMessageType('error');
    } finally {
      setActionLoading('');
    }
  };

  const handleTwoFactorComplete = () => {
    setShowTwoFactorSetup(false);
    loadSecurityData();
    setMessage('Two-factor authentication has been enabled successfully!');
    setMessageType('success');
  };

  const disable2FA = async () => {
    // This would need a confirmation dialog with password input
    // For now, redirect to 2FA setup which can handle disabling
    setShowTwoFactorSetup(true);
  };

  const formatEventType = (eventType) => {
    return eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getEventIcon = (eventType) => {
    if (eventType.includes('login')) return <Key className="w-4 h-4" />;
    if (eventType.includes('2fa')) return <Smartphone className="w-4 h-4" />;
    if (eventType.includes('email')) return <Mail className="w-4 h-4" />;
    return <Shield className="w-4 h-4" />;
  };

  const getEventColor = (eventType) => {
    if (eventType.includes('failed') || eventType.includes('disabled')) return 'text-red-600';
    if (eventType.includes('success') || eventType.includes('enabled') || eventType.includes('verified')) return 'text-green-600';
    return 'text-blue-600';
  };

  if (showTwoFactorSetup) {
    return (
      <TwoFactorSetup
        onComplete={handleTwoFactorComplete}
        onCancel={() => setShowTwoFactorSetup(false)}
      />
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {message && (
        <Alert className={messageType === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
          {messageType === 'success' ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-red-600" />
          )}
          <AlertDescription className={messageType === 'success' ? 'text-green-800' : 'text-red-800'}>
            {message}
          </AlertDescription>
        </Alert>
      )}

      {/* Security Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="w-5 h-5 mr-2 text-emerald-600" />
            Security Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Email Verification */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center space-x-3">
              <Mail className="w-5 h-5 text-blue-600" />
              <div>
                <h4 className="font-medium">Email Verification</h4>
                <p className="text-sm text-gray-600">{user?.email}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {securityInfo?.email_verified ? (
                <Badge className="bg-green-100 text-green-800 border-green-200">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Verified
                </Badge>
              ) : (
                <>
                  <Badge variant="outline" className="text-yellow-600 border-yellow-200">
                    <AlertTriangle className="w-3 h-3 mr-1" />
                    Unverified
                  </Badge>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={resendEmailVerification}
                    disabled={actionLoading === 'email'}
                  >
                    {actionLoading === 'email' ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      'Verify'
                    )}
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Two-Factor Authentication */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center space-x-3">
              <Smartphone className="w-5 h-5 text-purple-600" />
              <div>
                <h4 className="font-medium">Two-Factor Authentication</h4>
                <p className="text-sm text-gray-600">
                  Add an extra layer of security to your account
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {securityInfo?.two_factor_enabled ? (
                <>
                  <Badge className="bg-green-100 text-green-800 border-green-200">
                    <Shield className="w-3 h-3 mr-1" />
                    Enabled
                  </Badge>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={disable2FA}
                    disabled={actionLoading === '2fa'}
                  >
                    <Settings className="w-4 h-4 mr-1" />
                    Manage
                  </Button>
                </>
              ) : (
                <Button
                  size="sm"
                  onClick={() => setShowTwoFactorSetup(true)}
                  disabled={actionLoading === '2fa'}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Smartphone className="w-4 h-4 mr-1" />
                  Enable 2FA
                </Button>
              )}
            </div>
          </div>

          {/* Account Status */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center space-x-3">
              <Shield className="w-5 h-5 text-emerald-600" />
              <div>
                <h4 className="font-medium">Account Status</h4>
                <p className="text-sm text-gray-600">
                  Failed attempts: {securityInfo?.failed_login_attempts || 0}
                </p>
              </div>
            </div>
            <div>
              {securityInfo?.account_locked_until ? (
                <Badge variant="outline" className="text-red-600 border-red-200">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  Locked
                </Badge>
              ) : (
                <Badge className="bg-green-100 text-green-800 border-green-200">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Active
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Security Events */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Eye className="w-5 h-5 mr-2 text-blue-600" />
            Recent Security Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          {securityEvents.length > 0 ? (
            <div className="space-y-3">
              {securityEvents.map((event, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={getEventColor(event.event_type)}>
                      {getEventIcon(event.event_type)}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{formatEventType(event.event_type)}</p>
                      <p className="text-xs text-gray-600">
                        {new Date(event.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center text-gray-500">
                    <Clock className="w-3 h-3" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Shield className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No security events recorded yet</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Security Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-amber-600" />
            Security Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {!securityInfo?.email_verified && (
              <div className="flex items-center space-x-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <div>
                  <p className="font-medium text-amber-800">Verify your email address</p>
                  <p className="text-sm text-amber-700">
                    Email verification is required for account recovery and security notifications.
                  </p>
                </div>
              </div>
            )}
            
            {!securityInfo?.two_factor_enabled && (
              <div className="flex items-center space-x-3 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <Smartphone className="w-5 h-5 text-purple-600" />
                <div>
                  <p className="font-medium text-purple-800">Enable two-factor authentication</p>
                  <p className="text-sm text-purple-700">
                    Protect your account with an additional security layer.
                  </p>
                </div>
              </div>
            )}
            
            {securityInfo?.email_verified && securityInfo?.two_factor_enabled && (
              <div className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <div>
                  <p className="font-medium text-green-800">Great job!</p>
                  <p className="text-sm text-green-700">
                    Your account security is well configured.
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SecuritySettings;