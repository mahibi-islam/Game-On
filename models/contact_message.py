from db import mongo
from bson import ObjectId
from datetime import datetime

class ContactMessage:
    COLLECTION = 'contact_messages'
    
    @staticmethod
    def get_collection():
        return mongo.db.contact_messages
    
    @staticmethod
    def find_all(sort_by='created_at', direction=-1):
        """Get all contact messages sorted by date"""
        return list(ContactMessage.get_collection().find().sort(sort_by, direction))
    
    @staticmethod
    def delete(message_id):
        """Delete a contact message by ID"""
        return ContactMessage.get_collection().delete_one({'_id': ObjectId(message_id)})
