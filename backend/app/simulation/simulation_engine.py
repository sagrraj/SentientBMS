from typing import Dict, Any, List, Tuple
from backend.app.data_generator.generator import generate_24h_scenario
from backend.app.digital_twin.thermal_model import BuildingThermalModel
from backend.app.baseline.rbc_controller import RuleBasedController
from backend.app.ai_planner.planner import AIPlanner
from backend.app.safety.safety_gate import SafetyGate
from backend.app.safety.fallback import FallbackController
from backend.app.explainability.decision_explainer import generate_explanation
from backend.app.optimizer.cost_function import evaluate_objective
from backend.app.config import ZONES, DEFAULT_WEIGHTS

class SimulationEngine:
    def __init__(self):
        self.scenario_data = generate_24h_scenario()
        self.weights = DEFAULT_WEIGHTS.copy()
        
        self.rbc = RuleBasedController()
        self.planner = AIPlanner()
        self.safety_gate = SafetyGate()
        self.fallback_controller = FallbackController()
        
        self.reset()
        
    def reset(self):
        self.current_step = 0
        self.safety_violations_count = 0
        self.inject_violation_flag = False
        
        # Initialize building thermal models
        self.sentient_model = BuildingThermalModel()
        
        # Active setpoints trackers
        self.sentient_cooling = {z: 22.0 for z in ZONES}
        self.sentient_heating = {z: 20.0 for z in ZONES}
        
        self.sentient_history = []
        self.baseline_history = []
        self.run_baseline_full()

    def run_baseline_full(self):
        """
        Runs the Rule-Based Controller baseline simulation for the full 24 hours (96 steps).
        """
        model = BuildingThermalModel()
        self.baseline_history = []
        
        for step_data in self.scenario_data:
            hour = step_data["hour"]
            outdoor_temp = step_data["outdoor_temp"]
            carbon_intensity = step_data["carbon_intensity"]
            occupancies = step_data["occupancies"]
            
            cooling_setpoints = {}
            heating_setpoints = {}
            for z in ZONES:
                c, h = self.rbc.get_setpoints(z, hour)
                cooling_setpoints[z] = c
                heating_setpoints[z] = h
                
            temps, hvac_energy = model.step(
                cooling_setpoints,
                heating_setpoints,
                occupancies,
                outdoor_temp,
                hour,
                dt=900.0
            )
            
            total_energy = sum(hvac_energy.values())
            step_carbon = total_energy * (carbon_intensity / 1000.0)
            
            # Calculate comfort penalty
            comfort_penalty = 0.0
            for z in ZONES:
                occ = occupancies[z]
                if occ > 0:
                    t = temps[z]
                    if t < 20.0:
                        comfort_penalty += (20.0 - t) ** 2
                    elif t > 24.5:
                        comfort_penalty += (t - 24.5) ** 2
                        
            self.baseline_history.append({
                "step": step_data["step"],
                "hour": hour,
                "time_str": step_data["time_str"],
                "outdoor_temp": outdoor_temp,
                "carbon_intensity": carbon_intensity,
                "occupancies": occupancies.copy(),
                "temperatures": temps.copy(),
                "cooling_setpoints": cooling_setpoints.copy(),
                "heating_setpoints": heating_setpoints.copy(),
                "energy_kwh": total_energy,
                "carbon_kg": step_carbon,
                "comfort_penalty": comfort_penalty
            })

    def step_sentient(self) -> Dict[str, Any]:
        """
        Advances the SentientBMS simulation by one 15-minute step.
        """
        if self.current_step >= len(self.scenario_data):
            return {"status": "finished"}
            
        step_data = self.scenario_data[self.current_step]
        hour = step_data["hour"]
        outdoor_temp = step_data["outdoor_temp"]
        carbon_intensity = step_data["carbon_intensity"]
        occupancies = step_data["occupancies"]
        
        # 1. Read current building state
        current_state = {
            "hour": hour,
            "outdoor_temp": outdoor_temp,
            "carbon_intensity": carbon_intensity,
            "zones": {
                z: {
                    "temperature": self.sentient_model.temperatures[z],
                    "occupancy": occupancies[z]
                } for z in ZONES
            }
        }
        
        # 2. AI Planner generates candidate strategies and selects the best
        planning_results = self.planner.plan(current_state, self.weights)
        selected_strategy = planning_results["selected_strategy"]
        
        proposed_cooling = selected_strategy["cooling"].copy()
        proposed_heating = selected_strategy["heating"].copy()
        
        # Scenario 4 Injection: force a safety violation
        if self.inject_violation_flag:
            # Overwrite Zone 1 cooling setpoint to 35.0°C (exceeds max limit of 30.0°C)
            # which is guaranteed to fail safety validation.
            proposed_cooling["Zone 1: Open Office"] = 35.0
            self.inject_violation_flag = False  # Reset flag
            
        # 3. Pass through Safety Gate
        safety_passed, violations = self.safety_gate.validate(
            proposed_cooling,
            proposed_heating,
            self.sentient_cooling,
            self.sentient_heating
        )
        
        fallback_activated = False
        final_cooling = proposed_cooling
        final_heating = proposed_heating
        
        if not safety_passed:
            fallback_activated = True
            self.safety_violations_count += 1
            # Run fallback Rule-Based Controller
            final_cooling, final_heating = self.fallback_controller.get_fallback_setpoints(ZONES, hour)
            
        # 4. Actuate setpoints on Building Model & Update EnergyPlus IDF Model
        try:
            from simulation.energyplus_wrapper import energyplus_bridge
            # Generate the modified .idf file representing the new setpoints
            energyplus_bridge.update_setpoints(final_cooling, final_heating, output_path="simulation/modified.idf")
            # Execute EnergyPlus run (will run if binary is installed locally, else skips)
            energyplus_bridge.run_energyplus("simulation/modified.idf")
        except Exception as e:
            print(f"[SimulationEngine] EnergyPlus simulation bridge skipped: {e}")

        temps, hvac_energy = self.sentient_model.step(
            final_cooling,
            final_heating,
            occupancies,
            outdoor_temp,
            hour,
            dt=900.0
        )
        
        # 5. Calculate step metrics
        total_energy = sum(hvac_energy.values())
        step_carbon = total_energy * (carbon_intensity / 1000.0)
        
        comfort_penalty = 0.0
        for z in ZONES:
            occ = occupancies[z]
            if occ > 0:
                t = temps[z]
                if t < 20.0:
                    comfort_penalty += (20.0 - t) ** 2
                elif t > 24.5:
                    comfort_penalty += (t - 24.5) ** 2
                    
        # Update setpoint references
        self.sentient_cooling = final_cooling.copy()
        self.sentient_heating = final_heating.copy()
        
        # 6. Generate human explanation
        explanation = generate_explanation(
            selected_name=selected_strategy["name"] if not fallback_activated else "RBC Fallback",
            score=selected_strategy["score"],
            metrics={"energy_kwh": total_energy, "carbon_kg": step_carbon},
            outdoor_temp=outdoor_temp,
            carbon_intensity=carbon_intensity,
            occupancy_count=sum(occupancies.values()),
            safety_passed=safety_passed,
            fallback_activated=fallback_activated
        )
        
        # Record history
        record = {
            "step": self.current_step,
            "hour": hour,
            "time_str": step_data["time_str"],
            "outdoor_temp": outdoor_temp,
            "carbon_intensity": carbon_intensity,
            "occupancies": occupancies.copy(),
            "temperatures": temps.copy(),
            "cooling_setpoints": self.sentient_cooling.copy(),
            "heating_setpoints": self.sentient_heating.copy(),
            "energy_kwh": total_energy,
            "carbon_kg": step_carbon,
            "comfort_penalty": comfort_penalty,
            "candidate_strategies": planning_results["strategies"],
            "selected_strategy": selected_strategy["name"],
            "safety_passed": safety_passed,
            "violations": violations,
            "fallback_activated": fallback_activated,
            "explanation": explanation
        }
        
        self.sentient_history.append(record)
        self.current_step += 1
        return record

    def run_sentient_full(self):
        """
        Runs the SentientBMS controller for the remaining/all steps.
        """
        while self.current_step < len(self.scenario_data):
            self.step_sentient()

    def get_metrics_comparison(self) -> Dict[str, Any]:
        """
        Calculates total energy, carbon, comfort penalty for Baseline and SentientBMS.
        """
        # Sum of elements up to current step
        steps_completed = len(self.sentient_history)
        if steps_completed == 0:
            return {
                "baseline": {"energy": 0, "carbon": 0, "comfort": 0, "violations": 0},
                "sentient": {"energy": 0, "carbon": 0, "comfort": 0, "violations": 0},
                "savings": {"energy": 0, "carbon": 0, "comfort": 0}
            }
            
        base_sub = self.baseline_history[:steps_completed]
        
        base_energy = sum(x["energy_kwh"] for x in base_sub)
        base_carbon = sum(x["carbon_kg"] for x in base_sub)
        base_comfort = sum(x["comfort_penalty"] for x in base_sub)
        
        sent_energy = sum(x["energy_kwh"] for x in self.sentient_history)
        sent_carbon = sum(x["carbon_kg"] for x in self.sentient_history)
        sent_comfort = sum(x["comfort_penalty"] for x in self.sentient_history)
        
        # Avoid division by zero
        energy_savings = ((base_energy - sent_energy) / (base_energy + 1e-6)) * 100.0
        carbon_savings = ((base_carbon - sent_carbon) / (base_carbon + 1e-6)) * 100.0
        comfort_improvement = ((base_comfort - sent_comfort) / (base_comfort + 1e-6)) * 100.0
        
        return {
            "baseline": {
                "energy": round(base_energy, 2),
                "carbon": round(base_carbon, 2),
                "comfort": round(base_comfort, 2),
                "violations": 0
            },
            "sentient": {
                "energy": round(sent_energy, 2),
                "carbon": round(sent_carbon, 2),
                "comfort": round(sent_comfort, 2),
                "violations": self.safety_violations_count
            },
            "savings": {
                "energy": round(energy_savings, 1),
                "carbon": round(carbon_savings, 1),
                "comfort": round(comfort_improvement, 1)
            }
        }

# Global Simulation Engine instance
engine = SimulationEngine()

