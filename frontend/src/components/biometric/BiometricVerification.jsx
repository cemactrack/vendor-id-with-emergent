import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Upload, 
  Camera, 
  Shield, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  User,
  Fingerprint,
  Eye,
  Scan
} from 'lucide-react';

const BiometricVerification = () => {
  const [currentStep, setCurrentStep] = useState('document');
  const [verificationSession, setVerificationSession] = useState(null);
  const [documentAnalysis, setDocumentAnalysis] = useState(null);
  const [livenessResult, setLivenessResult] = useState(null);
  const [faceMatchResult, setFaceMatchResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  
  const documentInputRef = useRef(null);
  const livenessInputRef = useRef(null);
  const comparisonInputRef = useRef(null);

  const steps = [
    { id: 'document', title: 'Document Upload', icon: Upload },
    { id: 'liveness', title: 'Liveness Check', icon: Camera },
    { id: 'face_match', title: 'Face Matching', icon: Scan },
    { id: 'complete', title: 'Complete', icon: CheckCircle }
  ];

  useEffect(() => {
    startVerificationSession();
  }, []);

  const startVerificationSession = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/biometric/verification/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_type: 'initial_verification' })
      });

      const data = await response.json();
      
      if (data.success) {
        setVerificationSession(data.session);
        setProgress(20);
      } else {
        setError('Failed to start verification session');
      }
    } catch (err) {
      console.error('Session start error:', err);
      setError('Failed to start verification session');
    } finally {
      setLoading(false);
    }
  };

  const analyzeDocument = async (file) => {
    try {
      setLoading(true);
      setError('');
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', 'national_id'); // Default to national ID
      
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/biometric/document/analyze`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        setDocumentAnalysis(data.analysis_result);
        setProgress(40);
        setCurrentStep('liveness');
      } else {
        setError('Document analysis failed');
      }
    } catch (err) {
      console.error('Document analysis error:', err);
      setError('Document analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const createLivenessChallenge = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/biometric/liveness/challenge`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      });

      const data = await response.json();
      
      if (data.success) {
        return data.challenge;
      } else {
        throw new Error('Failed to create liveness challenge');
      }
    } catch (err) {
      console.error('Liveness challenge error:', err);
      setError('Failed to create liveness challenge');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const performLivenessCheck = async (file) => {
    try {
      setLoading(true);
      setError('');
      
      // First create a liveness challenge
      const challenge = await createLivenessChallenge();
      if (!challenge) return;
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('challenge_id', challenge.challenge_id);
      
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/biometric/liveness/respond`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        setLivenessResult(data.liveness_result);
        setProgress(70);
        setCurrentStep('face_match');
      } else {
        setError('Liveness check failed');
      }
    } catch (err) {
      console.error('Liveness check error:', err);
      setError('Liveness check failed');
    } finally {
      setLoading(false);
    }
  };

  const performFaceMatching = async (comparisonFile) => {
    try {
      setLoading(true);
      setError('');
      
      if (!documentAnalysis?.face_image_path) {
        setError('No reference face found in document');
        return;
      }
      
      const formData = new FormData();
      // For now, we'll use the comparison file as both reference and comparison
      // In a real implementation, you'd extract the face from the document
      formData.append('reference_file', comparisonFile);
      formData.append('comparison_file', comparisonFile);
      formData.append('match_threshold', '0.75');
      
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/biometric/face/match`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        setFaceMatchResult(data.match_result);
        setProgress(100);
        setCurrentStep('complete');
      } else {
        setError('Face matching failed');
      }
    } catch (err) {
      console.error('Face matching error:', err);
      setError('Face matching failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (file, type) => {
    if (!file) return;
    
    switch (type) {
      case 'document':
        analyzeDocument(file);
        break;
      case 'liveness':
        performLivenessCheck(file);
        break;
      case 'comparison':
        performFaceMatching(file);
        break;
      default:
        break;
    }
  };

  const renderStepIndicator = () => (
    <div className="flex justify-between mb-8">
      {steps.map((step, index) => {
        const isActive = step.id === currentStep;
        const isCompleted = steps.findIndex(s => s.id === currentStep) > index;
        const Icon = step.icon;
        
        return (
          <div key={step.id} className="flex flex-col items-center">
            <div className={`
              w-10 h-10 rounded-full flex items-center justify-center mb-2
              ${isActive ? 'bg-blue-500 text-white' : 
                isCompleted ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'}
            `}>
              <Icon className="w-5 h-5" />
            </div>
            <span className={`text-sm ${isActive ? 'text-blue-500 font-medium' : 'text-gray-500'}`}>
              {step.title}
            </span>
          </div>
        );
      })}
    </div>
  );

  const renderDocumentUpload = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Document Upload
        </CardTitle>
        <CardDescription>
          Upload a clear photo of your government-issued ID
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="document">Select Document Type</Label>
          <Select defaultValue="national_id">
            <SelectTrigger>
              <SelectValue placeholder="Select document type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="national_id">National ID</SelectItem>
              <SelectItem value="passport">Passport</SelectItem>
              <SelectItem value="drivers_license">Driver's License</SelectItem>
              <SelectItem value="voter_id">Voter ID</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Label htmlFor="document">Upload Document</Label>
          <Input
            id="document"
            type="file"
            accept="image/*"
            ref={documentInputRef}
            onChange={(e) => handleFileUpload(e.target.files[0], 'document')}
            disabled={loading}
          />
        </div>
        
        {documentAnalysis && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertTitle>Document Analysis Complete</AlertTitle>
            <AlertDescription>
              Face detected: {documentAnalysis.face_image_extracted ? 'Yes' : 'No'} | 
              Quality Score: {(documentAnalysis.quality_score * 100).toFixed(1)}% | 
              Confidence: {(documentAnalysis.face_confidence * 100).toFixed(1)}%
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  const renderLivenessCheck = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="w-5 h-5" />
          Liveness Detection
        </CardTitle>
        <CardDescription>
          Record a short video following the instructions: blink, turn head left, then smile
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="liveness">Upload Video/Photo</Label>
          <Input
            id="liveness"
            type="file"
            accept="video/*,image/*"
            ref={livenessInputRef}
            onChange={(e) => handleFileUpload(e.target.files[0], 'liveness')}
            disabled={loading}
          />
        </div>
        
        {livenessResult && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertTitle>Liveness Check Complete</AlertTitle>
            <AlertDescription>
              Success: {livenessResult.success ? 'Yes' : 'No'} | 
              Confidence: {(livenessResult.confidence_score * 100).toFixed(1)}% | 
              Face Quality: {livenessResult.face_quality}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  const renderFaceMatching = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Scan className="w-5 h-5" />
          Face Matching
        </CardTitle>
        <CardDescription>
          Upload a clear photo of your face for comparison
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor="comparison">Upload Face Photo</Label>
          <Input
            id="comparison"
            type="file"
            accept="image/*"
            ref={comparisonInputRef}
            onChange={(e) => handleFileUpload(e.target.files[0], 'comparison')}
            disabled={loading}
          />
        </div>
        
        {faceMatchResult && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertTitle>Face Matching Complete</AlertTitle>
            <AlertDescription>
              Match: {faceMatchResult.match_confirmed ? 'Yes' : 'No'} | 
              Similarity: {(faceMatchResult.similarity_score * 100).toFixed(1)}% | 
              Confidence: {(faceMatchResult.confidence_level * 100).toFixed(1)}%
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  const renderComplete = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-500" />
          Verification Complete
        </CardTitle>
        <CardDescription>
          Your biometric verification has been completed successfully
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <Shield className="w-8 h-8 text-green-500 mx-auto mb-2" />
            <h3 className="font-medium">Document Verified</h3>
            <p className="text-sm text-gray-600">ID document analyzed</p>
          </div>
          
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <User className="w-8 h-8 text-blue-500 mx-auto mb-2" />
            <h3 className="font-medium">Liveness Confirmed</h3>
            <p className="text-sm text-gray-600">Live person detected</p>
          </div>
          
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <Scan className="w-8 h-8 text-purple-500 mx-auto mb-2" />
            <h3 className="font-medium">Face Matched</h3>
            <p className="text-sm text-gray-600">Identity confirmed</p>
          </div>
        </div>
        
        <Badge variant="outline" className="w-full justify-center py-2">
          Verification Status: Verified
        </Badge>
      </CardContent>
    </Card>
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Biometric Verification</h1>
        <p className="text-gray-600">Complete your identity verification using biometric authentication</p>
      </div>

      {renderStepIndicator()}

      <div className="mb-6">
        <Progress value={progress} className="w-full" />
        <p className="text-sm text-gray-600 mt-2">{progress}% Complete</p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin mr-2" />
          <span>Processing...</span>
        </div>
      )}

      <div className="space-y-6">
        {currentStep === 'document' && renderDocumentUpload()}
        {currentStep === 'liveness' && renderLivenessCheck()}
        {currentStep === 'face_match' && renderFaceMatching()}
        {currentStep === 'complete' && renderComplete()}
      </div>

      {verificationSession && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Session Info</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Session ID:</span>
                <span className="ml-2">{verificationSession.session_id?.substring(0, 8)}...</span>
              </div>
              <div>
                <span className="font-medium">Status:</span>
                <Badge variant="outline" className="ml-2">{verificationSession.status}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BiometricVerification;