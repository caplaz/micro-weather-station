"""Test configuration for Micro Weather Station."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.micro_weather.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "outdoor_temp_sensor": "sensor.outdoor_temperature",
            "humidity_sensor": "sensor.humidity",
            "update_interval": 30,
        },
        options={},
        entry_id="test_entry_id",
        title="Micro Weather Station Test",
    )


@pytest.fixture
def mock_sensor_data():
    """Mock sensor data for testing."""
    return {
        "outdoor_temp": 72.0,  # Fahrenheit
        "indoor_temp": 70.0,
        "humidity": 65.0,
        "pressure": 29.92,  # inHg
        "wind_speed": 5.5,  # mph
        "wind_direction": 180.0,
        "wind_gust": 8.0,
        "rain_rate": 0.0,
        "rain_state": "Dry",
        "solar_radiation": 250.0,  # W/m²
        "solar_lux": 25000.0,
        "uv_index": 3.0,
    }
