"""Test the hourly forecast generation functionality."""

from datetime import datetime
from unittest.mock import Mock

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
)
import pytest

from custom_components.micro_weather.forecast.hourly import HourlyForecastGenerator


@pytest.fixture
def mock_analyzers():
    """Create mock analyzer instances."""
    atmospheric = Mock()
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
            "average_direction": 180.0,
            "direction_stability": 0.8,
            "direction_change_rate": 10.0,
            "significant_shift": False,
            "prevailing_direction": "south",
        }
    )

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
        "solar": solar,
        "trends": trends,
    }


@pytest.fixture
def hourly_forecast_generator(mock_analyzers):
    """Create HourlyForecastGenerator instance for testing."""
    return HourlyForecastGenerator(
        mock_analyzers["atmospheric"],
        mock_analyzers["solar"],
        mock_analyzers["trends"],
    )


class TestHourlyForecastGenerator:
    """Test the HourlyForecastGenerator class."""

    def test_init(self, hourly_forecast_generator):
        """Test HourlyForecastGenerator initialization."""
        assert hourly_forecast_generator is not None
        assert hourly_forecast_generator.atmospheric_analyzer is not None
        assert hourly_forecast_generator.solar_analyzer is not None
        assert hourly_forecast_generator.trends_analyzer is not None

    def test_generate_forecast(self, hourly_forecast_generator, mock_analyzers):
        """Test hourly forecast generation."""
        current_temp = 22.0  # Celsius
        current_condition = ATTR_CONDITION_PARTLYCLOUDY
        sensor_data = {
            "outdoor_temp": 72.0,  # Fahrenheit
            "humidity": 60.0,
            "pressure": 29.92,
            "wind_speed": 5.0,
            "solar_radiation": 800.0,
            "solar_lux": 85000.0,
            "uv_index": 6.0,
        }

        # Mock astronomical calculator
        astronomical_calculator = Mock()
        astronomical_calculator.calculate_diurnal_variation = Mock(return_value=2.0)

        # Mock sunrise/sunset times (timezone-aware)
        from datetime import timezone

        sunrise_time = datetime.now(timezone.utc).replace(hour=6, minute=30)
        sunset_time = datetime.now(timezone.utc).replace(hour=19, minute=30)

        meteorological_state = {
            "atmospheric_stability": 0.7,
            "pressure_analysis": {"current_trend": 0.1},
        }
        hourly_patterns = {
            "diurnal_patterns": {
                "temperature": {
                    "dawn": -2.0,
                    "morning": 1.0,
                    "noon": 3.0,
                    "afternoon": 2.0,
                    "evening": -1.0,
                }
            }
        }
        micro_evolution = {
            "evolution_rate": 0.3,
            "micro_changes": {"max_change_per_hour": 1.0},
        }

        result = hourly_forecast_generator.generate_forecast(
            current_temp,
            current_condition,
            sensor_data,
            sunrise_time,
            sunset_time,
            altitude=None,
            meteorological_state=meteorological_state,
            hourly_patterns=hourly_patterns,
            micro_evolution=micro_evolution,
        )

        assert isinstance(result, list)
        assert len(result) == 24  # 24-hour forecast

        for hour_forecast in result:
            assert isinstance(hour_forecast, dict)
            assert "datetime" in hour_forecast
            assert "temperature" in hour_forecast
            assert "condition" in hour_forecast
            assert "precipitation" in hour_forecast
            assert "wind_speed" in hour_forecast
            assert "humidity" in hour_forecast

            # Validate data types
            assert isinstance(hour_forecast["temperature"], float)
            assert isinstance(hour_forecast["condition"], str)
            assert isinstance(hour_forecast["precipitation"], float)
            assert isinstance(hour_forecast["wind_speed"], float)
            assert isinstance(hour_forecast["humidity"], (int, float))

    def test_forecast_temperature(self, hourly_forecast_generator, mock_analyzers):
        """Test hourly temperature forecasting."""
        hour_idx = 2
        current_temp = 22.0
        astronomical_context = {
            "is_daytime": True,
            "solar_elevation": 45.0,
            "hour_of_day": 14,
            "forecast_hour": 2,
        }
        meteorological_state = {"pressure_analysis": {"current_trend": 0.1}}
        hourly_patterns = {
            "diurnal_patterns": {
                "temperature": {
                    "dawn": -2.0,
                    "morning": 1.0,
                    "noon": 3.0,
                    "afternoon": 2.0,
                    "evening": -1.0,
                }
            }
        }
        micro_evolution = {
            "evolution_rate": 0.3,
            "micro_changes": {"max_change_per_hour": 1.0},
        }

        result = hourly_forecast_generator.forecast_temperature(
            hour_idx,
            current_temp,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert isinstance(result, float)
        # Should be close to base temperature with diurnal variation
        assert 18.0 <= result <= 26.0

    def test_forecast_condition(self, hourly_forecast_generator, mock_analyzers):
        """Test hourly condition forecasting."""
        hour_idx = 2
        current_condition = ATTR_CONDITION_PARTLYCLOUDY
        astronomical_context = {
            "is_daytime": True,
            "solar_elevation": 45.0,
            "hour_of_day": 14,
        }
        meteorological_state = {
            "pressure_analysis": {
                "current_trend": 0.0,
                "storm_probability": 10.0,
            },
            "cloud_analysis": {"cloud_cover": 40.0},
        }
        hourly_patterns = {}
        micro_evolution = {}

        result = hourly_forecast_generator.forecast_condition(
            hour_idx,
            current_condition,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert isinstance(result, str)
        assert result in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
            ATTR_CONDITION_CLEAR_NIGHT,
        ]

    def test_forecast_precipitation(self, hourly_forecast_generator, mock_analyzers):
        """Test hourly precipitation forecasting."""
        hour_idx = 2
        condition = ATTR_CONDITION_RAINY
        meteorological_state = {
            "pressure_analysis": {"storm_probability": 60.0},
            "moisture_analysis": {
                "transport_potential": 7.0,
                "condensation_potential": 0.6,
            },
            "atmospheric_stability": 0.4,
        }
        hourly_patterns = {}
        sensor_data = {"rain_rate_unit": "mm"}

        result = hourly_forecast_generator._forecast_precipitation(
            hour_idx,
            condition,
            meteorological_state,
            hourly_patterns,
            sensor_data,
        )

        assert isinstance(result, float)
        assert result >= 0

    def test_forecast_wind(self, hourly_forecast_generator, mock_analyzers):
        """Test hourly wind forecasting."""
        hour_idx = 2
        current_wind = 5.0
        condition = ATTR_CONDITION_PARTLYCLOUDY
        meteorological_state = {
            "pressure_analysis": {"pressure_system": "normal"},
            "wind_pattern_analysis": {
                "direction_stability": 0.8,
                "gradient_wind_effect": 3.0,
            },
        }
        hourly_patterns = {
            "diurnal_patterns": {
                "wind": {
                    "dawn": -1.0,
                    "morning": 0.5,
                    "noon": 1.0,
                    "afternoon": 1.5,
                    "evening": 0.5,
                }
            }
        }

        result = hourly_forecast_generator._forecast_wind(
            hour_idx,
            current_wind,
            condition,
            meteorological_state,
            hourly_patterns,
        )

        assert isinstance(result, float)
        assert result > 0

    def test_forecast_humidity(self, hourly_forecast_generator, mock_analyzers):
        """Test hourly humidity forecasting."""
        hour_idx = 2
        current_humidity = 60.0
        meteorological_state = {
            "moisture_analysis": {"trend_direction": "increasing"},
            "atmospheric_stability": 0.7,
        }
        hourly_patterns = {}
        condition = ATTR_CONDITION_CLOUDY

        result = hourly_forecast_generator._forecast_humidity(
            hour_idx,
            current_humidity,
            meteorological_state,
            hourly_patterns,
            condition,
        )

        assert isinstance(result, (int, float))
        assert 10 <= result <= 100

    def test_calculate_astronomical_context(self, hourly_forecast_generator):
        """Test astronomical context calculation."""
        forecast_time = datetime.now().replace(hour=14, minute=0)
        sunrise_time = datetime.now().replace(hour=6, minute=30)
        sunset_time = datetime.now().replace(hour=19, minute=30)
        hour_idx = 2

        result = hourly_forecast_generator._calculate_astronomical_context(
            forecast_time, sunrise_time, sunset_time, hour_idx
        )

        assert isinstance(result, dict)
        assert "is_daytime" in result
        assert "solar_elevation" in result
        assert "hour_of_day" in result
        assert "forecast_hour" in result

    def test_calculate_hourly_pressure_modulation(self, hourly_forecast_generator):
        """Test hourly pressure modulation calculation."""
        meteorological_state = {"pressure_analysis": {"current_trend": 0.1}}
        hour_idx = 2

        result = hourly_forecast_generator._calculate_hourly_pressure_modulation(
            meteorological_state, hour_idx
        )

        assert isinstance(result, float)

    def test_calculate_hourly_evolution_influence(self, hourly_forecast_generator):
        """Test hourly evolution influence calculation."""
        micro_evolution = {
            "evolution_rate": 0.3,
            "micro_changes": {"max_change_per_hour": 1.0},
        }
        hour_idx = 2

        result = hourly_forecast_generator._calculate_hourly_evolution_influence(
            micro_evolution, hour_idx
        )

        assert isinstance(result, float)

    def test_analyze_pressure_trend_severity(self, hourly_forecast_generator):
        """Test pressure trend severity analysis."""
        current_trend = -1.0
        long_term_trend = -0.5

        result = hourly_forecast_generator._analyze_pressure_trend_severity(
            current_trend, long_term_trend
        )

        assert isinstance(result, dict)
        assert "severity" in result
        assert "direction" in result
        assert "long_term_direction" in result
        assert "urgency_factor" in result
        assert "confidence" in result

    def test_calculate_pressure_aware_evolution_frequency(
        self, hourly_forecast_generator
    ):
        """Test pressure-aware evolution frequency calculation."""
        pressure_analysis = {
            "current_trend": -1.0,
            "long_term_trend": -0.5,
        }
        hour_idx = 2

        result = (
            hourly_forecast_generator._calculate_pressure_aware_evolution_frequency(
                pressure_analysis, hour_idx
            )
        )

        assert isinstance(result, bool)

    def test_determine_pressure_driven_condition(self, hourly_forecast_generator):
        """Test pressure-driven condition determination."""
        pressure_analysis = {
            "current_trend": -1.0,
            "long_term_trend": -0.5,
        }
        storm_probability = 30.0
        cloud_cover = 60.0
        is_daytime = True
        current_condition = ATTR_CONDITION_PARTLYCLOUDY

        result = hourly_forecast_generator._determine_pressure_driven_condition(
            pressure_analysis,
            storm_probability,
            cloud_cover,
            is_daytime,
            current_condition,
        )

        assert result is None or isinstance(result, str)
