import React, { useState, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { 
  Upload,
  FileText,
  CheckCircle,
  AlertTriangle,
  X,
  Eye,
  Download,
  RefreshCw
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';

const DocumentUpload = ({ onUploadComplete, vendorId }) => {
  const [uploadedDocuments, setUploadedDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const documentTypes = [
    {
      type: 'business_registration',
      title: 'Business Registration Certificate',
      description: 'Official business registration document from government authorities',
      required: true,
      maxSize: 10, // MB
      acceptedFormats: ['.pdf', '.jpg', '.jpeg', '.png']
    },
    {
      type: 'tax_id',
      title: 'Tax Identification Document',
      description: 'Tax ID, TIN, or VAT registration certificate',
      required: true,
      maxSize: 10,
      acceptedFormats: ['.pdf', '.jpg', '.jpeg', '.png']
    },
    {
      type: 'government_id',
      title: 'Government-Issued ID',
      description: 'Driver\'s license, passport, or national ID of business owner',
      required: true,
      maxSize: 5,
      acceptedFormats: ['.jpg', '.jpeg', '.png']
    },
    {
      type: 'operating_license',
      title: 'Operating License',
      description: 'Industry-specific operating license or permit',
      required: false,
      maxSize: 10,
      acceptedFormats: ['.pdf', '.jpg', '.jpeg', '.png']
    },
    {
      type: 'association_membership',
      title: 'Association Membership',
      description: 'Professional or trade association membership certificate',
      required: false,
      maxSize: 5,
      acceptedFormats: ['.pdf', '.jpg', '.jpeg', '.png']
    }
  ];

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e, documentType = null) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0], documentType);
    }
  }, []);

  const handleFileSelect = (e, documentType) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file, documentType);
    }
  };

  const handleFileUpload = async (file, documentType) => {
    setError('');
    setSuccess('');

    // Validate file
    const docType = documentTypes.find(dt => dt.type === documentType);
    if (!docType) {
      setError('Invalid document type');
      return;
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > docType.maxSize) {
      setError(`File size must be less than ${docType.maxSize}MB`);
      return;
    }

    // Check file format
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    if (!docType.acceptedFormats.includes(fileExt)) {
      setError(`Please upload files in format: ${docType.acceptedFormats.join(', ')}`);
      return;
    }

    try {
      setUploading(true);
      setUploadProgress({ [documentType]: 0 });

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => ({
          ...prev,
          [documentType]: Math.min((prev[documentType] || 0) + 10, 90)
        }));
      }, 200);

      // Upload file
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', documentType);

      const response = await vendorEcosystemAPI.uploadDocument(formData);

      clearInterval(progressInterval);
      setUploadProgress({ [documentType]: 100 });

      // Add to uploaded documents
      const newDocument = {
        documentId: response.document_id,
        type: documentType,
        filename: file.name,
        uploadDate: new Date(),
        status: 'uploaded',
        verificationStatus: 'pending'
      };

      setUploadedDocuments(prev => {
        const filtered = prev.filter(doc => doc.type !== documentType);
        return [...filtered, newDocument];
      });

      setSuccess(`${docType.title} uploaded successfully`);
      
      // Check if all required documents are uploaded
      const requiredDocs = documentTypes.filter(dt => dt.required);
      const uploadedRequiredDocs = [...uploadedDocuments, newDocument].filter(doc => 
        requiredDocs.some(req => req.type === doc.type)
      );

      if (uploadedRequiredDocs.length >= requiredDocs.length && onUploadComplete) {
        onUploadComplete(true);
      }

    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
      setTimeout(() => {
        setUploadProgress({});
      }, 2000);
    }
  };

  const removeDocument = async (documentId, documentType) => {
    try {
      await vendorEcosystemAPI.deleteDocument(documentId);
      setUploadedDocuments(prev => prev.filter(doc => doc.documentId !== documentId));
      setSuccess('Document removed successfully');

      // Update completion status
      const requiredDocs = documentTypes.filter(dt => dt.required);
      const remainingRequiredDocs = uploadedDocuments
        .filter(doc => doc.documentId !== documentId)
        .filter(doc => requiredDocs.some(req => req.type === doc.type));

      if (onUploadComplete) {
        onUploadComplete(remainingRequiredDocs.length >= requiredDocs.length);
      }
    } catch (error) {
      setError('Failed to remove document');
    }
  };

  const getDocumentStatus = (documentType) => {
    const uploaded = uploadedDocuments.find(doc => doc.type === documentType);
    if (uploaded) return uploaded;
    return null;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'uploaded':
        return <Badge className="bg-blue-100 text-blue-800">Uploaded</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-800">Pending Review</Badge>;
      case 'approved':
        return <Badge className="bg-green-100 text-green-800">Approved</Badge>;
      case 'rejected':
        return <Badge className="bg-red-100 text-red-800">Rejected</Badge>;
      default:
        return null;
    }
  };

  const completionPercentage = () => {
    const requiredDocs = documentTypes.filter(dt => dt.required);
    const uploadedRequired = uploadedDocuments.filter(doc => 
      requiredDocs.some(req => req.type === doc.type)
    );
    return Math.round((uploadedRequired.length / requiredDocs.length) * 100);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-4">
          <FileText className="w-8 h-8 text-blue-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Document Upload</h2>
        <p className="text-gray-600">
          Upload your verification documents to complete your vendor profile
        </p>
      </div>

      {/* Progress */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Completion Progress</span>
            <span className="text-sm text-gray-600">{completionPercentage()}%</span>
          </div>
          <Progress value={completionPercentage()} className="h-2" />
          <p className="text-xs text-gray-500 mt-2">
            {documentTypes.filter(dt => dt.required).length} required documents needed
          </p>
        </CardContent>
      </Card>

      {/* Alerts */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      {/* Document Upload Cards */}
      <div className="grid gap-6">
        {documentTypes.map((docType) => {
          const uploaded = getDocumentStatus(docType.type);
          const isUploading = uploadProgress[docType.type] !== undefined;
          
          return (
            <Card key={docType.type} className={`transition-all duration-200 ${
              uploaded ? 'ring-2 ring-green-200 bg-green-50' : 'hover:shadow-md'
            }`}>
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg flex items-center">
                      {docType.title}
                      {docType.required && (
                        <span className="text-red-500 ml-1">*</span>
                      )}
                    </CardTitle>
                    <p className="text-sm text-gray-600 mt-1">{docType.description}</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="text-xs text-gray-500">
                        Max size: {docType.maxSize}MB
                      </span>
                      <span className="text-xs text-gray-500">
                        Formats: {docType.acceptedFormats.join(', ')}
                      </span>
                    </div>
                  </div>
                  {uploaded && getStatusBadge(uploaded.verificationStatus)}
                </div>
              </CardHeader>

              <CardContent>
                {uploaded ? (
                  /* Uploaded Document Display */
                  <div className="flex items-center justify-between p-4 bg-white rounded-lg border">
                    <div className="flex items-center space-x-3">
                      <FileText className="w-8 h-8 text-green-600" />
                      <div>
                        <p className="font-medium text-gray-900">{uploaded.filename}</p>
                        <p className="text-sm text-gray-600">
                          Uploaded {uploaded.uploadDate.toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeDocument(uploaded.documentId, docType.type)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ) : (
                  /* Upload Area */
                  <div>
                    {/* Upload Progress */}
                    {isUploading && (
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Uploading...</span>
                          <span className="text-sm text-gray-600">
                            {uploadProgress[docType.type]}%
                          </span>
                        </div>
                        <Progress value={uploadProgress[docType.type]} className="h-2" />
                      </div>
                    )}

                    {/* Drop Zone */}
                    <div
                      className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                        dragActive
                          ? 'border-emerald-500 bg-emerald-50'
                          : 'border-gray-300 hover:border-emerald-400'
                      }`}
                      onDragEnter={handleDrag}
                      onDragLeave={handleDrag}
                      onDragOver={handleDrag}
                      onDrop={(e) => handleDrop(e, docType.type)}
                    >
                      <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-lg font-medium text-gray-900 mb-2">
                        Drop your file here or click to browse
                      </p>
                      <p className="text-sm text-gray-600 mb-4">
                        Supports: {docType.acceptedFormats.join(', ')} (Max: {docType.maxSize}MB)
                      </p>
                      
                      <input
                        type="file"
                        accept={docType.acceptedFormats.join(',')}
                        onChange={(e) => handleFileSelect(e, docType.type)}
                        className="hidden"
                        id={`file-input-${docType.type}`}
                        disabled={uploading}
                      />
                      
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => document.getElementById(`file-input-${docType.type}`).click()}
                        disabled={uploading}
                        className="mx-auto"
                      >
                        {uploading ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Uploading...
                          </>
                        ) : (
                          <>
                            <Upload className="w-4 h-4 mr-2" />
                            Choose File
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Instructions */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <h3 className="font-semibold text-blue-900 mb-3">Upload Guidelines</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
              Ensure all documents are clear, legible, and in color
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
              Documents should be recent and not expired
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
              All text and details must be fully visible
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
              Business documents must match the business name in your profile
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
              Government ID must belong to the business owner or authorized representative
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default DocumentUpload;