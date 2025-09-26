import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { CheckCircle, AlertTriangle, Mail, ArrowLeft, RefreshCw } from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useAuth } from '../../contexts/AuthContext';

const EmailVerification = () => {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
  const [status, setStatus] = useState('pending'); // pending, success, error
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  
  const token = searchParams.get('token');

  useEffect(() => {
    if (token) {
      verifyEmail(token);
    }
  }, [token]);

  const verifyEmail = async (verificationToken) => {
    if (verifying) return;
    
    try {
      setVerifying(true);
      setLoading(true);
      
      const response = await vendorEcosystemAPI.verifyEmail(verificationToken);
      
      setStatus('success');
      setMessage(response.message || 'Email verified successfully!');
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
      
    } catch (error) {
      setStatus('error');
      setMessage(error.response?.data?.detail || 'Email verification failed');
    } finally {
      setLoading(false);
      setVerifying(false);
    }
  };

  const resendVerification = async () => {
    if (!isAuthenticated || resending) return;
    
    try {
      setResending(true);
      await vendorEcosystemAPI.resendEmailVerification();
      setMessage('Verification email sent! Please check your inbox.');
      setStatus('info');
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Failed to resend verification email');
      setStatus('error');
    } finally {
      setResending(false);
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-16 h-16 text-green-600" />;
      case 'error':
        return <AlertTriangle className="w-16 h-16 text-red-600" />;
      default:
        return <Mail className="w-16 h-16 text-blue-600" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  const getMessageColor = () => {
    switch (status) {
      case 'success':
        return 'text-green-800';
      case 'error':
        return 'text-red-800';
      default:
        return 'text-blue-800';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="mx-auto mb-4">
              {getStatusIcon()}
            </div>
            <CardTitle className="text-2xl font-bold text-gray-900">
              {token ? 'Email Verification' : 'Verify Your Email'}
            </CardTitle>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {token ? (
              // Token verification flow
              <div className="text-center">
                {loading ? (
                  <div className="space-y-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto"></div>
                    <p className="text-gray-600">Verifying your email...</p>
                  </div>
                ) : (
                  <div className={`p-4 rounded-lg border ${getStatusColor()}`}>
                    <p className={`font-medium ${getMessageColor()}`}>
                      {message}
                    </p>
                    {status === 'success' && (
                      <p className="text-sm text-gray-600 mt-2">
                        Redirecting to login page...
                      </p>
                    )}
                  </div>
                )}
              </div>
            ) : (
              // Manual verification flow
              <div className="space-y-4">
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Check Your Email
                  </h3>
                  <p className="text-gray-600 mb-4">
                    We've sent a verification link to your email address. 
                    Click the link to verify your account.
                  </p>
                  
                  {user?.email && (
                    <div className="bg-gray-50 rounded-lg p-3 mb-4">
                      <p className="text-sm text-gray-700">
                        Email sent to: <span className="font-medium">{user.email}</span>
                      </p>
                    </div>
                  )}
                </div>

                {message && (
                  <Alert className={`${getStatusColor()}`}>
                    <AlertDescription className={getMessageColor()}>
                      {message}
                    </AlertDescription>
                  </Alert>
                )}

                {isAuthenticated && (
                  <Button
                    onClick={resendVerification}
                    disabled={resending}
                    variant="outline"
                    className="w-full"
                  >
                    {resending ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Mail className="w-4 h-4 mr-2" />
                        Resend Verification Email
                      </>
                    )}
                  </Button>
                )}
              </div>
            )}

            <div className="text-center space-y-4">
              <div className="border-t pt-4">
                <Link
                  to={isAuthenticated ? "/dashboard" : "/login"}
                  className="inline-flex items-center text-emerald-600 hover:text-emerald-700 font-medium"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  {isAuthenticated ? "Back to Dashboard" : "Back to Login"}
                </Link>
              </div>
              
              <div className="text-sm text-gray-500">
                <p>Didn't receive the email? Check your spam folder.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EmailVerification;