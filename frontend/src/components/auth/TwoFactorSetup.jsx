import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { 
  Shield, 
  Smartphone, 
  Key, 
  Copy, 
  CheckCircle, 
  ArrowLeft,
  QrCode,
  AlertTriangle,
  Download,
  Eye,
  EyeOff
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const TwoFactorSetup = ({ onComplete, onCancel }) => {
  const [step, setStep] = useState(1); // 1: password, 2: setup, 3: verify, 4: backup codes
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [setupData, setSetupData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copiedItems, setCopiedItems] = useState(new Set());
  const { user } = useAuth();
  const navigate = useNavigate();

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;

    try {
      setLoading(true);
      setError('');
      
      const response = await vendorEcosystemAPI.setup2FA(password);
      setSetupData(response.setup_data);
      setStep(2);
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to setup 2FA');
    } finally {
      setLoading(false);
    }
  };

  const handleVerificationSubmit = async (e) => {
    e.preventDefault();
    if (loading || !verificationCode) return;

    try {
      setLoading(true);
      setError('');
      
      await vendorEcosystemAPI.enable2FA(verificationCode);
      setStep(4);
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text, item) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedItems(prev => new Set([...prev, item]));
      setTimeout(() => {
        setCopiedItems(prev => {
          const newSet = new Set(prev);
          newSet.delete(item);
          return newSet;
        });
      }, 3000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const downloadBackupCodes = () => {
    if (!setupData?.backup_codes) return;

    const content = `Vendor Ecosystem - Two Factor Authentication Backup Codes
Generated on: ${new Date().toLocaleString()}
User: ${user?.email}

IMPORTANT: Keep these codes in a safe place. Each code can only be used once.

Backup Codes:
${setupData.backup_codes.map((code, index) => `${index + 1}. ${code}`).join('\n')}

Instructions:
- Use these codes if you lose access to your authenticator app
- Each code can only be used once
- Generate new codes if you use all of these
- Keep these codes secure and private

For help: security@vendoreco.com`;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'vendor-ecosystem-backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleComplete = () => {
    if (onComplete) {
      onComplete();
    } else {
      navigate('/dashboard');
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <form onSubmit={handlePasswordSubmit} className="space-y-6">
            <div className="text-center mb-6">
              <Shield className="w-16 h-16 text-emerald-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Verify Your Identity
              </h3>
              <p className="text-gray-600">
                Enter your current password to setup two-factor authentication
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                Current Password
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your current password"
                  className="pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading || !password}
              className="w-full bg-emerald-600 hover:bg-emerald-700"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Setting up...
                </div>
              ) : (
                'Continue Setup'
              )}
            </Button>
          </form>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <QrCode className="w-16 h-16 text-blue-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Scan QR Code
              </h3>
              <p className="text-gray-600">
                Use your authenticator app to scan this QR code
              </p>
            </div>

            {setupData && (
              <div className="space-y-6">
                {/* QR Code */}
                <div className="flex justify-center">
                  <div className="bg-white p-4 rounded-lg border-2 border-gray-200">
                    <img
                      src={setupData.qr_code}
                      alt="2FA QR Code"
                      className="w-48 h-48"
                    />
                  </div>
                </div>

                {/* Manual Setup Key */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm font-medium text-gray-700">
                      Manual Entry Key
                    </Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(setupData.setup_key, 'setup_key')}
                    >
                      {copiedItems.has('setup_key') ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                  <code className="text-sm bg-white px-2 py-1 rounded border font-mono">
                    {setupData.setup_key}
                  </code>
                </div>

                {/* Recommended Apps */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">Recommended Apps:</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Google Authenticator</li>
                    <li>• Microsoft Authenticator</li>
                    <li>• Authy</li>
                    <li>• 1Password</li>
                  </ul>
                </div>
              </div>
            )}

            <Button
              onClick={() => setStep(3)}
              className="w-full bg-blue-600 hover:bg-blue-700"
            >
              <Smartphone className="w-4 h-4 mr-2" />
              I've Added the Account
            </Button>
          </div>
        );

      case 3:
        return (
          <form onSubmit={handleVerificationSubmit} className="space-y-6">
            <div className="text-center mb-6">
              <Key className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Verify Setup
              </h3>
              <p className="text-gray-600">
                Enter the 6-digit code from your authenticator app
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="code" className="text-sm font-medium text-gray-700">
                Verification Code
              </Label>
              <Input
                id="code"
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                className="text-center text-2xl font-mono tracking-wider"
                maxLength={6}
                required
              />
            </div>

            <Button
              type="submit"
              disabled={loading || verificationCode.length !== 6}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Verifying...
                </div>
              ) : (
                'Verify & Enable 2FA'
              )}
            </Button>
          </form>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                2FA Enabled Successfully!
              </h3>
              <p className="text-gray-600">
                Save these backup codes in a secure location
              </p>
            </div>

            <Alert className="border-amber-200 bg-amber-50">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertDescription className="text-amber-800">
                <strong>Important:</strong> Save these backup codes now. You won't be able to see them again.
              </AlertDescription>
            </Alert>

            {setupData?.backup_codes && (
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-900">Backup Codes</h4>
                    <div className="flex space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(setupData.backup_codes.join('\n'), 'backup_codes')}
                      >
                        {copiedItems.has('backup_codes') ? (
                          <CheckCircle className="w-4 h-4 text-green-600" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={downloadBackupCodes}
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {setupData.backup_codes.map((code, index) => (
                      <div key={index} className="bg-white p-2 rounded border">
                        <code className="text-sm font-mono">{code}</code>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-green-50 rounded-lg p-4">
                  <h4 className="font-medium text-green-900 mb-2">What's Protected Now:</h4>
                  <ul className="text-sm text-green-800 space-y-1">
                    <li>• Account login</li>
                    <li>• Profile changes</li>
                    <li>• Document uploads</li>
                    <li>• Sensitive operations</li>
                  </ul>
                </div>
              </div>
            )}

            <Button
              onClick={handleComplete}
              className="w-full bg-emerald-600 hover:bg-emerald-700"
            >
              Complete Setup
            </Button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="flex items-center justify-between mb-4">
              {step > 1 && step < 4 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setStep(step - 1)}
                >
                  <ArrowLeft className="w-4 h-4" />
                </Button>
              )}
              <div className="flex-1 text-center">
                <Badge variant="outline" className="mb-2">
                  Step {step} of 4
                </Badge>
              </div>
              {step === 1 && onCancel && (
                <Button variant="ghost" size="sm" onClick={onCancel}>
                  Cancel
                </Button>
              )}
            </div>
            <CardTitle className="text-2xl font-bold text-gray-900">
              Two-Factor Authentication
            </CardTitle>
          </CardHeader>
          
          <CardContent>
            {error && (
              <Alert className="border-red-200 bg-red-50 mb-6">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            {renderStep()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TwoFactorSetup;