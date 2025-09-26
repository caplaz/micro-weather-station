"""Test the configuration flow."""

from unittest.mock import MagicMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.micro_weather.config_flow import (
    ConfigFlowHandler,
    OptionsFlowHandler,
)


class TestConfigFlow:
    """Test the config flow."""

    async def test_form(self, hass: HomeAssistant):
        """Test we get the form."""
        # Create flow directly instead of using async_init
        flow = ConfigFlowHandler()
        flow.hass = hass

        result = await flow.async_step_user()
        assert result["type"] == "form"
        assert result["errors"] == {}

    async def test_form_missing_required_sensor(self, hass: HomeAssistant):
        """Test form with missing required outdoor temp sensor."""
        # Create flow directly
        flow = ConfigFlowHandler()
        flow.hass = hass

        result = await flow.async_step_user(
            {
                # Missing outdoor_temp_sensor
                "update_interval": 30,
            }
        )
        assert result["type"] == "form"
        assert result["errors"] == {"base": "missing_outdoor_temp"}

    async def test_form_success(self, hass: HomeAssistant):
        """Test successful form submission."""
        # Create flow directly
        flow = ConfigFlowHandler()
        flow.hass = hass

        with patch(
            "custom_components.micro_weather.async_setup_entry",
            return_value=True,
        ):
            result = await flow.async_step_user(
                {
                    "outdoor_temp_sensor": "sensor.outdoor_temperature",
                    "humidity_sensor": "sensor.humidity",
                    "update_interval": 30,
                }
            )
            await hass.async_block_till_done()

        assert result["type"] == "create_entry"
        assert result["title"] == "Micro Weather Station"


class TestOptionsFlow:
    """Test the options flow."""

    async def test_options_flow_init(self, hass: HomeAssistant):
        """Test options flow initialization with some sensors configured."""
        # Create a mock config entry with some sensors configured
        config_entry = MagicMock(spec=config_entries.ConfigEntry)
        config_entry.options = {
            "outdoor_temp_sensor": "sensor.outdoor_temperature",
            "humidity_sensor": "sensor.humidity",
            "pressure_sensor": None,  # Not configured
            "sun_sensor": None,  # Not configured
            "update_interval": 30,
        }

        # Create options flow
        flow = OptionsFlowHandler(config_entry)
        flow.hass = hass

        result = await flow.async_step_init()
        assert result["type"] == "form"
        assert result["errors"] == {}

    async def test_options_flow_with_none_values(self, hass: HomeAssistant):
        """Test options flow handles None values for unconfigured sensors."""
        # Create a mock config entry with some sensors set to None
        config_entry = MagicMock(spec=config_entries.ConfigEntry)
        config_entry.options = {
            "outdoor_temp_sensor": "sensor.outdoor_temperature",
            "humidity_sensor": None,
            "pressure_sensor": None,
            "wind_speed_sensor": None,
            "sun_sensor": None,
            "update_interval": 30,
        }

        # Create options flow
        flow = OptionsFlowHandler(config_entry)
        flow.hass = hass

        # Test that the form can be displayed without errors
        result = await flow.async_step_init()
        assert result["type"] == "form"
        assert result["errors"] == {}

        # Submit form with some fields modified
        result = await flow.async_step_init(
            {
                "outdoor_temp_sensor": "sensor.outdoor_temperature",
                "humidity_sensor": "sensor.humidity",  # Adding a sensor
                # pressure_sensor, wind_speed_sensor, sun_sensor not in user_input
                # so they should retain their None values from config_entry.options
                "update_interval": 30,
            }
        )

        assert result["type"] == "create_entry"
        assert result["data"]["humidity_sensor"] == "sensor.humidity"
        # Fields not in user_input should retain their original values
        assert result["data"]["pressure_sensor"] is None
        assert result["data"]["sun_sensor"] is None

    async def test_options_flow_add_sun_sensor(self, hass: HomeAssistant):
        """Test adding a sun sensor through options flow."""
        # Create a mock config entry with no sun sensor configured
        config_entry = MagicMock(spec=config_entries.ConfigEntry)
        config_entry.options = {
            "outdoor_temp_sensor": "sensor.outdoor_temperature",
            "sun_sensor": None,  # Initially not configured
            "update_interval": 30,
        }

        # Create options flow
        flow = OptionsFlowHandler(config_entry)
        flow.hass = hass

        # Submit form with sun sensor added
        result = await flow.async_step_init(
            {
                "outdoor_temp_sensor": "sensor.outdoor_temperature",
                "sun_sensor": "sun.sun",  # Adding sun sensor
                "update_interval": 30,
            }
        )

        assert result["type"] == "create_entry"
        assert result["data"]["sun_sensor"] == "sun.sun"

    async def test_options_flow_remove_sensor(self, hass: HomeAssistant):
        """Test removing a sensor by clearing the field."""
        # Create a mock config entry with a sensor configured
        config_entry = MagicMock(spec=config_entries.ConfigEntry)
        config_entry.options = {
            "outdoor_temp_sensor": "sensor.outdoor_temperature",
            "humidity_sensor": "sensor.humidity",  # Initially configured
            "sun_sensor": "sun.sun",  # Initially configured
            "update_interval": 30,
        }

        # Create options flow
        flow = OptionsFlowHandler(config_entry)
        flow.hass = hass

        # Submit form with humidity sensor removed (cleared)
        result = await flow.async_step_init(
            {
                "outdoor_temp_sensor": "sensor.outdoor_temperature",
                "humidity_sensor": "",  # Cleared field - should be removed
                "sun_sensor": "sun.sun",  # Keep sun sensor
                "update_interval": 30,
            }
        )

        assert result["type"] == "create_entry"
        assert (
            result["data"]["humidity_sensor"] is None
        )  # Should be set to None when cleared
        assert result["data"]["sun_sensor"] == "sun.sun"  # Should remain configured

    async def test_options_flow_missing_required_sensor(self, hass: HomeAssistant):
        """Test options flow validation when required sensor is missing."""
        # Create a mock config entry
        config_entry = MagicMock(spec=config_entries.ConfigEntry)
        config_entry.options = {
            "outdoor_temp_sensor": "sensor.outdoor_temperature",
            "update_interval": 30,
        }

        # Create options flow
        flow = OptionsFlowHandler(config_entry)
        flow.hass = hass

        # Submit form with missing required outdoor temp sensor
        result = await flow.async_step_init(
            {
                "outdoor_temp_sensor": "",  # Empty required field
                "update_interval": 30,
            }
        )

        assert result["type"] == "form"
        assert result["errors"] == {"base": "missing_outdoor_temp"}

    async def test_options_flow_schema_building_with_defaults(
        self, hass: HomeAssistant
    ):
        """Test that schema building properly sets defaults for configured sensors."""
        # Create a mock config entry with various sensor configurations
        config_entry = MagicMock(spec=config_entries.ConfigEntry)
        config_entry.options = {
            "outdoor_temp_sensor": "sensor.outdoor_temperature",
            "humidity_sensor": "sensor.humidity",  # Configured
            "pressure_sensor": None,  # Not configured
            "sun_sensor": "sun.sun",  # Configured
            "update_interval": 45,
        }

        # Create options flow
        flow = OptionsFlowHandler(config_entry)
        flow.hass = hass

        # Get the form (this exercises the schema building code)
        result = await flow.async_step_init()

        assert result["type"] == "form"
        assert result["errors"] == {}

        # The schema should be built with proper defaults
        # This tests lines 229-231 where current values are retrieved
