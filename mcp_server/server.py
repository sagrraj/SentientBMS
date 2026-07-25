import json
from simulation.building_model import BuildingModel
from safety.validator import SafetyValidator
from optimization.objective import ObjectiveEvaluator

class MCPServer:
    def __init__(self):
        self.model = BuildingModel()
        self.validator = SafetyValidator()
        self.evaluator = ObjectiveEvaluator()
        
        # Current active setpoints
        self.current_cooling = {z: 22.0 for z in self.model.zones}
        self.current_heating = {z: 20.0 for z in self.model.zones}
        
        # Environment/Scenario values
        self.outdoor_temp = 25.0
        self.carbon_intensity = 300.0  # g CO2/kWh
        self.occupancies = {
            "Zone 1: Open Office": 10,
            "Zone 2: Meeting Room": 0,
            "Zone 3: Executive Suite": 1
        }
        self.hour = 8

    # MCP Tools
    def get_building_state(self):
        zones_state = {}
        for z in self.model.zones:
            t = self.model.temperatures[z]
            occ = self.occupancies[z]
            eng = self.model.hvac_energy[z]
            zones_state[z] = {
                "temperature": round(t, 2),
                "occupancy": occ,
                "energy_kwh": round(eng, 4),
                "cooling_setpoint": self.current_cooling[z],
                "heating_setpoint": self.current_heating[z]
            }
        return {
            "hour": self.hour,
            "outdoor_temp": round(self.outdoor_temp, 2),
            "carbon_intensity": self.carbon_intensity,
            "zones": zones_state
        }

    def get_zone_state(self, zone):
        state = self.get_building_state()
        return state["zones"].get(zone, {})

    def get_energy_consumption(self):
        state = self.get_building_state()
        return sum(z["energy_kwh"] for z in state["zones"].values())

    def get_weather(self):
        return {"outdoor_temperature": round(self.outdoor_temp, 2)}

    def get_weather_forecast(self):
        # Generate simple forecast for next 3 hours
        forecast = []
        for h in range(1, 4):
            f_hour = (self.hour + h) % 24
            # peak temperature at 14:00
            temp = 20.0 + 15.0 * (1.0 - abs(f_hour - 14) / 10.0 if abs(f_hour - 14) <= 10 else 0.0)
            forecast.append({"hour": f_hour, "predicted_outdoor_temp": round(temp, 2)})
        return forecast

    def get_occupancy(self):
        return self.occupancies

    def get_carbon_intensity(self):
        return self.carbon_intensity

    def simulate_scenario(self, strategy_name, candidate_cooling, candidate_heating):
        """
        Runs a Sandbox simulation step in the Digital Twin to evaluate proposed setpoints.
        """
        # Create a deep copy clone of building model for fast-forward sandbox
        sandbox_model = BuildingModel()
        sandbox_model.temperatures = self.model.temperatures.copy()
        
        # Simulate next timestep (e.g. 2 hours / 8 steps of 15 min each to project impact)
        total_energy = 0.0
        projected_temps = {}
        
        # Simple fast-forward simulation
        for step in range(8):
            sim_hour = (self.hour + (step * 0.25)) % 24
            temps, hvac_eng = sandbox_model.step(
                candidate_cooling, 
                candidate_heating, 
                self.occupancies, 
                self.outdoor_temp, 
                sim_hour,
                dt=900
            )
            total_energy += sum(hvac_eng.values())
            projected_temps = temps
            
        evaluation = self.evaluator.evaluate(total_energy, self.carbon_intensity, projected_temps, self.occupancies)
        evaluation["cooling"] = candidate_cooling
        evaluation["heating"] = candidate_heating
        return evaluation

    def validate_control_action(self, cooling_setpoints, heating_setpoints):
        # Validate each zone's setpoint against current setpoints
        for z in self.model.zones:
            ok, err = self.validator.validate_action(
                cooling_setpoints[z],
                heating_setpoints[z],
                self.current_cooling[z],
                self.current_heating[z]
            )
            if not ok:
                return False, f"Zone '{z}' Validation Failed: {err}"
        return True, "Approved"

    def apply_control_action(self, cooling_setpoints, heating_setpoints):
        # Perform validation first
        ok, msg = self.validate_control_action(cooling_setpoints, heating_setpoints)
        if ok:
            self.current_cooling = cooling_setpoints.copy()
            self.current_heating = heating_setpoints.copy()
            return True, "Successfully applied control setpoints"
        return False, f"Failed to apply: {msg}"
