# SentientBMS — Engineering Technical Report

## 1. Executive Summary
SentientBMS is an agentic, closed-loop Building Management System (BMS) designed to optimize commercial building heating, ventilation, and air conditioning (HVAC) operations. By combining thermodynamic physics modeling (Digital Twin) with real-time AI planning (LLM) and deterministic safety gates, the system realizes up to **17.3% energy savings**, **17.8% carbon reduction**, and a **30.5% comfort penalty decrease** relative to standard Rule-Based Controllers (RBC).

---

## 2. System Architecture & Control Loop
The core control loop executes every 15 minutes (96 steps per day):

```
[State Sensors] ──> [AI Strategic Planner] ──> [Digital Twin Sandbox]
                          │                           │ (Simulate Candidates)
                          ▼                           ▼
                  [Proposed Action] ───────────> [Cost Function Evaluation]
                          │
                          ▼
                  [Safety HUD Gate] ──(PASS)───> [EnergyPlus Actuation]
                          │
                       (FAIL)
                          ▼
                  [RBC Fallback Controller]
```

### State Variables
At step $t$, the system reads the state vector:
$$\mathbf{x}_t = [T_{out, t}, C_{intensity, t}, \mathbf{N}_{occ, t}, \mathbf{T}_{zone, t}]$$
Where:
- $T_{out, t}$: Outdoor air temperature
- $C_{intensity, t}$: Grid carbon emissions footprint ($g\text{ CO}_2/\text{kWh}$)
- $\mathbf{N}_{occ, t}$: Occupant vector across zones
- $\mathbf{T}_{zone, t}$: Indoor air temperature vector across zones

---

## 3. Physical Thermodynamic Modeling (Digital Twin)
Each thermal zone is modeled as a lumped-capacitance resistance-capacitance (RC) network:

$$C_z \frac{dT_z}{dt} = \frac{T_{out} - T_z}{R_{out, z}} + \sum_{adj} \frac{T_{adj} - T_z}{R_{int}} + \dot{Q}_{occ, z} + \dot{Q}_{solar, z} - \dot{Q}_{hvac, z}$$

Where:
- Zone thermal capacitance ($C_z$) = $5.0 \times 10^6 \text{ J/K}$
- Outdoor thermal resistance ($R_{out, z}$) = $0.05 \text{ K/W}$
- Inter-zone thermal resistance ($R_{int}$) = $0.2 \text{ K/W}$
- HVAC maximum capacity = $8000 \text{ W}$ (heating/cooling limit)
- Occupant thermal load ($\dot{Q}_{occ, z}$) = $100 \text{ W/person}$

---

## 4. Multi-Objective Cost Optimization
At each step, the AI planner proposes three candidate strategies: **Eco-Optimized**, **Carbon-Aware**, and **Comfort-First**. Each strategy is evaluated over a 2-hour lookahead horizon (8 steps) in the Digital Twin. The strategy that minimizes the normalized cost function $J$ is selected:

$$J = w_{energy} \cdot \left(\frac{E_{total}}{15.0}\right) + w_{carbon} \cdot \left(\frac{C_{emissions}}{5.0}\right) + w_{comfort} \cdot \left(\frac{\text{Comfort Penalty}}{10.0}\right)$$

Where:
- $E_{total}$: Sum of electrical inputs consumed by HVAC pumps
- $C_{emissions}$: Computed carbon footprint ($E_{total} \times C_{intensity}$)
- $\text{Comfort Penalty}$: Sum of squared indoor temperature deviations beyond comfort boundaries ($20.0^\circ\text{C} - 24.5^\circ\text{C}$) during occupied hours.

---

## 5. Deterministic Safety HUD Gate
To protect mechanical systems from anomalous AI suggestions, proposed setpoints must pass validation:
1. **Actuator Bound Check**:
   - $18.0^\circ\text{C} \le T_{cool} \le 30.0^\circ\text{C}$
   - $12.0^\circ\text{C} \le T_{heat} \le 22.0^\circ\text{C}$
2. **Thermal separation (Deadband)**:
   - $T_{cool} - T_{heat} \ge 1.0^\circ\text{C}$
3. **Ramp rate limit**:
   - $|T_t - T_{t-1}| \le 3.0^\circ\text{C}$ per step.

**RBC Fallback**: Any validation failure bypasses the AI planner immediately, routes actuation to the Rule-Based Controller (RBC), increments the safety violations tally, and logs the incident in the Safety HUD diagnostics history.

---

## 6. Experimental Results & Energy Savings
The system was evaluated against a standard rule-based controller over a peak hot summer day:

| Metric | Baseline RBC | SentientBMS | % Savings |
| :--- | :--- | :--- | :--- |
| **HVAC Electrical Cost (kWh)** | 45.4 | 37.6 | **17.3%** |
| **Carbon Footprint (kg CO₂)** | 9.8 | 8.0 | **17.8%** |
| **Comfort Penalty Deviation** | 12.1 | 8.4 | **30.5%** |

- **Carbon Shedding**: During peak grid stress hours (12:00 - 16:00, intensity at $550g\text{ CO}_2/\text{kWh}$), SentientBMS dynamically relaxes cooling limits, shifting loads to cleaner hours.
- **Comfort Preservation**: When occupancy spikes in meeting rooms, Comfort-First priorities automatically stabilize temperatures.
