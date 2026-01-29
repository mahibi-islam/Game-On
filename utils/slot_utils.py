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

    return sorted(slots, key=get_sort_key)

def is_past_slot(slot_time_str, date_str):
    """
    Checks if a slot is in the past relative to Bangladesh Standard Time.
    slot_time_str: e.g., '06:00 AM - 07:30 AM' or '18:30 - 20:00'
    date_str: e.g., '2026-01-29'
    """
    try:
        now_bst = get_bangladesh_now()
        today_bst_str = now_bst.strftime('%Y-%m-%d')
        
        # If date is in the past, all slots are past
        if date_str < today_bst_str:
            return True
        # If date is in the future, no slots are past
        if date_str > today_bst_str:
            return False
            
        # If date is today, check the start time
        start_time_str = slot_time_str.split('-')[0].strip()
        slot_minutes = parse_time_to_minutes(start_time_str)
        
        # Convert slot minutes to a datetime object for better comparison if needed,
        # but simple minutes comparison is fine for "today".
        now_minutes = now_bst.hour * 60 + now_bst.minute
        
        return slot_minutes < now_minutes
    except Exception:
        return False
