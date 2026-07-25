class RuleBasedController:
    def __init__(self):
        # Normal active occupancy schedules (8:00 to 18:00)
        self.occupied_cooling_setpoint = 22.0
        self.occupied_heating_setpoint = 20.0
        
        # Unoccupied/overnight schedules
        self.unoccupied_cooling_setpoint = 28.0
        self.unoccupied_heating_setpoint = 15.0

    def get_setpoints(self, zone, hour):
        # If it is during typical office working hours, use standard comfort setpoints
        if 8 <= hour <= 18:
            return self.occupied_cooling_setpoint, self.occupied_heating_setpoint
        else:
            return self.unoccupied_cooling_setpoint, self.unoccupied_heating_setpoint
