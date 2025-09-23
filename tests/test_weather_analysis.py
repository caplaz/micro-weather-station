"""Test the weather analysis functionality."""

from collections import deque
from datetime import datetime, timedelta

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
        assert result == "none"

        # Test dense fog conditions
        result_fog = analysis.analyze_fog_conditions(
            70.0, 99.0, 69.0, 1.0, 2.0, 5.0, True
        )
        assert result_fog == "foggy"

        # Test radiation fog
        result_rad = analysis.analyze_fog_conditions(
            70.0, 98.0, 68.0, 2.0, 2.0, 5.0, False
        )
        assert result_rad == "foggy"

    def test_analyze_cloud_cover(self, analysis):
        """Test cloud cover analysis."""
        # Test clear skies
        cloud_cover = analysis.analyze_cloud_cover(800.0, 80000.0, 8.0)
        assert cloud_cover <= 25  # Should be mostly clear (around 20%)

        # Test cloudy conditions
        cloud_cover_cloudy = analysis.analyze_cloud_cover(50.0, 5000.0, 1.0)
        assert cloud_cover_cloudy > 80  # Should be mostly cloudy

        # Test no solar input (night/inconclusive)
        cloud_cover_night = analysis.analyze_cloud_cover(0.0, 0.0, 0.0)
        assert cloud_cover_night == 40.0  # Inconclusive solar data = partly cloudy

    def test_analyze_cloud_cover_low_solar_radiation_fallback(self, analysis):
        """Test cloud cover analysis with low solar radiation fallback."""
        # Test the specific case from user's sensor data
        # Low solar radiation but clear conditions should return 40% (partly cloudy)
        cloud_cover = analysis.analyze_cloud_cover(26.0, 15000.0, 0.5, 15.0)
        assert cloud_cover == 40.0  # Fallback for inconclusive solar data

        # Test various combinations that trigger fallback
        assert analysis.analyze_cloud_cover(150.0, 18000.0, 0.8, 20.0) == 40.0
        assert analysis.analyze_cloud_cover(180.0, 19000.0, 0.9, 25.0) == 40.0

        # Test that higher values don't trigger fallback
        cloud_cover_normal = analysis.analyze_cloud_cover(250.0, 25000.0, 2.0, 30.0)
        assert cloud_cover_normal != 40.0  # Should not be fallback value

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
        """Test cloud cover analysis with seasonal variations."""
        # Test that seasonal factors are applied (simplified test)
        # Just verify the method runs without error for different months
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

        # Test unknown fallback (measurements very low but not triggering special case)
        # This should trigger the 40.0 fallback for inconclusive solar data
        cloud_cover_unknown = analysis.analyze_cloud_cover(1.0, 200.0, 0.2, 45.0)
        assert cloud_cover_unknown == 40.0  # Fallback for inconclusive data

    def test_analyze_cloud_cover_edge_cases(self, analysis):
        """Test cloud cover analysis edge cases."""
        # Clear historical data to avoid averaging effects
        analysis._sensor_history["solar_radiation"] = []

        # Test with zero values (triggers inconclusive fallback)
        cloud_cover_zero = analysis.analyze_cloud_cover(0.0, 0.0, 0.0, 45.0)
        assert cloud_cover_zero == 40.0  # Inconclusive solar data = partly cloudy

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
        visibility_clear = analysis.estimate_visibility("sunny", sensor_data)
        assert visibility_clear > 20  # Good visibility

        # Test foggy conditions
        visibility_fog = analysis.estimate_visibility("foggy", sensor_data)
        assert visibility_fog < 10  # Poor visibility

        # Test rainy conditions
        sensor_data_rain = sensor_data.copy()
        sensor_data_rain["rain_rate"] = 0.2
        visibility_rain = analysis.estimate_visibility("rainy", sensor_data_rain)
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
        assert isinstance(result_extreme, str)  # Should return a valid condition

        # Test with invalid temperature differences
        result_invalid = analysis.analyze_fog_conditions(
            50.0, 80.0, 30.0, 20.0, 10.0, 100.0, True  # Dewpoint > temperature
        )
        assert isinstance(result_invalid, str)  # Should handle invalid dewpoint

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
        result_extreme = analysis.estimate_visibility("sunny", sensor_data_extreme)
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
        result_invalid = analysis.estimate_visibility("foggy", sensor_data_invalid)
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
