"""Test the configuration flow."""
import pytest
from unittest.mock import patch
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.micro_weather.const import DOMAIN
from custom_components.micro_weather.config_flow import ConfigFlow


class TestConfigFlow:
    """Test the config flow."""

    async def test_form(self, hass: HomeAssistant):
        """Test we get the form."""
        # Directly create and register the config flow
        flow = ConfigFlow()
        flow.hass = hass
        hass.config_entries.flow.async_register_handler(DOMAIN, ConfigFlow)
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == "form"
        assert result["errors"] == {}

    async def test_form_missing_required_sensor(self, hass: HomeAssistant):
        """Test form with missing required outdoor temp sensor."""
        # Directly create and register the config flow
        flow = ConfigFlow()
        flow.hass = hass
        hass.config_entries.flow.async_register_handler(DOMAIN, ConfigFlow)
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                # Missing outdoor_temp_sensor
                "update_interval": 30,
            },
        )
        assert result2["type"] == "form"
        assert result2["errors"] == {"base": "missing_outdoor_temp"}

    async def test_form_success(self, hass: HomeAssistant):
        """Test successful form submission."""
        # Directly create and register the config flow
        flow = ConfigFlow()
        flow.hass = hass
        hass.config_entries.flow.async_register_handler(DOMAIN, ConfigFlow)
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        with patch(
            "custom_components.micro_weather.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry:
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    "outdoor_temp_sensor": "sensor.outdoor_temperature",
                    "humidity_sensor": "sensor.humidity",
                    "update_interval": 30,
                },
            )
            await hass.async_block_till_done()

        assert result2["type"] == "create_entry"
        assert result2["title"] == "Micro Weather Station"
        assert len(mock_setup_entry.mock_calls) == 1