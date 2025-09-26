import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth token management
let authToken = null;

const setAuthToken = (token) => {
  authToken = token;
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      setAuthToken(null);
      localStorage.removeItem('vendor_ecosystem_token');
      localStorage.removeItem('vendor_ecosystem_user');
      window.location.href = '/login';
    }
    console.error('API Error:', error);
    throw error;
  }
);

export const vendorEcosystemAPI = {
  // Auth token management
  setAuthToken,

  // Authentication
  register: async (userData) => {
    const response = await apiClient.post('/auth/register', userData);
    return response;
  },

  login: async (email, password) => {
    const response = await apiClient.post('/auth/login', null, {
      params: { email, password }
    });
    return response;
  },

  // Vendor Profile Management
  createVendorProfile: async (profileData) => {
    const response = await apiClient.post('/vendors/profile', profileData);
    return response.profile;
  },

  getVendorProfile: async (vendorId) => {
    const response = await apiClient.get(`/vendors/profile/${vendorId}`);
    return response.profile;
  },

  getVendorDashboard: async () => {
    const response = await apiClient.get('/vendors/dashboard');
    return response.dashboard;
  },

  updateVendorProfile: async (vendorId, updateData) => {
    const response = await apiClient.put(`/vendors/profile/${vendorId}`, updateData);
    return response.profile;
  },

  // Document Management
  uploadDocument: async (documentData) => {
    const response = await apiClient.post('/vendors/documents', documentData);
    return response.document;
  },

  getVendorDocuments: async () => {
    const response = await apiClient.get('/vendors/documents');
    return response.documents;
  },

  // Service Listings
  createServiceListing: async (listingData) => {
    const response = await apiClient.post('/vendors/listings', listingData);
    return response.listing;
  },

  searchServiceListings: async (query = '', category = null, location = '', limit = 20, offset = 0) => {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (category) params.append('category', category);
    if (location) params.append('location', location);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    const response = await apiClient.get(`/vendors/listings/search?${params.toString()}`);
    return response;
  },

  // Verification Management (Admin)
  getPendingVerifications: async (limit = 50) => {
    const response = await apiClient.get(`/admin/verifications/pending?limit=${limit}`);
    return response.verifications;
  },

  updateVerificationStatus: async (verificationId, status, notes = null) => {
    const response = await apiClient.put(`/admin/verifications/${verificationId}/status`, {
      status,
      notes
    });
    return response;
  },

  // Fraud Reporting
  reportFraud: async (vendorId, reportType, description, evidenceFiles = []) => {
    const response = await apiClient.post('/fraud/report', {
      reported_vendor_id: vendorId,
      report_type: reportType,
      description,
      evidence_files: evidenceFiles
    });
    return response.report;
  },

  // Public Verification
  verifyVendorPublic: async (vendorId) => {
    const response = await apiClient.get(`/public/verify/${vendorId}`);
    return response.verification;
  },

  publicVendorSearch: async (query = '', category = null, country = null, verifiedOnly = true, limit = 20, offset = 0) => {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (category) params.append('category', category);
    if (country) params.append('country', country);
    if (verifiedOnly) params.append('verified_only', 'true');
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    const response = await apiClient.get(`/public/search?${params.toString()}`);
    return response;
  },

  // System Statistics
  getEcosystemStats: async () => {
    const response = await apiClient.get('/admin/stats');
    return response.stats;
  },

  // Legacy API endpoints for backward compatibility
  getVendors: async (search = '', status = 'all', template = 'all', expired = null, limit = 50, offset = 0) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status && status !== 'all') params.append('status', status);
    if (template && template !== 'all') params.append('template', template);
    if (expired !== null) params.append('expired', expired.toString());
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    const response = await apiClient.get(`/vendors?${params.toString()}`);
    return response.vendors || [];
  },

  createVendor: async (vendorData) => {
    const response = await apiClient.post('/vendors', vendorData);
    return response.vendor;
  },

  updateVendor: async (id, vendorData) => {
    const response = await apiClient.put(`/vendors/${id}`, vendorData);
    return response.vendor;
  },

  deleteVendor: async (id) => {
    await apiClient.delete(`/vendors/${id}`);
    return true;
  },

  // QR Code and Barcode (legacy)
  getQRCodeURL: (vendorId) => {
    return `${API}/qr-code/${vendorId}`;
  },

  getBarcodeURL: (vendorId) => {
    return `${API}/barcode/${vendorId}`;
  },

  // Photo upload
  uploadPhoto: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API}/upload/photo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': authToken ? `Bearer ${authToken}` : undefined
      },
      timeout: 60000,
    });
    return response.data.photoUrl;
  },

  // Templates
  getTemplates: async () => {
    const response = await apiClient.get('/templates');
    return response;
  },

  getTemplate: async (templateName) => {
    const response = await apiClient.get(`/templates/${templateName}`);
    return response;
  },

  // Enhanced card data
  getEnhancedCardData: async (vendorId) => {
    const response = await apiClient.get(`/vendors/${vendorId}/card-data`);
    return response;
  },

  // CSV Import/Export
  importCSV: async (file, template = 'standard') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('template', template);
    
    const response = await axios.post(`${API}/vendors/import/csv`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': authToken ? `Bearer ${authToken}` : undefined
      },
      timeout: 120000,
    });
    return response.data;
  },

  exportCSV: async () => {
    const response = await axios.get(`${API}/vendors/export/csv`, {
      responseType: 'blob',
      headers: {
        'Authorization': authToken ? `Bearer ${authToken}` : undefined
      }
    });
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'vendors.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};