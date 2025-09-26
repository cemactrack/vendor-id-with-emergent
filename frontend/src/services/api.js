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
  // Get all vendors with optional filtering
  getVendors: async (search = '', status = 'all', limit = 50, offset = 0) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status && status !== 'all') params.append('status', status);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    const response = await apiClient.get(`/vendors?${params.toString()}`);
    return response.vendors || [];
  },

  // Get single vendor
  getVendor: async (id) => {
    const response = await apiClient.get(`/vendors/${id}`);
    return response.vendor;
  },

  // Create new vendor
  createVendor: async (vendorData) => {
    const response = await apiClient.post('/vendors', vendorData);
    return response.vendor;
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

  // Upload photo
  uploadPhoto: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API}/upload/photo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // Longer timeout for file uploads
    });
    return response.data.photoUrl;
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

  // Get QR code as image URL (for direct image src)
  getQRCodeURL: (vendorId) => {
    return `${API}/qr-code/${vendorId}`;
  },

  // Get barcode as image URL (for direct image src)
  getBarcodeURL: (vendorId) => {
    return `${API}/barcode/${vendorId}`;
  }
};