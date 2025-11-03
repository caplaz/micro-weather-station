"""Test the daily forecast generation functionality."""

from unittest.mock import Mock

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
)
import pytest

from custom_components.micro_weather.forecast.daily import DailyForecastGenerator


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
    atmospheric.adjust_pressure_for_altitude = Mock(return_value=29.92)
    atmospheric.calculate_circular_mean = Mock(return_value=180.0)
    atmospheric.calculate_angular_difference = Mock(return_value=90.0)
    atmospheric.analyze_fog_conditions = Mock(return_value=ATTR_CONDITION_FOG)

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
    def mock_analyze_cloud_cover(*args, **kwargs):
        # Check if pressure trends indicate storm conditions
        if len(args) > 4 and isinstance(args[4], dict):
            pressure_trends = args[4]
            storm_prob = pressure_trends.get("storm_probability", 0)
            current_trend = pressure_trends.get("current_trend", 0)
            # Falling pressure (negative trend) increases cloud cover
            if storm_prob > 60 or current_trend < -0.3:
                return 85.0  # High cloud cover for storms/falling pressure
            elif current_trend < 0:
                return 65.0  # Moderate cloud cover for falling pressure
        return 40.0  # Normal cloud cover

    solar.analyze_cloud_cover = Mock(side_effect=mock_analyze_cloud_cover)

    return {
        "atmospheric": atmospheric,
        "solar": solar,
        "trends": trends,
    }


@pytest.fixture
def daily_forecast_generator(mock_analyzers):
    """Create DailyForecastGenerator instance for testing."""
    return DailyForecastGenerator(mock_analyzers["trends"])


class TestDailyForecastGenerator:
    """Test the DailyForecastGenerator class."""

    def test_init(self, daily_forecast_generator):
        """Test DailyForecastGenerator initialization."""
        assert daily_forecast_generator is not None
        assert daily_forecast_generator.trends_analyzer is not None

    def test_generate_forecast(self, daily_forecast_generator, mock_analyzers):
        """Test daily forecast generation."""
        current_condition = ATTR_CONDITION_PARTLYCLOUDY
        sensor_data = {
            "outdoor_temp": 72.0,
            "humidity": 60.0,
            "wind_speed": 5.0,
        }
        altitude = 100.0

        # Mock meteorological state
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 10.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.7,
            "cloud_analysis": {"cloud_cover": 40.0},
            "moisture_analysis": {"condensation_potential": 0.3},
            "wind_pattern_analysis": {
                "direction_stability": 0.8,
                "gradient_wind_effect": 3.0,
            },
        }

        historical_patterns = {
            "temperature": {"volatility": 3.0},
            "seasonal_pattern": "normal",
        }

        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        result = daily_forecast_generator.generate_forecast(
            current_condition,
            sensor_data,
            altitude,
            meteorological_state,
            historical_patterns,
            system_evolution,
        )

        assert isinstance(result, list)
        assert len(result) == 5  # Should generate 5 days of forecast

        # Check forecast structure
        forecast_item = result[0]
        assert "datetime" in forecast_item
        assert "temperature" in forecast_item
        assert "templow" in forecast_item
        assert "condition" in forecast_item
        assert "precipitation" in forecast_item
        assert "wind_speed" in forecast_item
        assert "humidity" in forecast_item

        # Check temperature is reasonable
        assert isinstance(forecast_item["temperature"], float)
        assert forecast_item["temperature"] > 0

    def test_forecast_temperature(self, daily_forecast_generator, mock_analyzers):
        """Test temperature forecasting."""
        day_idx = 0
        current_temp = 70.0
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "current_trend": 0.1,
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns = {
            "temperature": {"volatility": 3.0},
        }
        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        result = daily_forecast_generator.forecast_temperature(
            day_idx,
            current_temp,
            meteorological_state,
            historical_patterns,
            system_evolution,
        )

        assert isinstance(result, float)
        assert 65 <= result <= 75  # Should be close to input temperature

    def test_forecast_condition(self, daily_forecast_generator, mock_analyzers):
        """Test condition forecasting."""
        day_idx = 0
        current_condition = ATTR_CONDITION_PARTLYCLOUDY
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 10.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.7,
            "cloud_analysis": {"cloud_cover": 40.0},
            "moisture_analysis": {"condensation_potential": 0.3},
        }
        historical_patterns = {}
        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        result = daily_forecast_generator.forecast_condition(
            day_idx,
            current_condition,
            meteorological_state,
            historical_patterns,
            system_evolution,
        )

        assert isinstance(result, str)
        assert result in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
            ATTR_CONDITION_FOG,
            ATTR_CONDITION_SNOWY,
        ]

    def test_forecast_precipitation(self, daily_forecast_generator, mock_analyzers):
        """Test precipitation forecasting."""
        day_idx = 0
        condition = ATTR_CONDITION_PARTLYCLOUDY
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 20.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "moisture_analysis": {
                "transport_potential": 5.0,
                "condensation_potential": 0.3,
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns = {}
        sensor_data = {
            "rain_rate_unit": "mm",
        }

        result = daily_forecast_generator._forecast_precipitation(
            day_idx,
            condition,
            meteorological_state,
            historical_patterns,
            sensor_data,
        )

        assert isinstance(result, float)
        assert result >= 0

    def test_forecast_wind(self, daily_forecast_generator, mock_analyzers):
        """Test wind forecasting."""
        day_idx = 0
        current_wind = 5.0
        condition = ATTR_CONDITION_PARTLYCLOUDY
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
            },
            "wind_pattern_analysis": {
                "direction_stability": 0.8,
                "gradient_wind_effect": 3.0,
            },
        }
        historical_patterns = {
            "wind": {"volatility": 2.0},
        }

        result = daily_forecast_generator._forecast_wind(
            day_idx,
            current_wind,
            condition,
            meteorological_state,
            historical_patterns,
        )

        assert isinstance(result, float)
        assert result > 0

    def test_forecast_humidity(self, daily_forecast_generator, mock_analyzers):
        """Test humidity forecasting."""
        day_idx = 0
        current_humidity = 60.0
        meteorological_state = {
            "moisture_analysis": {"trend_direction": "increasing"},
            "atmospheric_stability": 0.7,
        }
        historical_patterns = {}
        condition = ATTR_CONDITION_PARTLYCLOUDY

        result = daily_forecast_generator._forecast_humidity(
            day_idx,
            current_humidity,
            meteorological_state,
            historical_patterns,
            condition,
        )

        assert isinstance(result, int)
        assert 10 <= result <= 100

    def test_calculate_seasonal_temperature_adjustment(self, daily_forecast_generator):
        """Test seasonal temperature adjustment calculation."""
        # Test all days in the 5-day cycle
        adjustments = []
        for day in range(5):
            adjustment = (
                daily_forecast_generator._calculate_seasonal_temperature_adjustment(day)
            )
            assert isinstance(adjustment, (int, float))
            adjustments.append(adjustment)

        # Should have some variation
        assert len(set(adjustments)) > 1  # Not all the same

        # Should be reasonable adjustments (±1-2 degrees)
        for adj in adjustments:
            assert -2 <= adj <= 2

    def test_calculate_pressure_temperature_influence(self, daily_forecast_generator):
        """Test pressure temperature influence calculation."""
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "high_pressure",
                "current_trend": 0.2,
                "long_term_trend": 0.1,
            }
        }

        result = daily_forecast_generator._calculate_pressure_temperature_influence(
            meteorological_state, 0
        )

        assert isinstance(result, float)

    def test_calculate_historical_pattern_influence(self, daily_forecast_generator):
        """Test historical pattern influence calculation."""
        historical_patterns = {
            "temperature": {"volatility": 3.0},
        }

        result = daily_forecast_generator._calculate_historical_pattern_influence(
            historical_patterns, 0, "temperature"
        )

        assert isinstance(result, float)

    def test_calculate_system_evolution_influence(self, daily_forecast_generator):
        """Test system evolution influence calculation."""
        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        result = daily_forecast_generator._calculate_system_evolution_influence(
            system_evolution, 0, "temperature"
        )

        assert isinstance(result, float)

    def test_calculate_temperature_range(self, daily_forecast_generator):
        """Test temperature range calculation."""
        meteorological_state = {"atmospheric_stability": 0.6}

        # Test different conditions
        range_sunny = daily_forecast_generator._calculate_temperature_range(
            ATTR_CONDITION_SUNNY, meteorological_state
        )
        range_cloudy = daily_forecast_generator._calculate_temperature_range(
            ATTR_CONDITION_CLOUDY, meteorological_state
        )

        assert 2.0 <= range_sunny <= 15.0
        assert 2.0 <= range_cloudy <= 15.0

        # Sunny should have larger range than cloudy
        assert range_sunny >= range_cloudy
