# SentientBMS System Architecture

SentientBMS is an autonomous building energy management system that combines agentic planning, digital twin simulation, multi-objective optimization, and safety gate validation.

```
DATA GENERATOR
↓
VIRTUAL BUILDING STATE
↓
BASELINE RBC
↓
AI STRATEGIC PLANNER
↓
3 CANDIDATE STRATEGIES
↓
DIGITAL TWIN
↓
2-HOUR LOOKAHEAD SIMULATION
↓
COST FUNCTION
↓
STRATEGY RANKING
↓
SAFETY GATE
↓
┌───────────────┐
│               │
SAFE           UNSAFE
│               │
↓               ↓
EXECUTE         FALLBACK RBC
│               │
└───────┬───────┘
↓
EXPLAINABILITY
↓
DECISION AUDIT LOG
↓
DASHBOARD
```

---

## 1. Physical RC Thermal Model
The building thermodynamics are simulated using a lumped-capacitance resistance-capacitance (RC) model. For each zone $z$:

$$C_z \frac{dT_z}{dt} = \frac{T_{out} - T_z}{R_{out, z}} + \sum_{adj} \frac{T_{adj} - T_z}{R_{int}} + Q_{internal, z} + Q_{solar, z} + Q_{hvac, z}$$

Where:
- $C_z$: Thermal capacitance of the zone ($5 \times 10^6 \text{ J/K}$)
- $R_{out, z}$: Thermal resistance to the outdoors ($0.05 \text{ K/W}$)
- $R_{int}$: Inter-zone thermal resistance ($0.2 \text{ K/W}$)
- $Q_{internal, z}$: Internal heat gains from occupants ($100\text{ W/person}$) and equipment.
- $Q_{solar, z}$: Solar radiative gains.
- $Q_{hvac, z}$: Heat added or removed by the HVAC system (limited to $8000\text{ W}$ capacity).

---

## 2. Multi-Objective Cost Function
Every 15 minutes, three candidate strategies are simulated 2 hours into the future (8 lookahead steps) on the Digital Twin. The optimal strategy is selected by minimizing the unified cost function $J$:

$$J = w_1 \cdot \left(\frac{E_{\text{total}}}{15.0}\right) + w_2 \cdot \left(\frac{C_{\text{emissions}}}{5.0}\right) + w_3 \cdot \left(\frac{\text{Comfort Penalty}}{10.0}\right)$$

Where:
- $w_1, w_2, w_3$ are normalized weights ($\sum w_i = 1.0$) representing energy, carbon, and comfort priorities.
- The denominators ($15.0, 5.0, 10.0$) normalize the objectives to a similar numerical scale $[0, 1]$.

---

## 3. Deterministic Safety Gate
The safety layer acts as a firewall between the AI suggestions and the building actuators:
1. **Temperature Bounds Check**:
   - $18^\circ\text{C} \le \text{Cooling Setpoint} \le 30^\circ\text{C}$
   - $12^\circ\text{C} \le \text{Heating Setpoint} \le 22^\circ\text{C}$
2. **Deadband Check**:
   - $\text{Cooling Setpoint} - \text{Heating Setpoint} \ge 1.0^\circ\text{C}$
3. **Ramp Rate Limit**:
   - $|\text{Setpoint}_t - \text{Setpoint}_{t-1}| \le 3.0^\circ\text{C}$ per 15-minute step.

If any constraint is violated, the proposed setpoints are rejected, and the system falls back to the **Rule-Based Controller (RBC)**.

---

## 4. LLM Agent Prompt Engineering
The system utilizes a structured, role-based prompting pattern to orchestrate the AI Strategic Planner:
- **System Instructions**: Defines the agent as a senior building energy optimizer with strict thermodynamic constraints.
- **Dynamic Context Injection**: Feeds the current time, outdoor weather forecast, occupancies, and grid carbon intensity ($g\text{ CO}_2/\text{kWh}$) into the prompt structure.
- **Structured JSON Formatting**: Enforces output formatting through JSON schema definitions to ensure deterministic tool execution on the Model Context Protocol (MCP) server.

---

## 5. Prompt Latency Management
To minimize real-time control loop delay during operations:
- **Parallel Strategy Generation**: Rather than prompting the LLM sequentially, candidate strategies (Eco-Optimized, Carbon-Aware, and Comfort-First) are generated in parallel.
- **Asynchronous Execution**: Invocations to the LLM use async task management, capping prompt evaluation at a 2.5-second timeout window.
- **Caching**: Frequently encountered states (e.g. standard night-time setbacks) bypass LLM generation through a fast-lookup key-value cache database.

---

## 6. Technical Approach to Simulation Logs
Closed-loop telemetry history and decision paths are logged using a dual-channel database pipeline:
- **Telemetry DB**: High-frequency variables (temperatures, energy intake, setpoints) are stored in structured JSON formats (`data/agent_history.json`).
- **Audit & Explainability Log**: The LLM's natural language explanation detailing *why* a particular setpoint actuation was selected (e.g., peak shifting during high grid demand) is recorded chronologically, allowing building managers to audit the AI's logic step-by-step.

