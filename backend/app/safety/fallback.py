from typing import Dict, Tuple
from backend.app.baseline.rbc_controller import RuleBasedController

class FallbackController:
    def __init__(self):
        self.rbc = RuleBasedController()

    def get_fallback_setpoints(self, zones: list, hour: float) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Generates fallback setpoints using the trusted Rule-Based Controller (RBC).
        """
        cooling = {}
        heating = {}
        for z in zones:
            c_set, h_set = self.rbc.get_setpoints(z, hour)
            cooling[z] = c_set
            heating[z] = h_set
        return cooling, heating
