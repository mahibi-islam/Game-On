import os
import base64
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as UserCredentials
from flask import url_for, current_app
from bson import ObjectId

def send_email_smtp(to_email, subject, html_content):
    """Send an email using SMTP configurations from environment variables."""
    host = os.environ.get('EMAIL_HOST')
    port = os.environ.get('EMAIL_PORT')
    username = os.environ.get('EMAIL_USERNAME')
    password = os.environ.get('EMAIL_PASSWORD')
    sender = os.environ.get('EMAIL_SENDER') or username
    
    if not all([host, port, username, password]):
        print("SMTP: Configuration missing (EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD)")
        return False
        
    try:
        port = int(port)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to_email
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
            
        server.login(username, password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        print(f"SMTP: Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"SMTP Error: Failed to send email to {to_email}: {e}")
        return False

def send_email_gmail_api(to_email, subject, html_content):
    """Send an email using Google Gmail API with token or service account credentials."""
    creds_file = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_FILE') or os.environ.get('GOOGLE_CREDENTIALS_FILE') or 'credentials.json'
    token_file = os.environ.get('GOOGLE_TOKEN_FILE') or 'token.json'
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON') or os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    token_json = os.environ.get('GOOGLE_TOKEN_JSON')
    sender_email = os.environ.get('EMAIL_SENDER') or os.environ.get('EMAIL_USERNAME')
    
    has_token = bool(token_json) or os.path.exists(token_file)
    has_service_account = bool(creds_json) or os.path.exists(creds_file)

    if not (has_token or has_service_account) or not sender_email:
        print("GMAIL API: Not fully configured (Missing token, credentials or EMAIL_SENDER/USERNAME)")
        return False

    try:
        scopes = ['https://www.googleapis.com/auth/gmail.send']
        import json
        
        if token_json:
            token_info = json.loads(token_json) if isinstance(token_json, str) else token_json
            delegated_creds = UserCredentials.from_authorized_user_info(token_info, scopes)
        elif os.path.exists(token_file):
            delegated_creds = UserCredentials.from_authorized_user_file(token_file, scopes)
        elif creds_json:
            sa_info = json.loads(creds_json) if isinstance(creds_json, str) else creds_json
            creds = ServiceAccountCredentials.from_service_account_info(sa_info, scopes=scopes)
            delegated_creds = creds.with_subject(sender_email)
        else:
            creds = ServiceAccountCredentials.from_service_account_file(creds_file, scopes=scopes)
            delegated_creds = creds.with_subject(sender_email)
        
        service = build('gmail', 'v1', credentials=delegated_creds)
        
        message = MIMEText(html_content, 'html')
        message['to'] = to_email
        message['from'] = sender_email
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        print(f"GMAIL API: Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"GMAIL API Error: Failed to send email to {to_email}: {e}")
        return False

def send_email(to_email, subject, html_content):
    """Send an email trying SMTP first, and falling back to Gmail API."""
    print(f"Attempting to send email to: {to_email} with subject: {subject}")
    
    # 1. Try SMTP
    if send_email_smtp(to_email, subject, html_content):
        return True
        
    # 2. Try Gmail API
    if send_email_gmail_api(to_email, subject, html_content):
        return True
        
    # 3. Fallback: Log to console
    print("\n" + "="*50)
    print(f"CRITICAL: ALL EMAIL SENDING METHODS FAILED TO {to_email}")
    print(f"SUBJECT: {subject}")
    print("CONTENT (HTML preview truncated):")
    print(html_content[:500] + "...")
    print("="*50 + "\n")
    return False

def send_reset_email(to_email, reset_token):
    """Sends a password reset email."""
    try:
        reset_link = url_for('auth.reset_password', token=reset_token, _external=True)
    except Exception:
        # Fallback reset link if outside app context during debug
        reset_link = f"http://localhost:5000/reset-password?token={reset_token}"
        
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
    return send_email(to_email, "Password Reset - Game On", html_content)

def send_booking_emails(booking_data):
    """Asynchronously sends booking notification emails to the customer and the admin/location."""
    try:
        app = current_app._get_current_object()
        thread = threading.Thread(target=_send_booking_emails_sync, args=(app, booking_data))
        thread.daemon = True
        thread.start()
        print(f"Background thread started for sending booking emails for booking {booking_data.get('booking_id')}")
    except Exception as e:
        print(f"Error starting background thread for booking emails: {e}")
        # Run synchronously as emergency fallback if current_app is unavailable
        try:
            _send_booking_emails_sync(None, booking_data)
        except Exception as e2:
            print(f"Emergency synchronous email sending also failed: {e2}")

def _send_booking_emails_sync(app, booking_data):
    """Synchronous execution inside background thread, wrapped with app context."""
    if app:
        ctx = app.app_context()
        ctx.push()
        
    try:
        from models.slot import Slot
        from models.location import Location
        from models.settings import Settings
        from db import mongo

        booking_id = booking_data.get('booking_id') or f"#{booking_data.get('_id')}"
        date = booking_data.get('date', 'N/A')
        name = booking_data.get('name', 'N/A')
        phone = booking_data.get('phone', 'N/A')
        team_name = booking_data.get('team_name', '')
        payment_method = booking_data.get('payment_method', 'N/A')
        transaction_id = booking_data.get('transaction_id', '')
        amount = booking_data.get('amount', 'N/A')
        status = booking_data.get('status', 'pending')
        notes = booking_data.get('notes', '')

        # Fetch slot details
        slot_id = booking_data.get('time_slot')
        slot = None
        if slot_id:
            try:
                slot = Slot.find_by_id(str(slot_id))
            except Exception:
                pass
        from utils.slot_utils import slot_label
        slot_time = slot_label(slot)
        sport_name = slot.get('sport', 'N/A') if slot else 'N/A'

        # Fetch location details
        loc_id = booking_data.get('location_id')
        if not loc_id and slot:
            loc_id = slot.get('location_id')
            
        location = None
        if loc_id:
            try:
                location = Location.find_by_id(str(loc_id))
            except Exception:
                pass
        
        location_name = location.get('name', 'N/A') if location else 'N/A'
        location_address = location.get('address', 'N/A') if location else 'N/A'
        
        settings = Settings.find_one()
        turf_name = settings.get('turf_name', 'GAME ON') if settings else 'GAME ON'
        whatsapp = settings.get('whatsapp', '') if settings else ''

        # Prepare team name row
        team_row = f"""
        <tr>
            <td style="padding: 4px 0; color: #9ca3af; font-size: 13px;">Team Name:</td>
            <td style="padding: 4px 0; color: #ffffff; font-size: 13px; text-align: right;">{team_name}</td>
        </tr>
        """ if team_name else ""

        # Prepare transaction ID row
        transaction_row = f"""
        <tr>
            <td style="padding: 4px 0; color: #9ca3af; font-size: 13px;">Transaction ID:</td>
            <td style="padding: 4px 0; color: #ffffff; font-size: 13px; text-align: right;">{transaction_id}</td>
        </tr>
        """ if transaction_id else ""

        # Prepare notes row
        notes_row = f"""
        <tr style="margin-top: 10px;">
            <td style="padding: 4px 0; color: #9ca3af; font-size: 13px; vertical-align: top;">Booking Notes:</td>
            <td style="padding: 4px 0; color: #d1d5db; font-size: 13px; text-align: right; font-style: italic;">{notes}</td>
        </tr>
        """ if notes else ""

        # HTML template for Customer (Booking Confirmation)
        customer_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Booking Confirmed</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #0b0f19; font-family: 'Inter', Arial, sans-serif; color: #f3f4f6;">
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0b0f19; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="100%" style="max-width: 600px; background-color: #111827; border-radius: 16px; border: 1px solid #1f2937; overflow: hidden; border-spacing: 0; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);">
                            <!-- Header -->
                            <tr>
                                <td align="center" style="padding: 40px 40px 20px 40px; background: linear-gradient(135deg, #111827, #070a13);">
                                    <div style="background-color: rgba(16, 185, 129, 0.1); border-radius: 50%; width: 64px; height: 64px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px; line-height: 64px; text-align: center;">
                                        <span style="color: #10b981; font-size: 32px; font-weight: bold;">✓</span>
                                    </div>
                                    <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">Booking Confirmed!</h1>
                                    <p style="margin: 8px 0 0 0; color: #9ca3af; font-size: 14px;">Thank you for booking with {turf_name}</p>
                                </td>
                            </tr>
                            
                            <!-- Booking Details -->
                            <tr>
                                <td style="padding: 20px 40px 10px 40px;">
                                    <div style="background-color: #1f2937; border-radius: 12px; padding: 24px; border: 1px solid #374151;">
                                        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-spacing: 0; margin-bottom: 12px;">
                                            <tr>
                                                <td style="color: #9ca3af; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 1px;">Booking ID</td>
                                                <td style="color: #10b981; font-size: 16px; font-weight: 700; text-align: right;">{booking_id}</td>
                                            </tr>
                                        </table>
                                        <hr style="border: 0; border-top: 1px solid #374151; margin-bottom: 16px;">
                                        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-spacing: 0;">
                                            <tr>
                                                <td style="padding: 6px 0; color: #9ca3af; font-size: 14px;" width="35%">Location:</td>
                                                <td style="padding: 6px 0; color: #ffffff; font-size: 14px; font-weight: 600;" width="65%">{location_name}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; color: #9ca3af; font-size: 14px; vertical-align: top;">Address:</td>
                                                <td style="padding: 6px 0; color: #d1d5db; font-size: 14px;">{location_address}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; color: #9ca3af; font-size: 14px;">Sport:</td>
                                                <td style="padding: 6px 0; color: #ffffff; font-size: 14px; font-weight: 600; text-transform: capitalize;">{sport_name}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; color: #9ca3af; font-size: 14px;">Date:</td>
                                                <td style="padding: 6px 0; color: #ffffff; font-size: 14px; font-weight: 600;">{date}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; color: #9ca3af; font-size: 14px;">Time Slot:</td>
                                                <td style="padding: 6px 0; color: #ffffff; font-size: 14px; font-weight: 600;">{slot_time}</td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>

                            <!-- Payment & Personal Info -->
                            <tr>
                                <td style="padding: 10px 40px 20px 40px;">
                                    <h3 style="margin: 0 0 12px 0; color: #ffffff; font-size: 16px; font-weight: 600;">Player & Payment Details</h3>
                                    <div style="background-color: #151b2c; border-radius: 12px; padding: 20px; border: 1px solid #1e293b;">
                                        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-spacing: 0;">
                                            <tr>
                                                <td style="padding: 4px 0; color: #9ca3af; font-size: 13px;">Name:</td>
                                                <td style="padding: 4px 0; color: #ffffff; font-size: 13px; text-align: right;">{name}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0; color: #9ca3af; font-size: 13px;">Phone:</td>
                                                <td style="padding: 4px 0; color: #ffffff; font-size: 13px; text-align: right;">{phone}</td>
                                            </tr>
                                            {team_row}
                                            <tr>
                                                <td style="padding: 4px 0; color: #9ca3af; font-size: 13px;">Payment Method:</td>
                                                <td style="padding: 4px 0; color: #ffffff; font-size: 13px; text-align: right;">{payment_method}</td>
                                            </tr>
                                            {transaction_row}
                                            {notes_row}
                                            <tr>
                                                <td colspan="2" style="padding: 12px 0 0 0;"><hr style="border: 0; border-top: 1px solid #1e293b;"></td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 12px 0 0 0; color: #ffffff; font-size: 14px; font-weight: 600;">Total Paid:</td>
                                                <td style="padding: 12px 0 0 0; color: #10b981; font-size: 16px; font-weight: 700; text-align: right;">৳{amount}</td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>

                            <!-- Status -->
                            <tr>
                                <td align="center" style="padding: 0 40px 30px 40px;">
                                    <div style="background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px; padding: 12px 20px; font-size: 13px; font-weight: 500;">
                                        Booking Status: <span style="font-weight: 700; text-transform: uppercase;">{status}</span>
                                        <div style="font-size: 11px; margin-top: 4px; color: #d97706;">Please wait for the administrator to review and approve your booking.</div>
                                    </div>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td align="center" style="padding: 30px 40px; background-color: #0d121f; border-top: 1px solid #1f2937;">
                                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">This is an automated notification from {turf_name}.</p>
                                    <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 11px;">If you have any questions, please contact us at {whatsapp} or reply to this email.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        # Fetch customer's email address
        user_id = booking_data.get('user_id')
        customer_email = None
        if user_id:
            try:
                user = mongo.db.users.find_one({'$or': [{'_id': ObjectId(user_id)}, {'user_id': user_id}]})
                if user:
                    customer_email = user.get('email')
            except Exception as e:
                print(f"Error fetching user email in thread: {e}")

        # Send email to Customer
        if customer_email:
            send_email(customer_email, f"Booking Confirmed: {booking_id} - {turf_name}", customer_html)
        else:
            print(f"Skipping customer email sending: user_id '{user_id}' does not have a registered email or user document was not found.")

        # HTML template for Admin/Location (New Booking Alert)
        try:
            admin_link = url_for('admin.bookings', _external=True)
        except Exception:
            admin_link = "http://localhost:5000/admin/bookings"

        admin_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>New Booking Alert</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #0b0f19; font-family: 'Inter', Arial, sans-serif; color: #f3f4f6;">
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0b0f19; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="100%" style="max-width: 600px; background-color: #111827; border-radius: 16px; border: 1px solid #1f2937; overflow: hidden; border-spacing: 0; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);">
                            <!-- Header -->
                            <tr>
                                <td align="center" style="padding: 40px 40px 20px 40px; background: linear-gradient(135deg, #111827, #070a13);">
                                    <div style="background-color: rgba(59, 130, 246, 0.1); border-radius: 50%; width: 64px; height: 64px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px; line-height: 64px; text-align: center;">
                                        <span style="color: #3b82f6; font-size: 32px; font-weight: bold;">!</span>
                                    </div>
                                    <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">New Booking Request</h1>
                                    <p style="margin: 8px 0 0 0; color: #9ca3af; font-size: 14px;">A new slot has been booked on the website.</p>
                                </td>
                            </tr>
                            
                            <!-- Booking Details -->
                            <tr>
                                <td style="padding: 20px 40px 10px 40px;">
                                    <div style="background-color: #1f2937; border-radius: 12px; padding: 24px; border: 1px solid #374151;">
                                        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-spacing: 0; margin-bottom: 12px;">
                                            <tr>
                                                <td style="color: #9ca3af; font-size: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 1px;">Booking ID</td>
                                                <td style="color: #3b82f6; font-size: 16px; font-weight: 700; text-align: right;">{booking_id}</td>
                                            </tr>
                                        </table>
                                        <hr style="border: 0; border-top: 1px solid #374151; margin-bottom: 16px;">
                                        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-spacing: 0;">
                                            <tr>
                                                <td style="padding: 6px 0; color: #9ca3af; font-size: 14px;" width="35%">Location:</td>
                                                <td style="padding: 6px 0; color: #ffffff; font-size: 14px; font-weight: 600;" width="65%">{location_name}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; color: #9ca3af; font-size: 14px;">Sport:</td>
                                                <td style="padding: 6px 0; color: #ffffff; font-size: 14px; font-weight: 600; text-transform: capitalize;">{sport_name}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; color: #9ca3af; font-size: 14px;">Date:</td>
                                                <td style="padding: 6px 0; color: #ffffff; font-size: 14px; font-weight: 600;">{date}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0; color: #9ca3af; font-size: 14px;">Time Slot:</td>
                                                <td style="padding: 6px 0; color: #ffffff; font-size: 14px; font-weight: 600;">{slot_time}</td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>

                            <!-- Player & Payment Details -->
                            <tr>
                                <td style="padding: 10px 40px 20px 40px;">
                                    <h3 style="margin: 0 0 12px 0; color: #ffffff; font-size: 16px; font-weight: 600;">Player & Payment Details</h3>
                                    <div style="background-color: #151b2c; border-radius: 12px; padding: 20px; border: 1px solid #1e293b;">
                                        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-spacing: 0;">
                                            <tr>
                                                <td style="padding: 4px 0; color: #9ca3af; font-size: 13px;">Name:</td>
                                                <td style="padding: 4px 0; color: #ffffff; font-size: 13px; text-align: right;">{name}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0; color: #9ca3af; font-size: 13px;">Phone:</td>
                                                <td style="padding: 4px 0; color: #ffffff; font-size: 13px; text-align: right;"><a href="tel:{phone}" style="color: #3b82f6; text-decoration: none;">{phone}</a></td>
                                            </tr>
                                            {team_row}
                                            <tr>
                                                <td style="padding: 4px 0; color: #9ca3af; font-size: 13px;">Payment Method:</td>
                                                <td style="padding: 4px 0; color: #ffffff; font-size: 13px; text-align: right;">{payment_method}</td>
                                            </tr>
                                            {transaction_row}
                                            {notes_row}
                                            <tr>
                                                <td colspan="2" style="padding: 12px 0 0 0;"><hr style="border: 0; border-top: 1px solid #1e293b;"></td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 12px 0 0 0; color: #ffffff; font-size: 14px; font-weight: 600;">Amount To Verify:</td>
                                                <td style="padding: 12px 0 0 0; color: #3b82f6; font-size: 16px; font-weight: 700; text-align: right;">৳{amount}</td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                            </tr>

                            <!-- Call to Action -->
                            <tr>
                                <td align="center" style="padding: 10px 40px 30px 40px;">
                                    <div style="margin: 20px 0;">
                                        <a href="{admin_link}" style="background-color: #3b82f6; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 14px;">Open Booking Dashboard</a>
                                    </div>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td align="center" style="padding: 30px 40px; background-color: #0d121f; border-top: 1px solid #1f2937;">
                                    <p style="margin: 0; color: #9ca3af; font-size: 12px;">This is an admin notification for {location_name}.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        # Resolve admin email address
        admin_email = None
        if location and location.get('email'):
            admin_email = location.get('email')
            
        if not admin_email:
            if settings and settings.get('email'):
                admin_email = settings.get('email')
                
        if not admin_email:
            admin_email = os.environ.get('EMAIL_SENDER') or os.environ.get('EMAIL_USERNAME')

        # Send email to Admin/Location
        if admin_email:
            send_email(admin_email, f"[NEW BOOKING] {booking_id} - {location_name} - {date}", admin_html)
        else:
            print("Skipping admin email sending: Admin email could not be resolved.")

    except Exception as ex:
        print(f"Error sending booking emails in background thread: {ex}")
        import traceback
        traceback.print_exc()
    finally:
        if app:
            ctx.pop()

