from safety.validator import SafetyValidator

def test_safety_validator():
    validator = SafetyValidator()
    
    # Test valid setpoints
    ok, msg = validator.validate_action(22.0, 20.0, 22.0, 20.0)
    print(f"Test Valid setpoints: OK={ok}, Msg={msg}")
    assert ok == True
    
    # Test out of bounds cooling (too cold)
    ok, msg = validator.validate_action(15.0, 14.0, 22.0, 20.0)
    print(f"Test Out of bounds (cooling=15): OK={ok}, Msg={msg}")
    assert ok == False
    
    # Test deadband violation
    ok, msg = validator.validate_action(21.0, 20.5, 22.0, 20.0)
    print(f"Test Deadband violation: OK={ok}, Msg={msg}")
    assert ok == False
    
    # Test ramp rate violation
    ok, msg = validator.validate_action(26.0, 20.0, 22.0, 20.0)
    print(f"Test Ramp rate violation (+4C change): OK={ok}, Msg={msg}")
    assert ok == False
    
    print("\nAll safety validation tests passed successfully!")

if __name__ == "__main__":
    test_safety_validator()
