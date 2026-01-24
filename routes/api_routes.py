from flask import Blueprint, request, jsonify, session
from datetime import datetime
from models.slot import Slot
from models.booking import Booking

api_bp = Blueprint('api', __name__)

@api_bp.route('/slots')
def get_slots():
    """Get all enabled slots"""
    sport = request.args.get('sport', 'football')
    slots = Slot.find_all({'enabled': True, 'sport': sport}, sort=[('time', 1)])
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
    """Get availability for a specific date"""
    try:
        datetime.strptime(date, '%Y-%m-%d')  # Validate date format
        sport = request.args.get('sport', 'football')
        
        bookings = Booking.find_all({
            'date': date,
            'status': {'$in': ['pending', 'approved', 'paid']}
        })
        booked_slots = [b['time_slot'] for b in bookings]
        
        slots = Slot.find_all({'enabled': True, 'sport': sport}, sort=[('time', 1)])
        availability = []
        
        for slot in slots:
            slot_id = str(slot['_id'])
            is_booked = slot_id in booked_slots
            availability.append({
                '_id': slot_id,
                'time': slot['time'],
                'price': slot['price'],
                'sport': slot.get('sport', 'football'),
                'discount_active': slot.get('discount_active', False),
                'discount_percent': slot.get('discount_percent', 0),
                'available': not is_booked
            })
        
        return jsonify(availability)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/book', methods=['POST'])
def create_booking():
    """Create a new booking"""
    try:
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
            'user_id': str(session.get('user_id')) if session.get('user_id') else None
        }
        
        booking = Booking.create(booking_data)
        
        return jsonify({
            'success': True,
            'booking_id': booking['_id'],
            'booking': booking
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

