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
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlowHandler(ConfigFlow):
    """Handle a config flow for Micro Weather Station."""

    VERSION = 1

    def __init__(self, *args, **kwargs):
        """Initialize the config flow."""
        super().__init__(*args, **kwargs)
        self._user_input: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - show configuration menu."""
        if user_input is not None:
            if user_input.get("next_step") == "basic":
                return await self.async_step_basic()
            elif user_input.get("next_step") == "wind":
                return await self.async_step_wind()
            elif user_input.get("next_step") == "rain":
                return await self.async_step_rain()
            elif user_input.get("next_step") == "solar":
                return await self.async_step_solar()

        # Check if we have minimum required data
        has_basic = bool(self._user_input.get(CONF_OUTDOOR_TEMP_SENSOR))

        # Build step labels with checkmarks
        basic_check = "✅ " if has_basic else ""
        basic_label = f"{basic_check}Basic Setup (Temperature, Humidity, Pressure)"

        wind_check = "✅ " if self._user_input.get(CONF_WIND_SPEED_SENSOR) else ""
        wind_label = f"{wind_check}Wind Sensors"

        rain_check = (
            "✅ "
            if (
                self._user_input.get(CONF_RAIN_RATE_SENSOR)
                or self._user_input.get(CONF_RAIN_STATE_SENSOR)
            )
            else ""
        )
        rain_label = f"{rain_check}Rain & Precipitation Sensors"

        solar_check = (
            "✅ "
            if (
                self._user_input.get(CONF_SOLAR_RADIATION_SENSOR)
                or self._user_input.get(CONF_SOLAR_LUX_SENSOR)
            )
            else ""
        )
        solar_label = f"{solar_check}Solar & Light Sensors"

        data_schema = vol.Schema(
            {
                vol.Required("next_step"): vol.In(
                    {
                        "basic": basic_label,
                        "wind": wind_label,
                        "rain": rain_label,
                        "solar": solar_label,
                    }
                )
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors={},
        )

    async def async_step_basic(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle basic sensors step."""
        errors: dict[str, str] = {}

        # Get default altitude from Home Assistant home location
        default_altitude = 0.0
        if hasattr(self.hass.config, "latitude") and hasattr(
            self.hass.config, "longitude"
        ):
            default_altitude = getattr(self.hass.config, "elevation", 0.0) or 0.0

        if user_input is not None:
            # Validate required fields
            if not user_input.get("outdoor_temp_sensor"):
                errors["base"] = "missing_outdoor_temp"
            else:
                # Map string keys from UI to CONF_* constants for internal storage
                mapped_input = {}
                key_mapping = {
                    "outdoor_temp_sensor": CONF_OUTDOOR_TEMP_SENSOR,
                    "dewpoint_sensor": CONF_DEWPOINT_SENSOR,
                    "humidity_sensor": CONF_HUMIDITY_SENSOR,
                    "pressure_sensor": CONF_PRESSURE_SENSOR,
                    "altitude": CONF_ALTITUDE,
                    "update_interval": CONF_UPDATE_INTERVAL,
                }
                for ui_key, conf_key in key_mapping.items():
                    if ui_key in user_input:
                        mapped_input[conf_key] = user_input[ui_key]

                self._user_input.update(mapped_input)
                return await self.async_step_solar()

        data_schema = vol.Schema(
            {
                vol.Required(
                    "outdoor_temp_sensor",
                    default=self._user_input.get(CONF_OUTDOOR_TEMP_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(
                    "dewpoint_sensor",
                    default=self._user_input.get(CONF_DEWPOINT_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(
                    "humidity_sensor",
                    default=self._user_input.get(CONF_HUMIDITY_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="humidity"
                    )
                ),
                vol.Optional(
                    "pressure_sensor",
                    default=self._user_input.get(CONF_PRESSURE_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class=["pressure", "atmospheric_pressure"],
                    )
                ),
                vol.Optional(
                    "altitude",
                    default=self._user_input.get(CONF_ALTITUDE, default_altitude),
                ): vol.All(vol.Coerce(float), vol.Range(min=-500, max=10000)),
                vol.Required(
                    "update_interval",
                    default=self._user_input.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            }
        )

        return self.async_show_form(
            step_id="basic",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_wind(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle wind sensors step."""
        if user_input is not None:
            # Map string keys from UI to CONF_* constants for internal storage
            mapped_input = {}
            key_mapping = {
                "wind_speed_sensor": CONF_WIND_SPEED_SENSOR,
                "wind_direction_sensor": CONF_WIND_DIRECTION_SENSOR,
                "wind_gust_sensor": CONF_WIND_GUST_SENSOR,
            }
            for ui_key, conf_key in key_mapping.items():
                if ui_key in user_input:
                    mapped_input[conf_key] = user_input[ui_key]

            self._user_input.update(mapped_input)
            return await self.async_step_init()

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "wind_speed_sensor",
                    default=self._user_input.get(CONF_WIND_SPEED_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="wind_speed"
                    )
                ),
                vol.Optional(
                    "wind_direction_sensor",
                    default=self._user_input.get(
                        CONF_WIND_DIRECTION_SENSOR, vol.UNDEFINED
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    "wind_gust_sensor",
                    default=self._user_input.get(CONF_WIND_GUST_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            }
        )

        return self.async_show_form(
            step_id="wind",
            data_schema=data_schema,
        )

    async def async_step_rain(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle rain sensors step."""
        if user_input is not None:
            # Map string keys from UI to CONF_* constants for internal storage
            mapped_input = {}
            key_mapping = {
                "rain_rate_sensor": CONF_RAIN_RATE_SENSOR,
                "rain_state_sensor": CONF_RAIN_STATE_SENSOR,
            }
            for ui_key, conf_key in key_mapping.items():
                if ui_key in user_input:
                    mapped_input[conf_key] = user_input[ui_key]

            self._user_input.update(mapped_input)
            return await self.async_step_init()

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "rain_rate_sensor",
                    default=self._user_input.get(CONF_RAIN_RATE_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    "rain_state_sensor",
                    default=self._user_input.get(CONF_RAIN_STATE_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
            }
        )

        return self.async_show_form(
            step_id="rain",
            data_schema=data_schema,
        )

    async def async_step_solar(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle solar and light sensors step."""
        if user_input is not None:
            # Map string keys from UI to CONF_* constants for internal storage
            mapped_input = {}
            key_mapping = {
                "solar_radiation_sensor": CONF_SOLAR_RADIATION_SENSOR,
                "solar_lux_sensor": CONF_SOLAR_LUX_SENSOR,
                "uv_index_sensor": CONF_UV_INDEX_SENSOR,
                "sun_sensor": CONF_SUN_SENSOR,
            }
            for ui_key, conf_key in key_mapping.items():
                if ui_key in user_input:
                    mapped_input[conf_key] = user_input[ui_key]

            self._user_input.update(mapped_input)
            return await self._create_entry()

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "solar_radiation_sensor",
                    default=self._user_input.get(
                        CONF_SOLAR_RADIATION_SENSOR, vol.UNDEFINED
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="irradiance"
                    )
                ),
                vol.Optional(
                    "solar_lux_sensor",
                    default=self._user_input.get(CONF_SOLAR_LUX_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="illuminance"
                    )
                ),
                vol.Optional(
                    "uv_index_sensor",
                    default=self._user_input.get(CONF_UV_INDEX_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    "sun_sensor",
                    default=self._user_input.get(CONF_SUN_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sun")),
            }
        )

        return self.async_show_form(
            step_id="solar",
            data_schema=data_schema,
        )

    async def _create_entry(self) -> ConfigFlowResult:
        """Create the config entry."""
        # Prepare options - filter out None and empty string values
        options = {}

        # Process all fields
        all_fields = [
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

        for field in all_fields:
            value = self._user_input.get(field)
            # Only store if value is not None and not empty string
            if value:
                options[field] = value

        # Always store update interval
        options[CONF_UPDATE_INTERVAL] = self._user_input.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        return self.async_create_entry(
            title="Micro Weather Station",
            data={},
            options=options,
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
        self._user_input: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            if user_input["next_step_id"] == "basic":
                return await self.async_step_basic()
            elif user_input["next_step_id"] == "wind":
                return await self.async_step_wind()
            elif user_input["next_step_id"] == "rain":
                return await self.async_step_rain()
            elif user_input["next_step_id"] == "solar":
                return await self.async_step_solar()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("next_step_id"): vol.In(
                        {
                            "basic": "Basic Setup (Temperature, Humidity, Pressure)",
                            "wind": "Wind Sensors",
                            "rain": "Rain & Precipitation Sensors",
                            "solar": "Solar & Light Sensors",
                        }
                    )
                }
            ),
            errors={},
        )

    async def async_step_basic(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle basic sensors step."""
        if user_input is not None:
            # Map string keys from UI to CONF_* constants for internal storage
            mapped_input = {}
            key_mapping = {
                "outdoor_temp_sensor": CONF_OUTDOOR_TEMP_SENSOR,
                "dewpoint_sensor": CONF_DEWPOINT_SENSOR,
                "humidity_sensor": CONF_HUMIDITY_SENSOR,
                "pressure_sensor": CONF_PRESSURE_SENSOR,
                "altitude": CONF_ALTITUDE,
                "update_interval": CONF_UPDATE_INTERVAL,
            }
            for ui_key, conf_key in key_mapping.items():
                if ui_key in user_input:
                    mapped_input[conf_key] = user_input[ui_key]

            self._user_input.update(mapped_input)
            # For options flow, create entry directly after basic step
            return await self._create_options_entry()

        # Build schema with suggested values from current options
        current_options = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Required(
                    "outdoor_temp_sensor",
                    default=current_options.get(CONF_OUTDOOR_TEMP_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(
                    "dewpoint_sensor",
                    default=current_options.get(CONF_DEWPOINT_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(
                    "humidity_sensor",
                    default=current_options.get(CONF_HUMIDITY_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="humidity"
                    )
                ),
                vol.Optional(
                    "pressure_sensor",
                    default=current_options.get(CONF_PRESSURE_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        device_class=["pressure", "atmospheric_pressure"],
                    )
                ),
                vol.Optional(
                    "altitude",
                    default=current_options.get(CONF_ALTITUDE, vol.UNDEFINED),
                ): vol.All(vol.Coerce(float), vol.Range(min=-500, max=10000)),
                vol.Required(
                    "update_interval",
                    default=current_options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
            }
        )

        return self.async_show_form(
            step_id="basic",
            data_schema=data_schema,
        )

    async def async_step_wind(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle wind sensors step."""
        if user_input is not None:
            # Map string keys from UI to CONF_* constants for internal storage
            mapped_input = {}
            key_mapping = {
                "wind_speed_sensor": CONF_WIND_SPEED_SENSOR,
                "wind_direction_sensor": CONF_WIND_DIRECTION_SENSOR,
                "wind_gust_sensor": CONF_WIND_GUST_SENSOR,
            }
            for ui_key, conf_key in key_mapping.items():
                if ui_key in user_input:
                    mapped_input[conf_key] = user_input[ui_key]

            self._user_input.update(mapped_input)
            # For options flow, create entry directly after wind step
            return await self._create_options_entry()

        current_options = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "wind_speed_sensor",
                    default=current_options.get(CONF_WIND_SPEED_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="wind_speed"
                    )
                ),
                vol.Optional(
                    "wind_direction_sensor",
                    default=current_options.get(
                        CONF_WIND_DIRECTION_SENSOR, vol.UNDEFINED
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    "wind_gust_sensor",
                    default=current_options.get(CONF_WIND_GUST_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            }
        )

        return self.async_show_form(
            step_id="wind",
            data_schema=data_schema,
        )

    async def async_step_rain(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle rain sensors step."""
        if user_input is not None:
            # Map string keys from UI to CONF_* constants for internal storage
            mapped_input = {}
            key_mapping = {
                "rain_rate_sensor": CONF_RAIN_RATE_SENSOR,
                "rain_state_sensor": CONF_RAIN_STATE_SENSOR,
            }
            for ui_key, conf_key in key_mapping.items():
                if ui_key in user_input:
                    mapped_input[conf_key] = user_input[ui_key]

            self._user_input.update(mapped_input)
            # For options flow, create entry directly after rain step
            return await self._create_options_entry()

        current_options = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "rain_rate_sensor",
                    default=current_options.get(CONF_RAIN_RATE_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    "rain_state_sensor",
                    default=current_options.get(CONF_RAIN_STATE_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
            }
        )

        return self.async_show_form(
            step_id="rain",
            data_schema=data_schema,
        )

    async def async_step_solar(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle solar and light sensors step."""
        errors: dict[str, str] = {}
        current_options = self.config_entry.options

        if user_input is not None:
            # Map string keys from UI to CONF_* constants for internal storage
            mapped_input = {}
            key_mapping = {
                "solar_radiation_sensor": CONF_SOLAR_RADIATION_SENSOR,
                "solar_lux_sensor": CONF_SOLAR_LUX_SENSOR,
                "uv_index_sensor": CONF_UV_INDEX_SENSOR,
                "sun_sensor": CONF_SUN_SENSOR,
            }
            for ui_key, conf_key in key_mapping.items():
                if ui_key in user_input:
                    mapped_input[conf_key] = user_input[ui_key]

            self._user_input.update(mapped_input)

            try:
                # Validate at least outdoor temp sensor is provided
                outdoor_temp = self._user_input.get(
                    CONF_OUTDOOR_TEMP_SENSOR
                ) or self.config_entry.options.get(CONF_OUTDOOR_TEMP_SENSOR)
                if not outdoor_temp:
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

                    # Handle optional sensor fields: set to None if not present
                    # in user_input
                    optional_sensor_fields = all_sensor_fields[1:]  # Skip outdoor temp
                    for field in optional_sensor_fields:
                        if field not in self._user_input:
                            self._user_input[field] = None

                    for field in all_sensor_fields:
                        if field in self._user_input:
                            value = self._user_input[field]
                            # Set to None if empty/falsy, otherwise keep value
                            if value and value != "":
                                options[field] = value
                            else:
                                options[field] = None  # Set to None instead of removing

                    # Always update the interval
                    update_interval = self._user_input.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    )
                    options[CONF_UPDATE_INTERVAL] = update_interval

                    return self.async_create_entry(title="", data=options)

            except Exception as err:
                _LOGGER.error("Options validation error: %s", err)
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "solar_radiation_sensor",
                    default=current_options.get(
                        CONF_SOLAR_RADIATION_SENSOR, vol.UNDEFINED
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="irradiance"
                    )
                ),
                vol.Optional(
                    "solar_lux_sensor",
                    default=current_options.get(CONF_SOLAR_LUX_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="illuminance"
                    )
                ),
                vol.Optional(
                    "uv_index_sensor",
                    default=current_options.get(CONF_UV_INDEX_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    "sun_sensor",
                    default=current_options.get(CONF_SUN_SENSOR, vol.UNDEFINED),
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sun")),
            }
        )

        return self.async_show_form(
            step_id="solar",
            data_schema=data_schema,
            errors=errors,
        )

    async def _create_options_entry(self) -> ConfigFlowResult:
        """Create the options entry."""
        # Build new options dict from scratch
        # Start with current options, then update based on user input
        options = dict(self.config_entry.options)

        # Process all sensor fields from user input
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
            if field in self._user_input:
                value = self._user_input[field]
                # Set to None if empty/falsy, otherwise keep value
                if value and value != "":
                    options[field] = value
                else:
                    options[field] = None  # Set to None instead of removing

        # Always update the interval
        update_interval = self._user_input.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        options[CONF_UPDATE_INTERVAL] = update_interval

        return self.async_create_entry(title="", data=options)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
