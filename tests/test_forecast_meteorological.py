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

        # Test wind speed penalty specifically (regression test for bug where wind penalty was applied incorrectly)
        # Same conditions but with moderate vs strong wind
        stability_moderate_wind = (
            meteorological_analyzer.calculate_atmospheric_stability(
                25.0,
                50.0,
                10.0,
                {"long_term_trend": 1.0},  # Moderate wind (10 mph < 13 mph threshold)
            )
        )
        stability_strong_wind = meteorological_analyzer.calculate_atmospheric_stability(
            25.0,
            50.0,
            15.0,
            {"long_term_trend": 1.0},  # Strong wind (15 mph > 13 mph threshold)
        )
        # Strong wind should be less stable than moderate wind
        assert stability_strong_wind < stability_moderate_wind

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

    def test_analyze_state_with_mock_analyzers(self, mock_analyzers):
        """Test analyze_state with mock objects returned by analyzers."""
        # Configure analyzers to return mock objects instead of proper data
        mock_pressure_analysis = Mock()
        mock_pressure_analysis._mock_name = "pressure_analysis"
        mock_analyzers["atmospheric"].analyze_pressure_trends = Mock(
            return_value=mock_pressure_analysis
        )

        mock_wind_analysis = Mock()
        mock_wind_analysis._mock_name = "wind_analysis"
        mock_analyzers["atmospheric"].analyze_wind_direction_trends = Mock(
            return_value=mock_wind_analysis
        )

        mock_temp_trends = Mock()
        mock_temp_trends._mock_name = "temp_trends"
        mock_analyzers["trends"].get_historical_trends = Mock(
            side_effect=lambda sensor, hours=24: mock_temp_trends
        )

        analyzer = MeteorologicalAnalyzer(
            mock_analyzers["atmospheric"],
            mock_analyzers["core"],
            mock_analyzers["solar"],
            mock_analyzers["trends"],
        )

        sensor_data = {
            "outdoor_temp": 75.0,
            "humidity": 65.0,
            "pressure": 29.85,
            "wind_speed": 8.0,
            "solar_radiation": 750.0,
            "solar_lux": 80000.0,
            "uv_index": 6.0,
        }

        result = analyzer.analyze_state(sensor_data)

        # Should still return valid result with fallback values
        assert isinstance(result, dict)
        assert "pressure_analysis" in result
        assert "wind_analysis" in result
        assert "temp_trends" in result

        # Check fallback values are used
        assert result["pressure_analysis"]["pressure_system"] == "normal"
        assert result["wind_analysis"]["direction_stability"] == 0.5
        assert result["temp_trends"]["trend"] == 0

    def test_analyze_state_with_invalid_analyzer_data(self, mock_analyzers):
        """Test analyze_state with invalid data types from analyzers."""
        # Configure analyzers to return invalid data types
        mock_analyzers["atmospheric"].analyze_pressure_trends = Mock(
            return_value={
                "pressure_system": "normal",
                "current_trend": "invalid_string",  # Should be numeric
                "long_term_trend": None,  # Should be numeric
                "storm_probability": [],  # Should be numeric
            }
        )

        mock_analyzers["atmospheric"].analyze_wind_direction_trends = Mock(
            return_value={
                "direction_stability": {},  # Should be numeric
                "gust_factor": "invalid",  # Should be numeric
            }
        )

        mock_analyzers["trends"].get_historical_trends = Mock(
            side_effect=lambda sensor, hours=24: {
                "trend": [],  # Should be numeric
                "volatility": {},  # Should be numeric
            }
        )

        analyzer = MeteorologicalAnalyzer(
            mock_analyzers["atmospheric"],
            mock_analyzers["core"],
            mock_analyzers["solar"],
            mock_analyzers["trends"],
        )

        sensor_data = {
            "outdoor_temp": 75.0,
            "humidity": 65.0,
            "pressure": 29.85,
            "wind_speed": 8.0,
            "solar_radiation": 750.0,
            "solar_lux": 80000.0,
            "uv_index": 6.0,
        }

        result = analyzer.analyze_state(sensor_data)

        # Should still return valid result with sanitized values
        assert isinstance(result, dict)
        assert result["pressure_analysis"]["current_trend"] == 0
        assert result["pressure_analysis"]["long_term_trend"] == 0
        assert result["pressure_analysis"]["storm_probability"] == 0.0
        assert result["wind_analysis"]["direction_stability"] == 0.5
        assert result["wind_analysis"]["gust_factor"] == 1.0
        assert result["temp_trends"]["trend"] == 0
        assert result["temp_trends"]["volatility"] == 2.0

    def test_analyze_state_with_invalid_sensor_data(self, meteorological_analyzer):
        """Test analyze_state with invalid sensor data types."""
        # Create mock sensor data with invalid types
        mock_temp = Mock()
        mock_temp._mock_name = "temperature"
        mock_humidity = Mock()
        mock_humidity._mock_name = "humidity"
        mock_pressure = Mock()
        mock_pressure._mock_name = "pressure"
        mock_wind = Mock()
        mock_wind._mock_name = "wind_speed"
        mock_solar_rad = Mock()
        mock_solar_rad._mock_name = "solar_radiation"
        mock_solar_lux = Mock()
        mock_solar_lux._mock_name = "solar_lux"
        mock_uv = Mock()
        mock_uv._mock_name = "uv_index"

        sensor_data = {
            "outdoor_temp": mock_temp,  # Mock object
            "humidity": mock_humidity,  # Mock object
            "pressure": mock_pressure,  # Mock object
            "wind_speed": mock_wind,  # Mock object
            "solar_radiation": mock_solar_rad,  # Mock object
            "solar_lux": mock_solar_lux,  # Mock object
            "uv_index": mock_uv,  # Mock object
        }

        result = meteorological_analyzer.analyze_state(sensor_data)

        # Should use default values for all invalid sensor data
        assert (
            result["current_conditions"]["temperature"] == 70.0
        )  # DefaultSensorValues.TEMPERATURE_F
        assert (
            result["current_conditions"]["humidity"] == 50.0
        )  # DefaultSensorValues.HUMIDITY
        assert (
            result["current_conditions"]["pressure"] == 29.92
        )  # DefaultSensorValues.PRESSURE_INHG
        assert (
            result["current_conditions"]["wind_speed"] == 0.0
        )  # DefaultSensorValues.WIND_SPEED
        assert (
            result["current_conditions"]["dewpoint"] is not None
        )  # Should calculate fallback dewpoint

    def test_analyze_state_with_mixed_invalid_sensor_data(
        self, meteorological_analyzer
    ):
        """Test analyze_state with mixed valid and invalid sensor data."""
        sensor_data = {
            "outdoor_temp": "invalid_string",  # Invalid type
            "humidity": None,  # Invalid type
            "pressure": [],  # Invalid type
            "wind_speed": {},  # Invalid type
            "solar_radiation": "not_a_number",  # Invalid type
            "solar_lux": None,  # Invalid type
            "uv_index": [],  # Invalid type
        }

        result = meteorological_analyzer.analyze_state(sensor_data)

        # Should use default values for all invalid sensor data
        assert result["current_conditions"]["temperature"] == 70.0
        assert result["current_conditions"]["humidity"] == 50.0
        assert result["current_conditions"]["pressure"] == 29.92
        assert result["current_conditions"]["wind_speed"] == 0.0

    def test_analyze_state_with_dewpoint_calculation_errors(self, mock_analyzers):
        """Test analyze_state with dewpoint calculation errors."""
        # Configure core analyzer to return invalid dewpoint values
        mock_analyzers["core"].calculate_dewpoint = Mock(
            return_value="invalid_string"
        )  # Invalid type

        analyzer = MeteorologicalAnalyzer(
            mock_analyzers["atmospheric"],
            mock_analyzers["core"],
            mock_analyzers["solar"],
            mock_analyzers["trends"],
        )

        sensor_data = {
            "outdoor_temp": 75.0,
            "humidity": 65.0,
        }

        result = analyzer.analyze_state(sensor_data)

        # Should calculate fallback dewpoint
        expected_fallback_dewpoint = 75.0 - (100 - 65) / 5.0
        assert result["current_conditions"]["dewpoint"] == expected_fallback_dewpoint

    def test_analyze_state_with_dewpoint_exception(self, mock_analyzers):
        """Test analyze_state when dewpoint calculation raises exception."""
        # Configure core analyzer to raise exception
        mock_analyzers["core"].calculate_dewpoint = Mock(
            side_effect=AttributeError("Mock error")
        )

        analyzer = MeteorologicalAnalyzer(
            mock_analyzers["atmospheric"],
            mock_analyzers["core"],
            mock_analyzers["solar"],
            mock_analyzers["trends"],
        )

        sensor_data = {
            "outdoor_temp": 75.0,
            "humidity": 65.0,
        }

        result = analyzer.analyze_state(sensor_data)

        # Should use fallback dewpoint calculation
        expected_fallback_dewpoint = 75.0 - (100 - 65) / 5.0
        assert result["current_conditions"]["dewpoint"] == expected_fallback_dewpoint

    def test_analyze_state_with_none_dewpoint_and_invalid_humidity(
        self, mock_analyzers
    ):
        """Test analyze_state with None dewpoint and invalid humidity."""
        # Configure core analyzer to return None
        mock_analyzers["core"].calculate_dewpoint = Mock(return_value=None)

        analyzer = MeteorologicalAnalyzer(
            mock_analyzers["atmospheric"],
            mock_analyzers["core"],
            mock_analyzers["solar"],
            mock_analyzers["trends"],
        )

        sensor_data = {
            "outdoor_temp": 75.0,
            "humidity": "invalid",  # Invalid humidity type
        }

        result = analyzer.analyze_state(sensor_data)

        # Should use default humidity in fallback calculation
        expected_fallback_dewpoint = 75.0 - (100 - 50) / 5.0
        assert result["current_conditions"]["dewpoint"] == expected_fallback_dewpoint

    def test_analyze_cloud_cover_with_invalid_solar_data(self, mock_analyzers):
        """Test cloud cover analysis with invalid solar analyzer data."""
        # Configure solar analyzer to return invalid data
        mock_analyzers["solar"].analyze_cloud_cover = Mock(
            return_value="invalid_string"
        )  # Invalid type

        analyzer = MeteorologicalAnalyzer(
            mock_analyzers["atmospheric"],
            mock_analyzers["core"],
            mock_analyzers["solar"],
            mock_analyzers["trends"],
        )

        sensor_data = {
            "solar_radiation": 600.0,
            "solar_lux": 65000.0,
            "uv_index": 4.0,
            "solar_elevation": 30.0,
        }
        pressure_analysis = {"current_trend": -0.5}

        result = analyzer._analyze_cloud_cover_comprehensive(
            600.0, 65000.0, 4.0, sensor_data, pressure_analysis
        )

        # Should use fallback cloud cover calculation (50.0) + pressure trend adjustment (-0.5 < 0.1, so +40)
        assert result["cloud_cover"] == 90.0  # 50.0 + 40.0

    def test_analyze_cloud_cover_with_exception(self, mock_analyzers):
        """Test cloud cover analysis when solar analyzer raises exception."""
        # Configure solar analyzer to raise exception
        mock_analyzers["solar"].analyze_cloud_cover = Mock(
            side_effect=AttributeError("Mock error")
        )

        analyzer = MeteorologicalAnalyzer(
            mock_analyzers["atmospheric"],
            mock_analyzers["core"],
            mock_analyzers["solar"],
            mock_analyzers["trends"],
        )

        sensor_data = {
            "solar_radiation": 600.0,
            "solar_lux": 65000.0,
            "uv_index": 4.0,
            "solar_elevation": 30.0,
        }
        pressure_analysis = {"current_trend": -0.5}

        result = analyzer._analyze_cloud_cover_comprehensive(
            600.0, 65000.0, 4.0, sensor_data, pressure_analysis
        )

        # Should use fallback cloud cover calculation based on solar radiation (600 > 400, so 40.0) + pressure trend adjustment (-0.5 < 0.1, so +40)
        assert result["cloud_cover"] == 80.0  # 40.0 + 40.0

    def test_analyze_cloud_cover_with_invalid_pressure_trend(
        self, meteorological_analyzer
    ):
        """Test cloud cover analysis with invalid pressure trend data."""
        # Test with invalid pressure trend types
        sensor_data = {
            "solar_radiation": 600.0,
            "solar_lux": 65000.0,
            "uv_index": 4.0,
            "solar_elevation": 30.0,
        }

        # Test with string pressure trend
        pressure_analysis = {"current_trend": "invalid_string"}
        result = meteorological_analyzer._analyze_cloud_cover_comprehensive(
            600.0, 65000.0, 4.0, sensor_data, pressure_analysis
        )
        assert (
            result["cloud_cover"] == 80.0
        )  # 40.0 + 40.0 (pressure trend defaults to 0.0, which triggers slow fall increase)

        # Test with None pressure trend
        pressure_analysis = {"current_trend": None}
        result = meteorological_analyzer._analyze_cloud_cover_comprehensive(
            600.0, 65000.0, 4.0, sensor_data, pressure_analysis
        )
        assert (
            result["cloud_cover"] == 80.0
        )  # 40.0 + 40.0 (pressure trend defaults to 0.0, which triggers slow fall increase)

    def test_analyze_moisture_transport_with_invalid_data(
        self, meteorological_analyzer
    ):
        """Test moisture transport analysis with invalid humidity trends data."""
        # Test with invalid trend types
        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": "invalid_string"}, {"direction_stability": 0.8}, 5.0
        )
        assert result["trend_direction"] == "stable"  # Should use default when invalid

        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": None}, {"direction_stability": 0.8}, 5.0
        )
        assert result["trend_direction"] == "stable"  # Should use default when None

        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": []}, {"direction_stability": 0.8}, 5.0
        )
        assert (
            result["trend_direction"] == "stable"
        )  # Should use default when invalid type

    def test_analyze_moisture_transport_with_invalid_temp_dewpoint_spread(
        self, meteorological_analyzer
    ):
        """Test moisture transport analysis with invalid temp-dewpoint spread."""
        # Test with invalid temp_dewpoint_spread types
        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": 2.0}, {"direction_stability": 0.8}, "invalid_string"
        )
        assert (
            result["moisture_availability"] == "moderate"
        )  # Should use default spread of 5.0, which is moderate

        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": 2.0}, {"direction_stability": 0.8}, None
        )
        assert (
            result["moisture_availability"] == "moderate"
        )  # Should use default spread of 5.0, which is moderate

        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": 2.0}, {"direction_stability": 0.8}, {}
        )
        assert (
            result["moisture_availability"] == "moderate"
        )  # Should use default spread of 5.0, which is moderate

    def test_analyze_wind_patterns_with_invalid_data(self, meteorological_analyzer):
        """Test wind pattern analysis with invalid wind trends and pressure data."""
        # Test with invalid wind trend types
        result = meteorological_analyzer._analyze_wind_patterns(
            10.0,
            {"trend": "invalid_string"},
            {"direction_stability": 0.7, "gust_factor": 1.2},
            {"current_trend": -0.3},
        )
        assert result["shear_intensity"] == "low"  # Should use default when invalid

        result = meteorological_analyzer._analyze_wind_patterns(
            10.0,
            {"trend": None},
            {"direction_stability": 0.7, "gust_factor": 1.2},
            {"current_trend": -0.3},
        )
        assert result["shear_intensity"] == "low"  # Should use default when None

        result = meteorological_analyzer._analyze_wind_patterns(
            10.0,
            {"trend": []},
            {"direction_stability": 0.7, "gust_factor": 1.2},
            {"current_trend": -0.3},
        )
        assert (
            result["shear_intensity"] == "low"
        )  # Should use default when invalid type

    def test_analyze_wind_patterns_with_invalid_pressure_trend(
        self, meteorological_analyzer
    ):
        """Test wind pattern analysis with invalid pressure trend data."""
        # Test with invalid pressure trend types
        result = meteorological_analyzer._analyze_wind_patterns(
            10.0,
            {"trend": 0.5},
            {"direction_stability": 0.7, "gust_factor": 1.2},
            {"current_trend": "invalid_string"},
        )
        assert result["gradient_wind_effect"] == 0.0  # Should use default when invalid

        result = meteorological_analyzer._analyze_wind_patterns(
            10.0,
            {"trend": 0.5},
            {"direction_stability": 0.7, "gust_factor": 1.2},
            {"current_trend": None},
        )
        assert result["gradient_wind_effect"] == 0.0  # Should use default when None

        result = meteorological_analyzer._analyze_wind_patterns(
            10.0,
            {"trend": 0.5},
            {"direction_stability": 0.7, "gust_factor": 1.2},
            {"current_trend": {}},
        )
        assert (
            result["gradient_wind_effect"] == 0.0
        )  # Should use default when invalid type

    def test_analyze_wind_patterns_with_missing_gust_factor(
        self, meteorological_analyzer
    ):
        """Test wind pattern analysis when gust_factor is missing from wind analysis."""
        # Test with missing gust_factor key
        result = meteorological_analyzer._analyze_wind_patterns(
            10.0, {"trend": 0.5}, {"direction_stability": 0.7}, {"current_trend": -0.3}
        )
        assert result["gust_factor"] == 1.0  # Should use default when missing

    def test_analyze_cloud_cover_fallback_branches(self, mock_analyzers):
        """Test cloud cover fallback logic for different solar radiation levels."""
        # Configure solar analyzer to raise exception to trigger fallback
        mock_analyzers["solar"].analyze_cloud_cover = Mock(
            side_effect=AttributeError("Mock error")
        )

        analyzer = MeteorologicalAnalyzer(
            mock_analyzers["atmospheric"],
            mock_analyzers["core"],
            mock_analyzers["solar"],
            mock_analyzers["trends"],
        )

        # Use pressure trend that doesn't trigger adjustment (between 0.1 and 0.5)
        pressure_analysis = {"current_trend": 0.2}

        # Test high solar radiation branch (> 800)
        result = analyzer._analyze_cloud_cover_comprehensive(
            900.0, 90000.0, 8.0, {"solar_elevation": 30.0}, pressure_analysis
        )
        assert result["cloud_cover"] == 10.0

        # Test medium solar radiation branch (400-800)
        result = analyzer._analyze_cloud_cover_comprehensive(
            600.0, 65000.0, 4.0, {"solar_elevation": 30.0}, pressure_analysis
        )
        assert result["cloud_cover"] == 40.0

        # Test low solar radiation branch (100-400)
        result = analyzer._analyze_cloud_cover_comprehensive(
            200.0, 20000.0, 2.0, {"solar_elevation": 30.0}, pressure_analysis
        )
        assert result["cloud_cover"] == 70.0

        # Test very low solar radiation branch (< 100)
        result = analyzer._analyze_cloud_cover_comprehensive(
            50.0, 5000.0, 0.0, {"solar_elevation": 30.0}, pressure_analysis
        )
        assert result["cloud_cover"] == 90.0

    def test_analyze_cloud_cover_pressure_trend_branches(self, meteorological_analyzer):
        """Test cloud cover pressure trend adjustment branches."""
        sensor_data = {"solar_elevation": 30.0}

        # Test rapid falling pressure (< -0.5)
        pressure_analysis = {"current_trend": -1.0}
        result = meteorological_analyzer._analyze_cloud_cover_comprehensive(
            600.0, 65000.0, 4.0, {"solar_elevation": 30.0}, pressure_analysis
        )
        # 40.0 + 60.0 = 100.0, but capped at MAX_CLOUD_COVER (95.0)
        assert result["cloud_cover"] == 95.0

        # Test slow falling pressure (-0.5 to 0.1) - already covered
        pressure_analysis = {"current_trend": -0.3}
        result = meteorological_analyzer._analyze_cloud_cover_comprehensive(
            600.0, 65000.0, 4.0, sensor_data, pressure_analysis
        )
        assert result["cloud_cover"] == 80.0  # 40.0 + 40.0

        # Test rising pressure (> DIRECTION_RISING_MODERATE)
        pressure_analysis = {"current_trend": 1.0}
        result = meteorological_analyzer._analyze_cloud_cover_comprehensive(
            600.0, 65000.0, 4.0, sensor_data, pressure_analysis
        )
        # 40.0 - 40.0 = 0.0, but capped at MIN_CLOUD_COVER (5.0)
        assert result["cloud_cover"] == 5.0

    def test_analyze_moisture_transport_all_branches(self, meteorological_analyzer):
        """Test moisture transport analysis covering all branches."""
        # Test high moisture availability (< 5.0 spread)
        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": 2.0}, {"direction_stability": 0.8}, 3.0
        )
        assert result["moisture_availability"] == "high"
        assert result["condensation_potential"] == 0.8  # CONDENSATION_HIGH

        # Test moderate moisture availability (5.0-10.0 spread) - already covered
        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": 2.0}, {"direction_stability": 0.8}, 7.0
        )
        assert result["moisture_availability"] == "moderate"
        assert result["condensation_potential"] == 0.5  # CONDENSATION_MODERATE

        # Test low moisture availability (> 10.0 spread)
        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": 2.0}, {"direction_stability": 0.8}, 15.0
        )
        assert result["moisture_availability"] == "low"
        assert result["condensation_potential"] == 0.2  # CONDENSATION_LOW

        # Test decreasing humidity trend
        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": -6.0}, {"direction_stability": 0.8}, 5.0
        )
        assert result["trend_direction"] == "decreasing"

        # Test stable humidity trend - already covered
        result = meteorological_analyzer._analyze_moisture_transport(
            70.0, {"trend": 0.5}, {"direction_stability": 0.8}, 5.0
        )
        assert result["trend_direction"] == "stable"
