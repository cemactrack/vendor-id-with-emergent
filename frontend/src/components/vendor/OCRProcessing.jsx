import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  FileText,
  Upload,
  Eye,
  CheckCircle,
  AlertTriangle,
  Clock,
  RotateCw,
  Download,
  Search,
  ZoomIn,
  Copy,
  RefreshCw
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useAuth } from '../../contexts/AuthContext';

const OCRProcessing = () => {
  const [documents, setDocuments] = useState([]);
  const [ocrResults, setOcrResults] = useState({});
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState({});
  const [error, setError] = useState('');
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [activeTab, setActiveTab] = useState('documents');
  const [ocrSummary, setOcrSummary] = useState(null);
  
  const { user } = useAuth();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load vendor documents
      const vendorData = await vendorEcosystemAPI.getVendorDashboard();
      setDocuments(vendorData.documents || []);
      
      // Load OCR summary
      const summary = await vendorEcosystemAPI.getOCRSummary();
      setOcrSummary(summary);
      
      // Load OCR results for each document
      const results = {};
      for (const doc of vendorData.documents || []) {
        if (doc.ocr_processed) {
          try {
            const result = await vendorEcosystemAPI.getDocumentOCRResults(doc.document_id);
            results[doc.document_id] = result;
          } catch (err) {
            console.warn(`Failed to load OCR results for document ${doc.document_id}`);
          }
        }
      }
      setOcrResults(results);
      
    } catch (error) {
      console.error('Failed to load OCR data:', error);
      setError('Failed to load OCR processing data');
    } finally {
      setLoading(false);
    }
  };

  const processDocument = async (documentId, documentType) => {
    try {
      setProcessing(prev => ({ ...prev, [documentId]: true }));
      
      // Find the document
      const document = documents.find(doc => doc.document_id === documentId);
      if (!document || !document.file_path) {
        throw new Error('Document file not found');
      }

      // In a real implementation, you would fetch the file and process it
      // For now, we'll simulate the API call structure
      const result = await vendorEcosystemAPI.processDocumentOCR(documentId, documentType, null);
      
      // Reload data to get updated results
      await loadData();
      
    } catch (error) {
      console.error('OCR processing failed:', error);
      setError(error.response?.data?.detail || 'OCR processing failed');
    } finally {
      setProcessing(prev => ({ ...prev, [documentId]: false }));
    }
  };

  const validateDocumentData = async (documentId, expectedFields) => {
    try {
      const result = await vendorEcosystemAPI.validateDocumentOCR(documentId, expectedFields);
      
      // Update the OCR results with validation data
      setOcrResults(prev => ({
        ...prev,
        [documentId]: {
          ...prev[documentId],
          validation_results: result
        }
      }));
      
    } catch (error) {
      console.error('Validation failed:', error);
      setError('Document validation failed');
    }
  };

  const getDocumentStatusBadge = (document) => {
    if (document.ocr_processed) {
      const confidence = document.ocr_confidence || 0;
      if (confidence > 80) {
        return <Badge className="bg-green-100 text-green-800">High Confidence</Badge>;
      } else if (confidence > 60) {
        return <Badge className="bg-yellow-100 text-yellow-800">Medium Confidence</Badge>;
      } else {
        return <Badge className="bg-red-100 text-red-800">Low Confidence</Badge>;
      }
    } else {
      return <Badge variant="outline">Not Processed</Badge>;
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading OCR processing data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">OCR Document Processing</h1>
              <p className="text-gray-600">Process and validate your business documents with OCR</p>
            </div>
            <Button onClick={loadData} disabled={loading}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {/* OCR Summary */}
        {ocrSummary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Documents Processed</p>
                    <p className="text-2xl font-bold text-gray-900">{ocrSummary.processed_documents}</p>
                  </div>
                  <FileText className="w-8 h-8 text-blue-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Average Confidence</p>
                    <p className="text-2xl font-bold text-gray-900">{Math.round(ocrSummary.average_confidence)}%</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Words Extracted</p>
                    <p className="text-2xl font-bold text-gray-900">{ocrSummary.total_words_extracted}</p>
                  </div>
                  <Search className="w-8 h-8 text-purple-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Processing Time</p>
                    <p className="text-2xl font-bold text-gray-900">{Math.round(ocrSummary.average_processing_time)}s</p>
                  </div>
                  <Clock className="w-8 h-8 text-orange-600" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="results">OCR Results</TabsTrigger>
            <TabsTrigger value="validation">Validation</TabsTrigger>
          </TabsList>

          {/* Documents Tab */}
          <TabsContent value="documents" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Your Documents</CardTitle>
              </CardHeader>
              <CardContent>
                {documents.length > 0 ? (
                  <div className="space-y-4">
                    {documents.map((document) => (
                      <div key={document.document_id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <FileText className="w-8 h-8 text-blue-600" />
                          <div>
                            <h3 className="font-medium text-gray-900">{document.document_type}</h3>
                            <p className="text-sm text-gray-600">Uploaded {new Date(document.created_at).toLocaleDateString()}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                          {getDocumentStatusBadge(document)}
                          
                          {document.ocr_processed ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedDocument(document)}
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              View Results
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              onClick={() => processDocument(document.document_id, document.document_type)}
                              disabled={processing[document.document_id]}
                            >
                              {processing[document.document_id] ? (
                                <RotateCw className="w-4 h-4 mr-2 animate-spin" />
                              ) : (
                                <Upload className="w-4 h-4 mr-2" />
                              )}
                              Process OCR
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No documents uploaded</h3>
                    <p className="text-gray-600 mb-4">Upload documents to start OCR processing</p>
                    <Button onClick={() => window.location.href = '/documents'}>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Documents
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* OCR Results Tab */}
          <TabsContent value="results" className="space-y-6">
            {selectedDocument && ocrResults[selectedDocument.document_id] ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    OCR Results: {selectedDocument.document_type}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(ocrResults[selectedDocument.document_id].combined_text)}
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy Text
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Metadata */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="text-sm text-gray-600">Confidence</p>
                        <p className="font-semibold">{Math.round(ocrResults[selectedDocument.document_id].overall_confidence)}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Words Extracted</p>
                        <p className="font-semibold">{ocrResults[selectedDocument.document_id].total_words_extracted}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Pages</p>
                        <p className="font-semibold">{ocrResults[selectedDocument.document_id].page_count}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Processing Time</p>
                        <p className="font-semibold">{Math.round(ocrResults[selectedDocument.document_id].processing_time_seconds)}s</p>
                      </div>
                    </div>

                    {/* Extracted Text */}
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Extracted Text</h4>
                      <div className="bg-white border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                        <pre className="whitespace-pre-wrap text-sm text-gray-700">
                          {ocrResults[selectedDocument.document_id].combined_text}
                        </pre>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-8">
                    <Eye className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Select a document</h3>
                    <p className="text-gray-600">Choose a processed document to view OCR results</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Validation Tab */}
          <TabsContent value="validation" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Document Validation</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Validation Features</h3>
                  <p className="text-gray-600 mb-4">Validate extracted data against your profile information</p>
                  <Button disabled>
                    <AlertTriangle className="w-4 h-4 mr-2" />
                    Coming Soon
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default OCRProcessing;