# Vendor ID Card System - API Contracts & Integration Plan

## API Contracts

### Vendor Model
```json
{
  "id": "string (VID-NG-XXXX format)",
  "name": "string (UPPERCASE)",
  "photo": "string (base64 or URL)",
  "issueDate": "string (YYYY-MM-DD)",
  "status": "string (verified|pending)",
  "createdAt": "ISO date string",
  "updatedAt": "ISO date string"
}
```

### API Endpoints

#### 1. Get All Vendors
- **GET** `/api/vendors`
- **Response**: `{ vendors: Vendor[], total: number }`
- **Query params**: `?search=string&status=string&limit=number&offset=number`

#### 2. Get Single Vendor
- **GET** `/api/vendors/:id`
- **Response**: `{ vendor: Vendor }`

#### 3. Create Vendor
- **POST** `/api/vendors`
- **Body**: `{ name: string, photo?: string, issueDate?: string }`
- **Response**: `{ vendor: Vendor, message: string }`

#### 4. Update Vendor
- **PUT** `/api/vendors/:id`
- **Body**: `{ name?: string, photo?: string, status?: string }`
- **Response**: `{ vendor: Vendor, message: string }`

#### 5. Delete Vendor
- **DELETE** `/api/vendors/:id`
- **Response**: `{ message: string }`

#### 6. Generate QR Code
- **GET** `/api/qr-code/:vendorId`
- **Response**: QR code image (PNG) linking to https://www.vendor-id.com
- **Content-Type**: `image/png`

#### 7. Generate Barcode
- **GET** `/api/barcode/:vendorId`
- **Response**: Barcode image (PNG) with vendor ID
- **Content-Type**: `image/png`

#### 8. Upload Photo
- **POST** `/api/upload/photo`
- **Body**: FormData with image file
- **Response**: `{ photoUrl: string, message: string }`

## Data Migration from Mock

### Current Mock Data in `/app/frontend/src/data/mock.js`:
- Replace `mockAPI.getVendors()` with `axios.get('/api/vendors')`
- Replace `mockAPI.createVendor()` with `axios.post('/api/vendors')`
- Replace `mockAPI.updateVendor()` with `axios.put('/api/vendors/:id')`
- Replace `mockAPI.deleteVendor()` with `axios.delete('/api/vendors/:id')`
- Replace `generateQRCode()` with API call to `/api/qr-code/:vendorId`
- Replace `generateBarcode()` with API call to `/api/barcode/:vendorId`

### Frontend Components to Update:
1. **VendorDashboard.jsx**: Replace mock API calls with real API calls
2. **VendorCard.jsx**: Update QR code and barcode generation
3. **VendorForm.jsx**: Add real photo upload functionality
4. **mock.js**: Remove file after migration

## Backend Implementation Plan

### 1. MongoDB Models
- Vendor schema with validation
- Auto-generated vendor IDs (VID-NG-XXXX format)
- Photo storage handling (base64 or file system)

### 2. Dependencies to Install
- `qrcode` - QR code generation
- `jsbarcode` - Barcode generation  
- `multer` - File upload handling
- `sharp` - Image processing
- `canvas` - Image rendering

### 3. Business Logic
- Auto-generate unique vendor IDs
- Image validation and processing
- QR code linking to https://www.vendor-id.com
- Barcode generation with vendor ID
- Status management (pending → verified)

### 4. Security Features
- File upload validation
- Image size/type restrictions
- Input sanitization
- Error handling

## Integration Steps

1. ✅ Frontend with mock data complete
2. 🔄 Create backend models and endpoints
3. 🔄 Add QR/barcode generation
4. 🔄 Implement photo upload
5. 🔄 Replace frontend mock calls with real API
6. 🔄 Test full stack functionality
7. 🔄 Verify card generation with real data

## Expected Functionality After Integration

- Real vendor database with persistent storage
- Functional QR codes linking to https://www.vendor-id.com
- Scannable barcodes with vendor ID data
- Photo upload and storage
- Complete CRUD operations
- Print-ready cards with all security features