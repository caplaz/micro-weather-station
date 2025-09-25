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

        # Test submitting the form with some fields still None
        result = await flow.async_step_init(
            {
                "outdoor_temp_sensor": "sensor.outdoor_temperature",
                "humidity_sensor": "sensor.humidity",  # Adding a sensor
                # Leaving pressure_sensor, wind_speed_sensor, sun_sensor as None
                "update_interval": 30,
            }
        )

        assert result["type"] == "create_entry"
        assert result["data"]["humidity_sensor"] == "sensor.humidity"
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
