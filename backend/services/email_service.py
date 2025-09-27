import smtplib
import secrets
import string
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
import os
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for authentication and notifications"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@vendoreco.com")
        self.frontend_url = os.getenv("FRONTEND_URL", "https://idecosystem.preview.emergentagent.com")
        self.mock_email = os.getenv("MOCK_EMAIL", "true").lower() == "true"
        
    def generate_verification_token(self) -> str:
        """Generate secure verification token"""
        return secrets.token_urlsafe(32)
    
    def generate_reset_token(self) -> str:
        """Generate secure password reset token"""
        return secrets.token_urlsafe(32)
    
    async def send_verification_email(self, email: str, full_name: str, token: str) -> bool:
        """Send email verification"""
        try:
            if self.mock_email:
                logger.info(f"MOCK EMAIL: Verification email to {email} with token {token}")
                return True
            
            subject = "Verify Your Email - Vendor Ecosystem"
            verification_url = f"{self.frontend_url}/verify-email?token={token}"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 15px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                                <span style="color: white; font-size: 24px;">🛡️</span>
                            </div>
                            <h1 style="color: #1f2937; margin: 0;">Vendor Ecosystem</h1>
                        </div>
                        
                        <h2 style="color: #10b981;">Verify Your Email Address</h2>
                        <p>Hi {full_name},</p>
                        <p>Thank you for registering with Vendor Ecosystem! Please verify your email address to complete your registration and access all features.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_url}" style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">Verify Email Address</a>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            If you can't click the button above, copy and paste this link into your browser:<br>
                            <a href="{verification_url}" style="color: #10b981;">{verification_url}</a>
                        </p>
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            This verification link will expire in 24 hours. If you didn't create an account, you can safely ignore this email.
                        </p>
                        
                        <div style="border-top: 1px solid #e5e7eb; margin-top: 30px; padding-top: 20px; text-align: center; color: #6b7280; font-size: 12px;">
                            <p>© 2024 Vendor Ecosystem. All rights reserved.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            return await self._send_email(email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            return False
    
    async def send_password_reset_email(self, email: str, full_name: str, token: str) -> bool:
        """Send password reset email"""
        try:
            if self.mock_email:
                logger.info(f"MOCK EMAIL: Password reset email to {email} with token {token}")
                return True
            
            subject = "Password Reset - Vendor Ecosystem"
            reset_url = f"{self.frontend_url}/reset-password?token={token}"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 15px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                                <span style="color: white; font-size: 24px;">🔒</span>
                            </div>
                            <h1 style="color: #1f2937; margin: 0;">Vendor Ecosystem</h1>
                        </div>
                        
                        <h2 style="color: #ef4444;">Password Reset Request</h2>
                        <p>Hi {full_name},</p>
                        <p>We received a request to reset your password. Click the button below to create a new password:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">Reset Password</a>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            If you can't click the button above, copy and paste this link into your browser:<br>
                            <a href="{reset_url}" style="color: #ef4444;">{reset_url}</a>
                        </p>
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            This reset link will expire in 1 hour. If you didn't request a password reset, you can safely ignore this email.
                        </p>
                        
                        <div style="border-top: 1px solid #e5e7eb; margin-top: 30px; padding-top: 20px; text-align: center; color: #6b7280; font-size: 12px;">
                            <p>© 2024 Vendor Ecosystem. All rights reserved.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            return await self._send_email(email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False
    
    async def send_2fa_setup_email(self, email: str, full_name: str) -> bool:
        """Send 2FA setup confirmation email"""
        try:
            if self.mock_email:
                logger.info(f"MOCK EMAIL: 2FA setup confirmation to {email}")
                return True
            
            subject = "Two-Factor Authentication Enabled - Vendor Ecosystem"
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 15px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                                <span style="color: white; font-size: 24px;">🔐</span>
                            </div>
                            <h1 style="color: #1f2937; margin: 0;">Vendor Ecosystem</h1>
                        </div>
                        
                        <h2 style="color: #10b981;">Two-Factor Authentication Enabled</h2>
                        <p>Hi {full_name},</p>
                        <p>Two-factor authentication has been successfully enabled on your account. Your account is now more secure!</p>
                        
                        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 16px; margin: 20px 0;">
                            <h3 style="color: #16a34a; margin-top: 0;">Security Tips:</h3>
                            <ul style="color: #15803d; margin: 0;">
                                <li>Keep your backup codes in a safe place</li>
                                <li>Use an authenticator app like Google Authenticator or Authy</li>
                                <li>Never share your 2FA codes with anyone</li>
                            </ul>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            If you didn't enable 2FA, please contact our support team immediately.
                        </p>
                        
                        <div style="border-top: 1px solid #e5e7eb; margin-top: 30px; padding-top: 20px; text-align: center; color: #6b7280; font-size: 12px;">
                            <p>© 2024 Vendor Ecosystem. All rights reserved.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            return await self._send_email(email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Failed to send 2FA setup email to {email}: {e}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Internal method to send email via SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, skipping email send")
                return True  # Return True to not block functionality
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._smtp_send, msg, to_email)
            return result
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _smtp_send(self, msg: MIMEMultipart, to_email: str) -> bool:
        """Send email via SMTP (blocking operation for thread pool)"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg, to_addresses=[to_email])
            return True
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return False