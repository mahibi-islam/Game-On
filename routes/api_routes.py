from flask import Blueprint, request, jsonify, session
from datetime import datetime
from models.slot import Slot
from models.booking import Booking
from utils.slot_utils import sort_slots

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
        
        # Friday is 4, Saturday is 5 in weekday() (Monday=0, Sunday=6)
        is_weekend = date_obj.weekday() in [4, 5]
        rate_type = 'weekend' if is_weekend else 'weekday'
        
        # Check if the requested location is the default (first active) location
        locs = Location.find_all({'enabled': True})
        is_default_location = False
        if locs and str(locs[0]['_id']) == location_id:
            is_default_location = True

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
                'price': slot['price'],
                'sport': slot.get('sport', 'football'),
                'discount_active': slot.get('discount_active', False),
                'discount_percent': slot.get('discount_percent', 0),
                'available': is_available,
                'is_booked': is_booked,
                'is_pending': is_pending,
                'is_past': is_past,
                'location_id': str(slot.get('location_id')) if slot.get('location_id') else None
            })
        
        return jsonify(availability)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/book', methods=['POST'])
def create_booking():
    """Create a new booking"""
    try:
        from bson import ObjectId
        # Require user authentication
        if not session.get('user_logged_in'):
            return jsonify({'error': 'Authentication required. Please log in to book.'}), 401

        data = request.json
        date = data.get('date')
        time_slot = data.get('time_slot')
        
        # Check if slot is already booked
        existing = Booking.find_by_date_and_slot(date, time_slot)
        if existing:
            return jsonify({'error': 'This slot is already booked'}), 400
        
        # Get slot price
        slot = Slot.find_by_id(time_slot)
        if not slot:
            return jsonify({'error': 'Invalid time slot'}), 400
        
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

