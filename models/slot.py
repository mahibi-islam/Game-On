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
            'enabled': data.get('enabled', True)
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
        return Slot.get_collection().update_one(
            {'_id': ObjectId(slot_id)},
            {'$set': data}
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
                {'time': '06:00-07:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '07:00-08:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '08:00-09:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '09:00-10:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '10:00-11:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '11:00-12:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '12:00-13:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '13:00-14:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '14:00-15:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '15:00-16:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '16:00-17:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '17:00-18:00', 'price': 500, 'sport': 'badminton', 'enabled': True},
                {'time': '18:00-19:00', 'price': 800, 'sport': 'badminton', 'enabled': True},
                {'time': '19:00-20:00', 'price': 800, 'sport': 'badminton', 'enabled': True},
                {'time': '20:00-21:00', 'price': 800, 'sport': 'badminton', 'enabled': True},
                {'time': '21:00-22:00', 'price': 800, 'sport': 'badminton', 'enabled': True},
                {'time': '22:00-23:00', 'price': 800, 'sport': 'badminton', 'enabled': True},
            ]
            Slot.get_collection().insert_many(badminton_slots)
            print("Initialized default Badminton slots")

