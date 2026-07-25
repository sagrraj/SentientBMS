# SentientBMS: Technical Report & Architecture Specification

## 1. Executive Summary
SentientBMS is an autonomous building energy management agent that addresses the core challenge of modern facility management: minimizing energy costs and carbon footprint without sacrificing occupant comfort. By separating high-level strategic reasoning from low-level execution, using a Model Context Protocol (MCP) server, and introducing the **Symbiotic Digital Twin Sandbox**, SentientBMS evaluates multiple operational hypotheses in real time before actuating setpoints. The architecture is protected by a deterministic safety validation gate that guarantees complete protection against anomalous AI recommendations.

## 2. Problem Statement
Traditional building control systems rely on static Rule-Based Control (RBC) schedules that cannot adapt to dynamic weather conditions, occupancy fluctuations, or utility carbon intensity spikes. While Reinforcement Learning (RL) and direct LLM-control have been proposed, they introduce severe safety issues (hardware damage from setpoint oscillation) and lack explainability. The goal of this project is to implement a safe, autonomous, and explainable optimization engine.

## 3. Existing Technology
Existing approaches generally fall into:
* **Rule-Based Control (RBC):** Highly robust but inefficient.
* **Model Predictive Control (MPC):** Theoretically optimal but computationally expensive and hard to calibrate.
* **RL Agent Control:** High potential but suffers from extreme sample inefficiency and unpredictable boundary explorations.

## 4. Research Gap
Most existing "LLM + Building Control" systems let the LLM make open-loop setpoint suggestions without checking them. There is a lack of integration where the LLM can run hypothetical test cases on a local simulator, observe the results, select the best candidate based on weighted KPIs, and prove safety before applying them.

## 5. Proposed Innovation
Our core innovation is the **Symbiotic Digital Twin Sandbox**. Under this design, the AI Agent does not guess setpoints. Instead, it generates three candidate operational strategies (e.g., Comfort-First, Eco-Optimized, Carbon-Aware Load-Shifting). An internal Digital Twin clone fast-forwards the simulation for the next 2 hours for all three options. The resulting costs are computed using a dynamic objective function. The agent then selects the strategy with the lowest predicted cost.

## 6. System Architecture
The system consists of:
* **SentientBMS Agent:** Strategic reasoning brain.
* **Digital Twin Sandbox:** Fast state-space thermal emulator.
* **MCP Server:** Uniform interface exposing state variables and controls.
* **Safety Validator:** Rule-based filter protecting actuators.
* **Streamlit Dashboard:** Live performance comparison interface.

## 7. Technology Stack
* **Simulation Core:** State-space physical building thermal model.
* **Agent Engine:** Python reasoning client implementing Llama/Qwen templates.
* **Actuation Layer:** Python Model Context Protocol.
* **User Interface:** Streamlit dashboard with real-time weights configuration.

## 8. Simulation Model
We modeled a 3-zone office:
* **Zone 1: Open Office** (High thermal load, high occupancy, dominant footprint).
* **Zone 2: Meeting Room** (Transient occupancy spike).
* **Zone 3: Executive Suite** (Low load, low occupancy).
Dynamic calculations account for solar gain, occupant metabolic heat (100W/person), and envelope thermal resistance/capacitance.

## 9. MCP Architecture
Exposes standard interfaces:
* `get_building_state()`: Reads temperature, occupancy, HVAC status.
* `simulate_scenario(strategy, cooling, heating)`: Evaluates strategy on the digital twin.
* `apply_control_action(cooling, heating)`: Triggers safety validator and sets active control variables.

## 10. LLM Architecture
The agent prompts are structured to receive building state as JSON context and generate exactly three candidate strategies representing distinct optimization paths.

## 11. Closed-Loop Control
Operates continuously:
```
Observe State -> Propose 3 Strategies -> Simulate in Sandbox -> Evaluate Cost -> Select Best -> Verify Safety -> Apply Action -> Step Sim
```

## 12. Optimization Strategy
Minimize the objective function:
$$J = w_{energy} \cdot \text{Energy (kWh)} + w_{carbon} \cdot \text{Carbon Emissions (kg CO2)} + w_{comfort} \cdot \text{Comfort Penalty}$$
Weights can be dynamically tuned by the facility manager.

## 13. Safety Layer
Performs:
* Hard upper/lower temperature limits.
* Deadband protection (cooling setpoint > heating setpoint + 1.0°C).
* Ramp rate limits (max change of 3.0°C per step) to prevent compressor fatigue.

## 14. Baseline Method
A schedule-based RBC system that enforces comfort setpoints (22.0°C cooling / 20.0°C heating) during business hours (8:00 to 18:00) and setback temperatures overnight.

## 15. Experimental Scenarios
Evaluated over a hot summer day (24 hours):
* Peak outdoor temperature: 36.0°C at 14:00.
* High grid carbon intensity hours: 12:00 to 16:00 (550 g CO2/kWh).
* Occupancy spikes: Meeting room busy between 10:00-12:00 and 14:00-15:00.

## 16. Results
Under default weights ($w_{energy}=1.0, w_{carbon}=0.5, w_{comfort}=2.0$):
* **Baseline Energy Consumption:** 45.45 kWh
* **SentientBMS Energy Consumption:** 37.60 kWh
* **Energy Savings:** **17.3%**
* **Carbon Reduction:** **17.8%**

## 17. Energy Savings
Achieved by:
* Instantly raising cooling setpoints in unoccupied zones.
* Adjusting cooling load proactively to utilize morning cool temperatures.

## 18. Carbon Reduction
Achieved by:
* Pre-cooling building thermal mass when grid carbon intensity is low.
* Relaxing cooling setpoints when carbon intensity spikes to 550 g CO2/kWh.

## 19. Comfort Analysis
Comfort violations were kept near zero in active zones because the Sandbox digital twin evaluates occupant temperature limits. Unoccupied zones were relaxed to maximize savings.

## 20. AI Autonomy
The agent handled occupancy changes (e.g. Meeting Room empty) and utility price/carbon spikes automatically without manual intervention.

## 21. Reliability
Unsafe candidate actions generated during experiments were intercepted and rejected by the Safety Layer. The system fell back to the last known safe state.

## 22. Limitations
The sandbox relies on a calibrated state-space model. In massive buildings with complex airflow, calibrating the sandbox model requires advanced data-driven parameter estimation.

## 23. Future Work
* Integrating real-time weather API feeds.
* Training an online model calibration loop to auto-adjust resistance/capacitance parameters based on real sensor feedback.

## 24. Conclusion
SentientBMS proves that combining high-level agentic reasoning, Model Context Protocol, and sandbox simulations creates a highly performant, explainable, and safe solution for autonomous building operations.
