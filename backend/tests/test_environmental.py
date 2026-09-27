"""Tests for the environmental context service."""
import pytest
from app.services.environmental import assess_environment, validate_sensor_values


def test_no_data_returns_zero_modifier():
    ctx = assess_environment(None, None)
    assert ctx.priority_modifier == 0.0
    assert "No environmental data" in ctx.note


def test_elevated_humidity_increases_modifier():
    ctx = assess_environment(25.0, 75.0)   # humidity above 70 threshold
    assert ctx.priority_modifier > 0.0
    assert "humidity" in ctx.note.lower()


def test_high_temp_increases_modifier():
    ctx = assess_environment(40.0, 50.0)   # temp above 35 threshold
    assert ctx.priority_modifier > 0.0


def test_normal_conditions_no_warning():
    ctx = assess_environment(22.0, 45.0)
    assert ctx.priority_modifier == 0.0


def test_both_elevated_higher_modifier():
    ctx_both = assess_environment(40.0, 80.0)
    ctx_one  = assess_environment(40.0, 50.0)
    assert ctx_both.priority_modifier > ctx_one.priority_modifier


def test_modifier_capped_at_ten():
    ctx = assess_environment(100.0, 100.0)   # extreme values
    assert ctx.priority_modifier <= 10.0


# ── Validation ─────────────────────────────────────────────────────────────

def test_valid_sensor_values_no_errors():
    assert validate_sensor_values(25.0, 60.0) == []


def test_invalid_temperature_returns_error():
    errors = validate_sensor_values(200.0, 50.0)
    assert len(errors) == 1
    assert "Temperature" in errors[0]


def test_invalid_humidity_returns_error():
    errors = validate_sensor_values(25.0, 110.0)
    assert len(errors) == 1
    assert "Humidity" in errors[0]


def test_both_invalid_returns_two_errors():
    errors = validate_sensor_values(-100.0, 150.0)
    assert len(errors) == 2


def test_none_values_are_valid():
    assert validate_sensor_values(None, None) == []


@pytest.mark.parametrize("temp, hum", [
    (-40.0, 0.0),
    (85.0, 100.0),
    (0.0, 50.0),
])
def test_boundary_values_are_valid(temp, hum):
    assert validate_sensor_values(temp, hum) == []
