import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Textarea } from '../ui/textarea';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  FileText, 
  Eye, 
  CheckCircle, 
  XCircle,
  Clock,
  User,
  Building2,
  Calendar,
  Flag,
  Download,
  Zoom,
  ArrowLeft
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';

const DocumentReview = ({ documentId, onClose, onStatusUpdate }) => {
  const [document, setDocument] = useState(null);
  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadDocumentDetails();
  }, [documentId]);

  const loadDocumentDetails = async () => {
    try {
      setLoading(true);
      const docData = await vendorEcosystemAPI.getDocumentForReview(documentId);
      setDocument(docData.document);
      setVendor(docData.vendor);
    } catch (error) {
      setError('Failed to load document details');
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async () => {
    try {
      setProcessing(true);
      setError('');
      
      await vendorEcosystemAPI.approveDocument(documentId, reviewNotes);
      
      setSuccess('Document approved successfully');
      if (onStatusUpdate) onStatusUpdate('approved');
      
      setTimeout(() => {
        if (onClose) onClose();
      }, 2000);
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to approve document');
    } finally {
      setProcessing(false);
    }
  };

  const handleRejection = async () => {
    if (!reviewNotes.trim()) {
      setError('Please provide a reason for rejection');
      return;
    }

    try {
      setProcessing(true);
      setError('');
      
      await vendorEcosystemAPI.rejectDocument(documentId, reviewNotes);
      
      setSuccess('Document rejected');
      if (onStatusUpdate) onStatusUpdate('rejected');
      
      setTimeout(() => {
        if (onClose) onClose();
      }, 2000);
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to reject document');
    } finally {
      setProcessing(false);
    }
  };

  const getDocumentTypeDisplay = (type) => {
    const typeMap = {
      'business_registration': 'Business Registration Certificate',
      'tax_id': 'Tax Identification Document',
      'government_id': 'Government-Issued ID',
      'operating_license': 'Operating License',
      'association_membership': 'Association Membership'
    };
    return typeMap[type] || type;
  };

  const getPriorityBadge = (priority) => {
    const config = {
      5: { color: 'bg-red-100 text-red-800 border-red-200', label: 'Critical' },
      4: { color: 'bg-orange-100 text-orange-800 border-orange-200', label: 'High' },
      3: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', label: 'Medium' },
      2: { color: 'bg-blue-100 text-blue-800 border-blue-200', label: 'Low' },
      1: { color: 'bg-gray-100 text-gray-800 border-gray-200', label: 'Minimal' }
    };
    const priorityConfig = config[priority] || config[1];
    return (
      <Badge className={priorityConfig.color}>
        <Flag className="w-3 h-3 mr-1" />
        {priorityConfig.label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="p-8 text-center">
        <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Document Not Found</h3>
        <p className="text-gray-600">The requested document could not be loaded.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" onClick={onClose}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Queue
          </Button>
          <h1 className="text-2xl font-bold text-gray-900">Document Review</h1>
        </div>
        {getPriorityBadge(document.priority)}
      </div>

      {/* Alerts */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <XCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document Information */}
        <div className="lg:col-span-2 space-y-6">
          {/* Document Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="w-5 h-5 mr-2" />
                Document Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Document Type</label>
                  <p className="text-gray-900">{getDocumentTypeDisplay(document.document_type)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">File Name</label>
                  <p className="text-gray-900">{document.original_filename}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Upload Date</label>
                  <p className="text-gray-900">
                    {new Date(document.upload_timestamp).toLocaleString()}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">File Size</label>
                  <p className="text-gray-900">
                    {(document.file_size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              </div>

              {/* Document Preview */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">Document Preview</h4>
                  <div className="flex space-x-2">
                    <Button size="sm" variant="outline">
                      <Zoom className="w-4 h-4 mr-1" />
                      Zoom
                    </Button>
                    <Button size="sm" variant="outline">
                      <Download className="w-4 h-4 mr-1" />
                      Download
                    </Button>
                  </div>
                </div>
                
                {/* Placeholder for document preview */}
                <div className="w-full h-64 bg-gray-100 border border-gray-200 rounded flex items-center justify-center">
                  <div className="text-center">
                    <FileText className="w-16 h-16 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-600">Document Preview</p>
                    <p className="text-sm text-gray-500">{document.original_filename}</p>
                  </div>
                </div>
              </div>

              {/* OCR Results */}
              {document.ocr_text && (
                <div>
                  <h4 className="font-medium mb-2">Extracted Text (OCR)</h4>
                  <div className="bg-gray-50 p-3 rounded border text-sm">
                    <pre className="whitespace-pre-wrap text-gray-700">
                      {document.ocr_text}
                    </pre>
                  </div>
                </div>
              )}

              {/* Extracted Information */}
              {document.extracted_info && Object.keys(document.extracted_info).length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Extracted Information</h4>
                  <div className="bg-blue-50 p-3 rounded border">
                    {Object.entries(document.extracted_info).map(([key, value]) => (
                      <div key={key} className="flex justify-between py-1">
                        <span className="text-sm font-medium text-blue-900 capitalize">
                          {key.replace('_', ' ')}:
                        </span>
                        <span className="text-sm text-blue-800">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Review Notes */}
          <Card>
            <CardHeader>
              <CardTitle>Review Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                placeholder="Add review notes, feedback, or reasons for approval/rejection..."
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                rows={4}
                className="w-full"
              />
              <p className="text-sm text-gray-500 mt-2">
                Notes will be shared with the vendor and kept in audit logs
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Vendor Information Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <User className="w-5 h-5 mr-2" />
                Vendor Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {vendor && (
                <>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Business Name</label>
                    <p className="text-gray-900 font-medium">{vendor.business_name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Email</label>
                    <p className="text-gray-900">{vendor.email}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Country</label>
                    <p className="text-gray-900">{vendor.country}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Category</label>
                    <p className="text-gray-900 capitalize">{vendor.category?.replace('_', ' ')}</p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Verification Checklist */}
          <Card>
            <CardHeader>
              <CardTitle>Verification Checklist</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Document is clear & legible</span>
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Information matches profile</span>
                  <Clock className="w-4 h-4 text-yellow-600" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Document not expired</span>
                  <Clock className="w-4 h-4 text-yellow-600" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">No signs of tampering</span>
                  <Clock className="w-4 h-4 text-yellow-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleApproval}
              disabled={processing}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              {processing ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Processing...
                </div>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Approve Document
                </>
              )}
            </Button>

            <Button
              onClick={handleRejection}
              disabled={processing}
              variant="destructive"
              className="w-full"
            >
              {processing ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Processing...
                </div>
              ) : (
                <>
                  <XCircle className="w-4 h-4 mr-2" />
                  Reject Document
                </>
              )}
            </Button>

            <Button
              variant="outline"
              className="w-full"
              onClick={() => {/* Request more info */}}
            >
              Request More Information
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentReview;