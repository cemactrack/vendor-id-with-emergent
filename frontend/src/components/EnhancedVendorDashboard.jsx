import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  Plus, 
  Search, 
  Eye, 
  Edit, 
  Trash2, 
  Users, 
  CheckCircle, 
  Clock,
  Filter,
  Download,
  Upload,
  AlertTriangle,
  Ban,
  FileSpreadsheet,
  BarChart3,
  Calendar,
  Settings
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { vendorAPI } from '../services/api';
import EnhancedVendorForm from './EnhancedVendorForm';
import EnhancedVendorCard from './EnhancedVendorCard';

const EnhancedVendorDashboard = () => {
  const [vendors, setVendors] = useState([]);
  const [filteredVendors, setFilteredVendors] = useState([]);
  const [stats, setStats] = useState({});
  const [templates, setTemplates] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [templateFilter, setTemplateFilter] = useState('all');
  const [expiredFilter, setExpiredFilter] = useState('all');
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [isCardFlipped, setIsCardFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef(null);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterVendors();
  }, [vendors, searchTerm, statusFilter, templateFilter, expiredFilter]);

  const loadData = async () => {
    try {
      const [vendorsData, statsData, templatesData] = await Promise.all([
        vendorAPI.getVendors(),
        vendorAPI.getVendorStats(),
        vendorAPI.getTemplates()
      ]);
      
      setVendors(vendorsData);
      setStats(statsData);
      setTemplates(templatesData);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const filterVendors = () => {
    let filtered = vendors;
    
    if (searchTerm) {
      filtered = filtered.filter(vendor => 
        vendor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        vendor.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (vendor.company && vendor.company.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (vendor.email && vendor.email.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    if (statusFilter !== 'all') {
      filtered = filtered.filter(vendor => vendor.status === statusFilter);
    }
    
    if (templateFilter !== 'all') {
      filtered = filtered.filter(vendor => vendor.template === templateFilter);
    }
    
    if (expiredFilter !== 'all') {
      const now = new Date();
      filtered = filtered.filter(vendor => {
        if (!vendor.expiryDate) return expiredFilter === 'active';
        const expiryDate = new Date(vendor.expiryDate);
        return expiredFilter === 'expired' ? expiryDate < now : expiryDate >= now;
      });
    }
    
    setFilteredVendors(filtered);
  };

  const handleCreateVendor = () => {
    setSelectedVendor(null);
    setCurrentView('form');
  };

  const handleEditVendor = (vendor) => {
    setSelectedVendor(vendor);
    setCurrentView('form');
  };

  const handleViewCard = (vendor) => {
    setSelectedVendor(vendor);
    setIsCardFlipped(false);
    setCurrentView('card');
  };

  const handleDeleteVendor = async (vendorId) => {
    if (window.confirm('Are you sure you want to delete this vendor? This action cannot be undone.')) {
      try {
        await vendorAPI.deleteVendor(vendorId);
        toast({
          title: "Success",
          description: "Vendor deleted successfully"
        });
        loadData();
      } catch (error) {
        toast({
          title: "Error",
          description: "Failed to delete vendor",
          variant: "destructive"
        });
      }
    }
  };

  const handleFormSave = (vendor) => {
    loadData();
    setCurrentView('dashboard');
  };

  const handleFormCancel = () => {
    setCurrentView('dashboard');
    setSelectedVendor(null);
  };

  const handleImportCSV = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      toast({
        title: "Invalid file",
        description: "Please select a CSV file",
        variant: "destructive"
      });
      return;
    }

    setImporting(true);
    try {
      const result = await vendorAPI.importCSV(file);
      toast({
        title: "Import completed",
        description: `Created ${result.total_created} vendors with ${result.total_errors} errors`
      });
      
      if (result.total_errors > 0) {
        console.log('Import errors:', result.errors);
      }
      
      loadData();
    } catch (error) {
      toast({
        title: "Import failed",
        description: error.response?.data?.detail || "Failed to import vendors",
        variant: "destructive"
      });
    } finally {
      setImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleExportCSV = async () => {
    try {
      await vendorAPI.exportCSV();
      toast({
        title: "Export started",
        description: "CSV file download initiated"
      });
    } catch (error) {
      toast({
        title: "Export failed",
        description: "Failed to export vendors",
        variant: "destructive"
      });
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'verified': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'pending': return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'expired': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'suspended': return <Ban className="w-5 h-5 text-red-500" />;
      default: return <Users className="w-5 h-5 text-blue-500" />;
    }
  };

  const getTemplateColor = (templateName) => {
    const template = templates[templateName];
    return template?.colors?.primary || '#16a34a';
  };

  if (currentView === 'form') {
    return (
      <div className="min-h-screen bg-gray-50 p-4 md:p-6">
        <div className="max-w-6xl mx-auto">
          <EnhancedVendorForm
            vendor={selectedVendor}
            onSave={handleFormSave}
            onCancel={handleFormCancel}
          />
        </div>
      </div>
    );
  }

  if (currentView === 'card' && selectedVendor) {
    return (
      <div className="min-h-screen bg-gray-50 p-4 md:p-6">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <Button 
              onClick={() => setCurrentView('dashboard')} 
              variant="outline"
            >
              ← Back to Dashboard
            </Button>
          </div>
          <div className="flex justify-center">
            <EnhancedVendorCard
              vendor={selectedVendor}
              isFlipped={isCardFlipped}
              onFlip={() => setIsCardFlipped(!isCardFlipped)}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Enhanced Header */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-6 gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Enhanced Vendor ID Management</h1>
              <p className="text-gray-600 mt-1">Manage vendor identification cards with advanced features</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleImportCSV}
                className="hidden"
              />
              <Button 
                onClick={() => fileInputRef.current?.click()}
                variant="outline"
                disabled={importing}
                size="sm"
              >
                <Upload className="w-4 h-4 mr-2" />
                {importing ? 'Importing...' : 'Import CSV'}
              </Button>
              <Button onClick={handleExportCSV} variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
              <Button onClick={handleCreateVendor} className="bg-teal-600 hover:bg-teal-700">
                <Plus className="w-5 h-5 mr-2" />
                Create New Vendor
              </Button>
            </div>
          </div>

          {/* Enhanced Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Users className="w-6 h-6 text-blue-500" />
                  <div>
                    <p className="text-xl font-bold text-gray-900">{stats.total || 0}</p>
                    <p className="text-xs text-gray-600">Total</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-6 h-6 text-green-500" />
                  <div>
                    <p className="text-xl font-bold text-gray-900">{stats.verified || 0}</p>
                    <p className="text-xs text-gray-600">Verified</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Clock className="w-6 h-6 text-yellow-500" />
                  <div>
                    <p className="text-xl font-bold text-gray-900">{stats.pending || 0}</p>
                    <p className="text-xs text-gray-600">Pending</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-6 h-6 text-red-500" />
                  <div>
                    <p className="text-xl font-bold text-gray-900">{stats.expired || 0}</p>
                    <p className="text-xs text-gray-600">Expired</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Ban className="w-6 h-6 text-red-600" />
                  <div>
                    <p className="text-xl font-bold text-gray-900">{stats.suspended || 0}</p>
                    <p className="text-xs text-gray-600">Suspended</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Calendar className="w-6 h-6 text-orange-500" />
                  <div>
                    <p className="text-xl font-bold text-gray-900">{stats.expiring_soon || 0}</p>
                    <p className="text-xs text-gray-600">Expiring Soon</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Enhanced Search and Filter */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                placeholder="Search vendors..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="verified">Verified</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={templateFilter} onValueChange={setTemplateFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Templates" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Templates</SelectItem>
                {Object.entries(templates).map(([key, template]) => (
                  <SelectItem key={key} value={key}>
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: template.colors?.primary || '#16a34a' }}
                      ></div>
                      <span>{template.name}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={expiredFilter} onValueChange={setExpiredFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Cards" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Cards</SelectItem>
                <SelectItem value="active">Active Cards</SelectItem>
                <SelectItem value="expired">Expired Cards</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" onClick={() => {
              setSearchTerm('');
              setStatusFilter('all');
              setTemplateFilter('all');
              setExpiredFilter('all');
            }}>
              Clear Filters
            </Button>
          </div>
        </div>

        {/* Enhanced Vendors Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Vendors ({filteredVendors.length})</span>
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-gray-500" />
                <span className="text-sm text-gray-500">Enhanced View</span>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading vendors...</p>
              </div>
            ) : filteredVendors.length === 0 ? (
              <div className="text-center py-8">
                <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-lg text-gray-600 mb-2">No vendors found</p>
                <p className="text-gray-500 mb-4">
                  {searchTerm || statusFilter !== 'all' || templateFilter !== 'all' || expiredFilter !== 'all'
                    ? 'Try adjusting your search or filter criteria' 
                    : 'Create your first vendor to get started'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && templateFilter === 'all' && expiredFilter === 'all' && (
                  <Button onClick={handleCreateVendor} className="bg-teal-600 hover:bg-teal-700">
                    <Plus className="w-4 h-4 mr-2" />
                    Create First Vendor
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Photo</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Vendor Details</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Contact Info</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Company</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Status & Template</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Dates</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredVendors.map((vendor) => (
                      <tr key={vendor.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div className="w-10 h-10 rounded-full overflow-hidden bg-gray-200">
                            {vendor.photo ? (
                              <img 
                                src={vendor.photo} 
                                alt={vendor.name}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <Users className="w-5 h-5 text-gray-400" />
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div>
                            <div className="font-medium text-gray-900">{vendor.name}</div>
                            <div className="text-sm text-gray-600 font-mono">{vendor.id}</div>
                            {vendor.position && (
                              <div className="text-xs text-gray-500">{vendor.position}</div>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="text-sm">
                            {vendor.email && (
                              <div className="text-gray-600">{vendor.email}</div>
                            )}
                            {vendor.phone && (
                              <div className="text-gray-600">{vendor.phone}</div>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="text-sm">
                            {vendor.company && (
                              <div className="font-medium text-gray-900">{vendor.company}</div>
                            )}
                            {vendor.department && (
                              <div className="text-gray-600">{vendor.department}</div>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-col space-y-1">
                            <Badge 
                              variant={vendor.status === 'verified' ? 'default' : 
                                       vendor.status === 'expired' ? 'destructive' :
                                       vendor.status === 'suspended' ? 'destructive' : 'secondary'}
                            >
                            {getStatusIcon(vendor.status)}
                            <span className="ml-1">{vendor.status.toUpperCase()}</span>
                            </Badge>
                            <Badge 
                              variant="outline" 
                              style={{ 
                                borderColor: getTemplateColor(vendor.template),
                                color: getTemplateColor(vendor.template)
                              }}
                            >
                              {vendor.template.toUpperCase()}
                            </Badge>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          <div>Issue: {vendor.issueDate}</div>
                          {vendor.expiryDate && (
                            <div className={new Date(vendor.expiryDate) < new Date() ? 'text-red-600' : ''}>
                              Expires: {vendor.expiryDate}
                            </div>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex space-x-1">
                            <Button
                              onClick={() => handleViewCard(vendor)}
                              size="sm"
                              variant="outline"
                              title="View Card"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => handleEditVendor(vendor)}
                              size="sm"
                              variant="outline"
                              title="Edit Vendor"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => handleDeleteVendor(vendor.id)}
                              size="sm"
                              variant="outline"
                              title="Delete Vendor"
                              className="text-red-600 hover:text-red-700 hover:border-red-300"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EnhancedVendorDashboard;