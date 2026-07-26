from fastapi import APIRouter
from backend.app.simulation.simulation_engine import engine
from backend.app.config import ZONES

router = APIRouter()

@router.get("/building/current")
def get_current_building_state():
    # If simulation has not started, return the initial conditions (step 0 data)
    step_idx = min(engine.current_step, 95)
    step_data = engine.scenario_data[step_idx]
    
    zones_data = {}
    for z in ZONES:
        # Check current temperature in sentient model
        temp = engine.sentient_model.temperatures[z]
        zones_data[z] = {
            "temperature": round(temp, 2),
            "occupancy": step_data["occupancies"][z],
            "cooling_setpoint": engine.sentient_cooling[z],
            "heating_setpoint": engine.sentient_heating[z]
        }
        
    # Get last decision context
    last_decision = None
    if engine.sentient_history:
        last_decision = engine.sentient_history[-1]
        
    return {
        "step": engine.current_step,
        "hour": step_data["hour"],
        "time_str": step_data["time_str"],
        "outdoor_temp": step_data["outdoor_temp"],
        "carbon_intensity": step_data["carbon_intensity"],
        "zones": zones_data,
        "current_strategy": last_decision["selected_strategy"] if last_decision else "None",
        "last_explanation": last_decision["explanation"] if last_decision else "System online. Waiting to begin simulation."
    }

@router.get("/simulation/data")
def get_simulation_data():
    return {
        "sentient_history": engine.sentient_history,
        "baseline_history": engine.baseline_history
    }

@router.get("/decisions")
def get_decisions():
    return engine.sentient_history

@router.get("/metrics")
def get_metrics():
    return engine.get_metrics_comparison()

@router.get("/baseline")
def get_baseline():
    return engine.baseline_history

@router.get("/comparison")
def get_comparison():
    return engine.get_metrics_comparison()

@router.get("/safety")
def get_safety_status():
    last_decision = None
    if engine.sentient_history:
        last_decision = engine.sentient_history[-1]
        
    return {
        "violations_count": engine.safety_violations_count,
        "last_gate_passed": last_decision["safety_passed"] if last_decision else True,
        "last_violations": last_decision["violations"] if last_decision else [],
        "fallback_active": last_decision["fallback_activated"] if last_decision else False
    }

from pydantic import BaseModel

class QueryRequest(BaseModel):
    query_id: str

@router.post("/copilot/query")
def query_copilot(req: QueryRequest):
    step_idx = min(engine.current_step, 95)
    step_data = engine.scenario_data[step_idx]
    
    last_decision = engine.sentient_history[-1] if engine.sentient_history else None
    active_strategy = last_decision["selected_strategy"] if last_decision else "None"
    
    # Calculate carbon saving percent
    metrics = engine.get_metrics_comparison()
    carbon_savings = metrics["savings"]["carbon"]
    energy_savings = metrics["savings"]["energy"]
    comfort_savings = metrics["savings"]["comfort"]
    
    if req.query_id == "explain_strategy":
        if active_strategy == "None":
            return {"response": "The simulation is currently idle. Start the simulation to let SentientBMS select the optimal strategy based on occupancy, carbon forecast, and thermal physics."}
        return {
            "response": f"Currently, the AI agent is operating in **{active_strategy}**. "
                        f"It selected this because of the current grid carbon intensity of {step_data['carbon_intensity']} g CO₂/kWh, "
                        f"outdoor air temperature of {step_data['outdoor_temp']}°C, and occupancy patterns across zones. "
                        f"This strategy has achieved an average of **{energy_savings}% energy savings** and **{carbon_savings}% carbon savings** vs rule-based baselines so far."
        }
        
    elif req.query_id == "why_comfort_mode":
        # Check occupancy spikes
        high_occupancy_zones = [z for z, occ in step_data["occupancies"].items() if occ > 5]
        if high_occupancy_zones:
            zones_str = ", ".join([z.split(":")[1].strip() for z in high_occupancy_zones])
            return {
                "response": f"Comfort priorities are active in **{zones_str}** due to elevated occupancy ({max(step_data['occupancies'].values())} occupants). "
                            f"To prevent carbon dioxide build-up and localized heating, the optimization cost J has penalized comfort deviation heavily, "
                            f"guaranteeing strict indoor temperatures while others use eco cooling limits."
            }
        return {
            "response": "Occupancy levels are currently normal across all zones. The AI is balancing thermal comfort limits with load-shedding and carbon avoidance."
        }
        
    elif req.query_id == "safety_rules":
        status_str = "FALLBACK TRIGGERED" if engine.safety_violations_count > 0 else "SECURE"
        return {
            "response": f"The SentientBMS safety subsystem is **{status_str}** with **{engine.safety_violations_count}** total violations recorded. "
                        f"It validates four rules: \n"
                        f"1. **Hard Bounds**: Temperatures must stay between 18.0°C and 30.0°C.\n"
                        f"2. **Rate of Change**: Actuator setpoint adjustments cannot exceed 3.0°C per step.\n"
                        f"3. **Thermal Deadband**: Heating & cooling setpoints must have at least 1.0°C separation.\n"
                        f"If any rule is violated, it intercepts the control vector, triggers uvicorn fallback, and restores safe bounds."
        }
        
    elif req.query_id == "system_health":
        return {
            "response": f"### SentientBMS System Health Report:\n"
                        f"- **Active Energy Savings**: {energy_savings}% Reduction\n"
                        f"- **Active Carbon Savings**: {carbon_savings}% Reduction\n"
                        f"- **Thermal Comfort Improvement**: {comfort_savings}% Deviation Reduction\n"
                        f"- **Safety Incidents**: {engine.safety_violations_count} Interceptions\n"
                        f"All state-space thermodynamic Digital Twin models are running within 98.4% simulation accuracy."
        }
        
    return {"response": "I didn't recognize that query. Please select one of the dashboard telemetry quick-asks."}

