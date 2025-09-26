import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import secrets
import string
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.use_mock = os.getenv("MOCK_EMAIL", "true").lower() == "true"
        
    def generate_verification_token(self) -> str:
        """Generate secure verification token"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    def generate_reset_token(self) -> str:
        """Generate secure password reset token"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(48)
    
    async def send_verification_email(self, email: str, full_name: str, token: str) -> bool:
        """Send email verification email"""
        if self.use_mock:
            logger.info(f"MOCK EMAIL: Verification token for {email}: {token}")
            return True
            
        try:
            subject = "Verify Your Vendor Ecosystem Account"
            verification_url = f"{os.getenv('FRONTEND_URL', 'https://vendorsecure.preview.emergentagent.com')}/verify-email?token={token}"
            
            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                                <span style="color: white; font-size: 24px; font-weight: bold;">V</span>
                            </div>
                            <h1 style="color: #10b981; margin: 0;">Vendor Verification Ecosystem</h1>
                        </div>
                        
                        <h2 style="color: #374151;">Welcome, {full_name}!</h2>
                        
                        <p>Thank you for joining the Vendor Verification Ecosystem. To complete your registration and access all features, please verify your email address.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_url}" style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                                Verify Email Address
                            </a>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            If the button doesn't work, copy and paste this link into your browser:<br>
                            <a href="{verification_url}" style="color: #10b981; word-break: break-all;">{verification_url}</a>
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                        
                        <div style="background: #f9fafb; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;">
                            <h3 style="color: #374151; margin-top: 0;">Security Notice</h3>
                            <p style="margin: 0; font-size: 14px; color: #6b7280;">
                                This verification link will expire in 24 hours. If you didn't create this account, please ignore this email.
                            </p>
                        </div>
                        
                        <p style="text-align: center; color: #9ca3af; font-size: 12px; margin-top: 30px;">
                            © 2024 Vendor Verification Ecosystem. All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            return await self._send_email(email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            return False
    
    async def send_password_reset_email(self, email: str, full_name: str, token: str) -> bool:
        """Send password reset email"""
        if self.use_mock:
            logger.info(f"MOCK EMAIL: Password reset token for {email}: {token}")
            return True
            
        try:
            subject = "Reset Your Password - Vendor Ecosystem"
            reset_url = f"{os.getenv('FRONTEND_URL', 'https://vendorsecure.preview.emergentagent.com')}/reset-password?token={token}"
            
            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                                <span style="color: white; font-size: 24px; font-weight: bold;">V</span>
                            </div>
                            <h1 style="color: #10b981; margin: 0;">Password Reset Request</h1>
                        </div>
                        
                        <h2 style="color: #374151;">Hello, {full_name}</h2>
                        
                        <p>We received a request to reset your password for your Vendor Ecosystem account. If you didn't make this request, you can safely ignore this email.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" style="background: linear-gradient(135deg, #dc2626, #b91c1c); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                                Reset Password
                            </a>
                        </div>
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            If the button doesn't work, copy and paste this link into your browser:<br>
                            <a href="{reset_url}" style="color: #dc2626; word-break: break-all;">{reset_url}</a>
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                        
                        <div style="background: #fef2f2; padding: 15px; border-radius: 8px; border-left: 4px solid #dc2626;">
                            <h3 style="color: #374151; margin-top: 0;">Security Notice</h3>
                            <p style="margin: 0; font-size: 14px; color: #6b7280;">
                                This reset link will expire in 1 hour. For security reasons, please don't share this link with anyone.
                            </p>
                        </div>
                        
                        <p style="text-align: center; color: #9ca3af; font-size: 12px; margin-top: 30px;">
                            © 2024 Vendor Verification Ecosystem. All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            return await self._send_email(email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False
    
    async def send_2fa_setup_email(self, email: str, full_name: str) -> bool:
        """Send 2FA setup notification email"""
        if self.use_mock:
            logger.info(f"MOCK EMAIL: 2FA setup notification for {email}")
            return True
            
        try:
            subject = "Two-Factor Authentication Enabled - Vendor Ecosystem"
            
            body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                                <span style="color: white; font-size: 24px; font-weight: bold;">🔒</span>
                            </div>
                            <h1 style="color: #10b981; margin: 0;">Security Enhancement</h1>
                        </div>
                        
                        <h2 style="color: #374151;">Hello, {full_name}</h2>
                        
                        <p>Two-factor authentication has been successfully enabled on your Vendor Ecosystem account. This adds an extra layer of security to protect your account.</p>
                        
                        <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981; margin: 20px 0;">
                            <h3 style="color: #166534; margin-top: 0;">What's Protected Now:</h3>
                            <ul style="color: #166534; margin: 0;">
                                <li>Account login and access</li>
                                <li>Profile modifications</li>
                                <li>Document uploads</li>
                                <li>Verification status changes</li>
                            </ul>
                        </div>
                        
                        <p>Make sure to save your backup codes in a secure location. If you lose access to your authenticator app, these codes will be your only way to regain access to your account.</p>
                        
                        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                        
                        <p style="color: #6b7280; font-size: 14px;">
                            If you didn't enable 2FA, please contact our support team immediately at 
                            <a href="mailto:security@vendoreco.com" style="color: #dc2626;">security@vendoreco.com</a>
                        </p>
                        
                        <p style="text-align: center; color: #9ca3af; font-size: 12px; margin-top: 30px;">
                            © 2024 Vendor Verification Ecosystem. All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            return await self._send_email(email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send 2FA setup email to {email}: {e}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        if self.use_mock or not self.smtp_username:
            logger.info(f"MOCK EMAIL: {subject} to {to_email}")
            return True
            
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Run SMTP in thread to avoid blocking
            def send_smtp():
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                server.quit()
                
            await asyncio.get_event_loop().run_in_executor(None, send_smtp)
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error sending to {to_email}: {e}")
            return False