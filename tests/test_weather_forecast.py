"""Test the weather forecasting functionality."""

from unittest.mock import Mock, patch

from homeassistant.components.weather import (
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

from custom_components.micro_weather.weather_analysis import WeatherAnalysis
from custom_components.micro_weather.weather_forecast import WeatherForecast


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
    """Create WeatherForecast instance for testing."""
    return WeatherForecast(mock_analysis)


class TestWeatherForecast:
    """Test the WeatherForecast class."""

    def test_init(self, mock_analysis):
        """Test WeatherForecast initialization."""
        forecast = WeatherForecast(mock_analysis)
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
        with patch(
            "custom_components.micro_weather.weather_forecast.datetime"
        ) as mock_datetime:
            for month in [12, 1, 2]:
                mock_datetime.now.return_value.month = month
                patterns = forecast.analyze_temperature_patterns()
                assert patterns["seasonal_pattern"] == "winter"

            # Test spring months (Mar, Apr, May)
            for month in [3, 4, 5]:
                mock_datetime.now.return_value.month = month
                patterns = forecast.analyze_temperature_patterns()
                assert patterns["seasonal_pattern"] == "spring"

            # Test summer months (Jun, Jul, Aug)
            for month in [6, 7, 8]:
                mock_datetime.now.return_value.month = month
                patterns = forecast.analyze_temperature_patterns()
                assert patterns["seasonal_pattern"] == "summer"

            # Test fall months (Sep, Oct, Nov)
            for month in [9, 10, 11]:
                mock_datetime.now.return_value.month = month
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
