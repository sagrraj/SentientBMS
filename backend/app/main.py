import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api import simulation_routes, dashboard_routes, strategy_routes

app = FastAPI(
    title="SentientBMS Backend API",
    description="Autonomous Building Energy Management System with Digital Twin & AI Planning",
    version="1.0.0"
)

# Configure CORS for React frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(simulation_routes.router, prefix="/api", tags=["simulation"])
app.include_router(dashboard_routes.router, prefix="/api", tags=["dashboard"])
app.include_router(strategy_routes.router, prefix="/api", tags=["strategy"])

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
