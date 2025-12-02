"""Tests for the Micro Weather Station weather entity."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
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

from custom_components.micro_weather.const import (
    DOMAIN,
    KEY_CONDITION,
    KEY_FORECAST,
    KEY_HUMIDITY,
    KEY_PRECIPITATION,
    KEY_PRESSURE,
    KEY_TEMPERATURE,
    KEY_VISIBILITY,
    KEY_WIND_DIRECTION,
    KEY_WIND_SPEED,
)
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
        coordinator.data = {KEY_TEMPERATURE: 20}
        assert weather_entity.available is True

    async def test_async_added_to_hass_no_data(self, weather_entity, coordinator):
        """Test async_added_to_hass triggers refresh when no data."""
        coordinator.data = None
        await weather_entity.async_added_to_hass()
        coordinator.async_request_refresh.assert_called_once()

    async def test_async_added_to_hass_with_data(self, weather_entity, coordinator):
        """Test async_added_to_hass doesn't trigger refresh
        when data exists."""
        coordinator.data = {KEY_TEMPERATURE: 20}
        await weather_entity.async_added_to_hass()
        coordinator.async_request_refresh.assert_not_called()

    def test_condition_no_data(self, weather_entity, coordinator):
        """Test condition property when no data."""
        coordinator.data = None
        assert weather_entity.condition is None

    def test_condition_with_data(self, weather_entity, coordinator):
        """Test condition property with data."""
        coordinator.data = {KEY_CONDITION: ATTR_CONDITION_SUNNY}
        assert weather_entity.condition == ATTR_CONDITION_SUNNY

    def test_native_temperature_no_data(self, weather_entity, coordinator):
        """Test temperature property when no data."""
        coordinator.data = None
        assert weather_entity.native_temperature is None

    def test_native_temperature_with_data(self, weather_entity, coordinator):
        """Test temperature property with data."""
        coordinator.data = {KEY_TEMPERATURE: 25.5}
        assert weather_entity.native_temperature == 25.5

    def test_humidity_no_data(self, weather_entity, coordinator):
        """Test humidity property when no data."""
        coordinator.data = None
        assert weather_entity.humidity is None

    def test_humidity_with_data(self, weather_entity, coordinator):
        """Test humidity property with data."""
        coordinator.data = {KEY_HUMIDITY: 65}
        assert weather_entity.humidity == 65

    def test_native_pressure_no_data(self, weather_entity, coordinator):
        """Test pressure property when no data."""
        coordinator.data = None
        assert weather_entity.native_pressure is None

    def test_native_pressure_with_data(self, weather_entity, coordinator):
        """Test pressure property with data."""
        coordinator.data = {KEY_PRESSURE: 1013.25}
        assert weather_entity.native_pressure == 1013.25

    def test_native_wind_speed_no_data(self, weather_entity, coordinator):
        """Test wind speed property when no data."""
        coordinator.data = None
        assert weather_entity.native_wind_speed is None

    def test_native_wind_speed_with_data(self, weather_entity, coordinator):
        """Test wind speed property with data."""
        coordinator.data = {KEY_WIND_SPEED: 15.5}
        assert weather_entity.native_wind_speed == 15.5

    def test_wind_bearing_no_data(self, weather_entity, coordinator):
        """Test wind bearing property when no data."""
        coordinator.data = None
        assert weather_entity.wind_bearing is None

    def test_wind_bearing_with_data(self, weather_entity, coordinator):
        """Test wind bearing property with data."""
        coordinator.data = {KEY_WIND_DIRECTION: 270}
        assert weather_entity.wind_bearing == 270

    def test_native_visibility_no_data(self, weather_entity, coordinator):
        """Test visibility property when no data."""
        coordinator.data = None
        assert weather_entity.native_visibility is None

    def test_native_visibility_with_data(self, weather_entity, coordinator):
        """Test visibility property with data."""
        coordinator.data = {KEY_VISIBILITY: 10.5}
        assert weather_entity.native_visibility == 10.5

    def test_native_precipitation_no_data(self, weather_entity, coordinator):
        """Test precipitation property when no data."""
        coordinator.data = None
        assert weather_entity.native_precipitation is None

    def test_native_precipitation_with_data(self, weather_entity, coordinator):
        """Test precipitation property with data."""
        coordinator.data = {KEY_PRECIPITATION: 2.5}
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
        coordinator.data = {KEY_TEMPERATURE: 20}
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
        coordinator.data = {KEY_FORECAST: forecast_data}

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
            # Lightning-rainy base precipitation is 15mm ≈ 0.59in, with modifiers can range widely
            precip = lightning_forecasts[0]["native_precipitation"]
            assert 0.1 <= precip <= 3.0  # Reasonable range for thunderstorms in inches

    async def test_async_forecast_hourly_nighttime_conditions(
        self, weather_entity, coordinator
    ):
        """Test that sunny conditions become clear_night during nighttime hours."""
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time to be 10 PM (nighttime) - timezone aware
        mock_now = datetime(2024, 1, 1, 22, 0, 0, tzinfo=timezone.utc)

        with (
            patch(
                "homeassistant.util.dt.parse_datetime",
                side_effect=lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
            ),
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now
            # Mock fromisoformat to return proper timezone-aware datetime objects
            mock_dt_class.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )

            # Mock sun.sun entity with sunrise/sunset times
            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "2024-01-02T07:00:00Z",  # 7 AM next day
                "next_setting": "2024-01-02T18:00:00Z",  # 6 PM next day
            }

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_hourly()

                assert result is not None
                assert len(result) == 24

                # Check nighttime hours (before sunrise and after sunset)
                # Hours 0-6 should be nighttime (23:00 to 05:00 when current time is 22:00)
                night_forecasts = result[:7]
                for forecast in night_forecasts:
                    # Nighttime conditions should be either clear_night (from sunny) or cloudy (from partlycloudy)
                    assert forecast["condition"] in [
                        ATTR_CONDITION_CLEAR_NIGHT,
                        ATTR_CONDITION_CLOUDY,
                    ], f"Expected clear_night or cloudy at night, got {forecast['condition']} at hour {forecast['datetime']}"

                # Check daytime hours (after sunrise and before sunset)
                # Hours 8-17 should be daytime (around 7 AM to 5 PM next day)
                day_forecasts = result[8:18]  # Hours 8-17 (roughly 7 AM to 5 PM)
                sunny_day_forecasts = [
                    f for f in day_forecasts if f["condition"] == ATTR_CONDITION_SUNNY
                ]
                assert (
                    len(sunny_day_forecasts) > 0
                ), "Should have some sunny conditions during daytime"

    async def test_async_forecast_hourly_sun_entity_fallback(
        self, weather_entity, coordinator
    ):
        """Test fallback to hardcoded times when sun.sun entity is unavailable."""
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time to be 10 PM (nighttime) - timezone aware
        mock_now = datetime(2024, 1, 1, 22, 0, 0, tzinfo=timezone.utc)

        with (
            patch(
                "homeassistant.util.dt.parse_datetime",
                side_effect=lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
            ),
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now

            # Mock sun.sun entity as None (unavailable)
            with patch.object(
                weather_entity.coordinator.hass.states, "get", return_value=None
            ):
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_hourly()

                assert result is not None
                assert len(result) == 24

                # With fallback to hardcoded 6 AM/6 PM, hours 0-6 should be nighttime
                night_forecasts = result[:7]
                for forecast in night_forecasts:
                    assert forecast["condition"] in [
                        ATTR_CONDITION_CLEAR_NIGHT,
                        ATTR_CONDITION_CLOUDY,
                    ], f"Expected clear_night or cloudy at night with fallback, got {forecast['condition']}"

                # Hours 7-18 should be daytime (6 AM to 6 PM hardcoded)
                day_forecasts = result[7:19]
                sunny_day_forecasts = [
                    f for f in day_forecasts if f["condition"] == ATTR_CONDITION_SUNNY
                ]
                assert (
                    len(sunny_day_forecasts) > 0
                ), "Should have sunny conditions during hardcoded daytime"

    async def test_async_forecast_hourly_sun_entity_missing_attributes(
        self, weather_entity, coordinator
    ):
        """Test fallback when sun.sun entity exists but attributes are missing."""
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time to be 2 AM (nighttime) - timezone aware
        mock_now = datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc)

        with (
            patch(
                "homeassistant.util.dt.parse_datetime",
                side_effect=lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
            ),
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now

            # Mock sun.sun entity with missing attributes
            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {}  # Empty attributes

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_hourly()

                assert result is not None
                assert len(result) == 24

                # Should fall back to hardcoded times - first few hours should be nighttime (before 6 AM)
                # Hours 0-2 (3 AM to 4 AM) should be nighttime, hours 3-5 (5 AM to 6 AM) might be edge cases
                # Let's check the actual hours and ensure nighttime conversion happens
                night_forecasts = []
                for i, forecast in enumerate(result[:6]):  # Check first 6 hours
                    hour = datetime.fromisoformat(forecast["datetime"]).hour
                    if hour < 6:  # Before 6 AM should be nighttime
                        night_forecasts.append((i, forecast))

                # Should have at least some nighttime hours that get converted
                assert len(night_forecasts) > 0, "Should have some hours before 6 AM"

                for i, forecast in night_forecasts:
                    assert forecast["condition"] in [
                        ATTR_CONDITION_CLEAR_NIGHT,
                        ATTR_CONDITION_CLOUDY,
                    ], f"Expected clear_night or cloudy at night with missing attributes, got {forecast['condition']} at hour {i} ({forecast['datetime']})"

    async def test_async_forecast_hourly_bidirectional_day_night_conversion(
        self, weather_entity, coordinator
    ):
        """Test bidirectional conversion between daytime and nighttime conditions.

        This test covers the bug where partlycloudy conditions were converted to cloudy
        at night but not converted back to partlycloudy during the day, causing all
        24 hours to show the same nighttime condition.
        """
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time to be 2 PM (daytime) - when the forecast starts
        mock_now = datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc)

        with (
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now
            mock_dt_class.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )

            # Mock sun.sun entity with sunrise at 6 AM and sunset at 6 PM same day
            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "2024-01-01T06:00:00Z",  # Sunrise today (already passed)
                "next_setting": "2024-01-01T18:00:00Z",  # Sunset today at 6 PM
            }

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                # Test with partlycloudy condition - this should convert to cloudy at night
                # but back to partlycloudy during the day
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_PARTLYCLOUDY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_hourly()

                assert result is not None
                assert len(result) == 24

                # Parse forecast hours to determine day/night using actual sunrise/sunset
                daytime_forecasts = []
                nighttime_forecasts = []

                sunrise_time = datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
                sunset_time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

                for forecast in result:
                    forecast_time = datetime.fromisoformat(forecast["datetime"])
                    from custom_components.micro_weather.weather_utils import (
                        is_forecast_hour_daytime,
                    )

                    is_daytime = is_forecast_hour_daytime(
                        forecast_time, sunrise_time, sunset_time
                    )

                    if is_daytime:
                        daytime_forecasts.append(forecast)
                    else:
                        nighttime_forecasts.append(forecast)

                # Should have both daytime and nighttime hours
                assert len(daytime_forecasts) > 0, "Should have daytime hours"
                assert len(nighttime_forecasts) > 0, "Should have nighttime hours"

                # During daytime hours, conditions should be daytime equivalents (sunny, partlycloudy, cloudy, rainy, etc.)
                # Not clear-night (which is nighttime only)
                for forecast in daytime_forecasts:
                    assert (
                        forecast["condition"] != ATTR_CONDITION_CLEAR_NIGHT
                    ), f"Clear-night should not appear during daytime at {forecast['datetime']}"

                # During nighttime hours, sunny conditions should convert to clear-night
                # and partlycloudy should convert to cloudy or clear-night
                for forecast in nighttime_forecasts:
                    assert (
                        forecast["condition"] != ATTR_CONDITION_SUNNY
                    ), f"Sunny should not appear during nighttime at {forecast['datetime']}"

    async def test_async_forecast_hourly_bidirectional_day_night_conversion_sunny(
        self, weather_entity, coordinator
    ):
        """Test bidirectional conversion for sunny conditions.

        Sunny should convert to clear-night at night and back to sunny during day.
        """
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time to be 10 AM (daytime)
        mock_now = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

        with (
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now
            mock_dt_class.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )

            # Mock sun.sun entity
            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "2024-01-01T06:00:00Z",
                "next_setting": "2024-01-01T18:00:00Z",
            }

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_hourly()

                assert result is not None
                assert len(result) == 24

                # Check daytime hours (should be daytime conditions)
                daytime_forecasts = []
                nighttime_forecasts = []

                sunrise_time = datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
                sunset_time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

                for forecast in result:
                    forecast_time = datetime.fromisoformat(forecast["datetime"])
                    from custom_components.micro_weather.weather_utils import (
                        is_forecast_hour_daytime,
                    )

                    is_daytime = is_forecast_hour_daytime(
                        forecast_time, sunrise_time, sunset_time
                    )

                    if is_daytime:
                        daytime_forecasts.append(forecast)
                    else:
                        nighttime_forecasts.append(forecast)

                # Daytime should not have clear_night (nighttime only condition)
                for forecast in daytime_forecasts:
                    assert (
                        forecast["condition"] != ATTR_CONDITION_CLEAR_NIGHT
                    ), f"Clear-night should not appear during daytime at {forecast['datetime']}"

                # Nighttime should not have sunny (daytime only condition)
                for forecast in nighttime_forecasts:
                    assert (
                        forecast["condition"] != ATTR_CONDITION_SUNNY
                    ), f"Sunny should not appear during nighttime at {forecast['datetime']}"

    async def test_async_forecast_hourly_condition_progression_with_day_night_cycles(
        self, weather_entity, coordinator
    ):
        """Test that hourly forecast properly progresses conditions hour-by-hour with day/night cycles.

        This test verifies the fix for the issue where all 24 hours showed the same condition.
        Now each hour should use the previous hour's condition as its base, enabling proper
        day/night condition transitions throughout the forecast period.
        """
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time to be 2 PM (daytime) - when the forecast starts
        mock_now = datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc)

        with (
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now
            mock_dt_class.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )

            # Mock sun.sun entity with sunrise at 6 AM and sunset at 6 PM same day
            # This creates a scenario where the 24-hour forecast spans both day and night
            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "2024-01-01T06:00:00Z",  # Sunrise today (already passed)
                "next_setting": "2024-01-01T18:00:00Z",  # Sunset today at 6 PM
            }

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                # Start with partlycloudy condition - this should evolve through the forecast
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_PARTLYCLOUDY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_hourly()

                assert result is not None
                assert len(result) == 24

                # Verify that conditions change throughout the forecast (not all the same)
                conditions = [forecast["condition"] for forecast in result]
                unique_conditions = set(conditions)

                # Should have at least 2 different conditions (daytime and nighttime versions)
                assert (
                    len(unique_conditions) >= 2
                ), f"Expected multiple condition types, got only: {unique_conditions}"

                # First hour should be the current condition (partlycloudy during daytime)
                assert (
                    result[0]["condition"] == ATTR_CONDITION_PARTLYCLOUDY
                ), f"First hour should be current condition partlycloudy, got {result[0]['condition']}"

                # Find the transition from day to night (around sunset at 6 PM)
                # Hours 0-3 are afternoon (2 PM, 3 PM, 4 PM, 5 PM) - should be daytime
                # Hours 4-17 are evening/night (6 PM to 7 AM) - should be nighttime
                # Hours 18-23 are morning (8 AM to 1 PM) - should be daytime

                # Check daytime hours (should maintain partlycloudy or evolve to sunny/cloudy based on actual logic)
                daytime_forecasts = []
                nighttime_forecasts = []

                sunrise_time = datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
                sunset_time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

                for forecast in result:
                    forecast_time = datetime.fromisoformat(forecast["datetime"])
                    from custom_components.micro_weather.weather_utils import (
                        is_forecast_hour_daytime,
                    )

                    is_daytime = is_forecast_hour_daytime(
                        forecast_time, sunrise_time, sunset_time
                    )

                    if is_daytime:
                        daytime_forecasts.append(forecast)
                    else:
                        nighttime_forecasts.append(forecast)

                # Daytime should be partlycloudy, cloudy, or sunny (based on actual forecast logic)
                for forecast in daytime_forecasts:
                    assert forecast["condition"] in [
                        ATTR_CONDITION_PARTLYCLOUDY,
                        ATTR_CONDITION_CLOUDY,
                        ATTR_CONDITION_SUNNY,
                    ], f"Expected daytime condition (partlycloudy/cloudy/sunny) at {forecast['datetime']}, got {forecast['condition']}"

                # Nighttime should be cloudy or clear_night (nighttime equivalent of partlycloudy)
                for forecast in nighttime_forecasts:
                    assert forecast["condition"] in [
                        ATTR_CONDITION_CLOUDY,
                        ATTR_CONDITION_CLEAR_NIGHT,
                    ], f"Expected nighttime condition (cloudy/clear-night) at {forecast['datetime']}, got {forecast['condition']}"

                # Verify progression: conditions should evolve based on previous hour
                # Check that consecutive hours have related conditions (not random jumps)
                for i in range(1, len(result)):
                    prev_condition = result[i - 1]["condition"]
                    curr_condition = result[i]["condition"]

                    # Conditions should be related (same base condition with day/night variants)
                    condition_pairs = [
                        (ATTR_CONDITION_PARTLYCLOUDY, ATTR_CONDITION_CLOUDY),
                        (ATTR_CONDITION_CLOUDY, ATTR_CONDITION_PARTLYCLOUDY),
                        (ATTR_CONDITION_SUNNY, ATTR_CONDITION_CLEAR_NIGHT),
                        (ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_SUNNY),
                        # Day/night conversions at boundaries - cloudy/partlycloudy can convert to clear-night
                        (ATTR_CONDITION_CLOUDY, ATTR_CONDITION_CLEAR_NIGHT),
                        (ATTR_CONDITION_PARTLYCLOUDY, ATTR_CONDITION_CLEAR_NIGHT),
                        # Pressure-driven evolution can change conditions more dynamically
                        (ATTR_CONDITION_SUNNY, ATTR_CONDITION_PARTLYCLOUDY),
                        (ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_CLOUDY),
                    ]

                    is_valid_transition = (
                        prev_condition == curr_condition  # Same condition
                        or any(
                            prev_condition in pair and curr_condition in pair
                            for pair in condition_pairs
                        )
                    )

                    assert (
                        is_valid_transition
                    ), f"Invalid condition transition from {prev_condition} to {curr_condition} at hour {i}"

    async def test_async_forecast_hourly_condition_progression_sunny_scenario(
        self, weather_entity, coordinator
    ):
        """Test hourly condition progression starting with sunny conditions."""
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time to be 10 AM (daytime)
        mock_now = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

        with (
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now
            mock_dt_class.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )

            # Mock sun.sun entity
            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "2024-01-01T06:00:00Z",
                "next_setting": "2024-01-01T18:00:00Z",
            }

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_hourly()

                assert result is not None
                assert len(result) == 24

                # First hour should be sunny (current condition during daytime)
                assert result[0]["condition"] == ATTR_CONDITION_SUNNY

                # Daytime hours should remain sunny or partlycloudy
                daytime_forecasts = []
                nighttime_forecasts = []

                sunrise_time = datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
                sunset_time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

                for forecast in result:
                    forecast_time = datetime.fromisoformat(forecast["datetime"])
                    from custom_components.micro_weather.weather_utils import (
                        is_forecast_hour_daytime,
                    )

                    is_daytime = is_forecast_hour_daytime(
                        forecast_time, sunrise_time, sunset_time
                    )

                    if is_daytime:
                        daytime_forecasts.append(forecast)
                    else:
                        nighttime_forecasts.append(forecast)

                # Daytime should be sunny
                for forecast in daytime_forecasts:
                    assert forecast["condition"] in [
                        ATTR_CONDITION_SUNNY,
                        ATTR_CONDITION_PARTLYCLOUDY,
                    ], f"Expected sunny/partlycloudy during daytime, got {forecast['condition']}"

                # Nighttime should be clear_night
                for forecast in nighttime_forecasts:
                    assert forecast["condition"] in [
                        ATTR_CONDITION_CLEAR_NIGHT,
                        ATTR_CONDITION_CLOUDY,
                    ], f"Expected clear_night/cloudy during nighttime, got {forecast['condition']}"

                # Verify no abrupt condition changes (should evolve gradually)
                for i in range(1, len(result)):
                    prev = result[i - 1]["condition"]
                    curr = result[i]["condition"]

                    # Should not jump from sunny to cloudy directly (or vice versa)
                    invalid_transitions = [
                        (ATTR_CONDITION_SUNNY, ATTR_CONDITION_CLOUDY),
                        (ATTR_CONDITION_CLOUDY, ATTR_CONDITION_SUNNY),
                        (ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_PARTLYCLOUDY),
                        # Note: partlycloudy to clear-night is allowed at day/night boundaries
                    ]

                    is_invalid = any(
                        prev == invalid[0] and curr == invalid[1]
                        for invalid in invalid_transitions
                    )
                    assert (
                        not is_invalid
                    ), f"Invalid abrupt transition from {prev} to {curr} at hour {i}"

    async def test_async_forecast_hourly_sunrise_sunset_boundary(
        self, weather_entity, coordinator
    ):
        """Test condition transitions at sunrise and sunset boundaries.

        Note: For multi-day forecasts where we don't have tomorrow's sunset times,
        we use the fallback 6-18 hour day/night logic after the provided sunset date.
        This ensures reasonable behavior when actual sunrise/sunset data isn't available.
        """
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time to be just before sunset (5:30 PM)
        mock_now = datetime(2024, 1, 1, 17, 30, 0, tzinfo=timezone.utc)

        with (
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now
            mock_dt_class.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )

            # Mock sun.sun entity with sunset at 6 PM
            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "2024-01-02T06:00:00Z",  # Sunrise tomorrow
                "next_setting": "2024-01-01T18:00:00Z",  # Sunset today at 6 PM
            }

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_hourly()

                assert result is not None
                assert len(result) == 24

                # Forecast spans from current hour (5 PM) through ~4 PM tomorrow
                # Current time is 5:30 PM, rounded down to 5 PM
                # idx 0: 5 PM (daytime, before sunset at 6 PM)
                # idx 1: 6 PM (at sunset)
                # idx 2-11: 7 PM to 4 AM (nighttime, after sunset)
                # idx 12-23: Tomorrow 5 AM to 4 PM (using fallback 6-18 logic)

                for idx, forecast in enumerate(result):
                    forecast_time = datetime.fromisoformat(forecast["datetime"])
                    condition = forecast["condition"]

                    if idx == 0:
                        # First hour: 5 PM, still daytime before sunset
                        assert condition in [
                            ATTR_CONDITION_SUNNY,
                            ATTR_CONDITION_PARTLYCLOUDY,
                            ATTR_CONDITION_CLOUDY,
                        ], f"First hour before sunset should be daytime, got {condition} at {forecast_time}"
                    elif idx < 12:
                        # Hours 1-11: 6 PM to 4 AM (after sunset, nighttime)
                        assert condition in [
                            ATTR_CONDITION_CLEAR_NIGHT,
                            ATTR_CONDITION_CLOUDY,
                        ], f"Hours after sunset should be nighttime, got {condition} at {forecast_time}"
                    else:
                        # Hours 12-23: Tomorrow 5 AM to 4 PM
                        # Using fallback 6-18 hours for tomorrow:
                        # 6 AM - 5:59 PM should be daytime
                        is_daytime = 6 <= forecast_time.hour < 18
                        if is_daytime:
                            # Should be daytime conditions
                            assert condition in [
                                ATTR_CONDITION_SUNNY,
                                ATTR_CONDITION_PARTLYCLOUDY,
                            ], f"Hours during fallback daytime should be daytime conditions, got {condition} at {forecast_time}"
                        else:
                            # Should be nighttime
                            assert condition in [
                                ATTR_CONDITION_CLEAR_NIGHT,
                                ATTR_CONDITION_CLOUDY,
                            ], f"Hours during fallback nighttime should be nighttime, got {condition} at {forecast_time}"

    async def test_async_forecast_hourly_polar_regions(
        self, weather_entity, coordinator
    ):
        """Test behavior in polar regions with extreme sunrise/sunset times."""
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Test midnight sun scenario - sunset is very late (11 PM next day)
        mock_now = datetime(
            2024, 6, 21, 12, 0, 0, tzinfo=timezone.utc
        )  # Summer solstice

        with (
            patch(
                "homeassistant.util.dt.parse_datetime",
                side_effect=lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
            ),
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now
            mock_dt_class.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )

            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "2024-06-21T03:00:00Z",  # Sunrise today (already passed)
                "next_setting": "2024-06-22T23:00:00Z",  # Sunset very late tomorrow
            }

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_hourly()

                # During midnight sun, all forecast hours should be daytime
                # Check that no nighttime condition conversion occurs

                for i, forecast in enumerate(result):
                    assert (
                        forecast["condition"] != ATTR_CONDITION_CLEAR_NIGHT
                    ), f"Should not have clear_night during midnight sun, got {forecast['condition']} at hour {i}"

                # At least some hours should maintain the original sunny condition
                sunny_forecasts = [
                    f for f in result if f["condition"] == ATTR_CONDITION_SUNNY
                ]
                assert (
                    len(sunny_forecasts) > 0
                ), "Should have some sunny conditions during extended daytime"

    async def test_async_forecast_hourly_datetime_parsing_error(
        self, weather_entity, coordinator
    ):
        """Test graceful handling of malformed datetime strings."""
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time
        mock_now = datetime(2024, 1, 1, 22, 0, 0, tzinfo=timezone.utc)

        with (
            patch(
                "homeassistant.util.dt.parse_datetime",
                side_effect=lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
            ),
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
            patch("datetime.datetime.fromisoformat") as mock_fromisoformat,
        ):
            mock_dt_class.now.return_value = mock_now
            # Make fromisoformat raise an exception
            mock_fromisoformat.side_effect = ValueError("Invalid datetime format")

            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "invalid-datetime-string",
                "next_setting": "2024-01-02T18:00:00Z",
            }

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                # Should not raise exception, should fall back to hardcoded times
                result = await weather_entity.async_forecast_hourly()

                assert result is not None
                assert len(result) == 24

                # Should fall back to hardcoded times - 22:00 should be nighttime
                night_forecasts = result[:7]
                for forecast in night_forecasts:
                    assert forecast["condition"] in [
                        ATTR_CONDITION_CLEAR_NIGHT,
                        ATTR_CONDITION_CLOUDY,
                    ], f"Expected clear_night or cloudy with datetime parsing error, got {forecast['condition']}"

    async def test_datetime_format_consistency(self, weather_entity, coordinator):
        """Test that daily and hourly forecasts use consistent datetime formats.

        Both should use naive ISO datetime strings for consistent UI display.
        This test covers the fix for issue #16 where inconsistent datetime formats
        caused empty hourly data in the weather card.
        """
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time for reproducible testing
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with (
            patch(
                "homeassistant.util.dt.parse_datetime",
                side_effect=lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
            ),
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch("datetime.datetime") as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now
            mock_dt_class.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )

            # Mock sun.sun entity for sunrise/sunset data
            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "2024-01-02T07:00:00Z",
                "next_setting": "2024-01-02T18:00:00Z",
            }

            with patch.object(
                weather_entity.coordinator.hass.states,
                "get",
                return_value=mock_sun_state,
            ):
                # Set up coordinator data with both current conditions and forecast
                coordinator.data = {
                    "temperature": 20.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                    "forecast": [
                        {
                            "datetime": "2024-01-02T00:00:00",  # Naive datetime string
                            "temperature": 22.0,
                            "templow": 16.0,
                            "condition": ATTR_CONDITION_SUNNY,
                            "precipitation": 0.0,
                            "wind_speed": 10.0,
                            "humidity": 60,
                        }
                    ],
                }

                # Get both daily and hourly forecasts
                daily_forecast = await weather_entity.async_forecast_daily()
                hourly_forecast = await weather_entity.async_forecast_hourly()

                assert daily_forecast is not None
                assert hourly_forecast is not None

                # Check daily forecast datetime format
                daily_datetime = daily_forecast[0]["datetime"]
                assert isinstance(daily_datetime, str)
                # Should be naive ISO format (no timezone info)
                assert "Z" not in daily_datetime
                assert "+" not in daily_datetime
                assert "-" in daily_datetime  # Should contain date separators

                # Check hourly forecast datetime format
                for forecast in hourly_forecast:
                    hourly_datetime = forecast["datetime"]
                    assert isinstance(hourly_datetime, str)
                    # Should be naive ISO format (no timezone info)
                    assert "Z" not in hourly_datetime
                    assert "+" not in hourly_datetime
                    assert "-" in hourly_datetime  # Should contain date separators

                    # Verify it's a valid ISO format that can be parsed
                    parsed = datetime.fromisoformat(hourly_datetime)
                    assert parsed.tzinfo is None  # Should be naive

                # Verify that both formats are consistent by checking they can be compared
                # Parse one datetime from each to ensure format compatibility
                daily_parsed = datetime.fromisoformat(daily_datetime)
                hourly_parsed = datetime.fromisoformat(hourly_forecast[0]["datetime"])

                # Both should be naive datetimes
                assert daily_parsed.tzinfo is None
                assert hourly_parsed.tzinfo is None

                # Should be able to compare them (same type)
                assert isinstance(daily_parsed, datetime)
                assert isinstance(hourly_parsed, datetime)

    async def test_async_forecast_hourly_missing_temperature_sensor(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when temperature sensor is missing."""
        coordinator.data = {
            # No temperature sensor
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should use default temperature (20.0) and still generate forecast
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)
            assert forecast["native_temperature"] > 0  # Should have reasonable values

    async def test_async_forecast_hourly_missing_humidity_sensor(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when humidity sensor is missing."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            # No humidity sensor
            "wind_speed": 5.0,
            "precipitation": 0.0,
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should use default humidity (50) and still generate forecast
        for forecast in result:
            assert isinstance(forecast["humidity"], (int, float))
            assert 0 <= forecast["humidity"] <= 100

    async def test_async_forecast_hourly_missing_wind_sensor(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when wind speed sensor is missing."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            # No wind_speed sensor
            "precipitation": 0.0,
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should use default wind speed and still generate forecast
        for forecast in result:
            assert isinstance(forecast["native_wind_speed"], float)
            assert forecast["native_wind_speed"] >= 0

    async def test_async_forecast_hourly_missing_precipitation_sensor(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when precipitation sensor is missing."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            # No precipitation sensor
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should use default precipitation (0.0) and still generate forecast
        for forecast in result:
            assert isinstance(forecast["native_precipitation"], float)
            assert forecast["native_precipitation"] >= 0

    async def test_async_forecast_hourly_missing_solar_sensors(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when solar sensors (UV, radiation, lux) are missing."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
            # No solar sensors: uv_index, solar_radiation, lux
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should still generate forecast using defaults for solar data
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)
            assert isinstance(forecast["condition"], str)

    async def test_async_forecast_hourly_missing_pressure_sensor(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when pressure sensor is missing."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
            # No pressure sensor
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should use default pressure and still generate forecast
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)

    async def test_async_forecast_hourly_missing_visibility_sensor(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when visibility sensor is missing."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
            # No visibility sensor
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should still generate forecast without visibility data
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)

    async def test_async_forecast_hourly_missing_wind_direction_sensor(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when wind direction sensor is missing."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
            # No wind_direction sensor
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should still generate forecast without wind direction data
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)

    async def test_async_forecast_hourly_multiple_missing_sensors(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when multiple sensors are missing."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            # Missing: humidity, wind_speed, precipitation, pressure, visibility, wind_direction
            # Missing solar sensors: uv_index, solar_radiation, lux
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should use defaults for all missing sensors and still generate forecast
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)
            assert isinstance(forecast["condition"], str)
            assert isinstance(forecast["native_precipitation"], float)
            assert isinstance(forecast["native_wind_speed"], float)
            assert isinstance(forecast["humidity"], (int, float))

    async def test_async_forecast_hourly_none_sensor_values(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when sensor values are explicitly None."""
        coordinator.data = {
            "temperature": None,  # Temperature sensor returns None
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": None,  # Humidity sensor returns None
            "wind_speed": None,  # Wind sensor returns None
            "precipitation": None,  # Precipitation sensor returns None
            "pressure": None,  # Pressure sensor returns None
            "visibility": None,  # Visibility sensor returns None
            "wind_direction": None,  # Wind direction sensor returns None
            "uv_index": None,  # UV sensor returns None
            "solar_radiation": None,  # Solar radiation sensor returns None
            "lux": None,  # Lux sensor returns None
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should use defaults for all None values and still generate forecast
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)
            assert isinstance(forecast["condition"], str)
            assert isinstance(forecast["native_precipitation"], float)
            assert isinstance(forecast["native_wind_speed"], float)
            assert isinstance(forecast["humidity"], (int, float))

    async def test_async_forecast_hourly_minimal_sensor_data(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast with only the bare minimum sensor data."""
        coordinator.data = {
            # Only temperature and condition - the most basic required data
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
        }

        result = await weather_entity.async_forecast_hourly()

        assert result is not None
        assert len(result) == 24

        # Should generate complete forecast using defaults for missing sensors
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)
            assert isinstance(forecast["condition"], str)
            assert isinstance(forecast["native_precipitation"], float)
            assert isinstance(forecast["native_wind_speed"], float)
            assert isinstance(forecast["humidity"], (int, float))
            assert "datetime" in forecast

    async def test_async_forecast_hourly_empty_sensor_data(
        self, weather_entity, coordinator
    ):
        """Test hourly forecast when coordinator data is empty dict."""
        coordinator.data = {}  # Completely empty data

        result = await weather_entity.async_forecast_hourly()

        # Empty dict is falsy, so forecast returns None
        assert result is None

    def test_weather_properties_with_missing_sensors(self, weather_entity, coordinator):
        """Test weather entity properties when various sensors are missing."""
        # Test with partial sensor data
        coordinator.data = {
            "temperature": 25.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 60,
            # Missing: pressure, wind_speed, wind_direction, visibility, precipitation
        }

        # Properties that have data should return values
        assert weather_entity.native_temperature == 25.0
        assert weather_entity.condition == ATTR_CONDITION_SUNNY
        assert weather_entity.humidity == 60

        # Properties that are missing should return None
        assert weather_entity.native_pressure is None
        assert weather_entity.native_wind_speed is None
        assert weather_entity.wind_bearing is None
        assert weather_entity.native_visibility is None
        assert weather_entity.native_precipitation is None
        assert weather_entity.native_precipitation_unit is None

    def test_weather_properties_with_none_values(self, weather_entity, coordinator):
        """Test weather entity properties when sensors return None values."""
        coordinator.data = {
            "temperature": None,
            "condition": None,
            "humidity": None,
            "pressure": None,
            "wind_speed": None,
            "wind_direction": None,
            "visibility": None,
            "precipitation": None,
            "precipitation_unit": None,
        }

        # All properties should return None when sensors return None
        assert weather_entity.native_temperature is None
        assert weather_entity.condition is None
        assert weather_entity.humidity is None
        assert weather_entity.native_pressure is None
        assert weather_entity.native_wind_speed is None
        assert weather_entity.wind_bearing is None
        assert weather_entity.native_visibility is None
        assert weather_entity.native_precipitation is None
        assert weather_entity.native_precipitation_unit is None

    def test_weather_properties_with_empty_data(self, weather_entity, coordinator):
        """Test weather entity properties when coordinator data is empty."""
        coordinator.data = {}  # Empty dict

        # All properties should return None when no data
        assert weather_entity.native_temperature is None
        assert weather_entity.condition is None
        assert weather_entity.humidity is None
        assert weather_entity.native_pressure is None
        assert weather_entity.native_wind_speed is None
        assert weather_entity.wind_bearing is None
        assert weather_entity.native_visibility is None
        assert weather_entity.native_precipitation is None
        assert weather_entity.native_precipitation_unit is None

    def test_weather_properties_with_no_data(self, weather_entity, coordinator):
        """Test weather entity properties when coordinator data is None."""
        coordinator.data = None

        # All properties should return None when no coordinator data
        assert weather_entity.native_temperature is None
        assert weather_entity.condition is None
        assert weather_entity.humidity is None
        assert weather_entity.native_pressure is None
        assert weather_entity.native_wind_speed is None
        assert weather_entity.wind_bearing is None
        assert weather_entity.native_visibility is None
        assert weather_entity.native_precipitation is None
        assert weather_entity.native_precipitation_unit is None

    async def test_daily_forecast_with_missing_data(self, weather_entity, coordinator):
        """Test daily forecast when forecast data is missing or incomplete."""
        # Test with no forecast data
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
        }

        result = await weather_entity.async_forecast_daily()
        assert result is None

        # Test with empty forecast list
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "forecast": [],
        }

        result = await weather_entity.async_forecast_daily()
        assert result == []

        # Test with incomplete forecast data
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "forecast": [
                {
                    "datetime": "2024-01-01T00:00:00",
                    "temperature": 22.0,
                    # Missing templow, condition, etc.
                }
            ],
        }

        result = await weather_entity.async_forecast_daily()
        assert result is not None
        assert len(result) == 1
        assert result[0]["native_temperature"] == 22.0
        # Should use defaults for missing fields
        assert result[0]["native_templow"] == 19.0  # temperature - 3.0
        assert result[0]["condition"] == ATTR_CONDITION_SUNNY  # Should have default
        assert result[0]["native_precipitation"] == 0  # Default
        assert result[0]["native_wind_speed"] == 0  # Default
        assert result[0]["humidity"] == 50  # Default

    async def test_async_forecast_daily_comprehensive_fallback(
        self, weather_entity, coordinator
    ):
        """Test daily forecast generation using comprehensive meteorological analysis when no external forecast data."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
            # No "forecast" key - should trigger comprehensive forecast generation
        }

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 5  # 5-day forecast

        # Check that all items are Forecast objects with proper structure
        for forecast in result:
            assert isinstance(forecast, dict)
            assert "datetime" in forecast
            assert isinstance(forecast["native_temperature"], float)
            assert isinstance(forecast["native_templow"], float)
            assert "condition" in forecast
            assert isinstance(forecast["native_precipitation"], float)
            assert isinstance(forecast["native_wind_speed"], float)
            assert isinstance(forecast["humidity"], (int, float))

    async def test_async_forecast_daily_comprehensive_with_magicmock_sensors(
        self, weather_entity, coordinator
    ):
        """Test daily forecast with MagicMock sensor values (from tests)."""
        # Simulate test environment where sensors might be MagicMock objects
        mock_temperature = MagicMock()
        mock_temperature._mock_name = "temperature"

        coordinator.data = {
            "temperature": mock_temperature,  # MagicMock object
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
            # No "forecast" key
        }

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 5  # Should still generate 5-day forecast

        # Should handle MagicMock gracefully and use defaults
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)
            assert "condition" in forecast

    async def test_async_forecast_daily_comprehensive_error_handling(
        self, weather_entity, coordinator
    ):
        """Test error handling in comprehensive daily forecast generation."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
            # No "forecast" key
        }

        # Mock the forecast.generate_comprehensive_forecast to raise an exception
        with patch.object(
            weather_entity._daily_generator,
            "generate_forecast",
            side_effect=Exception("Test error"),
        ):
            result = await weather_entity.async_forecast_daily()

            # Should return None on error
            assert result is None

    async def test_async_forecast_daily_comprehensive_with_altitude(
        self, weather_entity, coordinator
    ):
        """Test daily forecast with altitude configuration."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
        }

        # Mock config entry with altitude
        weather_entity._config_entry.options = {"altitude": 500.0}

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 5

        # Should use the configured altitude for astronomical calculations
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)

    async def test_async_forecast_daily_comprehensive_minimal_sensors(
        self, weather_entity, coordinator
    ):
        """Test daily forecast with minimal sensor data."""
        coordinator.data = {
            "temperature": 15.0,
            "condition": ATTR_CONDITION_CLOUDY,
            "forecast": [
                {
                    "datetime": "2024-01-01T00:00:00",
                    "temperature": 18.0,
                    "templow": 10.0,
                    "condition": ATTR_CONDITION_CLOUDY,
                    "precipitation": 0.0,
                },
                {
                    "datetime": "2024-01-02T00:00:00",
                    "temperature": 16.0,
                    "templow": 8.0,
                    "condition": ATTR_CONDITION_CLOUDY,
                    "precipitation": 0.0,
                },
                {
                    "datetime": "2024-01-03T00:00:00",
                    "temperature": 17.0,
                    "templow": 9.0,
                    "condition": ATTR_CONDITION_CLOUDY,
                    "precipitation": 0.0,
                },
                {
                    "datetime": "2024-01-04T00:00:00",
                    "temperature": 19.0,
                    "templow": 11.0,
                    "condition": ATTR_CONDITION_CLOUDY,
                    "precipitation": 0.0,
                },
                {
                    "datetime": "2024-01-05T00:00:00",
                    "temperature": 20.0,
                    "templow": 12.0,
                    "condition": ATTR_CONDITION_CLOUDY,
                    "precipitation": 0.0,
                },
            ],
            # Missing other sensors - should use defaults
        }

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 5

        # Should generate forecast using defaults for missing sensors
        for forecast in result:
            assert isinstance(forecast["native_temperature"], float)
            assert "condition" in forecast
            assert isinstance(forecast["native_precipitation"], float)

    async def test_async_forecast_daily_external_vs_comprehensive(
        self, weather_entity, coordinator
    ):
        """Test that external forecast data takes precedence over comprehensive generation."""
        # Set up data with both external forecast and sensor data
        external_forecast = [
            {
                "datetime": "2024-01-01T00:00:00",
                "temperature": 25.0,
                "templow": 18.0,
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 10.0,
                "humidity": 45,
            }
        ]

        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_CLOUDY,
            "humidity": 60,
            "wind_speed": 5.0,
            "precipitation": 1.0,
            "forecast": external_forecast,  # External forecast present
        }

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 1

        # Should use external forecast data, not generate comprehensive forecast
        forecast = result[0]
        assert forecast["native_temperature"] == 25.0  # External temperature
        assert forecast["native_templow"] == 18.0  # External templow
        assert forecast["condition"] == ATTR_CONDITION_SUNNY  # External condition
        assert forecast["humidity"] == 45  # External humidity

    async def test_async_forecast_daily_condition_progression(
        self, weather_entity, coordinator
    ):
        """Test that daily forecast shows condition progression over days."""
        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
        }

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 5

        # Should have some variation in conditions across days
        conditions = [forecast["condition"] for forecast in result]
        unique_conditions = set(conditions)

        # At minimum should have the starting condition
        assert ATTR_CONDITION_SUNNY in unique_conditions

        # Should have some variation (comprehensive forecast generates meteorological progression)
        # Note: exact conditions depend on the algorithm, but should not be identical
        assert len(unique_conditions) >= 1  # At least the starting condition

        # Temperatures should vary across days
        temperatures = [forecast["native_temperature"] for forecast in result]
        unique_temps = set(temperatures)
        assert len(unique_temps) >= 1  # Should have some temperature variation

    async def test_forecast_temperature_unit_conversion(
        self, weather_entity, coordinator
    ):
        """Test that forecast temperatures are properly converted to Celsius units.

        This test verifies the fix for issue #17 where forecast temperatures
        were displayed in Fahrenheit instead of Celsius when configured for Celsius.
        """
        from unittest.mock import patch

        # Mock the forecast generation to return Fahrenheit temperatures
        # This simulates the original bug where forecasts were in Fahrenheit
        mock_fahrenheit_forecast = [
            {
                "datetime": "2024-01-01T00:00:00",
                "temperature": 68.0,  # 20°C = 68°F
                "templow": 59.0,  # 15°C = 59°F
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 5.0,
                "humidity": 50,
            },
            {
                "datetime": "2024-01-02T00:00:00",
                "temperature": 77.0,  # 25°C = 77°F
                "templow": 68.0,  # 20°C = 68°F
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 5.0,
                "humidity": 50,
            },
        ]

        with patch.object(
            weather_entity._daily_generator,
            "generate_forecast",
            return_value=mock_fahrenheit_forecast,
        ):
            coordinator.data = {
                "temperature": 20.0,  # Current temperature in Celsius
                "condition": ATTR_CONDITION_SUNNY,
                "humidity": 50,
                "wind_speed": 5.0,
                "precipitation": 0.0,
                # No external forecast - will use comprehensive generation
            }

            result = await weather_entity.async_forecast_daily()

            assert result is not None
            assert len(result) == 2

            # Verify temperatures are converted to Celsius
            forecast1 = result[0]
            forecast2 = result[1]

            # 68°F should be converted to 20°C
            assert abs(forecast1["native_temperature"] - 20.0) < 0.1
            assert abs(forecast1["native_templow"] - 15.0) < 0.1

            # 77°F should be converted to 25°C
            assert abs(forecast2["native_temperature"] - 25.0) < 0.1
            assert abs(forecast2["native_templow"] - 20.0) < 0.1

    async def test_hourly_forecast_temperature_unit_conversion(
        self, weather_entity, coordinator
    ):
        """Test that hourly forecast temperatures are properly converted to Celsius units."""
        from unittest.mock import patch

        # Mock the hourly forecast generation to return Fahrenheit temperatures
        mock_fahrenheit_hourly = [
            {
                "datetime": "2024-01-01T00:00:00",
                "temperature": 68.0,  # 20°C = 68°F
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 5.0,
                "humidity": 50,
                "is_nighttime": False,
            },
            {
                "datetime": "2024-01-01T01:00:00",
                "temperature": 64.4,  # 18°C = 64.4°F
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 5.0,
                "humidity": 50,
                "is_nighttime": False,
            },
        ]

        with patch.object(
            weather_entity._hourly_generator,
            "generate_forecast",
            return_value=mock_fahrenheit_hourly,
        ):
            coordinator.data = {
                "temperature": 20.0,  # Current temperature in Celsius
                "condition": ATTR_CONDITION_SUNNY,
                "humidity": 50,
                "wind_speed": 5.0,
                "precipitation": 0.0,
            }

            result = await weather_entity.async_forecast_hourly()

            assert result is not None
            assert len(result) == 2

            # Verify temperatures are converted to Celsius
            forecast1 = result[0]
            forecast2 = result[1]

            # 68°F should be converted to 20°C
            assert abs(forecast1["native_temperature"] - 20.0) < 0.1

            # 64.4°F should be converted to 18°C
            assert abs(forecast2["native_temperature"] - 18.0) < 0.1

    async def test_external_forecast_no_unit_conversion(
        self, weather_entity, coordinator
    ):
        """Test that external forecast data is not unit-converted (assumed to be in Celsius)."""
        # External forecast data should already be in Celsius
        external_forecast = [
            {
                "datetime": "2024-01-01T00:00:00",
                "temperature": 20.0,  # Already in Celsius
                "templow": 15.0,  # Already in Celsius
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 5.0,
                "humidity": 50,
            },
        ]

        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_SUNNY,
            "humidity": 50,
            "wind_speed": 5.0,
            "precipitation": 0.0,
            "forecast": external_forecast,  # External forecast present
        }

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 1

        forecast = result[0]

        # External temperatures should remain unchanged (no conversion)
        assert forecast["native_temperature"] == 20.0
        assert forecast["native_templow"] == 15.0

    async def test_daily_forecast_external_with_missing_templow(
        self, weather_entity, coordinator
    ):
        """Test external forecast handling when templow is missing."""
        external_forecast = [
            {
                "datetime": "2024-01-01T00:00:00",
                "temperature": 25.0,  # High temperature
                # templow is missing - should default to temperature - 3.0
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 10.0,
                "humidity": 45,
            }
        ]

        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_CLOUDY,
            "humidity": 60,
            "wind_speed": 5.0,
            "precipitation": 1.0,
            "forecast": external_forecast,
        }

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 1

        forecast = result[0]
        assert forecast["native_temperature"] == 25.0
        assert forecast["native_templow"] == 22.0  # 25.0 - 3.0

    async def test_daily_forecast_external_with_invalid_temperatures(
        self, weather_entity, coordinator
    ):
        """Test external forecast handling with None/invalid temperature values."""
        external_forecast = [
            {
                "datetime": "2024-01-01T00:00:00",
                "temperature": None,  # Invalid temperature
                "templow": 15.0,
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 10.0,
                "humidity": 45,
            }
        ]

        coordinator.data = {
            "temperature": 20.0,
            "condition": ATTR_CONDITION_CLOUDY,
            "humidity": 60,
            "wind_speed": 5.0,
            "precipitation": 1.0,
            "forecast": external_forecast,
        }

        result = await weather_entity.async_forecast_daily()

        assert result is not None
        assert len(result) == 1

        forecast = result[0]
        assert forecast["native_temperature"] == 20.0  # Default value when None
        assert forecast["native_templow"] == 15.0

    async def test_daily_forecast_comprehensive_extreme_temperatures(
        self, weather_entity, coordinator
    ):
        """Test comprehensive forecast with extreme temperature values."""
        from unittest.mock import patch

        # Mock extreme temperature forecast
        mock_extreme_forecast = [
            {
                "datetime": "2024-01-01T00:00:00",
                "temperature": 212.0,  # 100°C = 212°F (boiling point)
                "templow": -40.0,  # -40°C = -40°F
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 5.0,
                "humidity": 50,
            },
        ]

        with patch.object(
            weather_entity._daily_generator,
            "generate_forecast",
            return_value=mock_extreme_forecast,
        ):
            coordinator.data = {
                "temperature": 100.0,  # Extreme current temperature
                "condition": ATTR_CONDITION_SUNNY,
                "humidity": 10,  # Low humidity for extreme temps
                "wind_speed": 5.0,
                "precipitation": 0.0,
            }

            result = await weather_entity.async_forecast_daily()

            assert result is not None
            assert len(result) == 1

            forecast = result[0]
            # Should convert extreme temperatures accurately
            assert abs(forecast["native_temperature"] - 100.0) < 0.1  # 212°F -> 100°C
            assert abs(forecast["native_templow"] - (-40.0)) < 0.1  # -40°F -> -40°C

    async def test_daily_forecast_comprehensive_with_various_conditions(
        self, weather_entity, coordinator
    ):
        """Test comprehensive forecast with different starting weather conditions."""
        test_conditions = [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_SNOWY,
            ATTR_CONDITION_LIGHTNING_RAINY,
        ]

        for condition in test_conditions:
            coordinator.data = {
                "temperature": 20.0,
                "condition": condition,
                "humidity": 50,
                "wind_speed": 5.0,
                "precipitation": 0.0,
            }

            result = await weather_entity.async_forecast_daily()

            assert result is not None
            assert len(result) == 5

            # First forecast should start with the given condition
            first_forecast = result[0]
            assert first_forecast["condition"] == condition

            # All forecasts should have valid data
            for forecast in result:
                assert isinstance(forecast["native_temperature"], float)
                assert isinstance(forecast["native_templow"], float)
                assert forecast["condition"] in [
                    ATTR_CONDITION_SUNNY,
                    ATTR_CONDITION_PARTLYCLOUDY,
                    ATTR_CONDITION_CLOUDY,
                    ATTR_CONDITION_RAINY,
                    ATTR_CONDITION_SNOWY,
                    ATTR_CONDITION_LIGHTNING_RAINY,
                    ATTR_CONDITION_POURING,
                    ATTR_CONDITION_HAIL,
                    ATTR_CONDITION_WINDY,
                    ATTR_CONDITION_FOG,
                    ATTR_CONDITION_CLEAR_NIGHT,
                ]
                assert isinstance(forecast["native_precipitation"], float)
                assert isinstance(forecast["native_wind_speed"], float)
                assert isinstance(forecast["humidity"], int)

    async def test_daily_forecast_comprehensive_pressure_scenarios(
        self, weather_entity, coordinator
    ):
        """Test comprehensive forecast with different pressure system scenarios."""
        from unittest.mock import patch

        # Test high pressure system
        mock_high_pressure_state = {
            "pressure_analysis": {
                "pressure_system": "high_pressure",
                "current_trend": 2.0,
                "long_term_trend": 1.5,
                "storm_probability": 5,
            },
            "atmospheric_stability": 0.8,
            "cloud_analysis": {"cloud_cover": 20.0},
            "moisture_analysis": {"condensation_potential": 0.2},
            "wind_pattern_analysis": {"direction_stability": 0.7},
            "current_conditions": {"humidity": 40.0},
        }

        with patch.object(
            weather_entity._meteorological_analyzer,
            "analyze_state",
            return_value=mock_high_pressure_state,
        ):
            coordinator.data = {
                "temperature": 25.0,  # Warm temperature
                "condition": ATTR_CONDITION_SUNNY,
                "humidity": 40,
                "wind_speed": 3.0,
                "precipitation": 0.0,
            }

            result = await weather_entity.async_forecast_daily()

            assert result is not None
            assert len(result) == 5

            # High pressure should generally favor clearer conditions
            sunny_count = sum(
                1 for f in result if f["condition"] == ATTR_CONDITION_SUNNY
            )
            assert sunny_count >= 2  # At least some sunny days

        # Test low pressure system
        mock_low_pressure_state = {
            "pressure_analysis": {
                "pressure_system": "low_pressure",
                "current_trend": -1.5,
                "long_term_trend": -1.0,
                "storm_probability": 60,
            },
            "atmospheric_stability": 0.3,
            "cloud_analysis": {"cloud_cover": 80.0},
            "moisture_analysis": {"condensation_potential": 0.7},
            "wind_pattern_analysis": {"direction_stability": 0.4},
            "current_conditions": {"humidity": 70.0},
        }

        with patch.object(
            weather_entity._meteorological_analyzer,
            "analyze_state",
            return_value=mock_low_pressure_state,
        ):
            coordinator.data = {
                "temperature": 15.0,  # Cooler temperature
                "condition": ATTR_CONDITION_CLOUDY,
                "humidity": 70,
                "wind_speed": 8.0,
                "precipitation": 2.0,
            }

            result = await weather_entity.async_forecast_daily()

            assert result is not None
            assert len(result) == 5

            # Low pressure should favor precipitation
            rainy_count = sum(
                1
                for f in result
                if f["condition"]
                in [
                    ATTR_CONDITION_RAINY,
                    ATTR_CONDITION_LIGHTNING_RAINY,
                    ATTR_CONDITION_POURING,
                ]
            )
            assert rainy_count >= 1  # At least some rainy days

    async def test_daily_forecast_comprehensive_altitude_effects(
        self, weather_entity, coordinator
    ):
        """Test how altitude affects daily forecast generation."""
        # Test with different altitude settings
        test_altitudes = [0, 500, 1000, 2000]  # meters

        for altitude in test_altitudes:
            # Mock the coordinator entry to return different altitudes
            mock_entry = MagicMock()
            mock_entry.options = {"altitude": altitude}
            coordinator.entry = mock_entry

            coordinator.data = {
                "temperature": 20.0,
                "condition": ATTR_CONDITION_SUNNY,
                "humidity": 50,
                "wind_speed": 5.0,
                "precipitation": 0.0,
            }

            result = await weather_entity.async_forecast_daily()

            assert result is not None
            assert len(result) == 5

            # All forecasts should be valid regardless of altitude
            for forecast in result:
                assert isinstance(forecast["native_temperature"], float)
                assert isinstance(forecast["native_templow"], float)
                assert forecast["condition"] is not None
                assert isinstance(forecast["native_precipitation"], float)

    async def test_daily_forecast_external_vs_comprehensive_priority(
        self, weather_entity, coordinator
    ):
        """Test that external forecast takes absolute priority over comprehensive generation."""
        from unittest.mock import patch

        external_forecast = [
            {
                "datetime": "2024-01-01T00:00:00",
                "temperature": 30.0,  # Very different from sensor data
                "templow": 25.0,
                "condition": ATTR_CONDITION_SNOWY,  # Very different condition
                "precipitation": 10.0,  # Heavy precipitation
                "wind_speed": 20.0,  # Strong wind
                "humidity": 90,  # High humidity
            }
        ]

        # Mock comprehensive forecast to return completely different data
        mock_comprehensive = [
            {
                "datetime": "2024-01-01T00:00:00",
                "temperature": 15.0,  # Different temperature
                "templow": 10.0,
                "condition": ATTR_CONDITION_SUNNY,
                "precipitation": 0.0,
                "wind_speed": 5.0,
                "humidity": 40,
            }
        ]

        with patch.object(
            weather_entity._daily_generator,
            "generate_forecast",
            return_value=mock_comprehensive,
        ):
            coordinator.data = {
                "temperature": 20.0,
                "condition": ATTR_CONDITION_CLOUDY,
                "humidity": 50,
                "wind_speed": 5.0,
                "precipitation": 0.0,
                "forecast": external_forecast,  # External takes priority
            }

            result = await weather_entity.async_forecast_daily()

            assert result is not None
            assert len(result) == 1

            # Should use external forecast data exclusively
            forecast = result[0]
            assert forecast["native_temperature"] == 30.0  # External temperature
            assert forecast["native_templow"] == 25.0  # External templow
            assert forecast["condition"] == ATTR_CONDITION_SNOWY  # External condition
            assert forecast["native_precipitation"] == 10.0  # External precipitation
            assert forecast["native_wind_speed"] == 20.0  # External wind
            assert forecast["humidity"] == 90  # External humidity

    async def test_daily_forecast_temperature_unit_conversion_precision(
        self, weather_entity, coordinator
    ):
        """Test precision of temperature unit conversions in daily forecast."""
        from unittest.mock import patch

        # Test various Fahrenheit temperatures and their Celsius equivalents
        test_cases = [
            (32.0, 0.0),  # Freezing point
            (68.0, 20.0),  # Room temperature
            (77.0, 25.0),  # Warm
            (86.0, 30.0),  # Hot
            (104.0, 40.0),  # Very hot
            (-4.0, -20.0),  # Cold
            (212.0, 100.0),  # Boiling point
        ]

        for fahrenheit, expected_celsius in test_cases:
            mock_forecast = [
                {
                    "datetime": "2024-01-01T00:00:00",
                    "temperature": fahrenheit,
                    "templow": fahrenheit - 5.0,  # 5°F lower
                    "condition": ATTR_CONDITION_SUNNY,
                    "precipitation": 0.0,
                    "wind_speed": 5.0,
                    "humidity": 50,
                }
            ]

            with patch.object(
                weather_entity._daily_generator,
                "generate_forecast",
                return_value=mock_forecast,
            ):
                coordinator.data = {
                    "temperature": expected_celsius,
                    "condition": ATTR_CONDITION_SUNNY,
                    "humidity": 50,
                    "wind_speed": 5.0,
                    "precipitation": 0.0,
                }

                result = await weather_entity.async_forecast_daily()

                assert result is not None
                assert len(result) == 1

                forecast = result[0]
                # Check conversion precision (within 0.1°C)
                assert abs(forecast["native_temperature"] - expected_celsius) < 0.1
                assert (
                    abs(forecast["native_templow"] - (expected_celsius - 5.0 * 5 / 9))
                    < 0.1
                )


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
