"""Test the atmospheric analysis functionality."""

from collections import deque
from datetime import datetime, timedelta

from homeassistant.components.weather import ATTR_CONDITION_FOG
import pytest

from custom_components.micro_weather.analysis.atmospheric import AtmosphericAnalyzer


class TestAtmosphericAnalyzer:
    """Test the AtmosphericAnalyzer class."""

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
        """Create AtmosphericAnalyzer instance for testing."""
        return AtmosphericAnalyzer(mock_sensor_history)

    def test_analyze_fog_conditions(self, analyzer):
        """Test fog condition analysis using unified scoring system."""
        # Test clear conditions (no fog) - low humidity, large spread
        result = analyzer.analyze_fog_conditions(
            70.0, 50.0, 50.0, 20.0, 5.0, 200.0, True
        )
        assert result is None

        # Test dense fog conditions (nighttime)
        # High humidity (98% = 40pts) + tight spread (0.1°F = 30pts) + calm winds (1.5mph = 15pts) + no solar (10pts) = 95pts
        result_fog = analyzer.analyze_fog_conditions(
            70.0, 99.5, 69.9, 0.1, 1.5, 0.0, False
        )
        assert result_fog == ATTR_CONDITION_FOG

        # Test moderate fog conditions (nighttime)
        # High humidity (92% = 20pts) + moderate spread (2.0°F = 15pts) + light winds (3mph = 10pts) + no solar (10pts) = 55pts
        result_moderate = analyzer.analyze_fog_conditions(
            70.0, 92.0, 68.0, 2.0, 3.0, 0.0, False
        )
        assert result_moderate == ATTR_CONDITION_FOG

        # Test light fog (high humidity required)
        # Very high humidity (95% = 30pts) + larger spread (2.5°F = 5pts) + light winds (4mph = 10pts) + no solar (10pts) = 55pts
        result_light = analyzer.analyze_fog_conditions(
            70.0, 95.0, 67.5, 2.5, 4.0, 0.0, False
        )
        assert result_light == ATTR_CONDITION_FOG

        # Test twilight conditions with extremely high humidity and tight spread - IS fog
        # Very high humidity (99% = 40pts) + very tight spread (0.3°F = 30pts) + calm winds (1.3mph = 15pts) = 85pts
        # Even with 22 W/m² solar, the atmospheric conditions indicate dense fog blocking dawn light
        result_twilight_fog = analyzer.analyze_fog_conditions(
            54.0, 99.0, 53.7, 0.3, 1.3, 22.0, False
        )
        assert result_twilight_fog == ATTR_CONDITION_FOG  # Dense fog even at twilight

        # Test twilight with moderate humidity - should NOT be fog
        # Moderate humidity (90% = 0pts) even with tight spread doesn't trigger fog
        result_twilight_clear = analyzer.analyze_fog_conditions(
            54.0, 90.0, 53.0, 1.0, 3.0, 50.0, False
        )
        assert result_twilight_clear is None  # Normal dawn/twilight humidity, not fog

        # Test daytime fog (sun shining through fog)
        # Very high humidity (98% = 40pts) + tight spread (0.5°F = 30pts) + calm winds (2mph = 15pts) + low solar (<50 = 15pts) = 100pts
        result_daytime_fog = analyzer.analyze_fog_conditions(
            70.0, 98.0, 69.5, 0.5, 2.0, 40.0, True
        )
        assert result_daytime_fog == ATTR_CONDITION_FOG

        # Test marginal conditions (below threshold)
        # Moderate humidity (88% = 10pts) + larger spread (3.5°F = 0pts) + moderate winds (6mph = 5pts) + low solar (10pts) = 25pts
        result_marginal = analyzer.analyze_fog_conditions(
            70.0, 88.0, 64.5, 3.5, 6.0, 2.0, False
        )
        assert result_marginal is None  # Below 45-point threshold

        # Test evaporation fog conditions (warmer temp bonus)
        # Very high humidity (95% = 30pts) + tight spread (1.5°F = 15pts) + light winds (4mph = 10pts) + no solar (10pts) + temp bonus (5pts) = 70pts
        result_evap = analyzer.analyze_fog_conditions(
            50.0, 95.0, 48.5, 1.5, 4.0, 0.0, False
        )
        assert result_evap == ATTR_CONDITION_FOG

        # Test strong winds dispersing fog (negative score modifier)
        # High humidity (95% = 30pts) + tight spread (1.0°F = 25pts) + strong winds (12mph = -10pts) + no solar (10pts) = 55pts
        result_windy = analyzer.analyze_fog_conditions(
            70.0, 95.0, 69.0, 1.0, 12.0, 0.0, False
        )
        assert result_windy == ATTR_CONDITION_FOG  # Still enough for moderate fog

    def test_analyze_pressure_trends(self, analyzer):
        """Test pressure trend analysis."""
        pressure_analysis = analyzer.analyze_pressure_trends()
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

    def test_analyze_wind_direction_trends(self, analyzer):
        """Test wind direction trend analysis."""
        wind_analysis = analyzer.analyze_wind_direction_trends()
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

    def test_calculate_angular_difference(self, analyzer):
        """Test angular difference calculation."""
        # Test same direction
        diff_same = analyzer._calculate_angular_difference(90, 90)
        assert diff_same == 0

        # Test opposite directions
        diff_opposite = analyzer._calculate_angular_difference(0, 180)
        assert abs(diff_opposite) == 180

        # Test small difference
        diff_small = analyzer._calculate_angular_difference(10, 20)
        assert diff_small == 10

        # Test wraparound
        diff_wrap = analyzer._calculate_angular_difference(350, 10)
        assert diff_wrap == 20  # 350 to 10 is 20° clockwise

    def test_analyze_fog_conditions_error_handling(self, analyzer):
        """Test fog condition analysis with invalid inputs."""
        # Test with extreme values
        result_extreme = analyzer.analyze_fog_conditions(
            150.0, 110.0, 150.0, -10.0, 200.0, -100.0, True
        )
        assert isinstance(
            result_extreme, (str, type(None))
        )  # Should return a valid condition or None

        # Test with invalid temperature differences
        result_invalid = analyzer.analyze_fog_conditions(
            50.0, 80.0, 30.0, 20.0, 10.0, 100.0, True  # Dewpoint > temperature
        )
        assert isinstance(
            result_invalid, (str, type(None))
        )  # Should handle invalid dewpoint

    def test_analyze_pressure_trends_error_handling(self, analyzer):
        """Test pressure trend analysis error handling."""
        # Test with empty history
        analyzer._sensor_history = {}  # Clear history

        pressure_analysis = analyzer.analyze_pressure_trends()
        assert pressure_analysis["pressure_system"] == "unknown"
        assert pressure_analysis["storm_probability"] == 0.0

        # Test with insufficient data
        analyzer._sensor_history["pressure"] = [
            {"timestamp": datetime.now(), "value": 29.92}
        ]

        pressure_analysis_short = analyzer.analyze_pressure_trends()
        assert pressure_analysis_short["pressure_system"] == "unknown"
        assert pressure_analysis_short["storm_probability"] == 0.0

    def test_analyze_wind_direction_trends_error_handling(self, analyzer):
        """Test wind direction trend analysis error handling."""
        # Test with empty history
        analyzer._sensor_history = {}

        wind_analysis = analyzer.analyze_wind_direction_trends()
        assert wind_analysis["average_direction"] is None
        assert wind_analysis["direction_stability"] == 0.0
        assert wind_analysis["significant_shift"] is False

        # Test with invalid direction values
        analyzer._sensor_history["wind_direction"] = [
            {"timestamp": datetime.now(), "value": 400.0},  # Invalid direction > 360
            {
                "timestamp": datetime.now() - timedelta(hours=1),
                "value": -50.0,
            },  # Invalid negative
        ]

        wind_analysis_invalid = analyzer.analyze_wind_direction_trends()
        assert isinstance(
            wind_analysis_invalid["average_direction"], (float, type(None))
        )

    def test_calculate_circular_mean_error_handling(self, analyzer):
        """Test circular mean calculation error handling."""
        # Test with empty list
        mean_empty = analyzer._calculate_circular_mean([])
        assert mean_empty == 0.0

        # Test with invalid values (should filter out invalid ones)
        mean_invalid = analyzer._calculate_circular_mean([400, -50, 90, 180])
        assert isinstance(mean_invalid, float)
        assert 0 <= mean_invalid < 360

        # Test with extreme values
        mean_extreme = analyzer._calculate_circular_mean(
            [0, 720, 1080, 90]
        )  # Multiples of 360
        assert isinstance(mean_extreme, float)

    def test_calculate_prevailing_direction_error_handling(self, analyzer):
        """Test prevailing direction calculation error handling."""
        # Test with empty list
        direction_empty = analyzer._calculate_prevailing_direction([])
        assert direction_empty == "unknown"

        # Test with invalid values (should filter out invalid ones)
        direction_invalid = analyzer._calculate_prevailing_direction(
            [400, -50, 90, 180]
        )
        assert direction_invalid in ["north", "east", "south", "west", "unknown"]

        # Test with boundary values
        direction_boundary = analyzer._calculate_prevailing_direction([0, 360, 359.9])
        assert direction_boundary == "north"  # All should map to north sector

    def test_get_altitude_adjusted_pressure_thresholds_hpa(self, analyzer):
        """Test altitude-adjusted pressure thresholds in hPa."""
        thresholds = analyzer.get_altitude_adjusted_pressure_thresholds_hpa(1000.0)
        assert isinstance(thresholds, dict)
        assert "very_high" in thresholds
        assert "high" in thresholds
        assert "normal_high" in thresholds
        assert "normal" in thresholds
        assert "low" in thresholds
        assert "very_low" in thresholds

        # At 1000m altitude, thresholds should be lower than sea level
        sea_level_thresholds = analyzer.get_altitude_adjusted_pressure_thresholds_hpa(
            0.0
        )
        assert thresholds["normal"] < sea_level_thresholds["normal"]
