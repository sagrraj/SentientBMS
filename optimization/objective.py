class ObjectiveEvaluator:
    def __init__(self):
        self.weights = {
            "energy": 1.0,
            "carbon": 5.0,
            "comfort": 0.9
        }
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
        return {
            "cost": float(j_val),
            "energy_cost": float(self.weights["energy"] * energy_kwh),
            "carbon_cost": float(self.weights["carbon"] * carbon_emissions),
            "comfort_cost": float(self.weights["comfort"] * total_comfort_penalty),
            "carbon_emissions": float(carbon_emissions),
            "comfort_penalty": float(total_comfort_penalty)
        }
