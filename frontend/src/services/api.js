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

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    throw error;
  }
);

export const vendorAPI = {
  // Get all vendors with enhanced filtering
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

  // Get vendor statistics
  getVendorStats: async () => {
    return await apiClient.get('/vendors/stats');
  },

  // Get expiring vendors
  getExpiringVendors: async (days = 30) => {
    const response = await apiClient.get(`/vendors/expiring?days=${days}`);
    return response.vendors || [];
  },

  // Get single vendor
  getVendor: async (id) => {
    const response = await apiClient.get(`/vendors/${id}`);
    return response.vendor;
  },

  // Create new vendor with enhanced fields
  createVendor: async (vendorData) => {
    const response = await apiClient.post('/vendors', vendorData);
    return response.vendor;
  },

  // Bulk create vendors
  bulkCreateVendors: async (bulkData) => {
    return await apiClient.post('/vendors/bulk', bulkData);
  },

  // Update vendor
  updateVendor: async (id, vendorData) => {
    const response = await apiClient.put(`/vendors/${id}`, vendorData);
    return response.vendor;
  },

  // Delete vendor
  deleteVendor: async (id) => {
    await apiClient.delete(`/vendors/${id}`);
    return true;
  },

  // Get enhanced card data
  getEnhancedCardData: async (vendorId) => {
    return await apiClient.get(`/vendors/${vendorId}/card-data`);
  },

  // Template management
  getTemplates: async () => {
    return await apiClient.get('/templates');
  },

  getTemplate: async (templateName) => {
    return await apiClient.get(`/templates/${templateName}`);
  },

  // Upload photo
  uploadPhoto: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API}/upload/photo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });
    return response.data.photoUrl;
  },

  // Import/Export functions
  importCSV: async (file, template = 'standard') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('template', template);
    
    const response = await axios.post(`${API}/vendors/import/csv`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000,
    });
    return response.data;
  },

  exportCSV: async () => {
    const response = await axios.get(`${API}/vendors/export/csv`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'vendors.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // Get QR code as base64
  getQRCode: async (vendorId) => {
    const response = await apiClient.get(`/qr-code-base64/${vendorId}`);
    return response.qrCode;
  },

  // Get barcode as base64
  getBarcode: async (vendorId) => {
    const response = await apiClient.get(`/barcode-base64/${vendorId}`);
    return response.barcode;
  },

  // Get QR code as image URL
  getQRCodeURL: (vendorId) => {
    return `${API}/qr-code/${vendorId}`;
  },

  // Get barcode as image URL
  getBarcodeURL: (vendorId) => {
    return `${API}/barcode/${vendorId}`;
  }
};