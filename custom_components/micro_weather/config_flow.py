"""Config flow for Micro Weather Station integration."""

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    CONF_ALTITUDE,
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


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Micro Weather Station."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._data = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate at least outdoor temp sensor is provided
            if not user_input.get(CONF_OUTDOOR_TEMP_SENSOR):
                errors["base"] = "missing_outdoor_temp"
            else:
                return self.async_create_entry(
                    title="Micro Weather Station",
                    data={},
                    options=user_input,
                )

        # Build schema for initial setup - all sensors available
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
                vol.Optional(CONF_ALTITUDE): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=10000, step=1, unit_of_measurement="m"
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
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=60, step=1, unit_of_measurement="min"
                    )
                ),
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
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Micro Weather Station."""

    def __init__(self):
        """Initialize the options flow."""
        self._data = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial options step."""
        if user_input is not None:
            if user_input["next_step_id"] == "atmospheric":
                return await self.async_step_atmospheric()
            elif user_input["next_step_id"] == "wind":
                return await self.async_step_wind()
            elif user_input["next_step_id"] == "rain":
                return await self.async_step_rain()
            elif user_input["next_step_id"] == "solar":
                return await self.async_step_solar()
            elif user_input["next_step_id"] == "device_config":
                return await self.async_step_device_config()

        return self.async_show_menu(
            step_id="init",
            menu_options=["atmospheric", "wind", "rain", "solar", "device_config"],
            description_placeholders={
                "description": (
                    "Configure your Micro Weather Station by selecting sensor categories. "
                    "Start with atmospheric sensors (required) and optionally add wind, rain, "
                    "and solar sensors. When done, select 'Device Configuration'."
                ),
            },
        )

    async def async_step_atmospheric(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle atmospheric sensors configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate at least outdoor temp sensor is provided
            if not user_input.get(CONF_OUTDOOR_TEMP_SENSOR):
                errors["base"] = "missing_outdoor_temp"
            else:
                # Ensure optional fields are present in user_input
                self._optional_entities(
                    [
                        CONF_DEWPOINT_SENSOR,
                        CONF_HUMIDITY_SENSOR,
                        CONF_PRESSURE_SENSOR,
                        CONF_ALTITUDE,
                    ],
                    user_input,
                )

                # Store atmospheric sensor data
                self._data.update(user_input)

                # Save changes immediately
                options = dict(self.config_entry.options)
                for field in user_input:
                    value = user_input[field]
                    if value and value not in ("", "None"):
                        options[field] = value
                    else:
                        options[field] = None
                self.hass.config_entries.async_update_entry(
                    self.config_entry, options=options
                )

                return await self.async_step_init()

        # Get current options for defaults
        current_options = self.config_entry.options

        # Build atmospheric sensors schema
        schema_dict: dict[Any, Any] = {}

        # Outdoor temp is required and should have a value
        schema_dict[vol.Required(CONF_OUTDOOR_TEMP_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor", device_class="temperature"
                )
            )
        )

        # Optional sensors - always allow clearing
        schema_dict[vol.Optional(CONF_DEWPOINT_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor", device_class="temperature"
                )
            )
        )

        schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
            )
        )

        schema_dict[vol.Optional(CONF_PRESSURE_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class=["pressure", "atmospheric_pressure"],
                )
            )
        )

        schema_dict[vol.Optional(CONF_ALTITUDE, default=vol.UNDEFINED)] = (
            selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=10000, step=1, unit_of_measurement="m"
                )
            )
        )

        data_schema = self.add_suggested_values_to_schema(
            vol.Schema(schema_dict), current_options
        )

        return self.async_show_form(
            step_id="atmospheric",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_wind(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle wind sensors configuration."""
        if user_input is not None:
            # Ensure optional fields are present in user_input
            self._optional_entities(
                [
                    CONF_WIND_SPEED_SENSOR,
                    CONF_WIND_DIRECTION_SENSOR,
                    CONF_WIND_GUST_SENSOR,
                ],
                user_input,
            )

            # Store wind sensor data
            self._data.update(user_input)

            # Save changes immediately
            options = dict(self.config_entry.options)
            for field in user_input:
                value = user_input[field]
                if value and value not in ("", "None"):
                    options[field] = value
                else:
                    options[field] = None
            self.hass.config_entries.async_update_entry(
                self.config_entry, options=options
            )

            return await self.async_step_init()

        # Get current options for defaults
        current_options = self.config_entry.options

        # Build wind sensors schema
        schema_dict: dict[Any, Any] = {}

        schema_dict[vol.Optional(CONF_WIND_SPEED_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor", device_class="wind_speed"
                )
            )
        )

        schema_dict[vol.Optional(CONF_WIND_DIRECTION_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
        )

        schema_dict[vol.Optional(CONF_WIND_GUST_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
        )

        data_schema = self.add_suggested_values_to_schema(
            vol.Schema(schema_dict), current_options
        )

        return self.async_show_form(
            step_id="wind",
            data_schema=data_schema,
        )

    async def async_step_rain(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle rain sensors configuration."""
        if user_input is not None:
            # Ensure optional fields are present in user_input
            self._optional_entities(
                [
                    CONF_RAIN_RATE_SENSOR,
                    CONF_RAIN_STATE_SENSOR,
                ],
                user_input,
            )

            # Store rain sensor data
            self._data.update(user_input)

            # Save changes immediately
            options = dict(self.config_entry.options)
            for field in user_input:
                value = user_input[field]
                if value and value not in ("", "None"):
                    options[field] = value
                else:
                    options[field] = None
            self.hass.config_entries.async_update_entry(
                self.config_entry, options=options
            )

            return await self.async_step_init()

        # Get current options for defaults
        current_options = self.config_entry.options

        # Build rain sensors schema
        schema_dict: dict[Any, Any] = {}

        schema_dict[vol.Optional(CONF_RAIN_RATE_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
        )

        schema_dict[vol.Optional(CONF_RAIN_STATE_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            )
        )

        data_schema = self.add_suggested_values_to_schema(
            vol.Schema(schema_dict), current_options
        )

        return self.async_show_form(
            step_id="rain",
            data_schema=data_schema,
        )

    async def async_step_solar(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle solar/sun sensors configuration."""
        if user_input is not None:
            # Ensure optional fields are present in user_input
            self._optional_entities(
                [
                    CONF_SOLAR_RADIATION_SENSOR,
                    CONF_SOLAR_LUX_SENSOR,
                    CONF_UV_INDEX_SENSOR,
                    CONF_SUN_SENSOR,
                ],
                user_input,
            )

            # Store solar sensor data
            self._data.update(user_input)

            # Save changes immediately
            options = dict(self.config_entry.options)
            for field in user_input:
                value = user_input[field]
                if value and value not in ("", "None"):
                    options[field] = value
                else:
                    options[field] = None
            self.hass.config_entries.async_update_entry(
                self.config_entry, options=options
            )

            return await self.async_step_init()

        # Get current options for defaults
        current_options = self.config_entry.options

        # Build solar sensors schema
        schema_dict: dict[Any, Any] = {}

        schema_dict[
            vol.Optional(CONF_SOLAR_RADIATION_SENSOR, default=vol.UNDEFINED)
        ] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="irradiance")
        )

        schema_dict[vol.Optional(CONF_SOLAR_LUX_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor", device_class="illuminance"
                )
            )
        )

        schema_dict[vol.Optional(CONF_UV_INDEX_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
        )

        schema_dict[vol.Optional(CONF_SUN_SENSOR, default=vol.UNDEFINED)] = (
            selector.EntitySelector(selector.EntitySelectorConfig(domain="sun"))
        )

        data_schema = self.add_suggested_values_to_schema(
            vol.Schema(schema_dict), current_options
        )

        return self.async_show_form(
            step_id="solar",
            data_schema=data_schema,
        )

    async def async_step_device_config(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle final configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Store final data
                self._data.update(user_input)

                # Build new options dict from current options and accumulated data
                options = dict(self.config_entry.options)

                # Process all sensor fields from accumulated data
                all_sensor_fields = [
                    CONF_OUTDOOR_TEMP_SENSOR,
                    CONF_DEWPOINT_SENSOR,
                    CONF_HUMIDITY_SENSOR,
                    CONF_PRESSURE_SENSOR,
                    CONF_ALTITUDE,
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

                for field in all_sensor_fields:
                    if field in self._data:
                        value = self._data[field]
                        # Set to None if empty/falsy, otherwise keep value
                        if value and value not in ("", "None"):
                            options[field] = value
                        else:
                            options[field] = None

                # Always update the interval
                update_interval = self._data.get(
                    CONF_UPDATE_INTERVAL,
                    self.config_entry.options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                )
                options[CONF_UPDATE_INTERVAL] = update_interval

                return self.async_create_entry(title="", data=options)

            except Exception as err:
                _LOGGER.error("Options validation error: %s", err)
                errors["base"] = "unknown"

        # Get current options for defaults
        current_options = self.config_entry.options

        # Build final schema with update interval
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=current_options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=60, step=1, unit_of_measurement="min"
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="device_config",
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
