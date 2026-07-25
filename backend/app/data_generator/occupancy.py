def get_zone_occupancy(zone: str, hour: float) -> int:
    """
    Returns occupancy count for a zone given the hour of day.
    Office hours: 08:00 to 18:00.
    - Zone 1: ~18 people (continuous).
    - Zone 2 (Meeting Room): transient spikes of ~10-12 people at 10:00 and 14:00.
    - Zone 3 (Executive Suite): 2 people steady.
    """
    is_work_hours = (8.0 <= hour < 18.0)
    
    if not is_work_hours:
        return 0

    if "Zone 1" in zone:
        return 18
    elif "Zone 2" in zone:
        # Meetings from 10:00 - 12:00 and 14:00 - 15:30
        if (10.0 <= hour < 12.0):
            return 10
        elif (14.0 <= hour < 15.5):
            return 12
        else:
            return 1  # Standard quiet occupancy
    elif "Zone 3" in zone:
        return 2
    return 0
