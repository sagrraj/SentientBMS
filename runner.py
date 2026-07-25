import json
import os
import math
from simulation.building_model import BuildingModel
from baseline.rule_based_controller import RuleBasedController
from mcp_server.server import MCPServer
from ai_agent.agent import SentientBMSAgent
from optimization.objective import ObjectiveEvaluator

# Define Weather, Occupancy, and Carbon Scenarios for a 24-hour simulation
def get_scenario_data(hour):
    # Weather: summer peak hot day
    # Temp peaks at 14:00 at 36C
    outdoor_temp = 22.0 + 14.0 * max(0.0, math.sin((hour - 6) / 12.0 * math.pi)) if 6 <= hour <= 18 else 22.0
    
    # Grid Carbon Intensity: peak carbon intensity when grid is stressed (12:00 to 16:00)
    if 12 <= hour <= 16:
        carbon_intensity = 550.0 # g CO2/kWh
    elif 18 <= hour <= 22:
        carbon_intensity = 400.0
    else:
        carbon_intensity = 120.0 # Clean grid hours
        
    # Occupancy
    occupancies = {
        "Zone 1: Open Office": 0,
        "Zone 2: Meeting Room": 0,
        "Zone 3: Executive Suite": 0
    }
    
    if 8 <= hour <= 18:
        occupancies["Zone 1: Open Office"] = 18
        # Meeting Room busy only between 10:00-12:00 and 14:00-15:00
        if (10 <= hour < 12) or (14 <= hour < 15):
            occupancies["Zone 2: Meeting Room"] = 12
        occupancies["Zone 3: Executive Suite"] = 2
        
    return outdoor_temp, carbon_intensity, occupancies

def run_simulations():
    # Make sure output data directory exists
    os.makedirs("data", exist_ok=True)
    
    # ----------------------------------------------------
    # 1. RUN BASELINE SIMULATION (Rule-Based Controller)
    # ----------------------------------------------------
    baseline_model = BuildingModel()
    rbc = RuleBasedController()
    evaluator = ObjectiveEvaluator()
    
    baseline_history = []
    
    # Run 24 hours in 15-minute steps
    total_steps = 24 * 4
    for step in range(total_steps):
        hour = step * 0.25
        outdoor_temp, carbon_intensity, occupancies = get_scenario_data(hour)
        
        # Get setpoints
        cooling_setpoints = {}
        heating_setpoints = {}
        for z in baseline_model.zones:
            c_set, h_set = rbc.get_setpoints(z, hour)
            cooling_setpoints[z] = c_set
            heating_setpoints[z] = h_set
            
        # Run building model step
        temps, energy_kwh = baseline_model.step(
            cooling_setpoints,
            heating_setpoints,
            occupancies,
            outdoor_temp,
            hour,
            dt=900
        )
        
        total_energy = sum(energy_kwh.values())
        cost_metrics = evaluator.evaluate(total_energy, carbon_intensity, temps, occupancies)
        
        baseline_history.append({
            "hour": hour,
            "outdoor_temp": outdoor_temp,
            "carbon_intensity": carbon_intensity,
            "occupancies": occupancies.copy(),
            "temperatures": temps.copy(),
            "cooling_setpoints": cooling_setpoints.copy(),
            "heating_setpoints": heating_setpoints.copy(),
            "energy_kwh": energy_kwh.copy(),
            "total_energy": total_energy,
            "metrics": cost_metrics
        })
        
    # Save baseline history
    with open("data/baseline_history.json", "w") as f:
        json.dump(baseline_history, f, indent=2)
        
    # ----------------------------------------------------
    # 2. RUN SENTIENTBMS SIMULATION (Autonomous Agent + Sandbox)
    # ----------------------------------------------------
    mcp = MCPServer()
    agent = SentientBMSAgent()
    
    agent_history = []
    
    for step in range(total_steps):
        hour = step * 0.25
        outdoor_temp, carbon_intensity, occupancies = get_scenario_data(hour)
        
        # Feed actual scenario inputs to MCP Server state
        mcp.hour = hour
        mcp.outdoor_temp = outdoor_temp
        mcp.carbon_intensity = carbon_intensity
        mcp.occupancies = occupancies.copy()
        
        # Get current state from MCP Server
        current_state = mcp.get_building_state()
        
        # AI Agent proposes 3 Candidate Strategies
        strategies = agent.generate_candidate_strategies(current_state)
        
        # Simulate all strategies inside Digital Twin Sandbox
        simulated_results = {}
        for name, setpoints in strategies.items():
            sim_res = mcp.simulate_scenario(name, setpoints["cooling"], setpoints["heating"])
            simulated_results[name] = sim_res
            
        # AI selects the best-performing strategy
        decision = agent.choose_best_strategy(current_state, simulated_results, mcp.evaluator.weights)
        
        # Actuate through MCP Server
        cooling_act = decision["cooling_setpoints"]
        heating_act = decision["heating_setpoints"]
        
        applied, msg = mcp.apply_control_action(cooling_act, heating_act)
        
        # Safety Gate validation logs
        safety_log = {
            "status": "APPROVED" if applied else "REJECTED",
            "reason": msg,
            "proposed_cooling": cooling_act,
            "proposed_heating": heating_act
        }
        
        # Run building model active step in simulator
        temps, energy_kwh = mcp.model.step(
            mcp.current_cooling,
            mcp.current_heating,
            occupancies,
            outdoor_temp,
            hour,
            dt=900
        )
        
        total_energy = sum(energy_kwh.values())
        cost_metrics = mcp.evaluator.evaluate(total_energy, carbon_intensity, temps, occupancies)
        
        agent_history.append({
            "hour": hour,
            "outdoor_temp": outdoor_temp,
            "carbon_intensity": carbon_intensity,
            "occupancies": occupancies.copy(),
            "temperatures": temps.copy(),
            "cooling_setpoints": mcp.current_cooling.copy(),
            "heating_setpoints": mcp.current_heating.copy(),
            "energy_kwh": energy_kwh.copy(),
            "total_energy": total_energy,
            "metrics": cost_metrics,
            "ai_strategy": decision["selected_strategy"],
            "ai_explanation": decision["explanation"],
            "safety_log": safety_log
        })
        
    # Save agent history
    with open("data/agent_history.json", "w") as f:
        json.dump(agent_history, f, indent=2)

if __name__ == "__main__":
    print("Starting smart building simulations...")
    run_simulations()
    print("Simulations complete! Outputs written to data/baseline_history.json and data/agent_history.json")
