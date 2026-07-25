from typing import Dict, Any

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Ensures that weights sum to exactly 1.0. If they do not, normalizes them.
    """
    total = sum(weights.values())
    if total == 0:
        return {"energy": 0.33, "carbon": 0.33, "comfort": 0.34}
    keys = list(weights.keys())
    normalized = {}
    running_sum = 0.0
    for k in keys[:-1]:
        val = round(weights[k] / total, 3)
        normalized[k] = val
        running_sum += val
    # Set the last one to be the exact remainder
    normalized[keys[-1]] = round(1.0 - running_sum, 3)
    return normalized

def evaluate_objective(energy_kwh: float, carbon_intensity: float, comfort_penalty: float, weights: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculates the multi-objective cost J:
    J = w1 * Energy_norm + w2 * Carbon_norm + w3 * Comfort_norm
    """
    norm_w = normalize_weights(weights)
    
    # Calculate carbon emissions in kg (energy_kwh * intensity in g/kWh / 1000)
    carbon_emissions_kg = energy_kwh * (carbon_intensity / 1000.0)
    
    # Normalization factors to bring all objectives to a similar numerical scale [0, 1]
    # Under typical 2-hour operational scenarios:
    energy_norm_factor = 15.0  # typical energy consumption limit for 2h (kWh)
    carbon_norm_factor = 5.0   # typical carbon footprint limit (kg CO2)
    comfort_norm_factor = 10.0  # typical comfort penalty scale
    
    normalized_energy = energy_kwh / energy_norm_factor
    normalized_carbon = carbon_emissions_kg / carbon_norm_factor
    normalized_comfort = comfort_penalty / comfort_norm_factor
    
    score = (
        norm_w["energy"] * normalized_energy +
        norm_w["carbon"] * normalized_carbon +
        norm_w["comfort"] * normalized_comfort
    )
    
    return {
        "score": round(score, 4),
        "normalized_energy": round(normalized_energy, 4),
        "normalized_carbon": round(normalized_carbon, 4),
        "normalized_comfort": round(normalized_comfort, 4),
        "carbon_emissions_kg": round(carbon_emissions_kg, 4)
    }
