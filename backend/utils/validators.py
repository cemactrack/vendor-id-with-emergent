import re
import email_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class InputValidator:
    """Comprehensive input validation utilities"""
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')  # International format
    URL_PATTERN = re.compile(r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$')
    VENDOR_ID_PATTERN = re.compile(r'^VID-[A-Z]{2}-[A-Z0-9]{8}$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        try:
            if not email or not isinstance(email, str):
                return False
            
            # Basic regex check
            if not InputValidator.EMAIL_PATTERN.match(email):
                return False
            
            # Advanced email validation
            email_validator.validate_email(email)
            return True
        except:
            return False
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        if not password or not isinstance(password, str):
            return {
                "valid": False,
                "errors": ["Password is required"]
            }
        
        errors = []
        
        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            errors.append("Password must be less than 128 characters")
        
        # Character requirements
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\?]', password):
            errors.append("Password must contain at least one special character")
        
        # Common password check
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": InputValidator._calculate_password_strength(password)
        }
    
    @staticmethod
    def _calculate_password_strength(password: str) -> str:
        """Calculate password strength score"""
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\?]', password):
            score += 1
        
        if score <= 2:
            return "weak"
        elif score <= 4:
            return "medium"
        else:
            return "strong"
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        if not phone or not isinstance(phone, str):
            return False
        
        # Remove spaces, dashes, and parentheses
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        return InputValidator.PHONE_PATTERN.match(cleaned_phone) is not None
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False
        
        return InputValidator.URL_PATTERN.match(url) is not None
    
    @staticmethod
    def validate_vendor_id(vendor_id: str) -> bool:
        """Validate Vendor ID format"""
        if not vendor_id or not isinstance(vendor_id, str):
            return False
        
        return InputValidator.VENDOR_ID_PATTERN.match(vendor_id) is not None
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format"""
        if not uuid_str or not isinstance(uuid_str, str):
            return False
        
        return InputValidator.UUID_PATTERN.match(uuid_str.lower()) is not None
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = None) -> str:
        """Sanitize text input"""
        if not text or not isinstance(text, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = text.replace('\x00', '').strip()
        
        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def validate_business_name(name: str) -> Dict[str, Any]:
        """Validate business name"""
        if not name or not isinstance(name, str):
            return {
                "valid": False,
                "error": "Business name is required"
            }
        
        cleaned_name = InputValidator.sanitize_text(name)
        
        if len(cleaned_name) < 2:
            return {
                "valid": False,
                "error": "Business name must be at least 2 characters"
            }
        
        if len(cleaned_name) > 100:
            return {
                "valid": False,
                "error": "Business name must be less than 100 characters"
            }
        
        # Check for valid characters (letters, numbers, spaces, common punctuation)
        if not re.match(r'^[a-zA-Z0-9\s\-\.\,\&\'\"]+$', cleaned_name):
            return {
                "valid": False,
                "error": "Business name contains invalid characters"
            }
        
        return {
            "valid": True,
            "sanitized_name": cleaned_name
        }
    
    @staticmethod
    def validate_file_upload(file_data: bytes, filename: str, allowed_types: List[str] = None, max_size: int = None) -> Dict[str, Any]:
        """Validate file upload"""
        if not file_data or not filename:
            return {
                "valid": False,
                "error": "File and filename are required"
            }
        
        # Check file size
        file_size = len(file_data)
        if max_size and file_size > max_size:
            return {
                "valid": False,
                "error": f"File size exceeds maximum allowed size of {max_size} bytes"
            }
        
        # Check file extension
        if allowed_types:
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            if file_ext not in allowed_types:
                return {
                    "valid": False,
                    "error": f"File type '{file_ext}' not allowed. Allowed types: {', '.join(allowed_types)}"
                }
        
        # Check for null bytes in filename
        if '\x00' in filename:
            return {
                "valid": False,
                "error": "Invalid filename"
            }
        
        return {
            "valid": True,
            "file_size": file_size,
            "file_extension": filename.lower().split('.')[-1] if '.' in filename else ''
        }
    
    @staticmethod
    def validate_date(date_str: str, format_str: str = "%Y-%m-%d") -> Dict[str, Any]:
        """Validate date string"""
        if not date_str or not isinstance(date_str, str):
            return {
                "valid": False,
                "error": "Date is required"
            }
        
        try:
            parsed_date = datetime.strptime(date_str, format_str)
            return {
                "valid": True,
                "parsed_date": parsed_date
            }
        except ValueError:
            return {
                "valid": False,
                "error": f"Invalid date format. Expected format: {format_str}"
            }
    
    @staticmethod
    def validate_enum_value(value: Any, enum_class: Enum) -> Dict[str, Any]:
        """Validate enum value"""
        if value is None:
            return {
                "valid": False,
                "error": "Value is required"
            }
        
        # If it's already an enum instance
        if isinstance(value, enum_class):
            return {
                "valid": True,
                "enum_value": value
            }
        
        # Try to convert string to enum
        if isinstance(value, str):
            try:
                enum_value = enum_class(value)
                return {
                    "valid": True,
                    "enum_value": enum_value
                }
            except ValueError:
                valid_values = [e.value for e in enum_class]
                return {
                    "valid": False,
                    "error": f"Invalid value. Valid options: {', '.join(valid_values)}"
                }
        
        return {
            "valid": False,
            "error": f"Invalid type for enum value"
        }
    
    @staticmethod
    def validate_pagination(limit: int, offset: int) -> Dict[str, Any]:
        """Validate pagination parameters"""
        errors = []
        
        if limit is not None:
            if not isinstance(limit, int) or limit < 1:
                errors.append("Limit must be a positive integer")
            elif limit > 1000:
                errors.append("Limit cannot exceed 1000")
        
        if offset is not None:
            if not isinstance(offset, int) or offset < 0:
                errors.append("Offset must be a non-negative integer")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

class SecurityValidator:
    """Security-focused validation utilities"""
    
    @staticmethod
    def validate_sql_injection(input_str: str) -> bool:
        """Check for potential SQL injection patterns"""
        if not isinstance(input_str, str):
            return True  # Non-string inputs are safe from SQL injection
        
        # Common SQL injection patterns
        sql_patterns = [
            r"('|(\\')|(;)|(\\)|(\-\\-)|(\\|)|(\\*)|(%27)|(%3D)|(%3B)|(%40)|(%2B)",
            r"(union|select|insert|delete|update|drop|create|alter|exec|execute)",
            r"(script|javascript|vbscript|onload|onerror|onclick)"
        ]
        
        input_lower = input_str.lower()
        
        for pattern in sql_patterns:
            if re.search(pattern, input_lower):
                logger.warning(f"Potential SQL injection detected: {input_str[:100]}")
                return False
        
        return True
    
    @staticmethod
    def validate_xss(input_str: str) -> bool:
        """Check for potential XSS patterns"""
        if not isinstance(input_str, str):
            return True
        
        # Common XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"onmouseover=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>"
        ]
        
        input_lower = input_str.lower()
        
        for pattern in xss_patterns:
            if re.search(pattern, input_lower):
                logger.warning(f"Potential XSS detected: {input_str[:100]}")
                return False
        
        return True
    
    @staticmethod
    def validate_path_traversal(path: str) -> bool:
        """Check for path traversal attempts"""
        if not isinstance(path, str):
            return True
        
        # Check for path traversal patterns
        dangerous_patterns = [
            "..",
            "//",
            "\\\\",
            "/etc/",
            "/root/",
            "/home/",
            "c:\\",
            "%2e%2e",
            "..%2f",
            "..%5c"
        ]
        
        path_lower = path.lower()
        
        for pattern in dangerous_patterns:
            if pattern in path_lower:
                logger.warning(f"Potential path traversal detected: {path[:100]}")
                return False
        
        return True