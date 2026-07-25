def get_grid_carbon_intensity(hour: float) -> float:
    """
    Returns grid carbon intensity in g CO2/kWh.
    Under normal conditions: 200-350 g CO2/kWh.
    Under stress conditions (12:00 - 15:00): spikes up to 550 g CO2/kWh.
    """
    # Baseline carbon intensity profile (diurnal pattern)
    # Lower at night/morning (wind/solar), higher during peak hours.
    if 12.0 <= hour < 15.0:
        # High stress carbon spike
        return 550.0
    elif 15.0 <= hour < 18.0:
        return 450.0
    elif 18.0 <= hour < 22.0:
        return 380.0
    elif 6.0 <= hour < 12.0:
        return 280.0
    else:
        # Clean grid hours
        return 210.0
