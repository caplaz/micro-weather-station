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

        # Test no solar input (night)
        cloud_cover_night = analysis.analyze_cloud_cover(0.0, 0.0, 0.0)
        assert cloud_cover_night == 100  # Complete overcast assumption

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

    def test_calculate_prevailing_direction(self, analysis):
        """Test prevailing direction calculation."""
        # Test mostly north
        directions_north = [350, 0, 10, 20, 340]
        prevailing = analysis.calculate_prevailing_direction(directions_north)
        assert prevailing == "north"

        # Test mostly east
        directions_east = [80, 90, 100, 70, 110]
        prevailing_east = analysis.calculate_prevailing_direction(directions_east)
        assert prevailing_east == "east"

        # Test empty list
        prevailing_empty = analysis.calculate_prevailing_direction([])
        assert prevailing_empty == "unknown"
