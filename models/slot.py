from db import mongo
from bson import ObjectId
from utils.slot_utils import get_bangladesh_now

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
        venue = (data.get('venue') or '').strip()
        if venue:
            slot_data['venue'] = venue
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

        update_ops = {'$set': update_data}
        if 'venue' in data:
            venue = (data['venue'] or '').strip()
            if venue:
                update_data['venue'] = venue
            else:
                update_ops['$unset'] = {'venue': ''}
        
        return Slot.get_collection().update_one(
            {'_id': ObjectId(slot_id)},
            update_ops
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

        Slot.init_khulna_schedule(locs)
        Slot.raise_khulna_venue2_prices(locs)

    # GAME ON KHULNA football schedule (both venues share it): time -> (weekday, weekend) price.
    # Weekday = Sunday-Thursday, weekend = Friday-Saturday.
    # Venue 2 is then raised by KHULNA_VENUE2_PRICE_INCREASE (see raise_khulna_venue2_prices).
    KHULNA_VENUES = ['Venue 1', 'Venue 2']
    KHULNA_FOOTBALL_PRICES = [
        ('06:00-07:30', 2200, 2400),
        ('07:30-09:00', 2200, 2400),
        ('09:00-10:30', 2200, 2400),
        ('10:30-12:00', 2200, 2400),
        ('12:00-13:30', 2000, 2200),
        ('13:30-15:00', 2000, 2200),
        ('15:00-16:30', 2000, 2200),
        ('16:30-18:00', 2800, 3000),
        ('18:00-19:30', 2800, 3000),
        ('19:30-21:00', 2800, 3000),
        ('21:00-22:30', 2800, 3000),
        ('22:30-00:00', 2800, 3000),
        ('00:00-01:30', 2800, 3000),
        ('01:30-03:00', 2800, 3000),
        ('03:00-04:30', 2400, 2400),
        ('04:30-06:00', 2400, 2400),
    ]
    KHULNA_VENUE2_PRICE_INCREASE = 100

    @staticmethod
    def raise_khulna_venue2_prices(locs):
        """One-time migration: raise every GAME ON KHULNA Venue 2 football slot
        (weekday and weekend) by KHULNA_VENUE2_PRICE_INCREASE taka. Uses $inc so
        any per-slot price edits made in the admin panel are preserved."""
        from db import mongo
        from pymongo.errors import DuplicateKeyError

        khulna = next((l for l in locs if 'khulna' in l.get('name', '').lower()), None)
        if not khulna:
            return

        migration_id = 'khulna_venue2_price_increase_100'
        try:
            mongo.db.migrations.insert_one({'_id': migration_id})
        except DuplicateKeyError:
            return

        try:
            result = Slot.get_collection().update_many(
                {'location_id': khulna['_id'], 'sport': 'football', 'venue': 'Venue 2'},
                {'$inc': {'price': Slot.KHULNA_VENUE2_PRICE_INCREASE}}
            )
        except Exception:
            mongo.db.migrations.delete_one({'_id': migration_id})  # retry on next start
            raise
        print(f"Raised {result.modified_count} Khulna Venue 2 football slot price(s) "
              f"by {Slot.KHULNA_VENUE2_PRICE_INCREASE}")

    @staticmethod
    def init_khulna_schedule(locs):
        """One-time migration: GAME ON KHULNA runs two football venues with the
        same 90-minute slots and pricing (KHULNA_FOOTBALL_PRICES).

        Existing slots are matched by start/end time (so '6:00 - 7:30' matches
        '06:00-07:30') and updated in place, keeping their IDs so bookings still
        resolve. Duplicate slots have their bookings moved onto the kept slot.
        Missing slots are created; leftover football slots are disabled, not deleted."""
        from db import mongo
        from pymongo.errors import DuplicateKeyError
        from utils.slot_utils import parse_time_to_minutes

        khulna = next((l for l in locs if 'khulna' in l.get('name', '').lower()), None)
        if not khulna:
            return

        # Claim the migration atomically so concurrent gunicorn workers don't both run it
        migration_id = 'khulna_two_venue_schedule'
        try:
            mongo.db.migrations.insert_one({'_id': migration_id})
        except DuplicateKeyError:
            return

        try:
            Slot._apply_khulna_schedule(mongo, khulna, parse_time_to_minutes)
        except Exception:
            mongo.db.migrations.delete_one({'_id': migration_id})  # retry on next start
            raise

    @staticmethod
    def _apply_khulna_schedule(mongo, khulna, parse_time_to_minutes):
        loc_id = khulna['_id']
        col = Slot.get_collection()
        football = {'location_id': loc_id, 'sport': 'football'}

        def span(time_str):
            start, _, end = (time_str or '').partition('-')
            return parse_time_to_minutes(start), parse_time_to_minutes(end)

        # Existing single-venue slots become Venue 1
        col.update_many({**football, 'venue': {'$exists': False}}, {'$set': {'venue': 'Venue 1'}})
        existing = list(col.find(football))

        def move_bookings(from_id, to_id):
            mongo.db.bookings.update_many(
                {'time_slot': {'$in': [from_id, str(from_id)]}},
                {'$set': {'time_slot': str(to_id)}}
            )

        scheduled_ids = set()
        created = 0
        for venue in Slot.KHULNA_VENUES:
            for time_str, weekday_price, weekend_price in Slot.KHULNA_FOOTBALL_PRICES:
                for rate_type, price in (('weekday', weekday_price), ('weekend', weekend_price)):
                    matches = [s for s in existing
                               if s.get('venue') == venue
                               and s.get('rate_type', 'weekday') == rate_type
                               and s['_id'] not in scheduled_ids
                               and span(s.get('time')) == span(time_str)]
                    fields = {'time': time_str, 'price': float(price), 'enabled': True}
                    if matches:
                        # Prefer an exact, enabled match as the slot to keep
                        matches.sort(key=lambda s: (s.get('time') != time_str, not s.get('enabled', True)))
                        keep = matches[0]
                        col.update_one({'_id': keep['_id']}, {'$set': fields})
                        for dup in matches[1:]:
                            move_bookings(dup['_id'], keep['_id'])
                        scheduled_ids.add(keep['_id'])
                    else:
                        result = col.insert_one({
                            **football, **fields, 'venue': venue, 'rate_type': rate_type,
                            'discount_active': False, 'discount_percent': 0.0
                        })
                        scheduled_ids.add(result.inserted_id)
                        created += 1

        off_schedule = [s['_id'] for s in existing if s['_id'] not in scheduled_ids]
        if off_schedule:
            col.update_many({'_id': {'$in': off_schedule}}, {'$set': {'enabled': False}})
            orphaned = mongo.db.bookings.count_documents({
                'time_slot': {'$in': off_schedule + [str(i) for i in off_schedule]},
                'status': {'$in': ['pending', 'approved', 'paid']},
                'date': {'$gte': get_bangladesh_now().strftime('%Y-%m-%d')}
            })
            if orphaned:
                print(f"WARNING: {orphaned} upcoming Khulna booking(s) are on slots outside the new "
                      f"schedule (now disabled). Review them in Admin > Bookings.")

        print(f"Applied Khulna two-venue football schedule for {khulna['name']}: "
              f"{len(scheduled_ids)} slots ({created} new), {len(off_schedule)} off-schedule slots disabled")
