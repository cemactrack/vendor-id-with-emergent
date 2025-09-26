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
  Settings,
  Shield,
  Award,
  CreditCard
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { vendorAPI } from '../services/api';
import EnhancedVendorForm from './EnhancedVendorForm';
import ProfessionalVendorCard from './ProfessionalVendorCard';

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
      case 'verified': return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case 'pending': return <Clock className="w-5 h-5 text-amber-500" />;
      case 'expired': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'suspended': return <Ban className="w-5 h-5 text-red-600" />;
      default: return <Users className="w-5 h-5 text-blue-500" />;
    }
  };

  const getTemplateColor = (templateName) => {
    const template = templates[templateName];
    return template?.colors?.primary || '#16a34a';
  };

  const getTemplateIcon = (templateName) => {
    switch (templateName) {
      case 'premium': return <Award className="w-4 h-4" />;
      case 'executive': return <Shield className="w-4 h-4" />;
      default: return <CreditCard className="w-4 h-4" />;
    }
  };

  if (currentView === 'form') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 md:p-6">
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
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 md:p-6">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <Button 
              onClick={() => setCurrentView('dashboard')} 
              variant="outline"
              className="shadow-md hover:shadow-lg transition-shadow"
            >
              ← Back to Dashboard
            </Button>
          </div>
          <div className="flex justify-center">
            <ProfessionalVendorCard
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Professional Header */}
        <div className="mb-8">
          {/* Title Section */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 mb-6">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Professional Vendor ID Management</h1>
                  <p className="text-gray-600 mt-1">Industry-standard identification cards with advanced security features</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
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
                  className="shadow-md hover:shadow-lg transition-shadow"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  {importing ? 'Importing...' : 'Import CSV'}
                </Button>
                <Button 
                  onClick={handleExportCSV} 
                  variant="outline" 
                  size="sm"
                  className="shadow-md hover:shadow-lg transition-shadow"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export CSV
                </Button>
                <Button 
                  onClick={handleCreateVendor} 
                  className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 shadow-lg hover:shadow-xl transition-all"
                >
                  <Plus className="w-5 h-5 mr-2" />
                  Create New Vendor
                </Button>
              </div>
            </div>
          </div>

          {/* Enhanced Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            <Card className="shadow-lg border-0 bg-gradient-to-br from-blue-50 to-indigo-100">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                    <Users className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.total || 0}</p>
                    <p className="text-xs text-gray-600 font-medium">Total Vendors</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="shadow-lg border-0 bg-gradient-to-br from-emerald-50 to-green-100">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-emerald-500 rounded-lg flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.verified || 0}</p>
                    <p className="text-xs text-gray-600 font-medium">Verified</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="shadow-lg border-0 bg-gradient-to-br from-amber-50 to-yellow-100">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-amber-500 rounded-lg flex items-center justify-center">
                    <Clock className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.pending || 0}</p>
                    <p className="text-xs text-gray-600 font-medium">Pending</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="shadow-lg border-0 bg-gradient-to-br from-red-50 to-rose-100">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.expired || 0}</p>
                    <p className="text-xs text-gray-600 font-medium">Expired</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="shadow-lg border-0 bg-gradient-to-br from-gray-50 to-slate-100">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-600 rounded-lg flex items-center justify-center">
                    <Ban className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.suspended || 0}</p>
                    <p className="text-xs text-gray-600 font-medium">Suspended</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="shadow-lg border-0 bg-gradient-to-br from-orange-50 to-amber-100">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.expiring_soon || 0}</p>
                    <p className="text-xs text-gray-600 font-medium">Expiring Soon</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Professional Search and Filter */}
          <Card className="shadow-lg border-0 bg-white">
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <Input
                    placeholder="Search vendors..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 shadow-sm border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
                  />
                </div>
                
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="shadow-sm border-gray-300">
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
                  <SelectTrigger className="shadow-sm border-gray-300">
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
                  <SelectTrigger className="shadow-sm border-gray-300">
                    <SelectValue placeholder="All Cards" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Cards</SelectItem>
                    <SelectItem value="active">Active Cards</SelectItem>
                    <SelectItem value="expired">Expired Cards</SelectItem>
                  </SelectContent>
                </Select>
                
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setSearchTerm('');
                    setStatusFilter('all');
                    setTemplateFilter('all');
                    setExpiredFilter('all');
                  }}
                  className="shadow-sm border-gray-300 hover:bg-gray-50"
                >
                  Clear Filters
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Professional Vendors Table */}
        <Card className="shadow-xl border-0 bg-white">
          <CardHeader className="bg-gradient-to-r from-emerald-50 to-teal-50 border-b">
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <BarChart3 className="w-6 h-6 text-emerald-600" />
                <span className="text-xl font-bold text-gray-900">Professional Vendors ({filteredVendors.length})</span>
              </div>
              <Badge variant="outline" className="bg-white shadow-sm">
                Industry Standard View
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="text-center py-16">
                <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-emerald-600 mx-auto"></div>
                <p className="mt-6 text-gray-600 font-medium">Loading professional vendors...</p>
              </div>
            ) : filteredVendors.length === 0 ? (
              <div className="text-center py-16">
                <div className="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Users className="w-12 h-12 text-gray-400" />
                </div>
                <p className="text-xl text-gray-600 mb-2 font-medium">No vendors found</p>
                <p className="text-gray-500 mb-6">
                  {searchTerm || statusFilter !== 'all' || templateFilter !== 'all' || expiredFilter !== 'all'
                    ? 'Try adjusting your search or filter criteria' 
                    : 'Create your first professional vendor to get started'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && templateFilter === 'all' && expiredFilter === 'all' && (
                  <Button 
                    onClick={handleCreateVendor} 
                    className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 shadow-lg"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Create First Vendor
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="text-left py-4 px-6 font-semibold text-gray-900">Photo</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-900">Vendor Details</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-900">Contact Info</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-900">Organization</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-900">Status & Template</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-900">Validity Period</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-900">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredVendors.map((vendor, index) => (
                      <tr key={vendor.id} className={`border-b hover:bg-gray-50 transition-colors ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                        <td className="py-4 px-6">
                          <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-100 shadow-sm border border-gray-200">
                            {vendor.photo ? (
                              <img 
                                src={vendor.photo} 
                                alt={vendor.name}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-200 to-gray-300">
                                <Users className="w-6 h-6 text-gray-500" />
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <div>
                            <div className="font-bold text-gray-900 text-base">{vendor.name}</div>
                            <div className="text-sm text-gray-600 font-mono bg-gray-100 rounded px-2 py-1 inline-block mt-1">{vendor.id}</div>
                            {vendor.position && (
                              <div className="text-xs text-gray-500 mt-1 font-medium">{vendor.position}</div>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <div className="text-sm space-y-1">
                            {vendor.email && (
                              <div className="text-gray-700 flex items-center space-x-1">
                                <span className="text-gray-400">✉</span>
                                <span>{vendor.email}</span>
                              </div>
                            )}
                            {vendor.phone && (
                              <div className="text-gray-700 flex items-center space-x-1">
                                <span className="text-gray-400">☎</span>
                                <span>{vendor.phone}</span>
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <div className="text-sm">
                            {vendor.company && (
                              <div className="font-semibold text-gray-900">{vendor.company}</div>
                            )}
                            {vendor.department && (
                              <div className="text-gray-600">{vendor.department}</div>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex flex-col space-y-2">
                            <Badge 
                              variant={vendor.status === 'verified' ? 'default' : 
                                       vendor.status === 'expired' ? 'destructive' :
                                       vendor.status === 'suspended' ? 'destructive' : 'secondary'}
                              className="shadow-sm"
                            >
                              <div className="flex items-center space-x-1">
                                {getStatusIcon(vendor.status)}
                                <span className="ml-1 font-medium">{vendor.status.toUpperCase()}</span>
                              </div>
                            </Badge>
                            <Badge 
                              variant="outline" 
                              className="shadow-sm"
                              style={{ 
                                borderColor: getTemplateColor(vendor.template),
                                color: getTemplateColor(vendor.template)
                              }}
                            >
                              <div className="flex items-center space-x-1">
                                {getTemplateIcon(vendor.template)}
                                <span className="ml-1 font-medium">{vendor.template.toUpperCase()}</span>
                              </div>
                            </Badge>
                          </div>
                        </td>
                        <td className="py-4 px-6 text-sm">
                          <div className="space-y-1">
                            <div className="text-gray-700">
                              <span className="font-medium">Issued:</span> {vendor.issueDate}
                            </div>
                            {vendor.expiryDate && (
                              <div className={`${new Date(vendor.expiryDate) < new Date() ? 'text-red-600 font-semibold' : 'text-gray-700'}`}>
                                <span className="font-medium">Expires:</span> {vendor.expiryDate}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex space-x-1">
                            <Button
                              onClick={() => handleViewCard(vendor)}
                              size="sm"
                              variant="outline"
                              title="View Professional Card"
                              className="shadow-sm hover:shadow-md transition-shadow"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => handleEditVendor(vendor)}
                              size="sm"
                              variant="outline"
                              title="Edit Vendor"
                              className="shadow-sm hover:shadow-md transition-shadow"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => handleDeleteVendor(vendor.id)}
                              size="sm"
                              variant="outline"
                              title="Delete Vendor"
                              className="text-red-600 hover:text-red-700 hover:border-red-300 shadow-sm hover:shadow-md transition-all"
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