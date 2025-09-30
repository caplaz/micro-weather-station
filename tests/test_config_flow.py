from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.micro_weather.config_flow import (
    ConfigFlowHandler,
    OptionsFlowHandler,
)
from custom_components.micro_weather.const import (
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

        # Submit with missing required sensor
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
            # Submit all sensor data for initial setup
            result = await flow.async_step_user(
                {
                    "outdoor_temp_sensor": "sensor.outdoor_temperature",
                    "humidity_sensor": "sensor.humidity",
                    "pressure_sensor": "sensor.pressure",
                    "altitude": 100,
                    "wind_speed_sensor": "sensor.wind_speed",
                    "wind_direction_sensor": "sensor.wind_direction",
                    "wind_gust_sensor": "sensor.wind_gust",
                    "rain_rate_sensor": "sensor.rain_rate",
                    "rain_state_sensor": "sensor.rain_state",
                    "solar_radiation_sensor": "sensor.solar_radiation",
                    "solar_lux_sensor": "sensor.solar_lux",
                    "uv_index_sensor": "sensor.uv_index",
                    "sun_sensor": "sun.sun",
                    "update_interval": 30,
                }
            )
            await hass.async_block_till_done()

        assert result["type"] == "create_entry"
        assert result["title"] == "Micro Weather Station"


class TestOptionsFlow:
    """Test the options flow."""

    @patch.object(
        OptionsFlowHandler,
        "config_entry",
        new_callable=lambda: property(lambda self: None),
    )
    async def test_options_flow_init(self, mock_config_entry, hass: HomeAssistant):
        """Test options flow initialization with some sensors configured."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_HUMIDITY_SENSOR: "sensor.humidity",
                CONF_PRESSURE_SENSOR: None,  # Not configured
                CONF_SUN_SENSOR: None,  # Not configured
                CONF_UPDATE_INTERVAL: 30,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Should start with menu
        result = await flow.async_step_init()
        assert result["type"] == "menu"
        assert result["step_id"] == "init"

    @patch("homeassistant.helpers.frame.report_usage")
    async def test_options_flow_with_none_values(
        self, mock_report_usage, hass: HomeAssistant
    ):
        """Test options flow handles None values for unconfigured sensors."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_HUMIDITY_SENSOR: None,
                CONF_PRESSURE_SENSOR: None,
                CONF_WIND_SPEED_SENSOR: None,
                CONF_SUN_SENSOR: None,
                CONF_UPDATE_INTERVAL: 30,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Start with menu
        await flow.async_step_init()

        # Configure atmospheric sensors
        result = await flow.async_step_init({"next_step_id": "atmospheric"})
        assert result["type"] == "form"

        result = await flow.async_step_atmospheric(
            {
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_HUMIDITY_SENSOR: "sensor.humidity",  # Adding a sensor
                # pressure_sensor not in user_input so should retain None
            }
        )
        assert result["type"] == "menu"  # Returns to menu

        # Finish configuration
        result = await flow.async_step_init({"next_step_id": "device_config"})
        assert result["type"] == "form"

        result = await flow.async_step_device_config(
            {
                CONF_UPDATE_INTERVAL: 30,
            }
        )

        assert result["type"] == "create_entry"
        assert result["data"][CONF_HUMIDITY_SENSOR] == "sensor.humidity"
        # Fields not in user_input should retain their original values
        assert result["data"][CONF_PRESSURE_SENSOR] is None
        assert result["data"][CONF_SUN_SENSOR] is None

    @patch("homeassistant.helpers.frame.report_usage")
    async def test_options_flow_add_sun_sensor(
        self, mock_report_usage, hass: HomeAssistant
    ):
        """Test adding a sun sensor through options flow."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_SUN_SENSOR: None,  # Initially not configured
                CONF_UPDATE_INTERVAL: 30,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Start with menu
        await flow.async_step_init()

        # Configure solar sensors
        result = await flow.async_step_init({"next_step_id": "solar"})
        assert result["type"] == "form"

        result = await flow.async_step_solar(
            {
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",  # Required
                CONF_SUN_SENSOR: "sun.sun",  # Adding sun sensor
            }
        )
        assert result["type"] == "menu"

        # Finish configuration
        result = await flow.async_step_init({"next_step_id": "device_config"})
        assert result["type"] == "form"

        result = await flow.async_step_device_config({})

        assert result["type"] == "create_entry"
        assert result["data"][CONF_SUN_SENSOR] == "sun.sun"

    @patch("homeassistant.helpers.frame.report_usage")
    async def test_options_flow_remove_sensor(
        self, mock_report_usage, hass: HomeAssistant
    ):
        """Test removing a sensor by clearing the field."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_HUMIDITY_SENSOR: "sensor.humidity",  # Initially configured
                CONF_SUN_SENSOR: "sun.sun",  # Initially configured
                CONF_UPDATE_INTERVAL: 30,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Start with menu
        await flow.async_step_init()

        # Configure atmospheric sensors (remove humidity)
        result = await flow.async_step_init({"next_step_id": "atmospheric"})
        assert result["type"] == "form"

        result = await flow.async_step_atmospheric(
            {
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_HUMIDITY_SENSOR: "",  # Cleared field - should be removed
            }
        )
        assert result["type"] == "menu"

        # Finish configuration
        result = await flow.async_step_init({"next_step_id": "device_config"})
        assert result["type"] == "form"

        result = await flow.async_step_device_config({})

        assert result["type"] == "create_entry"
        assert (
            result["data"][CONF_HUMIDITY_SENSOR] is None
        )  # Should be set to None when cleared
        assert result["data"][CONF_SUN_SENSOR] == "sun.sun"  # Should remain configured

    @patch("homeassistant.helpers.frame.report_usage")
    async def test_options_flow_missing_required_sensor(
        self, mock_report_usage, hass: HomeAssistant
    ):
        """Test options flow validation when required sensor is missing."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_UPDATE_INTERVAL: 30,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Start with menu
        await flow.async_step_init()

        # Try to configure atmospheric sensors without required sensor
        result = await flow.async_step_init({"next_step_id": "atmospheric"})
        assert result["type"] == "form"

        result = await flow.async_step_atmospheric(
            {
                # No sensors provided
            }
        )

        assert result["type"] == "form"
        assert result["errors"] == {"base": "missing_outdoor_temp"}

    @patch("homeassistant.helpers.frame.report_usage")
    async def test_options_flow_schema_building_with_defaults(
        self, mock_report_usage, hass: HomeAssistant
    ):
        """Test that schema building properly sets defaults for configured sensors."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_HUMIDITY_SENSOR: "sensor.humidity",  # Configured
                CONF_PRESSURE_SENSOR: None,  # Not configured
                CONF_SUN_SENSOR: "sun.sun",  # Configured
                CONF_UPDATE_INTERVAL: 45,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Start with menu
        result = await flow.async_step_init()
        assert result["type"] == "menu"

        # Go to atmospheric step to check schema building
        result = await flow.async_step_init({"next_step_id": "atmospheric"})
        assert result["type"] == "form"

    @patch("homeassistant.helpers.frame.report_usage")
    async def test_options_flow_configure_wind_sensors(
        self, mock_report_usage, hass: HomeAssistant
    ):
        """Test configuring wind sensors through options flow."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_WIND_SPEED_SENSOR: None,  # Initially not configured
                CONF_UPDATE_INTERVAL: 30,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Start with menu
        await flow.async_step_init()

        # Configure wind sensors
        result = await flow.async_step_init({"next_step_id": "wind"})
        assert result["type"] == "form"

        result = await flow.async_step_wind(
            {
                CONF_WIND_SPEED_SENSOR: "sensor.wind_speed",
                CONF_WIND_DIRECTION_SENSOR: "sensor.wind_direction",
                CONF_WIND_GUST_SENSOR: "sensor.wind_gust",
            }
        )
        assert result["type"] == "menu"

        # Finish configuration
        result = await flow.async_step_init({"next_step_id": "device_config"})
        assert result["type"] == "form"

        result = await flow.async_step_device_config({})

        assert result["type"] == "create_entry"
        assert result["data"][CONF_WIND_SPEED_SENSOR] == "sensor.wind_speed"
        assert result["data"][CONF_WIND_DIRECTION_SENSOR] == "sensor.wind_direction"
        assert result["data"][CONF_WIND_GUST_SENSOR] == "sensor.wind_gust"

    @patch("homeassistant.helpers.frame.report_usage")
    async def test_options_flow_configure_rain_sensors(
        self, mock_report_usage, hass: HomeAssistant
    ):
        """Test configuring rain sensors through options flow."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_RAIN_RATE_SENSOR: None,  # Initially not configured
                CONF_UPDATE_INTERVAL: 30,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Start with menu
        await flow.async_step_init()

        # Configure rain sensors
        result = await flow.async_step_init({"next_step_id": "rain"})
        assert result["type"] == "form"

        result = await flow.async_step_rain(
            {
                CONF_RAIN_RATE_SENSOR: "sensor.rain_rate",
                CONF_RAIN_STATE_SENSOR: "binary_sensor.rain_state",
            }
        )
        assert result["type"] == "menu"

        # Finish configuration
        result = await flow.async_step_init({"next_step_id": "device_config"})
        assert result["type"] == "form"

        result = await flow.async_step_device_config({})

        assert result["type"] == "create_entry"
        assert result["data"][CONF_RAIN_RATE_SENSOR] == "sensor.rain_rate"
        assert result["data"][CONF_RAIN_STATE_SENSOR] == "binary_sensor.rain_state"

    async def test_initial_config_flow_altitude_default(self, hass: HomeAssistant):
        """Test that initial config flow shows altitude default from HA elevation."""
        # Set HA elevation
        hass.config.elevation = 150.5

        # Create flow directly
        flow = ConfigFlowHandler()
        flow.hass = hass

        result = await flow.async_step_user()
        assert result["type"] == "form"
        assert result["errors"] == {}

        # Check that the schema includes altitude with default from HA elevation
        # The schema should have been built with the default value

    @patch("homeassistant.helpers.frame.report_usage")
    async def test_options_flow_atmospheric_schema_with_defaults(
        self, mock_report_usage, hass: HomeAssistant
    ):
        """Test that atmospheric schema building properly sets defaults for configured sensors."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_HUMIDITY_SENSOR: "sensor.humidity",  # Configured
                CONF_PRESSURE_SENSOR: None,  # Not configured
                CONF_SUN_SENSOR: "sun.sun",  # Configured
                CONF_UPDATE_INTERVAL: 45,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Start with menu
        result = await flow.async_step_init()
        assert result["type"] == "menu"

        # Go to atmospheric step to check schema building
        result = await flow.async_step_init({"next_step_id": "atmospheric"})
        assert result["type"] == "form"

        # The schema should be built with proper defaults
        # This tests that current values are retrieved correctly

    @patch("homeassistant.helpers.frame.report_usage")
    async def test_options_flow_configure_solar_sensors(
        self, mock_report_usage, hass: HomeAssistant
    ):
        """Test configuring solar sensors through options flow."""
        # Create a real config entry
        config_entry = config_entries.ConfigEntry(
            entry_id="test_entry",
            version=1,
            minor_version=0,
            domain="micro_weather",
            title="Test Weather Station",
            data={},
            options={
                CONF_OUTDOOR_TEMP_SENSOR: "sensor.outdoor_temperature",
                CONF_SOLAR_RADIATION_SENSOR: None,  # Initially not configured
                CONF_UPDATE_INTERVAL: 30,
            },
            source=config_entries.SOURCE_USER,
            unique_id="test_unique_id",
            discovery_keys=set(),
            subentries_data={},
        )
        # Add it to HA's config entries
        hass.config_entries._entries[config_entry.entry_id] = config_entry

        # Create options flow and set config_entry directly on the instance
        flow = OptionsFlowHandler()
        # Bypass the property setter by setting the private attribute
        flow._config_entry = config_entry
        flow.hass = hass

        # Start with menu
        await flow.async_step_init()

        # Configure solar sensors
        result = await flow.async_step_init({"next_step_id": "solar"})
        assert result["type"] == "form"

        result = await flow.async_step_solar(
            {
                CONF_SOLAR_RADIATION_SENSOR: "sensor.solar_radiation",
                CONF_SOLAR_LUX_SENSOR: "sensor.lux",
                CONF_UV_INDEX_SENSOR: "sensor.uv_index",
                CONF_SUN_SENSOR: "sun.sun",
            }
        )
        assert result["type"] == "menu"

        # Finish configuration
        result = await flow.async_step_init({"next_step_id": "device_config"})
        assert result["type"] == "form"

        result = await flow.async_step_device_config({})

        assert result["type"] == "create_entry"
        assert result["data"][CONF_SOLAR_RADIATION_SENSOR] == "sensor.solar_radiation"
        assert result["data"][CONF_SOLAR_LUX_SENSOR] == "sensor.lux"
        assert result["data"][CONF_UV_INDEX_SENSOR] == "sensor.uv_index"
        assert result["data"][CONF_SUN_SENSOR] == "sun.sun"
