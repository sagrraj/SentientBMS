from typing import Dict, List, Any
from backend.app.data_generator.weather import get_outdoor_temperature
from backend.app.data_generator.occupancy import get_zone_occupancy
from backend.app.data_generator.carbon import get_grid_carbon_intensity
from backend.app.config import ZONES

def generate_24h_scenario() -> List[Dict[str, Any]]:
    """
    Generates a 96-step time series (15-minute intervals) for a 24-hour simulation.
    """
    steps = []
    total_steps = 24 * 4  # 96 steps
    
    for s in range(total_steps):
        hour = s * 0.25
        outdoor_temp = get_outdoor_temperature(hour)
        carbon_intensity = get_grid_carbon_intensity(hour)
        
        occupancies = {}
        for zone in ZONES:
            occupancies[zone] = get_zone_occupancy(zone, hour)
            
        steps.append({
            "step": s,
            "hour": hour,
            "time_str": f"{int(hour):02d}:{int((hour % 1) * 60):02d}",
            "outdoor_temp": outdoor_temp,
            "carbon_intensity": carbon_intensity,
            "occupancies": occupancies
        })
        
    return steps
