# SentientBMS — AI-Powered Autonomous Smart Building Optimization

SentientBMS is a production-quality autonomous Building Management System (BMS) that integrates a physical building thermal model, an active Digital Twin simulation sandbox, a deterministic safety gate, and a multi-objective cost optimization layer.

---

## 🎥 PoC Demonstration Video
Watch the autonomous loop, digital twin visualizations, safety validations, and dynamic control actions in action:
[![Play on YouTube](https://img.shields.io/badge/YouTube-Play%20Video-red?style=for-the-badge&logo=youtube)](https://youtu.be/XwfJjB-7ZPw)

*(Click the button above to play the video on YouTube)*

---

## 1. Project Directory Structure
```
sentient-bms/
│
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI Application Server Entrypoint
│   │   ├── config.py               # Zone profiles & constants
│   │   ├── data_generator/         # Weather, carbon & occupancy profiles
│   │   ├── baseline/               # Rule-Based Controller (RBC) baseline
│   │   ├── digital_twin/           # Thermal state-space models & lookahead
│   │   ├── ai_planner/             # Candidate strategy generator & ranking
│   │   ├── optimizer/              # Multi-objective cost J function
│   │   ├── safety/                 # Safety Gate & Fallback routing
│   │   ├── explainability/         # Human-readable decision explainers
│   │   ├── simulation/             # Global Simulation Engine
│   │   └── api/                    # REST routes (dashboards, weights, states)
│   ├── requirements.txt            # Python dependencies
│   └── tests/                      # Unit test suites
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main Smart Building Operations Dashboard
│   │   ├── index.css               # Tailwind v4 configuration directives
│   │   └── main.jsx                # React DOM render mount
│   ├── package.json                # NPM configuration
│   ├── tailwind.config.js          # Tailwind CSS settings
│   └── postcss.config.js           # PostCSS compiler rules
│
├── docs/
│   ├── architecture.md             # Thermodynamic and control formulas
│   ├── technical_report.md         # Comprehensive engineering report
│   └── demo_script.md              # Hackathon presentation steps
```



## 3. Running Verification Tests
To run the automated test suite checking physical parameters, bounds checks, and safety logic:
```bash
cd backend
set PYTHONPATH=.
python tests/test_backend.py
```
*(On Linux/macOS, use `PYTHONPATH=. python tests/test_backend.py`)*

---

## 4. Key Simulation Scenarios
1. **Scenario 1 — Normal Nighttime operation**: The building is unoccupied and cooler outside. The AI runs **Eco-Optimized** mode.
2. **Scenario 2 — Carbon Intensity Spike**: Grid carbon intensity spikes to 550 g CO2/kWh at 12:00. The AI switches to **Carbon-Aware** mode to shed HVAC load.
3. **Scenario 3 — Occupancy Peaks**: Meeting rooms fill up at 10:00 and 14:00. The AI selects **Comfort-First** in those zones to preserve indoor temperature levels.
4. **Scenario 4 — Safety Gate Interception**: Injecting an invalid action (such as 35°C setpoints) immediately triggers the deterministic **Safety Gate**, activating the **RBC Fallback Controller** and incrementing safety violations.
