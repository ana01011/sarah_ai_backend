#!/usr/bin/env python3
"""
Test email and OTP functionality
"""
import asyncio
import sys
import os
sys.path.append('/root/openhermes_backend')

from app.services.email_service import email_service

async def test_email():
    """Test email sending"""
    print("🧪 Testing Email Service...")
    
    # Test simple email
    success = await email_service.send_email(
        "silvercity320@gmail.com",
        "Test Email from Sarah AI",
        "This is a test email. If you received this, email is working!",
        is_html=False
    )
    
    if success:
        print("✅ Email sent successfully!")
    else:
        print("❌ Email sending failed!")

if __name__ == "__main__":
    asyncio.run(test_email())
