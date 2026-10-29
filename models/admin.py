from db import mongo
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson import ObjectId

class Admin:
    """Admin model"""
    COLLECTION = 'admins'
    
    @staticmethod
    def get_collection():
        return mongo.db.admins
    
    @staticmethod
    def create(username, password, location_id=None, role=None, full_name=None):
        """Create a new admin with optional role and branch assignment"""
        if not role:
            role = 'branch_admin' if location_id else 'superadmin'
            
        loc_id = None
        if location_id:
            loc_id = ObjectId(location_id) if isinstance(location_id, str) and len(location_id) == 24 else location_id

        admin_data = {
            'username': username.strip().lower(),
            'password': generate_password_hash(password),
            'role': role,
            'location_id': loc_id,
            'full_name': full_name or username,
            'created_at': datetime.now()
        }
        result = Admin.get_collection().insert_one(admin_data)
        admin_data['_id'] = str(result.inserted_id)
        return admin_data
    
    @staticmethod
    def find_by_username(username):
        """Find admin by username (case-insensitive)"""
        if not username:
            return None
        return Admin.get_collection().find_one({'username': username.strip().lower()})
    
    @staticmethod
    def find_by_id(admin_id):
        """Find admin by ID"""
        if not admin_id:
            return None
        try:
            return Admin.get_collection().find_one({'_id': ObjectId(admin_id)})
        except Exception:
            return None

    @staticmethod
    def find_all(query=None):
        """Find all admins"""
        return list(Admin.get_collection().find(query or {}))

    @staticmethod
    def update(admin_id, data):
        """Update admin data"""
        update_data = {}
        if 'username' in data:
            update_data['username'] = data['username'].strip().lower()
        if 'full_name' in data:
            update_data['full_name'] = data['full_name']
        if 'role' in data:
            update_data['role'] = data['role']
        if 'location_id' in data:
            lid = data['location_id']
            if lid:
                update_data['location_id'] = ObjectId(lid) if isinstance(lid, str) and len(lid) == 24 else lid
            else:
                update_data['location_id'] = None
        if 'password' in data and data['password']:
            update_data['password'] = generate_password_hash(data['password'])

        return Admin.get_collection().update_one(
            {'_id': ObjectId(admin_id)},
            {'$set': update_data}
        )

    @staticmethod
    def delete(admin_id):
        """Delete admin"""
        return Admin.get_collection().delete_one({'_id': ObjectId(admin_id)})

    @staticmethod
    def verify_password(admin, password):
        """Verify admin password"""
        return check_password_hash(admin['password'], password)
    
    @staticmethod
    def init_defaults():
        """Initialize default admins: Super Admin, Bogura Admin, and Khulna Admin"""
        from models.location import Location
        locs = Location.find_all()
        if not locs:
            Location.init_defaults()
            locs = Location.find_all()

        # Find Bogura & Khulna locations
        bogura_loc = None
        khulna_loc = None
        for loc in locs:
            name_lower = loc.get('name', '').lower()
            if 'bogura' in name_lower or 'gohail' in name_lower:
                bogura_loc = loc
            elif 'khulna' in name_lower:
                khulna_loc = loc
                
        if not bogura_loc and locs:
            bogura_loc = locs[0]
        if not khulna_loc and len(locs) > 1:
            khulna_loc = locs[1]

        # Never fall back to a hardcoded password: missing default admins are only
        # created when ADMIN_PASSWORD is set.
        admin_password = os.environ.get('ADMIN_PASSWORD')
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        legacy_weak_password = os.environ.get('LEGACY_WEAK_ADMIN_PASSWORD', 'admin123')
        for existing in Admin.find_all():
            if Admin.verify_password(existing, legacy_weak_password):
                print(f"SECURITY WARNING: admin '{existing.get('username')}' still uses an insecure "
                      f"default password. Change it immediately in Admin > Users.")

        # 1. Super Admin
        superadmin = Admin.find_by_username(admin_username)
        if not superadmin:
            if admin_password:
                Admin.create(admin_username, admin_password, role='superadmin', full_name='Super Administrator')
                print(f"Default superadmin user '{admin_username}' created.")
            else:
                print(f"WARNING: no superadmin '{admin_username}' exists and ADMIN_PASSWORD is not set; skipping creation.")
        else:
            # Ensure superadmin role is explicitly set
            if superadmin.get('role') != 'superadmin' or superadmin.get('location_id') is not None:
                Admin.get_collection().update_one(
                    {'_id': superadmin['_id']},
                    {'$set': {'role': 'superadmin', 'location_id': None, 'full_name': superadmin.get('full_name', 'Super Administrator')}}
                )

        # 2. Bogura Branch Admin
        if bogura_loc:
            bogura_admin = Admin.find_by_username('admin_bogura')
            bogura_password = os.environ.get('ADMIN_BOGURA_PASSWORD') or admin_password
            if not bogura_admin and bogura_password:
                Admin.create(
                    'admin_bogura',
                    bogura_password,
                    location_id=bogura_loc['_id'],
                    role='branch_admin',
                    full_name='Bogura Admin'
                )
                print(f"Default Bogura branch admin 'admin_bogura' created for location: {bogura_loc.get('name')}")
            elif bogura_admin:
                Admin.get_collection().update_one(
                    {'_id': bogura_admin['_id']},
                    {'$set': {
                        'role': 'branch_admin',
                        'location_id': ObjectId(bogura_loc['_id']) if isinstance(bogura_loc['_id'], str) else bogura_loc['_id'],
                        'full_name': bogura_admin.get('full_name', 'Bogura Admin')
                    }}
                )

        # 3. Khulna Branch Admin
        if khulna_loc:
            khulna_admin = Admin.find_by_username('admin_khulna')
            khulna_password = os.environ.get('ADMIN_KHULNA_PASSWORD') or admin_password
            if not khulna_admin and khulna_password:
                Admin.create(
                    'admin_khulna',
                    khulna_password,
                    location_id=khulna_loc['_id'],
                    role='branch_admin',
                    full_name='Khulna Admin'
                )
                print(f"Default Khulna branch admin 'admin_khulna' created for location: {khulna_loc.get('name')}")
            elif khulna_admin:
                Admin.get_collection().update_one(
                    {'_id': khulna_admin['_id']},
                    {'$set': {
                        'role': 'branch_admin',
                        'location_id': ObjectId(khulna_loc['_id']) if isinstance(khulna_loc['_id'], str) else khulna_loc['_id'],
                        'full_name': khulna_admin.get('full_name', 'Khulna Admin')
                    }}
                )

