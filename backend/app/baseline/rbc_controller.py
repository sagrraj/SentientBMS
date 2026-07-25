class RuleBasedController:
    def __init__(self):
        # Normal active occupancy schedules (08:00 to 18:00)
        self.occupied_cooling_setpoint = 22.0
        self.occupied_heating_setpoint = 20.0
        
        # Unoccupied/overnight schedules (18:00 to 08:00)
        self.unoccupied_cooling_setpoint = 28.0
        self.unoccupied_heating_setpoint = 15.0

    def get_setpoints(self, zone: str, hour: float):
        """
        Determines setpoints based on static operating schedules.
        """
        if 8.0 <= hour < 18.0:
            return self.occupied_cooling_setpoint, self.occupied_heating_setpoint
        else:
            return self.unoccupied_cooling_setpoint, self.unoccupied_heating_setpoint
