import time
from db import mongo

class Settings:
    """Settings model"""
    COLLECTION = 'settings'
    
    _cache = None
    _cache_time = 0
    CACHE_DURATION = 15  # seconds
    
    @staticmethod
    def get_collection():
        return mongo.db.settings
    
    @staticmethod
    def find_one():
        """Get settings"""
        now = time.time()
        if Settings._cache is None or (now - Settings._cache_time) > Settings.CACHE_DURATION:
            data = Settings.get_collection().find_one()
            Settings._cache = dict(data) if data else None
            Settings._cache_time = now
        return dict(Settings._cache) if Settings._cache else None
    
    @staticmethod
    def update(data):
        """Update settings"""
        result = Settings.get_collection().update_one(
            {},
            {'$set': data},
            upsert=True
        )
        Settings.clear_cache()
        return result
        
    @staticmethod
    def clear_cache():
        Settings._cache = None
        Settings._cache_time = 0
    
    @staticmethod
    def init_defaults():
        """Initialize default settings"""
        if not Settings.find_one():
            Settings.get_collection().insert_one({
                'turf_name': 'GAME ON',
                'address': 'Gohail Road,Bogura',
                'phone': '+8801780037275',
                'whatsapp': '+8801780037275',
                'email': 'bogura.gameon@gmail.com',
                'facebook': 'https://www.facebook.com/share/1ADMmWtRMw/',
                'rules': 'Please maintain cleanliness. No smoking allowed.',
                'homepage_content': 'Welcome to GAME ON'
            })
            Settings.clear_cache()


