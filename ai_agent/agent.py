import json

class SentientBMSAgent:
    def __init__(self):
        self.role = "Facility AI Energy Optimization Architect"
        
    def generate_candidate_strategies(self, state):
        """
        Generate three plausible operational hypotheses based on the current building state.
        In a production system, this sends a prompt to Qwen/Llama with the building state.
        Here we model the AI reasoning agent generating three distinct control strategies.
        """
        hour = state["hour"]
        outdoor_temp = state["outdoor_temp"]
        carbon_intensity = state["carbon_intensity"]
        zones = state["zones"]
        
        # Base templates
        strategies = {
            "Strategy A (Eco-Optimized)": {},
            "Strategy B (Comfort-First)": {},
            "Strategy C (Carbon-Aware Load-Shifting)": {}
        }
        
        for name in strategies.keys():
            cooling = {}
            heating = {}
            for z, data in zones.items():
                occ = data["occupancy"]
                # Start with standard occupied sets
                c_set, h_set = 22.0, 20.0
                
                if occ == 0:
                    # Unoccupied: relax setpoints
                    c_set, h_set = 27.0, 16.0
                else:
                    if "Eco" in name:
                        # Eco-Optimized: slightly warmer in summer, cooler in winter
                        c_set = 23.5 if outdoor_temp > 22 else 22.5
                        h_set = 19.0
                    elif "Comfort" in name:
                        # Comfort-First: Keep perfect temperatures
                        c_set = 21.5
                        h_set = 20.5
                    elif "Carbon" in name:
                        # Carbon-Aware: Shift load.
                        if carbon_intensity > 400:
                            # High carbon intensity: raise cooling setpoint to reduce load
                            c_set = 24.5
                            h_set = 18.5
                        elif carbon_intensity < 150:
                            # Low carbon intensity: pre-cool/pre-heat
                            c_set = 20.5
                            h_set = 21.5
                        else:
                            c_set = 22.5
                            h_set = 19.5
                
                cooling[z] = c_set
                heating[z] = h_set
                
            strategies[name] = {"cooling": cooling, "heating": heating}
            
        return strategies

    def choose_best_strategy(self, state, simulated_results, explanation_weights):
        """
        AI evaluates the results of sandbox runs and explains its decision.
        """
        best_name = None
        min_cost = float('inf')
        
        for name, res in simulated_results.items():
            if res["cost"] < min_cost:
                min_cost = res["cost"]
                best_name = name
                
        # Generate concise explanation log from AI
        best_res = simulated_results[best_name]
        hour = state["hour"]
        outdoor_temp = state["outdoor_temp"]
        carbon_intensity = state["carbon_intensity"]
        
        reasons = []
        if "Carbon" in best_name:
            reasons.append(f"Grid carbon intensity is currently {carbon_intensity} g/kWh. Selecting Carbon-Aware strategy to minimize emissions.")
        elif "Eco" in best_name:
            reasons.append("Low occupancy or moderate weather detected. Eco-Optimized strategy minimizes baseline energy consumption.")
        else:
            reasons.append("Occupant presence is high. Comfort-First strategy selected to prevent comfort penalty violations.")
            
        reasons.append(f"Predicted Cost J={best_res['cost']:.3f} (Energy Cost: {best_res['energy_cost']:.3f}, Carbon Cost: {best_res['carbon_cost']:.3f}, Comfort Penalty: {best_res['comfort_penalty']:.3f}).")
        
        explanation = " ".join(reasons)
        
        return {
            "selected_strategy": best_name,
            "cooling_setpoints": self.filter_for_active_state(best_name, simulated_results),
            "heating_setpoints": self.filter_for_active_state_heating(best_name, simulated_results),
            "explanation": explanation
        }
        
    def filter_for_active_state(self, best_name, simulated_results):
        return simulated_results[best_name]["cooling"]
        
    def filter_for_active_state_heating(self, best_name, simulated_results):
        return simulated_results[best_name]["heating"]
