"""Test the trends analysis functionality."""

from collections import deque
from datetime import datetime, timedelta

import pytest

from custom_components.micro_weather.analysis.trends import TrendsAnalyzer


class TestTrendsAnalyzer:
    """Test the TrendsAnalyzer class."""

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
    def analyzer(self, mock_sensor_history):
        """Create TrendsAnalyzer instance for testing."""
        return TrendsAnalyzer(mock_sensor_history)

    def test_store_historical_data(self, analyzer, mock_sensor_history):
        """Test storing historical sensor data."""
        sensor_data = {
            "outdoor_temp": 75.0,
            "humidity": 65.0,
            "pressure": 29.90,
        }

        initial_temp_count = len(mock_sensor_history["outdoor_temp"])
        analyzer.store_historical_data(sensor_data)

        # Check that data was added
        assert len(mock_sensor_history["outdoor_temp"]) == initial_temp_count + 1
        assert len(mock_sensor_history["humidity"]) == initial_temp_count + 1
        assert len(mock_sensor_history["pressure"]) == initial_temp_count + 1

        # Check that the latest entry has correct data
        latest_temp = mock_sensor_history["outdoor_temp"][-1]
        assert latest_temp["value"] == 75.0
        assert isinstance(latest_temp["timestamp"], datetime)

    def test_get_historical_trends(self, analyzer, mock_sensor_history):
        """Test historical trend calculation."""
        # Test with existing data
        trends = analyzer.get_historical_trends("outdoor_temp", hours=24)
        assert trends is not None
        assert "current" in trends
        assert "average" in trends
        assert "trend" in trends
        assert "min" in trends
        assert "max" in trends
        assert "volatility" in trends

        # Test with non-existent sensor
        trends_none = analyzer.get_historical_trends("nonexistent_sensor")
        assert trends_none == {}

        # Test with insufficient data
        empty_history = {"test_sensor": deque(maxlen=192)}
        analyzer_empty = TrendsAnalyzer(empty_history)
        trends_empty = analyzer_empty.get_historical_trends("test_sensor")
        assert trends_empty == {}

    def test_calculate_trend(self, analyzer):
        """Test trend calculation (linear regression)."""
        # Test with simple data
        x_values = [0, 1, 2, 3, 4]
        y_values = [0, 1, 2, 3, 4]  # Perfect positive correlation
        trend = analyzer.calculate_trend(x_values, y_values)
        assert abs(trend - 1.0) < 0.01  # Should be slope of 1

        # Test with negative trend
        y_values_neg = [4, 3, 2, 1, 0]
        trend_neg = analyzer.calculate_trend(x_values, y_values_neg)
        assert abs(trend_neg - (-1.0)) < 0.01  # Should be slope of -1

        # Test with no trend (horizontal line)
        y_values_flat = [5, 5, 5, 5, 5]
        trend_flat = analyzer.calculate_trend(x_values, y_values_flat)
        assert abs(trend_flat) < 0.01  # Should be slope of 0

        # Test edge cases
        trend_empty = analyzer.calculate_trend([], [])
        assert trend_empty == 0.0

        trend_single = analyzer.calculate_trend([1], [1])
        assert trend_single == 0.0

    def test_calculate_circular_mean(self, analyzer):
        """Test circular mean calculation for wind directions."""
        # Test with simple directions
        directions = [0, 90, 180, 270]  # All cardinal directions
        mean = analyzer.calculate_circular_mean(directions)
        # Should average to some value, but exact value depends on implementation
        assert isinstance(mean, float)
        assert 0 <= mean < 360

        # Test with concentrated directions (mostly north)
        directions_north = [350, 10, 20, 340]  # Mostly north
        mean_north = analyzer.calculate_circular_mean(directions_north)
        # Should be around north (0°), but could be around 360° which is equivalent
        assert mean_north >= 350 or mean_north <= 20  # Around north

        # Test empty list
        mean_empty = analyzer.calculate_circular_mean([])
        assert mean_empty == 0.0

    def test_get_historical_trends_error_handling(self, analyzer):
        """Test historical trends with error conditions."""
        # Test with future timestamps
        future_time = datetime.now() + timedelta(hours=1)
        analyzer._sensor_history["future_sensor"] = [
            {"timestamp": future_time, "value": 100.0},
        ]

        trends_future = analyzer.get_historical_trends("future_sensor")
        assert trends_future == {}  # Should exclude future data

    def test_calculate_trend_error_handling(self, analyzer):
        """Test trend calculation error handling."""
        # Test with empty lists
        trend_empty = analyzer.calculate_trend([], [])
        assert trend_empty == 0.0

        # Test with mismatched lengths
        trend_mismatch = analyzer.calculate_trend([1, 2], [1])
        assert trend_mismatch == 0.0

        # Test with single points
        trend_single = analyzer.calculate_trend([1], [1])
        assert trend_single == 0.0

        # Test with constant values (zero variance)
        trend_constant = analyzer.calculate_trend([1, 2, 3], [5, 5, 5])
        assert trend_constant == 0.0
