from typing import Dict, Any
from backend.app.digital_twin.thermal_model import BuildingThermalModel
from backend.app.data_generator.weather import get_outdoor_temperature
from backend.app.data_generator.occupancy import get_zone_occupancy
from backend.app.data_generator.carbon import get_grid_carbon_intensity
from backend.app.optimizer.cost_function import evaluate_objective

def simulate_strategy_lookahead(
    current_temperatures: Dict[str, float],
    current_hour: float,
    cooling_setpoints: Dict[str, float],
    heating_setpoints: Dict[str, float],
    weights: Dict[str, float]
) -> Dict[str, Any]:
    """
    Simulates the building's thermal and energy response 2 hours (8 steps) into the future
    under the specified setpoints. Calculates total energy, carbon, and comfort penalty.
    """
    # Clone thermal model and set current state
    sandbox = BuildingThermalModel()
    sandbox.temperatures = current_temperatures.copy()
    
    total_energy = 0.0
    total_carbon = 0.0
    total_comfort_penalty = 0.0
    
    # Store projected temperatures over time for analysis if needed
    projected_temps_history = []
    
    # Run 8 steps of 15 minutes each (2 hours lookahead)
    for step in range(8):
        future_hour = (current_hour + step * 0.25) % 24
        
        # Get forecasted environment parameters
        outdoor_temp = get_outdoor_temperature(future_hour)
        carbon_intensity = get_grid_carbon_intensity(future_hour)
        
        occupancies = {z: get_zone_occupancy(z, future_hour) for z in sandbox.zones}
        
        # Step the thermal simulation
        temps, hvac_energy = sandbox.step(
            cooling_setpoints,
            heating_setpoints,
            occupancies,
            outdoor_temp,
            future_hour,
            dt=900.0
        )
        
        # Calculate step metrics
        step_energy = sum(hvac_energy.values())
        step_carbon = step_energy * (carbon_intensity / 1000.0)
        
        # Calculate comfort penalty for this step
        # T_MIN_COMFORT = 20.0, T_MAX_COMFORT = 24.5
        step_comfort = 0.0
        for z in sandbox.zones:
            occ = occupancies[z]
            if occ > 0:
                t = temps[z]
                if t < 20.0:
                    step_comfort += (20.0 - t) ** 2
                elif t > 24.5:
                    step_comfort += (t - 24.5) ** 2
                    
        total_energy += step_energy
        total_carbon += step_carbon
        total_comfort_penalty += step_comfort
        projected_temps_history.append(temps.copy())
        
    # Evaluate normalized cost function
    eval_results = evaluate_objective(total_energy, total_carbon * 1000.0 / (total_energy + 1e-6) if total_energy > 0 else 0, total_comfort_penalty, weights)
    
    # Format return dictionary
    return {
        "energy_kwh": round(total_energy, 4),
        "carbon_kg": round(total_carbon, 4),
        "comfort_penalty": round(total_comfort_penalty, 4),
        "score": eval_results["score"],
        "projected_temperatures": projected_temps_history[-1],
        "cooling_setpoints": cooling_setpoints,
        "heating_setpoints": heating_setpoints
    }
