import streamlit as st
import json
import pandas as pd
import os
import subprocess

st.set_page_config(page_title="SentientBMS", layout="wide")

# Custom CSS for Premium Design
st.markdown("""
    <style>
    .main {
        background-color: #0f111a;
        color: #e2e8f0;
    }
    .metric-card {
        background-color: #1e2230;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 14px;
        color: #94a3b8;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
    }
    .ai-log {
        background-color: #111827;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #374151;
        font-family: monospace;
        height: 250px;
        overflow-y: scroll;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ SentientBMS — Autonomous Building Optimization")
st.markdown("### Closed-Loop AI Sandbox & Digital Twin Optimization Engine")

# Sidebar for tuning optimization weights
st.sidebar.header("🎯 Tuning Agent Priorities")
st.sidebar.write("Adjust weights to change the objective function J:")

w_energy = st.sidebar.slider("Energy Cost Weight (w1)", 0.0, 5.0, 1.0, 0.1)
w_carbon = st.sidebar.slider("Carbon Penalty Weight (w2)", 0.0, 5.0, 0.5, 0.1)
w_comfort = st.sidebar.slider("Comfort Violation Weight (w3)", 0.0, 5.0, 2.0, 0.1)

# Re-run simulation trigger
if st.sidebar.button("⚡ Re-Run Simulation with New Weights"):
    with st.spinner("Re-simulating SentientBMS under new objective weights..."):
        # Update weights in files directly by generating a small script or modifying runner setup
        # For simplicity, we can dynamically rewrite optimization/objective.py to reflect these weights
        obj_code = f"""class ObjectiveEvaluator:
    def __init__(self):
        self.weights = {{
            "energy": {w_energy},
            "carbon": {w_carbon},
            "comfort": {w_comfort}
        }}
        self.t_min_comfort = 20.0
        self.t_max_comfort = 24.5

    def calculate_comfort_penalty(self, temp, occupancy):
        if occupancy == 0:
            return 0.0
        penalty = 0.0
        if temp < self.t_min_comfort:
            penalty = (self.t_min_comfort - temp) ** 2
        elif temp > self.t_max_comfort:
            penalty = (temp - self.t_max_comfort) ** 2
        return penalty

    def evaluate(self, energy_kwh, carbon_intensity_g_kwh, zone_temps, occupancies):
        carbon_emissions = energy_kwh * (carbon_intensity_g_kwh / 1000.0)
        comfort_penalties = []
        for zone, temp in zone_temps.items():
            occ = occupancies.get(zone, 0)
            comfort_penalties.append(self.calculate_comfort_penalty(temp, occ))
        total_comfort_penalty = sum(comfort_penalties)
        j_val = (self.weights["energy"] * energy_kwh +
                 self.weights["carbon"] * carbon_emissions +
                 self.weights["comfort"] * total_comfort_penalty)
        return {{
            "cost": float(j_val),
            "energy_cost": float(self.weights["energy"] * energy_kwh),
            "carbon_cost": float(self.weights["carbon"] * carbon_emissions),
            "comfort_cost": float(self.weights["comfort"] * total_comfort_penalty),
            "carbon_emissions": float(carbon_emissions),
            "comfort_penalty": float(total_comfort_penalty)
        }}
"""
        with open("optimization/objective.py", "w") as f:
            f.write(obj_code)
            
        # Re-run simulation
        subprocess.run(["python", "runner.py"], check=True)
        st.success("Simulation finished successfully!")

# Load simulation history
if os.path.exists("data/baseline_history.json") and os.path.exists("data/agent_history.json"):
    with open("data/baseline_history.json", "r") as f:
        base_hist = json.load(f)
    with open("data/agent_history.json", "r") as f:
        agent_hist = json.load(f)
        
    # KPIs Calculation
    base_total_energy = sum(step["total_energy"] for step in base_hist)
    agent_total_energy = sum(step["total_energy"] for step in agent_hist)
    energy_savings = ((base_total_energy - agent_total_energy) / base_total_energy) * 100.0
    
    base_total_carbon = sum(step["metrics"]["carbon_emissions"] for step in base_hist)
    agent_total_carbon = sum(step["metrics"]["carbon_emissions"] for step in agent_hist)
    carbon_savings = ((base_total_carbon - agent_total_carbon) / base_total_carbon) * 100.0
    
    base_comfort_pen = sum(step["metrics"]["comfort_penalty"] for step in base_hist)
    agent_comfort_pen = sum(step["metrics"]["comfort_penalty"] for step in agent_hist)
    
    # Render KPI Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: #3b82f6;">
                <div class="metric-title">⚡ TOTAL ENERGY USAGE</div>
                <div class="metric-value">{agent_total_energy:.2f} kWh <span style="font-size: 16px; color: #10b981;">(Saved {energy_savings:.1f}%)</span></div>
                <div style="font-size: 12px; color: #94a3b8;">Baseline: {base_total_energy:.2f} kWh</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: #10b981;">
                <div class="metric-title">🌱 CARBON EMISSIONS</div>
                <div class="metric-value">{agent_total_carbon:.2f} kg CO2 <span style="font-size: 16px; color: #10b981;">(Saved {carbon_savings:.1f}%)</span></div>
                <div style="font-size: 12px; color: #94a3b8;">Baseline: {base_total_carbon:.2f} kg CO2</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        comfort_status = "Improved" if agent_comfort_pen <= base_comfort_pen else "Degraded"
        color = "#10b981" if agent_comfort_pen <= base_comfort_pen else "#ef4444"
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: #8b5cf6;">
                <div class="metric-title">🛋️ TOTAL COMFORT PENALTY</div>
                <div class="metric-value">{agent_comfort_pen:.2f} <span style="font-size: 16px; color: {color};">({comfort_status})</span></div>
                <div style="font-size: 12px; color: #94a3b8;">Baseline penalty: {base_comfort_pen:.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
    # Main Plots
    st.markdown("### 📈 Simulation Analytics")
    
    # Collect data for plotting
    hours = [step["hour"] for step in agent_hist]
    out_temp = [step["outdoor_temp"] for step in agent_hist]
    carb_intensity = [step["carbon_intensity"] for step in agent_hist]
    
    # Zones Dataframes
    df_dict = {
        "Hour": hours,
        "Outdoor Temperature": out_temp,
        "Carbon Intensity (g/kWh)": carb_intensity
    }
    
    for z in ["Zone 1: Open Office", "Zone 2: Meeting Room", "Zone 3: Executive Suite"]:
        df_dict[f"{z} - AI Temp"] = [step["temperatures"][z] for step in agent_hist]
        df_dict[f"{z} - Base Temp"] = [step["temperatures"][z] for step in base_hist]
        df_dict[f"{z} - AI Cooling Setpoint"] = [step["cooling_setpoints"][z] for step in agent_hist]
        df_dict[f"{z} - Occupancy"] = [step["occupancies"][z] for step in agent_hist]
        
    df = pd.DataFrame(df_dict)
    
    tab1, tab2, tab3 = st.tabs(["🌡️ Temperatures & Setpoints", "🔋 Energy & Carbon Profile", "👥 Occupancy Patterns"])
    
    with tab1:
        st.write("Compare SentientBMS adaptive setpoint tuning vs Baseline:")
        zone_select = st.selectbox("Select Zone to View", ["Zone 1: Open Office", "Zone 2: Meeting Room", "Zone 3: Executive Suite"])
        
        plot_df = df[["Hour", f"{zone_select} - AI Temp", f"{zone_select} - Base Temp", f"{zone_select} - AI Cooling Setpoint", "Outdoor Temperature"]]
        st.line_chart(plot_df.set_index("Hour"))
        
    with tab2:
        st.write("Energy Consumption & Grid Carbon Intensity Over Time:")
        energy_df = pd.DataFrame({
            "Hour": hours,
            "AI HVAC Energy (kWh)": [step["total_energy"] for step in agent_hist],
            "Baseline HVAC Energy (kWh)": [step["total_energy"] for step in base_hist],
            "Carbon Intensity (g CO2/kWh)": carb_intensity
        })
        st.line_chart(energy_df.set_index("Hour"))
        
    with tab3:
        st.write("Dynamic Occupancy Profiles by Zone:")
        occ_df = df[["Hour", "Zone 1: Open Office - Occupancy", "Zone 2: Meeting Room - Occupancy", "Zone 3: Executive Suite - Occupancy"]]
        st.line_chart(occ_df.set_index("Hour"))
        
    # AI Decision Activity Log
    st.markdown("### 🪵 SentientBMS Decision Activity Log")
    log_content = ""
    for step in agent_hist:
        time_str = f"{int(step['hour']):02d}:{int((step['hour'] % 1) * 60):02d}"
        log_content += f"[{time_str}] STRATEGY: {step['ai_strategy']} | OUTDOOR: {step['outdoor_temp']:.1f}°C | CARBON: {step['carbon_intensity']:.0f} g/kWh\n"
        log_content += f" -> REASONING: {step['ai_explanation']}\n"
        log_content += f" -> SAFETY STATUS: {step['safety_log']['status']} ({step['safety_log']['reason']})\n"
        log_content += "-"*80 + "\n"
        
    st.text_area("Live Output Log from Autonomous Agent Decision Loop:", value=log_content, height=280)
    
else:
    st.warning("Simulation history files not found. Run runner.py first to generate the logs.")
