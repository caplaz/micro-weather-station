"""Test the configuration flow."""

import pytest
from unittest.mock import patch, Mock
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.micro_weather.const import DOMAIN
from custom_components.micro_weather.config_flow import ConfigFlowHandler


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
        ) as mock_setup_entry:
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
