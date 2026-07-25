from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.simulation.simulation_engine import engine
from backend.app.optimizer.cost_function import normalize_weights

router = APIRouter()

class WeightsUpdate(BaseModel):
    energy: float
    carbon: float
    comfort: float

@router.post("/weights")
def update_weights(data: WeightsUpdate):
    # Normalize weights so they sum to 1.0
    weights_dict = {
        "energy": data.energy,
        "carbon": data.carbon,
        "comfort": data.comfort
    }
    normalized = normalize_weights(weights_dict)
    engine.weights = normalized
    
    # Save the current length of sentient history to rerun up to the same step, 
    # or just rerun full if it was already finished.
    prev_step = engine.current_step
    
    # Reset simulation
    engine.reset()
    engine.weights = normalized  # Re-apply after reset
    
    # Rerun up to the previous step (or full if it was completed)
    if prev_step > 0:
        for _ in range(prev_step):
            engine.step_sentient()
            
    return {
        "status": "success",
        "weights": engine.weights,
        "steps_rerun": engine.current_step
    }

@router.post("/optimization/run")
def run_optimization():
    engine.run_sentient_full()
    return {"status": "success", "metrics": engine.get_metrics_comparison()}
