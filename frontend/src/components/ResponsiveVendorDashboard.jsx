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
  Shield,
  Award,
  CreditCard,
  Grid3X3,
  List,
  Settings,
  TrendingUp,
  Activity,
  Zap
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { vendorAPI } from '../services/api';
import EnhancedVendorForm from './EnhancedVendorForm';
import ResponsiveProfessionalCard from './ResponsiveProfessionalCard';

const ResponsiveVendorDashboard = () => {
  const [vendors, setVendors] = useState([]);
  const [filteredVendors, setFilteredVendors] = useState([]);
  const [stats, setStats] = useState({});
  const [templates, setTemplates] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [templateFilter, setTemplateFilter] = useState('all');
  const [expiredFilter, setExpiredFilter] = useState('all');
  const [currentView, setCurrentView] = useState('dashboard');
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'grid'
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [isCardFlipped, setIsCardFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const fileInputRef = useRef(null);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    filterVendors();
  }, [vendors, searchTerm, statusFilter, templateFilter, expiredFilter]);

  const checkMobile = () => {
    setIsMobile(window.innerWidth < 768);
    if (window.innerWidth < 768) {
      setViewMode('grid'); // Auto-switch to grid on mobile
    }
  };

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
    const icons = {
      verified: <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-500" />,
      pending: <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-amber-500" />,
      expired: <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5 text-red-500" />,
      suspended: <Ban className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />,
      default: <Users className="w-4 h-4 sm:w-5 sm:h-5 text-blue-500" />
    };
    return icons[status] || icons.default;
  };

  const getTemplateColor = (templateName) => {
    const template = templates[templateName];
    return template?.colors?.primary || '#16a34a';
  };

  const getTemplateIcon = (templateName) => {
    const icons = {
      premium: <Award className="w-3 h-3 sm:w-4 sm:h-4" />,
      executive: <Shield className="w-3 h-3 sm:w-4 sm:h-4" />,
      default: <CreditCard className="w-3 h-3 sm:w-4 sm:h-4" />
    };
    return icons[templateName] || icons.default;
  };

  // Mobile-optimized stats cards
  const ResponsiveStatsGrid = () => (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 mb-6">
      {[
        { key: 'total', label: 'Total', icon: Users, color: 'blue', gradient: 'from-blue-500 to-indigo-600' },
        { key: 'verified', label: 'Verified', icon: CheckCircle, color: 'emerald', gradient: 'from-emerald-500 to-green-600' },
        { key: 'pending', label: 'Pending', icon: Clock, color: 'amber', gradient: 'from-amber-500 to-yellow-600' },
        { key: 'expired', label: 'Expired', icon: AlertTriangle, color: 'red', gradient: 'from-red-500 to-rose-600' },
        { key: 'suspended', label: 'Suspended', icon: Ban, color: 'gray', gradient: 'from-gray-500 to-slate-600' },
        { key: 'expiring_soon', label: 'Expiring', icon: Calendar, color: 'orange', gradient: 'from-orange-500 to-amber-600' }
      ].map(({ key, label, icon: Icon, color, gradient }) => (
        <Card key={key} className="shadow-lg border-0 bg-gradient-to-br from-white to-gray-50 hover:shadow-xl transition-all duration-300 hover:scale-105 cursor-pointer group">
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className={`w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br ${gradient} rounded-lg flex items-center justify-center shadow-md group-hover:scale-110 transition-transform duration-300`}>
                <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-lg sm:text-2xl font-bold text-gray-900 leading-none">{stats[key] || 0}</p>
                <p className="text-xs sm:text-sm text-gray-600 font-medium truncate">{label}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  // Mobile-optimized filters
  const ResponsiveFilters = () => (
    <Card className="shadow-lg border-0 bg-white mb-6">
      <CardContent className="p-4 sm:p-6">
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              placeholder="Search vendors..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 shadow-sm border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 text-base"
            />
          </div>
          
          {/* Filter row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="shadow-sm border-gray-300">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="verified">✅ Verified</SelectItem>
                <SelectItem value="pending">⏳ Pending</SelectItem>
                <SelectItem value="expired">❌ Expired</SelectItem>
                <SelectItem value="suspended">🚫 Suspended</SelectItem>
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
                <SelectItem value="active">🟢 Active Cards</SelectItem>
                <SelectItem value="expired">🔴 Expired Cards</SelectItem>
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
              <Filter className="w-4 h-4 mr-2" />
              Clear
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  // Grid view for mobile
  const GridView = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
      {filteredVendors.map((vendor) => (
        <Card key={vendor.id} className="shadow-lg border-0 bg-white hover:shadow-xl transition-all duration-300 hover:scale-105 group">
          <CardContent className="p-4">
            <div className="space-y-3">
              {/* Header */}
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 rounded-lg overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 shadow-sm border border-gray-200 flex-shrink-0">
                  {vendor.photo ? (
                    <img 
                      src={vendor.photo} 
                      alt={vendor.name}
                      className="w-full h-full object-cover transition-all duration-300 group-hover:brightness-110"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Users className="w-6 h-6 text-gray-500" />
                    </div>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-bold text-gray-900 text-sm truncate">{vendor.name}</h3>
                  <p className="text-xs text-gray-600 font-mono bg-gray-100 rounded px-2 py-1 inline-block mt-1">{vendor.id}</p>
                </div>
              </div>
              
              {/* Details */}
              <div className="space-y-2 text-xs">
                {vendor.company && (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-blue-100 rounded flex items-center justify-center flex-shrink-0">
                      <div className="w-2 h-2 bg-blue-500 rounded"></div>
                    </div>
                    <span className="text-gray-700 font-medium truncate">{vendor.company}</span>
                  </div>
                )}
                {vendor.email && (
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-400">📧</span>
                    <span className="text-gray-600 truncate">{vendor.email}</span>
                  </div>
                )}
                {vendor.phone && (
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-400">📱</span>
                    <span className="text-gray-600">{vendor.phone}</span>
                  </div>
                )}
              </div>
              
              {/* Status and Template */}
              <div className="flex space-x-2">
                <Badge 
                  variant={vendor.status === 'verified' ? 'default' : 
                           vendor.status === 'expired' ? 'destructive' :
                           vendor.status === 'suspended' ? 'destructive' : 'secondary'}
                  className="text-xs shadow-sm"
                >
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(vendor.status)}
                    <span className="font-medium">{vendor.status.toUpperCase()}</span>
                  </div>
                </Badge>
                
                <Badge 
                  variant="outline" 
                  className="text-xs shadow-sm"
                  style={{ 
                    borderColor: getTemplateColor(vendor.template),
                    color: getTemplateColor(vendor.template)
                  }}
                >
                  <div className="flex items-center space-x-1">
                    {getTemplateIcon(vendor.template)}
                    <span className="font-medium">{vendor.template.toUpperCase()}</span>
                  </div>
                </Badge>
              </div>
              
              {/* Dates */}
              <div className="text-xs text-gray-600 space-y-1">
                <div>Issued: {vendor.issueDate}</div>
                {vendor.expiryDate && (
                  <div className={new Date(vendor.expiryDate) < new Date() ? 'text-red-600 font-semibold' : ''}>
                    Expires: {vendor.expiryDate}
                  </div>
                )}
              </div>
              
              {/* Actions */}
              <div className="flex space-x-1 pt-2 border-t border-gray-100">
                <Button
                  onClick={() => handleViewCard(vendor)}
                  size="sm"
                  variant="outline"
                  className="flex-1 text-xs shadow-sm hover:shadow-md transition-all"
                >
                  <Eye className="w-3 h-3 mr-1" />
                  View
                </Button>
                <Button
                  onClick={() => handleEditVendor(vendor)}
                  size="sm"
                  variant="outline"
                  className="flex-1 text-xs shadow-sm hover:shadow-md transition-all"
                >
                  <Edit className="w-3 h-3 mr-1" />
                  Edit
                </Button>
                <Button
                  onClick={() => handleDeleteVendor(vendor.id)}
                  size="sm"
                  variant="outline"
                  className="text-red-600 hover:text-red-700 hover:border-red-300 shadow-sm hover:shadow-md transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  // Enhanced table view
  const TableView = () => (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b">
          <tr>
            <th className="text-left py-4 px-6 font-semibold text-gray-900">Vendor</th>
            <th className="text-left py-4 px-6 font-semibold text-gray-900 hidden sm:table-cell">Contact</th>
            <th className="text-left py-4 px-6 font-semibold text-gray-900 hidden md:table-cell">Organization</th>
            <th className="text-left py-4 px-6 font-semibold text-gray-900">Status</th>
            <th className="text-left py-4 px-6 font-semibold text-gray-900 hidden lg:table-cell">Validity</th>
            <th className="text-left py-4 px-6 font-semibold text-gray-900">Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredVendors.map((vendor, index) => (
            <tr key={vendor.id} className={`border-b hover:bg-gray-50/50 transition-colors duration-200 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'}`}>
              <td className="py-4 px-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg overflow-hidden bg-gray-100 shadow-sm border border-gray-200 flex-shrink-0">
                    {vendor.photo ? (
                      <img 
                        src={vendor.photo} 
                        alt={vendor.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-200 to-gray-300">
                        <Users className="w-5 h-5 text-gray-500" />
                      </div>
                    )}
                  </div>
                  <div className="min-w-0">
                    <div className="font-bold text-gray-900 text-sm sm:text-base truncate">{vendor.name}</div>
                    <div className="text-xs sm:text-sm text-gray-600 font-mono bg-gray-100 rounded px-2 py-1 inline-block mt-1">{vendor.id}</div>
                    {vendor.position && (
                      <div className="text-xs text-gray-500 mt-1 font-medium hidden sm:block">{vendor.position}</div>
                    )}
                  </div>
                </div>
              </td>
              
              <td className="py-4 px-6 hidden sm:table-cell">
                <div className="text-sm space-y-1">
                  {vendor.email && (
                    <div className="text-gray-700 flex items-center space-x-1">
                      <span className="text-gray-400">📧</span>
                      <span className="truncate">{vendor.email}</span>
                    </div>
                  )}
                  {vendor.phone && (
                    <div className="text-gray-700 flex items-center space-x-1">
                      <span className="text-gray-400">📱</span>
                      <span>{vendor.phone}</span>
                    </div>
                  )}
                </div>
              </td>
              
              <td className="py-4 px-6 hidden md:table-cell">
                <div className="text-sm">
                  {vendor.company && (
                    <div className="font-semibold text-gray-900 truncate">{vendor.company}</div>
                  )}
                  {vendor.department && (
                    <div className="text-gray-600 truncate">{vendor.department}</div>
                  )}
                </div>
              </td>
              
              <td className="py-4 px-6">
                <div className="flex flex-col space-y-2">
                  <Badge 
                    variant={vendor.status === 'verified' ? 'default' : 
                             vendor.status === 'expired' ? 'destructive' :
                             vendor.status === 'suspended' ? 'destructive' : 'secondary'}
                    className="shadow-sm w-fit"
                  >
                    <div className="flex items-center space-x-1">
                      {getStatusIcon(vendor.status)}
                      <span className="ml-1 font-medium text-xs">{vendor.status.toUpperCase()}</span>
                    </div>
                  </Badge>
                  <Badge 
                    variant="outline" 
                    className="shadow-sm w-fit"
                    style={{ 
                      borderColor: getTemplateColor(vendor.template),
                      color: getTemplateColor(vendor.template)
                    }}
                  >
                    <div className="flex items-center space-x-1">
                      {getTemplateIcon(vendor.template)}
                      <span className="ml-1 font-medium text-xs">{vendor.template.toUpperCase()}</span>
                    </div>
                  </Badge>
                </div>
              </td>
              
              <td className="py-4 px-6 text-sm hidden lg:table-cell">
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
                    className="shadow-sm hover:shadow-md transition-all"
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button
                    onClick={() => handleEditVendor(vendor)}
                    size="sm"
                    variant="outline"
                    title="Edit Vendor"
                    className="shadow-sm hover:shadow-md transition-all hidden sm:inline-flex"
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    onClick={() => handleDeleteVendor(vendor.id)}
                    size="sm"
                    variant="outline"
                    title="Delete Vendor"
                    className="text-red-600 hover:text-red-700 hover:border-red-300 shadow-sm hover:shadow-md transition-all hidden sm:inline-flex"
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
  );

  if (currentView === 'form') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 sm:p-6">
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
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 sm:p-6">
        <div className="max-w-6xl mx-auto">
          <div className="mb-4 sm:mb-6">
            <Button 
              onClick={() => setCurrentView('dashboard')} 
              variant="outline"
              className="shadow-md hover:shadow-lg transition-all"
            >
              ← Back to Dashboard
            </Button>
          </div>
          <div className="flex justify-center">
            <ResponsiveProfessionalCard
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-3 sm:p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Enhanced Mobile-First Header */}
        <div className="mb-6 sm:mb-8">
          {/* Title Section */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-4 sm:p-6 mb-4 sm:mb-6">
            <div className="flex flex-col space-y-4 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
              <div className="flex items-center space-x-3 sm:space-x-4">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900">Professional Vendor ID</h1>
                  <p className="text-sm sm:text-base text-gray-600 mt-1">Industry-standard identification system</p>
                </div>
              </div>
              
              <div className="flex flex-wrap gap-2 sm:gap-3">
                {/* Mobile-optimized action buttons */}
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
                  size={isMobile ? "sm" : "default"}
                  className="shadow-md hover:shadow-lg transition-all flex-1 sm:flex-none"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  {importing ? 'Importing...' : (isMobile ? 'Import' : 'Import CSV')}
                </Button>
                <Button 
                  onClick={handleExportCSV} 
                  variant="outline" 
                  size={isMobile ? "sm" : "default"}
                  className="shadow-md hover:shadow-lg transition-all flex-1 sm:flex-none"
                >
                  <Download className="w-4 h-4 mr-2" />
                  {isMobile ? 'Export' : 'Export CSV'}
                </Button>
                <Button 
                  onClick={handleCreateVendor} 
                  className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 shadow-lg hover:shadow-xl transition-all flex-1 sm:flex-none"
                  size={isMobile ? "sm" : "default"}
                >
                  <Plus className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                  {isMobile ? 'New' : 'Create New Vendor'}
                </Button>
              </div>
            </div>
          </div>

          {/* Responsive Stats */}
          <ResponsiveStatsGrid />

          {/* Responsive Filters */}
          <ResponsiveFilters />
        </div>

        {/* Enhanced Vendors Display */}
        <Card className="shadow-xl border-0 bg-white">
          <CardHeader className="bg-gradient-to-r from-emerald-50 to-teal-50 border-b">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-3 sm:space-y-0">
              <CardTitle className="flex items-center space-x-3">
                <BarChart3 className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-600" />
                <span className="text-lg sm:text-xl font-bold text-gray-900">
                  Professional Vendors ({filteredVendors.length})
                </span>
              </CardTitle>
              
              <div className="flex items-center space-x-2">
                <Badge variant="outline" className="bg-white shadow-sm">
                  {viewMode === 'grid' ? '🔲 Grid View' : '📋 Table View'}
                </Badge>
                {!isMobile && (
                  <div className="flex rounded-lg border border-gray-200 bg-white p-1">
                    <Button
                      onClick={() => setViewMode('table')}
                      variant={viewMode === 'table' ? 'default' : 'ghost'}
                      size="sm"
                      className="h-8"
                    >
                      <List className="w-4 h-4" />
                    </Button>
                    <Button
                      onClick={() => setViewMode('grid')}
                      variant={viewMode === 'grid' ? 'default' : 'ghost'}
                      size="sm"
                      className="h-8"
                    >
                      <Grid3X3 className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="p-0">
            {loading ? (
              <div className="text-center py-12 sm:py-16">
                <div className="relative mx-auto mb-6">
                  <div className="animate-spin rounded-full h-12 w-12 sm:h-16 sm:w-16 border-4 border-emerald-200 border-t-emerald-600 mx-auto"></div>
                  <div className="absolute inset-0 rounded-full bg-emerald-50 animate-ping opacity-75"></div>
                </div>
                <p className="text-gray-600 font-medium animate-pulse">Loading professional vendors...</p>
              </div>
            ) : filteredVendors.length === 0 ? (
              <div className="text-center py-12 sm:py-16 px-4">
                <div className="w-20 h-20 sm:w-24 sm:h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Users className="w-10 h-10 sm:w-12 sm:h-12 text-gray-400" />
                </div>
                <p className="text-lg sm:text-xl text-gray-600 mb-2 font-medium">No vendors found</p>
                <p className="text-gray-500 mb-6 text-sm sm:text-base">
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
              <div className={`p-4 sm:p-6 ${viewMode === 'grid' ? '' : 'p-0'}`}>
                {viewMode === 'grid' ? <GridView /> : <TableView />}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ResponsiveVendorDashboard;