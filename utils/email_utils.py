import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import url_for

def send_reset_email(to_email, reset_token):
    """Sends a password reset email to the user."""
    
    # Extract email config from environment
    host = os.environ.get('EMAIL_HOST')
    port = os.environ.get('EMAIL_PORT')
    username = os.environ.get('EMAIL_USERNAME')
    password = os.environ.get('EMAIL_PASSWORD')

    # Construct reset link
    reset_link = url_for('auth.reset_password', token=reset_token, _external=True)

    # For development: log to console if SMTP not fully configured
    if not all([host, port, username, password]):
        print("\n" + "="*50)
        print(f"PASSWORD RESET LINK FOR {to_email}:")
        print(reset_link)
        print("="*50 + "\n")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_email
        msg['Subject'] = "Password Reset - Game On"
        
        body = f"""
    Hi,

    SUIIIIIIIII
    {reset_link}

    If you didn't request this, please ignore this email.

    Best regards,
    Game On Team
    """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(host, int(port))
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        # Still print the link to console for debugging
        print(f"DEBUG Reset Link: {reset_link}")
        return False
