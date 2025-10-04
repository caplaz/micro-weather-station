"""Tests for the Micro Weather Station weather entity."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.weather import (
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
import pytest

from custom_components.micro_weather.const import DOMAIN
from custom_components.micro_weather.weather import (
    MicroWeatherEntity,
    async_setup_entry,
)


class TestMicroWeatherEntity:
    """Test the Micro Weather Station weather entity."""

    @pytest.fixture
    def config_entry(self):
        """Create a mock config entry."""
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test_entry_id"
        return entry

    @pytest.fixture
    def coordinator(self):
        """Create a mock coordinator."""
        coordinator = MagicMock()
        coordinator.data = None
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    @pytest.fixture
    def weather_entity(self, coordinator, config_entry):
        """Create a weather entity instance."""
        return MicroWeatherEntity(coordinator, config_entry)

    def test_init(self, weather_entity, config_entry):
        """Test entity initialization."""
        assert weather_entity._config_entry == config_entry
        expected_id = f"{config_entry.entry_id}_weather"
        assert weather_entity._attr_unique_id == expected_id
        assert weather_entity._attr_has_entity_name is True
        assert weather_entity._attr_name is None
        assert weather_entity._attr_supported_features == 3
        # FORECAST_DAILY | FORECAST_HOURLY
        assert weather_entity._attr_native_temperature_unit == UnitOfTemperature.CELSIUS
        assert weather_entity._attr_native_pressure_unit == UnitOfPressure.HPA
        assert (
            weather_entity._attr_native_wind_speed_unit
            == UnitOfSpeed.KILOMETERS_PER_HOUR
        )
        assert weather_entity._attr_native_visibility_unit == UnitOfLength.KILOMETERS

        # Check device info
        device_info = weather_entity._attr_device_info
        assert device_info["identifiers"] == {(DOMAIN, config_entry.entry_id)}
        assert device_info["name"] == "Micro Weather Station"
        assert device_info["manufacturer"] == "Micro Weather"
        assert device_info["model"] == "MWS-1"

    def test_available_no_data(self, weather_entity, coordinator):
        """Test availability when no data."""
        coordinator.data = None
        assert weather_entity.available is False

    def test_available_with_data(self, weather_entity, coordinator):
        """Test availability when data exists."""
        coordinator.data = {"temperature": 20}
        assert weather_entity.available is True

    async def test_async_added_to_hass_no_data(self, weather_entity, coordinator):
        """Test async_added_to_hass triggers refresh when no data."""
        coordinator.data = None
        await weather_entity.async_added_to_hass()
        coordinator.async_request_refresh.assert_called_once()

    async def test_async_added_to_hass_with_data(self, weather_entity, coordinator):
        """Test async_added_to_hass doesn't trigger refresh
        when data exists."""
        coordinator.data = {"temperature": 20}
        await weather_entity.async_added_to_hass()
        coordinator.async_request_refresh.assert_not_called()

    def test_condition_no_data(self, weather_entity, coordinator):
        """Test condition property when no data."""
        coordinator.data = None
        assert weather_entity.condition is None

    def test_condition_with_data(self, weather_entity, coordinator):
        """Test condition property with data."""
        coordinator.data = {"condition": ATTR_CONDITION_SUNNY}
        assert weather_entity.condition == ATTR_CONDITION_SUNNY

    def test_native_temperature_no_data(self, weather_entity, coordinator):
        """Test temperature property when no data."""
        coordinator.data = None
        assert weather_entity.native_temperature is None

    def test_native_temperature_with_data(self, weather_entity, coordinator):
        """Test temperature property with data."""
        coordinator.data = {"temperature": 25.5}
        assert weather_entity.native_temperature == 25.5

    def test_humidity_no_data(self, weather_entity, coordinator):
        """Test humidity property when no data."""
        coordinator.data = None
        assert weather_entity.humidity is None

    def test_humidity_with_data(self, weather_entity, coordinator):
        """Test humidity property with data."""
        coordinator.data = {"humidity": 65}
        assert weather_entity.humidity == 65

    def test_native_pressure_no_data(self, weather_entity, coordinator):
        """Test pressure property when no data."""
        coordinator.data = None
        assert weather_entity.native_pressure is None

    def test_native_pressure_with_data(self, weather_entity, coordinator):
        """Test pressure property with data."""
        coordinator.data = {"pressure": 1013.25}
        assert weather_entity.native_pressure == 1013.25

    def test_native_wind_speed_no_data(self, weather_entity, coordinator):
        """Test wind speed property when no data."""
        coordinator.data = None
        assert weather_entity.native_wind_speed is None

    def test_native_wind_speed_with_data(self, weather_entity, coordinator):
        """Test wind speed property with data."""
        coordinator.data = {"wind_speed": 15.5}
        assert weather_entity.native_wind_speed == 15.5

    def test_wind_bearing_no_data(self, weather_entity, coordinator):
        """Test wind bearing property when no data."""
        coordinator.data = None
        assert weather_entity.wind_bearing is None

    def test_wind_bearing_with_data(self, weather_entity, coordinator):
        """Test wind bearing property with data."""
        coordinator.data = {"wind_direction": 270}
        assert weather_entity.wind_bearing == 270

    def test_native_visibility_no_data(self, weather_entity, coordinator):
        """Test visibility property when no data."""
        coordinator.data = None
        assert weather_entity.native_visibility is None

    def test_native_visibility_with_data(self, weather_entity, coordinator):
        """Test visibility property with data."""
        coordinator.data = {"visibility": 10.5}
        assert weather_entity.native_visibility == 10.5

    def test_native_precipitation_no_data(self, weather_entity, coordinator):
        """Test precipitation property when no data."""
        coordinator.data = None
        assert weather_entity.native_precipitation is None

    def test_native_precipitation_with_data(self, weather_entity, coordinator):
        """Test precipitation property with data."""
        coordinator.data = {"precipitation": 2.5}
        assert weather_entity.native_precipitation == 2.5

    def test_native_precipitation_unit_no_data(self, weather_entity, coordinator):
        """Test precipitation unit property when no data."""
        coordinator.data = None
        assert weather_entity.native_precipitation_unit is None

    def test_native_precipitation_unit_with_data(self, weather_entity, coordinator):
        """Test precipitation unit property with data."""
        coordinator.data = {"precipitation_unit": "mm/h"}
        assert weather_entity.native_precipitation_unit == "mm/h"

    def test_native_precipitation_unit_none_value(self, weather_entity, coordinator):
        """Test precipitation unit property when unit is None."""
        coordinator.data = {"precipitation_unit": None}
        assert weather_entity.native_precipitation_unit is None

    async def test_async_forecast_daily_no_data(self, weather_entity, coordinator):
        """Test daily forecast when no data."""
        coordinator.data = None
        result = await weather_entity.async_forecast_daily()
        assert result is None

    async def test_async_forecast_daily_no_forecast(self, weather_entity, coordinator):
        """Test daily forecast when no forecast data."""
        coordinator.data = {"temperature": 20}
        result = await weather_entity.async_forecast_daily()
        assert result is None

    async def test_async_forecast_daily_with_data(self, weather_entity, coordinator):
        """Test daily forecast with forecast data."""
        forecast_data = [
            {
                "datetime": "2025-10-04T00:00:00",
                "temperature": 22.0,
                "templow": 16.0,
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 10.0,
                "humidity": 60,
            },
            {
                "datetime": "2025-10-05T00:00:00",
                "temperature": 20.0,
                "templow": 14.0,
                "condition": ATTR_CONDITION_PARTLYCLOUDY,
                "precipitation": 1.5,
                "wind_speed": 12.0,
                "humidity": 65,
            },
        ]
        coordinator.data = {"forecast": forecast_data}

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 2

        # Check first forecast item
        forecast1 = result[0]
        assert isinstance(forecast1, dict)
        assert forecast1["datetime"] == "2025-10-04T00:00:00"
        assert forecast1["native_temperature"] == 22.0
        assert forecast1["native_templow"] == 16.0
        assert forecast1["condition"] == ATTR_CONDITION_SUNNY
        assert forecast1["native_precipitation"] == 0.0
        assert forecast1["native_wind_speed"] == 10.0
        assert forecast1["humidity"] == 60

        # Check second forecast item
        forecast2 = result[1]
        assert isinstance(forecast2, dict)
        assert forecast2["datetime"] == "2025-10-05T00:00:00"
        assert forecast2["native_temperature"] == 20.0
        assert forecast2["native_templow"] == 14.0
        assert forecast2["condition"] == ATTR_CONDITION_PARTLYCLOUDY
        assert forecast2["native_precipitation"] == 1.5
        assert forecast2["native_wind_speed"] == 12.0
        assert forecast2["humidity"] == 65

    async def test_async_forecast_hourly_no_data(self, weather_entity, coordinator):
        """Test hourly forecast when no data."""
        coordinator.data = None
        result = await weather_entity.async_forecast_hourly()
        assert result is None

    async def test_async_forecast_hourly_with_data(self, weather_entity, coordinator):
        """Test hourly forecast generation."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24  # 24 hours

        # Check that all items are Forecast objects
        for forecast in result:
            assert isinstance(forecast, dict)
            assert forecast["datetime"] is not None
            assert isinstance(forecast["native_temperature"], float)
            assert forecast["condition"] is not None
            assert isinstance(forecast["native_precipitation"], float)
            assert isinstance(forecast["native_wind_speed"], float)
            assert isinstance(forecast["humidity"], (int, float))

    async def test_async_forecast_hourly_with_rain(self, weather_entity, coordinator):
        """Test hourly forecast with rain condition."""
        coordinator.data = {
            "temperature": 18.0,
            "condition": ATTR_CONDITION_RAINY,
            "humidity": 80,
            "wind_speed": 8.0,
            "precipitation": 2.5,
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Check that precipitation is calculated for rainy conditions
        rainy_forecasts = [f for f in result if f["condition"] == ATTR_CONDITION_RAINY]
        assert len(rainy_forecasts) > 0

        for forecast in rainy_forecasts:
            assert forecast["native_precipitation"] > 0

    async def test_async_forecast_hourly_with_imperial_precipitation(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast with imperial precipitation units."""
        coordinator.data = {
            "temperature": 18.0,
            "condition": ATTR_CONDITION_LIGHTNING_RAINY,
            "humidity": 80,
            "wind_speed": 8.0,
            "precipitation": 0.1,  # 0.1 in/h
            "precipitation_unit": "in/h",
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Check that precipitation values are reasonable for imperial units
        lightning_forecasts = [
            f for f in result if f["condition"] == ATTR_CONDITION_LIGHTNING_RAINY
        ]
        if lightning_forecasts:
            # Should vary around the current precipitation rate (0.1 in/h)
            precip = lightning_forecasts[0]["native_precipitation"]
            assert 0.05 <= precip <= 0.2
            # Should be close to 0.1 in/h with variation


class TestAsyncSetupEntry:
    """Test the async_setup_entry function."""

    @pytest.fixture
    def hass(self):
        """Create a mock Home Assistant instance."""
        return MagicMock(spec=HomeAssistant)

    @pytest.fixture
    def config_entry(self):
        """Create a mock config entry."""
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test_entry_id"
        return entry

    @pytest.fixture
    def async_add_entities(self):
        """Create a mock async_add_entities callback."""
        return MagicMock()

    async def test_async_setup_entry(self, hass, config_entry, async_add_entities):
        """Test async_setup_entry function."""
        # Mock the coordinator in hass.data
        coordinator = MagicMock()
        hass.data = {DOMAIN: {config_entry.entry_id: coordinator}}

        await async_setup_entry(hass, config_entry, async_add_entities)

        # Check that async_add_entities was called with a MicroWeatherEntity
        async_add_entities.assert_called_once()
        args = async_add_entities.call_args[0][0]
        assert len(args) == 1
        assert isinstance(args[0], MicroWeatherEntity)
        assert args[0]._config_entry == config_entry
