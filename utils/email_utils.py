import smtplib
import os
import threading  
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import url_for

def send_async_email(username, password, host, port, msg):
    """
    Internal function to be run in a background thread.
    This prevents the main application from freezing.
    """
    try:
        with smtplib.SMTP(host, int(port)) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email in background: {e}")

def send_reset_email(to_email, reset_token):
    """Sends a password reset email to the user using a background thread."""
    
    host = os.environ.get('EMAIL_HOST')
    port = int(os.environ.get('EMAIL_PORT', 587))
    username = os.environ.get('EMAIL_USERNAME')
    password = os.environ.get('EMAIL_PASSWORD')
    
    reset_link = url_for('auth.reset_password', token=reset_token, _external=True)
    
    if not all([host, username, password]):
        print("\n" + "="*50)
        print(f"PASSWORD RESET LINK FOR {to_email}:")
        print(reset_link)
        print("="*50 + "\n")
        return True
    
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = to_email
    msg['Subject'] = "Password Reset - Game On"
    
    body = f"""
    Hi,

    You requested a password reset for your Game On Bogura account.
    Please click the link below to reset your password. This link will expire in 1 hour.
    {reset_link}

    If you didn't request this, please ignore this email.

    Best regards,
    Game On Team
    """
    msg.attach(MIMEText(body, 'plain'))
    
    
    try:
        email_thread = threading.Thread(
            target=send_async_email, 
            args=(username, password, host, port, msg)
        )
        email_thread.start()
        return True
    except Exception as e:
        print(f"Error starting email thread: {e}")
        print(f"DEBUG Reset Link: {reset_link}")
        return False