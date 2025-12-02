"""Test the core weather condition analysis functionality."""

from collections import deque
from datetime import datetime, timedelta

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
)
import pytest

from custom_components.micro_weather.analysis.atmospheric import AtmosphericAnalyzer
from custom_components.micro_weather.analysis.core import WeatherConditionAnalyzer
from custom_components.micro_weather.analysis.solar import SolarAnalyzer
from custom_components.micro_weather.analysis.trends import TrendsAnalyzer


class TestWeatherConditionAnalyzer:
    """Test the WeatherConditionAnalyzer class."""

    @pytest.fixture
    def mock_sensor_history(self):
        """Create mock sensor history for testing."""
        history = {
            "outdoor_temp": deque(maxlen=192),
            "humidity": deque(maxlen=192),
            "pressure": deque(maxlen=192),
            "wind_speed": deque(maxlen=192),
            "wind_direction": deque(maxlen=192),
            "solar_radiation": deque(maxlen=192),
            "rain_rate": deque(maxlen=192),
        }

        # Add some historical data
        base_time = datetime.now()
        for i in range(10):
            timestamp = base_time - timedelta(hours=i)
            history["outdoor_temp"].append({"timestamp": timestamp, "value": 70.0 + i})
            history["humidity"].append({"timestamp": timestamp, "value": 60.0 + i})
            history["pressure"].append(
                {"timestamp": timestamp, "value": 29.92 - i * 0.01}
            )
            history["wind_speed"].append(
                {"timestamp": timestamp, "value": 5.0 + i * 0.1}
            )
            history["wind_direction"].append(
                {"timestamp": timestamp, "value": 180.0 + i * 10}
            )
            history["solar_radiation"].append(
                {"timestamp": timestamp, "value": 200.0 + i * 10}
            )
            history["rain_rate"].append({"timestamp": timestamp, "value": 0.0})

        return history

    @pytest.fixture
    def analyzers(self, mock_sensor_history):
        """Create analyzer instances for testing."""
        trends = TrendsAnalyzer(mock_sensor_history)
        atmospheric = AtmosphericAnalyzer(mock_sensor_history, trends)
        solar = SolarAnalyzer(mock_sensor_history)
        core = WeatherConditionAnalyzer(atmospheric, solar, trends)
        return {
            "atmospheric": atmospheric,
            "solar": solar,
            "trends": trends,
            "core": core,
        }

    def test_calculate_dewpoint(self, analyzers):
        """Test dewpoint calculation."""
        # Test standard conditions
        dewpoint = analyzers["core"].calculate_dewpoint(
            72.0, 60.0
        )  # 72°F, 60% humidity
        assert dewpoint is not None
        assert 50 < dewpoint < 72  # Dewpoint should be between 50°F and air temp

        # Test high humidity
        dewpoint_high = analyzers["core"].calculate_dewpoint(70.0, 90.0)
        assert dewpoint_high > dewpoint  # Higher humidity = higher dewpoint

        # Test low humidity
        dewpoint_low = analyzers["core"].calculate_dewpoint(70.0, 10.0)
        assert dewpoint_low < dewpoint  # Lower humidity = lower dewpoint

        # Test edge case: very dry air
        dewpoint_dry = analyzers["core"].calculate_dewpoint(70.0, 0.0)
        assert (
            dewpoint_dry == 70.0 - 50
        )  # Should return temp - 50 for very dry conditions

    def test_calculate_dewpoint_edge_cases(self, analyzers):
        """Test dewpoint calculation edge cases."""
        # Test very high humidity
        dewpoint_100 = analyzers["core"].calculate_dewpoint(80.0, 100.0)
        assert abs(dewpoint_100 - 80.0) < 1  # Should be very close to air temperature

        # Test very low temperature
        dewpoint_cold = analyzers["core"].calculate_dewpoint(-10.0, 50.0)
        assert dewpoint_cold < -10.0  # Dewpoint should be below air temperature

        # Test very high temperature
        dewpoint_hot = analyzers["core"].calculate_dewpoint(120.0, 30.0)
        assert dewpoint_hot < 120.0  # Dewpoint should be below air temperature

        # Test boundary humidity values
        dewpoint_min_humidity = analyzers["core"].calculate_dewpoint(70.0, 0.1)
        dewpoint_max_humidity = analyzers["core"].calculate_dewpoint(70.0, 99.9)
        assert dewpoint_min_humidity < dewpoint_max_humidity

    def test_classify_precipitation_intensity(self, analyzers):
        """Test precipitation intensity classification."""
        assert analyzers["core"].classify_precipitation_intensity(0.0) == "trace"
        assert analyzers["core"].classify_precipitation_intensity(0.01) == "light"
        assert analyzers["core"].classify_precipitation_intensity(0.15) == "moderate"
        assert analyzers["core"].classify_precipitation_intensity(0.6) == "heavy"

    def test_estimate_visibility(self, analyzers):
        """Test visibility estimation."""
        sensor_data = {
            "solar_lux": 50000.0,
            "solar_radiation": 600.0,
            "rain_rate": 0.0,
            "wind_speed": 5.0,
            "wind_gust": 8.0,
            "humidity": 50.0,
            "outdoor_temp": 70.0,
        }

        # Test clear conditions
        visibility_clear = analyzers["core"].estimate_visibility(
            ATTR_CONDITION_SUNNY, sensor_data
        )
        assert visibility_clear > 20  # Good visibility

        # Test foggy conditions
        visibility_fog = analyzers["core"].estimate_visibility(
            ATTR_CONDITION_FOG, sensor_data
        )
        assert visibility_fog < 10  # Poor visibility

        # Test rainy conditions
        sensor_data_rain = sensor_data.copy()
        sensor_data_rain["rain_rate"] = 0.2
        visibility_rain = analyzers["core"].estimate_visibility(
            ATTR_CONDITION_RAINY, sensor_data_rain
        )
        assert visibility_rain < 20  # Reduced visibility

    def test_weather_condition_priority_order(self, analyzers):
        """Test that weather conditions follow correct priority order: rain > fog > cloudy, windy only on sunny."""

        # PRIORITY 1: Rain should override fog
        sensor_data_rain_fog = {
            "rain_rate": 0.1,  # Significant rain
            "rain_state": "wet",
            "outdoor_temp": 50.0,
            "humidity": 98.0,  # Fog-level humidity
            "dewpoint": 49.5,
            "wind_speed": 2.0,
            "wind_gust": 3.0,
            "solar_radiation": 10.0,
            "solar_lux": 1000.0,
            "uv_index": 0.0,
            "pressure": 29.92,
            "solar_elevation": 45.0,
        }
        condition = analyzers["core"].determine_condition(sensor_data_rain_fog, 0.0)
        assert condition == ATTR_CONDITION_RAINY  # Rain takes priority over fog

        # PRIORITY 2: Fog should override cloudy
        # For fog, we need very specific conditions:
        # - Very high humidity (98%+)
        # - Very tight dewpoint spread (< 1°F)
        # - Calm winds
        # - Very low solar radiation
        sensor_data_fog = {
            "rain_rate": 0.0,  # No rain
            "rain_state": "dry",
            "outdoor_temp": 50.0,
            "humidity": 99.0,  # Very high humidity (must be >= 98 for fog)
            "dewpoint": 49.6,  # Very tight dewpoint spread (0.4°F)
            "wind_speed": 1.0,  # Very calm winds
            "wind_gust": 2.0,
            "solar_radiation": 5.0,  # Very low solar (fog blocks light)
            "solar_lux": 500.0,
            "uv_index": 0.0,
            "pressure": 29.92,
            "solar_elevation": 30.0,  # Low enough that 5 W/m² is fog-level
        }
        condition = analyzers["core"].determine_condition(sensor_data_fog, 0.0)
        assert condition == ATTR_CONDITION_FOG  # Fog takes priority over cloudy

        # PRIORITY 5: Windy should ONLY apply on sunny days
        sensor_data_windy_cloudy = {
            "rain_rate": 0.0,
            "rain_state": "dry",
            "outdoor_temp": 60.0,
            "humidity": 70.0,
            "dewpoint": 50.0,
            "wind_speed": 25.0,  # Strong winds
            "wind_gust": 35.0,
            "solar_radiation": 100.0,  # Low solar = cloudy
            "solar_lux": 10000.0,
            "uv_index": 1.0,
            "pressure": 29.92,
            "solar_elevation": 45.0,
        }
        condition = analyzers["core"].determine_condition(sensor_data_windy_cloudy, 0.0)
        assert condition in [
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_PARTLYCLOUDY,
        ]  # Should be cloudy/partly cloudy, NOT windy

        # Windy should apply on sunny days
        sensor_data_windy_sunny = {
            "rain_rate": 0.0,
            "rain_state": "dry",
            "outdoor_temp": 70.0,
            "humidity": 40.0,
            "dewpoint": 40.0,
            "wind_speed": 25.0,  # Strong winds
            "wind_gust": 35.0,
            "solar_radiation": 800.0,  # High solar = sunny
            "solar_lux": 80000.0,
            "uv_index": 8.0,
            "pressure": 30.10,
            "solar_elevation": 60.0,
        }
        # Clear condition and cloud cover history to avoid hysteresis from previous tests
        analyzers["solar"]._condition_history = []
        analyzers["solar"]._sensor_history["cloud_cover"] = deque()
        condition = analyzers["core"].determine_condition(sensor_data_windy_sunny, 0.0)
        assert condition == ATTR_CONDITION_WINDY  # Windy on sunny day

        # Test that cloudy with moderate winds stays cloudy (not windy)
        sensor_data_cloudy_moderate_wind = {
            "rain_rate": 0.0,
            "rain_state": "dry",
            "outdoor_temp": 60.0,
            "humidity": 75.0,
            "dewpoint": 52.0,
            "wind_speed": 15.0,  # Moderate winds (not strong enough)
            "wind_gust": 20.0,
            "solar_radiation": 150.0,  # Moderate solar = cloudy
            "solar_lux": 15000.0,
            "uv_index": 2.0,
            "pressure": 29.80,
            "solar_elevation": 45.0,
        }
        condition = analyzers["core"].determine_condition(
            sensor_data_cloudy_moderate_wind, 0.0
        )
        assert condition in [
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_PARTLYCLOUDY,
        ]  # Should stay cloudy (winds not strong enough)

    def test_determine_condition_with_hysteresis(self, analyzers):
        """Test that determine_weather_condition applies hysteresis correctly."""
        # Mock the cloud cover analysis to return controlled values
        original_analyze_cloud_cover = analyzers["solar"].analyze_cloud_cover

        # First call - establish baseline with sunny condition
        analyzers["solar"].analyze_cloud_cover = (
            lambda *args, **kwargs: 15.0
        )  # Sunny (≤30%)
        condition1 = analyzers["core"].determine_condition(
            {
                "solar_radiation": 800.0,
                "solar_lux": 80000.0,
                "uv_index": 8.0,
                "solar_elevation": 45.0,
            },
            0.0,
        )
        assert condition1 == ATTR_CONDITION_SUNNY

        # Second call - small change to partly cloudy cloud cover
        # This should be rejected by hysteresis (change from 15% to 25% = 10% change, below 15% threshold)
        analyzers["solar"].analyze_cloud_cover = (
            lambda *args, **kwargs: 25.0
        )  # Edge of sunny range
        condition2 = analyzers["core"].determine_condition(
            {
                "solar_radiation": 750.0,  # Slightly less radiation
                "solar_lux": 75000.0,
                "uv_index": 7.5,
                "solar_elevation": 45.0,
            },
            0.0,
        )
        assert (
            condition2 == ATTR_CONDITION_SUNNY
        )  # Should maintain sunny due to hysteresis (10% change < 15% threshold)

        # Third call - significant change that should trigger condition change
        analyzers["solar"].analyze_cloud_cover = (
            lambda *args, **kwargs: 50.0
        )  # Clearly partly cloudy
        condition3 = analyzers["core"].determine_condition(
            {
                "solar_radiation": 500.0,  # Much less radiation
                "solar_lux": 50000.0,
                "uv_index": 5.0,
                "solar_elevation": 45.0,
            },
            0.0,
        )
        assert (
            condition3 == ATTR_CONDITION_PARTLYCLOUDY
        )  # Should allow change due to significant cloud cover increase (50-25=25% > 15%)

        # Restore original method
        analyzers["solar"].analyze_cloud_cover = original_analyze_cloud_cover

    def test_hysteresis_debug_logging(self, analyzers, caplog):
        """Test that hysteresis provides appropriate debug logging."""
        import logging

        # Set up initial history with a sunny condition
        analyzers["solar"]._condition_history.append(
            {"condition": "sunny", "cloud_cover": 20.0, "timestamp": datetime.now()}
        )

        # Enable debug logging
        with caplog.at_level(logging.DEBUG):
            # Trigger hysteresis rejection (small change - 28% vs 20% = 8% change < 15% threshold)
            result = analyzers["solar"].apply_condition_hysteresis(
                ATTR_CONDITION_PARTLYCLOUDY, 28.0
            )

        assert result == ATTR_CONDITION_SUNNY  # Should be rejected
        assert "Condition stable: keeping sunny" in caplog.text
        # The change is 8.0, threshold is 15.0 (sunny -> partlycloudy)
        assert "change: 8.0 < 15.0" in caplog.text

        # Clear log and test acceptance (large change from most recent baseline)
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            result = analyzers["solar"].apply_condition_hysteresis(
                ATTR_CONDITION_PARTLYCLOUDY, 45.0
            )

        assert result == ATTR_CONDITION_PARTLYCLOUDY  # Should be accepted
        assert "Condition change: sunny -> partlycloudy" in caplog.text
        # The change is 17.0 (45 - 28 from previous call), threshold is reduced due to trend

    def test_estimate_visibility_error_handling(self, analyzers):
        """Test visibility estimation with invalid inputs."""
        # Test with extreme values
        sensor_data_extreme = {
            "solar_lux": 150.0,
            "solar_radiation": 110.0,
            "rain_rate": 150.0,
            "wind_speed": -10.0,
            "wind_gust": 200.0,
            "humidity": -100.0,
            "outdoor_temp": 150.0,
        }
        result_extreme = analyzers["core"].estimate_visibility(
            ATTR_CONDITION_SUNNY, sensor_data_extreme
        )
        assert isinstance(
            result_extreme, (int, float)
        )  # Should return a valid visibility

        # Test with invalid temperature differences
        sensor_data_invalid = {
            "solar_lux": 50.0,
            "solar_radiation": 80.0,
            "rain_rate": 30.0,
            "wind_speed": 20.0,
            "wind_gust": 10.0,
            "humidity": 100.0,
            "outdoor_temp": 50.0,  # Dewpoint > temperature scenario
        }
        result_invalid = analyzers["core"].estimate_visibility(
            ATTR_CONDITION_FOG, sensor_data_invalid
        )
        assert isinstance(
            result_invalid, (int, float)
        )  # Should handle invalid dewpoint

    def test_no_fog_at_sunrise_with_normal_solar_for_elevation(
        self, analyzers, mock_sensor_history
    ):
        """Test that fog is not detected at sunrise when solar radiation is normal for the sun angle.

        At low solar elevations (e.g., 6.45° at 7:50 AM), solar radiation is naturally low
        (e.g., 42.9 W/m²) but this is normal for clear conditions at that sun angle.
        The fog check should recognize this as clear sky conditions, not fog.
        """
        # Simulate sunrise conditions: 7:50 AM, low elevation but clear
        sensor_data = {
            "outdoor_temp": 42.0,  # Cool morning
            "humidity": 78.0,  # Moderate humidity (not fog-level)
            "dewpoint": 35.0,  # Spread of 7°F - not very close
            "wind_speed": 0.0,  # Calm
            "wind_gust": 5.0,
            "solar_radiation": 45.0,  # Low but normal for sunrise
            "solar_lux": 5000.0,
            "uv_index": 0.1,
            "rain_rate": 0.0,
            "rain_state": "dry",
            "pressure": 29.92,
            "solar_elevation": 6.5,  # Just after sunrise - low elevation
        }

        # With low elevation (6.5°), clear-sky max is ~50-60 W/m², so 45 W/m² is ~80% of max
        # This should NOT trigger fog since it's consistent with clear-sky at this angle

        # Check that fog is not detected
        result = analyzers["core"].determine_condition(sensor_data, 0.0)

        # Should NOT be fog (likely cloudy or partly cloudy due to low solar, but not fog)
        assert result != ATTR_CONDITION_FOG, (
            f"Expected no fog at sunrise with normal solar radiation for elevation, "
            f"but got {result}"
        )

    def test_fog_still_detected_at_sunrise_when_solar_abnormally_low(
        self, analyzers, mock_sensor_history
    ):
        """Test that fog IS detected when solar radiation is abnormally low for the elevation.

        If solar radiation is much lower than expected for the sun angle (indicating
        something blocking sunlight), fog should still be detected.
        """
        # Simulate sunrise with fog: very low solar for the elevation + high humidity
        sensor_data = {
            "outdoor_temp": 42.0,  # Cool morning
            "humidity": 95.0,  # Very high humidity (fog-like)
            "dewpoint": 40.0,  # Spread of only 2°F - very close (fog condition)
            "wind_speed": 0.0,  # Calm
            "wind_gust": 2.0,
            "solar_radiation": 5.0,  # Much lower than expected for elevation (~10% of max)
            "solar_lux": 500.0,
            "uv_index": 0.0,
            "rain_rate": 0.0,
            "rain_state": "dry",
            "pressure": 29.92,
            "solar_elevation": 6.5,  # Just after sunrise
        }

        # With low elevation, clear-sky max is ~50-60 W/m², so 5 W/m² is only ~10%
        # This SHOULD allow fog detection since solar is abnormally low

        # High humidity + abnormally low solar should trigger fog
        result = analyzers["core"].determine_condition(sensor_data, 0.0)

        # With 95% humidity, 2°F dewpoint spread, and very low solar, fog should be detected
        assert result == ATTR_CONDITION_FOG, (
            f"Expected fog with abnormally low solar radiation and high humidity, "
            f"but got {result}"
        )
