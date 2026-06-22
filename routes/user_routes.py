from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.settings import Settings
from models.booking import Booking
from models.slot import Slot
from models.user import get_current_user
from db import mongo
from datetime import datetime, timedelta
from bson import ObjectId
from utils.slot_utils import sort_slots, get_bangladesh_now, get_bangladesh_tz

user_bp = Blueprint('user', __name__)

@user_bp.route('/')
def index():
    """Home page"""
    settings = Settings.find_one()
    try:
        testimonials = list(mongo.db.testimonials.find().limit(3))
        gallery_images = list(mongo.db.gallery.find({'type': 'image'}).limit(6))
    except Exception:
        testimonials = []
        gallery_images = []
    return render_template('index.html', settings=settings, testimonials=testimonials, gallery_images=gallery_images)

@user_bp.route('/booking')
def booking():
    """Booking page"""
    loc_param = request.args.get('location')
    sport_param = request.args.get('sport')
    date_param = request.args.get('date')
    slot_param = request.args.get('slot')
    
    settings = Settings.find_one()
    user = get_current_user()
    return render_template('booking.html', settings=settings, user=user, 
                           preselected_location_id=loc_param,
                           preselected_sport=sport_param,
                           preselected_date=date_param,
                           preselected_slot_id=slot_param)


@user_bp.route('/profile')
def profile():
    """User profile with booking history"""
    if not session.get('user_logged_in'):
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('auth.login', next=url_for('user.profile')))

    settings = Settings.find_one()
    user = get_current_user()

    session_user_id = session.get('user_id')
    user_id_query = {'$or': [{'user_id': session_user_id}]}
    try:
        user_id_query['$or'].append({'user_id': ObjectId(session_user_id)})
    except Exception:
        pass
    # Fallback: match by phone if old bookings lack user_id
    if user and user.get('phone'):
        user_id_query['$or'].append({'phone': user.get('phone')})

    bookings = Booking.find_all(user_id_query, sort=[('created_at', -1)])
    
    # Collect all slot IDs
    slot_ids = set()
    for booking in bookings:
        if booking.get('time_slot'):
            slot_ids.add(booking['time_slot'])
            
    # Fetch all slots in a single query
    slot_object_ids = []
    for sid in slot_ids:
        if isinstance(sid, ObjectId):
            slot_object_ids.append(sid)
        elif isinstance(sid, str) and len(sid) == 24:
            slot_object_ids.append(ObjectId(sid))
        else:
            slot_object_ids.append(sid)
            
    slots_list = Slot.find_all({'_id': {'$in': slot_object_ids}})
    slots_map = {str(s['_id']): s for s in slots_list}
    
    # Collect all location IDs
    loc_ids = set()
    for slot in slots_list:
        if slot.get('location_id'):
            loc_ids.add(slot['location_id'])
    for booking in bookings:
        if booking.get('location_id'):
            loc_ids.add(booking['location_id'])
            
    # Fetch all locations in a single query
    loc_object_ids = []
    for lid in loc_ids:
        if isinstance(lid, ObjectId):
            loc_object_ids.append(lid)
        elif isinstance(lid, str) and len(lid) == 24:
            loc_object_ids.append(ObjectId(lid))
        else:
            loc_object_ids.append(lid)
            
    from models.location import Location
    locations_list = Location.find_all({'_id': {'$in': loc_object_ids}})
    locations_map = {str(l['_id']): l for l in locations_list}
    
    # Helper to get slot/location safely
    def get_slot(sid):
        return slots_map.get(str(sid)) if sid else None
        
    def get_location(lid):
        return locations_map.get(str(lid)) if lid else None
        
    now_bangladesh = get_bangladesh_now()
    today = now_bangladesh.date()
    bookings_view = []

    for booking in bookings:
        booking_copy = dict(booking)
        booking_copy['_id'] = str(booking.get('_id')) if booking.get('_id') else ''

        # Attach slot time and location for readability
        slot = get_slot(booking.get('time_slot'))
        booking_copy['slot_time'] = slot['time'] if slot else 'N/A'

        loc_id = booking.get('location_id') or (slot.get('location_id') if slot else None)
        location = get_location(loc_id)
        booking_copy['location_name'] = location.get('name') if location else 'N/A'

        # Determine cancel eligibility (>= 48 hours before slot start and not already cancelled)
        can_cancel = False
        date_str = booking.get('date')
        slot_time_str = slot['time'] if slot else None
        if date_str and slot_time_str:
            try:
                start_time_part = slot_time_str.split('-')[0]
                start_hour, start_minute = [int(x) for x in start_time_part.split(':')]
                slot_start_dt = datetime.strptime(date_str, '%Y-%m-%d')
                slot_start_dt = slot_start_dt.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0, tzinfo=get_bangladesh_tz())
                can_cancel = (slot_start_dt - now_bangladesh) >= timedelta(hours=48) and booking.get('status') != 'cancelled'
            except Exception:
                can_cancel = False
        booking_copy['can_cancel'] = can_cancel

        # Display status: show 'played' if slot start is in the past and not cancelled
        try:
            if date_str and slot_time_str:
                start_time_part = slot_time_str.split('-')[0]
                start_hour, start_minute = [int(x) for x in start_time_part.split(':')]
                slot_start_dt = datetime.strptime(date_str, '%Y-%m-%d').replace(hour=start_hour, minute=start_minute, second=0, microsecond=0, tzinfo=get_bangladesh_tz())
                if now_bangladesh >= slot_start_dt and booking.get('status') != 'cancelled':
                    booking_copy['status_display'] = 'played'
                else:
                    booking_copy['status_display'] = booking.get('status')
            else:
                booking_copy['status_display'] = booking.get('status')
        except Exception:
            booking_copy['status_display'] = booking.get('status')

        bookings_view.append(booking_copy)

    return render_template('profile.html', user=user, bookings=bookings_view, settings=settings)

@user_bp.route('/profile/update', methods=['POST'])
def update_profile():
    """Update user profile"""
    if not session.get('user_logged_in'):
        return redirect(url_for('auth.login'))
    
    from models.user import update_details
    
    user_id = session.get('user_id')
    data = request.form
    
    success = update_details(user_id, {
        'first_name': data.get('first_name'),
        'last_name': data.get('last_name'),
        'phone': data.get('phone')
    })
    
    if success:
        flash('Profile updated successfully!', 'success')
    else:
        flash('No changes made or update failed.', 'info')
        
    return redirect(url_for('user.profile'))

@user_bp.route('/availability')
def availability():
    """Availability page"""
    return render_template('availability.html')

@user_bp.route('/pricing')
def pricing():
    """Pricing page"""
    football_slots = Slot.find_all({'enabled': True, 'sport': 'football'})
    badminton_slots = Slot.find_all({'enabled': True, 'sport': 'badminton'})
    
    football_slots = sort_slots(football_slots)
    badminton_slots = sort_slots(badminton_slots)
    
    preselected_location_id = request.args.get('location')
    
    return render_template('pricing.html', football_slots=football_slots, badminton_slots=badminton_slots, preselected_location_id=preselected_location_id)

@user_bp.route('/facilities')
def facilities():
    """Facilities page"""
    settings = Settings.find_one()
    return render_template('facilities.html', settings=settings)

@user_bp.route('/gallery')
def gallery():
    """Gallery page"""
    try:
        images = list(mongo.db.gallery.find({'type': 'image'}))
        videos = list(mongo.db.gallery.find({'type': 'video'}))
    except Exception:
        images = []
        videos = []
    return render_template('gallery.html', images=images, videos=videos)

@user_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        mongo.db.contact_messages.insert_one({
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'message': request.form.get('message'),
            'created_at': get_bangladesh_now()
        })
        flash('Message sent successfully!', 'success')
        return redirect(url_for('user.contact'))
    settings = Settings.find_one()
    return render_template('contact.html', settings=settings)

@user_bp.route('/booking-confirmation/<booking_id>')
def booking_confirmation(booking_id):
    """Booking confirmation page"""
    booking = Booking.find_by_id(booking_id)
    if not booking:
        flash('Booking not found', 'error')
        return redirect(url_for('user.index'))
    
    slot = Slot.find_by_id(booking['time_slot'])
    from models.location import Location
    loc_id = booking.get('location_id') or (slot.get('location_id') if slot else None)
    location = Location.find_by_id(str(loc_id)) if loc_id else None
    settings = Settings.find_one()
    return render_template('booking_confirmation.html', booking=booking, slot=slot, location=location, settings=settings)


@user_bp.route('/booking/<booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    """Allow a user to cancel their own booking if it's at least 2 days away"""
    if not session.get('user_logged_in'):
        flash('Please log in to manage your bookings.', 'error')
        return redirect(url_for('auth.login', next=url_for('user.profile')))

    booking = Booking.find_by_id(booking_id)
    current_user = get_current_user()
    authorized = False
    if booking:
        # Authorized if user_id matches or phone matches current user's phone
        if str(booking.get('user_id')) == session.get('user_id'):
            authorized = True
        elif current_user and booking.get('phone') and booking.get('phone') == current_user.get('phone'):
            authorized = True
    if not booking or not authorized:
        flash('Booking not found or unauthorized.', 'error')
        return redirect(url_for('user.profile'))

    # Enforce 48-hour rule based on slot start time
    date_str = booking.get('date')
    slot = None
    try:
        slot = Slot.find_by_id(booking.get('time_slot')) if booking.get('time_slot') else None
    except Exception:
        slot = None
    if not date_str or not slot or not slot.get('time'):
        flash('Unable to cancel this booking.', 'error')
        return redirect(url_for('user.profile'))

    try:
        start_time_part = slot['time'].split('-')[0]
        start_hour, start_minute = [int(x) for x in start_time_part.split(':')]
        slot_start_dt = datetime.strptime(date_str, '%Y-%m-%d')
        slot_start_dt = slot_start_dt.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0, tzinfo=get_bangladesh_tz())
    except Exception:
        flash('Unable to cancel this booking.', 'error')
        return redirect(url_for('user.profile'))

    now_bangladesh = get_bangladesh_now()
    if now_bangladesh >= slot_start_dt:
        flash('Slot time has passed. Cannot cancel.', 'error')
        return redirect(url_for('user.profile'))

    if (slot_start_dt - now_bangladesh) < timedelta(hours=48):
        flash('Please call to cancel the booking', 'error')
        return redirect(url_for('user.profile'))

    if booking.get('status') == 'cancelled':
        flash('This booking is already cancelled.', 'info')
        return redirect(url_for('user.profile'))

    Booking.update(booking_id, {'status': 'cancelled'})
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('user.profile'))

