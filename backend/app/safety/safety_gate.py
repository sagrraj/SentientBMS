from typing import Dict, Any, List, Tuple

class SafetyGate:
    def __init__(self):
        self.min_cooling = 18.0
        self.max_cooling = 30.0
        self.min_heating = 12.0
        self.max_heating = 22.0
        self.min_deadband = 1.0
        self.max_ramp_rate = 3.0  # °C change per step

    def validate(
        self,
        proposed_cooling: Dict[str, float],
        proposed_heating: Dict[str, float],
        previous_cooling: Dict[str, float],
        previous_heating: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Validates proposed HVAC cooling and heating setpoints against constraints.
        Returns (passed, list_of_violations).
        """
        violations = []
        
        for z in proposed_cooling.keys():
            pc = proposed_cooling[z]
            ph = proposed_heating[z]
            
            # 1. Bounds check
            if not (self.min_cooling <= pc <= self.max_cooling):
                violations.append(f"Zone '{z}': Cooling setpoint {pc}°C out of range [{self.min_cooling}, {self.max_cooling}]")
            if not (self.min_heating <= ph <= self.max_heating):
                violations.append(f"Zone '{z}': Heating setpoint {ph}°C out of range [{self.min_heating}, {self.max_heating}]")
                
            # 2. Deadband check (cooling setpoint must be higher than heating setpoint + deadband)
            if pc - ph < self.min_deadband:
                violations.append(f"Zone '{z}': Setpoint deadband {pc - ph}°C is below minimum requirement {self.min_deadband}°C")
                
            # 3. Ramp rate check
            if previous_cooling and z in previous_cooling:
                prev_c = previous_cooling[z]
                if abs(pc - prev_c) > self.max_ramp_rate:
                    violations.append(f"Zone '{z}': Cooling setpoint change of {abs(pc - prev_c):.1f}°C exceeds max ramp rate {self.max_ramp_rate}°C")
            if previous_heating and z in previous_heating:
                prev_h = previous_heating[z]
                if abs(ph - prev_h) > self.max_ramp_rate:
                    violations.append(f"Zone '{z}': Heating setpoint change of {abs(ph - prev_h):.1f}°C exceeds max ramp rate {self.max_ramp_rate}°C")
                    
        return len(violations) == 0, violations
