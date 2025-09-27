import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { Mail, Lock, Eye, EyeOff, Shield, Smartphone, Key } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { Link, useNavigate } from 'react-router-dom';

const EnhancedLoginForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    totpToken: '',
    backupCode: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [requires2FA, setRequires2FA] = useState(false);
  const [use2FAMode, setUse2FAMode] = useState('totp'); // 'totp' or 'backup'
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError(''); // Clear error when user types
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // If 2FA is required, send the 2FA code
      if (requires2FA) {
        const totpToken = use2FAMode === 'totp' ? formData.totpToken : null;
        const backupCode = use2FAMode === 'backup' ? formData.backupCode : null;
        
        if (!totpToken && !backupCode) {
          setError(`Please enter your ${use2FAMode === 'totp' ? 'authenticator code' : 'backup code'}`);
          return;
        }

        const response = await vendorEcosystemAPI.login(
          formData.email, 
          formData.password, 
          totpToken, 
          backupCode
        );

        if (response.user && response.token) {
          const result = await login(formData.email, formData.password);
          if (result.success) {
            setSuccess('Login successful!');
            if (onSuccess) {
              onSuccess(result.user);
            } else {
              navigate('/dashboard');
            }
          }
        }
      } else {
        // First login attempt
        const response = await vendorEcosystemAPI.login(formData.email, formData.password);
        
        if (response.requires_2fa) {
          setRequires2FA(true);
          setSuccess('Please enter your two-factor authentication code');
          return;
        }

        if (response.user && response.token) {
          const result = await login(formData.email, formData.password);
          if (result.success) {
            setSuccess('Login successful!');
            if (onSuccess) {
              onSuccess(result.user);
            } else {
              navigate('/dashboard');
            }
          }
        }
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      setError(errorMessage);
      
      // Reset 2FA requirement on error
      if (requires2FA) {
        setRequires2FA(false);
        setFormData(prev => ({
          ...prev,
          totpToken: '',
          backupCode: ''
        }));
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleAuthMode = () => {
    setUse2FAMode(prev => prev === 'totp' ? 'backup' : 'totp');
    setFormData(prev => ({
      ...prev,
      totpToken: '',
      backupCode: ''
    }));
    setError('');
  };

  const resetForm = () => {
    setRequires2FA(false);
    setFormData({
      email: '',
      password: '',
      totpToken: '',
      backupCode: ''
    });
    setError('');
    setSuccess('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h1>
          <p className="text-gray-600">Sign in to your Vendor Ecosystem account</p>
        </div>

        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="space-y-1 pb-6">
            <CardTitle className="text-2xl font-bold text-center text-gray-900">
              {requires2FA ? 'Two-Factor Authentication' : 'Sign In'}
            </CardTitle>
            {requires2FA && (
              <p className="text-sm text-gray-600 text-center">
                Enter your {use2FAMode === 'totp' ? 'authenticator app code' : 'backup code'}
              </p>
            )}
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertDescription className="text-red-800">
                    {error}
                  </AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="border-green-200 bg-green-50">
                  <AlertDescription className="text-green-800">
                    {success}
                  </AlertDescription>
                </Alert>
              )}

              {!requires2FA ? (
                <>
                  {/* Email */}
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                      Email Address
                    </Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        placeholder="Enter your email"
                        className="pl-10 h-12 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
                        required
                        autoComplete="email"
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                      Password
                    </Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                      <Input
                        id="password"
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        value={formData.password}
                        onChange={handleInputChange}
                        placeholder="Enter your password"
                        className="pl-10 pr-10 h-12 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
                        required
                        autoComplete="current-password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>

                  {/* Remember me and Forgot password */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <input
                        id="remember-me"
                        name="remember-me"
                        type="checkbox"
                        className="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded"
                      />
                      <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                        Remember me
                      </label>
                    </div>
                    <Link
                      to="/forgot-password"
                      className="text-sm text-emerald-600 hover:text-emerald-500 font-medium"
                    >
                      Forgot password?
                    </Link>
                  </div>
                </>
              ) : (
                <>
                  {/* 2FA Code Input */}
                  <div className="space-y-2">
                    <Label 
                      htmlFor={use2FAMode === 'totp' ? 'totpToken' : 'backupCode'} 
                      className="text-sm font-medium text-gray-700 flex items-center"
                    >
                      {use2FAMode === 'totp' ? (
                        <>
                          <Smartphone className="w-4 h-4 mr-2" />
                          Authenticator Code
                        </>
                      ) : (
                        <>
                          <Key className="w-4 h-4 mr-2" />
                          Backup Code
                        </>
                      )}
                    </Label>
                    <div className="relative">
                      {use2FAMode === 'totp' ? (
                        <Input
                          id="totpToken"
                          name="totpToken"
                          type="text"
                          value={formData.totpToken}
                          onChange={handleInputChange}
                          placeholder="Enter 6-digit code"
                          className="h-12 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 text-center text-lg font-mono tracking-wider"
                          maxLength={6}
                          pattern="[0-9]{6}"
                          autoComplete="one-time-code"
                          required
                        />
                      ) : (
                        <Input
                          id="backupCode"
                          name="backupCode"
                          type="text"
                          value={formData.backupCode}
                          onChange={handleInputChange}
                          placeholder="XXXX-XXXX"
                          className="h-12 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 text-center text-lg font-mono tracking-wider"
                          maxLength={9}
                          pattern="[A-Z0-9]{4}-[A-Z0-9]{4}"
                          autoComplete="off"
                          required
                        />
                      )}
                    </div>
                    <div className="text-center">
                      <button
                        type="button"
                        onClick={toggleAuthMode}
                        className="text-sm text-emerald-600 hover:text-emerald-500 font-medium"
                      >
                        {use2FAMode === 'totp' ? 'Use backup code instead' : 'Use authenticator app instead'}
                      </button>
                    </div>
                  </div>

                  {/* Back to login */}
                  <div className="text-center">
                    <button
                      type="button"
                      onClick={resetForm}
                      className="text-sm text-gray-600 hover:text-gray-500"
                    >
                      ← Back to login
                    </button>
                  </div>
                </>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    {requires2FA ? 'Verifying...' : 'Signing In...'}
                  </div>
                ) : (
                  requires2FA ? 'Verify & Sign In' : 'Sign In'
                )}
              </Button>
            </form>

            {!requires2FA && (
              <>
                {/* Sign up link */}
                <div className="mt-6 text-center">
                  <p className="text-sm text-gray-600">
                    Don't have an account?{' '}
                    <Link
                      to="/register"
                      className="text-emerald-600 hover:text-emerald-500 font-medium"
                    >
                      Sign up for free
                    </Link>
                  </p>
                </div>

                {/* Demo accounts */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <p className="text-xs text-gray-500 text-center mb-3">Demo Accounts:</p>
                  <div className="space-y-2 text-xs text-gray-600">
                    <div className="flex justify-between">
                      <span>Vendor:</span>
                      <span className="font-mono">vendor@demo.com / demo123</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Admin:</span>
                      <span className="font-mono">admin@demo.com / demo123</span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Additional Info */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            Secure vendor verification and trust ecosystem
          </p>
        </div>
      </div>
    </div>
  );
};

export default EnhancedLoginForm;