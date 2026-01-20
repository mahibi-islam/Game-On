from db import mongo

class Settings:
    """Settings model"""
    COLLECTION = 'settings'
    
    @staticmethod
    def get_collection():
        return mongo.db.settings
    
    @staticmethod
    def find_one():
        """Get settings"""
        return Settings.get_collection().find_one()
    
    @staticmethod
    def update(data):
        """Update settings"""
        return Settings.get_collection().update_one(
            {},
            {'$set': data},
            upsert=True
        )
    
    @staticmethod
    def init_defaults():
        """Initialize default settings"""
        if not Settings.find_one():
            Settings.get_collection().insert_one({
                'turf_name': 'GAME ON BOGURA',
                'address': 'Gohail Road,Bogura',
                'phone': '+8801780-037275',
                'whatsapp': '+8801780-037275',
                'email': 'info@turf.com',
                'facebook': 'https://www.facebook.com/share/1ADMmWtRMw/',
                'rules': 'Please maintain cleanliness. No smoking allowed.',
                'homepage_content': 'Welcome to GAME ON BOGURA!'
            })

