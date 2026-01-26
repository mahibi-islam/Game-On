from db import mongo
from bson import ObjectId

class Slot:
    """Time slot model"""
    COLLECTION = 'slots'
    
    @staticmethod
    def get_collection():
        return mongo.db.slots
    
    @staticmethod
    def create(data):
        """Create a new slot"""
        slot_data = {
            'time': data.get('time'),
            'price': float(data.get('price')),
            'sport': data.get('sport', 'football'),
            'rate_type': data.get('rate_type', 'weekday'),
            'enabled': data.get('enabled', True),
            'discount_active': data.get('discount_active', False),
            'discount_percent': float(data.get('discount_percent', 0.0))
        }
        result = Slot.get_collection().insert_one(slot_data)
        slot_data['_id'] = str(result.inserted_id)
        return slot_data
    
    @staticmethod
    def find_by_id(slot_id):
        """Find slot by ID"""
        return Slot.get_collection().find_one({'_id': ObjectId(slot_id)})
    
    @staticmethod
    def find_all(query=None, sort=None):
        """Find all slots"""
        cursor = Slot.get_collection().find(query or {})
        if sort:
            cursor = cursor.sort(sort)
        return list(cursor)
    
    @staticmethod
    def update(slot_id, data):
        """Update slot"""
        update_data = {}
        if 'time' in data: update_data['time'] = data['time']
        if 'price' in data: update_data['price'] = float(data['price'])
        if 'sport' in data: update_data['sport'] = data['sport']
        if 'rate_type' in data: update_data['rate_type'] = data['rate_type']
        if 'enabled' in data: update_data['enabled'] = data['enabled']
        if 'discount_active' in data: update_data['discount_active'] = data['discount_active']
        if 'discount_percent' in data: update_data['discount_percent'] = float(data['discount_percent'])
        
        return Slot.get_collection().update_one(
            {'_id': ObjectId(slot_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def count(query=None):
        """Count slots"""
        return Slot.get_collection().count_documents(query or {})
    
    @staticmethod
    def init_defaults():
        """Initialize default slots"""
        # Default slots for Football
        if Slot.get_collection().count_documents({'sport': 'football'}) == 0:
            football_slots = [
                {'time': '06:00-07:30', 'price': 2500, 'sport': 'football', 'enabled': True},
                {'time': '07:30-09:00', 'price': 2500, 'sport': 'football', 'enabled': True},
                {'time': '09:00-10:30', 'price': 2500, 'sport': 'football', 'enabled': True},
                {'time': '10:30-12:00', 'price': 2500, 'sport': 'football', 'enabled': True},
                {'time': '12:00-13:30', 'price': 2500, 'sport': 'football', 'enabled': True},
                {'time': '13:30-15:00', 'price': 2500, 'sport': 'football', 'enabled': True},
                {'time': '15:00-16:30', 'price': 2500, 'sport': 'football', 'enabled': True},
                {'time': '16:30-18:00', 'price': 2500, 'sport': 'football', 'enabled': True},
                {'time': '18:00-19:30', 'price': 3500, 'sport': 'football', 'enabled': True},
                {'time': '19:30-21:00', 'price': 3500, 'sport': 'football', 'enabled': True},
                {'time': '21:00-22:30', 'price': 3500, 'sport': 'football', 'enabled': True},
                {'time': '22:30-00:00', 'price': 3500, 'sport': 'football', 'enabled': True},
            ]
            Slot.get_collection().insert_many(football_slots)
            print("Initialized default Football slots")

        # Default slots for Badminton
        if Slot.get_collection().count_documents({'sport': 'badminton'}) == 0:
            badminton_slots = [
                {'time': '06:00-07:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '07:00-08:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '08:00-09:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '09:00-10:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '10:00-11:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '11:00-12:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '12:00-13:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '13:00-14:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '14:00-15:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '15:00-16:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '16:00-17:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '17:00-18:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '18:00-19:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '19:00-20:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '20:00-21:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '21:00-22:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
                {'time': '22:00-23:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True},
            ]
            Slot.get_collection().insert_many(badminton_slots)
            print("Initialized default Badminton slots")

        # Update existing slots without rate_type
        Slot.get_collection().update_many(
            {'rate_type': {'$exists': False}},
            {'$set': {'rate_type': 'weekday'}}
        )

