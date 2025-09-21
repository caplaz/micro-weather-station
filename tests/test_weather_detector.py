"""Test the weather detector functionality."""

from unittest.mock import Mock

from homeassistant.core import HomeAssistant
import pytest

from custom_components.micro_weather.weather_detector import WeatherDetector


class TestWeatherDetector:
    """Test the WeatherDetector class."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.states = Mock()
        return hass

    @pytest.fixture
    def mock_options(self):
        """Create mock options for WeatherDetector."""
        return {
            "outdoor_temp_sensor": "sensor.outdoor_temperature",
            "humidity_sensor": "sensor.humidity",
            "pressure_sensor": "sensor.pressure",
            "wind_speed_sensor": "sensor.wind_speed",
            "wind_direction_sensor": "sensor.wind_direction",
            "wind_gust_sensor": "sensor.wind_gust",
            "rain_rate_sensor": "sensor.rain_rate",
            "rain_state_sensor": "sensor.rain_state",
            "solar_radiation_sensor": "sensor.solar_radiation",
            "solar_lux_sensor": "sensor.solar_lux",
            "uv_index_sensor": "sensor.uv_index",
        }

    def test_init(self, mock_hass, mock_options):
        """Test WeatherDetector initialization."""
        detector = WeatherDetector(mock_hass, mock_options)
        assert detector is not None
        assert detector.hass == mock_hass
        assert detector.options == mock_options

    def test_detect_sunny_condition(self, mock_hass, mock_options, mock_sensor_data):
        """Test detection of sunny conditions."""
        # Set up mock states
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "rain_state":
                state = Mock()
                state.state = "Dry"
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "solar_radiation":
                state = Mock()
                state.state = "800.0"  # High solar radiation for sunny conditions
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "solar_lux":
                state = Mock()
                state.state = "75000.0"  # High solar lux for clear skies
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "uv_index":
                state = Mock()
                state.state = "7.0"  # High UV index for clear skies
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "rain_rate":
                state = Mock()
                state.state = "0.0"
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        # Map to correct sensor entity IDs from options
        sensor_mapping = {
            "sensor.outdoor_temp": "sensor.outdoor_temperature",
            "sensor.solar_radiation": "sensor.solar_radiation",
            "sensor.rain_rate": "sensor.rain_rate",
            "sensor.rain_state": "sensor.rain_state",
        }

        for src, dest in sensor_mapping.items():
            if src in mock_states:
                mock_states[dest] = mock_states[src]

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert result["condition"] == "sunny"

    def test_detect_rainy_condition(self, mock_hass, mock_options, mock_sensor_data):
        """Test detection of rainy conditions."""
        # Set up mock states for rainy conditions
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "rain_state":
                state = Mock()
                state.state = "Rain"
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "rain_rate":
                state = Mock()
                state.state = "0.5"  # Rain rate > 0
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "outdoor_temp":
                state = Mock()
                state.state = "60.0"  # Above freezing
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert result["condition"] == "rainy"

    def test_detect_stormy_condition(self, mock_hass, mock_options, mock_sensor_data):
        """Test detection of stormy conditions."""
        # Set up mock states for stormy conditions
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "rain_rate":
                state = Mock()
                state.state = "0.3"
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "wind_gust":
                state = Mock()
                state.state = "30.0"  # High wind gust
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "pressure":
                state = Mock()
                state.state = "29.5"  # Low pressure
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert result["condition"] == "stormy"

    def test_detect_snowy_condition(self, mock_hass, mock_options, mock_sensor_data):
        """Test detection of snowy conditions."""
        # Set up mock states for snowy conditions
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "rain_rate":
                state = Mock()
                state.state = "0.2"
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "outdoor_temp":
                state = Mock()
                state.state = "30.0"  # Below freezing
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        # Map to the correct sensor entity ID
        mock_states["sensor.outdoor_temperature"] = mock_states["sensor.outdoor_temp"]

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert result["condition"] == "snowy"

    def test_detect_cloudy_condition(self, mock_hass, mock_options, mock_sensor_data):
        """Test detection of cloudy conditions."""
        # Set up mock states for cloudy conditions
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "solar_radiation":
                state = Mock()
                state.state = "50.0"  # Low solar radiation
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "rain_rate":
                state = Mock()
                state.state = "0.0"
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "rain_state":
                state = Mock()
                state.state = "Dry"
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert result["condition"] == "cloudy"

    def test_forecast_generation(self, mock_hass, mock_options, mock_sensor_data):
        """Test that forecast is generated."""
        # Set up mock states with basic sensor data
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            state = Mock()
            state.state = str(value)
            mock_states[f"sensor.{sensor_key}"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert "forecast" in result
        assert len(result["forecast"]) == 5

        # Check forecast structure
        forecast_item = result["forecast"][0]
        assert "datetime" in forecast_item
        assert "temperature" in forecast_item
        assert "condition" in forecast_item

    def test_temperature_conversion(self, mock_hass, mock_options, mock_sensor_data):
        """Test temperature conversion from Fahrenheit to Celsius."""
        # Set up mock states with 72°F temperature
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "outdoor_temp":
                state = Mock()
                state.state = "72.0"  # 72°F
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        # Map to the correct sensor entity ID from options
        mock_states["sensor.outdoor_temperature"] = mock_states["sensor.outdoor_temp"]

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        # 72°F should be approximately 22.2°C
        assert abs(result["temperature"] - 22.2) < 0.5

    def test_pressure_conversion(self, mock_hass, mock_options, mock_sensor_data):
        """Test pressure conversion from inHg to hPa."""
        # Set up mock states with 29.92 inHg pressure
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "pressure":
                state = Mock()
                state.state = "29.92"  # 29.92 inHg
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        # 29.92 inHg should be approximately 1013 hPa
        assert abs(result["pressure"] - 1013) < 5

    def test_wind_speed_conversion(self, mock_hass, mock_options, mock_sensor_data):
        """Test wind speed conversion from mph to km/h."""
        # Set up mock states with 5.5 mph wind speed
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "wind_speed":
                state = Mock()
                state.state = "5.5"  # 5.5 mph
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        # 5.5 mph should be approximately 8.9 km/h
        assert abs(result["wind_speed"] - 8.9) < 1.0

    def test_visibility_calculation(self, mock_hass, mock_options, mock_sensor_data):
        """Test visibility calculation."""
        # Set up mock states with basic sensor data
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            state = Mock()
            state.state = str(value)
            mock_states[f"sensor.{sensor_key}"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert "visibility" in result
        assert result["visibility"] > 0
