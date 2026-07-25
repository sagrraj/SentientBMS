import math

def get_outdoor_temperature(hour: float) -> float:
    """
    Returns outdoor temperature for a given hour.
    Peaks at 14:00 at 36.0°C and dips at 04:00 at 24.0°C.
    Uses a smooth sinusoidal profile with slight deterministic noise.
    """
    # Sinusoidal wave peaking at 14:00
    base = 30.0  # Daily mean
    amplitude = 6.0  # Range: 24.0°C to 36.0°C
    
    # 14:00 corresponds to phase pi/2 -> (hour - 8)/12 * pi
    # At hour = 14, sin((14-8)/12 * pi) = sin(pi/2) = 1 => 36.0°C
    # At hour = 2, sin((2-8)/12 * pi) = sin(-pi/2) = -1 => 24.0°C
    temp = base + amplitude * math.sin((hour - 8.0) / 12.0 * math.pi)
    
    # Add small deterministic noise based on sine of hour*3 to make it look realistic
    noise = 0.2 * math.sin(hour * 3.0)
    return round(temp + noise, 2)
