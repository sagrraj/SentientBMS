class SafetyValidator:
    def __init__(self):
        # Operational constraints
        self.min_cooling = 18.0
        self.max_cooling = 30.0
        self.min_heating = 12.0
        self.max_heating = 22.0
        self.min_deadband = 1.0
        self.max_ramp_rate = 3.0 # Max change in degrees C per step

    def validate_action(self, proposed_cooling, proposed_heating, current_cooling, current_heating):
        errors = []
        
        # 1. Bounds checking
        if not (self.min_cooling <= proposed_cooling <= self.max_cooling):
            errors.append(f"Cooling setpoint {proposed_cooling}°C out of bounds [{self.min_cooling}, {self.max_cooling}]")
            
        if not (self.min_heating <= proposed_heating <= self.max_heating):
            errors.append(f"Heating setpoint {proposed_heating}°C out of bounds [{self.min_heating}, {self.max_heating}]")
            
        # 2. Deadband check
        if proposed_cooling - proposed_heating < self.min_deadband:
            errors.append(f"Setpoint difference ({proposed_cooling - proposed_heating}°C) is below deadband limit ({self.min_deadband}°C)")
            
        # 3. Ramp rate check
        if current_cooling is not None:
            if abs(proposed_cooling - current_cooling) > self.max_ramp_rate:
                errors.append(f"Cooling setpoint ramp rate exceeds {self.max_ramp_rate}°C/step (diff: {abs(proposed_cooling - current_cooling)}°C)")
        if current_heating is not None:
            if abs(proposed_heating - current_heating) > self.max_ramp_rate:
                errors.append(f"Heating setpoint ramp rate exceeds {self.max_ramp_rate}°C/step (diff: {abs(proposed_heating - current_heating)}°C)")
                
        if errors:
            return False, "; ".join(errors)
        return True, "Action approved"
