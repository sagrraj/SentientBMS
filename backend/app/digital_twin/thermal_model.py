import math
from typing import Dict, Tuple
from backend.app.config import ZONES

class BuildingThermalModel:
    def __init__(self):
        self.zones = ZONES
        
        # Room Capacitances (J/K) and Resistance to outdoors (K/W)
        self.C = {z: 5e6 for z in self.zones}  # thermal capacity
        self.R_out = {z: 0.05 for z in self.zones}  # thermal resistance to outside
        self.R_int = 0.2  # thermal resistance between adjacent zones
        
        # Initial temperatures
        self.temperatures = {z: 22.0 for z in self.zones}
        
        # Max heating/cooling power (Watts)
        self.max_hvac_power = 8000.0  # 8 kW cooling/heating capacity per zone
        self.cop = 3.0  # Coefficient of Performance for HVAC
        
        # Current energy consumption (kWh) in last step
        self.hvac_energy = {z: 0.0 for z in self.zones}
        
    def get_internal_gains(self, zone: str, occupancy: int, hour: float) -> float:
        # Occupancy heat gain: 100W per person
        q_occ = occupancy * 100.0
        
        # Equipment/Lighting load based on hour of day
        if 8.0 <= hour < 18.0:
            q_equip = 1500.0 if "Zone 1" in zone else (800.0 if "Zone 2" in zone else 600.0)
        else:
            q_equip = 200.0
            
        return q_occ + q_equip

    def get_solar_gain(self, zone: str, hour: float, outdoor_temp: float) -> float:
        # Simple solar model peaking at 13:00
        if 6.0 <= hour < 18.0:
            solar_intensity = max(0.0, math.sin((hour - 6.0) / 12.0 * math.pi))
            q_solar = solar_intensity * (2000.0 if "Zone 1" in zone else 1000.0)
        else:
            q_solar = 0.0
        return q_solar

    def step(self, cooling_setpoints: Dict[str, float], heating_setpoints: Dict[str, float], 
             occupancy: Dict[str, int], outdoor_temp: float, hour: float, dt: float = 900.0) -> Tuple[Dict[str, float], Dict[str, float]]:
        # dt = 900 seconds (15 minutes)
        new_temps = {}
        self.hvac_energy = {}
        
        # Adjacency matrix for simple layout: Zone 1 connected to Zone 2 and Zone 3. Zone 2 and Zone 3 not directly adjacent.
        adjacencies = {
            "Zone 1: Open Office": ["Zone 2: Meeting Room", "Zone 3: Executive Suite"],
            "Zone 2: Meeting Room": ["Zone 1: Open Office"],
            "Zone 3: Executive Suite": ["Zone 1: Open Office"]
        }
        
        for z in self.zones:
            t_curr = self.temperatures[z]
            
            # 1. Thermal exchange with outdoors
            q_out = (outdoor_temp - t_curr) / self.R_out[z]
            
            # 2. Thermal exchange with adjacent zones
            q_adj = 0.0
            for adj in adjacencies[z]:
                q_adj += (self.temperatures[adj] - t_curr) / self.R_int
                
            # 3. Internal and Solar Gains
            q_internal = self.get_internal_gains(z, occupancy[z], hour)
            q_solar = self.get_solar_gain(z, hour, outdoor_temp)
            
            # 4. HVAC Control (immediate steady-state response)
            q_hvac = 0.0
            hvac_elec_w = 0.0
            
            # If temp is higher than cooling setpoint, cool down
            if t_curr > cooling_setpoints[z]:
                # We need cooling (extract heat, negative q_hvac)
                needed_cooling = (t_curr - cooling_setpoints[z]) * self.C[z] / dt + q_out + q_adj + q_internal + q_solar
                if needed_cooling > 0:
                    q_hvac = -min(needed_cooling, self.max_hvac_power)
                    hvac_elec_w = abs(q_hvac) / self.cop
            # If temp is lower than heating setpoint, heat up
            elif t_curr < heating_setpoints[z]:
                # We need heating (add heat, positive q_hvac)
                needed_heating = (heating_setpoints[z] - t_curr) * self.C[z] / dt - (q_out + q_adj + q_internal + q_solar)
                if needed_heating > 0:
                    q_hvac = min(needed_heating, self.max_hvac_power)
                    hvac_elec_w = abs(q_hvac) / self.cop
            
            # Update temperature using thermodynamic differential equation
            net_heat = q_out + q_adj + q_internal + q_solar + q_hvac
            t_next = t_curr + (net_heat / self.C[z]) * dt
            
            new_temps[z] = float(t_next)
            # Energy in kWh: Power (W) * time (hr) / 1000
            self.hvac_energy[z] = (hvac_elec_w * (dt / 3600.0)) / 1000.0
            
        self.temperatures = new_temps
        return self.temperatures, self.hvac_energy
