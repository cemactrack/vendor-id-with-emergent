from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Comprehensive error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_exception(request, exc)
    
    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle different types of exceptions"""
        
        # Log the error
        error_id = self._generate_error_id()
        
        try:
            # Get request body for logging (safely)
            request_body = await self._get_request_body(request)
        except:
            request_body = "Unable to read request body"
        
        # Log error details
        logger.error(
            f"Error ID: {error_id}\n"
            f"Path: {request.url.path}\n"
            f"Method: {request.method}\n"
            f"Query Params: {dict(request.query_params)}\n"
            f"Headers: {dict(request.headers)}\n"
            f"Body: {request_body}\n"
            f"Exception: {type(exc).__name__}: {str(exc)}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        # Handle specific exception types
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": True,
                    "error_id": error_id,
                    "detail": exc.detail,
                    "status_code": exc.status_code
                }
            )
        
        elif isinstance(exc, ValueError):
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "error_id": error_id,
                    "detail": str(exc),
                    "status_code": 400
                }
            )
        
        elif isinstance(exc, PermissionError):
            return JSONResponse(
                status_code=403,
                content={
                    "error": True,
                    "error_id": error_id,
                    "detail": "Permission denied",
                    "status_code": 403
                }
            )
        
        elif isinstance(exc, FileNotFoundError):
            return JSONResponse(
                status_code=404,
                content={
                    "error": True,
                    "error_id": error_id,
                    "detail": "Resource not found",
                    "status_code": 404
                }
            )
        
        elif isinstance(exc, ConnectionError):
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "error_id": error_id,
                    "detail": "Service temporarily unavailable",
                    "status_code": 503
                }
            )
        
        elif isinstance(exc, TimeoutError):
            return JSONResponse(
                status_code=504,
                content={
                    "error": True,
                    "error_id": error_id,
                    "detail": "Request timeout",
                    "status_code": 504
                }
            )
        
        else:
            # Generic server error
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "error_id": error_id,
                    "detail": "Internal server error",
                    "status_code": 500
                }
            )
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking"""
        from uuid import uuid4
        return f"ERR-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
    
    async def _get_request_body(self, request: Request) -> str:
        """Safely get request body for logging"""
        try:
            # Clone the receive to avoid consuming the original stream
            body = b""
            async for chunk in request.stream():
                body += chunk
            
            # Try to decode as JSON first, then as text
            try:
                decoded = body.decode('utf-8')
                json.loads(decoded)  # Validate JSON
                return decoded
            except (json.JSONDecodeError, UnicodeDecodeError):
                return f"<Binary data: {len(body)} bytes>"
        except:
            return "<Unable to read body>"

class ValidationErrorHandler:
    """Handle Pydantic validation errors"""
    
    @staticmethod
    def format_validation_error(error) -> Dict[str, Any]:
        """Format Pydantic validation error for API response"""
        errors = []
        
        for err in error.errors():
            field_path = " -> ".join(str(x) for x in err["loc"])
            errors.append({
                "field": field_path,
                "message": err["msg"],
                "type": err["type"],
                "input": err.get("input")
            })
        
        return {
            "error": True,
            "detail": "Validation error",
            "validation_errors": errors,
            "status_code": 422
        }

class DatabaseErrorHandler:
    """Handle database-specific errors"""
    
    @staticmethod
    def handle_mongo_error(exc: Exception) -> Dict[str, Any]:
        """Handle MongoDB specific errors"""
        error_message = str(exc)
        
        if "duplicate key" in error_message.lower():
            return {
                "error": True,
                "detail": "A record with this data already exists",
                "status_code": 409
            }
        
        elif "connection" in error_message.lower():
            return {
                "error": True,
                "detail": "Database connection error",
                "status_code": 503
            }
        
        elif "timeout" in error_message.lower():
            return {
                "error": True,
                "detail": "Database operation timed out",
                "status_code": 504
            }
        
        else:
            return {
                "error": True,
                "detail": "Database operation failed",
                "status_code": 500
            }

class AuthenticationErrorHandler:
    """Handle authentication and authorization errors"""
    
    @staticmethod
    def handle_jwt_error(exc: Exception) -> Dict[str, Any]:
        """Handle JWT related errors"""
        error_message = str(exc).lower()
        
        if "expired" in error_message:
            return {
                "error": True,
                "detail": "Token has expired",
                "error_code": "TOKEN_EXPIRED",
                "status_code": 401
            }
        
        elif "invalid" in error_message or "decode" in error_message:
            return {
                "error": True,
                "detail": "Invalid token",
                "error_code": "INVALID_TOKEN",
                "status_code": 401
            }
        
        else:
            return {
                "error": True,
                "detail": "Authentication failed",
                "error_code": "AUTH_FAILED",
                "status_code": 401
            }
    
    @staticmethod
    def handle_permission_error() -> Dict[str, Any]:
        """Handle permission/authorization errors"""
        return {
            "error": True,
            "detail": "Insufficient permissions for this operation",
            "error_code": "INSUFFICIENT_PERMISSIONS",
            "status_code": 403
        }

class RateLimitErrorHandler:
    """Handle rate limiting errors"""
    
    @staticmethod
    def handle_rate_limit_error(retry_after: int = None) -> Dict[str, Any]:
        """Handle rate limit exceeded errors"""
        response = {
            "error": True,
            "detail": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "status_code": 429
        }
        
        if retry_after:
            response["retry_after"] = retry_after
        
        return response

def setup_error_handlers(app):
    """Setup custom error handlers for the FastAPI app"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "detail": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.error(f"ValueError in {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "detail": str(exc),
                "status_code": 400
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception in {request.url.path}: {str(exc)}")
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "detail": "Internal server error",
                "status_code": 500
            }
        )