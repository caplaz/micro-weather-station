"""Test the weather forecasting functionality."""

from unittest.mock import Mock

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
            0, "partly_cloudy", pressure_analysis, sensor_data
        )
        assert isinstance(condition_day1, str)
        assert condition_day1 in [
            "sunny",
            "partly_cloudy",
            "partlycloudy",
            "cloudy",
            "rainy",
            "lightning-rainy",
            "fog",
            "snowy",
            "clear-night",
        ]

        # Test storm conditions
        pressure_storm = pressure_analysis.copy()
        pressure_storm["storm_probability"] = 70
        condition_storm = forecast.forecast_condition_enhanced(
            0, "partly_cloudy", pressure_storm, sensor_data
        )
        assert condition_storm in ["lightning-rainy", "rainy"]

        # Test high pressure (should favor clear conditions)
        pressure_high = pressure_analysis.copy()
        pressure_high["pressure_system"] = "high_pressure"
        condition_high = forecast.forecast_condition_enhanced(
            0, "cloudy", pressure_high, sensor_data
        )
        # Should be more likely to be clear/sunny
        assert condition_high in ["sunny", "partly_cloudy", "cloudy"]

    def test_forecast_precipitation_enhanced(self, forecast, mock_analysis):
        """Test enhanced precipitation forecasting."""
        pressure_analysis = {
            "pressure_system": "normal",
            "storm_probability": 20.0,
        }
        humidity_trend = {
            "average": 70.0,
        }

        # Test normal conditions
        precip_normal = forecast.forecast_precipitation_enhanced(
            0, "partly_cloudy", pressure_analysis, humidity_trend
        )
        assert isinstance(precip_normal, float)
        assert precip_normal >= 0

        # Test stormy conditions
        precip_storm = forecast.forecast_precipitation_enhanced(
            0, "lightning-rainy", pressure_analysis, humidity_trend
        )
        assert precip_storm > precip_normal  # Should be more precipitation

        # Test high storm probability
        pressure_high_storm = pressure_analysis.copy()
        pressure_high_storm["storm_probability"] = 80
        precip_high_storm = forecast.forecast_precipitation_enhanced(
            0, "rainy", pressure_high_storm, humidity_trend
        )
        assert precip_high_storm > precip_normal

        # Test distant forecast (should have reduced precipitation)
        precip_distant = forecast.forecast_precipitation_enhanced(
            4, "partly_cloudy", pressure_analysis, humidity_trend
        )
        assert precip_distant <= precip_normal  # Should be reduced

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
            0, 5.0, "partly_cloudy", wind_trend, pressure_analysis
        )
        assert isinstance(wind_normal, float)
        assert wind_normal > 0  # Should be positive wind speed

        # Test stormy conditions (should have higher wind)
        wind_storm = forecast.forecast_wind_enhanced(
            0, 5.0, "lightning-rainy", wind_trend, pressure_analysis
        )
        assert wind_storm > wind_normal

        # Test low pressure system (should have higher wind)
        pressure_low = pressure_analysis.copy()
        pressure_low["pressure_system"] = "low_pressure"
        wind_low_pressure = forecast.forecast_wind_enhanced(
            0, 5.0, "cloudy", wind_trend, pressure_low
        )
        assert wind_low_pressure > wind_normal

        # Test high pressure system (should have lower wind)
        pressure_high = pressure_analysis.copy()
        pressure_high["pressure_system"] = "high_pressure"
        wind_high_pressure = forecast.forecast_wind_enhanced(
            0, 5.0, "sunny", wind_trend, pressure_high
        )
        assert wind_high_pressure < wind_normal

    def test_forecast_humidity(self, forecast, mock_analysis):
        """Test humidity forecasting."""
        humidity_trend = {
            "trend": 0.5,
        }

        # Test normal conditions
        humidity_normal = forecast.forecast_humidity(
            0, 60.0, humidity_trend, "partly_cloudy"
        )
        assert isinstance(humidity_normal, int)
        assert 10 <= humidity_normal <= 100

        # Test foggy conditions (should have high humidity)
        humidity_fog = forecast.forecast_humidity(0, 60.0, humidity_trend, "fog")
        assert humidity_fog > humidity_normal

        # Test sunny conditions (should have lower humidity)
        humidity_sunny = forecast.forecast_humidity(0, 60.0, humidity_trend, "sunny")
        assert humidity_sunny < humidity_normal

        # Test distant forecast (should gradually change)
        humidity_distant = forecast.forecast_humidity(
            3, 60.0, humidity_trend, "partly_cloudy"
        )
        assert isinstance(humidity_distant, int)
        assert 10 <= humidity_distant <= 100

    def test_analyze_temperature_patterns(self, forecast, mock_analysis):
        """Test temperature pattern analysis."""
        patterns = forecast.analyze_temperature_patterns()

        assert isinstance(patterns, dict)
        assert "trend" in patterns
        assert "daily_variation" in patterns
        assert "seasonal_pattern" in patterns

        assert isinstance(patterns["trend"], float)
        assert isinstance(patterns["daily_variation"], float)
        assert patterns["seasonal_pattern"] in [
            "winter",
            "spring",
            "summer",
            "fall",
            "normal",
        ]

        # Daily variation should be reasonable
        assert 0 < patterns["daily_variation"] < 50
