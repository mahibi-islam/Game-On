from db import mongo
from datetime import datetime
from bson import ObjectId
from utils.slot_utils import get_bangladesh_now
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import os
import urllib.parse
from flask import current_app
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

class Booking:
    """Booking model with database operations"""
    COLLECTION = 'bookings'
    
    @staticmethod
    def get_collection():
        return mongo.db.bookings
    
    @staticmethod
    def get_next_sequence():
        """Get the next sequential ID for bookings"""
        result = mongo.db.counters.find_one_and_update(
            {'_id': 'booking_id'},
            {'$inc': {'sequence_value': 1}},
            upsert=True,
            return_document=True
        )
        return result['sequence_value']

    @staticmethod
    def create(data):
        """Create a new booking"""
        next_seq = Booking.get_next_sequence()
        booking_id_str = f"GAMEON#{next_seq}" 
        
        booking_data = {
            'booking_id': booking_id_str,
            'date': data.get('date'),
            'time_slot': data.get('time_slot'),
            'name': data.get('name'),
            'phone': data.get('phone'),
            'team_name': data.get('team_name', ''),
            'payment_method': data.get('payment_method'),
            'transaction_id': data.get('transaction_id', ''),
            'amount': data.get('amount'),
            'status': data.get('status', 'pending'),
            'notes': data.get('notes', ''),
            'created_at': get_bangladesh_now().isoformat(),
            'location_id': ObjectId(data.get('location_id')) if data.get('location_id') else None,
            'user_id': data.get('user_id')
        }
        result = Booking.get_collection().insert_one(booking_data)
        booking_data['_id'] = str(result.inserted_id)
        if booking_data.get('location_id'):
            booking_data['location_id'] = str(booking_data['location_id'])
        
        # Write to Excel
        Booking.write_to_excel(booking_data)
        
        # Send WhatsApp notification
        Booking.send_whatsapp_notification(booking_data)
        
        # Send email notifications
        try:
            from utils.email_utils import send_booking_emails
            send_booking_emails(booking_data)
        except Exception as e:
            print(f"Error calling send_booking_emails: {e}")
            
        return booking_data
    
    @staticmethod
    def find_by_id(booking_id):
        """Find booking by ID"""
        return Booking.get_collection().find_one({'_id': ObjectId(booking_id)})
    
    @staticmethod
    def find_by_date_and_slot(date, time_slot, exclude_booking_id=None):
        """Find booking by date and time slot"""
        query = {
            'date': date,
            'status': {'$in': ['pending', 'approved', 'paid']}
        }
        
        if exclude_booking_id:
            try:
                ex_id = ObjectId(exclude_booking_id) if isinstance(exclude_booking_id, str) and len(exclude_booking_id) == 24 else exclude_booking_id
                query['_id'] = {'$ne': ex_id}
            except Exception:
                query['_id'] = {'$ne': exclude_booking_id}

        # Handle string vs ObjectId for time_slot by checking both
        if isinstance(time_slot, (str, ObjectId)):
            ts_str = str(time_slot)
            if len(ts_str) == 24:
                query['time_slot'] = {'$in': [ts_str, ObjectId(ts_str)]}
            else:
                query['time_slot'] = time_slot
        else:
            query['time_slot'] = time_slot
            
        return Booking.get_collection().find_one(query)
    
    @staticmethod
    def find_all(query=None, sort=None, limit=None):
        """Find all bookings matching query"""
        cursor = Booking.get_collection().find(query or {})
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    @staticmethod
    def update(booking_id, data):
        """Update booking"""
        result = Booking.get_collection().update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': data}
        )
        # Update Excel
        booking = Booking.find_by_id(booking_id)
        if booking:
            booking.update(data)
            Booking.update_in_excel(booking_id, booking)
        return result
    
    @staticmethod
    def count(query=None):
        """Count bookings"""
        return Booking.get_collection().count_documents(query or {})
    
    @staticmethod
    def aggregate(pipeline):
        """Aggregate bookings"""
        return list(Booking.get_collection().aggregate(pipeline))
    
    @staticmethod
    def get_excel_file_path():
        """Get Excel file path"""
        return current_app.config.get('EXCEL_FILE', 'bookings.xlsx') if current_app else 'bookings.xlsx'
    
    @staticmethod
    def get_google_sheet():
        """Get Google Sheets client and worksheet if configured"""
        if not GSPREAD_AVAILABLE:
            print("Google Sheets: gspread library not available")
            return None
        
        if not current_app:
            print("Google Sheets: No Flask app context")
            return None
            
        sheets_url = current_app.config.get('GOOGLE_SHEETS_URL')
        creds_file = current_app.config.get('GOOGLE_SHEETS_CREDENTIALS_FILE')
        
        print(f"Google Sheets Config Check:")
        print(f"  - GOOGLE_SHEETS_URL: {sheets_url}")
        print(f"  - GOOGLE_SHEETS_CREDENTIALS_FILE: {creds_file}")
        print(f"  - Credentials file exists: {os.path.exists(creds_file) if creds_file else False}")
        
        if not sheets_url:
            print("Google Sheets: GOOGLE_SHEETS_URL not configured in .env")
            return None
            
        if not creds_file:
            print("Google Sheets: GOOGLE_SHEETS_CREDENTIALS_FILE not configured in .env")
            return None
            
        if not os.path.exists(creds_file):
            print(f"Google Sheets: Credentials file not found at: {creds_file}")
            return None
        
        try:
            print("Google Sheets: Attempting to connect...")
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
            client = gspread.authorize(creds)
            
           
            print(f"Google Sheets: Opening spreadsheet from URL: {sheets_url}")
            spreadsheet = client.open_by_url(sheets_url)
            worksheet = spreadsheet.sheet1
            print(f"Google Sheets: Successfully connected to '{spreadsheet.title}' - Sheet: {worksheet.title}")
            return worksheet
        except Exception as e:
            print(f"Google Sheets ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def init_google_sheet():
        """Initialize Google Sheet with headers if empty"""
        worksheet = Booking.get_google_sheet()
        if not worksheet:
            return False
        
        try:
            # Check if headers exist
            if not worksheet.row_values(1):
                headers = [
                    'Booking ID', 'Date', 'Location', 'Time Slot', 'Name', 'Phone', 
                    'Team Name', 'Payment Method', 'Amount', 'Status', 
                    'Transaction ID', 'Notes', 'Created At'
                ]
                worksheet.append_row(headers)
                # Format header row
                worksheet.format('A1:M1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.38, 'blue': 0.57},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                })
            return True
        except Exception as e:
            print(f"Error initializing Google Sheet: {e}")
            return False
    
    @staticmethod
    def init_excel():
        """Initialize Excel file if it doesn't exist"""
    
        excel_file = Booking.get_excel_file_path()
        if not os.path.exists(excel_file):
            wb = Workbook()
            ws = wb.active
            ws.title = "Bookings"
            headers = [
                'Booking ID', 'Date', 'Location', 'Time Slot', 'Name', 'Phone', 
                'Team Name', 'Payment Method', 'Amount', 'Status', 
                'Transaction ID', 'Notes', 'Created At'
            ]
            ws.append(headers)
            
            # Style headers
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")
            
            wb.save(excel_file)
        
 
        Booking.init_google_sheet()
    
    @staticmethod
    def write_to_excel(booking_data):
        """Write booking to Excel and Google Sheets"""
        
        from models.slot import Slot
        from models.location import Location
        slot_id = booking_data.get('time_slot')
        slot = None
        if slot_id:
            try:
                if isinstance(slot_id, str) and len(slot_id) == 24:
                    slot = Slot.find_by_id(slot_id)
                elif isinstance(slot_id, ObjectId):
                    slot = Slot.find_by_id(str(slot_id))
            except Exception as e:
                print(f"Debug: Slot fetch error: {e}")
                slot = None
        
        slot_time = slot.get('time', 'N/A') if slot else 'N/A'
        
        # Resolve location name
        location_name = 'N/A'
        loc_id = booking_data.get('location_id')
        if not loc_id and slot:
            loc_id = slot.get('location_id')
        if loc_id:
            loc = Location.find_by_id(str(loc_id))
            if loc:
                location_name = loc.get('name', 'N/A')
        
     
        display_id = booking_data.get('booking_id')
        if not display_id:
            # Fallback for old ones
            display_id = str(booking_data.get('_id', ''))
            if len(display_id) > 10: # It's a hash
                display_id = f"LEGACY_{display_id[-6:]}"
        
      
        if display_id and not display_id.startswith('#'):
            display_id = f"#{display_id}"

        print(f"Debug: Exporting Booking - ID: {display_id}, Location: {location_name}, Time: {slot_time}")

      
        try:
            excel_file = Booking.get_excel_file_path()
            if not os.path.exists(excel_file):
                print(f"Excel file not found, initializing: {excel_file}")
                Booking.init_excel()
            
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            row = [
                display_id,
                booking_data.get('date', ''),
                location_name,
                slot_time,
                booking_data.get('name', ''),
                booking_data.get('phone', ''),
                booking_data.get('team_name', ''),
                booking_data.get('payment_method', ''),
                booking_data.get('amount', ''),
                booking_data.get('status', ''),
                booking_data.get('transaction_id', ''),
                booking_data.get('notes', ''),
                booking_data.get('created_at', '')
            ]
            ws.append(row)
            wb.save(excel_file)
            print(f"Successfully wrote booking to Excel: {excel_file}")
        except Exception as e:
            print(f"ERROR writing to local Excel file: {e}")
            import traceback
            traceback.print_exc()
        
        # Sync to Google Sheets if configured
        try:
            print("\n=== Attempting Google Sheets Sync ===")
            worksheet = Booking.get_google_sheet()
            if worksheet:
                print("Google Sheets: Writing booking data...")
                worksheet.append_row(row)
                print("✓ Successfully synced booking to Google Sheets")
            else:
                print("Google Sheets: Skipped (not configured or connection failed)")
            print("=== Google Sheets Sync Complete ===\n")
        except Exception as e:
            print(f"Google Sheets Sync ERROR: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def update_in_excel(booking_id, updated_data):
        """Update booking in Excel and Google Sheets"""
   
        from models.slot import Slot
        from models.location import Location
        slot_id = updated_data.get('time_slot')
        slot = None
        if slot_id:
            try:
                if isinstance(slot_id, str) and len(slot_id) == 24:
                    slot = Slot.find_by_id(slot_id)
                elif isinstance(slot_id, ObjectId):
                    slot = Slot.find_by_id(str(slot_id))
            except Exception as e:
                print(f"Debug: Slot fetch error during update: {e}")
                slot = None
        slot_time = slot.get('time', '') if slot else ''

        # Resolve location name
        location_name = ''
        loc_id = updated_data.get('location_id')
        if not loc_id and slot:
            loc_id = slot.get('location_id')
        if loc_id:
            loc = Location.find_by_id(str(loc_id))
            if loc:
                location_name = loc.get('name', '')
        
        try:
            excel_file = Booking.get_excel_file_path()
            if not os.path.exists(excel_file):
                print(f"Excel file not found for update: {excel_file}")
                return
                
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            found = False
            id_to_find = str(booking_id)
            alt_id = updated_data.get('booking_id', '')
            if alt_id and not alt_id.startswith('$'):
                alt_id = f"#{alt_id}"
            
            for row in ws.iter_rows(min_row=2, values_only=False):
               
                if row[0].value == id_to_find or row[0].value == alt_id or (isinstance(row[0].value, str) and row[0].value.replace('#','') == alt_id.replace('#','')):
                    row[1].value = updated_data.get('date', row[1].value)
                    if location_name:
                        row[2].value = location_name
                    if slot_time:
                        row[3].value = slot_time
                    row[4].value = updated_data.get('name', row[4].value)
                    row[5].value = updated_data.get('phone', row[5].value)
                    row[6].value = updated_data.get('team_name', row[6].value)
                    row[7].value = updated_data.get('payment_method', row[7].value)
                    row[8].value = updated_data.get('amount', row[8].value)
                    row[9].value = updated_data.get('status', row[9].value)
                    row[10].value = updated_data.get('transaction_id', row[10].value)
                    row[11].value = updated_data.get('notes', row[11].value)
                    found = True
                    break
            
            wb.save(excel_file)
            if found:
                print(f"Successfully updated booking in Excel: {booking_id}")
            else:
                print(f"Booking ID not found in Excel: {booking_id}")
        except Exception as e:
            print(f"ERROR updating local Excel file: {e}")
            import traceback
            traceback.print_exc()
       
        try:
            worksheet = Booking.get_google_sheet()
            if worksheet:
          
                search_query = alt_id if alt_id else id_to_find
                cell = worksheet.find(search_query)
                if cell:
                    row_num = cell.row
                    if updated_data.get('date'): worksheet.update_cell(row_num, 2, updated_data.get('date'))
                    if location_name: worksheet.update_cell(row_num, 3, location_name)
                    if slot_time: worksheet.update_cell(row_num, 4, slot_time)
                    if updated_data.get('name'): worksheet.update_cell(row_num, 5, updated_data.get('name'))
                    if updated_data.get('phone'): worksheet.update_cell(row_num, 6, updated_data.get('phone'))
                    if updated_data.get('team_name'): worksheet.update_cell(row_num, 7, updated_data.get('team_name'))
                    if updated_data.get('payment_method'): worksheet.update_cell(row_num, 8, updated_data.get('payment_method'))
                    if updated_data.get('amount'): worksheet.update_cell(row_num, 9, updated_data.get('amount'))
                    if updated_data.get('status'): worksheet.update_cell(row_num, 10, updated_data.get('status'))
                    if updated_data.get('transaction_id'): worksheet.update_cell(row_num, 11, updated_data.get('transaction_id'))
                    if updated_data.get('notes'): worksheet.update_cell(row_num, 12, updated_data.get('notes'))
        except Exception as e:
            print(f"Error updating Google Sheets: {e}")
    
    @staticmethod
    def send_whatsapp_notification(booking_data):
        """Send WhatsApp notification about booking"""
        try:
            from models.settings import Settings
            settings = Settings.find_one()
            if not settings or not settings.get('whatsapp'):
                return None
            
            from models.slot import Slot
            slot = Slot.find_by_id(booking_data.get('time_slot'))
            slot_time = slot.get('time', 'N/A') if slot else 'N/A'
            
            whatsapp_number = settings['whatsapp'].replace('+', '').replace(' ', '').replace('-', '')
            
            message = f""" *Booking Confirmed!*

 *Date:* {booking_data.get('date', 'N/A')}
 *Time Slot:* {slot_time}
 *Name:* {booking_data.get('name', 'N/A')}
 *Phone:* {booking_data.get('phone', 'N/A')}
 *Amount:* ৳{booking_data.get('amount', 'N/A')}
 *Payment:* {booking_data.get('payment_method', 'N/A')}
 *Booking ID:* #{booking_data.get('booking_id', booking_data.get('_id', 'N/A'))}

Thank you for your booking!"""
            
            whatsapp_url = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(message)}"
            print(f"WhatsApp notification URL: {whatsapp_url}")
            return whatsapp_url
            
        except Exception as e:
            print(f"Error sending WhatsApp notification: {e}")
            return None
    
    @staticmethod
    def init_defaults():
        """Initialize default data"""
        pass

