from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId, InvalidId
from datetime import datetime
from flask import session
from pymongo import ReturnDocument
from db import mongo
import os


# Collection references via Flask-PyMongo
users_collection = mongo.db.users
counters_collection = mongo.db.counters


def calculate_age(dob_string):
    """Jonmo tarikh (string) theke boyosh hishab kore."""
    if not dob_string:
        return None
    # Jonmo tarikh string theke date object e convert kora hocche.
    birth_date = datetime.strptime(dob_string, '%Y-%m-%d').date()
    today = datetime.today().date()
    # Boyosh hishab korar formula.
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


def get_next_nomad_id():

    # 'counters' collection theke 'user_id_counter' er value 1 kore barano hocche.
    # Eita prottek notun user er jonno ekta unique number ensure kore.
    counter = counters_collection.find_one_and_update(
        {'_id': 'user_id_counter'},
        {'$inc': {'sequence_value': 1}},
        upsert=True, # Jodi counter na thake, tobe notun toiri korbe.
        return_document=ReturnDocument.AFTER # Update howar porer document ta return korbe.
    )
    # Notun ID ta "nomad#" prefix er shathe return kora hocche.
    return f"User#{counter['sequence_value']}"


def create_user(data):
    """Ekjon notun user (Traveler or Host) toiri kore ebong database e save kore."""
    # Password ke direct save na kore, hash kore save kora hocche securityr jonno.
    hashed_password = generate_password_hash(data['password'])
    # Notun user er jonno unique ID toiri kora hocche.
    nomad_id = get_next_nomad_id()
    # Jonmo tarikh theke boyosh hishab kora hocche.
    age = calculate_age(data['dob'])
    role = data.get('role', 'user')
    
    # User er shob information diye ekta document (dictionary) toiri kora hocche.
    user_document = {
        "user_id": nomad_id,
        "first_name": data['first_name'],
        "last_name": data['last_name'],
        "dob": data['dob'],
        "age": age,
        "nid": data['nid'],
        "email": data['email'],
        "phone": data['phone'],
        "password": hashed_password,
        "role": role,
        "created_at": datetime.utcnow(),  # User toirir shomoy
        "last_login": None, # Prothome last_login null thakbe
        "verification": {
            "status": "not_submitted",
            "nid_photo": "",
            "own_photo": ""
        }
    }
    # Notun user document ta 'users' collection e insert kora hocche.
    users_collection.insert_one(user_document)
    return nomad_id


def find_user_by_login(login_identifier):
    """Database theke user ke tader email ba user_id diye khuje ber kore."""
    # Prothome email diye user khujar cheshta kora hocche.
    user = users_collection.find_one({"email": login_identifier})
    # Jodi email diye na paowa jay, tobe user_id diye khujar cheshta kora hocche.
    if not user:
        user = users_collection.find_one({"user_id": login_identifier})
    return user

def update_last_login(user_id):
    """User er last_login timestamp update kore."""
    # nirdishto user_id er document e 'last_login' field ta current time diye update kora hocche.
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_login": datetime.utcnow()}}
    )

def update_details(user_id, data):
    """Update user profile details"""
    update_data = {
        "first_name": data.get('first_name'),
        "last_name": data.get('last_name'),
        "phone": data.get('phone')
    }
    
    # Filter out None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    if is_valid_objectid(user_id):
        query = {"_id": ObjectId(user_id)}
    else:
        query = {"user_id": user_id}
        
    result = users_collection.update_one(query, {"$set": update_data})
    return result.modified_count > 0


def submit_verification_photos(user_id, nid_photo, own_photo):
    
    upload_folder = "static/uploads"
    os.makedirs(upload_folder, exist_ok=True)
    nid_filename = f"nid_{user_id}.jpg"
    own_filename = f"own_{user_id}.jpg"
    nid_path = f"{upload_folder}/{nid_filename}"
    own_path = f"{upload_folder}/{own_filename}"
    nid_photo.save(nid_path)
    own_photo.save(own_path)
    
    if is_valid_objectid(user_id):
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "verification": {
                    "nid_photo": nid_path,
                    "own_photo": own_path,
                    "status": "pending"
                }
            }}
        )
    else:
        users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "verification": {
                    "nid_photo": nid_path,
                    "own_photo": own_path,
                    "status": "pending"
                }
            }}
        )


def is_valid_objectid(oid):
    try:
        ObjectId(oid)
        return True
    except (InvalidId, TypeError):
        return False


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    if is_valid_objectid(user_id):
        return users_collection.find_one({"_id": ObjectId(user_id)})
    else:
        # Assuming user_id could be the custom 'nomad_id'
        return users_collection.find_one({"user_id": user_id})
