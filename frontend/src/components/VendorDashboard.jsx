import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { 
  Plus, 
  Search, 
  Eye, 
  Edit, 
  Trash2, 
  Users, 
  CheckCircle, 
  Clock,
  Filter
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { vendorAPI } from '../services/api';
import VendorForm from './VendorForm';
import VendorCard from './VendorCard';

const VendorDashboard = () => {
  const [vendors, setVendors] = useState([]);
  const [filteredVendors, setFilteredVendors] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentView, setCurrentView] = useState('dashboard'); // dashboard, form, card
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [isCardFlipped, setIsCardFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadVendors();
  }, []);

  useEffect(() => {
    filterVendors();
  }, [vendors, searchTerm, statusFilter]);

  const loadVendors = async () => {
    try {
      const data = await mockAPI.getVendors();
      setVendors(data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load vendors",
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
        vendor.id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    if (statusFilter !== 'all') {
      filtered = filtered.filter(vendor => vendor.status === statusFilter);
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
    if (window.confirm('Are you sure you want to delete this vendor?')) {
      try {
        await mockAPI.deleteVendor(vendorId);
        toast({
          title: "Success",
          description: "Vendor deleted successfully"
        });
        loadVendors();
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
    loadVendors();
    setCurrentView('dashboard');
  };

  const handleFormCancel = () => {
    setCurrentView('dashboard');
    setSelectedVendor(null);
  };

  const getStats = () => {
    const total = vendors.length;
    const verified = vendors.filter(v => v.status === 'verified').length;
    const pending = vendors.filter(v => v.status === 'pending').length;
    
    return { total, verified, pending };
  };

  const stats = getStats();

  if (currentView === 'form') {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <VendorForm
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
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <Button 
              onClick={() => setCurrentView('dashboard')} 
              variant="outline"
            >
              ← Back to Dashboard
            </Button>
          </div>
          <div className="flex justify-center">
            <VendorCard
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
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Vendor ID Management</h1>
              <p className="text-gray-600 mt-1">Manage and generate vendor identification cards</p>
            </div>
            <Button onClick={handleCreateVendor} className="bg-teal-600 hover:bg-teal-700">
              <Plus className="w-5 h-5 mr-2" />
              Create New Vendor
            </Button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Users className="w-8 h-8 text-blue-500" />
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
                    <p className="text-sm text-gray-600">Total Vendors</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-8 h-8 text-green-500" />
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.verified}</p>
                    <p className="text-sm text-gray-600">Verified</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Clock className="w-8 h-8 text-yellow-500" />
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{stats.pending}</p>
                    <p className="text-sm text-gray-600">Pending</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Search and Filter */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                placeholder="Search vendors by name or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="all">All Status</option>
                <option value="verified">Verified</option>
                <option value="pending">Pending</option>
              </select>
            </div>
          </div>
        </div>

        {/* Vendors Table */}
        <Card>
          <CardHeader>
            <CardTitle>Vendors ({filteredVendors.length})</CardTitle>
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
                  {searchTerm || statusFilter !== 'all' 
                    ? 'Try adjusting your search or filter criteria' 
                    : 'Create your first vendor to get started'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && (
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
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Name</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Vendor ID</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Issue Date</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Status</th>
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
                        <td className="py-3 px-4 font-medium text-gray-900">{vendor.name}</td>
                        <td className="py-3 px-4 text-gray-600 font-mono">{vendor.id}</td>
                        <td className="py-3 px-4 text-gray-600">{vendor.issueDate}</td>
                        <td className="py-3 px-4">
                          <Badge variant={vendor.status === 'verified' ? 'default' : 'secondary'}>
                            {vendor.status.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex space-x-2">
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

export default VendorDashboard;