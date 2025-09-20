"""Test the weather detector functionality."""
import pytest
from custom_components.micro_weather.weather_detector import WeatherDetector


class TestWeatherDetector:
    """Test the WeatherDetector class."""

    def test_init(self):
        """Test WeatherDetector initialization."""
        detector = WeatherDetector()
        assert detector is not None

    def test_detect_sunny_condition(self, mock_sensor_data):
        """Test detection of sunny conditions."""
        detector = WeatherDetector()
        
        # High solar radiation should indicate sunny
        mock_sensor_data["solar_radiation"] = 500.0
        mock_sensor_data["rain_rate"] = 0.0
        mock_sensor_data["rain_state"] = "Dry"
        
        result = detector.detect_weather(mock_sensor_data)
        assert result["condition"] == "sunny"

    def test_detect_rainy_condition(self, mock_sensor_data):
        """Test detection of rainy conditions."""
        detector = WeatherDetector()
        
        # Rain rate > 0 should indicate rainy
        mock_sensor_data["rain_rate"] = 0.5
        mock_sensor_data["rain_state"] = "Rain"
        mock_sensor_data["outdoor_temp"] = 60.0  # Above freezing
        
        result = detector.detect_weather(mock_sensor_data)
        assert result["condition"] == "rainy"

    def test_detect_stormy_condition(self, mock_sensor_data):
        """Test detection of stormy conditions."""
        detector = WeatherDetector()
        
        # High wind + rain should indicate stormy
        mock_sensor_data["rain_rate"] = 0.3
        mock_sensor_data["wind_gust"] = 30.0
        mock_sensor_data["pressure"] = 29.5  # Low pressure
        
        result = detector.detect_weather(mock_sensor_data)
        assert result["condition"] == "stormy"

    def test_detect_snowy_condition(self, mock_sensor_data):
        """Test detection of snowy conditions."""
        detector = WeatherDetector()
        
        # Rain + low temp should indicate snow
        mock_sensor_data["rain_rate"] = 0.2
        mock_sensor_data["outdoor_temp"] = 30.0  # Below freezing
        
        result = detector.detect_weather(mock_sensor_data)
        assert result["condition"] == "snowy"

    def test_detect_cloudy_condition(self, mock_sensor_data):
        """Test detection of cloudy conditions."""
        detector = WeatherDetector()
        
        # Low solar radiation, no rain
        mock_sensor_data["solar_radiation"] = 50.0
        mock_sensor_data["rain_rate"] = 0.0
        mock_sensor_data["rain_state"] = "Dry"
        
        result = detector.detect_weather(mock_sensor_data)
        assert result["condition"] == "cloudy"

    def test_forecast_generation(self, mock_sensor_data):
        """Test that forecast is generated."""
        detector = WeatherDetector()
        
        result = detector.detect_weather(mock_sensor_data)
        assert "forecast" in result
        assert len(result["forecast"]) == 5
        
        # Check forecast structure
        forecast_item = result["forecast"][0]
        assert "datetime" in forecast_item
        assert "temperature" in forecast_item
        assert "condition" in forecast_item

    def test_temperature_conversion(self, mock_sensor_data):
        """Test temperature conversion from Fahrenheit to Celsius."""
        detector = WeatherDetector()
        
        # 72°F should be approximately 22.2°C
        result = detector.detect_weather(mock_sensor_data)
        assert abs(result["temperature"] - 22.2) < 0.5

    def test_pressure_conversion(self, mock_sensor_data):
        """Test pressure conversion from inHg to hPa."""
        detector = WeatherDetector()
        
        # 29.92 inHg should be approximately 1013 hPa
        result = detector.detect_weather(mock_sensor_data)
        assert abs(result["pressure"] - 1013) < 5

    def test_wind_speed_conversion(self, mock_sensor_data):
        """Test wind speed conversion from mph to km/h."""
        detector = WeatherDetector()
        
        # 5.5 mph should be approximately 8.9 km/h
        result = detector.detect_weather(mock_sensor_data)
        assert abs(result["wind_speed"] - 8.9) < 1.0

    def test_visibility_calculation(self, mock_sensor_data):
        """Test visibility calculation."""
        detector = WeatherDetector()
        
        result = detector.detect_weather(mock_sensor_data)
        assert "visibility" in result
        assert result["visibility"] > 0