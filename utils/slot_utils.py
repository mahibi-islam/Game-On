from datetime import datetime, timedelta, timezone

def get_bangladesh_tz():
    """
    Returns the timezone object for Bangladesh Standard Time (UTC+6).
    """
    return timezone(timedelta(hours=6))

def get_bangladesh_now():
    """
    Returns the current time in Bangladesh Standard Time (UTC+6).
    """
    return datetime.now(timezone.utc).astimezone(get_bangladesh_tz())

def parse_time_to_minutes(time_str):
    """
    Parses a time string (e.g., '06:00', '18:30', '01:30 AM', '12:00 AM') 
    into minutes from the start of the day.
    """
    if not time_str:
        return 0
        
    time_str = time_str.strip().upper()
    
    # Handle AM/PM formats
    if 'AM' in time_str or 'PM' in time_str:
        try:
            # Handle formats like '01:30 AM', '1:30 PM', '12:00AM'
            period = 'AM' if 'AM' in time_str else 'PM'
            # Remove AM/PM and split by space if exists
            t_part = time_str.replace('AM', '').replace('PM', '').strip()
            
            h_m = t_part.split(':')
            hour = int(h_m[0])
            minute = int(h_m[1]) if len(h_m) > 1 else 0
            
            if period == 'PM' and hour < 12:
                hour += 12
            if period == 'AM' and hour == 12:
                hour = 0
            
            return hour * 60 + minute
        except Exception:
            return 0
    else:
        # Handle 24h formats like '06:00' or '18:30'
        try:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return hour * 60 + minute
        except Exception:
            return 0

def slot_label(slot, default='N/A'):
    """
    Display label for a slot: its time, plus the venue name when the
    location has more than one venue (e.g. '06:00-07:30 (Venue 2)').
    """
    if not slot:
        return default
    time_str = slot.get('time', default)
    venue = slot.get('venue')
    return f"{time_str} ({venue})" if venue else time_str

def sort_slots(slots, start_hour=6):
    """
    Sorts a list of slots starting from a specific hour (default 06:00 AM).
    Slots starting before this hour are moved to the end of the day.
    """
    start_minutes = start_hour * 60
    
    def get_sort_key(slot):
        time_field = slot.get('time', '00:00')
        # Handle formats like "06:00-07:30" or "06:00 AM - 07:30 AM"
        start_time_str = time_field.split('-')[0].strip()
        
        minutes = parse_time_to_minutes(start_time_str)
        
        if minutes < start_minutes:
            return minutes + 1440
        return minutes

    # Group by venue (stable sort keeps time order within each venue)
    return sorted(sorted(slots, key=get_sort_key), key=lambda s: s.get('venue') or '')

BUSINESS_DAY_START_HOUR = 6

def rate_type_for_date(date_obj):
    """'weekend' for Friday/Saturday (weekday() 4/5), otherwise 'weekday'."""
    return 'weekend' if date_obj.weekday() in (4, 5) else 'weekday'

def slot_start_datetime(date_str, slot_time_str, day_start_hour=BUSINESS_DAY_START_HOUR):
    """
    Actual start of a slot booked on `date_str`, in Bangladesh time.
    A booking date is a business day running 06:00 -> 06:00, so slots that
    start before 06:00 (e.g. '00:00-01:30') happen on the following calendar day.
    """
    start_minutes = parse_time_to_minutes(slot_time_str.split('-')[0].strip())
    start = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=get_bangladesh_tz())
    start += timedelta(minutes=start_minutes)
    if start_minutes < day_start_hour * 60:
        start += timedelta(days=1)
    return start

def is_past_slot(slot_time_str, date_str):
    """
    Checks if a slot has already started relative to Bangladesh Standard Time.
    slot_time_str: e.g., '06:00 AM - 07:30 AM' or '18:30 - 20:00'
    date_str: e.g., '2026-01-29'
    """
    try:
        return slot_start_datetime(date_str, slot_time_str) < get_bangladesh_now()
    except Exception:
        return False
