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

  login: async (email, password, totpToken = null, backupCode = null) => {
    const params = new URLSearchParams();
    params.append('email', email);
    params.append('password', password);
    if (totpToken) params.append('totp_token', totpToken);
    if (backupCode) params.append('backup_code', backupCode);
    
    const response = await apiClient.post('/auth/login', null, { params });
    return response;
  },

  // Enhanced Authentication
  verifyEmail: async (token) => {
    const response = await apiClient.post('/auth/verify-email', { token });
    return response;
  },

  resendEmailVerification: async () => {
    const response = await apiClient.post('/auth/resend-verification');
    return response;
  },

  forgotPassword: async (email) => {
    const response = await apiClient.post('/auth/forgot-password', { email });
    return response;
  },

  resetPassword: async (token, newPassword) => {
    const response = await apiClient.post('/auth/reset-password', {
      token,
      new_password: newPassword
    });
    return response;
  },

  // Two-Factor Authentication
  setup2FA: async (password) => {
    const response = await apiClient.post('/auth/2fa/setup', { password });
    return response;
  },

  enable2FA: async (token) => {
    const response = await apiClient.post('/auth/2fa/enable', { token });
    return response;
  },

  disable2FA: async (password, token = null) => {
    const response = await apiClient.post('/auth/2fa/disable', {
      password,
      token
    });
    return response;
  },

  verify2FA: async (token) => {
    const response = await apiClient.post('/auth/2fa/verify', { token });
    return response;
  },

  // Security Management
  getSecurityInfo: async () => {
    const response = await apiClient.get('/auth/security/info');
    return response.security;
  },

  getSecurityEvents: async (limit = 20) => {
    const response = await apiClient.get(`/auth/security/events?limit=${limit}`);
    return response.events;
  },

  // Document Management
  uploadDocument: async (formData) => {
    const response = await apiClient.post('/vendors/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    return response;
  },

  getVendorDocuments: async () => {
    const response = await apiClient.get('/vendors/documents');
    return response.documents;
  },

  deleteDocument: async (documentId) => {
    const response = await apiClient.delete(`/vendors/documents/${documentId}`);
    return response;
  },

  getDocumentVerificationSummary: async () => {
    const response = await apiClient.get('/vendors/documents/summary');
    return response.summary;
  },

  // Admin Document Review Endpoints
  getVerificationQueue: async (limit = 50) => {
    const response = await apiClient.get(`/admin/verification-queue?limit=${limit}`);
    return response.queue;
  },

  getDocumentForReview: async (documentId) => {
    const response = await apiClient.get(`/admin/documents/${documentId}/review`);
    return response;
  },

  approveDocument: async (documentId, notes = '') => {
    const response = await apiClient.post(`/admin/documents/${documentId}/approve`);
    return response;
  },

  rejectDocument: async (documentId, reason) => {
    const formData = new FormData();
    formData.append('reason', reason);
    const response = await apiClient.post(`/admin/documents/${documentId}/reject`, formData);
    return response;
  },

  // Vendor ID Management
  getVendorIdInfo: async () => {
    const response = await apiClient.get('/vendors/vendor-id');
    return response.vendor_id;
  },

  requestPhysicalCard: async (shippingAddress) => {
    const response = await apiClient.post('/vendors/vendor-id/request-physical-card', {
      shipping_address: shippingAddress
    });
    return response;
  },
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