from db import mongo
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Admin:
    """Admin model"""
    COLLECTION = 'admins'
    
    @staticmethod
    def get_collection():
        return mongo.db.admins
    
    @staticmethod
    def create(username, password):
        """Create a new admin"""
        admin_data = {
            'username': username,
            'password': generate_password_hash(password),
            'created_at': datetime.now()
        }
        result = Admin.get_collection().insert_one(admin_data)
        admin_data['_id'] = str(result.inserted_id)
        return admin_data
    
    @staticmethod
    def find_by_username(username):
        """Find admin by username"""
        return Admin.get_collection().find_one({'username': username})
    
    @staticmethod
    def verify_password(admin, password):
        """Verify admin password"""
        return check_password_hash(admin['password'], password)
    
    @staticmethod
    def init_defaults():
        """Initialize default admin"""
        if not Admin.find_by_username('admin'):
            admin_password = os.environ.get('ADMIN_PASSWORD')
            if admin_password:
                Admin.create('admin', admin_password)
                print("Default admin user created.")
            else:
                logging.warning("ADMIN_PASSWORD not set. Default admin creation skipped.")

