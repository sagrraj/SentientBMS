from fastapi import APIRouter, HTTPException
from backend.app.simulation.simulation_engine import engine

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "app": "SentientBMS"}

@router.post("/simulation/step")
def step_simulation():
    res = engine.step_sentient()
    return res

@router.post("/simulation/run")
def run_simulation():
    engine.run_sentient_full()
    return {"status": "success", "steps_completed": len(engine.sentient_history)}

@router.post("/simulation/reset")
def reset_simulation():
    engine.reset()
    return {"status": "reset"}

@router.post("/simulation/inject_violation")
def inject_violation():
    engine.inject_violation_flag = True
    return {"status": "violation_queued"}
