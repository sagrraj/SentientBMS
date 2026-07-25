# SentientBMS Hackathon Demo Script

Follow this step-by-step guide to demonstrate the SentientBMS prototype to the judges.

---

## Prerequisites
1. Start the FastAPI backend server:
   ```bash
   cd backend
   python -m uvicorn app.main:app --port 8000
   ```
2. Start the Vite React frontend:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` in a web browser.

---

## Scenario 1: Normal Diurnal Operation (00:00 - 08:00)
- **Goal**: Show base schedules and nighttime relaxation.
- **Action**: Click the **Play** button or click the **Step** button multiple times.
- **Visuals**:
  - The simulation moves through nighttime steps.
  - Notice the AI selects **Eco-Optimized** because the building is unoccupied, keeping cooling setpoints relaxed at 28.0°C to save energy.

---

## Scenario 2: High Carbon Grid Event (12:00 - 15:00)
- **Goal**: Demonstrate carbon-awareness load shedding.
- **Action**: Step or let the play loop run until it reaches `12:00` (step 48).
- **Visuals**:
  - Grid carbon intensity spikes to `550.0 g CO2/kWh` (highlighted in the header).
  - The AI planner immediately shifts from Comfort-First to **Carbon-Aware** mode.
  - Setpoints are automatically raised in Zone 1 to reduce electrical load during dirty grid hours.
  - The Decision Audit Log details the exact grid carbon levels and the optimization score.

---

## Scenario 3: High Occupancy & Hot Weather (08:00 - 12:00)
- **Goal**: Demonstrate how the comfort weight prioritizes occupied rooms.
- **Action**: Notice Zone 2 (Meeting Room) occupancy spikes to 10 people at `10:00` (step 40).
- **Visuals**:
  - The AI shifts to **Comfort-First** in Zone 2 to cool the room to 22.0°C, preventing a comfort penalty.
  - In Zone 3 (Executive Suite), setpoints remain relaxed (24.0°C) since occupancy is very low.

---

## Scenario 4: Safety Violation Injection & Fallback RBC
- **Goal**: Prove that unsafe AI recommendations are rejected.
- **Action**: Click the **Inject Safety Violation** button during active play, then click **Step**.
- **Visuals**:
  - The next step will show `Safety Gate Monitor: FALLBACK ACTIVE`.
  - The violations list will display: `Zone 'Zone 1: Open Office': Cooling setpoint 35.0°C out of range [18.0, 30.0]`.
  - The active controller will immediately reject the AI setpoint and run the fallback Rule-Based Controller.
  - The Safety Violations counter in the KPI cards increments.
