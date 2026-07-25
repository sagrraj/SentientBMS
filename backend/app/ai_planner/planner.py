from typing import Dict, Any, List
from backend.app.ai_planner.strategy_generator import generate_strategies
from backend.app.digital_twin.simulator import simulate_strategy_lookahead

class AIPlanner:
    def __init__(self):
        pass
        
    def plan(self, current_state: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Generates candidate strategies, runs lookahead simulation on Digital Twin,
        ranks them by cost score, and returns the selected optimal strategy.
        """
        # 1. Generate 3 candidate strategies
        candidates = generate_strategies(current_state)
        
        evaluated_strategies = []
        best_strategy = None
        lowest_score = float('inf')
        
        # 2. Simulate each strategy through the Digital Twin lookahead
        for name, setpoints in candidates.items():
            sim_res = simulate_strategy_lookahead(
                current_temperatures={z: current_state["zones"][z]["temperature"] for z in current_state["zones"]},
                current_hour=current_state["hour"],
                cooling_setpoints=setpoints["cooling"],
                heating_setpoints=setpoints["heating"],
                weights=weights
            )
            
            evaluated = {
                "name": name,
                "cooling": setpoints["cooling"],
                "heating": setpoints["heating"],
                "energy_kwh": sim_res["energy_kwh"],
                "carbon_kg": sim_res["carbon_kg"],
                "comfort_penalty": sim_res["comfort_penalty"],
                "score": sim_res["score"],
                "reason": setpoints["reason"]
            }
            
            evaluated_strategies.append(evaluated)
            
            if sim_res["score"] < lowest_score:
                lowest_score = sim_res["score"]
                best_strategy = evaluated
                
        return {
            "strategies": evaluated_strategies,
            "selected_strategy": best_strategy
        }
