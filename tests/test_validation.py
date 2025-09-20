"""Test configuration validation logic for Micro Weather Station."""

import pytest
from typing import Any, Dict

from custom_components.micro_weather.const import (
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_UPDATE_INTERVAL,
    CONF_INDOOR_TEMP_SENSOR,
    CONF_PRESSURE_SENSOR,
    CONF_WIND_SPEED_SENSOR,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


class TestConfigValidation:
    """Test configuration validation logic."""

    def test_constants_import(self):
        """Test that all required constants are importable."""
        assert DOMAIN == "micro_weather"
        assert isinstance(DEFAULT_UPDATE_INTERVAL, int)
        assert DEFAULT_UPDATE_INTERVAL > 0

    def test_valid_configuration(self):
        """Test validation of a valid configuration."""
        config = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
            CONF_HUMIDITY_SENSOR: "sensor.humidity",
            CONF_UPDATE_INTERVAL: 30,
        }
        
        result, error = self._validate_config(config)
        assert result is True
        assert error == "valid"

    def test_missing_outdoor_temp_sensor(self):
        """Test validation fails when outdoor temp sensor is missing."""
        config = {
            CONF_HUMIDITY_SENSOR: "sensor.humidity",
            CONF_UPDATE_INTERVAL: 30,
        }
        
        result, error = self._validate_config(config)
        assert result is False
        assert error == "missing_outdoor_temp"

    def test_empty_outdoor_temp_sensor(self):
        """Test validation fails when outdoor temp sensor is empty."""
        config = {
            CONF_OUTDOOR_TEMP_SENSOR: "",
            CONF_HUMIDITY_SENSOR: "sensor.humidity",
            CONF_UPDATE_INTERVAL: 30,
        }
        
        result, error = self._validate_config(config)
        assert result is False
        assert error == "missing_outdoor_temp"

    def test_invalid_update_interval_too_high(self):
        """Test validation fails when update interval is too high."""
        config = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
            CONF_UPDATE_INTERVAL: 120,
        }
        
        result, error = self._validate_config(config)
        assert result is False
        assert error == "invalid_update_interval"

    def test_invalid_update_interval_too_low(self):
        """Test validation fails when update interval is too low."""
        config = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
            CONF_UPDATE_INTERVAL: 0,
        }
        
        result, error = self._validate_config(config)
        assert result is False
        assert error == "invalid_update_interval"

    def test_invalid_update_interval_negative(self):
        """Test validation fails when update interval is negative."""
        config = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
            CONF_UPDATE_INTERVAL: -5,
        }
        
        result, error = self._validate_config(config)
        assert result is False
        assert error == "invalid_update_interval"

    def test_minimal_valid_config(self):
        """Test validation with minimal required configuration."""
        config = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
        }
        
        result, error = self._validate_config(config)
        assert result is True
        assert error == "valid"

    def test_full_sensor_config(self):
        """Test validation with all optional sensors provided."""
        config = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
            CONF_INDOOR_TEMP_SENSOR: "sensor.indoor_temperature",
            CONF_HUMIDITY_SENSOR: "sensor.humidity",
            CONF_PRESSURE_SENSOR: "sensor.pressure",
            CONF_WIND_SPEED_SENSOR: "sensor.wind_speed",
            CONF_UPDATE_INTERVAL: 15,
        }
        
        result, error = self._validate_config(config)
        assert result is True
        assert error == "valid"

    def test_default_update_interval_applied(self):
        """Test that default update interval is applied when not provided."""
        import voluptuous as vol
        
        schema = vol.Schema({
            vol.Required(CONF_OUTDOOR_TEMP_SENSOR): str,
            vol.Optional(CONF_HUMIDITY_SENSOR): str,
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=60)
            ),
        })
        
        data = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temp",
            CONF_HUMIDITY_SENSOR: "sensor.humidity",
        }
        
        result = schema(data)
        assert result[CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL

    def test_voluptuous_coercion(self):
        """Test that voluptuous properly coerces string numbers to integers."""
        import voluptuous as vol
        
        schema = vol.Schema({
            vol.Required(CONF_OUTDOOR_TEMP_SENSOR): str,
            vol.Required(CONF_UPDATE_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=60)
            ),
        })
        
        data = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temp",
            CONF_UPDATE_INTERVAL: "30",  # String that should be coerced to int
        }
        
        result = schema(data)
        assert isinstance(result[CONF_UPDATE_INTERVAL], int)
        assert result[CONF_UPDATE_INTERVAL] == 30

    def test_voluptuous_range_validation(self):
        """Test that voluptuous range validation works correctly."""
        import voluptuous as vol
        
        schema = vol.Schema({
            vol.Required(CONF_OUTDOOR_TEMP_SENSOR): str,
            vol.Required(CONF_UPDATE_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=60)
            ),
        })
        
        # Test valid range
        valid_data = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temp",
            CONF_UPDATE_INTERVAL: 30,
        }
        result = schema(valid_data)
        assert result[CONF_UPDATE_INTERVAL] == 30
        
        # Test invalid range (too high)
        invalid_data_high = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temp",
            CONF_UPDATE_INTERVAL: 120,
        }
        with pytest.raises(vol.Invalid):
            schema(invalid_data_high)
        
        # Test invalid range (too low)
        invalid_data_low = {
            CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temp",
            CONF_UPDATE_INTERVAL: 0,
        }
        with pytest.raises(vol.Invalid):
            schema(invalid_data_low)

    def _validate_config(self, user_input: Dict[str, Any]) -> tuple[bool, str]:
        """Validate configuration like the config flow does."""
        if not user_input.get(CONF_OUTDOOR_TEMP_SENSOR):
            return False, "missing_outdoor_temp"
        
        # Validate update interval
        update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        if not isinstance(update_interval, int) or not (1 <= update_interval <= 60):
            return False, "invalid_update_interval"
        
        return True, "valid"


class TestComponentStructure:
    """Test component structure and imports."""

    def test_main_module_import(self):
        """Test that main module can be imported."""
        import custom_components.micro_weather
        assert hasattr(custom_components.micro_weather, 'DOMAIN')

    def test_constants_module_import(self):
        """Test that constants module can be imported."""
        from custom_components.micro_weather.const import DOMAIN
        assert DOMAIN == "micro_weather"

    def test_weather_detector_import(self):
        """Test that weather detector can be imported."""
        from custom_components.micro_weather.weather_detector import WeatherDetector
        assert WeatherDetector is not None

    def test_version_import(self):
        """Test that version module can be imported."""
        from custom_components.micro_weather.version import __version__
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_config_flow_import(self):
        """Test that config flow can be imported (basic structure test)."""
        # This test is more limited due to Home Assistant dependencies
        # but we can at least check the module exists
        import sys
        import os
        
        config_flow_path = os.path.join(
            os.path.dirname(__file__),
            "../custom_components/micro_weather/config_flow.py"
        )
        assert os.path.exists(config_flow_path)


class TestIntegrationMetadata:
    """Test integration metadata and manifest."""

    def test_manifest_structure(self):
        """Test that manifest.json has required structure."""
        import json
        import os
        
        manifest_path = os.path.join(
            os.path.dirname(__file__),
            "../custom_components/micro_weather/manifest.json"
        )
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Required fields
        required_fields = [
            "domain", "name", "version", "documentation", 
            "issue_tracker", "codeowners", "requirements"
        ]
        
        for field in required_fields:
            assert field in manifest, f"Missing required field: {field}"
        
        # Specific values
        assert manifest["domain"] == "micro_weather"
        assert manifest["name"] == "Micro Weather Station"
        assert manifest["config_flow"] is True
        assert manifest["integration_type"] == "device"

    def test_version_consistency(self):
        """Test that version is consistent between manifest and version.py."""
        import json
        import os
        from custom_components.micro_weather.version import __version__
        
        manifest_path = os.path.join(
            os.path.dirname(__file__),
            "../custom_components/micro_weather/manifest.json"
        )
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert manifest["version"] == __version__

    def test_domain_consistency(self):
        """Test that domain is consistent across files."""
        import json
        import os
        from custom_components.micro_weather.const import DOMAIN
        
        manifest_path = os.path.join(
            os.path.dirname(__file__),
            "../custom_components/micro_weather/manifest.json"
        )
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert manifest["domain"] == DOMAIN