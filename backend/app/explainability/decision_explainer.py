from typing import Dict, Any

def generate_explanation(
    selected_name: str,
    score: float,
    metrics: Dict[str, float],
    outdoor_temp: float,
    carbon_intensity: float,
    occupancy_count: int,
    safety_passed: bool,
    fallback_activated: bool
) -> str:
    """
    Generates a human-readable explanation explaining why the controller selected a given strategy.
    """
    reasons = []
    
    # 1. State assessment
    if carbon_intensity >= 450.0:
        reasons.append(f"Grid carbon intensity is extremely high ({carbon_intensity} g CO2/kWh).")
    elif carbon_intensity < 250.0:
        reasons.append(f"Grid carbon intensity is low ({carbon_intensity} g CO2/kWh), representing clean electricity.")
        
    if outdoor_temp >= 33.0:
        reasons.append(f"Outdoor temperature is hot ({outdoor_temp}°C), increasing building thermal loads.")
    elif outdoor_temp <= 22.0:
        reasons.append(f"Outdoor temperature is moderate ({outdoor_temp}°C).")
        
    if occupancy_count > 20:
        reasons.append(f"Total occupancy is high ({occupancy_count} people) across the zones.")
    elif occupancy_count == 0:
        reasons.append("The building is currently unoccupied.")
        
    # 2. Strategy rationale
    if fallback_activated:
        reasons.append("The proposed AI strategy failed safety verification (ramp rate or bounds check) and was rejected. The trusted Rule-Based Controller was activated as a fallback.")
    else:
        if "Carbon-Aware" in selected_name:
            if carbon_intensity >= 450.0:
                reasons.append(f"Selected '{selected_name}' to curtail non-critical cooling loads and avoid high-carbon grid emissions.")
            else:
                reasons.append(f"Selected '{selected_name}' to load-shift (pre-cooling the thermal mass) while grid energy is clean.")
        elif "Eco-Optimized" in selected_name:
            reasons.append(f"Selected '{selected_name}' to minimize base electrical energy usage, allowing slightly higher temperature bands.")
        elif "Comfort-First" in selected_name:
            reasons.append(f"Selected '{selected_name}' to prioritize occupant comfort by narrowing temperature ranges around 22°C.")
            
    # Add numerical context
    if not fallback_activated:
        reasons.append(f"This strategy achieved the lowest unified objective score J = {score:.3f} (Projected Energy: {metrics.get('energy_kwh', 0.0):.2f} kWh, Projected Carbon: {metrics.get('carbon_kg', 0.0):.2f} kg CO2).")
        
    return " ".join(reasons)
