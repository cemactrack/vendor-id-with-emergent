import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from io import BytesIO
from PIL import Image
import base64

class QRBarcodeService:
    
    @staticmethod
    def generate_qr_code(vendor_id: str) -> str:
        """Generate QR code linking to vendor-id.com"""
        # QR code should link to the website as specified
        qr_data = "https://www.vendor-id.com"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def generate_barcode(vendor_id: str) -> str:
        """Generate barcode with vendor ID"""
        # Remove VID-NG- prefix and use just the number for barcode
        barcode_data = vendor_id.replace('VID-NG-', '')
        
        # Create barcode
        code = Code128(barcode_data, writer=ImageWriter())
        
        # Generate barcode image
        buffer = BytesIO()
        code.write(buffer)
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def get_qr_code_image(vendor_id: str) -> bytes:
        """Get QR code as PNG bytes"""
        qr_data = "https://www.vendor-id.com"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        return buffer.getvalue()
    
    @staticmethod
    def get_barcode_image(vendor_id: str) -> bytes:
        """Get barcode as PNG bytes"""
        barcode_data = vendor_id.replace('VID-NG-', '')
        
        code = Code128(barcode_data, writer=ImageWriter())
        
        buffer = BytesIO()
        code.write(buffer)
        return buffer.getvalue()