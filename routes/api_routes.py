from flask import Blueprint, request, jsonify, session
from datetime import datetime
from models.slot import Slot
from models.booking import Booking
from db import limiter
from utils.slot_utils import sort_slots, rate_type_for_date, is_past_slot

api_bp = Blueprint('api', __name__)

@api_bp.route('/slots')
def get_slots():
    """Get all enabled slots"""
    sport = request.args.get('sport', 'football')
    slots = Slot.find_all({'enabled': True, 'sport': sport})
    slots = sort_slots(slots)
    return jsonify([{
        '_id': str(slot['_id']),
        'time': slot['time'],
        'venue': slot.get('venue'),
        'price': slot['price'],
        'sport': slot.get('sport', 'football'),
        'discount_active': slot.get('discount_active', False),
        'discount_percent': slot.get('discount_percent', 0)
    } for slot in slots])

@api_bp.route('/availability/<date>')
def get_availability(date):
    """Get availability for a specific date and location"""
    try:
        from utils.slot_utils import get_bangladesh_now, is_past_slot
        from models.location import Location
        from bson import ObjectId
        
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        sport = request.args.get('sport', 'football')
        location_id = request.args.get('location_id')
        
        # Default to first active location if not provided
        if not location_id or location_id == 'undefined' or location_id == 'null':
            locs = Location.find_all({'enabled': True})
            if locs:
                location_id = str(locs[0]['_id'])
            else:
                return jsonify({'error': 'No active locations found'}), 400
        
        rate_type = rate_type_for_date(date_obj)
        
        # Check if the requested location is the default (first active) location
        locs = Location.find_all({'enabled': True})
        is_default_location = False
        if locs and str(locs[0]['_id']) == location_id:
            is_default_location = True

        location = Location.find_by_id(location_id)
        online_booking_enabled = location.get('online_booking_enabled', True) if location else True
        phone = location.get('phone', '') if location else ''

        bookings_query = {'date': date}
        loc_obj_id = ObjectId(location_id) if len(location_id) == 24 else location_id
        if is_default_location:
            # Legacy bookings do not have a location_id and are implicitly for Bogura (default location)
            bookings_query['$or'] = [
                {'location_id': loc_obj_id},
                {'location_id': {'$exists': False}},
                {'location_id': None}
            ]
        else:
            bookings_query['location_id'] = loc_obj_id

        bookings = Booking.find_all(bookings_query)
        
        booked_slot_ids = {str(b['time_slot']) for b in bookings if b.get('status') in ['approved', 'paid']}
        pending_slot_ids = {str(b['time_slot']) for b in bookings if b.get('status') == 'pending'}
        
        slots = Slot.find_all({
            'enabled': True, 
            'sport': sport,
            'rate_type': rate_type,
            'location_id': ObjectId(location_id) if len(location_id) == 24 else location_id
        })
        slots = sort_slots(slots)
        
        availability = []
        for slot in slots:
            slot_id = str(slot['_id'])
            is_booked = slot_id in booked_slot_ids
            is_pending = slot_id in pending_slot_ids
            is_past = is_past_slot(slot['time'], date)
            
            # available is ONLY True if it's not booked, not pending AND not in the past
            is_available = not is_booked and not is_pending and not is_past
            
            availability.append({
                '_id': slot_id,
                'time': slot['time'],
                'venue': slot.get('venue'),
                'price': slot['price'],
                'sport': slot.get('sport', 'football'),
                'discount_active': slot.get('discount_active', False),
                'discount_percent': slot.get('discount_percent', 0),
                'available': is_available,
                'is_booked': is_booked,
                'is_pending': is_pending,
                'is_past': is_past,
                'location_id': str(slot.get('location_id')) if slot.get('location_id') else None,
                'online_booking_enabled': online_booking_enabled,
                'phone': phone
            })
        
        return jsonify(availability)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/book', methods=['POST'])
@limiter.limit('10 per hour')
def create_booking():
    """Create a new booking"""
    try:
        from bson import ObjectId
        # Require user authentication
        if not session.get('user_logged_in'):
            return jsonify({'error': 'Authentication required. Please log in to book.'}), 401

        data = request.get_json(silent=True) or {}
        date = data.get('date')
        time_slot = data.get('time_slot')

        # Validate the date
        try:
            date_obj = datetime.strptime(date or '', '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid booking date'}), 400

        # Get slot (price is always taken from the slot, never from the request)
        try:
            slot = Slot.find_by_id(time_slot)
        except Exception:
            slot = None
        if not slot or not slot.get('enabled', True):
            return jsonify({'error': 'Invalid time slot'}), 400

        # The slot's rate must match the date (weekday vs. Friday/Saturday weekend pricing)
        if slot.get('rate_type', 'weekday') != rate_type_for_date(date_obj):
            return jsonify({'error': 'This time slot is not available on the selected date. Please pick the slot again.'}), 400

        if is_past_slot(slot['time'], date):
            return jsonify({'error': 'This time slot has already started or passed.'}), 400

        # Check if slot is already booked
        existing = Booking.find_by_date_and_slot(date, time_slot)
        if existing:
            return jsonify({'error': 'This slot is already booked'}), 400

        # Verify online booking is enabled for the location
        from models.location import Location
        loc_id = slot.get('location_id')
        if loc_id:
            location = Location.find_by_id(str(loc_id))
            if not location or not location.get('enabled', True):
                return jsonify({'error': 'This location is not accepting bookings.'}), 400
            if not location.get('online_booking_enabled', True):
                return jsonify({'error': 'Online bookings are currently disabled for this location. Please contact admin to book.'}), 400
        
        booking_data = {
            'date': date,
            'time_slot': time_slot,
            'name': data.get('name'),
            'phone': data.get('phone'),
            'team_name': data.get('team_name', ''),
            'payment_method': data.get('payment_method'),
            'transaction_id': data.get('transaction_id', ''),
            'amount': slot['price'] * (1 - float(slot.get('discount_percent', 0)) / 100) if slot.get('discount_active') else slot['price'],
            'status': 'pending',
            'notes': data.get('notes', ''),
            'user_id': str(session.get('user_id')) if session.get('user_id') else None,
            'location_id': str(slot['location_id']) if slot.get('location_id') else None
        }
        
        booking = Booking.create(booking_data)
        
        from flask import flash
        flash('Booking confirmed! Thank you for choosing us.', 'success')
        
        return jsonify({
            'success': True,
            'booking_id': booking.get('booking_id') or str(booking['_id']),
            'booking': booking
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

