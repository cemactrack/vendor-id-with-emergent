import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { 
  Search, 
  Filter,
  MapPin, 
  Shield, 
  Star,
  Building2,
  Globe,
  QrCode,
  Eye,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { Link } from 'react-router-dom';

const PublicVendorSearch = () => {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [verifiedOnly, setVerifiedOnly] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalVendors, setTotalVendors] = useState(0);
  const [itemsPerPage] = useState(12);

  const businessCategories = [
    { value: 'all', label: 'All Categories' },
    { value: 'technology', label: 'Technology' },
    { value: 'manufacturing', label: 'Manufacturing' },
    { value: 'agriculture', label: 'Agriculture' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'education', label: 'Education' },
    { value: 'finance', label: 'Finance' },
    { value: 'retail', label: 'Retail' },
    { value: 'services', label: 'Services' },
    { value: 'construction', label: 'Construction' },
    { value: 'logistics', label: 'Logistics' },
    { value: 'food_beverage', label: 'Food & Beverage' },
    { value: 'automotive', label: 'Automotive' },
    { value: 'energy', label: 'Energy' },
    { value: 'real_estate', label: 'Real Estate' }
  ];

  const countries = [
    { value: 'all', label: 'All Countries' },
    { value: 'NG', label: 'Nigeria' },
    { value: 'CM', label: 'Cameroon' },
    { value: 'GH', label: 'Ghana' },
    { value: 'KE', label: 'Kenya' },
    { value: 'ZA', label: 'South Africa' },
    { value: 'US', label: 'United States' },
    { value: 'GB', label: 'United Kingdom' },
    { value: 'CA', label: 'Canada' }
  ];

  useEffect(() => {
    searchVendors();
  }, [searchQuery, selectedCategory, selectedCountry, verifiedOnly, currentPage]);

  const searchVendors = async () => {
    try {
      setLoading(true);
      const offset = (currentPage - 1) * itemsPerPage;
      const response = await vendorEcosystemAPI.publicVendorSearch(
        searchQuery,
        selectedCategory === 'all' ? null : selectedCategory,
        selectedCountry === 'all' ? null : selectedCountry,
        verifiedOnly,
        itemsPerPage,
        offset
      );
      
      setVendors(response.vendors || []);
      setTotalVendors(response.total || 0);
    } catch (error) {
      console.error('Search failed:', error);
      setVendors([]);
      setTotalVendors(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    searchVendors();
  };

  const getTrustScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrustScoreBadge = (score) => {
    if (score >= 80) return 'bg-green-100 text-green-800 border-green-200';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-red-100 text-red-800 border-red-200';
  };

  const totalPages = Math.ceil(totalVendors / itemsPerPage);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="text-center">
            <div className="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Shield className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold mb-4">Vendor Verification Directory</h1>
            <p className="text-xl text-emerald-100 max-w-2xl mx-auto">
              Find verified, trusted vendors from around the world. All vendors are thoroughly verified for your security.
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search and Filters */}
        <Card className="mb-8 shadow-lg">
          <CardContent className="pt-6">
            <form onSubmit={handleSearch} className="space-y-6">
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  type="text"
                  placeholder="Search vendors by name or business..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 h-12 text-lg"
                />
              </div>

              {/* Filters */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category
                  </label>
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="All Categories" />
                    </SelectTrigger>
                    <SelectContent>
                      {businessCategories.map((category) => (
                        <SelectItem key={category.value} value={category.value}>
                          {category.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Country
                  </label>
                  <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="All Countries" />
                    </SelectTrigger>
                    <SelectContent>
                      {countries.map((country) => (
                        <SelectItem key={country.value} value={country.value}>
                          {country.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-end">
                  <label className="flex items-center space-x-2 h-12">
                    <input
                      type="checkbox"
                      checked={verifiedOnly}
                      onChange={(e) => setVerifiedOnly(e.target.checked)}
                      className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                    />
                    <span className="text-sm font-medium text-gray-700">Verified vendors only</span>
                  </label>
                </div>
              </div>

              <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 h-12 text-lg">
                <Search className="w-5 h-5 mr-2" />
                Search Vendors
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Results Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {loading ? 'Searching...' : `${totalVendors} Vendors Found`}
            </h2>
            <p className="text-gray-600">
              {searchQuery && `Results for "${searchQuery}"`}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
          </div>
        </div>

        {/* Vendor Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, index) => (
              <Card key={index} className="animate-pulse">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    <div className="h-3 bg-gray-200 rounded w-full"></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : vendors.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {vendors.map((vendor) => (
              <Card key={vendor.vendor_id} className="hover:shadow-lg transition-shadow duration-200">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
                      {vendor.business_name?.charAt(0)?.toUpperCase()}
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${getTrustScoreColor(vendor.trust_score)}`}>
                        {Math.round(vendor.trust_score)}
                      </div>
                      <div className="text-xs text-gray-500">Trust Score</div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <h3 className="font-semibold text-gray-900 text-lg leading-tight">
                        {vendor.business_name}
                      </h3>
                      <p className="text-gray-600 text-sm capitalize">
                        {vendor.category?.replace('_', ' ')}
                      </p>
                    </div>

                    <div className="flex items-center text-gray-600">
                      <MapPin className="w-4 h-4 mr-1" />
                      <span className="text-sm truncate">{vendor.location}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <Badge className={getTrustScoreBadge(vendor.trust_score)}>
                        <Shield className="w-3 h-3 mr-1" />
                        Level {vendor.verification_level}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {vendor.verified_since && 
                          `Verified ${new Date(vendor.verified_since).toLocaleDateString()}`
                        }
                      </span>
                    </div>

                    <div className="pt-2 border-t">
                      <div className="flex justify-between items-center">
                        <Link 
                          to={`/verify/${vendor.vendor_id}`}
                          className="text-emerald-600 hover:text-emerald-800 text-sm font-medium flex items-center"
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          View Profile
                        </Link>
                        <button className="text-gray-400 hover:text-gray-600">
                          <QrCode className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="text-center py-12">
            <CardContent>
              <Building2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No vendors found</h3>
              <p className="text-gray-600 mb-4">
                Try adjusting your search criteria or browse all verified vendors
              </p>
              <Button 
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategory('');
                  setSelectedCountry('');
                  setCurrentPage(1);
                }}
                variant="outline"
              >
                Clear Filters
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center space-x-4 mt-8">
            <Button
              variant="outline"
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1 || loading}
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Previous
            </Button>
            
            <div className="flex space-x-2">
              {[...Array(Math.min(5, totalPages))].map((_, index) => {
                const pageNum = Math.max(1, currentPage - 2) + index;
                if (pageNum > totalPages) return null;
                
                return (
                  <Button
                    key={pageNum}
                    variant={pageNum === currentPage ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCurrentPage(pageNum)}
                    disabled={loading}
                  >
                    {pageNum}
                  </Button>
                );
              })}
            </div>
            
            <Button
              variant="outline"
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages || loading}
            >
              Next
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        )}

        {/* Stats Footer */}
        <div className="mt-12 bg-white rounded-lg shadow-sm border p-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Join the Trusted Vendor Ecosystem
            </h3>
            <p className="text-gray-600 mb-4">
              Over {totalVendors} verified vendors from around the world trust our verification platform
            </p>
            <div className="flex justify-center space-x-8 text-sm text-gray-600">
              <div className="flex items-center">
                <Shield className="w-4 h-4 mr-2 text-emerald-600" />
                Verified Profiles
              </div>
              <div className="flex items-center">
                <Globe className="w-4 h-4 mr-2 text-blue-600" />
                Global Reach
              </div>
              <div className="flex items-center">
                <Star className="w-4 h-4 mr-2 text-yellow-600" />
                Trust Scoring
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PublicVendorSearch;