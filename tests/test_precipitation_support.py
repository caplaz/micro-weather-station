"""Test precipitation support in weather entity."""

from unittest.mock import Mock

from custom_components.micro_weather.weather_detector import WeatherDetector
from custom_components.micro_weather.weather_utils import convert_precipitation_rate


class TestPrecipitationSupport:
    """Test precipitation support functionality."""

    def test_convert_precipitation_rate_inches(self):
        """Test conversion from inches per hour to mm per hour."""
        # Test inches per hour conversion
        result = convert_precipitation_rate(1.0, "in/h")
        assert result == 25.4  # 1 inch = 25.4 mm

        result = convert_precipitation_rate(0.1, "in/hr")
        assert result == 2.5  # 0.1 inch = 2.54 mm, rounded to 2.5

        result = convert_precipitation_rate(0.5, "inches/h")
        assert result == 12.7  # 0.5 inch = 12.7 mm

    def test_convert_precipitation_rate_mm(self):
        """Test mm per hour (no conversion needed)."""
        # Test mm per hour (no conversion)
        result = convert_precipitation_rate(10.0, "mm/h")
        assert result == 10.0

        result = convert_precipitation_rate(5.5, "mmh")
        assert result == 5.5

    def test_convert_precipitation_rate_no_unit(self):
        """Test precipitation rate without unit (assume mm/h)."""
        # Test no unit specified (assume mm/h)
        result = convert_precipitation_rate(3.0, None)
        assert result == 3.0

        result = convert_precipitation_rate(7.5, "")
        assert result == 7.5

    def test_convert_precipitation_rate_none_value(self):
        """Test precipitation rate with None value."""
        # Test None value
        result = convert_precipitation_rate(None, "in/h")
        assert result is None

    def test_convert_precipitation_rate_invalid_value(self):
        """Test precipitation rate with invalid value."""
        # Test invalid value
        result = convert_precipitation_rate("invalid", "in/h")
        assert result is None

    def test_weather_data_includes_precipitation(self):
        """Test that weather data includes precipitation when rain_rate sensor is configured."""
        mock_hass = Mock()
        mock_hass.states.get.return_value = None  # No sensors configured

        # Mock options with rain_rate sensor
        mock_options = {
            "outdoor_temp_sensor": "sensor.outdoor_temp",
            "rain_rate_sensor": "sensor.rain_rate",
        }

        detector = WeatherDetector(mock_hass, mock_options)

        # Mock sensor states
        temp_state = Mock()
        temp_state.state = "20.0"
        temp_state.attributes = {"unit_of_measurement": "°C"}

        rain_state = Mock()
        rain_state.state = "0.1"  # 0.1 in/h
        rain_state.attributes = {"unit_of_measurement": "in/h"}

        def mock_get_state(entity_id):
            if entity_id == "sensor.outdoor_temp":
                return temp_state
            elif entity_id == "sensor.rain_rate":
                return rain_state
            return None

        mock_hass.states.get.side_effect = mock_get_state

        # Get weather data
        weather_data = detector.get_weather_data()

        # Verify precipitation is included (no conversion, returns raw sensor value)
        assert "precipitation" in weather_data
        assert weather_data["precipitation"] == 0.1  # Raw sensor value in in/h
        assert weather_data.get("precipitation_unit") == "in"

    def test_weather_data_no_precipitation_sensor(self):
        """Test that weather data handles missing precipitation sensor gracefully."""
        mock_hass = Mock()
        mock_hass.states.get.return_value = None

        # Mock options without rain_rate sensor
        mock_options = {
            "outdoor_temp_sensor": "sensor.outdoor_temp",
        }

        detector = WeatherDetector(mock_hass, mock_options)

        # Mock only temperature sensor
        temp_state = Mock()
        temp_state.state = "20.0"
        temp_state.attributes = {"unit_of_measurement": "°C"}

        def mock_get_state(entity_id):
            if entity_id == "sensor.outdoor_temp":
                return temp_state
            return None

        mock_hass.states.get.side_effect = mock_get_state

        # Get weather data
        weather_data = detector.get_weather_data()

        # Verify precipitation is None when no sensor configured
        assert weather_data.get("precipitation") is None
