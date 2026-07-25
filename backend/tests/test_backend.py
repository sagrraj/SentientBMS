from backend.app.data_generator.weather import get_outdoor_temperature
from backend.app.data_generator.occupancy import get_zone_occupancy
from backend.app.data_generator.carbon import get_grid_carbon_intensity
from backend.app.baseline.rbc_controller import RuleBasedController
from backend.app.safety.safety_gate import SafetyGate
from backend.app.simulation.simulation_engine import SimulationEngine
from backend.app.optimizer.cost_function import normalize_weights, evaluate_objective

def test_data_generators():
    # Test weather temperature ranges
    for h in [0.0, 6.0, 12.0, 14.0, 18.0, 23.0]:
        temp = get_outdoor_temperature(h)
        assert 23.0 <= temp <= 37.0
        
    # Test occupancy spikes
    assert get_zone_occupancy("Zone 2: Meeting Room", 10.5) == 10
    assert get_zone_occupancy("Zone 2: Meeting Room", 14.5) == 12
    assert get_zone_occupancy("Zone 2: Meeting Room", 17.0) == 1
    assert get_zone_occupancy("Zone 2: Meeting Room", 22.0) == 0
    
    # Test carbon intensity spike
    assert get_grid_carbon_intensity(13.0) == 550.0
    assert get_grid_carbon_intensity(23.0) == 210.0

def test_rbc_setpoints():
    rbc = RuleBasedController()
    c, h = rbc.get_setpoints("Zone 1: Open Office", 10.0)
    assert c == 22.0
    assert h == 20.0
    
    c, h = rbc.get_setpoints("Zone 1: Open Office", 20.0)
    assert c == 28.0
    assert h == 15.0

def test_safety_gate():
    gate = SafetyGate()
    
    # Valid setpoints
    cooling = {"Zone 1: Open Office": 22.0}
    heating = {"Zone 1: Open Office": 20.0}
    prev_cooling = {"Zone 1: Open Office": 22.0}
    prev_heating = {"Zone 1: Open Office": 20.0}
    passed, violations = gate.validate(cooling, heating, prev_cooling, prev_heating)
    assert passed
    assert len(violations) == 0
    
    # Out of bounds
    cooling_bad = {"Zone 1: Open Office": 32.0} # Too warm
    passed, violations = gate.validate(cooling_bad, heating, prev_cooling, prev_heating)
    assert not passed
    assert len(violations) > 0
    
    # Deadband violation
    cooling_db = {"Zone 1: Open Office": 20.5}
    heating_db = {"Zone 1: Open Office": 20.0} # diff is 0.5 < 1.0
    passed, violations = gate.validate(cooling_db, heating_db, prev_cooling, prev_heating)
    assert not passed
    
    # Ramp rate violation (+4C)
    cooling_ramp = {"Zone 1: Open Office": 26.0} # 26 - 22 = 4 > 3
    passed, violations = gate.validate(cooling_ramp, heating, prev_cooling, prev_heating)
    assert not passed

def test_weight_normalization():
    w = {"energy": 1.0, "carbon": 1.0, "comfort": 1.0}
    normalized = normalize_weights(w)
    assert sum(normalized.values()) == 1.0
    assert normalized["energy"] == 0.333
    
    # Test evaluation
    eval_res = evaluate_objective(10.0, 300.0, 5.0, w)
    assert eval_res["score"] > 0
    assert eval_res["carbon_emissions_kg"] == 3.0

def test_simulation_engine():
    engine = SimulationEngine()
    engine.reset()
    
    # Verify baseline runs on reset
    assert len(engine.baseline_history) == 96
    
    # Advance one step
    res = engine.step_sentient()
    assert res["step"] == 0
    assert len(engine.sentient_history) == 1
    initial_violations = engine.safety_violations_count
    engine.inject_violation_flag = True
    res2 = engine.step_sentient()
    assert res2["step"] == 1
    assert res2["safety_passed"] == False
    assert res2["fallback_activated"] == True
    assert engine.safety_violations_count == initial_violations + 1

if __name__ == "__main__":
    print("Running backend tests...")
    test_data_generators()
    print("test_data_generators passed!")
    test_rbc_setpoints()
    print("test_rbc_setpoints passed!")
    test_safety_gate()
    print("test_safety_gate passed!")
    test_weight_normalization()
    print("test_weight_normalization passed!")
    test_simulation_engine()
    print("test_simulation_engine passed!")
    print("All tests passed successfully!")
