// Mock data for vendor ID cards
export const mockVendors = [
  {
    id: "VID-NG-8734",
    name: "AISHA SANNI",
    issueDate: "2024-07-20",
    photo: "https://images.unsplash.com/photo-1494790108755-2616b612b47c?w=400&h=400&fit=crop&crop=face",
    status: "verified",
    createdAt: "2024-07-20T10:30:00Z"
  },
  {
    id: "VID-NG-9851",
    name: "IBRAHIM MOHAMMED",
    issueDate: "2024-07-18",
    photo: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face",
    status: "verified",
    createdAt: "2024-07-18T14:15:00Z"
  },
  {
    id: "VID-NG-7432",
    name: "FATIMA ABDUL",
    issueDate: "2024-07-15",
    photo: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop&crop=face",
    status: "verified",
    createdAt: "2024-07-15T09:20:00Z"
  },
  {
    id: "VID-NG-6523",
    name: "CHUKWU EMEKA",
    issueDate: "2024-07-12",
    photo: "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&h=400&fit=crop&crop=face",
    status: "pending",
    createdAt: "2024-07-12T16:45:00Z"
  },
  {
    id: "VID-NG-5417",
    name: "ADUNNI WILLIAMS",
    issueDate: "2024-07-10",
    photo: "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=400&h=400&fit=crop&crop=face",
    status: "verified",
    createdAt: "2024-07-10T11:30:00Z"
  }
];

// Generate QR code data URL (mock implementation)
export const generateQRCode = (data) => {
  // This will be replaced with actual QR code generation in backend
  return `data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==`;
};

// Generate barcode data URL (mock implementation)
export const generateBarcode = (vendorId) => {
  // This will be replaced with actual barcode generation in backend
  return `data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==`;
};

// Mock API functions
export const mockAPI = {
  getVendors: () => Promise.resolve(mockVendors),
  getVendor: (id) => Promise.resolve(mockVendors.find(v => v.id === id)),
  createVendor: (vendorData) => {
    const newVendor = {
      ...vendorData,
      id: `VID-NG-${Math.floor(Math.random() * 9000) + 1000}`,
      issueDate: new Date().toISOString().split('T')[0],
      status: 'pending',
      createdAt: new Date().toISOString()
    };
    mockVendors.push(newVendor);
    return Promise.resolve(newVendor);
  },
  updateVendor: (id, vendorData) => {
    const index = mockVendors.findIndex(v => v.id === id);
    if (index !== -1) {
      mockVendors[index] = { ...mockVendors[index], ...vendorData };
      return Promise.resolve(mockVendors[index]);
    }
    return Promise.reject(new Error('Vendor not found'));
  },
  deleteVendor: (id) => {
    const index = mockVendors.findIndex(v => v.id === id);
    if (index !== -1) {
      mockVendors.splice(index, 1);
      return Promise.resolve(true);
    }
    return Promise.reject(new Error('Vendor not found'));
  }
};