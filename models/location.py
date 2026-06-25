import time
import json
from db import mongo
from bson import ObjectId

def serialize_query(query):
    if query is None:
        return ""
    def default(o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, dict):
            return {k: default(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [default(x) for x in o]
        raise TypeError
    try:
        normalized = default(query)
        return json.dumps(normalized, sort_keys=True)
    except Exception:
        return str(query)

class Location:
    COLLECTION = 'locations'
    
    _find_all_cache = {}
    _find_by_id_cache = {}
    CACHE_DURATION = 15  # seconds
    
    @staticmethod
    def get_collection():
        return mongo.db.locations
        
    @staticmethod
    def clear_cache():
        Location._find_all_cache.clear()
        Location._find_by_id_cache.clear()
    
    @staticmethod
    def create(data):
        """Create a new location"""
        location_data = {
            'name': data.get('name'),
            'address': data.get('address'),
            'phone': data.get('phone'),
            'whatsapp': data.get('whatsapp'),
            'email': data.get('email', ''),
            'rules': data.get('rules', 'Please maintain cleanliness. No smoking allowed.'),
            'homepage_content': data.get('homepage_content', 'Welcome to GAME ON!'),
            'enabled': data.get('enabled', True),
            'image_url': data.get('image_url', '')
        }
        result = Location.get_collection().insert_one(location_data)
        location_data['_id'] = str(result.inserted_id)
        Location.clear_cache()
        return location_data
    
    @staticmethod
    def find_by_id(location_id):
        """Find location by ID"""
        if not location_id:
            return None
        loc_id_str = str(location_id)
        now = time.time()
        
        cached = Location._find_by_id_cache.get(loc_id_str)
        if cached is not None and (now - cached['time']) < Location.CACHE_DURATION:
            return dict(cached['data']) if cached['data'] else None
            
        try:
            data = Location.get_collection().find_one({'_id': ObjectId(loc_id_str)})
            Location._find_by_id_cache[loc_id_str] = {
                'data': dict(data) if data else None,
                'time': now
            }
            return data
        except Exception:
            return None
    
    @staticmethod
    def find_all(query=None):
        """Find all locations"""
        now = time.time()
        key = serialize_query(query)
        
        cached = Location._find_all_cache.get(key)
        if cached is not None and (now - cached['time']) < Location.CACHE_DURATION:
            return [dict(item) for item in cached['data']]
            
        data = list(Location.get_collection().find(query or {}))
        Location._find_all_cache[key] = {
            'data': [dict(item) for item in data],
            'time': now
        }
        return data
    
    @staticmethod
    def update(location_id, data):
        """Update location details"""
        update_data = {}
        for key in ['name', 'address', 'phone', 'whatsapp', 'email', 'rules', 'homepage_content', 'enabled', 'image_url']:
            if key in data:
                if key == 'enabled':
                    update_data[key] = bool(data[key])
                else:
                    update_data[key] = data[key]
        
        result = Location.get_collection().update_one(
            {'_id': ObjectId(location_id)},
            {'$set': update_data}
        )
        Location.clear_cache()
        return result
        
    @staticmethod
    def delete(location_id):
        """Delete location"""
        result = Location.get_collection().delete_one({'_id': ObjectId(location_id)})
        Location.clear_cache()
        return result

    @staticmethod
    def init_defaults():
        """Initialize default locations and return their IDs"""
        Location.clear_cache()
        # Auto-migrate/rename existing 'GAME ON BOGURA - Cantonment' in the DB to 'GAME ON KHULNA'
        Location.get_collection().update_one(
            {'name': 'GAME ON BOGURA - Cantonment'},
            {'$set': {
                'name': 'GAME ON KHULNA',
                'address': 'Khulna Sadar, Khulna',
                'email': 'khulna.gameon@gmail.com',
                'homepage_content': 'Welcome to GAME ON KHULNA!'
            }}
        )

        if Location.get_collection().count_documents({}) == 0:
            # Try to populate based on settings if available
            from models.settings import Settings
            settings = Settings.find_one()
            if settings:
                gohail_road = {
                    'name': settings.get('turf_name', 'GAME ON') + ' - Gohail Road',
                    'address': settings.get('address', 'Gohail Road, Bogura'),
                    'phone': settings.get('phone', '+8801780037275'),
                    'whatsapp': settings.get('whatsapp', '+8801780037275'),
                    'email': settings.get('email', 'bogura.gameon@gmail.com'),
                    'rules': settings.get('rules', 'Please maintain cleanliness. No smoking allowed.'),
                    'homepage_content': settings.get('homepage_content', 'Welcome to GAME ON!'),
                    'enabled': True
                }
            else:
                gohail_road = {
                    'name': 'GAME ON - Gohail Road',
                    'address': 'Gohail Road, Bogura',
                    'phone': '+8801780037275',
                    'whatsapp': '+8801780037275',
                    'email': 'bogura.gameon@gmail.com',
                    'rules': 'Please maintain cleanliness. No smoking allowed.',
                    'homepage_content': 'Welcome to GAME ON!',
                    'enabled': True
                }
            
            khulna = {
                'name': 'GAME ON KHULNA',
                'address': 'Khulna Sadar, Khulna',
                'phone': '+8801333770044',
                'whatsapp': '+8801333770044',
                'email': 'khulna.gameon@gmail.com',
                'rules': 'Please maintain cleanliness. Wear proper shoes.',
                'homepage_content': 'Welcome to GAME ON KHULNA!',
                'enabled': True
            }
            
            gohail_ref = Location.get_collection().insert_one(gohail_road)
            khulna_ref = Location.get_collection().insert_one(khulna)
            print("Initialized default locations")
            return [str(gohail_ref.inserted_id), str(khulna_ref.inserted_id)]
        else:
            locs = list(Location.get_collection().find())
            return [str(l['_id']) for l in locs]
