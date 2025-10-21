"""Tests for the Micro Weather Station weather entity."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
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
            patch(
                "custom_components.micro_weather.weather_forecast.datetime"
            ) as mock_dt_class,
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
            patch(
                "custom_components.micro_weather.weather_forecast.datetime"
            ) as mock_dt_class,
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
            patch(
                "custom_components.micro_weather.weather_forecast.datetime"
            ) as mock_dt_class,
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
            patch(
                "custom_components.micro_weather.weather_forecast.datetime"
            ) as mock_dt_class,
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

                # During daytime hours, partlycloudy should be maintained (not converted to cloudy)
                for forecast in daytime_forecasts:
                    assert (
                        forecast["condition"] == ATTR_CONDITION_PARTLYCLOUDY
                    ), f"Expected partlycloudy during daytime, got {forecast['condition']} at {forecast['datetime']}"

                # During nighttime hours, partlycloudy should be converted to cloudy
                for forecast in nighttime_forecasts:
                    assert (
                        forecast["condition"] == ATTR_CONDITION_CLOUDY
                    ), f"Expected cloudy during nighttime, got {forecast['condition']} at {forecast['datetime']}"

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
            patch(
                "custom_components.micro_weather.weather_forecast.datetime"
            ) as mock_dt_class,
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

                # Check daytime hours (should remain sunny)
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
                    assert (
                        forecast["condition"] == ATTR_CONDITION_SUNNY
                    ), f"Expected sunny during daytime, got {forecast['condition']} at {forecast['datetime']}"

                # Nighttime should be clear_night
                for forecast in nighttime_forecasts:
                    assert (
                        forecast["condition"] == ATTR_CONDITION_CLEAR_NIGHT
                    ), f"Expected clear_night during nighttime, got {forecast['condition']} at {forecast['datetime']}"

    async def test_async_forecast_hourly_sunrise_sunset_boundary(
        self, weather_entity, coordinator
    ):
        """Test behavior exactly at sunrise and sunset times."""
        from datetime import datetime, timezone
        from unittest.mock import patch

        # Mock current time to be exactly at sunrise (7 AM)
        mock_now = datetime(2024, 1, 2, 7, 0, 0, tzinfo=timezone.utc)

        with (
            patch(
                "homeassistant.util.dt.parse_datetime",
                side_effect=lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
            ),
            patch("homeassistant.util.dt.now", return_value=mock_now),
            patch(
                "custom_components.micro_weather.weather_forecast.datetime"
            ) as mock_dt_class,
        ):
            mock_dt_class.now.return_value = mock_now
            mock_dt_class.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
                s.replace("Z", "+00:00")
            )

            mock_sun_state = MagicMock()
            mock_sun_state.attributes = {
                "next_rising": "2024-01-02T07:00:00Z",  # Exactly now
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

                result = await weather_entity.async_forecast_hourly()

                # First hour should be daytime (sunrise_time <= forecast_time)
                first_hour = result[0]
                assert (
                    first_hour["condition"] == ATTR_CONDITION_SUNNY
                ), f"Expected sunny at sunrise boundary, got {first_hour['condition']}"

                # Test exactly at sunset
                mock_now_sunset = datetime(2024, 1, 2, 18, 0, 0, tzinfo=timezone.utc)
                with (
                    patch(
                        "homeassistant.util.dt.parse_datetime",
                        side_effect=lambda s: datetime.fromisoformat(
                            s.replace("Z", "+00:00")
                        ),
                    ),
                    patch("homeassistant.util.dt.now", return_value=mock_now_sunset),
                    patch(
                        "custom_components.micro_weather.weather_forecast.datetime"
                    ) as mock_dt_class_sunset,
                ):
                    mock_dt_class_sunset.now.return_value = mock_now_sunset
                    mock_dt_class_sunset.fromisoformat.side_effect = (
                        lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
                    )
                    result_sunset = await weather_entity.async_forecast_hourly()

                    # First hour should be nighttime (forecast_time < sunset_time fails)
                    first_hour_sunset = result_sunset[0]
                    assert (
                        first_hour_sunset["condition"] == ATTR_CONDITION_CLEAR_NIGHT
                    ), f"Expected clear_night at sunset boundary, got {first_hour_sunset['condition']}"

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
            patch(
                "custom_components.micro_weather.weather_forecast.datetime"
            ) as mock_dt_class,
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
            patch(
                "custom_components.micro_weather.weather_forecast.datetime"
            ) as mock_dt_class,
            patch(
                "custom_components.micro_weather.weather_forecast.datetime.fromisoformat"
            ) as mock_fromisoformat,
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
            patch(
                "custom_components.micro_weather.weather_forecast.datetime"
            ) as mock_dt_class,
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
