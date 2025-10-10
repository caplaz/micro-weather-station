"""Test the weather analysis functionality."""

from collections import deque
from datetime import datetime, timedelta

from homeassistant.components.weather import (
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
)
import pytest

from custom_components.micro_weather.weather_analysis import WeatherAnalysis


class TestWeatherAnalysis:
    """Test the WeatherAnalysis class."""

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
    def analysis(self, mock_sensor_history):
        """Create WeatherAnalysis instance for testing."""
        return WeatherAnalysis(mock_sensor_history)

    def test_init(self, mock_sensor_history):
        """Test WeatherAnalysis initialization."""
        analysis = WeatherAnalysis(mock_sensor_history)
        assert analysis is not None
        assert analysis._sensor_history == mock_sensor_history

    def test_init_empty_history(self):
        """Test WeatherAnalysis initialization with empty history."""
        analysis = WeatherAnalysis()
        assert analysis is not None
        assert analysis._sensor_history == {}

    def test_calculate_dewpoint(self, analysis):
        """Test dewpoint calculation."""
        # Test standard conditions
        dewpoint = analysis.calculate_dewpoint(72.0, 60.0)  # 72°F, 60% humidity
        assert dewpoint is not None
        assert 50 < dewpoint < 72  # Dewpoint should be between 50°F and air temp

        # Test high humidity
        dewpoint_high = analysis.calculate_dewpoint(70.0, 90.0)
        assert dewpoint_high > dewpoint  # Higher humidity = higher dewpoint

        # Test low humidity
        dewpoint_low = analysis.calculate_dewpoint(70.0, 10.0)
        assert dewpoint_low < dewpoint  # Lower humidity = lower dewpoint

        # Test edge case: very dry air
        dewpoint_dry = analysis.calculate_dewpoint(70.0, 0.0)
        assert (
            dewpoint_dry == 70.0 - 50
        )  # Should return temp - 50 for very dry conditions

    def test_calculate_dewpoint_edge_cases(self, analysis):
        """Test dewpoint calculation edge cases."""
        # Test very high humidity
        dewpoint_100 = analysis.calculate_dewpoint(80.0, 100.0)
        assert abs(dewpoint_100 - 80.0) < 1  # Should be very close to air temperature

        # Test very low temperature
        dewpoint_cold = analysis.calculate_dewpoint(-10.0, 50.0)
        assert dewpoint_cold < -10.0  # Dewpoint should be below air temperature

        # Test very high temperature
        dewpoint_hot = analysis.calculate_dewpoint(120.0, 30.0)
        assert dewpoint_hot < 120.0  # Dewpoint should be below air temperature

        # Test boundary humidity values
        dewpoint_min_humidity = analysis.calculate_dewpoint(70.0, 0.1)
        dewpoint_max_humidity = analysis.calculate_dewpoint(70.0, 99.9)
        assert dewpoint_min_humidity < dewpoint_max_humidity

    def test_classify_precipitation_intensity(self, analysis):
        """Test precipitation intensity classification."""
        assert analysis.classify_precipitation_intensity(0.0) == "trace"
        assert analysis.classify_precipitation_intensity(0.01) == "light"
        assert analysis.classify_precipitation_intensity(0.15) == "moderate"
        assert analysis.classify_precipitation_intensity(0.6) == "heavy"

    def test_analyze_fog_conditions(self, analysis):
        """Test fog condition analysis."""
        # Test clear conditions (no fog)
        result = analysis.analyze_fog_conditions(
            70.0, 50.0, 50.0, 20.0, 5.0, 200.0, True
        )
        assert result is None

        # Test dense fog conditions (nighttime with no solar radiation)
        result_fog = analysis.analyze_fog_conditions(
            70.0, 99.5, 69.9, 0.1, 1.5, 0.0, False
        )
        assert result_fog == ATTR_CONDITION_FOG

        # Test radiation fog (nighttime with no solar radiation)
        result_rad = analysis.analyze_fog_conditions(
            70.0, 99.5, 69.5, 0.5, 2.0, 0.0, False
        )
        assert result_rad == ATTR_CONDITION_FOG

        # Test twilight conditions with high humidity - should NOT be fog
        result_twilight = analysis.analyze_fog_conditions(
            54.0, 99.0, 53.7, 0.3, 1.3, 22.0, False
        )
        assert result_twilight is None  # Twilight with solar radiation = not fog

        # Test extreme fog during twilight (very suppressed solar radiation)
        result_twilight_fog = analysis.analyze_fog_conditions(
            70.0, 99.9, 69.4, 0.1, 1.0, 10.0, False
        )
        assert (
            result_twilight_fog == ATTR_CONDITION_FOG
        )  # Dense fog blocking dawn light

    def test_analyze_cloud_cover(self, analysis):
        """Test cloud cover analysis."""
        # Test clear skies
        cloud_cover = analysis.analyze_cloud_cover(800.0, 80000.0, 8.0)
        assert cloud_cover <= 25  # Should be mostly clear (around 20%)

        # Test cloudy conditions
        cloud_cover_cloudy = analysis.analyze_cloud_cover(50.0, 5000.0, 1.0)
        assert cloud_cover_cloudy > 80  # Should be mostly cloudy

        # Test no solar input (night/heavy overcast)
        cloud_cover_night = analysis.analyze_cloud_cover(0.0, 0.0, 0.0)
        assert cloud_cover_night == 100.0  # No solar input = complete overcast

    def test_analyze_cloud_cover_low_solar_radiation_fallback(self, analysis):
        """Test cloud cover analysis with improved low solar radiation logic."""
        # Test very low solar values (heavy overcast)
        cloud_cover_heavy = analysis.analyze_cloud_cover(20.0, 3000.0, 0.0, 15.0)
        assert cloud_cover_heavy == pytest.approx(
            88.6, abs=0.1
        )  # Astronomical calculation

        # Test moderately low solar values (mostly cloudy)
        cloud_cover_mostly = analysis.analyze_cloud_cover(75.0, 7500.0, 0.5, 15.0)
        assert cloud_cover_mostly == pytest.approx(
            59.8, abs=0.1
        )  # Astronomical calculation (UV ignored due to inconsistency)

        # Test borderline low solar values (partly cloudy fallback)
        cloud_cover_fallback = analysis.analyze_cloud_cover(150.0, 15000.0, 0.8, 20.0)
        assert cloud_cover_fallback == pytest.approx(
            39.1, abs=0.1
        )  # Astronomical calculation (UV ignored due to inconsistency)

        # Test that higher values don't trigger fallback
        cloud_cover_normal = analysis.analyze_cloud_cover(250.0, 25000.0, 2.0, 30.0)
        assert (
            cloud_cover_normal != 40.0
            and cloud_cover_normal != 70.0
            and cloud_cover_normal != 85.0
        )  # Should be calculated normally

    def test_analyze_cloud_cover_elevation_effects(self, analysis):
        """Test cloud cover analysis with different solar elevations."""
        # Test with moderate radiation that shows elevation effects
        cloud_cover_high = analysis.analyze_cloud_cover(
            200.0, 20000.0, 2.0, 80.0
        )  # High elevation
        cloud_cover_low = analysis.analyze_cloud_cover(
            200.0, 20000.0, 2.0, 20.0
        )  # Low elevation

        # With the same actual radiation, lower elevation gives lower cloud cover
        # because the actual radiation represents a higher percentage of the lower max
        assert cloud_cover_low < cloud_cover_high

        # Test very low elevation (near horizon) - may show clear due to algorithm
        cloud_cover_horizon = analysis.analyze_cloud_cover(100.0, 10000.0, 2.0, 5.0)
        assert isinstance(cloud_cover_horizon, float)
        assert 0 <= cloud_cover_horizon <= 100

        # Test zero elevation (should use minimum factor)
        cloud_cover_zero = analysis.analyze_cloud_cover(50.0, 5000.0, 1.0, 0.0)
        assert isinstance(cloud_cover_zero, float)
        assert 0 <= cloud_cover_zero <= 100

    def test_analyze_cloud_cover_seasonal_adjustments(self, analysis):
        """Test cloud cover analysis with different months."""
        # Test that the method runs without error for different months
        import datetime
        from unittest.mock import patch

        # Test winter conditions
        with patch(
            "custom_components.micro_weather.weather_analysis.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime(2024, 1, 15)
            winter_cover = analysis.analyze_cloud_cover(300.0, 30000.0, 3.0, 60.0)

        # Test summer conditions
        with patch(
            "custom_components.micro_weather.weather_analysis.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime(2024, 7, 15)
            summer_cover = analysis.analyze_cloud_cover(300.0, 30000.0, 3.0, 60.0)

        # Both should return valid cloud cover percentages
        assert isinstance(winter_cover, float)
        assert isinstance(summer_cover, float)
        assert 0 <= winter_cover <= 100
        assert 0 <= summer_cover <= 100

    def test_analyze_cloud_cover_measurement_weighting(self, analysis):
        """Test cloud cover analysis measurement weighting logic."""
        # Test primary weighting (solar radiation > 10)
        cloud_cover_primary = analysis.analyze_cloud_cover(500.0, 50000.0, 5.0, 45.0)
        assert isinstance(cloud_cover_primary, float)
        assert 0 <= cloud_cover_primary <= 100

        # Test lux fallback (low radiation, high lux)
        cloud_cover_lux = analysis.analyze_cloud_cover(5.0, 5000.0, 0.5, 45.0)
        assert isinstance(cloud_cover_lux, float)
        assert 0 <= cloud_cover_lux <= 100

        # Test UV fallback (very low radiation and lux, some UV)
        cloud_cover_uv = analysis.analyze_cloud_cover(2.0, 500.0, 1.0, 45.0)
        assert isinstance(cloud_cover_uv, float)
        assert 0 <= cloud_cover_uv <= 100

        # Test mostly cloudy conditions (very low solar measurements)
        # This should use astronomical calculation for very low measurements
        cloud_cover_mostly = analysis.analyze_cloud_cover(1.0, 200.0, 0.2, 45.0)
        assert cloud_cover_mostly == pytest.approx(
            99.5, abs=0.1
        )  # Astronomical calculation

    def test_analyze_cloud_cover_edge_cases(self, analysis):
        """Test cloud cover analysis edge cases."""
        # Clear historical data to avoid averaging effects
        analysis._sensor_history["solar_radiation"] = []

        # Test with zero values (triggers heavy overcast)
        cloud_cover_zero = analysis.analyze_cloud_cover(0.0, 0.0, 0.0, 45.0)
        assert cloud_cover_zero == 100.0  # No solar input = complete overcast

        # Test with very high values (should cap at 0% cloud cover)
        cloud_cover_max = analysis.analyze_cloud_cover(2000.0, 200000.0, 20.0, 90.0)
        assert cloud_cover_max == 0.0  # Completely clear

        # Test with negative values (should be handled gracefully)
        cloud_cover_negative = analysis.analyze_cloud_cover(-10.0, -1000.0, -1.0, 45.0)
        assert isinstance(cloud_cover_negative, float)
        # Should still return a valid percentage

    def test_get_solar_radiation_average(self, analysis):
        """Test solar radiation averaging."""
        # Test with no historical data
        average = analysis._get_solar_radiation_average(100.0)
        assert average == 100.0  # Should return current value

        # Test with insufficient historical data
        analysis._sensor_history["solar_radiation"] = [
            {"timestamp": datetime.now() - timedelta(minutes=5), "value": 90.0},
            {"timestamp": datetime.now() - timedelta(minutes=10), "value": 95.0},
        ]
        average_insufficient = analysis._get_solar_radiation_average(100.0)
        assert average_insufficient == 100.0  # Should return current value

        # Test with sufficient historical data
        analysis._sensor_history["solar_radiation"].extend(
            [
                {"timestamp": datetime.now() - timedelta(minutes=15), "value": 85.0},
                {"timestamp": datetime.now() - timedelta(minutes=20), "value": 80.0},
                {"timestamp": datetime.now() - timedelta(minutes=25), "value": 75.0},
            ]
        )
        average_sufficient = analysis._get_solar_radiation_average(100.0)
        assert isinstance(average_sufficient, float)
        assert average_sufficient > 0

        # Test filtering out zero values
        analysis._sensor_history["solar_radiation"].append(
            {"timestamp": datetime.now() - timedelta(minutes=30), "value": 0.0}
        )
        average_filtered = analysis._get_solar_radiation_average(100.0)
        assert average_filtered > 0  # Should exclude zero values

    def test_get_solar_radiation_average_time_filtering(self, analysis):
        """Test solar radiation averaging with time-based filtering."""
        base_time = datetime.now()

        # Add data from different time periods
        analysis._sensor_history["solar_radiation"] = [
            # Recent data (within 15 minutes)
            {"timestamp": base_time - timedelta(minutes=1), "value": 100.0},
            {"timestamp": base_time - timedelta(minutes=5), "value": 110.0},
            {"timestamp": base_time - timedelta(minutes=10), "value": 105.0},
            {"timestamp": base_time - timedelta(minutes=14), "value": 95.0},
            # Older data (beyond 15 minutes)
            {"timestamp": base_time - timedelta(minutes=20), "value": 120.0},
            {"timestamp": base_time - timedelta(minutes=30), "value": 130.0},
        ]

        average = analysis._get_solar_radiation_average(108.0)
        assert isinstance(average, float)

        # Should only consider recent readings (within 15 minutes)
        # Expected: weighted average of [100, 110, 105, 95] with current 108
        recent_values = [100.0, 110.0, 105.0, 95.0, 108.0]
        expected_avg = sum(recent_values) / len(
            recent_values
        )  # Simple average for test
        assert (
            abs(average - expected_avg) < 5.0
        )  # Should be close to recent data average

    def test_estimate_visibility(self, analysis):
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
        visibility_clear = analysis.estimate_visibility(
            ATTR_CONDITION_SUNNY, sensor_data
        )
        assert visibility_clear > 20  # Good visibility

        # Test foggy conditions
        visibility_fog = analysis.estimate_visibility(ATTR_CONDITION_FOG, sensor_data)
        assert visibility_fog < 10  # Poor visibility

        # Test rainy conditions
        sensor_data_rain = sensor_data.copy()
        sensor_data_rain["rain_rate"] = 0.2
        visibility_rain = analysis.estimate_visibility(
            ATTR_CONDITION_RAINY, sensor_data_rain
        )
        assert visibility_rain < 20  # Reduced visibility

    def test_store_historical_data(self, analysis, mock_sensor_history):
        """Test storing historical sensor data."""
        sensor_data = {
            "outdoor_temp": 75.0,
            "humidity": 65.0,
            "pressure": 29.90,
        }

        initial_temp_count = len(mock_sensor_history["outdoor_temp"])
        analysis.store_historical_data(sensor_data)

        # Check that data was added
        assert len(mock_sensor_history["outdoor_temp"]) == initial_temp_count + 1
        assert len(mock_sensor_history["humidity"]) == initial_temp_count + 1
        assert len(mock_sensor_history["pressure"]) == initial_temp_count + 1

        # Check that the latest entry has correct data
        latest_temp = mock_sensor_history["outdoor_temp"][-1]
        assert latest_temp["value"] == 75.0
        assert isinstance(latest_temp["timestamp"], datetime)

    def test_get_historical_trends(self, analysis, mock_sensor_history):
        """Test historical trend calculation."""
        # Test with existing data
        trends = analysis.get_historical_trends("outdoor_temp", hours=24)
        assert trends is not None
        assert "current" in trends
        assert "average" in trends
        assert "trend" in trends
        assert "min" in trends
        assert "max" in trends
        assert "volatility" in trends

        # Test with non-existent sensor
        trends_none = analysis.get_historical_trends("nonexistent_sensor")
        assert trends_none == {}

        # Test with insufficient data
        empty_history = {"test_sensor": deque(maxlen=192)}
        analysis_empty = WeatherAnalysis(empty_history)
        trends_empty = analysis_empty.get_historical_trends("test_sensor")
        assert trends_empty == {}

    def test_calculate_trend(self, analysis):
        """Test trend calculation (linear regression)."""
        # Test with simple data
        x_values = [0, 1, 2, 3, 4]
        y_values = [0, 1, 2, 3, 4]  # Perfect positive correlation
        trend = analysis.calculate_trend(x_values, y_values)
        assert abs(trend - 1.0) < 0.01  # Should be slope of 1

        # Test with negative trend
        y_values_neg = [4, 3, 2, 1, 0]
        trend_neg = analysis.calculate_trend(x_values, y_values_neg)
        assert abs(trend_neg - (-1.0)) < 0.01  # Should be slope of -1

        # Test with no trend (horizontal line)
        y_values_flat = [5, 5, 5, 5, 5]
        trend_flat = analysis.calculate_trend(x_values, y_values_flat)
        assert abs(trend_flat) < 0.01  # Should be slope of 0

        # Test edge cases
        trend_empty = analysis.calculate_trend([], [])
        assert trend_empty == 0.0

        trend_single = analysis.calculate_trend([1], [1])
        assert trend_single == 0.0

    def test_analyze_pressure_trends(self, analysis):
        """Test pressure trend analysis."""
        pressure_analysis = analysis.analyze_pressure_trends()
        assert isinstance(pressure_analysis, dict)
        assert "pressure_system" in pressure_analysis
        assert "storm_probability" in pressure_analysis

        # Should have valid pressure system classification
        assert pressure_analysis["pressure_system"] in [
            "high_pressure",
            "low_pressure",
            "normal",
            "unknown",
        ]

        # Storm probability should be between 0 and 100
        assert 0 <= pressure_analysis["storm_probability"] <= 100

    def test_analyze_wind_direction_trends(self, analysis):
        """Test wind direction trend analysis."""
        wind_analysis = analysis.analyze_wind_direction_trends()
        assert isinstance(wind_analysis, dict)

        expected_keys = [
            "average_direction",
            "direction_stability",
            "direction_change_rate",
            "significant_shift",
            "prevailing_direction",
        ]
        for key in expected_keys:
            assert key in wind_analysis

        # Direction stability should be between 0 and 1
        assert 0 <= wind_analysis["direction_stability"] <= 1

        # Prevailing direction should be a cardinal direction or unknown
        assert wind_analysis["prevailing_direction"] in [
            "north",
            "east",
            "south",
            "west",
            "unknown",
        ]

    def test_calculate_circular_mean(self, analysis):
        """Test circular mean calculation for wind directions."""
        # Test with simple directions
        directions = [0, 90, 180, 270]  # All cardinal directions
        mean = analysis.calculate_circular_mean(directions)
        # Should average to some value, but exact value depends on implementation
        assert isinstance(mean, float)
        assert 0 <= mean < 360

        # Test with concentrated directions (mostly north)
        directions_north = [350, 10, 20, 340]  # Mostly north
        mean_north = analysis.calculate_circular_mean(directions_north)
        # Should be around north (0°), but could be around 360° which is equivalent
        assert mean_north >= 350 or mean_north <= 20  # Around north

        # Test empty list
        mean_empty = analysis.calculate_circular_mean([])
        assert mean_empty == 0.0

    def test_calculate_angular_difference(self, analysis):
        """Test angular difference calculation."""
        # Test same direction
        diff_same = analysis.calculate_angular_difference(90, 90)
        assert diff_same == 0

        # Test opposite directions
        diff_opposite = analysis.calculate_angular_difference(0, 180)
        assert abs(diff_opposite) == 180

        # Test small difference
        diff_small = analysis.calculate_angular_difference(10, 20)
        assert diff_small == 10

        # Test wraparound
        diff_wrap = analysis.calculate_angular_difference(350, 10)
        assert diff_wrap == 20  # 350 to 10 is 20° clockwise

    def test_analyze_fog_conditions_error_handling(self, analysis):
        """Test fog condition analysis with invalid inputs."""
        # Test with extreme values
        result_extreme = analysis.analyze_fog_conditions(
            150.0, 110.0, 150.0, -10.0, 200.0, -100.0, True
        )
        assert isinstance(
            result_extreme, (str, type(None))
        )  # Should return a valid condition or None

        # Test with invalid temperature differences
        result_invalid = analysis.analyze_fog_conditions(
            50.0, 80.0, 30.0, 20.0, 10.0, 100.0, True  # Dewpoint > temperature
        )
        assert isinstance(
            result_invalid, (str, type(None))
        )  # Should handle invalid dewpoint

    def test_estimate_visibility_error_handling(self, analysis):
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
        result_extreme = analysis.estimate_visibility(
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
        result_invalid = analysis.estimate_visibility(
            ATTR_CONDITION_FOG, sensor_data_invalid
        )
        assert isinstance(
            result_invalid, (int, float)
        )  # Should handle invalid dewpoint

    def test_get_historical_trends_error_handling(self, analysis):
        """Test historical trends with error conditions."""
        # Test with future timestamps
        future_time = datetime.now() + timedelta(hours=1)
        analysis._sensor_history["future_sensor"] = [
            {"timestamp": future_time, "value": 100.0},
        ]

        trends_future = analysis.get_historical_trends("future_sensor")
        assert trends_future == {}  # Should exclude future data

    def test_calculate_trend_error_handling(self, analysis):
        """Test trend calculation error handling."""
        # Test with empty lists
        trend_empty = analysis.calculate_trend([], [])
        assert trend_empty == 0.0

        # Test with mismatched lengths
        trend_mismatch = analysis.calculate_trend([1, 2], [1])
        assert trend_mismatch == 0.0

        # Test with single points
        trend_single = analysis.calculate_trend([1], [1])
        assert trend_single == 0.0

        # Test with constant values (zero variance)
        trend_constant = analysis.calculate_trend([1, 2, 3], [5, 5, 5])
        assert trend_constant == 0.0

    def test_analyze_pressure_trends_error_handling(self, analysis):
        """Test pressure trend analysis error handling."""
        # Test with empty history
        analysis._sensor_history = {}  # Clear history

        pressure_analysis = analysis.analyze_pressure_trends()
        assert pressure_analysis["pressure_system"] == "unknown"
        assert pressure_analysis["storm_probability"] == 0.0

        # Test with insufficient data
        analysis._sensor_history["pressure"] = [
            {"timestamp": datetime.now(), "value": 29.92}
        ]

        pressure_analysis_short = analysis.analyze_pressure_trends()
        assert pressure_analysis_short["pressure_system"] == "unknown"
        assert pressure_analysis_short["storm_probability"] == 0.0

    def test_analyze_wind_direction_trends_error_handling(self, analysis):
        """Test wind direction trend analysis error handling."""
        # Test with empty history
        analysis._sensor_history = {}

        wind_analysis = analysis.analyze_wind_direction_trends()
        assert wind_analysis["average_direction"] is None
        assert wind_analysis["direction_stability"] == 0.0
        assert wind_analysis["significant_shift"] is False

        # Test with invalid direction values
        analysis._sensor_history["wind_direction"] = [
            {"timestamp": datetime.now(), "value": 400.0},  # Invalid direction > 360
            {
                "timestamp": datetime.now() - timedelta(hours=1),
                "value": -50.0,
            },  # Invalid negative
        ]

        wind_analysis_invalid = analysis.analyze_wind_direction_trends()
        assert isinstance(
            wind_analysis_invalid["average_direction"], (float, type(None))
        )

    def test_calculate_circular_mean_error_handling(self, analysis):
        """Test circular mean calculation error handling."""
        # Test with empty list
        mean_empty = analysis.calculate_circular_mean([])
        assert mean_empty == 0.0

        # Test with invalid values (should filter out invalid ones)
        mean_invalid = analysis.calculate_circular_mean([400, -50, 90, 180])
        assert isinstance(mean_invalid, float)
        assert 0 <= mean_invalid < 360

        # Test with extreme values
        mean_extreme = analysis.calculate_circular_mean(
            [0, 720, 1080, 90]
        )  # Multiples of 360
        assert isinstance(mean_extreme, float)

    def test_calculate_prevailing_direction_error_handling(self, analysis):
        """Test prevailing direction calculation error handling."""
        # Test with empty list
        direction_empty = analysis.calculate_prevailing_direction([])
        assert direction_empty == "unknown"

        # Test with invalid values (should filter out invalid ones)
        direction_invalid = analysis.calculate_prevailing_direction([400, -50, 90, 180])
        assert direction_invalid in ["north", "east", "south", "west", "unknown"]

        # Test with boundary values
        direction_boundary = analysis.calculate_prevailing_direction([0, 360, 359.9])
        assert direction_boundary == "north"  # All should map to north sector

    def test_calculate_clear_sky_max_radiation(self, analysis):
        """Test clear-sky maximum radiation calculation."""
        # Test at zenith (90° elevation)
        max_rad_zenith = analysis._calculate_clear_sky_max_radiation(90.0)
        assert isinstance(max_rad_zenith, float)
        assert 600 < max_rad_zenith < 1200  # Should be in reasonable range

        # Test at moderate elevation (45°)
        max_rad_45 = analysis._calculate_clear_sky_max_radiation(45.0)
        assert isinstance(max_rad_45, float)
        assert 200 < max_rad_45 < 600  # Should be lower than zenith

        # Test at low elevation (20°)
        max_rad_20 = analysis._calculate_clear_sky_max_radiation(20.0)
        assert isinstance(max_rad_20, float)
        assert 50 < max_rad_20 < 300  # Should be much lower

        # Test at horizon (0° elevation)
        max_rad_0 = analysis._calculate_clear_sky_max_radiation(0.0)
        assert max_rad_0 == 50.0  # Should return minimum value

        # Test below horizon (negative elevation)
        max_rad_negative = analysis._calculate_clear_sky_max_radiation(-10.0)
        assert max_rad_negative == 50.0  # Should return minimum value

        # Test that higher elevation gives higher radiation
        assert max_rad_zenith > max_rad_45 > max_rad_20

    def test_calculate_clear_sky_max_radiation_seasonal_variations(self, analysis):
        """Test seasonal variations in clear-sky radiation calculation."""
        import datetime

        # Test winter conditions (higher solar constant due to closer Earth-Sun distance)
        winter_rad = analysis._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 1, 4)
        )
        print(f"Winter radiation: {winter_rad}")

        # Test summer conditions (lower solar constant due to farther Earth-Sun distance)
        summer_rad = analysis._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 7, 4)
        )
        print(f"Summer radiation: {summer_rad}")

        # Winter (perihelion) should have higher radiation due to closer distance to sun
        assert winter_rad > summer_rad

        # Check that the difference is meaningful (should be several W/m²)
        assert winter_rad - summer_rad > 10

    def test_calculate_clear_sky_max_radiation_bounds(self, analysis):
        """Test bounds checking in clear-sky radiation calculation."""
        # Test that very high elevations don't exceed maximum
        max_rad_high = analysis._calculate_clear_sky_max_radiation(85.0)
        assert max_rad_high <= 1200.0  # Should be capped at maximum

        # Test that very low elevations don't go below minimum
        max_rad_low = analysis._calculate_clear_sky_max_radiation(1.0)
        assert max_rad_low >= 50.0  # Should be floored at minimum

    def test_calculate_air_mass(self, analysis):
        """Test air mass calculation."""
        # Test at zenith (90° elevation)
        air_mass_zenith = analysis._calculate_air_mass(90.0)
        assert abs(air_mass_zenith - 1.0) < 0.01  # Should be very close to 1.0

        # Test at moderate elevation (45°)
        air_mass_45 = analysis._calculate_air_mass(45.0)
        assert 1.4 < air_mass_45 < 1.5  # Should be around 1.41

        # Test at low elevation (20°)
        air_mass_20 = analysis._calculate_air_mass(20.0)
        assert 2.8 < air_mass_20 < 3.0  # Should be around 2.9

        # Test at very low elevation (5°)
        air_mass_5 = analysis._calculate_air_mass(5.0)
        assert 10 < air_mass_5 < 15  # Should be high air mass

        # Test below horizon
        air_mass_negative = analysis._calculate_air_mass(-10.0)
        assert air_mass_negative == 38.0  # Should return maximum air mass

        # Test that air mass increases as elevation decreases
        assert air_mass_zenith < air_mass_45 < air_mass_20 < air_mass_5

    def test_calculate_air_mass_edge_cases(self, analysis):
        """Test air mass calculation edge cases."""
        # Test at exactly 0° elevation
        air_mass_zero = analysis._calculate_air_mass(0.0)
        assert air_mass_zero == 38.0  # Should return maximum air mass

        # Test at very high elevation (near zenith)
        air_mass_89 = analysis._calculate_air_mass(89.0)
        assert 1.0 <= air_mass_89 < 1.01  # Should be very close to 1.0

        # Test boundary values
        air_mass_90 = analysis._calculate_air_mass(90.0)
        assert abs(air_mass_90 - 1.0) < 0.01

        air_mass_1 = analysis._calculate_air_mass(1.0)
        assert air_mass_1 > 20  # Should be very high

    def test_calculate_air_mass_kasten_young_formula(self, analysis):
        """Test that air mass uses Kasten-Young formula correctly."""
        # Test specific values to verify Kasten-Young implementation
        # At 45° elevation, air mass should be approximately 1.41
        air_mass_45 = analysis._calculate_air_mass(45.0)
        expected_45 = 1.0 / (
            0.7071067811865476 + 0.50572 * (96.07995 - 45.0) ** (-1.6364)
        )  # Manual calculation
        assert abs(air_mass_45 - expected_45) < 0.01

        # At 30° elevation, air mass should be approximately 1.99
        air_mass_30 = analysis._calculate_air_mass(30.0)
        expected_30 = 1.0 / (
            0.5 + 0.50572 * (96.07995 - 30.0) ** (-1.6364)
        )  # Manual calculation
        assert abs(air_mass_30 - expected_30) < 0.01

    def test_clear_sky_radiation_integration_with_cloud_cover(self, analysis):
        """Test integration between clear-sky radiation and cloud cover analysis."""
        # Test that clear-sky radiation affects cloud cover calculation
        # Same actual radiation at different elevations should give different cloud cover

        # At high elevation (higher clear-sky max)
        cloud_cover_high = analysis.analyze_cloud_cover(300.0, 30000.0, 3.0, 80.0)
        # At low elevation (lower clear-sky max)
        cloud_cover_low = analysis.analyze_cloud_cover(300.0, 30000.0, 3.0, 30.0)

        # Same actual radiation should give lower cloud cover percentage at lower elevation
        # because the clear-sky maximum is lower, so actual radiation represents
        # higher percentage of max
        assert cloud_cover_low < cloud_cover_high

        # Test extreme case: very low elevation
        cloud_cover_very_low = analysis.analyze_cloud_cover(200.0, 20000.0, 2.0, 10.0)
        assert isinstance(cloud_cover_very_low, float)
        assert 0 <= cloud_cover_very_low <= 100

    def test_astronomical_calculations_with_different_dates(self, analysis):
        """Test astronomical calculations vary correctly with date."""
        import datetime

        # Test perihelion (closest to sun, highest radiation)
        rad_perihelion = analysis._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 1, 4)
        )

        # Test aphelion (farthest from sun, lowest radiation)
        rad_aphelion = analysis._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 7, 4)
        )

        # Perihelion should have higher radiation
        assert rad_perihelion > rad_aphelion

        # Test equinoxes (intermediate radiation)
        rad_spring = analysis._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 3, 20)
        )

        rad_fall = analysis._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 9, 22)
        )

        # Equinoxes should be between perihelion and aphelion
        assert rad_aphelion < rad_spring < rad_perihelion
        assert rad_aphelion < rad_fall < rad_perihelion

    def test_apply_condition_hysteresis_no_history(self, analysis):
        """Test hysteresis with no previous condition history."""
        # First call should always return the proposed condition
        result = analysis._apply_condition_hysteresis("sunny", 25.0)
        assert result == "sunny"

        # Check that history was initialized
        assert len(analysis._condition_history) == 1
        assert analysis._condition_history[0]["condition"] == "sunny"
        assert analysis._condition_history[0]["cloud_cover"] == 25.0

    def test_apply_condition_hysteresis_same_condition(self, analysis):
        """Test hysteresis when proposed condition is same as previous."""
        # Set up initial history
        analysis._condition_history.append(
            {"condition": "sunny", "cloud_cover": 25.0, "timestamp": datetime.now()}
        )

        # Same condition should be returned immediately
        result = analysis._apply_condition_hysteresis("sunny", 30.0)
        assert result == "sunny"

        # History should be updated
        assert len(analysis._condition_history) == 2
        assert analysis._condition_history[-1]["condition"] == "sunny"
        assert analysis._condition_history[-1]["cloud_cover"] == 30.0

    def test_apply_condition_hysteresis_sunny_to_partlycloudy_below_threshold(
        self, analysis
    ):
        """Test hysteresis prevents sunny to partlycloudy when change is too small."""
        # Set up initial history with sunny condition
        analysis._condition_history.append(
            {"condition": "sunny", "cloud_cover": 35.0, "timestamp": datetime.now()}
        )

        # Try to change to partlycloudy with small cloud cover increase (only 5%)
        # Threshold is 15%, so this should be rejected
        result = analysis._apply_condition_hysteresis("partlycloudy", 40.0)
        assert result == "sunny"  # Should maintain previous condition

        # History should record the rejected change attempt
        assert len(analysis._condition_history) == 2
        assert (
            analysis._condition_history[-1]["condition"] == "sunny"
        )  # Kept old condition
        assert (
            analysis._condition_history[-1]["cloud_cover"] == 40.0
        )  # Recorded new cloud cover

    def test_apply_condition_hysteresis_sunny_to_partlycloudy_above_threshold(
        self, analysis
    ):
        """Test hysteresis allows sunny to partlycloudy when change exceeds threshold."""
        # Set up initial history with sunny condition
        analysis._condition_history.append(
            {"condition": "sunny", "cloud_cover": 30.0, "timestamp": datetime.now()}
        )

        # Try to change to partlycloudy with significant cloud cover increase (20%)
        # Threshold is 15%, so this should be allowed
        result = analysis._apply_condition_hysteresis("partlycloudy", 50.0)
        assert result == "partlycloudy"  # Should allow the change

        # History should record the successful change
        assert len(analysis._condition_history) == 2
        assert analysis._condition_history[-1]["condition"] == "partlycloudy"
        assert analysis._condition_history[-1]["cloud_cover"] == 50.0

    def test_apply_condition_hysteresis_partlycloudy_to_sunny_below_threshold(
        self, analysis
    ):
        """Test hysteresis prevents partlycloudy to sunny when change is too small."""
        # Set up initial history with partlycloudy condition
        analysis._condition_history.append(
            {
                "condition": "partlycloudy",
                "cloud_cover": 45.0,
                "timestamp": datetime.now(),
            }
        )

        # Try to change to sunny with small cloud cover decrease (only 8%)
        # Threshold is 15%, so this should be rejected
        result = analysis._apply_condition_hysteresis("sunny", 37.0)
        assert result == "partlycloudy"  # Should maintain previous condition

    def test_apply_condition_hysteresis_partlycloudy_to_sunny_above_threshold(
        self, analysis
    ):
        """Test hysteresis allows partlycloudy to sunny when change exceeds threshold."""
        # Set up initial history with partlycloudy condition
        analysis._condition_history.append(
            {
                "condition": "partlycloudy",
                "cloud_cover": 50.0,
                "timestamp": datetime.now(),
            }
        )

        # Try to change to sunny with significant cloud cover decrease (25%)
        # Threshold is 15%, so this should be allowed
        result = analysis._apply_condition_hysteresis("sunny", 25.0)
        assert result == "sunny"  # Should allow the change

    def test_apply_condition_hysteresis_partlycloudy_to_cloudy_above_threshold(
        self, analysis
    ):
        """Test hysteresis for partlycloudy to cloudy transition."""
        # Set up initial history with partlycloudy condition
        analysis._condition_history.append(
            {
                "condition": "partlycloudy",
                "cloud_cover": 50.0,
                "timestamp": datetime.now(),
            }
        )

        # Try to change to cloudy with moderate cloud cover increase (15%)
        # Threshold for partlycloudy->cloudy is 10%, so this should be allowed
        result = analysis._apply_condition_hysteresis("cloudy", 65.0)
        assert result == "cloudy"  # Should allow the change

    def test_apply_condition_hysteresis_cloudy_to_partlycloudy_below_threshold(
        self, analysis
    ):
        """Test hysteresis prevents cloudy to partlycloudy when change is too small."""
        # Set up initial history with cloudy condition
        analysis._condition_history.append(
            {"condition": "cloudy", "cloud_cover": 70.0, "timestamp": datetime.now()}
        )

        # Try to change to partlycloudy with small cloud cover decrease (only 5%)
        # Threshold is 10%, so this should be rejected
        result = analysis._apply_condition_hysteresis("partlycloudy", 65.0)
        assert result == "cloudy"  # Should maintain previous condition

    def test_apply_condition_hysteresis_unknown_transition(self, analysis):
        """Test hysteresis with unknown transition (uses default threshold)."""
        # Set up initial history
        analysis._condition_history.append(
            {"condition": "sunny", "cloud_cover": 20.0, "timestamp": datetime.now()}
        )

        # Try a transition that doesn't have a specific threshold (should use 5% default)
        # First try with change below default threshold
        result = analysis._apply_condition_hysteresis("cloudy", 23.0)  # Only 3% change
        assert result == "sunny"  # Should be rejected due to low threshold

        # Now try with change above default threshold from the original baseline
        # Since hysteresis uses the most recent history entry, we need a bigger change
        result = analysis._apply_condition_hysteresis(
            "cloudy", 28.0
        )  # 8% change from last (23.0)
        assert result == "cloudy"  # Should be allowed

    def test_apply_condition_hysteresis_history_limit(self, analysis):
        """Test that condition history is properly managed with time-based cleanup."""
        from datetime import timedelta

        # Add entries spanning more than 24 hours
        base_time = datetime.now()
        for i in range(15):
            # Spread entries over 30 hours (some will be old, some recent)
            timestamp = base_time - timedelta(
                hours=30 - i * 2
            )  # 0, 2, 4, ..., 28 hours ago
            analysis._condition_history.append(
                {"condition": "sunny", "cloud_cover": 25.0 + i, "timestamp": timestamp}
            )

        # Before cleanup, should have all 15 entries
        assert len(analysis._condition_history) == 15

        # Trigger cleanup by calling hysteresis (which does cleanup)
        analysis._apply_condition_hysteresis("sunny", 25.0)

        # After cleanup, should only have entries from last 24 hours
        # (entries from 0-22 hours ago = 12 entries)
        assert len(analysis._condition_history) <= 12  # Should be cleaned up

        # All remaining entries should be within 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        for entry in analysis._condition_history:
            assert entry["timestamp"] > cutoff_time

        # The most recent entries should be preserved
        # (entries from most recent timestamps should be there)
        recent_entries = [
            entry
            for entry in analysis._condition_history
            if entry["timestamp"] > base_time - timedelta(hours=24)
        ]
        assert len(recent_entries) > 0

    def test_determine_weather_condition_with_hysteresis(self, analysis):
        """Test that determine_weather_condition applies hysteresis correctly."""
        # Mock the cloud cover analysis to return controlled values
        original_analyze_cloud_cover = analysis.analyze_cloud_cover

        # First call - establish baseline with sunny condition
        analysis.analyze_cloud_cover = lambda *args, **kwargs: 20.0  # Sunny (≤25%)
        condition1 = analysis.determine_weather_condition(
            {
                "solar_radiation": 800.0,
                "solar_lux": 80000.0,
                "uv_index": 8.0,
                "solar_elevation": 45.0,
            },
            0.0,
        )
        assert condition1 == "sunny"

        # Second call - small change to partly cloudy cloud cover
        # This should be rejected by hysteresis (change from 20% to 28% = 8% change, below 10% threshold)
        analysis.analyze_cloud_cover = (
            lambda *args, **kwargs: 28.0
        )  # Partly cloudy range (25-50%)
        condition2 = analysis.determine_weather_condition(
            {
                "solar_radiation": 750.0,  # Slightly less radiation
                "solar_lux": 75000.0,
                "uv_index": 7.5,
                "solar_elevation": 45.0,
            },
            0.0,
        )
        assert (
            condition2 == "sunny"
        )  # Should maintain sunny due to hysteresis (8% change < 10% threshold)

        # Third call - significant change that should trigger condition change
        analysis.analyze_cloud_cover = (
            lambda *args, **kwargs: 45.0
        )  # Still partly cloudy
        condition3 = analysis.determine_weather_condition(
            {
                "solar_radiation": 600.0,  # Much less radiation
                "solar_lux": 60000.0,
                "uv_index": 6.0,
                "solar_elevation": 45.0,
            },
            0.0,
        )
        assert (
            condition3 == "partlycloudy"
        )  # Should allow change due to significant cloud cover increase (45-28=17% > 10%)

        # Restore original method
        analysis.analyze_cloud_cover = original_analyze_cloud_cover

    def test_hysteresis_debug_logging(self, analysis, caplog):
        """Test that hysteresis provides appropriate debug logging."""
        import logging

        # Set up initial history
        analysis._condition_history.append(
            {"condition": "sunny", "cloud_cover": 30.0, "timestamp": datetime.now()}
        )

        # Enable debug logging
        with caplog.at_level(logging.DEBUG):
            # Trigger hysteresis rejection (small change)
            result = analysis._apply_condition_hysteresis("partlycloudy", 35.0)

        assert result == "sunny"  # Should be rejected
        assert "Condition stable: keeping sunny" in caplog.text
        assert "change: 5.0 < threshold: 10.0" in caplog.text

        # Clear log and test acceptance (large change from most recent baseline)
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            result = analysis._apply_condition_hysteresis("partlycloudy", 45.0)

        assert result == "partlycloudy"  # Should be accepted
        assert "Condition change: sunny -> partlycloudy" in caplog.text
        assert "change: 10.0 >= threshold: 10.0" in caplog.text
