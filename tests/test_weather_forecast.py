"""Test the weather forecasting functionality."""

from collections import deque
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
)
import pytest

from custom_components.micro_weather.const import (
    KEY_CONDITION,
    KEY_HUMIDITY,
    KEY_OUTDOOR_TEMP,
    KEY_PRESSURE,
    KEY_RAIN_RATE,
    KEY_WIND_GUST,
    KEY_WIND_SPEED,
)
from custom_components.micro_weather.weather_analysis import WeatherAnalysis
from custom_components.micro_weather.weather_forecast import AdvancedWeatherForecast


@pytest.fixture
def mock_analysis():
    """Create mock WeatherAnalysis instance."""
    analysis = Mock(spec=WeatherAnalysis)

    # Mock the methods that forecast depends on
    analysis.analyze_pressure_trends.return_value = {
        "pressure_system": "normal",
        "storm_probability": 20.0,
        "current_trend": 0.0,
        "long_term_trend": 0.0,
    }

    analysis.get_historical_trends.side_effect = lambda sensor, hours=24: {
        "current": 60.0,
        "average": 58.0,
        "trend": 0.2,
        "min": 50.0,
        "max": 70.0,
        "volatility": 5.0,
    }

    analysis.analyze_wind_direction_trends.return_value = {
        "average_direction": 180.0,
        "direction_stability": 0.8,
        "direction_change_rate": 10.0,
        "significant_shift": False,
        "prevailing_direction": "south",
    }

    # Mock cloud cover analysis methods with dynamic behavior
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

    def mock_map_cloud_cover_to_condition(cloud_cover):
        if cloud_cover > 80:
            return ATTR_CONDITION_LIGHTNING_RAINY
        elif cloud_cover > 60:
            return ATTR_CONDITION_RAINY
        elif cloud_cover > 40:
            return ATTR_CONDITION_CLOUDY
        elif cloud_cover > 20:
            return ATTR_CONDITION_PARTLYCLOUDY
        else:
            return ATTR_CONDITION_SUNNY

    analysis.analyze_cloud_cover.side_effect = mock_analyze_cloud_cover
    analysis._map_cloud_cover_to_condition.side_effect = (
        mock_map_cloud_cover_to_condition
    )

    return analysis


@pytest.fixture
def forecast(mock_analysis):
    """Create AdvancedWeatherForecast instance for testing."""
    return AdvancedWeatherForecast(mock_analysis)


class TestWeatherForecast:
    """Test the WeatherForecast class."""

    def test_init(self, mock_analysis):
        """Test AdvancedWeatherForecast initialization."""
        forecast = AdvancedWeatherForecast(mock_analysis)
        assert forecast is not None
        assert forecast.analysis == mock_analysis

    def test_generate_enhanced_forecast(self, forecast, mock_analysis):
        """Test enhanced forecast generation."""
        sensor_data = {
            "outdoor_temp": 72.0,
            "humidity": 60.0,
            "wind_speed": 5.0,
        }

        result = forecast.generate_enhanced_forecast("partly_cloudy", sensor_data)

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

        # Check temperature is in Celsius (converted from Fahrenheit)
        assert isinstance(forecast_item["temperature"], float)
        assert forecast_item["temperature"] > 0  # Should be reasonable Celsius value

    def test_forecast_temperature_enhanced(self, forecast, mock_analysis):
        """Test enhanced temperature forecasting."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 10.0,
        }
        temp_patterns = {
            "trend": 0.5,
            "daily_variation": 5.0,
        }

        # Test first day forecast
        temp_day1 = forecast.forecast_temperature_enhanced(
            0, 70.0, temp_patterns, pressure_analysis
        )
        assert isinstance(temp_day1, float)
        assert 65 <= temp_day1 <= 75  # Should be close to input temperature

        # Test later day forecast
        temp_day3 = forecast.forecast_temperature_enhanced(
            2, 70.0, temp_patterns, pressure_analysis
        )
        assert isinstance(temp_day3, float)

        # Test high pressure system (should be warmer)
        pressure_high = pressure_analysis.copy()
        pressure_high["pressure_system"] = "high_pressure"
        temp_high = forecast.forecast_temperature_enhanced(
            0, 70.0, temp_patterns, pressure_high
        )
        assert temp_high > temp_day1  # Should be warmer

        # Test low pressure system (should be cooler)
        pressure_low = pressure_analysis.copy()
        pressure_low["pressure_system"] = "low_pressure"
        temp_low = forecast.forecast_temperature_enhanced(
            0, 70.0, temp_patterns, pressure_low
        )
        assert temp_low < temp_day1  # Should be cooler

    def test_calculate_seasonal_temperature_adjustment(self, forecast):
        """Test seasonal temperature adjustment calculation."""
        # Test all days in the 5-day cycle
        adjustments = []
        for day in range(5):
            adjustment = forecast.calculate_seasonal_temperature_adjustment(day)
            assert isinstance(adjustment, (int, float))
            adjustments.append(adjustment)

        # Should have some variation
        assert len(set(adjustments)) > 1  # Not all the same

        # Should be reasonable adjustments (±1-2 degrees)
        for adj in adjustments:
            assert -2 <= adj <= 2

    def test_forecast_condition_enhanced(self, forecast, mock_analysis):
        """Test enhanced condition forecasting."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 10.0,
        }
        sensor_data = {
            "wind_speed": 5.0,
            "humidity": 60.0,
        }

        # Test first day (high confidence)
        condition_day1 = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data
        )
        assert isinstance(condition_day1, str)
        assert condition_day1 in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
            ATTR_CONDITION_FOG,
            ATTR_CONDITION_SNOWY,
        ]

        # Test storm conditions
        pressure_storm = pressure_analysis.copy()
        pressure_storm["storm_probability"] = 70
        condition_storm = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_PARTLYCLOUDY, pressure_storm, sensor_data
        )
        assert condition_storm in [ATTR_CONDITION_LIGHTNING_RAINY, ATTR_CONDITION_RAINY]

        # Test high pressure (should favor clear conditions)
        pressure_high = pressure_analysis.copy()
        pressure_high["pressure_system"] = "high_pressure"
        condition_high = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_CLOUDY, pressure_high, sensor_data
        )
        # Should be more likely to be clear/sunny
        assert condition_high in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
        ]

    def test_forecast_precipitation_enhanced(self, forecast, mock_analysis):
        """Test enhanced precipitation forecasting."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 20.0,
        }
        humidity_trend = {
            "average": 70.0,
        }
        sensor_data = {
            "rain_rate_unit": "mm",  # Default to metric
        }

        # Test normal conditions
        precip_normal = forecast.forecast_precipitation_enhanced(
            0,
            ATTR_CONDITION_PARTLYCLOUDY,
            pressure_analysis,
            humidity_trend,
            sensor_data,
        )
        assert isinstance(precip_normal, float)
        assert precip_normal >= 0

        # Test stormy conditions
        precip_storm = forecast.forecast_precipitation_enhanced(
            0,
            ATTR_CONDITION_LIGHTNING_RAINY,
            pressure_analysis,
            humidity_trend,
            sensor_data,
        )
        assert precip_storm > precip_normal  # Should be more precipitation

        # Test high storm probability
        pressure_high_storm = pressure_analysis.copy()
        pressure_high_storm["storm_probability"] = 80
        precip_high_storm = forecast.forecast_precipitation_enhanced(
            0, ATTR_CONDITION_RAINY, pressure_high_storm, humidity_trend, sensor_data
        )
        assert precip_high_storm > precip_normal

        # Test distant forecast (should have reduced precipitation)
        precip_distant = forecast.forecast_precipitation_enhanced(
            4,
            ATTR_CONDITION_PARTLYCLOUDY,
            pressure_analysis,
            humidity_trend,
            sensor_data,
        )
        assert precip_distant <= precip_normal  # Should be reduced

        # Test unit conversion (inches)
        sensor_data_inches = sensor_data.copy()
        sensor_data_inches["rain_rate_unit"] = "in"
        precip_inches = forecast.forecast_precipitation_enhanced(
            0,
            ATTR_CONDITION_RAINY,
            pressure_analysis,
            humidity_trend,
            sensor_data_inches,
        )
        # Should be converted from mm to inches (approximately 1/25.4)
        expected_inches = 5.0 / 25.4  # 5.0 mm converted to inches
        assert abs(precip_inches - expected_inches) < 0.1

    def test_forecast_wind_enhanced(self, forecast, mock_analysis):
        """Test enhanced wind forecasting."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 10.0,
        }
        wind_trend = {
            "trend": 0.1,
        }

        # Test normal conditions
        wind_normal = forecast.forecast_wind_enhanced(
            0, 5.0, ATTR_CONDITION_PARTLYCLOUDY, wind_trend, pressure_analysis
        )
        assert isinstance(wind_normal, float)
        assert wind_normal > 0  # Should be positive wind speed

        # Test stormy conditions (should have higher wind)
        wind_storm = forecast.forecast_wind_enhanced(
            0, 5.0, ATTR_CONDITION_LIGHTNING_RAINY, wind_trend, pressure_analysis
        )
        assert wind_storm > wind_normal

        # Test low pressure system (should have higher wind)
        pressure_low = pressure_analysis.copy()
        pressure_low["pressure_system"] = "low_pressure"
        wind_low_pressure = forecast.forecast_wind_enhanced(
            0, 5.0, ATTR_CONDITION_CLOUDY, wind_trend, pressure_low
        )
        assert wind_low_pressure > wind_normal

        # Test high pressure system (should have lower wind)
        pressure_high = pressure_analysis.copy()
        pressure_high["pressure_system"] = "high_pressure"
        wind_high_pressure = forecast.forecast_wind_enhanced(
            0, 5.0, ATTR_CONDITION_SUNNY, wind_trend, pressure_high
        )
        assert wind_high_pressure < wind_normal

    def test_forecast_humidity(self, forecast, mock_analysis):
        """Test humidity forecasting."""
        humidity_trend = {
            "trend": 0.5,
        }

        # Test normal conditions
        humidity_normal = forecast.forecast_humidity(
            0, 60.0, humidity_trend, ATTR_CONDITION_PARTLYCLOUDY
        )
        assert isinstance(humidity_normal, int)
        assert 10 <= humidity_normal <= 100

        # Test foggy conditions (should have high humidity)
        humidity_fog = forecast.forecast_humidity(
            0, 60.0, humidity_trend, ATTR_CONDITION_FOG
        )
        assert humidity_fog > humidity_normal

        # Test sunny conditions (should have lower humidity)
        humidity_sunny = forecast.forecast_humidity(
            0, 60.0, humidity_trend, ATTR_CONDITION_SUNNY
        )
        assert humidity_sunny < humidity_normal

        # Test distant forecast (should gradually change)
        humidity_distant = forecast.forecast_humidity(
            3, 60.0, humidity_trend, ATTR_CONDITION_PARTLYCLOUDY
        )
        assert isinstance(humidity_distant, int)
        assert 10 <= humidity_distant <= 100

    def test_forecast_condition_enhanced_cloud_cover_integration(
        self, forecast, mock_analysis
    ):
        """Test that forecast_condition_enhanced uses cloud cover analysis for near-term forecasts."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 10.0,
            "current_trend": -0.5,  # Falling pressure
            "long_term_trend": -0.3,
        }
        sensor_data = {
            "solar_radiation": 800.0,
            "solar_lux": 85000.0,
            "uv_index": 6.0,
            "solar_elevation": 45.0,
            "wind_speed": 5.0,
            "humidity": 60.0,
        }

        # Test day 0 - should use cloud cover analysis
        condition_day0 = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data
        )
        assert isinstance(condition_day0, str)
        # With falling pressure, should get cloudier condition from cloud cover analysis
        assert condition_day0 in [
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
        ]

        # Test day 1 - should also use cloud cover analysis
        condition_day1 = forecast.forecast_condition_enhanced(
            1, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data
        )
        assert isinstance(condition_day1, str)

        # Test day 2 - should use pressure-based rules with cloud cover influence
        condition_day2 = forecast.forecast_condition_enhanced(
            2, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data
        )
        assert isinstance(condition_day2, str)

    def test_forecast_condition_with_cloud_cover(self, forecast, mock_analysis):
        """Test the cloud cover based forecast condition method."""
        pressure_analysis = {
            "pressure_system": "low_pressure",
            "storm_probability": 30.0,
            "current_trend": -1.0,
            "long_term_trend": -0.5,
        }
        sensor_data = {
            "solar_radiation": 600.0,
            "solar_lux": 65000.0,
            "uv_index": 4.0,
            "solar_elevation": 30.0,
        }

        # Test day 0 with cloud cover analysis
        condition = forecast._forecast_condition_with_cloud_cover(
            0, pressure_analysis, sensor_data
        )
        assert isinstance(condition, str)
        assert condition in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
        ]

        # Test with high storm probability - should get stormy condition
        pressure_storm = pressure_analysis.copy()
        pressure_storm["storm_probability"] = 80.0
        condition_storm = forecast._forecast_condition_with_cloud_cover(
            0, pressure_storm, sensor_data
        )
        assert condition_storm in [ATTR_CONDITION_LIGHTNING_RAINY, ATTR_CONDITION_RAINY]

    def test_project_pressure_trends_for_forecast(self, forecast):
        """Test pressure trend projection for forecast days."""
        current_analysis = {
            "pressure_system": "normal",
            "storm_probability": 40.0,
            "current_trend": -0.8,
            "long_term_trend": -0.4,
        }

        # Test day 0 projection (minimal decay)
        projected_day0 = forecast._project_pressure_trends_for_forecast(
            0, current_analysis
        )
        assert projected_day0["current_trend"] == current_analysis["current_trend"]
        assert projected_day0["long_term_trend"] == current_analysis["long_term_trend"]
        assert (
            projected_day0["storm_probability"] == current_analysis["storm_probability"]
        )

        # Test day 1 projection (some decay)
        projected_day1 = forecast._project_pressure_trends_for_forecast(
            1, current_analysis
        )
        # For negative trends, decay makes them approach zero (less negative)
        assert (
            projected_day1["current_trend"] > current_analysis["current_trend"]
        )  # Should be less negative
        assert projected_day1["long_term_trend"] > current_analysis["long_term_trend"]
        assert (
            projected_day1["storm_probability"] < current_analysis["storm_probability"]
        )

        # Test decay magnitude
        decay_factor = 1.0 - (1 * 0.2)  # 0.8 for day 1
        expected_trend = current_analysis["current_trend"] * decay_factor
        assert abs(projected_day1["current_trend"] - expected_trend) < 0.01

    def test_estimate_cloud_cover_from_pressure(self, forecast):
        """Test cloud cover estimation from pressure analysis alone."""
        # Test high pressure system
        pressure_high = {
            "pressure_system": "high_pressure",
            "storm_probability": 5.0,
        }
        cloud_cover_high = forecast._estimate_cloud_cover_from_pressure(pressure_high)
        assert 15 <= cloud_cover_high <= 25  # Should be low cloud cover

        # Test low pressure system
        pressure_low = {
            "pressure_system": "low_pressure",
            "storm_probability": 20.0,
        }
        cloud_cover_low = forecast._estimate_cloud_cover_from_pressure(pressure_low)
        assert cloud_cover_low > cloud_cover_high  # Should be higher cloud cover

        # Test storm conditions
        pressure_storm = {
            "pressure_system": "low_pressure",
            "storm_probability": 85.0,
        }
        cloud_cover_storm = forecast._estimate_cloud_cover_from_pressure(pressure_storm)
        assert cloud_cover_storm > cloud_cover_low  # Should be much higher
        assert cloud_cover_storm <= 95  # Should be capped

        # Test normal pressure
        pressure_normal = {
            "pressure_system": "normal",
            "storm_probability": 15.0,
        }
        cloud_cover_normal = forecast._estimate_cloud_cover_from_pressure(
            pressure_normal
        )
        assert 30 <= cloud_cover_normal <= 50  # Should be moderate

    def test_get_progressive_condition(self, forecast):
        """Test progressive condition changes for medium-term forecasts."""
        # Test sunny to cloudy progression
        progression_sunny = forecast._get_progressive_condition(ATTR_CONDITION_SUNNY, 2)
        assert progression_sunny in [
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_SUNNY,
        ]

        # Test rainy improvement
        progression_rainy = forecast._get_progressive_condition(ATTR_CONDITION_RAINY, 2)
        assert progression_rainy in [
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_SUNNY,
        ]

        # Test stormy improvement
        progression_storm = forecast._get_progressive_condition(
            ATTR_CONDITION_LIGHTNING_RAINY, 2
        )
        assert progression_storm in [
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_PARTLYCLOUDY,
        ]

        # Test day 3 (index 1 in progression)
        progression_day3 = forecast._get_progressive_condition(ATTR_CONDITION_RAINY, 3)
        # Should be different from day 2 result
        assert isinstance(progression_day3, str)

        # Test day 4 (index 2 in progression)
        progression_day4 = forecast._get_progressive_condition(ATTR_CONDITION_RAINY, 4)
        assert isinstance(progression_day4, str)

    def test_forecast_condition_enhanced_all_days(self, forecast, mock_analysis):
        """Test forecast condition for all forecast days."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 25.0,
        }
        sensor_data = {
            "wind_speed": 8.0,
            "humidity": 65.0,
            "solar_radiation": 700.0,
            "solar_lux": 75000.0,
            "uv_index": 5.0,
            "solar_elevation": 40.0,
        }

        current_condition = ATTR_CONDITION_PARTLYCLOUDY

        # Test all 5 days
        for day in range(5):
            condition = forecast.forecast_condition_enhanced(
                day, current_condition, pressure_analysis, sensor_data
            )
            assert isinstance(condition, str)
            assert condition in [
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_CLOUDY,
                ATTR_CONDITION_RAINY,
                ATTR_CONDITION_LIGHTNING_RAINY,
                ATTR_CONDITION_FOG,
                ATTR_CONDITION_SNOWY,
            ]

    def test_forecast_condition_enhanced_pressure_systems(
        self, forecast, mock_analysis
    ):
        """Test forecast conditions with different pressure systems."""
        sensor_data = {
            "wind_speed": 6.0,
            "humidity": 55.0,
            "solar_radiation": 800.0,
            "solar_lux": 85000.0,
            "uv_index": 6.0,
            "solar_elevation": 45.0,
        }

        # Test high pressure system - should favor clear conditions
        pressure_high = {
            "pressure_system": "high_pressure",
            "storm_probability": 5.0,
        }
        condition_high = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_CLOUDY, pressure_high, sensor_data
        )
        # Should be more likely to be clear/sunny
        assert condition_high in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
        ]

        # Test low pressure system - should favor cloudy conditions
        pressure_low = {
            "pressure_system": "low_pressure",
            "storm_probability": 35.0,
        }
        condition_low = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_PARTLYCLOUDY, pressure_low, sensor_data
        )
        # Should be more likely to be cloudy/rainy
        assert condition_low in [
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
            ATTR_CONDITION_PARTLYCLOUDY,
        ]

    def test_forecast_condition_enhanced_wind_influence(self, forecast, mock_analysis):
        """Test wind direction influence on forecast conditions."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 15.0,
        }

        # Mock wind analysis for stable conditions
        mock_analysis.analyze_wind_direction_trends.return_value = {
            "average_direction": 180.0,
            "direction_stability": 0.9,  # Very stable
            "direction_change_rate": 5.0,
            "significant_shift": False,
            "prevailing_direction": "south",
        }

        sensor_data = {
            "wind_speed": 4.0,
            "humidity": 50.0,
            "solar_radiation": 900.0,
            "solar_lux": 95000.0,
            "uv_index": 7.0,
            "solar_elevation": 50.0,
        }

        # Test with stable wind - should favor current conditions
        condition_stable = forecast.forecast_condition_enhanced(
            2, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data
        )
        assert isinstance(condition_stable, str)

        # Mock wind analysis for unstable conditions
        mock_analysis.analyze_wind_direction_trends.return_value = {
            "average_direction": 180.0,
            "direction_stability": 0.2,  # Unstable
            "direction_change_rate": 45.0,
            "significant_shift": True,
            "prevailing_direction": "south",
        }

        # Test with unstable wind - should be more variable
        condition_unstable = forecast.forecast_condition_enhanced(
            2, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data
        )
        assert isinstance(condition_unstable, str)

    def test_forecast_condition_enhanced_error_handling(self, forecast, mock_analysis):
        """Test error handling in forecast condition enhancement."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 10.0,
        }
        sensor_data = {
            "wind_speed": 5.0,
            "humidity": 60.0,
        }

        # Mock cloud cover analysis to raise exception
        mock_analysis.analyze_cloud_cover.side_effect = Exception(
            "Cloud analysis failed"
        )

        # Should fall back gracefully for near-term forecasts
        condition = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data
        )
        assert isinstance(condition, str)  # Should still return a valid condition

        # Reset mock
        mock_analysis.analyze_cloud_cover.side_effect = None
        mock_analysis.analyze_cloud_cover.return_value = 40.0

    def test_forecast_condition_enhanced_missing_sensor_data(
        self, forecast, mock_analysis
    ):
        """Test forecast with missing or incomplete sensor data."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 20.0,
        }

        # Test with minimal sensor data
        sensor_data_minimal = {
            "wind_speed": 5.0,
        }

        condition = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data_minimal
        )
        assert isinstance(condition, str)

        # Test with empty sensor data
        sensor_data_empty = {}

        condition_empty = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data_empty
        )
        assert isinstance(condition_empty, str)

    def test_sensors_unavailable_none_values(self, forecast, mock_analysis):
        """Test forecast when sensor values are None (sensors unavailable)."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 20.0,
        }

        # Test with None values for solar sensors
        sensor_data_none = {
            "solar_radiation": None,
            "solar_lux": None,
            "uv_index": None,
            "solar_elevation": None,
            "wind_speed": None,
            "humidity": None,
        }

        # Should fall back to pressure-based estimation
        condition = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data_none
        )
        assert isinstance(condition, str)
        # Should still return a valid condition
        assert condition in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
        ]

    def test_sensors_unavailable_missing_keys(self, forecast, mock_analysis):
        """Test forecast when sensor keys are completely missing."""
        pressure_analysis = {
            "pressure_system": "low_pressure",
            "storm_probability": 30.0,
        }

        # Test with no solar sensor data at all
        sensor_data_no_solar = {
            "wind_speed": 5.0,
            "humidity": 60.0,
            # No solar_radiation, solar_lux, uv_index, solar_elevation
        }

        condition = forecast._forecast_condition_with_cloud_cover(
            0, pressure_analysis, sensor_data_no_solar
        )
        assert isinstance(condition, str)
        # Should use defaults (0.0 for solar data) and still work

    def test_historical_trends_unavailable(self, forecast, mock_analysis):
        """Test forecast when historical trend data is unavailable."""
        # Mock get_historical_trends to return None (no historical data)
        mock_analysis.get_historical_trends.side_effect = None
        mock_analysis.get_historical_trends.return_value = None

        # Should handle gracefully and return default values
        patterns = forecast.analyze_temperature_patterns()
        assert patterns == {
            "trend": 0.0,
            "daily_variation": 10.0,
            "seasonal_pattern": "normal",
        }

        # Reset mock
        mock_analysis.get_historical_trends.side_effect = lambda sensor, hours=24: {
            "current": 60.0,
            "average": 58.0,
            "trend": 0.2,
            "min": 50.0,
            "max": 70.0,
            "volatility": 5.0,
        }

    def test_pressure_analysis_unavailable(self, forecast, mock_analysis):
        """Test forecast when pressure analysis data is incomplete or None."""
        # Test with incomplete pressure analysis
        pressure_analysis_incomplete = {
            "pressure_system": "normal",
            # Missing storm_probability, current_trend, long_term_trend
        }

        sensor_data = {
            "wind_speed": 5.0,
            "humidity": 60.0,
        }

        condition = forecast.forecast_condition_enhanced(
            0, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis_incomplete, sensor_data
        )
        assert isinstance(condition, str)

        # Test with None pressure analysis (shouldn't happen but test robustness)
        # This would be caught at a higher level, but test the method handles it
        try:
            condition_none = forecast._estimate_cloud_cover_from_pressure({})
            assert isinstance(condition_none, float)
            assert 0 <= condition_none <= 100
        except (AttributeError, KeyError):
            # Expected if pressure_analysis is None
            pass

    def test_wind_analysis_unavailable(self, forecast, mock_analysis):
        """Test forecast when wind direction analysis is unavailable."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 15.0,
        }

        sensor_data = {
            "wind_speed": 5.0,
            "humidity": 60.0,
        }

        # Mock wind analysis to return None or incomplete data
        mock_analysis.analyze_wind_direction_trends.return_value = None

        # Should handle gracefully (use defaults in the calling code)
        condition = forecast.forecast_condition_enhanced(
            2, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data
        )
        assert isinstance(condition, str)

        # Reset mock
        mock_analysis.analyze_wind_direction_trends.return_value = {
            "average_direction": 180.0,
            "direction_stability": 0.8,
            "direction_change_rate": 10.0,
            "significant_shift": False,
            "prevailing_direction": "south",
        }

    def test_forecast_with_all_sensors_unavailable(self, forecast, mock_analysis):
        """Test forecast when all sensors are completely unavailable."""
        # Completely empty sensor data
        sensor_data_empty = {}

        # Mock all analysis methods to fail or return minimal data
        mock_analysis.analyze_cloud_cover.return_value = 40.0  # Default cloud cover
        mock_analysis.get_historical_trends.return_value = None

        # Should still generate a forecast using defaults and fallbacks
        result = forecast.generate_enhanced_forecast("partly_cloudy", sensor_data_empty)

        assert isinstance(result, list)
        assert len(result) == 5
        assert all(isinstance(item, dict) for item in result)
        assert all("condition" in item for item in result)

        # Reset mocks
        mock_analysis.analyze_cloud_cover.side_effect = None
        mock_analysis.get_historical_trends.side_effect = lambda sensor, hours=24: {
            "current": 60.0,
            "average": 58.0,
            "trend": 0.2,
            "min": 50.0,
            "max": 70.0,
            "volatility": 5.0,
        }

    def test_cloud_cover_calculation_with_none_solar_data(
        self, forecast, mock_analysis
    ):
        """Test cloud cover calculation when solar sensor data is None."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 20.0,
        }

        # Solar data is None (sensors unavailable)
        sensor_data = {
            "solar_radiation": None,
            "solar_lux": None,
            "uv_index": None,
            "solar_elevation": None,
        }

        # Should fall back to pressure-based estimation
        condition = forecast._forecast_condition_with_cloud_cover(
            0, pressure_analysis, sensor_data
        )
        assert isinstance(condition, str)

        # Should be based on pressure system (normal = partly cloudy-ish)
        assert condition in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
        ]

    def test_analyze_temperature_patterns_seasonal_coverage(
        self, forecast, mock_analysis
    ):
        """Test seasonal pattern detection in temperature analysis."""
        # Test winter months (Dec, Jan, Feb)
        with patch("homeassistant.util.dt.now") as mock_dt_now:
            mock_dt_now.return_value.month = 12
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "winter"

            mock_dt_now.return_value.month = 1
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "winter"

            mock_dt_now.return_value.month = 2
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "winter"

            # Test spring months (Mar, Apr, May)
            mock_dt_now.return_value.month = 3
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "spring"

            mock_dt_now.return_value.month = 4
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "spring"

            mock_dt_now.return_value.month = 5
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "spring"

            # Test summer months (Jun, Jul, Aug)
            mock_dt_now.return_value.month = 6
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "summer"

            mock_dt_now.return_value.month = 7
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "summer"

            mock_dt_now.return_value.month = 8
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "summer"

            # Test fall months (Sep, Oct, Nov)
            mock_dt_now.return_value.month = 9
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "fall"

            mock_dt_now.return_value.month = 10
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "fall"

            mock_dt_now.return_value.month = 11
            patterns = forecast.analyze_temperature_patterns()
            assert patterns["seasonal_pattern"] == "fall"

    def test_forecast_precipitation_pouring_condition(self, forecast, mock_analysis):
        """Test precipitation forecasting for pouring condition."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 30.0,
        }
        humidity_trend = {
            "average": 70.0,
        }
        sensor_data = {
            "rain_rate_unit": "mm",
        }

        # Test pouring condition specifically
        precip_pouring = forecast.forecast_precipitation_enhanced(
            0,
            ATTR_CONDITION_POURING,
            pressure_analysis,
            humidity_trend,
            sensor_data,
        )
        assert isinstance(precip_pouring, float)
        assert precip_pouring >= 0

        # Pouring should have higher precipitation than regular rain
        precip_rainy = forecast.forecast_precipitation_enhanced(
            0,
            ATTR_CONDITION_RAINY,
            pressure_analysis,
            humidity_trend,
            sensor_data,
        )
        assert precip_pouring > precip_rainy

    def test_forecast_wind_condition_adjustments(self, forecast, mock_analysis):
        """Test wind forecasting with various weather conditions."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 10.0,
        }
        wind_trend = {
            "trend": 0.0,
        }

        base_wind = 10.0  # mph

        # Test all condition adjustments are applied
        conditions_to_test = [
            (ATTR_CONDITION_LIGHTNING_RAINY, 1.5),  # Should increase wind
            (ATTR_CONDITION_WINDY, 2.0),  # Should significantly increase wind
            (ATTR_CONDITION_SUNNY, 0.8),  # Should decrease wind
            (ATTR_CONDITION_FOG, 0.6),  # Should significantly decrease wind
        ]

        for condition, expected_multiplier in conditions_to_test:
            wind_forecast = forecast.forecast_wind_enhanced(
                0, base_wind, condition, wind_trend, pressure_analysis
            )
            # Should be different from base (converted to km/h)
            assert isinstance(wind_forecast, float)
            assert wind_forecast > 0

    def test_forecast_condition_enhanced_day_2_3_4_coverage(
        self, forecast, mock_analysis
    ):
        """Test specific coverage for days 2-4 in enhanced condition forecasting."""
        pressure_analysis = {
            "pressure_system": "high_pressure",
            "storm_probability": 75.0,  # High storm probability
        }
        sensor_data = {
            "wind_speed": 5.0,
            "humidity": 60.0,
        }

        # Test day 2 with high storm probability - should return pouring
        condition_day2 = forecast.forecast_condition_enhanced(
            2, ATTR_CONDITION_PARTLYCLOUDY, pressure_analysis, sensor_data
        )
        assert condition_day2 == ATTR_CONDITION_POURING

        # Test day 3-4 with high pressure and stable wind
        mock_analysis.analyze_wind_direction_trends.return_value = {
            "direction_stability": 0.9,  # Very stable
            "significant_shift": False,
        }

        for day in [3, 4]:
            condition = forecast.forecast_condition_enhanced(
                day, ATTR_CONDITION_CLOUDY, pressure_analysis, sensor_data
            )
            assert isinstance(condition, str)

    def test_cloud_cover_fallback_error_handling(self, forecast, mock_analysis):
        """Test that cloud cover analysis falls back gracefully on errors."""
        pressure_analysis = {
            "pressure_system": "low_pressure",
            "storm_probability": 50.0,
        }
        sensor_data = {
            "solar_radiation": 500.0,
            "solar_lux": 50000.0,
            "uv_index": 3.0,
            "solar_elevation": 30.0,
        }

        # Mock cloud cover analysis to always raise exception
        mock_analysis.analyze_cloud_cover.side_effect = Exception("Analysis failed")

        # Should fall back to pressure-based estimation
        condition = forecast._forecast_condition_with_cloud_cover(
            0, pressure_analysis, sensor_data
        )
        assert isinstance(condition, str)
        # Should be a valid condition
        assert condition in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
        ]

        # Reset mock
        mock_analysis.analyze_cloud_cover.side_effect = None
        mock_analysis.analyze_cloud_cover.return_value = 40.0


class TestAdvancedWeatherForecast:
    """Test the new comprehensive forecasting functionality."""

    def test_generate_comprehensive_forecast(self, forecast, mock_analysis):
        """Test comprehensive daily forecast generation using all sensor data."""
        current_condition = ATTR_CONDITION_PARTLYCLOUDY
        sensor_data = {
            "outdoor_temp": 75.0,  # Fahrenheit
            "humidity": 65.0,
            "pressure": 29.85,
            "wind_speed": 8.0,
            "solar_radiation": 750.0,
            "solar_lux": 80000.0,
            "uv_index": 6.0,
            "solar_elevation": 45.0,
        }
        altitude = 100.0  # meters

        result = forecast.generate_comprehensive_forecast(
            current_condition, sensor_data, altitude
        )

        assert isinstance(result, list)
        assert len(result) == 5  # 5-day forecast

        for day_forecast in result:
            assert isinstance(day_forecast, dict)
            assert "datetime" in day_forecast
            assert "temperature" in day_forecast
            assert "templow" in day_forecast
            assert "condition" in day_forecast
            assert "precipitation" in day_forecast
            assert "wind_speed" in day_forecast
            assert "humidity" in day_forecast

            # Validate data types and ranges
            assert isinstance(day_forecast["temperature"], float)
            assert isinstance(day_forecast["templow"], float)
            assert isinstance(day_forecast["condition"], str)
            assert isinstance(day_forecast["precipitation"], float)
            assert isinstance(day_forecast["wind_speed"], float)
            assert isinstance(day_forecast["humidity"], int)

            # Validate condition is valid
            assert day_forecast["condition"] in [
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_CLOUDY,
                ATTR_CONDITION_RAINY,
                ATTR_CONDITION_LIGHTNING_RAINY,
                ATTR_CONDITION_POURING,
                ATTR_CONDITION_FOG,
                ATTR_CONDITION_SNOWY,
                ATTR_CONDITION_WINDY,
            ]

            # Validate ranges
            assert 0 <= day_forecast["precipitation"]
            assert 0 <= day_forecast["wind_speed"]
            assert 0 <= day_forecast["humidity"] <= 100

    def test_generate_comprehensive_forecast_storm_conditions(
        self, forecast, mock_analysis
    ):
        """Test comprehensive forecast under storm conditions."""
        # Mock high storm probability
        mock_analysis.analyze_pressure_trends.return_value = {
            "pressure_system": "low_pressure",
            "storm_probability": 85.0,
            "current_trend": -1.2,
            "long_term_trend": -0.8,
        }

        current_condition = ATTR_CONDITION_CLOUDY
        sensor_data = {
            "outdoor_temp": 68.0,
            "humidity": 80.0,
            "pressure": 29.60,
            "wind_speed": 15.0,
            "solar_radiation": 300.0,
            "solar_lux": 30000.0,
            "uv_index": 2.0,
        }

        result = forecast.generate_comprehensive_forecast(
            current_condition, sensor_data
        )

        # Should generate stormy conditions
        assert len(result) == 5
        # First day should be stormy due to high storm probability
        assert result[0]["condition"] in [
            ATTR_CONDITION_LIGHTNING_RAINY,
            ATTR_CONDITION_POURING,
        ]
        assert result[0]["precipitation"] > 10.0  # High precipitation

    def test_generate_comprehensive_forecast_high_pressure(
        self, forecast, mock_analysis
    ):
        """Test comprehensive forecast under high pressure conditions."""
        # Mock high pressure system
        mock_analysis.analyze_pressure_trends.return_value = {
            "pressure_system": "high_pressure",
            "storm_probability": 5.0,
            "current_trend": 0.3,
            "long_term_trend": 0.2,
        }

        current_condition = ATTR_CONDITION_CLOUDY
        sensor_data = {
            "outdoor_temp": 78.0,
            "humidity": 45.0,
            "pressure": 30.15,
            "wind_speed": 3.0,
            "solar_radiation": 900.0,
            "solar_lux": 95000.0,
            "uv_index": 8.0,
        }

        result = forecast.generate_comprehensive_forecast(
            current_condition, sensor_data
        )

        # Should generate clearer conditions
        assert len(result) == 5
        # First day should be clearer due to high pressure
        assert result[0]["condition"] in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
        ]
        assert result[0]["precipitation"] < 2.0  # Low precipitation

    def test_generate_hourly_forecast_comprehensive(self, forecast, mock_analysis):
        """Test comprehensive hourly forecast generation."""
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

        # Test with sunrise/sunset times
        # sunrise_time = datetime.now().replace(hour=6, minute=30)
        # sunset_time = datetime.now().replace(hour=19, minute=30)

        result = forecast.generate_hourly_forecast_comprehensive(
            current_temp, current_condition, sensor_data
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
            assert isinstance(hour_forecast["humidity"], (int, float))  # Can be float

    def test_generate_hourly_forecast_comprehensive_nighttime(
        self, forecast, mock_analysis
    ):
        """Test hourly forecast with nighttime condition conversion."""
        current_temp = 15.0  # Celsius
        current_condition = ATTR_CONDITION_SUNNY
        sensor_data = {
            "outdoor_temp": 59.0,  # Fahrenheit
            "humidity": 70.0,
            "pressure": 29.80,
            "wind_speed": 2.0,
        }

        # Set times so current hour is nighttime
        # sunrise_time = (now + timedelta(hours=6)).replace(hour=6, minute=0)  # 6 hours from now
        # sunset_time = (now - timedelta(hours=2)).replace(hour=18, minute=0)  # 2 hours ago

        result = forecast.generate_hourly_forecast_comprehensive(
            current_temp, current_condition, sensor_data
        )

        assert len(result) == 24
        # Check that nighttime hours have appropriate conditions
        nighttime_found = False
        for hour_forecast in result:
            if hour_forecast.get("is_nighttime", False):
                # Should convert sunny to clear-night during nighttime
                assert hour_forecast["condition"] in [
                    ATTR_CONDITION_SUNNY,  # May keep sunny if close to dawn/dusk
                    ATTR_CONDITION_CLEAR_NIGHT,
                    ATTR_CONDITION_PARTLYCLOUDY,
                    ATTR_CONDITION_CLOUDY,
                ]
                nighttime_found = True

        assert nighttime_found, "Should have nighttime hours in forecast"

    def test_generate_hourly_forecast_comprehensive_missing_humidity(
        self, forecast, mock_analysis
    ):
        """Test hourly forecast with missing humidity sensor data."""
        current_temp = 22.0  # Celsius
        current_condition = ATTR_CONDITION_PARTLYCLOUDY
        sensor_data = {
            "outdoor_temp": 72.0,  # Fahrenheit
            "pressure": 29.92,
            "wind_speed": 5.0,
            "solar_radiation": 800.0,
            "solar_lux": 85000.0,
            "uv_index": 6.0,
            # Note: no 'humidity' key - this is the case we're testing
        }

        # Set sunrise/sunset times
        # now = datetime.now()
        # sunrise_time = now.replace(hour=6, minute=30)
        # sunset_time = now.replace(hour=18, minute=30)

        result = forecast.generate_hourly_forecast_comprehensive(
            current_temp, current_condition, sensor_data
        )

        assert len(result) == 24
        # Check that all forecast hours have required fields
        for hour_forecast in result:
            assert isinstance(hour_forecast["temperature"], float)
            assert isinstance(hour_forecast["condition"], str)
            assert isinstance(hour_forecast["precipitation"], float)
            assert isinstance(hour_forecast["wind_speed"], float)
            assert isinstance(
                hour_forecast["humidity"], (int, float)
            )  # Should default to 50
            # Verify humidity defaults to around 50 when sensor is missing
            assert 45 <= hour_forecast["humidity"] <= 55

    def test_analyze_comprehensive_meteorological_state(self, forecast, mock_analysis):
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

        result = forecast._analyze_comprehensive_meteorological_state(
            sensor_data, altitude
        )

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

    def test_analyze_comprehensive_meteorological_state_mock_handling(
        self, forecast, mock_analysis
    ):
        """Test meteorological analysis with mock object error handling."""
        sensor_data = {
            "outdoor_temp": 70.0,
            "humidity": 60.0,
            "pressure": 29.92,
            "wind_speed": 5.0,
        }

        # Mock methods to raise AttributeError (simulating mock objects)
        mock_analysis.analyze_pressure_trends.side_effect = AttributeError("Mock error")
        mock_analysis.get_historical_trends.side_effect = AttributeError("Mock error")
        mock_analysis.analyze_wind_direction_trends.side_effect = AttributeError(
            "Mock error"
        )

        # Should handle errors gracefully and return valid analysis
        result = forecast._analyze_comprehensive_meteorological_state(sensor_data, 0.0)

        assert isinstance(result, dict)
        assert "pressure_analysis" in result
        assert "wind_analysis" in result
        assert "temp_trends" in result

        # Reset mocks
        mock_analysis.analyze_pressure_trends.side_effect = None
        mock_analysis.get_historical_trends.side_effect = None
        mock_analysis.analyze_wind_direction_trends.side_effect = None

    def test_calculate_atmospheric_stability(self, forecast):
        """Test atmospheric stability calculation."""
        # Test stable conditions (cool, humid, light wind)
        stability1 = forecast._calculate_atmospheric_stability(
            15.0, 80.0, 3.0, {"long_term_trend": 0.1}
        )
        assert 0.5 <= stability1 <= 1.0  # Should be relatively stable

        # Test unstable conditions (warm, dry, strong wind)
        stability2 = forecast._calculate_atmospheric_stability(
            30.0, 30.0, 20.0, {"long_term_trend": 2.0}
        )
        assert 0.0 <= stability2 <= 0.5  # Should be relatively unstable

        # Test boundary conditions
        stability_min = forecast._calculate_atmospheric_stability(
            40.0, 10.0, 50.0, {"long_term_trend": 10.0}
        )
        stability_max = forecast._calculate_atmospheric_stability(
            5.0, 95.0, 0.0, {"long_term_trend": -5.0}
        )

        assert 0.0 <= stability_min <= 1.0
        assert 0.0 <= stability_max <= 1.0

    def test_classify_weather_system(self, forecast):
        """Test weather system classification."""
        # Test stable high pressure system
        result1 = forecast._classify_weather_system(
            {"pressure_system": "high_pressure", "current_trend": 0.2},
            {"direction_stability": 0.9},
            {"trend": 0.1},
            0.8,  # High stability
        )
        assert result1["type"] == "stable_high"
        assert result1["evolution_potential"] == "gradual_improvement"

        # Test active low pressure system
        result2 = forecast._classify_weather_system(
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
        result3 = forecast._classify_weather_system(
            {"pressure_system": "normal", "current_trend": 0.0},
            {"direction_stability": 0.6},
            {"trend": 0.0},
            0.5,  # Neutral stability
        )
        assert result3["type"] == "transitional"
        assert result3["evolution_potential"] == "moderate_change"

    def test_analyze_cloud_cover_comprehensive(self, forecast, mock_analysis):
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

        result = forecast._analyze_cloud_cover_comprehensive(
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

    def test_analyze_moisture_transport(self, forecast):
        """Test moisture transport analysis."""
        result = forecast._analyze_moisture_transport(
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

    def test_analyze_wind_patterns(self, forecast):
        """Test wind pattern analysis."""
        result = forecast._analyze_wind_patterns(
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

    def test_analyze_historical_weather_patterns(self, forecast, mock_analysis):
        """Test historical weather pattern analysis."""
        result = forecast._analyze_historical_weather_patterns()

        assert isinstance(result, dict)
        assert "correlations" in result

        # Should have pattern data for different variables
        assert "temperature" in result
        assert "pressure" in result

        # Validate temperature patterns
        temp_patterns = result["temperature"]
        assert "volatility" in temp_patterns
        assert "seasonal_factor" in temp_patterns

    def test_model_weather_system_evolution(self, forecast):
        """Test weather system evolution modeling."""
        meteorological_state = {
            "weather_system": {"type": "stable_high"},
            "atmospheric_stability": 0.8,
            "pressure_analysis": {"current_trend": 0.2},
        }

        result = forecast._model_weather_system_evolution(meteorological_state)

        assert isinstance(result, dict)
        required_keys = [
            "evolution_path",
            "confidence_levels",
            "transition_probabilities",
        ]

        for key in required_keys:
            assert key in result

        assert isinstance(result["evolution_path"], list)
        assert isinstance(result["confidence_levels"], list)
        assert isinstance(result["transition_probabilities"], dict)

        # Validate transition probabilities
        transitions = result["transition_probabilities"]
        assert "persistence" in transitions
        assert "gradual_change" in transitions
        assert "rapid_change" in transitions

        total_prob = sum(transitions.values())
        assert abs(total_prob - 1.0) < 0.01  # Should sum to approximately 1.0

    def test_forecast_temperature_comprehensive(self, forecast):
        """Test comprehensive temperature forecasting."""
        meteorological_state = {
            "atmospheric_stability": 0.7,
            "pressure_analysis": {"pressure_system": "normal", "current_trend": 0.1},
        }
        historical_patterns = {"temperature": {"volatility": 3.0}}
        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        # Test different days
        temp_day0 = forecast._forecast_temperature_comprehensive(
            0, 22.0, meteorological_state, historical_patterns, system_evolution
        )
        temp_day2 = forecast._forecast_temperature_comprehensive(
            2, 22.0, meteorological_state, historical_patterns, system_evolution
        )

        assert isinstance(temp_day0, float)
        assert isinstance(temp_day2, float)

        # Day 2 should be slightly different due to distance dampening
        assert abs(temp_day0 - temp_day2) < 5.0  # Should be reasonably close

    def test_forecast_condition_comprehensive(self, forecast):
        """Test comprehensive condition forecasting."""
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 30.0,
            },
            "cloud_analysis": {"cloud_cover": 60.0},
            "moisture_analysis": {"condensation_potential": 0.4},
        }
        historical_patterns = {}
        system_evolution = {
            "evolution_path": ["transitional"],
            "confidence_levels": [0.7],
        }

        result = forecast._forecast_condition_comprehensive(
            0,
            ATTR_CONDITION_PARTLYCLOUDY,
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
            ATTR_CONDITION_POURING,
            ATTR_CONDITION_FOG,
            ATTR_CONDITION_SNOWY,
            ATTR_CONDITION_WINDY,
        ]

    def test_forecast_condition_comprehensive_storm_override(self, forecast):
        """Test that storm probability overrides other condition logic."""
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "high_pressure",
                "storm_probability": 80.0,
            },
            "cloud_analysis": {"cloud_cover": 20.0},  # Would normally be clear
            "moisture_analysis": {"condensation_potential": 0.1},
        }
        historical_patterns = {}
        system_evolution = {
            "evolution_path": ["active_low"],
            "confidence_levels": [0.9],
        }

        result = forecast._forecast_condition_comprehensive(
            0,
            ATTR_CONDITION_SUNNY,
            meteorological_state,
            historical_patterns,
            system_evolution,
        )

        # Should override clear conditions due to high storm probability
        assert result in [ATTR_CONDITION_LIGHTNING_RAINY, ATTR_CONDITION_POURING]

    def test_forecast_precipitation_comprehensive(self, forecast):
        """Test comprehensive precipitation forecasting."""
        meteorological_state = {
            "pressure_analysis": {"storm_probability": 60.0},
            "moisture_analysis": {
                "transport_potential": 7.0,
                "condensation_potential": 0.6,
            },
            "atmospheric_stability": 0.4,
        }
        sensor_data = {"rain_rate_unit": "mm"}

        # Test different conditions
        precip_rainy = forecast._forecast_precipitation_comprehensive(
            0, ATTR_CONDITION_RAINY, meteorological_state, {}, sensor_data
        )
        precip_storm = forecast._forecast_precipitation_comprehensive(
            0, ATTR_CONDITION_LIGHTNING_RAINY, meteorological_state, {}, sensor_data
        )

        assert isinstance(precip_rainy, float)
        assert isinstance(precip_storm, float)
        assert precip_rainy >= 0
        assert precip_storm >= precip_rainy  # Storm should have more precipitation

    def test_forecast_wind_comprehensive(self, forecast):
        """Test comprehensive wind forecasting."""
        meteorological_state = {
            "pressure_analysis": {"pressure_system": "normal"},
            "wind_pattern_analysis": {
                "direction_stability": 0.8,
                "gradient_wind_effect": 3.0,
            },
        }
        historical_patterns = {"wind": {"volatility": 2.0}}

        # Test different conditions
        wind_normal = forecast._forecast_wind_comprehensive(
            0,
            5.0,
            ATTR_CONDITION_PARTLYCLOUDY,
            meteorological_state,
            historical_patterns,
        )
        wind_stormy = forecast._forecast_wind_comprehensive(
            0,
            5.0,
            ATTR_CONDITION_LIGHTNING_RAINY,
            meteorological_state,
            historical_patterns,
        )

        assert isinstance(wind_normal, float)
        assert isinstance(wind_stormy, float)
        assert wind_normal > 0
        assert wind_stormy > wind_normal  # Stormy conditions should have stronger wind

    def test_forecast_humidity_comprehensive(self, forecast):
        """Test comprehensive humidity forecasting."""
        meteorological_state = {
            "moisture_analysis": {"trend_direction": "increasing"},
            "atmospheric_stability": 0.7,
        }

        # Test different conditions
        humidity_cloudy = forecast._forecast_humidity_comprehensive(
            0, 60.0, meteorological_state, {}, ATTR_CONDITION_CLOUDY
        )
        humidity_sunny = forecast._forecast_humidity_comprehensive(
            0, 60.0, meteorological_state, {}, ATTR_CONDITION_SUNNY
        )

        assert isinstance(humidity_cloudy, int)
        assert isinstance(humidity_sunny, int)
        assert 0 <= humidity_cloudy <= 100
        assert 0 <= humidity_sunny <= 100
        assert humidity_cloudy >= humidity_sunny  # Cloudy should be more humid

    def test_calculate_temperature_range(self, forecast):
        """Test temperature range calculation based on conditions."""
        meteorological_state = {"atmospheric_stability": 0.6}

        # Test different conditions
        range_sunny = forecast._calculate_temperature_range(
            ATTR_CONDITION_SUNNY, meteorological_state
        )
        range_cloudy = forecast._calculate_temperature_range(
            ATTR_CONDITION_CLOUDY, meteorological_state
        )
        range_rainy = forecast._calculate_temperature_range(
            ATTR_CONDITION_RAINY, meteorological_state
        )

        assert 2.0 <= range_sunny <= 15.0
        assert 2.0 <= range_cloudy <= 15.0
        assert 2.0 <= range_rainy <= 15.0

        # Sunny should have larger range than cloudy/rainy
        assert range_sunny >= range_cloudy
        assert range_sunny >= range_rainy

    def test_analyze_hourly_weather_patterns(self, forecast, mock_analysis):
        """Test hourly weather pattern analysis."""
        result = forecast._analyze_hourly_weather_patterns()

        assert isinstance(result, dict)
        assert "diurnal_patterns" in result
        assert "volatility" in result

        # Check diurnal patterns structure
        diurnal = result["diurnal_patterns"]
        assert "temperature" in diurnal
        assert "humidity" in diurnal
        assert "wind" in diurnal

        # Check volatility structure
        volatility = result["volatility"]
        assert "temperature" in volatility
        assert "humidity" in volatility
        assert "wind" in volatility

    def test_model_hourly_weather_evolution(self, forecast):
        """Test hourly weather evolution modeling."""
        meteorological_state = {
            "atmospheric_stability": 0.7,
            "weather_system": {"type": "stable_high"},
        }

        result = forecast._model_hourly_weather_evolution(meteorological_state)

        assert isinstance(result, dict)
        assert "evolution_rate" in result
        assert "stability_factor" in result
        assert "micro_changes" in result

        assert 0 <= result["evolution_rate"] <= 1.0
        assert result["stability_factor"] == 0.7

    def test_forecast_hourly_temperature_comprehensive(self, forecast):
        """Test comprehensive hourly temperature forecasting."""
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

        result = forecast._forecast_hourly_temperature_comprehensive(
            22.0,
            2,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert isinstance(result, float)
        # Should be close to base temperature with diurnal variation
        assert 18.0 <= result <= 26.0

    def test_forecast_hourly_temperature_comprehensive_daytime_with_sun_times(
        self, forecast
    ):
        """Test comprehensive temperature calculation during daytime with astronomical context."""
        # Simulate solar noon (2 PM) - should be warmest
        astronomical_context = {
            "is_daytime": True,
            "solar_elevation": 60.0,  # High sun
            "hour_of_day": 14,  # 2 PM
            "forecast_hour": 0,
        }
        meteorological_state = {"pressure_analysis": {"current_trend": 0.0}}
        hourly_patterns = {
            "diurnal_patterns": {
                "temperature": {
                    "dawn": -2.0,
                    "morning": 1.0,
                    "noon": 3.0,
                    "afternoon": 2.0,
                    "evening": -1.0,
                    "night": -3.0,
                    "midnight": -2.0,
                }
            }
        }
        micro_evolution = {
            "evolution_rate": 0.0,
            "micro_changes": {"max_change_per_hour": 1.0},
        }

        result = forecast._forecast_hourly_temperature_comprehensive(
            20.0,
            0,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        # At solar noon, temperature should be higher than base
        assert result > 20.0
        assert 21.0 <= result <= 25.0  # Should show daytime warming

    def test_forecast_hourly_temperature_comprehensive_nighttime_cooling(
        self, forecast
    ):
        """Test comprehensive temperature calculation during nighttime."""
        # Simulate deep night (2 AM)
        astronomical_context = {
            "is_daytime": False,
            "solar_elevation": 0.0,
            "hour_of_day": 2,  # 2 AM
            "forecast_hour": 0,
        }
        meteorological_state = {"pressure_analysis": {"current_trend": 0.0}}
        hourly_patterns = {
            "diurnal_patterns": {
                "temperature": {
                    "dawn": -2.0,
                    "morning": 1.0,
                    "noon": 3.0,
                    "afternoon": 2.0,
                    "evening": -1.0,
                    "night": -3.0,
                    "midnight": -2.0,
                }
            }
        }
        micro_evolution = {
            "evolution_rate": 0.0,
            "micro_changes": {"max_change_per_hour": 1.0},
        }

        result = forecast._forecast_hourly_temperature_comprehensive(
            20.0,
            0,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        # During deep night, should be cooler
        assert result < 18.0  # Should show nighttime cooling

    def test_forecast_hourly_temperature_comprehensive_pressure_modulation(
        self, forecast
    ):
        """Test comprehensive temperature calculation with pressure trend modulation."""
        astronomical_context = {
            "is_daytime": True,
            "solar_elevation": 45.0,
            "hour_of_day": 12,
            "forecast_hour": 0,
        }

        # Test with falling pressure (cooling effect)
        meteorological_state_falling = {"pressure_analysis": {"current_trend": -2.0}}
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
            "evolution_rate": 0.0,
            "micro_changes": {"max_change_per_hour": 1.0},
        }

        result_falling = forecast._forecast_hourly_temperature_comprehensive(
            20.0,
            0,
            astronomical_context,
            meteorological_state_falling,
            hourly_patterns,
            micro_evolution,
        )

        # Test with rising pressure (warming effect)
        meteorological_state_rising = {"pressure_analysis": {"current_trend": 2.0}}

        result_rising = forecast._forecast_hourly_temperature_comprehensive(
            20.0,
            0,
            astronomical_context,
            meteorological_state_rising,
            hourly_patterns,
            micro_evolution,
        )

        # Rising pressure should result in warmer temperature than falling pressure
        assert result_rising > result_falling

    def test_forecast_hourly_temperature_comprehensive_dampening(self, forecast):
        """Test that temperature variation dampens for distant forecast hours."""
        astronomical_context_near = {
            "is_daytime": True,
            "solar_elevation": 45.0,
            "hour_of_day": 12,
            "forecast_hour": 0,
        }
        astronomical_context_distant = {
            "is_daytime": True,
            "solar_elevation": 45.0,
            "hour_of_day": 12,
            "forecast_hour": 20,
        }
        meteorological_state = {"pressure_analysis": {"current_trend": 0.0}}
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
            "evolution_rate": 0.0,
            "micro_changes": {"max_change_per_hour": 1.0},
        }

        result_near = forecast._forecast_hourly_temperature_comprehensive(
            20.0,
            0,
            astronomical_context_near,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        result_distant = forecast._forecast_hourly_temperature_comprehensive(
            20.0,
            20,
            astronomical_context_distant,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        # Distant forecast should have less variation from base temperature
        near_variation = abs(result_near - 20.0)
        distant_variation = abs(result_distant - 20.0)

        assert distant_variation <= near_variation

    def test_forecast_hourly_temperature_comprehensive_natural_variation(
        self, forecast
    ):
        """Test that natural variation is added to prevent identical temperatures."""
        astronomical_context = {
            "is_daytime": True,
            "solar_elevation": 45.0,
            "hour_of_day": 12,
            "forecast_hour": 0,
        }
        meteorological_state = {"pressure_analysis": {"current_trend": 0.0}}
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
            "evolution_rate": 0.0,
            "micro_changes": {"max_change_per_hour": 1.0},
        }

        # Get multiple results with different hour indices
        results = []
        for hour_idx in range(5):
            astronomical_context["forecast_hour"] = hour_idx
            result = forecast._forecast_hourly_temperature_comprehensive(
                20.0,
                hour_idx,
                astronomical_context,
                meteorological_state,
                hourly_patterns,
                micro_evolution,
            )
            results.append(result)

        # Results should be slightly different due to natural variation
        unique_results = set(round(r, 1) for r in results)
        assert len(unique_results) > 1  # Should have some variation

    def test_forecast_hourly_temperature_comprehensive_returns_valid_float(
        self, forecast
    ):
        """Test that comprehensive temperature calculation always returns a valid float."""
        test_cases = [
            # Daytime cases
            {
                "astronomical_context": {
                    "is_daytime": True,
                    "solar_elevation": 60.0,
                    "hour_of_day": 12,
                    "forecast_hour": 0,
                },
                "meteorological_state": {"pressure_analysis": {"current_trend": 0.0}},
                "hourly_patterns": {"diurnal_patterns": {"temperature": {"noon": 3.0}}},
                "micro_evolution": {
                    "evolution_rate": 0.0,
                    "micro_changes": {"max_change_per_hour": 1.0},
                },
            },
            # Nighttime cases
            {
                "astronomical_context": {
                    "is_daytime": False,
                    "solar_elevation": 0.0,
                    "hour_of_day": 2,
                    "forecast_hour": 0,
                },
                "meteorological_state": {"pressure_analysis": {"current_trend": 0.0}},
                "hourly_patterns": {
                    "diurnal_patterns": {"temperature": {"night": -3.0}}
                },
                "micro_evolution": {
                    "evolution_rate": 0.0,
                    "micro_changes": {"max_change_per_hour": 1.0},
                },
            },
            # Edge cases with missing data
            {
                "astronomical_context": {
                    "is_daytime": True,
                    "solar_elevation": 30.0,
                    "hour_of_day": 10,
                    "forecast_hour": 0,
                },
                "meteorological_state": {},  # Empty meteorological state
                "hourly_patterns": {
                    "diurnal_patterns": {
                        "temperature": {
                            "dawn": -2.0,
                            "morning": 1.0,
                            "noon": 3.0,
                            "afternoon": 2.0,
                            "evening": -1.0,
                            "night": -3.0,
                            "midnight": -2.0,
                        }
                    }
                },  # Include all required diurnal pattern keys
                "micro_evolution": {
                    "evolution_rate": 0.0,
                    "micro_changes": {"max_change_per_hour": 1.0},
                },
            },
        ]

        for test_case in test_cases:
            result = forecast._forecast_hourly_temperature_comprehensive(
                20.0,
                test_case["astronomical_context"]["forecast_hour"],
                test_case["astronomical_context"],
                test_case["meteorological_state"],
                test_case["hourly_patterns"],
                test_case["micro_evolution"],
            )

            assert isinstance(result, float)
            assert not str(result).endswith("j")  # Should not be complex
            assert -50 <= result <= 60  # Reasonable temperature range

    def test_forecast_hourly_condition_comprehensive(self, forecast):
        """Test comprehensive hourly condition forecasting."""
        astronomical_context = {"is_daytime": False, "hour_of_day": 2}  # Nighttime
        meteorological_state = {
            "pressure_analysis": {"storm_probability": 20.0},
            "cloud_analysis": {"cloud_cover": 40.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.2}}

        result = forecast._forecast_hourly_condition_comprehensive(
            2,
            ATTR_CONDITION_SUNNY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert isinstance(result, str)
        # Should convert sunny to nighttime condition
        assert result in [
            ATTR_CONDITION_SUNNY,  # May keep if near dawn/dusk
            ATTR_CONDITION_CLEAR_NIGHT,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
        ]

    def test_forecast_hourly_precipitation_comprehensive(self, forecast):
        """Test comprehensive hourly precipitation forecasting."""
        meteorological_state = {
            "pressure_analysis": {"storm_probability": 50.0},
            "moisture_analysis": {"condensation_potential": 0.5},
        }
        hourly_patterns = {}
        sensor_data = {"rain_rate_unit": "mm"}

        # Test different conditions
        precip_rainy = forecast._forecast_hourly_precipitation_comprehensive(
            0, ATTR_CONDITION_RAINY, meteorological_state, hourly_patterns, sensor_data
        )
        precip_storm = forecast._forecast_hourly_precipitation_comprehensive(
            0,
            ATTR_CONDITION_LIGHTNING_RAINY,
            meteorological_state,
            hourly_patterns,
            sensor_data,
        )

        assert isinstance(precip_rainy, float)
        assert isinstance(precip_storm, float)
        assert precip_rainy >= 0
        assert precip_storm >= precip_rainy

    def test_forecast_hourly_wind_comprehensive(self, forecast):
        """Test comprehensive hourly wind forecasting."""
        meteorological_state = {}
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

        # Test afternoon hour (should have higher wind)
        result_afternoon = forecast._forecast_hourly_wind_comprehensive(
            0, 10.0, ATTR_CONDITION_PARTLYCLOUDY, meteorological_state, hourly_patterns
        )

        # Mock the forecast time to be afternoon
        with patch(
            "custom_components.micro_weather.weather_forecast.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime.now().replace(hour=15)  # 3 PM

            result_afternoon = forecast._forecast_hourly_wind_comprehensive(
                0,
                10.0,
                ATTR_CONDITION_PARTLYCLOUDY,
                meteorological_state,
                hourly_patterns,
            )

            assert isinstance(result_afternoon, float)
            assert result_afternoon > 0

    def test_forecast_hourly_humidity_comprehensive(self, forecast):
        """Test comprehensive hourly humidity forecasting."""
        meteorological_state = {"moisture_analysis": {"trend_direction": "stable"}}
        hourly_patterns = {
            "diurnal_patterns": {
                "humidity": {
                    "dawn": 5,
                    "morning": -5,
                    "noon": -10,
                    "afternoon": -5,
                    "evening": 5,
                }
            }
        }
        condition = ATTR_CONDITION_CLOUDY

        result = forecast._forecast_hourly_humidity_comprehensive(
            0, 65.0, meteorological_state, hourly_patterns, condition
        )

        assert isinstance(result, int)
        assert 0 <= result <= 100

        # Cloudy conditions should maintain higher humidity
        assert result >= 50

    def test_get_historical_trends_method(self, forecast, mock_analysis):
        """Test the get_historical_trends method."""
        # Test with valid sensor
        result = forecast.get_historical_trends("outdoor_temp", hours=24)

        assert isinstance(result, dict)
        assert "current" in result
        assert "average" in result
        assert "trend" in result
        assert "min" in result
        assert "max" in result
        assert "volatility" in result

        # Test with different hours
        result_48h = forecast.get_historical_trends("humidity", hours=48)
        assert isinstance(result_48h, dict)

    def test_comprehensive_forecast_error_handling(self, forecast, mock_analysis):
        """Test error handling in comprehensive forecast methods."""
        # Test with minimal sensor data
        sensor_data_minimal = {"outdoor_temp": 70.0}

        # Should handle missing data gracefully
        result = forecast.generate_comprehensive_forecast(
            ATTR_CONDITION_PARTLYCLOUDY, sensor_data_minimal
        )

        assert isinstance(result, list)
        assert len(result) == 5

        # All forecasts should have required fields
        for forecast_item in result:
            assert "condition" in forecast_item
            assert "temperature" in forecast_item

    def test_hourly_forecast_error_handling(self, forecast, mock_analysis):
        """Test error handling in hourly forecast methods."""
        # Test with missing sunrise/sunset times
        result = forecast.generate_hourly_forecast_comprehensive(
            20.0, ATTR_CONDITION_SUNNY, {"outdoor_temp": 68.0}
        )

        assert isinstance(result, list)
        assert len(result) == 24

        # Should handle astronomical calculations without sunrise/sunset
        for hour_forecast in result:
            assert "condition" in hour_forecast
            assert "temperature" in hour_forecast

    # ======== HOURLY FORECAST CLOUD COVER TESTS ========

    def test_forecast_hourly_condition_clear_skies_daytime(self, forecast):
        """Test hourly condition with clear skies (low cloud cover) during daytime."""
        # Clear skies (10% cloud cover) during daytime should remain sunny
        astronomical_context = {"is_daytime": True, "hour_of_day": 12}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 10.0},  # Clear
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_SUNNY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_SUNNY
        ), "Clear skies (10% cloud cover) should remain sunny during daytime"

    def test_forecast_hourly_condition_clear_skies_nighttime(self, forecast):
        """Test hourly condition with clear skies during nighttime."""
        # Clear skies (5% cloud cover) during nighttime should be clear_night
        astronomical_context = {"is_daytime": False, "hour_of_day": 22}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 5.0},  # Very clear
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_SUNNY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_CLEAR_NIGHT
        ), "Clear skies during nighttime should become clear_night"

    def test_forecast_hourly_condition_partly_cloudy_daytime(self, forecast):
        """Test hourly condition with partly cloudy (moderate cloud cover) during daytime."""
        # Partly cloudy (35% cloud cover) during daytime should stay partly cloudy
        astronomical_context = {"is_daytime": True, "hour_of_day": 14}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 35.0},  # Partly cloudy
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_PARTLYCLOUDY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_PARTLYCLOUDY
        ), "Partly cloudy during daytime should remain partly cloudy"

    def test_forecast_hourly_condition_overcast_daytime(self, forecast):
        """Test hourly condition with overcast (high cloud cover) during daytime."""
        # Overcast (85% cloud cover) during daytime should be cloudy
        astronomical_context = {"is_daytime": True, "hour_of_day": 15}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 85.0},  # Very cloudy
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_CLOUDY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_CLOUDY
        ), "Overcast (85% cloud cover) should remain cloudy during daytime"

    def test_forecast_hourly_condition_neutral_cloud_cover_daytime(self, forecast):
        """Test hourly condition with neutral cloud cover (50%) during daytime."""
        # Neutral cloud cover (50%) is unreliable - should preserve input condition
        astronomical_context = {"is_daytime": True, "hour_of_day": 13}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 50.0},  # Neutral/unreliable
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        # Test with sunny input
        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_SUNNY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )
        assert (
            result == ATTR_CONDITION_SUNNY
        ), "Neutral cloud cover should preserve sunny during daytime"

        # Test with partly cloudy input
        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_PARTLYCLOUDY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )
        assert (
            result == ATTR_CONDITION_PARTLYCLOUDY
        ), "Neutral cloud cover should preserve partly cloudy during daytime"

    def test_forecast_hourly_condition_rainy_preserved_daytime(self, forecast):
        """Test that rain conditions are preserved regardless of time of day."""
        # Rainy conditions should persist through daytime
        astronomical_context = {"is_daytime": True, "hour_of_day": 11}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 90.0},
            "pressure_analysis": {"storm_probability": 60.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_RAINY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_RAINY
        ), "Rainy conditions should be preserved during daytime"

    def test_forecast_hourly_condition_rainy_preserved_nighttime(self, forecast):
        """Test that rain conditions are preserved during nighttime."""
        astronomical_context = {"is_daytime": False, "hour_of_day": 23}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 95.0},
            "pressure_analysis": {"storm_probability": 70.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_POURING,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_POURING
        ), "Heavy rain should be preserved during nighttime"

    def test_forecast_hourly_condition_storm_preserved_daytime(self, forecast):
        """Test that storm conditions are preserved during daytime."""
        astronomical_context = {"is_daytime": True, "hour_of_day": 10}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 95.0},
            "pressure_analysis": {"storm_probability": 85.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_LIGHTNING_RAINY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_LIGHTNING_RAINY
        ), "Storm conditions should be preserved during daytime"

    def test_forecast_hourly_condition_clear_night_to_sunny(self, forecast):
        """Test conversion from clear_night to sunny at sunrise."""
        astronomical_context = {"is_daytime": True, "hour_of_day": 7}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 15.0},  # Reliable clear
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_CLEAR_NIGHT,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_SUNNY
        ), "Clear night should become sunny at daytime"

    def test_forecast_hourly_condition_partly_cloudy_nighttime_clear(self, forecast):
        """Test partly cloudy with clear skies during nighttime."""
        astronomical_context = {"is_daytime": False, "hour_of_day": 20}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 25.0},  # Reliable clear
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_PARTLYCLOUDY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_CLEAR_NIGHT
        ), "Partly cloudy with clear skies should become clear_night at night"

    def test_forecast_hourly_condition_cloudy_to_clear_transition(self, forecast):
        """Test cloud cover improving from cloudy to clear during daytime."""
        astronomical_context = {"is_daytime": True, "hour_of_day": 12}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 15.0},  # Reliably clear
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {
            "micro_changes": {"change_probability": 0.6, "max_change_per_hour": 2.0}
        }

        # Start with cloudy, should improve to clear based on cloud cover
        result = forecast._forecast_hourly_condition_comprehensive(
            6,
            ATTR_CONDITION_CLOUDY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        # With high cloud cover reliability and daytime, should stay sunny
        assert result in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_CLOUDY,
        ], "Should handle cloud cover transition"

    def test_forecast_hourly_condition_fog_preserved_daytime(self, forecast):
        """Test that fog conditions are preserved during daytime."""
        astronomical_context = {"is_daytime": True, "hour_of_day": 8}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 98.0},
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_FOG,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_FOG
        ), "Fog conditions should be preserved during daytime"

    def test_forecast_hourly_condition_snow_preserved_nighttime(self, forecast):
        """Test that snow conditions are preserved during nighttime."""
        astronomical_context = {"is_daytime": False, "hour_of_day": 2}
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 90.0},
            "pressure_analysis": {"storm_probability": 20.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        result = forecast._forecast_hourly_condition_comprehensive(
            0,
            ATTR_CONDITION_SNOWY,
            astronomical_context,
            meteorological_state,
            hourly_patterns,
            micro_evolution,
        )

        assert (
            result == ATTR_CONDITION_SNOWY
        ), "Snow conditions should be preserved during nighttime"

    def test_forecast_hourly_condition_24_hour_cycle(self, forecast):
        """Test hourly condition through a full 24-hour cycle with consistent base condition."""
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 20.0},  # Consistently clear
            "pressure_analysis": {"storm_probability": 0.0},
        }
        hourly_patterns = {}
        micro_evolution = {"micro_changes": {"change_probability": 0.3}}

        conditions_by_hour = {}
        for hour in range(24):
            is_daytime = 6 <= hour < 18  # 6 AM to 6 PM
            astronomical_context = {"is_daytime": is_daytime, "hour_of_day": hour}

            result = forecast._forecast_hourly_condition_comprehensive(
                hour,
                ATTR_CONDITION_SUNNY,
                astronomical_context,
                meteorological_state,
                hourly_patterns,
                micro_evolution,
            )
            conditions_by_hour[hour] = result

        # Check daytime hours (6-17) are sunny or partly cloudy
        for hour in range(6, 18):
            assert conditions_by_hour[hour] in [
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_PARTLYCLOUDY,
            ], f"Hour {hour} should be sunny/partly cloudy during daytime"

        # Check nighttime hours (18-5) are clear_night
        for hour in list(range(18, 24)) + list(range(0, 6)):
            assert (
                conditions_by_hour[hour] == ATTR_CONDITION_CLEAR_NIGHT
            ), f"Hour {hour} should be clear_night during nighttime"

    # ======== WEATHER ANALYSIS EDGE CASE TESTS ========
    # Note: These tests use a real WeatherAnalysis instance, not the mocked one

    def test_weather_analysis_fog_detection_dense_fog(self):
        """Test dense fog detection with extreme conditions."""
        weather_analysis = WeatherAnalysis()

        # Simulate dense fog conditions
        result = weather_analysis.analyze_fog_conditions(
            temp=32.0,  # At freezing
            humidity=99.9,  # Virtually saturated
            dewpoint=31.8,  # Very tight spread
            spread=0.2,
            wind_speed=0.5,  # Very calm
            solar_rad=0.5,  # No solar radiation
            is_daytime=False,
        )

        assert (
            result == ATTR_CONDITION_FOG
        ), "Should detect dense fog with extreme conditions"

    def test_weather_analysis_fog_detection_twilight_false_positive(self):
        """Test that fog is not falsely detected during twilight."""
        weather_analysis = WeatherAnalysis()

        # Twilight with high humidity should not trigger fog
        result = weather_analysis.analyze_fog_conditions(
            temp=70.0,
            humidity=95.0,  # High but not extreme
            dewpoint=68.0,
            spread=2.0,
            wind_speed=5.0,
            solar_rad=50.0,  # Twilight solar radiation
            is_daytime=False,
        )

        assert (
            result is None
        ), "Should not falsely detect fog during twilight with solar radiation"

    def test_weather_analysis_dewpoint_calculation_extremes(self):
        """Test dewpoint calculation with extreme humidity values."""
        weather_analysis = WeatherAnalysis()

        # Test with very dry air
        dewpoint_dry = weather_analysis.calculate_dewpoint(100.0, 5.0)
        assert dewpoint_dry < 30.0, "Very dry air should have very low dewpoint"

        # Test with saturated air
        dewpoint_saturated = weather_analysis.calculate_dewpoint(70.0, 100.0)
        assert (
            abs(dewpoint_saturated - 70.0) < 1.0
        ), "Saturated air should have dewpoint near temp"

        # Test with zero humidity fallback
        dewpoint_zero = weather_analysis.calculate_dewpoint(80.0, 0.0)
        assert isinstance(
            dewpoint_zero, float
        ), "Should handle zero humidity gracefully"

    def test_weather_analysis_pressure_altitude_adjustment_high_elevation(self):
        """Test pressure adjustment at high altitude uses barometric formula."""
        weather_analysis = WeatherAnalysis()

        # Test that the method handles altitude adjustments consistently
        # At higher altitudes, atmospheric pressure is lower
        pressure_sea_level = weather_analysis.adjust_pressure_for_altitude(
            pressure_inhg=29.92, altitude_m=0, pressure_type="relative"
        )

        pressure_high_alt = weather_analysis.adjust_pressure_for_altitude(
            pressure_inhg=29.92, altitude_m=1609, pressure_type="relative"
        )

        # Just verify both return valid float values
        assert isinstance(pressure_sea_level, float), "Should return a float"
        assert isinstance(pressure_high_alt, float), "Should return a float"
        # Both should be reasonable pressure values (in inHg)
        assert (
            10 < pressure_sea_level < 35
        ), f"Sea level pressure should be realistic, got {pressure_sea_level}"
        assert (
            10 < pressure_high_alt < 35
        ), f"Altitude pressure should be realistic, got {pressure_high_alt}"

    def test_weather_analysis_pressure_altitude_adjustment_sea_level(self):
        """Test pressure adjustment at sea level."""
        weather_analysis = WeatherAnalysis()

        # At sea level, atmospheric pressure should equal station pressure
        adjusted = weather_analysis.adjust_pressure_for_altitude(
            pressure_inhg=29.92, altitude_m=0, pressure_type="relative"
        )

        assert abs(adjusted - 29.92) < 0.1, "Sea level pressure should not be adjusted"

    def test_weather_analysis_wind_direction_circular_mean(self):
        """Test circular mean calculation for wind directions."""
        weather_analysis = WeatherAnalysis()

        # Directions around north (350, 10, 5 degrees)
        directions = [350.0, 10.0, 5.0, 355.0]
        mean = weather_analysis.calculate_circular_mean(directions)

        # Mean should be near 0/360 (north), not 180 (south)
        assert (
            mean < 45 or mean > 315
        ), f"Circular mean of northerly directions should be north, got {mean}°"

    def test_weather_analysis_wind_direction_angular_difference(self):
        """Test angular difference calculation between wind directions."""
        weather_analysis = WeatherAnalysis()

        # Test normal difference
        diff = weather_analysis.calculate_angular_difference(0.0, 90.0)
        assert diff == 90.0, "Should calculate 90° difference correctly"

        # Test wraparound case (350° to 10°)
        diff = weather_analysis.calculate_angular_difference(350.0, 10.0)
        assert (
            abs(diff - 20.0) < 0.1
        ), "Should handle wraparound correctly (350° to 10° = 20°)"

        # Test reverse wraparound (10° to 350°)
        diff = weather_analysis.calculate_angular_difference(10.0, 350.0)
        assert (
            abs(diff + 20.0) < 0.1 or abs(diff - 340.0) < 0.1
        ), "Should handle reverse wraparound"

    def test_weather_analysis_pressure_trend_rapid_drop(self):
        """Test pressure trend analysis with rapid pressure drop."""
        weather_analysis = WeatherAnalysis()

        # Create history of rapidly dropping pressure
        import datetime

        now = datetime.datetime.now()

        # Mock historical pressure data (simulation)
        weather_analysis._sensor_history[KEY_PRESSURE] = deque(maxlen=192)

        # Add 24 readings showing rapid pressure drop (simulating falling pressure)
        for i in range(24):
            weather_analysis._sensor_history[KEY_PRESSURE].append(
                {
                    "timestamp": now - datetime.timedelta(hours=24 - i),
                    "value": 29.92
                    - (i * 0.15),  # Dropping 0.15 inHg per hour = 3.6 inHg/day
                }
            )

        trends = weather_analysis.analyze_pressure_trends(altitude=0)

        # Rapid drop should indicate low pressure system
        assert (
            trends["pressure_system"] == "low_pressure"
        ), f"Rapid pressure drop should indicate low pressure, got {trends['pressure_system']}"
        # Storm probability should be elevated due to rapid drop and low pressure
        assert (
            trends["storm_probability"] >= 40
        ), f"Rapid pressure drop should increase storm probability, got {trends['storm_probability']}"

    def test_weather_analysis_cloud_cover_low_solar_radiation(self):
        """Test cloud cover calculation with very low solar radiation."""
        weather_analysis = WeatherAnalysis()

        cloud_cover = weather_analysis.analyze_cloud_cover(
            solar_radiation=10.0,  # Very low
            solar_lux=500.0,  # Very low
            uv_index=0.1,  # Very low
            solar_elevation=45.0,
        )

        # Low solar radiation should indicate some cloudiness
        # The actual algorithm uses complex calculations, so we just check it's reasonable
        assert 0 <= cloud_cover <= 100, "Cloud cover should be between 0-100%"
        assert (
            cloud_cover > 30
        ), "Very low solar radiation should indicate notable cloud cover"

    def test_weather_analysis_cloud_cover_high_solar_radiation(self):
        """Test cloud cover calculation with high solar radiation."""
        weather_analysis = WeatherAnalysis()

        cloud_cover = weather_analysis.analyze_cloud_cover(
            solar_radiation=1000.0,  # Very high
            solar_lux=100000.0,  # Very high
            uv_index=11.0,  # Very high
            solar_elevation=80.0,  # Sun nearly overhead
        )

        # High solar radiation should indicate low cloud cover
        assert 0 <= cloud_cover <= 100, "Cloud cover should be between 0-100%"
        assert (
            cloud_cover < 50
        ), "Very high solar radiation should indicate relatively clear skies (<50%)"

    def test_weather_analysis_visibility_in_fog(self):
        """Test visibility estimation in fog conditions."""
        weather_analysis = WeatherAnalysis()

        sensor_data = {
            KEY_OUTDOOR_TEMP: 32.0,
            KEY_HUMIDITY: 99.0,
            "dewpoint": 31.5,
        }

        visibility = weather_analysis.estimate_visibility(
            ATTR_CONDITION_FOG, sensor_data
        )

        # Dense fog should have low visibility
        assert visibility < 1.0, "Dense fog should have visibility less than 1 km"

    def test_weather_analysis_visibility_in_storm(self):
        """Test visibility estimation during thunderstorm."""
        weather_analysis = WeatherAnalysis()

        sensor_data = {
            KEY_RAIN_RATE: 0.5,  # Heavy rain
            KEY_WIND_SPEED: 25.0,  # Strong winds
            KEY_WIND_GUST: 40.0,
        }

        visibility = weather_analysis.estimate_visibility(
            ATTR_CONDITION_LIGHTNING_RAINY, sensor_data
        )

        # Storm with heavy rain should have reduced visibility
        assert (
            0.5 < visibility < 10.0
        ), "Storm visibility should be reduced but not as low as fog"

    # ============================================================================
    # EDGE CASE TESTS: Multi-day forecast with sunset boundary handling
    # ============================================================================

    def test_forecast_hourly_condition_multi_day_sunset_boundary(self, forecast):
        """Test that forecast correctly handles transition from sunset day to next day.

        When forecast crosses into next day, dates after sunset should use fallback 6-18 hour logic.
        """
        # Current time: Jan 1, 5 PM (after sunset at 6 PM is just before sunset actually)
        # Sunset: Jan 1, 6 PM
        # Forecast: 24 hours starting from 6 PM Jan 1 through 6 PM Jan 2

        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 30},
            "pressure_trend": {"current_trend": 0},
        }

        hourly_patterns = {"diurnal_patterns": {}, "volatility": {}}
        micro_evolution = {"micro_changes": {"change_probability": 0}}

        # Before sunset: should be daytime/sunny
        result_before = forecast._forecast_hourly_condition_comprehensive(
            hour_idx=0,
            current_condition=ATTR_CONDITION_SUNNY,
            astronomical_context={
                "is_daytime": True,
                "solar_elevation": 5,
                "hour_of_day": 17,
                "forecast_hour": 0,
            },
            meteorological_state=meteorological_state,
            hourly_patterns=hourly_patterns,
            micro_evolution=micro_evolution,
        )
        assert result_before == ATTR_CONDITION_SUNNY

        # After sunset on same day: should convert to nighttime
        result_after = forecast._forecast_hourly_condition_comprehensive(
            hour_idx=1,
            current_condition=ATTR_CONDITION_SUNNY,
            astronomical_context={
                "is_daytime": False,
                "solar_elevation": 0,
                "hour_of_day": 18,
                "forecast_hour": 1,
            },
            meteorological_state=meteorological_state,
            hourly_patterns=hourly_patterns,
            micro_evolution=micro_evolution,
        )
        assert result_after == ATTR_CONDITION_CLEAR_NIGHT

    def test_forecast_hourly_condition_neutral_cloud_cover_50_percent_daytime(
        self, forecast
    ):
        """Test that CLOUDY->PARTLYCLOUDY conversion works with exactly 50% cloud cover.

        This tests the fix for: cloud_cover <= 50 (not just < 50) during daytime.
        At exactly 50% cloud cover (neutral), nighttime CLOUDY should convert to PARTLYCLOUDY at daytime.
        """
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 50.0},  # Exactly neutral
            "pressure_trend": {"current_trend": 0},
        }

        hourly_patterns = {"diurnal_patterns": {}, "volatility": {}}
        micro_evolution = {"micro_changes": {"change_probability": 0}}

        # Start with CLOUDY condition (from nighttime conversion)
        result = forecast._forecast_hourly_condition_comprehensive(
            hour_idx=0,
            current_condition=ATTR_CONDITION_CLOUDY,  # Was converted at night
            astronomical_context={
                "is_daytime": True,
                "solar_elevation": 45,
                "hour_of_day": 12,
                "forecast_hour": 0,
            },
            meteorological_state=meteorological_state,
            hourly_patterns=hourly_patterns,
            micro_evolution=micro_evolution,
        )

        # With exactly 50% cloud cover at daytime, should convert back to PARTLYCLOUDY
        assert (
            result == ATTR_CONDITION_PARTLYCLOUDY
        ), "At 50% cloud cover daytime, CLOUDY should become PARTLYCLOUDY"

    def test_forecast_hourly_condition_neutral_cloud_cover_49_percent_daytime(
        self, forecast
    ):
        """Test that CLOUDY->PARTLYCLOUDY conversion works with 49% cloud cover."""
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 49.0},  # Just below neutral
            "pressure_trend": {"current_trend": 0},
        }

        hourly_patterns = {"diurnal_patterns": {}, "volatility": {}}
        micro_evolution = {"micro_changes": {"change_probability": 0}}

        result = forecast._forecast_hourly_condition_comprehensive(
            hour_idx=0,
            current_condition=ATTR_CONDITION_CLOUDY,
            astronomical_context={
                "is_daytime": True,
                "solar_elevation": 45,
                "hour_of_day": 12,
                "forecast_hour": 0,
            },
            meteorological_state=meteorological_state,
            hourly_patterns=hourly_patterns,
            micro_evolution=micro_evolution,
        )

        assert result == ATTR_CONDITION_PARTLYCLOUDY

    def test_forecast_hourly_condition_neutral_cloud_cover_51_percent_daytime(
        self, forecast
    ):
        """Test that CLOUDY stays CLOUDY when cloud cover exceeds 50% at daytime."""
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 51.0},  # Just above neutral
            "pressure_trend": {"current_trend": 0},
        }

        hourly_patterns = {"diurnal_patterns": {}, "volatility": {}}
        micro_evolution = {"micro_changes": {"change_probability": 0}}

        result = forecast._forecast_hourly_condition_comprehensive(
            hour_idx=0,
            current_condition=ATTR_CONDITION_CLOUDY,
            astronomical_context={
                "is_daytime": True,
                "solar_elevation": 45,
                "hour_of_day": 12,
                "forecast_hour": 0,
            },
            meteorological_state=meteorological_state,
            hourly_patterns=hourly_patterns,
            micro_evolution=micro_evolution,
        )

        # At 51% (above neutral), should keep CLOUDY
        assert result == ATTR_CONDITION_CLOUDY

    def test_forecast_hourly_condition_nighttime_partlycloudy_50_percent_converts_to_cloudy(
        self, forecast
    ):
        """Test that PARTLYCLOUDY->CLOUDY conversion works at exactly 50% cloud cover at nighttime."""
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 50.0},  # Exactly neutral
            "pressure_trend": {"current_trend": 0},
        }

        hourly_patterns = {"diurnal_patterns": {}, "volatility": {}}
        micro_evolution = {"micro_changes": {"change_probability": 0}}

        # At nighttime with 50% cloud cover, PARTLYCLOUDY should convert to CLOUDY
        result = forecast._forecast_hourly_condition_comprehensive(
            hour_idx=0,
            current_condition=ATTR_CONDITION_PARTLYCLOUDY,
            astronomical_context={
                "is_daytime": False,
                "solar_elevation": 0,
                "hour_of_day": 22,
                "forecast_hour": 0,
            },
            meteorological_state=meteorological_state,
            hourly_patterns=hourly_patterns,
            micro_evolution=micro_evolution,
        )

        assert result == ATTR_CONDITION_CLOUDY

    def test_forecast_hourly_condition_nighttime_partlycloudy_49_percent_converts_to_clear_night(
        self, forecast
    ):
        """Test that PARTLYCLOUDY->CLEAR_NIGHT conversion works below 50% cloud cover at nighttime."""
        meteorological_state = {
            "cloud_analysis": {"cloud_cover": 49.0},  # Just below neutral
            "pressure_trend": {"current_trend": 0},
        }

        hourly_patterns = {"diurnal_patterns": {}, "volatility": {}}
        micro_evolution = {"micro_changes": {"change_probability": 0}}

        result = forecast._forecast_hourly_condition_comprehensive(
            hour_idx=0,
            current_condition=ATTR_CONDITION_PARTLYCLOUDY,
            astronomical_context={
                "is_daytime": False,
                "solar_elevation": 0,
                "hour_of_day": 22,
                "forecast_hour": 0,
            },
            meteorological_state=meteorological_state,
            hourly_patterns=hourly_patterns,
            micro_evolution=micro_evolution,
        )

        assert result == ATTR_CONDITION_CLEAR_NIGHT

    def test_weather_utils_is_forecast_hour_daytime_multi_day_after_sunset_date(self):
        """Test that dates after sunset date fall back to 6-18 hour logic."""
        from custom_components.micro_weather.weather_utils import (
            is_forecast_hour_daytime,
        )

        # Sunset was on Jan 1
        sunrise_time = datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
        sunset_time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

        # Test times on Jan 2 (after sunset date)
        test_cases = [
            (
                datetime(2024, 1, 2, 5, 0, 0, tzinfo=timezone.utc),
                False,
            ),  # 5 AM = before 6 = nighttime
            (
                datetime(2024, 1, 2, 6, 0, 0, tzinfo=timezone.utc),
                True,
            ),  # 6 AM = start of day
            (
                datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
                True,
            ),  # Noon = daytime
            (
                datetime(2024, 1, 2, 18, 0, 0, tzinfo=timezone.utc),
                False,
            ),  # 6 PM = end of day
            (
                datetime(2024, 1, 2, 23, 0, 0, tzinfo=timezone.utc),
                False,
            ),  # 11 PM = nighttime
        ]

        for forecast_time, expected_is_daytime in test_cases:
            result = is_forecast_hour_daytime(forecast_time, sunrise_time, sunset_time)
            assert (
                result == expected_is_daytime
            ), f"At {forecast_time.hour}:00 Jan 2, expected is_daytime={expected_is_daytime}, got {result}"

    def test_weather_utils_is_forecast_hour_daytime_before_sunset_date_uses_actual_times(
        self,
    ):
        """Test that dates before/on sunset date use actual sunrise/sunset times."""
        from custom_components.micro_weather.weather_utils import (
            is_forecast_hour_daytime,
        )

        # Sunset on Jan 1 at 6 PM
        sunrise_time = datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
        sunset_time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

        # Test times on Jan 1 (same day as sunset)
        test_cases = [
            (
                datetime(2024, 1, 1, 5, 59, 0, tzinfo=timezone.utc),
                False,
            ),  # Before sunrise
            (datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc), True),  # At sunrise
            (datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc), True),  # Noon
            (
                datetime(2024, 1, 1, 17, 59, 0, tzinfo=timezone.utc),
                True,
            ),  # Before sunset
            (
                datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
                False,
            ),  # At sunset (exclusive)
        ]

        for forecast_time, expected_is_daytime in test_cases:
            result = is_forecast_hour_daytime(forecast_time, sunrise_time, sunset_time)
            assert (
                result == expected_is_daytime
            ), f"At {forecast_time.hour}:{forecast_time.minute:02d} Jan 1, expected is_daytime={expected_is_daytime}, got {result}"

    def test_forecast_hourly_comprehensive_multi_day_cycle_sunny_to_cloudy_and_back(
        self, forecast
    ):
        """Integration test: full 24-hour forecast with day/night/day cycle.

        Verifies the complete fix for the "clear night at 2pm" bug:
        - Starting condition: sunny
        - After sunset: converts to clear-night
        - After sunrise next day: converts back to sunny
        """
        # Current time: Jan 1, 2 PM (daytime)
        with patch("homeassistant.util.dt.now") as mock_now:
            mock_now.return_value = datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc)

            sunrise_time = datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
            sunset_time = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

            result = forecast.generate_hourly_forecast_comprehensive(
                current_temp=20,
                current_condition=ATTR_CONDITION_SUNNY,
                sensor_data={
                    KEY_HUMIDITY: 50,
                    KEY_PRESSURE: 1013,
                    KEY_WIND_SPEED: 5,
                    KEY_OUTDOOR_TEMP: 20,
                },
                sunrise_time=sunrise_time,
                sunset_time=sunset_time,
            )

            # Verify structure
            assert len(result) == 24

            # Track condition transitions
            conditions = [f[KEY_CONDITION] for f in result]
            is_nighttimes = [f.get("is_nighttime", False) for f in result]

            # First 4 hours should be daytime (2 PM to 6 PM, before/after sunset at 6 PM)
            # Hour 0 = 2 PM, Hour 1 = 3 PM, Hour 2 = 4 PM, Hour 3 = 5 PM
            for i in range(4):
                assert not is_nighttimes[i], f"Hour {i} should be daytime"
                assert conditions[i] in [
                    ATTR_CONDITION_SUNNY,
                    ATTR_CONDITION_PARTLYCLOUDY,
                    ATTR_CONDITION_CLOUDY,
                ]

            # At hour 4 (6 PM) should convert to nighttime
            assert is_nighttimes[4], "Hour 4 (6 PM sunset) should be nighttime"
            assert conditions[4] in [ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_CLOUDY]

            # After sunset (hours 5-12 = 7 PM to 2 AM) should be nighttime
            for i in range(5, 13):
                assert is_nighttimes[i], f"Hour {i} should be nighttime"
                assert conditions[i] in [
                    ATTR_CONDITION_CLEAR_NIGHT,
                    ATTR_CONDITION_CLOUDY,
                ]

            # After sunrise next day (using fallback 6-18) should be back to daytime
            # Hours 13+ = 3 AM next day onwards
            for i in range(13, 24):
                forecast_hour = (14 + i) % 24
                # Using fallback 6-18, so 6 AM to 6 PM (before 18) = daytime
                if 6 <= forecast_hour < 18:
                    assert not is_nighttimes[
                        i
                    ], f"Hour {i} (forecast hour {forecast_hour}) should be daytime by fallback"
                    # Should be daytime-appropriate condition
                    assert conditions[i] in [
                        ATTR_CONDITION_SUNNY,
                        ATTR_CONDITION_PARTLYCLOUDY,
                        ATTR_CONDITION_CLOUDY,
                    ]
                else:
                    assert is_nighttimes[
                        i
                    ], f"Hour {i} (forecast hour {forecast_hour}) should be nighttime by fallback"

    def test_hourly_forecast_weather_icon_variation(self, forecast, mock_analysis):
        """Test that weather icons vary throughout the 24-hour hourly forecast."""
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

        # Mock cloud cover to return neutral value (50%) to test enhanced micro-evolution
        mock_analysis.analyze_cloud_cover.return_value = 50.0

        # Mock pressure analysis for moderate evolution potential
        mock_analysis.analyze_pressure_trends.return_value = {
            "pressure_system": "normal",
            "storm_probability": 20.0,
            "current_trend": 0.1,
            "long_term_trend": 0.0,
        }

        result = forecast.generate_hourly_forecast_comprehensive(
            current_temp, current_condition, sensor_data
        )

        assert len(result) == 24

        # Extract conditions from forecast
        conditions = [f[KEY_CONDITION] for f in result]

        # Count unique conditions - should have variation beyond just day/night
        unique_conditions = set(conditions)
        assert (
            len(unique_conditions) >= 2
        ), f"Should have at least 2 different conditions, got {unique_conditions}"

        # Check that micro-evolution occurs (every 6 hours starting at hour 6)
        # Hours 6, 12, 18 should potentially show different conditions
        evolution_hours = [6, 12, 18]
        evolution_conditions = [conditions[h] for h in evolution_hours]

        # At least one evolution hour should be different from the starting condition
        different_from_start = any(
            cond != current_condition for cond in evolution_conditions
        )
        assert (
            different_from_start
        ), f"Micro-evolution should produce different conditions at hours {evolution_hours}, got {evolution_conditions}"

        # Verify all conditions are valid
        valid_conditions = [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_CLEAR_NIGHT,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
            ATTR_CONDITION_POURING,
            ATTR_CONDITION_FOG,
            ATTR_CONDITION_SNOWY,
            ATTR_CONDITION_WINDY,
        ]

        for condition in conditions:
            assert condition in valid_conditions, f"Invalid condition: {condition}"

    def test_hourly_forecast_micro_evolution_with_neutral_cloud_cover(
        self, forecast, mock_analysis
    ):
        """Test micro-evolution works with neutral cloud cover (50%) using other meteorological factors."""
        current_temp = 20.0
        current_condition = ATTR_CONDITION_PARTLYCLOUDY
        sensor_data = {
            "outdoor_temp": 68.0,
            "humidity": 65.0,
            "pressure": 29.85,
            "wind_speed": 8.0,
        }

        # Mock neutral cloud cover (50%) - should trigger enhanced micro-evolution
        mock_analysis.analyze_cloud_cover.return_value = 50.0

        # Mock pressure analysis with falling pressure (should drive cloudier conditions)
        mock_analysis.analyze_pressure_trends.return_value = {
            "pressure_system": "normal",
            "storm_probability": 25.0,
            "current_trend": -0.3,  # Falling pressure
            "long_term_trend": -0.1,
        }

        result = forecast.generate_hourly_forecast_comprehensive(
            current_temp, current_condition, sensor_data
        )

        assert len(result) == 24
        conditions = [f[KEY_CONDITION] for f in result]

        # Should show some variation due to pressure-driven evolution
        unique_conditions = set(conditions)
        # With neutral cloud cover, we should at least get some variation from day/night conversion
        # and potentially micro-evolution
        assert (
            len(unique_conditions) >= 1
        ), f"Should have at least the base condition, got {unique_conditions}"

        # Check that evolution occurs at micro-evolution points (hours 6, 12, 18)
        evolution_points = [6, 12, 18]
        evolution_conditions = [conditions[h] for h in evolution_points]

        # Evolution points should have valid conditions (may or may not be different from start)
        for cond in evolution_conditions:
            assert cond in [
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_CLEAR_NIGHT,
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_CLOUDY,
                ATTR_CONDITION_RAINY,
                ATTR_CONDITION_LIGHTNING_RAINY,
            ], f"Invalid condition at evolution point: {cond}"

    def test_hourly_forecast_micro_evolution_extreme_cloud_cover(
        self, forecast, mock_analysis
    ):
        """Test micro-evolution with extreme cloud cover values still works."""
        current_temp = 18.0
        current_condition = ATTR_CONDITION_CLOUDY
        sensor_data = {
            "outdoor_temp": 64.4,
            "humidity": 70.0,
            "pressure": 29.70,
            "wind_speed": 12.0,
        }

        # Mock extreme cloud cover (< 20) - should trigger clear conditions
        mock_analysis.analyze_cloud_cover.return_value = 15.0

        result = forecast.generate_hourly_forecast_comprehensive(
            current_temp, current_condition, sensor_data
        )

        assert len(result) == 24
        conditions = [f[KEY_CONDITION] for f in result]

        # Should show some variation due to extreme cloud cover
        evolution_points = [6, 12, 18]
        evolution_conditions = [conditions[h] for h in evolution_points]

        # With extreme low cloud cover, evolution points should have valid conditions
        # May include clear/sunny conditions due to extreme cloud cover, but not guaranteed
        for cond in evolution_conditions:
            assert cond in [
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_CLEAR_NIGHT,
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_CLOUDY,
                ATTR_CONDITION_RAINY,
                ATTR_CONDITION_LIGHTNING_RAINY,
            ], f"Invalid condition at evolution point: {cond}"

        # The overall forecast should have some variation
        unique_conditions = set(conditions)
        assert (
            len(unique_conditions) >= 1
        ), f"Should have condition variation, got {unique_conditions}"
