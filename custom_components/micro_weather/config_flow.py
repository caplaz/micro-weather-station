"""Config flow for Micro Weather Station integration."""

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    CONF_DEWPOINT_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_PRESSURE_SENSOR,
    CONF_RAIN_RATE_SENSOR,
    CONF_RAIN_STATE_SENSOR,
    CONF_SOLAR_LUX_SENSOR,
    CONF_SOLAR_RADIATION_SENSOR,
    CONF_SUN_SENSOR,
    CONF_UPDATE_INTERVAL,
    CONF_UV_INDEX_SENSOR,
    CONF_WIND_DIRECTION_SENSOR,
    CONF_WIND_GUST_SENSOR,
    CONF_WIND_SPEED_SENSOR,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Micro Weather Station."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate at least outdoor temp sensor is provided
                if not user_input.get(CONF_OUTDOOR_TEMP_SENSOR):
                    errors["base"] = "missing_outdoor_temp"
                else:
                    # Prepare options
                    options = {
                        CONF_OUTDOOR_TEMP_SENSOR: user_input.get(
                            CONF_OUTDOOR_TEMP_SENSOR
                        ),
                        CONF_DEWPOINT_SENSOR: user_input.get(CONF_DEWPOINT_SENSOR),
                        CONF_HUMIDITY_SENSOR: user_input.get(CONF_HUMIDITY_SENSOR),
                        CONF_PRESSURE_SENSOR: user_input.get(CONF_PRESSURE_SENSOR),
                        CONF_WIND_SPEED_SENSOR: user_input.get(CONF_WIND_SPEED_SENSOR),
                        CONF_WIND_DIRECTION_SENSOR: user_input.get(
                            CONF_WIND_DIRECTION_SENSOR
                        ),
                        CONF_WIND_GUST_SENSOR: user_input.get(CONF_WIND_GUST_SENSOR),
                        CONF_RAIN_RATE_SENSOR: user_input.get(CONF_RAIN_RATE_SENSOR),
                        CONF_RAIN_STATE_SENSOR: user_input.get(CONF_RAIN_STATE_SENSOR),
                        CONF_SOLAR_RADIATION_SENSOR: user_input.get(
                            CONF_SOLAR_RADIATION_SENSOR
                        ),
                        CONF_SOLAR_LUX_SENSOR: user_input.get(CONF_SOLAR_LUX_SENSOR),
                        CONF_UV_INDEX_SENSOR: user_input.get(CONF_UV_INDEX_SENSOR),
                        CONF_SUN_SENSOR: user_input.get(CONF_SUN_SENSOR),
                        CONF_UPDATE_INTERVAL: user_input.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    }

                    return self.async_create_entry(
                        title="Micro Weather Station",
                        data={},
                        options=options,
                    )

            except Exception as err:
                _LOGGER.error("Configuration validation error: %s", err)
                errors["base"] = "unknown"

        # Build schema with entity selectors
        data_schema = vol.Schema(
            {
                vol.Required(CONF_OUTDOOR_TEMP_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(CONF_DEWPOINT_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(CONF_HUMIDITY_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="humidity"
                    )
                ),
                vol.Optional(CONF_PRESSURE_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="pressure"
                    )
                ),
                vol.Optional(CONF_WIND_SPEED_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="wind_speed"
                    )
                ),
                vol.Optional(CONF_WIND_DIRECTION_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_WIND_GUST_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_RAIN_RATE_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_RAIN_STATE_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
                vol.Optional(CONF_SOLAR_RADIATION_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="irradiance"
                    )
                ),
                vol.Optional(CONF_SOLAR_LUX_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="illuminance"
                    )
                ),
                vol.Optional(CONF_UV_INDEX_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_SUN_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sun")
                ),
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Micro Weather Station."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate at least outdoor temp sensor is provided
                if not user_input.get(CONF_OUTDOOR_TEMP_SENSOR):
                    errors["base"] = "missing_outdoor_temp"
                else:
                    # Update options
                    options = {
                        CONF_OUTDOOR_TEMP_SENSOR: user_input.get(
                            CONF_OUTDOOR_TEMP_SENSOR
                        ),
                        CONF_DEWPOINT_SENSOR: user_input.get(CONF_DEWPOINT_SENSOR),
                        CONF_HUMIDITY_SENSOR: user_input.get(CONF_HUMIDITY_SENSOR),
                        CONF_PRESSURE_SENSOR: user_input.get(CONF_PRESSURE_SENSOR),
                        CONF_WIND_SPEED_SENSOR: user_input.get(CONF_WIND_SPEED_SENSOR),
                        CONF_WIND_DIRECTION_SENSOR: user_input.get(
                            CONF_WIND_DIRECTION_SENSOR
                        ),
                        CONF_WIND_GUST_SENSOR: user_input.get(CONF_WIND_GUST_SENSOR),
                        CONF_RAIN_RATE_SENSOR: user_input.get(CONF_RAIN_RATE_SENSOR),
                        CONF_RAIN_STATE_SENSOR: user_input.get(CONF_RAIN_STATE_SENSOR),
                        CONF_SOLAR_RADIATION_SENSOR: user_input.get(
                            CONF_SOLAR_RADIATION_SENSOR
                        ),
                        CONF_SOLAR_LUX_SENSOR: user_input.get(CONF_SOLAR_LUX_SENSOR),
                        CONF_UV_INDEX_SENSOR: user_input.get(CONF_UV_INDEX_SENSOR),
                        CONF_SUN_SENSOR: user_input.get(CONF_SUN_SENSOR),
                        CONF_UPDATE_INTERVAL: user_input.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    }

                    return self.async_create_entry(title="", data=options)

            except Exception as err:
                _LOGGER.error("Options validation error: %s", err)
                errors["base"] = "unknown"

        # Get current options
        current_options = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_OUTDOOR_TEMP_SENSOR,
                    default=current_options.get(CONF_OUTDOOR_TEMP_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(
                    CONF_DEWPOINT_SENSOR,
                    default=current_options.get(CONF_DEWPOINT_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(
                    CONF_HUMIDITY_SENSOR,
                    default=current_options.get(CONF_HUMIDITY_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="humidity"
                    )
                ),
                vol.Optional(
                    CONF_PRESSURE_SENSOR,
                    default=current_options.get(CONF_PRESSURE_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="pressure"
                    )
                ),
                vol.Optional(
                    CONF_WIND_SPEED_SENSOR,
                    default=current_options.get(CONF_WIND_SPEED_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="wind_speed"
                    )
                ),
                vol.Optional(
                    CONF_WIND_DIRECTION_SENSOR,
                    default=current_options.get(CONF_WIND_DIRECTION_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_WIND_GUST_SENSOR,
                    default=current_options.get(CONF_WIND_GUST_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_RAIN_RATE_SENSOR,
                    default=current_options.get(CONF_RAIN_RATE_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_RAIN_STATE_SENSOR,
                    default=current_options.get(CONF_RAIN_STATE_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
                vol.Optional(
                    CONF_SOLAR_RADIATION_SENSOR,
                    default=current_options.get(CONF_SOLAR_RADIATION_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="irradiance"
                    )
                ),
                vol.Optional(
                    CONF_SOLAR_LUX_SENSOR,
                    default=current_options.get(CONF_SOLAR_LUX_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="illuminance"
                    )
                ),
                vol.Optional(
                    CONF_UV_INDEX_SENSOR,
                    default=current_options.get(CONF_UV_INDEX_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_SUN_SENSOR,
                    default=current_options.get(CONF_SUN_SENSOR),
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sun")),
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=current_options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
