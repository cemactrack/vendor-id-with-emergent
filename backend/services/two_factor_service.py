import pyotp
import qrcode
import qrcode.image.svg
import io
import base64
import secrets
import hashlib
import bcrypt
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class TwoFactorService:
    """Service for Two-Factor Authentication operations"""
    
    def __init__(self):
        self.issuer = "Vendor Ecosystem"
        
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_recovery_info(self, email: str, secret: str) -> Dict:
        """Generate complete 2FA setup information including QR code and backup codes"""
        try:
            # Create TOTP URI
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=email,
                issuer_name=self.issuer
            )
            
            # Generate QR code
            qr_code_data = self._generate_qr_code(provisioning_uri)
            
            # Generate backup codes
            backup_codes = self._generate_backup_codes()
            hashed_backup_codes = [self.hash_backup_code(code) for code in backup_codes]
            
            return {
                "qr_code": qr_code_data,
                "setup_key": secret,
                "backup_codes": backup_codes,
                "hashed_backup_codes": hashed_backup_codes,
                "issuer": self.issuer
            }
            
        except Exception as e:
            logger.error(f"Failed to generate recovery info: {e}")
            raise
    
    def _generate_qr_code(self, provisioning_uri: str) -> str:
        """Generate QR code as base64 encoded PNG"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            raise
    
    def _generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup recovery codes"""
        codes = []
        for _ in range(count):
            # Generate 8-character code in XXXX-XXXX format
            part1 = secrets.token_hex(2).upper()
            part2 = secrets.token_hex(2).upper()
            codes.append(f"{part1}-{part2}")
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Hash backup code for secure storage"""
        # Remove hyphens and convert to lowercase for consistent hashing
        normalized_code = code.replace("-", "").lower()
        return hashlib.sha256(normalized_code.encode()).hexdigest()
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            # Allow 1 window tolerance (30 seconds before/after)
            return totp.verify(token, valid_window=1)
        except Exception as e:
            logger.error(f"Failed to verify TOTP: {e}")
            return False
    
    def verify_backup_code(self, code: str, stored_hashes: List[str]) -> bool:
        """Verify backup code against stored hashes"""
        try:
            code_hash = self.hash_backup_code(code)
            return code_hash in stored_hashes
        except Exception as e:
            logger.error(f"Failed to verify backup code: {e}")
            return False
    
    def generate_backup_codes_for_user(self, count: int = 10) -> Tuple[List[str], List[str]]:
        """Generate new backup codes for a user (returns both plain and hashed)"""
        plain_codes = self._generate_backup_codes(count)
        hashed_codes = [self.hash_backup_code(code) for code in plain_codes]
        return plain_codes, hashed_codes