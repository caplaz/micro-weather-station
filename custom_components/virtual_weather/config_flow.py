"""Config flow for Virtual Weather Station integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_TEMPERATURE_RANGE,
    CONF_HUMIDITY_RANGE,
    CONF_PRESSURE_RANGE,
    CONF_WIND_SPEED_RANGE,
    CONF_UPDATE_INTERVAL,
    CONF_WEATHER_PATTERNS,
    DEFAULT_TEMPERATURE_RANGE,
    DEFAULT_HUMIDITY_RANGE,
    DEFAULT_PRESSURE_RANGE,
    DEFAULT_WIND_SPEED_RANGE,
    DEFAULT_UPDATE_INTERVAL,
    WEATHER_PATTERNS,
)

_LOGGER = logging.getLogger(__name__)


def _validate_range(value: str) -> tuple[float, float]:
    """Validate and parse temperature range."""
    try:
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError("Range must have exactly 2 values")
        min_val = float(parts[0].strip())
        max_val = float(parts[1].strip())
        if min_val >= max_val:
            raise ValueError("Minimum value must be less than maximum")
        return (min_val, max_val)
    except (ValueError, AttributeError) as err:
        raise ValueError(f"Invalid range format: {err}") from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Virtual Weather Station."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate ranges
                temp_range = _validate_range(user_input[CONF_TEMPERATURE_RANGE])
                humidity_range = _validate_range(user_input[CONF_HUMIDITY_RANGE])
                pressure_range = _validate_range(user_input[CONF_PRESSURE_RANGE])
                wind_speed_range = _validate_range(user_input[CONF_WIND_SPEED_RANGE])

                # Prepare options
                options = {
                    CONF_TEMPERATURE_RANGE: temp_range,
                    CONF_HUMIDITY_RANGE: humidity_range,
                    CONF_PRESSURE_RANGE: pressure_range,
                    CONF_WIND_SPEED_RANGE: wind_speed_range,
                    CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                    CONF_WEATHER_PATTERNS: user_input[CONF_WEATHER_PATTERNS],
                }

                return self.async_create_entry(
                    title="Virtual Weather Station",
                    data={},
                    options=options,
                )

            except ValueError as err:
                _LOGGER.error("Configuration validation error: %s", err)
                errors["base"] = "invalid_range"

        # Build schema with defaults
        data_schema = vol.Schema({
            vol.Required(
                CONF_TEMPERATURE_RANGE,
                default=f"{DEFAULT_TEMPERATURE_RANGE[0]}, {DEFAULT_TEMPERATURE_RANGE[1]}"
            ): str,
            vol.Required(
                CONF_HUMIDITY_RANGE,
                default=f"{DEFAULT_HUMIDITY_RANGE[0]}, {DEFAULT_HUMIDITY_RANGE[1]}"
            ): str,
            vol.Required(
                CONF_PRESSURE_RANGE,
                default=f"{DEFAULT_PRESSURE_RANGE[0]}, {DEFAULT_PRESSURE_RANGE[1]}"
            ): str,
            vol.Required(
                CONF_WIND_SPEED_RANGE,
                default=f"{DEFAULT_WIND_SPEED_RANGE[0]}, {DEFAULT_WIND_SPEED_RANGE[1]}"
            ): str,
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=DEFAULT_UPDATE_INTERVAL
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            vol.Required(
                CONF_WEATHER_PATTERNS,
                default=WEATHER_PATTERNS
            ): vol.All(vol.Ensure_list, [vol.In(WEATHER_PATTERNS)]),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @config_entries.HANDLERS.register(DOMAIN)
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Virtual Weather Station."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate ranges
                temp_range = _validate_range(user_input[CONF_TEMPERATURE_RANGE])
                humidity_range = _validate_range(user_input[CONF_HUMIDITY_RANGE])
                pressure_range = _validate_range(user_input[CONF_PRESSURE_RANGE])
                wind_speed_range = _validate_range(user_input[CONF_WIND_SPEED_RANGE])

                # Update options
                options = {
                    CONF_TEMPERATURE_RANGE: temp_range,
                    CONF_HUMIDITY_RANGE: humidity_range,
                    CONF_PRESSURE_RANGE: pressure_range,
                    CONF_WIND_SPEED_RANGE: wind_speed_range,
                    CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                    CONF_WEATHER_PATTERNS: user_input[CONF_WEATHER_PATTERNS],
                }

                return self.async_create_entry(title="", data=options)

            except ValueError as err:
                _LOGGER.error("Options validation error: %s", err)
                errors["base"] = "invalid_range"

        # Get current options
        current_options = self.config_entry.options
        
        data_schema = vol.Schema({
            vol.Required(
                CONF_TEMPERATURE_RANGE,
                default=f"{current_options.get(CONF_TEMPERATURE_RANGE, DEFAULT_TEMPERATURE_RANGE)[0]}, {current_options.get(CONF_TEMPERATURE_RANGE, DEFAULT_TEMPERATURE_RANGE)[1]}"
            ): str,
            vol.Required(
                CONF_HUMIDITY_RANGE,
                default=f"{current_options.get(CONF_HUMIDITY_RANGE, DEFAULT_HUMIDITY_RANGE)[0]}, {current_options.get(CONF_HUMIDITY_RANGE, DEFAULT_HUMIDITY_RANGE)[1]}"
            ): str,
            vol.Required(
                CONF_PRESSURE_RANGE,
                default=f"{current_options.get(CONF_PRESSURE_RANGE, DEFAULT_PRESSURE_RANGE)[0]}, {current_options.get(CONF_PRESSURE_RANGE, DEFAULT_PRESSURE_RANGE)[1]}"
            ): str,
            vol.Required(
                CONF_WIND_SPEED_RANGE,
                default=f"{current_options.get(CONF_WIND_SPEED_RANGE, DEFAULT_WIND_SPEED_RANGE)[0]}, {current_options.get(CONF_WIND_SPEED_RANGE, DEFAULT_WIND_SPEED_RANGE)[1]}"
            ): str,
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=current_options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            vol.Required(
                CONF_WEATHER_PATTERNS,
                default=current_options.get(CONF_WEATHER_PATTERNS, WEATHER_PATTERNS)
            ): vol.All(vol.Ensure_list, [vol.In(WEATHER_PATTERNS)]),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""