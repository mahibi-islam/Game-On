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
            'discount_percent': float(data.get('discount_percent', 0.0)),
            'location_id': ObjectId(data.get('location_id')) if data.get('location_id') else None
        }
        result = Slot.get_collection().insert_one(slot_data)
        slot_data['_id'] = str(result.inserted_id)
        if slot_data.get('location_id'):
            slot_data['location_id'] = str(slot_data['location_id'])
        return slot_data
    
    @staticmethod
    def find_by_id(slot_id):
        """Find slot by ID"""
        return Slot.get_collection().find_one({'_id': ObjectId(slot_id)})
    
    @staticmethod
    def find_all(query=None, sort=None):
        """Find all slots"""
        q = query or {}
        # Convert location_id from string to ObjectId in query if applicable
        if 'location_id' in q and isinstance(q['location_id'], str) and len(q['location_id']) == 24:
            q['location_id'] = ObjectId(q['location_id'])
        cursor = Slot.get_collection().find(q)
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
        if 'location_id' in data: 
            update_data['location_id'] = ObjectId(data['location_id']) if data['location_id'] else None
        
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
        """Initialize default slots for all locations"""
        from models.location import Location
        locs = Location.find_all()
        if not locs:
            Location.init_defaults()
            locs = Location.find_all()
        
        if not locs:
            return
            
        gohail_id = locs[0]['_id']
        
        # Retrofit existing slots without location_id to the first location
        Slot.get_collection().update_many(
            {'location_id': {'$exists': False}},
            {'$set': {'location_id': gohail_id}}
        )
        
        # Make sure rate_type exists on all slots
        Slot.get_collection().update_many(
            {'rate_type': {'$exists': False}},
            {'$set': {'rate_type': 'weekday'}}
        )
        
        # Initialize default slots for each location if it doesn't have any weekday/weekend slots
        for loc in locs:
            loc_id = loc['_id']
            
            # Check weekday slots
            if Slot.get_collection().count_documents({'location_id': loc_id, 'rate_type': 'weekday'}) == 0:
                football_slots = [
                    {'time': '06:00-07:30', 'price': 2500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '07:30-09:00', 'price': 2500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '09:00-10:30', 'price': 2500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '10:30-12:00', 'price': 2500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '12:00-13:30', 'price': 2500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '13:30-15:00', 'price': 2500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '15:00-16:30', 'price': 2500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '16:30-18:00', 'price': 2500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '18:00-19:30', 'price': 3500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '19:30-21:00', 'price': 3500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '21:00-22:30', 'price': 3500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '22:30-00:00', 'price': 3500, 'sport': 'football', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                ]
                Slot.get_collection().insert_many(football_slots)
                
                badminton_slots = [
                    {'time': '06:00-07:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '07:00-08:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '08:00-09:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '09:00-10:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '10:00-11:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '11:00-12:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '12:00-13:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '13:00-14:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '14:00-15:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '15:00-16:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '16:00-17:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '17:00-18:00', 'price': 500, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '18:00-19:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '19:00-20:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '20:00-21:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '21:00-22:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                    {'time': '22:00-23:00', 'price': 800, 'sport': 'badminton', 'rate_type': 'weekday', 'enabled': True, 'location_id': loc_id},
                ]
                Slot.get_collection().insert_many(badminton_slots)
                print(f"Initialized default weekday slots for location: {loc['name']}")
                
            # Check weekend slots
            if Slot.get_collection().count_documents({'location_id': loc_id, 'rate_type': 'weekend'}) == 0:
                weekday_slots = list(Slot.get_collection().find({'location_id': loc_id, 'rate_type': 'weekday'}))
                if weekday_slots:
                    weekend_slots = []
                    for ws in weekday_slots:
                        ws_copy = {
                            'time': ws['time'],
                            'price': ws['price'],
                            'sport': ws.get('sport', 'football'),
                            'rate_type': 'weekend',
                            'enabled': ws.get('enabled', True),
                            'location_id': loc_id,
                            'discount_active': ws.get('discount_active', False),
                            'discount_percent': ws.get('discount_percent', 0.0)
                        }
                        weekend_slots.append(ws_copy)
                    Slot.get_collection().insert_many(weekend_slots)
                    print(f"Migrated/Initialized weekend slots from weekday slots for location: {loc['name']}")
                else:
                    football_weekend = [
                        {'time': '06:00-07:30', 'price': 3000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '07:30-09:00', 'price': 3000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '09:00-10:30', 'price': 3000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '10:30-12:00', 'price': 3000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '12:00-13:30', 'price': 3000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '13:30-15:00', 'price': 3000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '15:00-16:30', 'price': 3000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '16:30-18:00', 'price': 3000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '18:00-19:30', 'price': 4000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '19:30-21:00', 'price': 4000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '21:00-22:30', 'price': 4000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '22:30-00:00', 'price': 4000, 'sport': 'football', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                    ]
                    Slot.get_collection().insert_many(football_weekend)
                    badminton_weekend = [
                        {'time': '06:00-07:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '07:00-08:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '08:00-09:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '09:00-10:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '10:00-11:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '11:00-12:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '12:00-13:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '13:00-14:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '14:00-15:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '15:00-16:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '16:00-17:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '17:00-18:00', 'price': 600, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '18:00-19:00', 'price': 1000, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '19:00-20:00', 'price': 1000, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '20:00-21:00', 'price': 1000, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '21:00-22:00', 'price': 1000, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                        {'time': '22:00-23:00', 'price': 1000, 'sport': 'badminton', 'rate_type': 'weekend', 'enabled': True, 'location_id': loc_id},
                    ]
                    Slot.get_collection().insert_many(badminton_weekend)
                    print(f"Initialized default weekend slots for location: {loc['name']}")


