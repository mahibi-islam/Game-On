import os
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as UserCredentials
from flask import url_for

def send_reset_email(to_email, reset_token):
   
    creds_file = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_FILE') or 'Credentials.json'
    token_file = 'token.json'
    sender_email = os.environ.get('EMAIL_SENDER') or os.environ.get('EMAIL_USERNAME')
    
    reset_link = url_for('auth.reset_password', token=reset_token, _external=True)
    
    has_token = os.path.exists(token_file)
    has_service_account = os.path.exists(creds_file)

    if not (has_token or has_service_account) or not sender_email:
        print("\n" + "="*50)
        print("GMAIL API NOT FULLY CONFIGURED (Missing token.json, Credentials.json or EMAIL_SENDER/USERNAME)")
        print(f"PASSWORD RESET LINK FOR {to_email}:")
        print(reset_link)
        print("="*50 + "\n")
        return True

    try:
        scopes = ['https://www.googleapis.com/auth/gmail.send']
        
        if has_token:
            delegated_creds = UserCredentials.from_authorized_user_file(token_file, scopes)
        else:
            creds = ServiceAccountCredentials.from_service_account_file(creds_file, scopes=scopes)
            delegated_creds = creds.with_subject(sender_email)
        
        service = build('gmail', 'v1', credentials=delegated_creds)
        
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h2 style="color: #00ff88; text-align: center;">Game On Bogura</h2>
            <p>Hi,</p>
            <p>You requested a password reset for your Game On Bogura account.</p>
            <p>Please click the button below to reset your password. This link will expire in 1 hour.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #00ff88; color: #000; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Password</a>
            </div>
            <p>If you didn't request this, please ignore this email.</p>
            <p>If the button above doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{reset_link}</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #999; text-align: center;">&copy; 2026 Game On Bogura. All rights reserved.</p>
        </div>
        """
        
        message = MIMEText(html_content, 'html')
        message['to'] = to_email
        message['from'] = sender_email
        message['subject'] = "Password Reset - Game On"
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        print(f"Email sent successfully via Gmail API to {to_email}")
        return True

    except Exception as e:
        print(f"Error sending email via Gmail API: {e}")
        # Always print the link as a ultimate fallback
        print(f"DEBUG Reset Link for {to_email}: {reset_link}")
        return False
