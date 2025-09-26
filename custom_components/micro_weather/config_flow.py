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
                    # Prepare options - filter out None and empty string values
                    options = {}

                    # Process all fields
                    all_fields = [
                        CONF_OUTDOOR_TEMP_SENSOR,
                        CONF_DEWPOINT_SENSOR,
                        CONF_HUMIDITY_SENSOR,
                        CONF_PRESSURE_SENSOR,
                        CONF_WIND_SPEED_SENSOR,
                        CONF_WIND_DIRECTION_SENSOR,
                        CONF_WIND_GUST_SENSOR,
                        CONF_RAIN_RATE_SENSOR,
                        CONF_RAIN_STATE_SENSOR,
                        CONF_SOLAR_RADIATION_SENSOR,
                        CONF_SOLAR_LUX_SENSOR,
                        CONF_UV_INDEX_SENSOR,
                        CONF_SUN_SENSOR,
                    ]

                    for field in all_fields:
                        value = user_input.get(field)
                        # Only store if value is not None and not empty string
                        if value:
                            options[field] = value

                    # Always store update interval
                    options[CONF_UPDATE_INTERVAL] = user_input.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    )

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
                        domain="sensor",
                        device_class=["pressure", "atmospheric_pressure"],
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
                    # Build new options dict from scratch
                    # Start with current options, then update based on user input
                    options = dict(self.config_entry.options)

                    # Process all sensor fields from user input
                    all_sensor_fields = [
                        CONF_OUTDOOR_TEMP_SENSOR,
                        CONF_DEWPOINT_SENSOR,
                        CONF_HUMIDITY_SENSOR,
                        CONF_PRESSURE_SENSOR,
                        CONF_WIND_SPEED_SENSOR,
                        CONF_WIND_DIRECTION_SENSOR,
                        CONF_WIND_GUST_SENSOR,
                        CONF_RAIN_RATE_SENSOR,
                        CONF_RAIN_STATE_SENSOR,
                        CONF_SOLAR_RADIATION_SENSOR,
                        CONF_SOLAR_LUX_SENSOR,
                        CONF_UV_INDEX_SENSOR,
                        CONF_SUN_SENSOR,
                    ]

                    # Handle optional sensor fields: set to None if not present
                    # in user_input
                    optional_sensor_fields = all_sensor_fields[1:]  # Skip outdoor temp
                    self._optional_entities(optional_sensor_fields, user_input)

                    for field in all_sensor_fields:
                        if field in user_input:
                            value = user_input[field]
                            # Set to None if empty/falsy, otherwise keep value
                            if value and value != "":
                                options[field] = value
                            else:
                                options[field] = None  # Set to None instead of removing

                    # Always update the interval
                    update_interval = user_input.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    )
                    options[CONF_UPDATE_INTERVAL] = update_interval

                    return self.async_create_entry(title="", data=options)

            except Exception as err:
                _LOGGER.error("Options validation error: %s", err)
                errors["base"] = "unknown"

        # Build schema with suggested values from current options
        current_options = self.config_entry.options

        schema_dict: dict[vol.Required | vol.Optional, Any] = {}

        # Required fields always have defaults
        schema_dict[
            vol.Required(
                CONF_OUTDOOR_TEMP_SENSOR,
                default=current_options.get(CONF_OUTDOOR_TEMP_SENSOR),
            )
        ] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
        )

        schema_dict[
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=current_options.get(
                    CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                ),
            )
        ] = vol.All(vol.Coerce(int), vol.Range(min=1, max=60))

        # Optional fields configuration
        optional_fields = [
            (
                CONF_DEWPOINT_SENSOR,
                selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
            ),
            (
                CONF_HUMIDITY_SENSOR,
                selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="humidity"
                    )
                ),
            ),
            (
                CONF_PRESSURE_SENSOR,
                selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class=["pressure", "atmospheric_pressure"],
                    )
                ),
            ),
            (
                CONF_WIND_SPEED_SENSOR,
                selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="wind_speed"
                    )
                ),
            ),
            (
                CONF_WIND_DIRECTION_SENSOR,
                selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            ),
            (
                CONF_WIND_GUST_SENSOR,
                selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            ),
            (
                CONF_RAIN_RATE_SENSOR,
                selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            ),
            (
                CONF_RAIN_STATE_SENSOR,
                selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
            ),
            (
                CONF_SOLAR_RADIATION_SENSOR,
                selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="irradiance"
                    )
                ),
            ),
            (
                CONF_SOLAR_LUX_SENSOR,
                selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="illuminance"
                    )
                ),
            ),
            (
                CONF_UV_INDEX_SENSOR,
                selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            ),
            (
                CONF_SUN_SENSOR,
                selector.EntitySelector(selector.EntitySelectorConfig(domain="sun")),
            ),
        ]

        # Build base schema with vol.UNDEFINED defaults for optional fields
        for field_name, field_selector in optional_fields:
            schema_dict[vol.Optional(field_name, default=vol.UNDEFINED)] = (
                field_selector
            )

        base_schema = vol.Schema(schema_dict)

        # Use add_suggested_values_to_schema to populate defaults from current options
        data_schema = self.add_suggested_values_to_schema(base_schema, current_options)

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )

    def _optional_entities(
        self, keys: list[str], user_input: dict[str, Any] | None = None
    ) -> None:
        """Set value to None if key does not exist in user_input."""
        if user_input is None:
            return
        for key in keys:
            if key not in user_input:
                user_input[key] = None


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
