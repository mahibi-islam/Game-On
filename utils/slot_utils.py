from datetime import datetime

def parse_time_to_minutes(time_str):
    """
    Parses a time string (e.g., '06:00', '18:30', '01:30 AM', '06:00 PM') 
    into minutes from the start of the day.
    """
    time_str = time_str.strip().upper()
    
    # Handle AM/PM formats
    if 'AM' in time_str or 'PM' in time_str:
        try:
            # Try to handle formats like '01:30 AM' or '6:00PM'
            # First, extract the time part and the AM/PM part
            if ' ' in time_str:
                parts = time_str.split(' ')
                t_part = parts[0]
                period = parts[1]
            else:
                # If there's no space, handle cases like '6:00PM'
                period = 'AM' if 'AM' in time_str else 'PM'
                t_part = time_str.replace(period, '')
            
            h_m = t_part.split(':')
            hour = int(h_m[0])
            minute = int(h_m[1]) if len(h_m) > 1 else 0
            
            if period == 'PM' and hour < 12:
                hour += 12
            if period == 'AM' and hour == 12:
                hour = 0
            
            return hour * 60 + minute
        except Exception:
            # Fallback if parsing fails
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
        # The time field usually looks like "06:00-07:30" or "06:00 AM - 07:30 AM"
        time_field = slot.get('time', '00:00')
        start_time_str = time_field.split('-')[0].strip()
        
        minutes = parse_time_to_minutes(start_time_str)
        
        # Adjust minutes so that the sort starts from start_minutes
        # Example: if start_hour is 6, minutes 0-359 (12 AM - 5:59 AM) are shifted
        # by +1440 (24 hours) to appear after minutes 360-1439.
        if minutes < start_minutes:
            return minutes + 1440
        return minutes

    return sorted(slots, key=get_sort_key)
