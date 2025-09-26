import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { 
  FileText, 
  Eye, 
  Clock,
  User,
  Building2,
  Search,
  Filter,
  RefreshCw,
  Calendar,
  Flag,
  ArrowRight
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import DocumentReview from './DocumentReview';

const VerificationQueue = () => {
  const [queueItems, setQueueItems] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadQueue();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [queueItems, searchQuery, filterType, filterPriority]);

  const loadQueue = async () => {
    try {
      setLoading(true);
      const queue = await vendorEcosystemAPI.getVerificationQueue();
      setQueueItems(queue);
    } catch (error) {
      console.error('Failed to load verification queue:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshQueue = async () => {
    try {
      setRefreshing(true);
      await loadQueue();
    } finally {
      setRefreshing(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...queueItems];

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(item => 
        item.vendor_info?.business_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.document_info?.original_filename?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.vendor_id?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Document type filter
    if (filterType && filterType !== 'all') {
      filtered = filtered.filter(item => 
        item.document_info?.document_type === filterType
      );
    }

    // Priority filter
    if (filterPriority && filterPriority !== 'all') {
      filtered = filtered.filter(item => 
        item.priority === parseInt(filterPriority)
      );
    }

    // Sort by priority and date
    filtered.sort((a, b) => {
      if (a.priority !== b.priority) {
        return b.priority - a.priority; // Higher priority first
      }
      return new Date(a.created_at) - new Date(b.created_at); // Older first
    });

    setFilteredItems(filtered);
  };

  const getDocumentTypeDisplay = (type) => {
    const typeMap = {
      'business_registration': 'Business Registration',
      'tax_id': 'Tax ID',
      'government_id': 'Government ID',
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

  const handleDocumentReview = (item) => {
    setSelectedDocument(item);
  };

  const handleReviewComplete = (status) => {
    // Remove the reviewed document from queue
    setQueueItems(prev => prev.filter(item => 
      item.document_id !== selectedDocument.document_id
    ));
    setSelectedDocument(null);
  };

  if (selectedDocument) {
    return (
      <DocumentReview
        documentId={selectedDocument.document_id}
        onClose={() => setSelectedDocument(null)}
        onStatusUpdate={handleReviewComplete}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Verification Queue</h1>
          <p className="text-gray-600">Review and approve vendor documents</p>
        </div>
        <Button onClick={refreshQueue} disabled={refreshing} variant="outline">
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search vendors or documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="Document Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="business_registration">Business Registration</SelectItem>
                <SelectItem value="tax_id">Tax ID</SelectItem>
                <SelectItem value="government_id">Government ID</SelectItem>
                <SelectItem value="operating_license">Operating License</SelectItem>
                <SelectItem value="association_membership">Association Membership</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger>
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                <SelectItem value="5">Critical</SelectItem>
                <SelectItem value="4">High</SelectItem>
                <SelectItem value="3">Medium</SelectItem>
                <SelectItem value="2">Low</SelectItem>
                <SelectItem value="1">Minimal</SelectItem>
              </SelectContent>
            </Select>

            <div className="flex items-center text-sm text-gray-600">
              <Filter className="w-4 h-4 mr-2" />
              {filteredItems.length} of {queueItems.length} items
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Queue Items */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredItems.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No documents to review</h3>
              <p className="text-gray-600">
                {queueItems.length === 0 
                  ? "All documents have been processed" 
                  : "No documents match your current filters"
                }
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item) => (
            <Card key={item.queue_id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-1">
                          {getDocumentTypeDisplay(item.document_info?.document_type)}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {item.document_info?.original_filename}
                        </p>
                      </div>
                      {getPriorityBadge(item.priority)}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div className="flex items-center">
                        <Building2 className="w-4 h-4 text-gray-400 mr-2" />
                        <div>
                          <p className="font-medium text-gray-900">
                            {item.vendor_info?.business_name}
                          </p>
                          <p className="text-gray-600">{item.vendor_info?.email}</p>
                        </div>
                      </div>

                      <div className="flex items-center">
                        <User className="w-4 h-4 text-gray-400 mr-2" />
                        <div>
                          <p className="text-gray-600">Vendor ID</p>
                          <p className="font-mono text-gray-900">{item.vendor_id}</p>
                        </div>
                      </div>

                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 text-gray-400 mr-2" />
                        <div>
                          <p className="text-gray-600">Submitted</p>
                          <p className="text-gray-900">
                            {new Date(item.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-4 pt-4 border-t">
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span>Size: {(item.document_info?.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                        <span>•</span>
                        <span>Waiting {Math.floor((new Date() - new Date(item.created_at)) / (1000 * 60 * 60 * 24))} days</span>
                      </div>

                      <Button 
                        onClick={() => handleDocumentReview(item)}
                        size="sm"
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        Review Document
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default VerificationQueue;