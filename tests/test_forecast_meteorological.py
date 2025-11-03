"""Test the meteorological analysis functionality."""

from unittest.mock import Mock

import pytest

from custom_components.micro_weather.forecast.meteorological import (
    MeteorologicalAnalyzer,
)


@pytest.fixture
def mock_analyzers():
    """Create mock analyzer instances."""
    atmospheric = Mock()
    core = Mock()
    solar = Mock()
    trends = Mock()

    # Configure atmospheric methods
    atmospheric.analyze_pressure_trends = Mock(
        return_value={
            "pressure_system": "normal",
            "storm_probability": 20.0,
            "current_trend": 0.0,
            "long_term_trend": 0.0,
        }
    )
    atmospheric.analyze_wind_direction_trends = Mock(
        return_value={
            "direction_stability": 0.8,
            "gust_factor": 1.0,
        }
    )

    # Configure core methods
    core.calculate_dewpoint = Mock(return_value=15.0)

    # Configure trends methods
    trends.get_historical_trends = Mock(
        side_effect=lambda sensor, hours=24: {
            "current": 60.0,
            "average": 58.0,
            "trend": 0.2,
            "min": 50.0,
            "max": 70.0,
            "volatility": 5.0,
        }
    )

    # Configure solar methods
    solar.analyze_cloud_cover = Mock(return_value=40.0)

    return {
        "atmospheric": atmospheric,
        "core": core,
        "solar": solar,
        "trends": trends,
    }


@pytest.fixture
def meteorological_analyzer(mock_analyzers):
    """Create MeteorologicalAnalyzer instance for testing."""
    return MeteorologicalAnalyzer(
        mock_analyzers["atmospheric"],
        mock_analyzers["core"],
        mock_analyzers["solar"],
        mock_analyzers["trends"],
    )


class TestMeteorologicalAnalyzer:
    """Test the MeteorologicalAnalyzer class."""

    def test_init(self, meteorological_analyzer):
        """Test MeteorologicalAnalyzer initialization."""
        assert meteorological_analyzer is not None
        assert meteorological_analyzer.atmospheric_analyzer is not None
        assert meteorological_analyzer.core_analyzer is not None
        assert meteorological_analyzer.solar_analyzer is not None
        assert meteorological_analyzer.trends_analyzer is not None

    def test_analyze_state(self, meteorological_analyzer, mock_analyzers):
        """Test comprehensive meteorological state analysis."""
        sensor_data = {
            "outdoor_temp": 75.0,
            "humidity": 65.0,
            "pressure": 29.85,
            "wind_speed": 8.0,
            "solar_radiation": 750.0,
            "solar_lux": 80000.0,
            "uv_index": 6.0,
            "solar_elevation": 45.0,
        }
        altitude = 150.0

        result = meteorological_analyzer.analyze_state(sensor_data, altitude)

        assert isinstance(result, dict)

        # Check required keys
        required_keys = [
            "pressure_analysis",
            "wind_analysis",
            "temp_trends",
            "humidity_trends",
            "wind_trends",
            "current_conditions",
            "atmospheric_stability",
            "weather_system",
            "cloud_analysis",
            "moisture_analysis",
            "wind_pattern_analysis",
        ]

        for key in required_keys:
            assert key in result

        # Validate current conditions
        current = result["current_conditions"]
        assert "temperature" in current
        assert "humidity" in current
        assert "pressure" in current
        assert "wind_speed" in current

        # Validate atmospheric stability
        assert 0.0 <= result["atmospheric_stability"] <= 1.0

        # Validate weather system
        weather_sys = result["weather_system"]
        assert "type" in weather_sys
        assert "evolution_potential" in weather_sys
        assert "persistence_factor" in weather_sys

    def test_calculate_atmospheric_stability(self, meteorological_analyzer):
        """Test atmospheric stability calculation."""
        # Test stable conditions (cool, humid, light wind)
        stability1 = meteorological_analyzer.calculate_atmospheric_stability(
            15.0, 80.0, 3.0, {"long_term_trend": 0.1}
        )
        assert 0.5 <= stability1 <= 1.0  # Should be relatively stable

        # Test unstable conditions (warm, dry, strong wind)
        stability2 = meteorological_analyzer.calculate_atmospheric_stability(
            30.0, 30.0, 20.0, {"long_term_trend": 2.0}
        )
        assert 0.0 <= stability2 <= 0.5  # Should be relatively unstable

        # Test boundary conditions
        stability_min = meteorological_analyzer.calculate_atmospheric_stability(
            40.0, 10.0, 50.0, {"long_term_trend": 10.0}
        )
        stability_max = meteorological_analyzer.calculate_atmospheric_stability(
            5.0, 95.0, 0.0, {"long_term_trend": -5.0}
        )

        assert 0.0 <= stability_min <= 1.0
        assert 0.0 <= stability_max <= 1.0

    def test_classify_weather_system(self, meteorological_analyzer):
        """Test weather system classification."""
        # Test stable high pressure system
        result1 = meteorological_analyzer.classify_weather_system(
            {"pressure_system": "high_pressure", "current_trend": 0.2},
            {"direction_stability": 0.9},
            {"trend": 0.1},
            0.8,  # High stability
        )
        assert result1["type"] == "stable_high"
        assert result1["evolution_potential"] == "gradual_improvement"

        # Test active low pressure system
        result2 = meteorological_analyzer.classify_weather_system(
            {
                "pressure_system": "low_pressure",
                "current_trend": -1.0,
                "storm_probability": 60.0,
            },
            {"direction_stability": 0.3},
            {"trend": -0.5},
            0.2,  # Low stability
        )
        assert result2["type"] == "active_low"
        assert result2["evolution_potential"] == "rapid_change"

        # Test transitional system
        result3 = meteorological_analyzer.classify_weather_system(
            {"pressure_system": "normal", "current_trend": 0.0},
            {"direction_stability": 0.6},
            {"trend": 0.0},
            0.5,  # Neutral stability
        )
        assert result3["type"] == "transitional"
        assert result3["evolution_potential"] == "moderate_change"

    def test_analyze_cloud_cover_comprehensive(
        self, meteorological_analyzer, mock_analyzers
    ):
        """Test comprehensive cloud cover analysis."""
        sensor_data = {
            "solar_radiation": 600.0,
            "solar_lux": 65000.0,
            "uv_index": 4.0,
            "solar_elevation": 30.0,
        }
        pressure_analysis = {
            "pressure_system": "low_pressure",
            "storm_probability": 40.0,
        }

        result = meteorological_analyzer._analyze_cloud_cover_comprehensive(
            600.0, 65000.0, 4.0, sensor_data, pressure_analysis
        )

        assert isinstance(result, dict)
        assert "cloud_cover" in result
        assert "cloud_type" in result
        assert "solar_efficiency" in result

        assert 0 <= result["cloud_cover"] <= 100
        assert result["cloud_type"] in [
            "clear",
            "few_clouds",
            "scattered",
            "broken",
            "overcast",
        ]
        assert 0 <= result["solar_efficiency"] <= 100

    def test_analyze_moisture_transport(self, meteorological_analyzer):
        """Test moisture transport analysis."""
        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": 2.0}, {"direction_stability": 0.8}, 5.0
        )

        assert isinstance(result, dict)
        required_keys = [
            "moisture_content",
            "transport_potential",
            "moisture_availability",
            "condensation_potential",
            "trend_direction",
        ]

        for key in required_keys:
            assert key in result

        assert 0 <= result["moisture_content"] <= 100
        assert 0 <= result["transport_potential"] <= 10
        assert result["moisture_availability"] in ["low", "moderate", "high"]
        assert 0 <= result["condensation_potential"] <= 1.0
        assert result["trend_direction"] in ["stable", "increasing", "decreasing"]

    def test_analyze_wind_patterns(self, meteorological_analyzer):
        """Test wind pattern analysis."""
        result = meteorological_analyzer._analyze_wind_patterns(
            10.0,
            {"trend": 0.5},
            {"direction_stability": 0.7, "gust_factor": 1.2},
            {"current_trend": -0.3},
        )

        assert isinstance(result, dict)
        required_keys = [
            "wind_speed",
            "direction_stability",
            "gust_factor",
            "shear_intensity",
            "gradient_wind_effect",
        ]

        for key in required_keys:
            assert key in result

        assert result["wind_speed"] == 10.0
        assert 0 <= result["direction_stability"] <= 1.0
        assert result["gust_factor"] >= 1.0
        assert result["shear_intensity"] in ["low", "moderate", "high", "extreme"]
