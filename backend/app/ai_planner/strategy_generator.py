from typing import Dict, Any
from backend.app.config import ZONES

def generate_strategies(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates exactly three candidate strategies: Eco-Optimized, Comfort-First, and Carbon-Aware.
    Returns setpoint proposals for each zone.
    """
    hour = state["hour"]
    outdoor_temp = state["outdoor_temp"]
    carbon_intensity = state["carbon_intensity"]
    zones_data = state["zones"]
    
    strategies = {}
    
    # 1. Eco-Optimized (Setpoint range: 24°C to 27°C cooling, 16°C to 18°C heating)
    eco_setpoints = {}
    for zone in ZONES:
        occ = zones_data[zone]["occupancy"]
        if occ == 0:
            eco_setpoints[zone] = {"cooling": 28.0, "heating": 15.0}
        else:
            eco_setpoints[zone] = {"cooling": 25.5, "heating": 18.0}
    strategies["Eco-Optimized"] = {
        "cooling": {z: s["cooling"] for z, s in eco_setpoints.items()},
        "heating": {z: s["heating"] for z, s in eco_setpoints.items()},
        "reason": "Optimize energy efficiency by maintaining slightly wider temperature bands and relaxing unoccupied zones."
    }
    
    # 2. Comfort-First (Setpoint range: 21°C to 24°C cooling, 20°C to 22°C heating)
    comfort_setpoints = {}
    for zone in ZONES:
        occ = zones_data[zone]["occupancy"]
        if occ == 0:
            comfort_setpoints[zone] = {"cooling": 26.0, "heating": 16.0}
        else:
            comfort_setpoints[zone] = {"cooling": 22.0, "heating": 20.5}
    strategies["Comfort-First"] = {
        "cooling": {z: s["cooling"] for z, s in comfort_setpoints.items()},
        "heating": {z: s["heating"] for z, s in comfort_setpoints.items()},
        "reason": "Prioritize indoor climate by keeping tight setpoints close to the optimal comfort level (22°C)."
    }
    
    # 3. Carbon-Aware (Setpoint range: 24°C to 26°C cooling, 17°C to 19°C heating)
    carbon_setpoints = {}
    for zone in ZONES:
        occ = zones_data[zone]["occupancy"]
        if occ == 0:
            carbon_setpoints[zone] = {"cooling": 27.5, "heating": 15.0}
        else:
            if carbon_intensity >= 450.0:
                # High carbon intensity: curtail cooling load
                carbon_setpoints[zone] = {"cooling": 26.0, "heating": 17.5}
            elif carbon_intensity < 250.0:
                # Clean grid hours: pre-cool the space to store thermal mass
                carbon_setpoints[zone] = {"cooling": 21.5, "heating": 20.0}
            else:
                # Normal grid
                carbon_setpoints[zone] = {"cooling": 24.0, "heating": 19.0}
    strategies["Carbon-Aware"] = {
        "cooling": {z: s["cooling"] for z, s in carbon_setpoints.items()},
        "heating": {z: s["heating"] for z, s in carbon_setpoints.items()},
        "reason": f"Grid carbon is {'elevated' if carbon_intensity >= 450.0 else ('clean' if carbon_intensity < 250.0 else 'moderate')}. Adjusting load accordingly."
    }
    
    return strategies
