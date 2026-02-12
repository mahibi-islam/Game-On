from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from bson import ObjectId
from datetime import datetime
from functools import wraps
from models.admin import Admin
from models.booking import Booking
from models.slot import Slot
from models.settings import Settings
from utils.slot_utils import sort_slots, get_bangladesh_now, get_bangladesh_tz
from db import mongo
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== Authentication ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.find_by_username(username)
        # If admin not found, attempt to initialize defaults and retry
        if not admin:
            try:
                Admin.init_defaults()
                admin = Admin.find_by_username(username)
            except Exception:
                admin = None
        if admin and Admin.verify_password(admin, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.clear()
    return redirect(url_for('admin.login'))

# ==================== Dashboard ====================

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    now_bangladesh = get_bangladesh_now()
    today = now_bangladesh.strftime('%Y-%m-%d')
    today_bookings = Booking.count({'date': today})
    upcoming_bookings = Booking.count({
        'date': {'$gte': today},
        'status': {'$in': ['pending', 'approved', 'paid']}
    })
    
    # Calculate total earnings
    paid_bookings = Booking.find_all({'status': 'paid'})
    total_earnings = sum(b.get('amount', 0) for b in paid_bookings)
    
    # Popular slots
    pipeline = [
        {'$match': {'status': {'$in': ['pending', 'approved', 'paid']}}},
        {'$group': {'_id': '$time_slot', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    popular_slots = list(Booking.aggregate(pipeline))
    
    # Enrich popular slots with slot details
    for slot_data in popular_slots:
        slot = Slot.find_by_id(slot_data['_id'])
        if slot:
            slot_data['time'] = slot.get('time', 'N/A')
            slot_data['sport'] = slot.get('sport', 'N/A').title()
        else:
            slot_data['time'] = 'N/A'
            slot_data['sport'] = 'N/A'
    
    recent_bookings = Booking.find_all(sort=[('created_at', -1)], limit=10)
    
    # Get slot details for recent bookings
    for booking in recent_bookings:
        slot_id = booking.get('time_slot')
        slot = Slot.find_by_id(slot_id) if slot_id else None
        booking['slot_time'] = slot['time'] if slot else 'N/A'
    
    # Data for Slot Performance (Bar Chart)
    # We already have popular_slots, let's use all slots that have bookings
    all_slot_counts = list(Booking.aggregate([
        {'$match': {'status': {'$in': ['pending', 'approved', 'paid']}}},
        {'$group': {'_id': '$time_slot', 'count': {'$sum': 1}}}
    ]))
    
    performance_labels = []
    performance_values = []
    
    # Categorization for Booking Distribution (Pie Chart)
    distribution = {
        'Morning': 0,    # 06:00 - 12:00
        'Afternoon': 0,  # 12:00 - 18:00
        'Evening': 0,    # 18:00 - 21:00
        'Night': 0       # 21:00 - 06:00
    }
    
    for item in all_slot_counts:
        slot = Slot.find_by_id(item['_id'])
        if slot:
            time_str = slot.get('time', 'N/A')
            sport_name = slot.get('sport', 'football').title()
            performance_labels.append(f"{time_str} ({sport_name})")
            performance_values.append(item['count'])
            
            # Categorize based on start hour
            try:
                start_hour = int(time_str.split(':')[0])
                if 6 <= start_hour < 12:
                    distribution['Morning'] += item['count']
                elif 12 <= start_hour < 18:
                    distribution['Afternoon'] += item['count']
                elif 18 <= start_hour < 21:
                    distribution['Evening'] += item['count']
                else:
                    distribution['Night'] += item['count']
            except (ValueError, IndexError):
                pass

    return render_template('admin/dashboard.html',
                         today_bookings=today_bookings,
                         upcoming_bookings=upcoming_bookings,
                         total_earnings=total_earnings,
                         popular_slots=popular_slots,
                         recent_bookings=recent_bookings,
                         performance_labels=performance_labels,
                         performance_values=performance_values,
                         distribution_labels=list(distribution.keys()),
                         distribution_values=list(distribution.values()))

# ==================== Bookings Management ====================

@admin_bp.route('/bookings')
@admin_required
def bookings():
    """View all bookings"""
    filter_type = request.args.get('filter', 'all')
    now_bangladesh = get_bangladesh_now()
    today = now_bangladesh.strftime('%Y-%m-%d')
    
    query = {}
    if filter_type == 'today':
        query['date'] = today
    elif filter_type == 'pending':
        query['status'] = 'pending'
    elif filter_type == 'approved':
        query['status'] = 'approved'
    
    bookings_list = Booking.find_all(query, sort=[('created_at', -1)])
    
    # Get slot details for each booking
    for booking in bookings_list:
        slot_id = booking.get('time_slot')
        slot = Slot.find_by_id(slot_id) if slot_id else None
        booking['slot_time'] = slot['time'] if slot else 'N/A'
        
        # Fallback for missing booking_id
        if not booking.get('booking_id'):
            booking['booking_id'] = f"LEGACY_{str(booking['_id'])[-6:]}"
            
        # Compute played display if past slot start and not cancelled
        try:
            date_str = booking.get('date')
            slot_time = slot['time'] if slot else None
            status = booking.get('status')
            played = False
            if date_str and slot_time:
                start_part = slot_time.split('-')[0]
                h, m = [int(x) for x in start_part.split(':')]
                slot_start = datetime.strptime(date_str, '%Y-%m-%d').replace(hour=h, minute=m, second=0, microsecond=0, tzinfo=get_bangladesh_tz())
                played = now_bangladesh >= slot_start and status != 'cancelled'
            booking['status_display'] = 'played' if played else status
        except Exception:
            booking['status_display'] = booking.get('status')
    
    return render_template('admin/bookings.html', bookings=bookings_list, filter_type=filter_type)

@admin_bp.route('/booking/<booking_id>/<action>', methods=['POST'])
@admin_required
def update_booking(booking_id, action):
    """Update booking status"""
    booking = Booking.find_by_id(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    if action == 'approve':
        Booking.update(booking_id, {'status': 'approved'})
    elif action == 'cancel':
        # Prevent cancelling if slot already passed
        slot = Slot.find_by_id(booking.get('time_slot')) if booking.get('time_slot') else None
        if slot and booking.get('date'):
            try:
                start_part = slot['time'].split('-')[0]
                h, m = [int(x) for x in start_part.split(':')]
                slot_start = datetime.strptime(booking['date'], '%Y-%m-%d').replace(hour=h, minute=m, second=0, microsecond=0, tzinfo=get_bangladesh_tz())
                if get_bangladesh_now() >= slot_start:
                    return jsonify({'error': 'Cannot cancel a past slot'}), 400
            except Exception:
                pass
        Booking.update(booking_id, {'status': 'cancelled'})
    elif action == 'paid':
        Booking.update(booking_id, {'status': 'paid'})
    elif action == 'pending':
        Booking.update(booking_id, {'status': 'pending'})
    
    return jsonify({'success': True})

@admin_bp.route('/booking/create', methods=['GET', 'POST'])
@admin_required
def create_manual_booking():
    """Create manual booking"""
    if request.method == 'POST':
        data = request.form
        slot = Slot.find_by_id(data.get('time_slot'))
        
        if not slot:
            flash('Invalid time slot', 'error')
            return redirect(url_for('admin.create_manual_booking'))
        
        booking_data = {
            'date': data.get('date'),
            'time_slot': data.get('time_slot'),
            'name': data.get('name'),
            'phone': data.get('phone'),
            'team_name': data.get('team_name', ''),
            'payment_method': data.get('payment_method'),
            'transaction_id': data.get('transaction_id', ''),
            'amount': slot['price'] * (1 - float(slot.get('discount_percent', 0)) / 100) if slot.get('discount_active') else slot['price'],
            'status': 'approved',
            'notes': data.get('notes', '')
        }
        
        Booking.create(booking_data)
        flash('Booking created successfully', 'success')
        return redirect(url_for('admin.bookings'))
    
    slots = Slot.find_all({'enabled': True})
    slots = sort_slots(slots)
    return render_template('admin/create_booking.html', slots=slots)

# ==================== Slots Management ====================

@admin_bp.route('/slots')
@admin_required
def slots():
    """View all slots"""
    football_slots = Slot.find_all({'sport': 'football'})
    badminton_slots = Slot.find_all({'sport': 'badminton'})
    
    football_slots = sort_slots(football_slots)
    badminton_slots = sort_slots(badminton_slots)
    
    return render_template('admin/slots.html', football_slots=football_slots, badminton_slots=badminton_slots)

@admin_bp.route('/slot/create', methods=['POST'])
@admin_required
def create_slot():
    """Create new slot"""
    data = request.json
    Slot.create(data)
    return jsonify({'success': True})

@admin_bp.route('/slot/<slot_id>/update', methods=['POST'])
@admin_required
def update_slot(slot_id):
    """Update slot"""
    data = request.json
    Slot.update(slot_id, {
        'time': data.get('time'),
        'price': float(data.get('price')),
        'sport': data.get('sport', 'football'),
        'rate_type': data.get('rate_type', 'weekday'),
        'enabled': data.get('enabled', True),
        'discount_active': data.get('discount_active', False),
        'discount_percent': float(data.get('discount_percent', 0.0))
    })
    return jsonify({'success': True})

# ==================== Calendar ====================

@admin_bp.route('/calendar')
@admin_required
def calendar():
    """Calendar view"""
    return render_template('admin/calendar.html')

# ==================== Gallery Management ====================

@admin_bp.route('/gallery')
@admin_required
def gallery():
    """Gallery management"""
    try:
        images = list(mongo.db.gallery.find({'type': 'image'}))
        videos = list(mongo.db.gallery.find({'type': 'video'}))
    except Exception:
        images = []
        videos = []
    return render_template('admin/gallery.html', images=images, videos=videos)

@admin_bp.route('/gallery/upload', methods=['POST'])
@admin_required
def upload_gallery():
    """Upload gallery item"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    file_type = request.form.get('type', 'image')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join('static/gallery', filename)
    file.save(filepath)
    
    mongo.db.gallery.insert_one({
        'filename': filename,
        'path': f'gallery/{filename}',
        'type': file_type,
        'uploaded_at': get_bangladesh_now()
    })
    
    return jsonify({'success': True, 'filename': filename})

@admin_bp.route('/gallery/delete/<gallery_id>', methods=['POST'])
@admin_required
def delete_gallery_item(gallery_id):
    """Delete gallery item"""
    item = mongo.db.gallery.find_one({'_id': ObjectId(gallery_id)})
    if item:
        filepath = os.path.join('static', item['path'])
        if os.path.exists(filepath):
            os.remove(filepath)
        mongo.db.gallery.delete_one({'_id': ObjectId(gallery_id)})
    return jsonify({'success': True})

# ==================== Payments Management ====================

@admin_bp.route('/payments')
@admin_required
def payments():
    """Payments management"""
    bookings_list = Booking.find_all(sort=[('created_at', -1)])
    for booking in bookings_list:
        slot_id = booking.get('time_slot')
        slot = Slot.find_by_id(slot_id) if slot_id else None
        booking['slot_time'] = slot['time'] if slot else 'N/A'
    return render_template('admin/payments.html', bookings=bookings_list)

# ==================== Carousel Management ====================

@admin_bp.route('/settings/carousel/upload', methods=['POST'])
@admin_required
def upload_carousel_image():
    """Upload carousel image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(f"{int(get_bangladesh_now().timestamp())}_{file.filename}")
    filepath = os.path.join('static/carousel', filename)
    file.save(filepath)
    
    # Update settings
    settings = Settings.find_one()
    images = settings.get('carousel_images', []) if settings else []
    images.append(filename)
    Settings.update({'carousel_images': images})
    
    return jsonify({'success': True, 'filename': filename})

@admin_bp.route('/settings/carousel/delete/<filename>', methods=['POST'])
@admin_required
def delete_carousel_image(filename):
    """Delete carousel image"""
    filepath = os.path.join('static/carousel', secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Update settings
    settings = Settings.find_one()
    images = settings.get('carousel_images', []) if settings else []
    if filename in images:
        images.remove(filename)
        Settings.update({'carousel_images': images})
        
    return jsonify({'success': True})

# ==================== Settings ====================

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Settings management"""
    if request.method == 'POST':
        Settings.update({
            'turf_name': request.form.get('turf_name'),
            'address': request.form.get('address'),
            'phone': request.form.get('phone'),
            'whatsapp': request.form.get('whatsapp'),
            'email': request.form.get('email'),
            'facebook': request.form.get('facebook'),
            'rules': request.form.get('rules'),
            'homepage_content': request.form.get('homepage_content')
        })
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin.settings'))
    
    settings = Settings.find_one()
    return render_template('admin/settings.html', settings=settings)

# ==================== Export ====================

@admin_bp.route('/export')
@admin_required
def export():
    """Export bookings to Excel"""
    excel_file = Booking.get_excel_file_path()
    return send_file(excel_file, as_attachment=True, download_name='bookings.xlsx')

# ==================== Messages Management ====================

@admin_bp.route('/messages')
@admin_required
def messages():
    """View contact messages"""
    from models.contact_message import ContactMessage
    messages = ContactMessage.find_all()
    # Format date for display
    for msg in messages:
        if 'created_at' in msg and isinstance(msg['created_at'], datetime):
            msg['display_date'] = msg['created_at'].strftime('%Y-%m-%d %H:%M')
        else:
            msg['display_date'] = 'N/A'
    return render_template('admin/messages.html', messages=messages)

@admin_bp.route('/messages/delete/<message_id>', methods=['POST'])
@admin_required
def delete_message(message_id):
    """Delete a contact message"""
    from models.contact_message import ContactMessage
    ContactMessage.delete(message_id)
    flash('Message deleted successfully.', 'success')
    return redirect(url_for('admin.messages'))

