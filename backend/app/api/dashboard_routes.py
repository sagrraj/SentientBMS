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
