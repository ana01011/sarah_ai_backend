"""
Email service for sending emails via Gmail SMTP
"""
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import os
from app.core.database import db

class EmailService:
    def __init__(self):
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_user = "silvercity320@gmail.com"
        self.smtp_password = "mdzn bquj htir trhf"
        self.from_email = "silvercity320@gmail.com"
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    async def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send an email via Gmail SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False
    
    async def send_verification_otp(self, user_id: str, email: str) -> str:
        """Send OTP for email verification"""
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store OTP in database with expiry
        expiry = datetime.utcnow() + timedelta(minutes=5)
        await db.execute("""
            UPDATE users 
            SET verification_otp = $2, 
                otp_expires_at = $3,
                otp_attempts = 0
            WHERE id = $1
        """, user_id, otp, expiry)
        
        # Email body
        subject = "Sarah AI - Verify Your Email"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #333;">Welcome to Sarah AI! 🎉</h2>
                <p style="color: #666;">Please verify your email address by entering this code:</p>
                <div style="background: #f0f0f0; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                    <h1 style="color: #4CAF50; font-size: 48px; letter-spacing: 10px; margin: 0;">{otp}</h1>
                </div>
                <p style="color: #999;">This code will expire in 5 minutes.</p>
                <p style="color: #999;">If you didn't create an account, please ignore this email.</p>
            </div>
        </body>
        </html>
        """
        
        await self.send_email(email, subject, body, is_html=True)
        return otp
    
    async def send_login_otp(self, email: str) -> str:
        """Send OTP for 2FA login"""
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store OTP
        user = await db.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if user:
            expiry = datetime.utcnow() + timedelta(minutes=5)
            await db.execute("""
                UPDATE users 
                SET login_otp = $2, 
                    login_otp_expires = $3
                WHERE id = $1
            """, user['id'], otp, expiry)
        
        # Email body
        subject = "Sarah AI - Login Code"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #333;">Login Verification 🔐</h2>
                <p style="color: #666;">Your login verification code is:</p>
                <div style="background: #f0f0f0; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                    <h1 style="color: #2196F3; font-size: 48px; letter-spacing: 10px; margin: 0;">{otp}</h1>
                </div>
                <p style="color: #999;">This code will expire in 5 minutes.</p>
                <p style="color: #ff6b6b;">⚠️ If you didn't try to login, secure your account immediately!</p>
            </div>
        </body>
        </html>
        """
        
        await self.send_email(email, subject, body, is_html=True)
        return otp
    
    async def send_password_reset_otp(self, email: str) -> bool:
        """Send OTP for password reset"""
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Get user and store OTP
        user = await db.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if not user:
            return False
        
        expiry = datetime.utcnow() + timedelta(minutes=15)
        await db.execute("""
            UPDATE users 
            SET reset_otp = $2, 
                reset_otp_expires = $3
            WHERE id = $1
        """, user['id'], otp, expiry)
        
        # Email body
        subject = "Sarah AI - Password Reset Code"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #333;">Password Reset Request 🔑</h2>
                <p style="color: #666;">Your password reset code is:</p>
                <div style="background: #f0f0f0; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                    <h1 style="color: #FF9800; font-size: 48px; letter-spacing: 10px; margin: 0;">{otp}</h1>
                </div>
                <p style="color: #999;">This code will expire in 15 minutes.</p>
                <p style="color: #999;">If you didn't request this, please ignore this email.</p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(email, subject, body, is_html=True)

# Singleton instance
email_service = EmailService()
