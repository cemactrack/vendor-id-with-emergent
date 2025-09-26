import pyotp
import qrcode
import io
import base64
from typing import List, Optional, Tuple
import secrets
import string
from datetime import datetime, timedelta
import hashlib

class TwoFactorService:
    def __init__(self):
        self.issuer_name = "Vendor Ecosystem"
        
    def generate_secret(self) -> str:
        """Generate a new TOTP secret for a user"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, email: str, secret: str) -> str:
        """Generate QR code for authenticator app setup"""
        try:
            # Create TOTP URI
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=email,
                issuer_name=self.issuer_name
            )
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{qr_code_base64}"
            
        except Exception as e:
            raise Exception(f"Failed to generate QR code: {str(e)}")
    
    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception:
            return False
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for 2FA recovery"""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            # Format as XXXX-XXXX for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Hash backup code for secure storage"""
        # Remove formatting and convert to uppercase
        clean_code = code.replace('-', '').upper()
        return hashlib.sha256(clean_code.encode()).hexdigest()
    
    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> bool:
        """Verify backup code against stored hashes"""
        clean_code = code.replace('-', '').upper()
        code_hash = hashlib.sha256(clean_code.encode()).hexdigest()
        return code_hash in hashed_codes
    
    def get_time_remaining(self) -> int:
        """Get seconds remaining until next TOTP period"""
        return 30 - (int(datetime.now().timestamp()) % 30)
    
    def is_rate_limited(self, last_attempt: Optional[datetime], max_attempts: int = 5) -> bool:
        """Check if user is rate limited for 2FA attempts"""
        if not last_attempt:
            return False
        
        # Rate limit: max 5 attempts per minute
        time_diff = datetime.utcnow() - last_attempt
        return time_diff < timedelta(minutes=1)
    
    def generate_recovery_info(self, email: str, secret: str) -> dict:
        """Generate complete 2FA setup information"""
        backup_codes = self.generate_backup_codes()
        hashed_codes = [self.hash_backup_code(code) for code in backup_codes]
        qr_code = self.generate_qr_code(email, secret)
        
        return {
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': backup_codes,
            'hashed_backup_codes': hashed_codes,
            'setup_key': secret,  # Manual entry key for authenticator apps
            'issuer': self.issuer_name
        }