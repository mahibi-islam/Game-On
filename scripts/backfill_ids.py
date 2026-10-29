from app import create_app
from db import mongo
from models.booking import Booking

app = create_app()

def backfill_ids():
    with app.app_context():
        # Check current count
        counter = mongo.db.counters.find_one({'_id': 'booking_id'})
        if not counter:
            mongo.db.counters.insert_one({'_id': 'booking_id', 'sequence_value': 0})
            current_val = 0
        else:
            current_val = counter['sequence_value']
            
        # Get all bookings without a sequential ID, sorted by created_at or _id
        bookings = list(mongo.db.bookings.find({'booking_id': {'$exists': False}}).sort('_id', 1))
        
        print(f"Found {len(bookings)} bookings to backfill.")
        
        for booking in bookings:
            current_val += 1
            booking_id_str = f"GAMEON{current_val}"
            mongo.db.bookings.update_one(
                {'_id': booking['_id']},
                {'$set': {'booking_id': booking_id_str}}
            )
            print(f"Assigned {booking_id_str} to booking {booking['_id']}")
            
        # Update counter
        mongo.db.counters.update_one(
            {'_id': 'booking_id'},
            {'$set': {'sequence_value': current_val}}
        )
        print(f"Updated booking_id counter to {current_val}")

if __name__ == "__main__":
    backfill_ids()
