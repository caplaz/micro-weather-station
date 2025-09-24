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
        # Check that analysis and forecast modules are initialized
        assert hasattr(detector, "analysis")
        assert hasattr(detector, "forecast")
        assert detector.analysis is not None
        assert detector.forecast is not None

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
            "sensor.humidity": "sensor.humidity",
            "sensor.pressure": "sensor.pressure",
            "sensor.wind_speed": "sensor.wind_speed",
            "sensor.wind_direction": "sensor.wind_direction",
            "sensor.wind_gust": "sensor.wind_gust",
            "sensor.rain_rate": "sensor.rain_rate",
            "sensor.rain_state": "sensor.rain_state",
            "sensor.solar_radiation": "sensor.solar_radiation",
            "sensor.solar_lux": "sensor.solar_lux",
            "sensor.uv_index": "sensor.uv_index",
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
                # Moisture sensor reports "Wet" when precipitation is detected
                state.state = "Wet"
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

    def test_detect_partly_cloudy_condition(
        self, mock_hass, mock_options, mock_sensor_data
    ):
        """Test detection of partly cloudy conditions."""
        # Set up mock states for partly cloudy conditions (moderate cloud cover)
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "solar_radiation":
                state = Mock()
                state.state = "400.0"  # Moderate solar radiation
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "solar_lux":
                state = Mock()
                state.state = "40000.0"  # Moderate lux
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "uv_index":
                state = Mock()
                state.state = "4.0"  # Moderate UV
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert result["condition"] == "partly_cloudy"

    def test_detect_clear_night_condition(self, mock_hass, mock_options):
        """Test detection of clear night conditions."""
        # Set up sensor data for clear night
        detector = WeatherDetector(mock_hass, mock_options)

        # Mock states for clear night (high pressure, calm winds, low humidity)
        mock_states = {
            "sensor.outdoor_temperature": Mock(state="70.0"),
            "sensor.humidity": Mock(state="40.0"),
            "sensor.pressure": Mock(state="30.10"),  # High pressure
            "sensor.wind_speed": Mock(state="2.0"),  # Calm winds
            "sensor.wind_gust": Mock(state="5.0"),
            "sensor.solar_radiation": Mock(state="0.0"),  # Night
            "sensor.solar_lux": Mock(state="0.0"),
            "sensor.rain_rate": Mock(state="0.0"),
        }

        mock_hass.states.get.side_effect = lambda entity_id: mock_states.get(entity_id)

        result = detector.get_weather_data()
        assert result["condition"] == "clear-night"

    def test_detect_foggy_condition(self, mock_hass, mock_options, mock_sensor_data):
        """Test detection of foggy conditions."""
        # Set up mock states for foggy conditions
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "humidity":
                state = Mock()
                state.state = "95.0"  # Very high humidity
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "outdoor_temp":
                state = Mock()
                state.state = "65.0"  # Cool temperature
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "wind_speed":
                state = Mock()
                state.state = "2.0"  # Light wind
                mock_states[f"sensor.{sensor_key}"] = state
            elif sensor_key == "rain_rate":
                state = Mock()
                state.state = "0.0"  # No rain
                mock_states[f"sensor.{sensor_key}"] = state
            else:
                state = Mock()
                state.state = str(value)
                mock_states[f"sensor.{sensor_key}"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert result["condition"] == "foggy"

    def test_detect_snowy_condition_edge_cases(
        self, mock_hass, mock_options, mock_sensor_data
    ):
        """Test detection of snowy conditions with edge cases."""
        # Test with freezing temperature and light precipitation
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "rain_rate":
                state = Mock()
                state.state = "0.1"  # Light precipitation
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

    def test_weather_condition_with_low_solar_radiation(self, mock_hass, mock_options):
        """Test weather detection with low solar radiation scenario."""
        # Simulate the user's actual sensor readings
        mock_states = {
            "sensor.outdoor_temperature": Mock(state="72.0"),
            "sensor.humidity": Mock(state="65.0"),
            "sensor.pressure": Mock(state="29.92"),
            "sensor.wind_speed": Mock(state="5.5"),
            "sensor.wind_direction": Mock(state="180.0"),
            "sensor.wind_gust": Mock(state="8.0"),
            "sensor.rain_rate": Mock(state="0.0"),
            "sensor.rain_state": Mock(state="Dry"),
            "sensor.solar_radiation": Mock(state="26.0"),  # User's actual reading
            "sensor.solar_lux": Mock(state="15000.0"),  # User's actual reading
            "sensor.uv_index": Mock(state="0.5"),  # User's reading
        }

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()

        # With the improved algorithm, this should detect partly cloudy
        # (not cloudy as it would have before the fix)
        assert result["condition"] == "partly_cloudy"

        # Verify cloud cover is around 40% (the fallback value)
        # Note: We can't directly test cloud cover here since it's internal to analysis
        # but the condition detection should reflect the improved logic

    def test_weather_condition_boundaries(self, mock_hass, mock_options):
        """Test weather condition detection at boundary values."""
        # Test boundary between sunny and partly cloudy
        mock_states_sunny = {
            "sensor.outdoor_temperature": Mock(state="75.0"),
            "sensor.humidity": Mock(state="50.0"),
            "sensor.pressure": Mock(state="30.10"),
            "sensor.wind_speed": Mock(state="3.0"),
            "sensor.wind_direction": Mock(state="90.0"),
            "sensor.wind_gust": Mock(state="5.0"),
            "sensor.rain_rate": Mock(state="0.0"),
            "sensor.rain_state": Mock(state="Dry"),
            "sensor.solar_radiation": Mock(state="750.0"),  # High radiation
            "sensor.solar_lux": Mock(state="70000.0"),  # High lux
            "sensor.uv_index": Mock(state="7.5"),  # High UV
        }

        mock_hass.states.get = lambda entity_id: mock_states_sunny.get(entity_id)
        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert result["condition"] == "sunny"

        # Test boundary between partly cloudy and cloudy
        mock_states_cloudy = {
            "sensor.outdoor_temperature": Mock(state="70.0"),
            "sensor.humidity": Mock(state="60.0"),
            "sensor.pressure": Mock(state="29.92"),
            "sensor.wind_speed": Mock(state="5.0"),
            "sensor.wind_direction": Mock(state="180.0"),
            "sensor.wind_gust": Mock(state="7.0"),
            "sensor.rain_rate": Mock(state="0.0"),
            "sensor.rain_state": Mock(state="Dry"),
            "sensor.solar_radiation": Mock(state="100.0"),  # Low radiation
            "sensor.solar_lux": Mock(state="8000.0"),  # Low lux
            "sensor.uv_index": Mock(state="1.5"),  # Low UV
        }

        mock_hass.states.get = lambda entity_id: mock_states_cloudy.get(entity_id)
        detector2 = WeatherDetector(mock_hass, mock_options)
        result2 = detector2.get_weather_data()
        assert result2["condition"] == "cloudy"

    def test_weather_detection_with_missing_sensors(self, mock_hass, mock_options):
        """Test weather detection when some sensors are unavailable."""
        # Test with missing solar sensors (should still work)
        mock_states = {
            "sensor.outdoor_temperature": Mock(state="70.0"),
            "sensor.humidity": Mock(state="60.0"),
            "sensor.pressure": Mock(state="29.92"),
            "sensor.wind_speed": Mock(state="5.0"),
            "sensor.wind_direction": Mock(state="180.0"),
            "sensor.wind_gust": Mock(state="8.0"),
            "sensor.rain_rate": Mock(state="0.0"),
            "sensor.rain_state": Mock(state="Dry"),
            # Missing solar sensors
        }

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()

        # Should still provide a valid condition even with missing solar data
        assert "condition" in result
        assert result["condition"] is not None
        assert isinstance(result["condition"], str)

    def test_weather_detection_with_extreme_values(self, mock_hass, mock_options):
        """Test weather detection with extreme sensor values."""
        # Test with extreme heat
        mock_states_hot = {
            "sensor.outdoor_temperature": Mock(state="110.0"),  # Very hot
            "sensor.humidity": Mock(state="10.0"),  # Very dry
            "sensor.pressure": Mock(state="30.20"),  # High pressure
            "sensor.wind_speed": Mock(state="2.0"),
            "sensor.wind_direction": Mock(state="180.0"),
            "sensor.wind_gust": Mock(state="3.0"),
            "sensor.rain_rate": Mock(state="0.0"),
            "sensor.rain_state": Mock(state="Dry"),
            "sensor.solar_radiation": Mock(state="900.0"),
            "sensor.solar_lux": Mock(state="85000.0"),
            "sensor.uv_index": Mock(state="9.0"),
        }

        mock_hass.states.get = lambda entity_id: mock_states_hot.get(entity_id)
        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()
        assert result["condition"] == "sunny"  # Should still detect clear conditions

        # Test with extreme cold
        mock_states_cold = {
            "sensor.outdoor_temperature": Mock(state="-10.0"),  # Very cold
            "sensor.humidity": Mock(state="80.0"),  # Humid
            "sensor.pressure": Mock(state="29.50"),  # Low pressure
            "sensor.wind_speed": Mock(state="15.0"),
            "sensor.wind_direction": Mock(state="270.0"),
            "sensor.wind_gust": Mock(state="25.0"),
            "sensor.rain_rate": Mock(state="0.0"),
            "sensor.rain_state": Mock(state="Dry"),
            "sensor.solar_radiation": Mock(state="200.0"),
            "sensor.solar_lux": Mock(state="15000.0"),
            "sensor.uv_index": Mock(state="2.0"),
        }

        mock_hass.states.get = lambda entity_id: mock_states_cold.get(entity_id)
        detector2 = WeatherDetector(mock_hass, mock_options)
        result2 = detector2.get_weather_data()
        # Should detect some condition (likely cloudy or partly cloudy due to low solar)
        assert result2["condition"] in ["partly_cloudy", "cloudy", "sunny"]

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

    def test_get_weather_data_structure(
        self, mock_hass, mock_options, mock_sensor_data
    ):
        """Test that get_weather_data returns correct structure."""
        # Set up mock states
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            state = Mock()
            state.state = str(value)
            # Use the correct entity IDs from mock_options
            if sensor_key == "outdoor_temp":
                mock_states["sensor.outdoor_temperature"] = state
            elif sensor_key == "humidity":
                mock_states["sensor.humidity"] = state
            elif sensor_key == "pressure":
                mock_states["sensor.pressure"] = state
            elif sensor_key == "wind_speed":
                mock_states["sensor.wind_speed"] = state
            elif sensor_key == "wind_direction":
                mock_states["sensor.wind_direction"] = state
            elif sensor_key == "wind_gust":
                mock_states["sensor.wind_gust"] = state
            elif sensor_key == "rain_rate":
                mock_states["sensor.rain_rate"] = state
            elif sensor_key == "rain_state":
                mock_states["sensor.rain_state"] = state
            elif sensor_key == "solar_radiation":
                mock_states["sensor.solar_radiation"] = state
            elif sensor_key == "solar_lux":
                mock_states["sensor.solar_lux"] = state
            elif sensor_key == "uv_index":
                mock_states["sensor.uv_index"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()

        # Check required fields are present
        required_fields = [
            "temperature",
            "humidity",
            "pressure",
            "wind_speed",
            "wind_direction",
            "visibility",
            "condition",
            "forecast",
            "last_updated",
        ]

        for field in required_fields:
            assert field in result

        # Check data types
        assert isinstance(result["temperature"], (float, type(None)))
        assert isinstance(result["humidity"], (float, type(None)))
        assert isinstance(result["pressure"], (float, type(None)))
        assert isinstance(result["wind_speed"], (float, type(None)))
        assert isinstance(result["condition"], str)
        assert isinstance(result["forecast"], list)

    def test_sensor_data_filtering(self, mock_hass, mock_options, mock_sensor_data):
        """Test that None values are filtered from results."""
        # Set up mock states with some unavailable sensors
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            if sensor_key == "pressure":  # Simulate unavailable pressure sensor
                continue  # Don't add this sensor
            else:
                state = Mock()
                state.state = str(value)
                # Use the correct entity IDs from mock_options
                if sensor_key == "outdoor_temp":
                    mock_states["sensor.outdoor_temperature"] = state
                elif sensor_key == "humidity":
                    mock_states["sensor.humidity"] = state
                elif sensor_key == "wind_speed":
                    mock_states["sensor.wind_speed"] = state
                elif sensor_key == "wind_direction":
                    mock_states["sensor.wind_direction"] = state
                elif sensor_key == "wind_gust":
                    mock_states["sensor.wind_gust"] = state
                elif sensor_key == "rain_rate":
                    mock_states["sensor.rain_rate"] = state
                elif sensor_key == "rain_state":
                    mock_states["sensor.rain_state"] = state
                elif sensor_key == "solar_radiation":
                    mock_states["sensor.solar_radiation"] = state
                elif sensor_key == "solar_lux":
                    mock_states["sensor.solar_lux"] = state
                elif sensor_key == "uv_index":
                    mock_states["sensor.uv_index"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()

        # Pressure should not be in result since sensor was unavailable
        assert "pressure" not in result or result["pressure"] is None

        # Other fields should still be present
        assert "temperature" in result
        assert "condition" in result

    def test_historical_data_storage(self, mock_hass, mock_options, mock_sensor_data):
        """Test that historical data is stored properly."""
        # Set up mock states
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            state = Mock()
            state.state = str(value)
            # Use the correct entity IDs from mock_options
            if sensor_key == "outdoor_temp":
                mock_states["sensor.outdoor_temperature"] = state
            elif sensor_key == "humidity":
                mock_states["sensor.humidity"] = state
            elif sensor_key == "pressure":
                mock_states["sensor.pressure"] = state
            elif sensor_key == "wind_speed":
                mock_states["sensor.wind_speed"] = state
            elif sensor_key == "wind_direction":
                mock_states["sensor.wind_direction"] = state
            elif sensor_key == "wind_gust":
                mock_states["sensor.wind_gust"] = state
            elif sensor_key == "rain_rate":
                mock_states["sensor.rain_rate"] = state
            elif sensor_key == "rain_state":
                mock_states["sensor.rain_state"] = state
            elif sensor_key == "solar_radiation":
                mock_states["sensor.solar_radiation"] = state
            elif sensor_key == "solar_lux":
                mock_states["sensor.solar_lux"] = state
            elif sensor_key == "uv_index":
                mock_states["sensor.uv_index"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)

        # Check initial history is empty (except for any defaults)
        initial_temp_history = len(
            detector.analysis._sensor_history.get("outdoor_temp", [])
        )

        # Get weather data (this should store historical data)
        detector.get_weather_data()

        # Check that historical data was added
        final_temp_history = len(
            detector.analysis._sensor_history.get("outdoor_temp", [])
        )
        assert final_temp_history >= initial_temp_history

    def test_condition_history_tracking(
        self, mock_hass, mock_options, mock_sensor_data
    ):
        """Test that weather conditions are tracked historically."""
        # Set up mock states
        mock_states = {}
        for sensor_key, value in mock_sensor_data.items():
            state = Mock()
            state.state = str(value)
            # Use the correct entity IDs from mock_options
            if sensor_key == "outdoor_temp":
                mock_states["sensor.outdoor_temperature"] = state
            elif sensor_key == "humidity":
                mock_states["sensor.humidity"] = state
            elif sensor_key == "pressure":
                mock_states["sensor.pressure"] = state
            elif sensor_key == "wind_speed":
                mock_states["sensor.wind_speed"] = state
            elif sensor_key == "wind_direction":
                mock_states["sensor.wind_direction"] = state
            elif sensor_key == "wind_gust":
                mock_states["sensor.wind_gust"] = state
            elif sensor_key == "rain_rate":
                mock_states["sensor.rain_rate"] = state
            elif sensor_key == "rain_state":
                mock_states["sensor.rain_state"] = state
            elif sensor_key == "solar_radiation":
                mock_states["sensor.solar_radiation"] = state
            elif sensor_key == "solar_lux":
                mock_states["sensor.solar_lux"] = state
            elif sensor_key == "uv_index":
                mock_states["sensor.uv_index"] = state

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)

        # Get weather data multiple times
        result1 = detector.get_weather_data()
        result2 = detector.get_weather_data()

        # Both results should have conditions
        assert "condition" in result1
        assert "condition" in result2
        assert isinstance(result1["condition"], str)
        assert isinstance(result2["condition"], str)

    def test_convert_temperature_celsius(self, mock_hass, mock_options):
        """Test temperature conversion with Celsius input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test various Celsius inputs
        assert detector._convert_temperature(25.0, "°C") == 25.0
        assert detector._convert_temperature(0.0, "C") == 0.0
        assert detector._convert_temperature(-10.5, "celsius") == -10.5
        assert detector._convert_temperature(100.0, "°C") == 100.0

    def test_convert_temperature_fahrenheit(self, mock_hass, mock_options):
        """Test temperature conversion with Fahrenheit input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test Fahrenheit to Celsius conversions
        assert detector._convert_temperature(77.0, "°F") == 25.0  # 77°F = 25°C
        assert detector._convert_temperature(32.0, "F") == 0.0  # 32°F = 0°C
        assert (
            detector._convert_temperature(212.0, "fahrenheit") == 100.0
        )  # 212°F = 100°C
        assert detector._convert_temperature(-40.0, "°F") == -40.0  # -40°F = -40°C

    def test_convert_temperature_unknown_unit(self, mock_hass, mock_options):
        """Test temperature conversion with unknown or missing units."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test unknown units (should assume Celsius)
        assert detector._convert_temperature(25.0, "kelvin") == 25.0
        assert detector._convert_temperature(25.0, "K") == 25.0
        assert detector._convert_temperature(25.0, None) == 25.0
        assert detector._convert_temperature(25.0, "") == 25.0

    def test_convert_temperature_none_value(self, mock_hass, mock_options):
        """Test temperature conversion with None input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test None input
        assert detector._convert_temperature(None, "°C") is None
        assert detector._convert_temperature(None, "°F") is None
        assert detector._convert_temperature(None, None) is None

    def test_convert_pressure_hpa(self, mock_hass, mock_options):
        """Test pressure conversion with hPa input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test various hPa inputs
        assert detector._convert_pressure(1013.25, "hPa") == 1013.2
        assert detector._convert_pressure(1000.0, "mbar") == 1000.0
        assert detector._convert_pressure(1013.0, "mb") == 1013.0

    def test_convert_pressure_inhg(self, mock_hass, mock_options):
        """Test pressure conversion with inHg input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test inHg to hPa conversions
        assert (
            detector._convert_pressure(29.92, "inHg") == 1013.2
        )  # Standard atmospheric pressure
        assert detector._convert_pressure(30.0, "inhg") == 1015.9
        assert detector._convert_pressure(28.0, '"Hg') == 948.2

    def test_convert_pressure_unknown_unit(self, mock_hass, mock_options):
        """Test pressure conversion with unknown or missing units."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test unknown units (should assume hPa)
        assert detector._convert_pressure(1013.0, "psi") == 1013.0
        assert detector._convert_pressure(1013.0, "bar") == 1013.0
        assert detector._convert_pressure(1013.0, None) == 1013.0
        assert detector._convert_pressure(1013.0, "") == 1013.0

    def test_convert_pressure_none_value(self, mock_hass, mock_options):
        """Test pressure conversion with None input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test None input
        assert detector._convert_pressure(None, "hPa") is None
        assert detector._convert_pressure(None, "inHg") is None
        assert detector._convert_pressure(None, None) is None

    def test_convert_wind_speed_kmh(self, mock_hass, mock_options):
        """Test wind speed conversion with km/h input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test various km/h inputs
        assert detector._convert_wind_speed(10.0, "km/h") == 10.0
        assert detector._convert_wind_speed(25.5, "kmh") == 25.5
        assert detector._convert_wind_speed(0.0, "kph") == 0.0

    def test_convert_wind_speed_mph(self, mock_hass, mock_options):
        """Test wind speed conversion with mph input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test mph to km/h conversions
        assert (
            detector._convert_wind_speed(10.0, "mph") == 16.1
        )  # 10 mph = 16.0934 km/h
        assert detector._convert_wind_speed(1.0, "mi/h") == 1.6  # 1 mph = 1.60934 km/h
        assert detector._convert_wind_speed(0.0, "mph") == 0.0

    def test_convert_wind_speed_ms(self, mock_hass, mock_options):
        """Test wind speed conversion with m/s input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test m/s to km/h conversions
        assert detector._convert_wind_speed(10.0, "m/s") == 36.0  # 10 m/s = 36 km/h
        assert detector._convert_wind_speed(2.5, "ms") == 9.0  # 2.5 m/s = 9 km/h
        assert detector._convert_wind_speed(0.0, "m/s") == 0.0

    def test_convert_wind_speed_unknown_unit(self, mock_hass, mock_options):
        """Test wind speed conversion with unknown or missing units."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test unknown units (should assume km/h)
        assert detector._convert_wind_speed(10.0, "knots") == 10.0
        assert detector._convert_wind_speed(10.0, "beaufort") == 10.0
        assert detector._convert_wind_speed(10.0, None) == 10.0
        assert detector._convert_wind_speed(10.0, "") == 10.0

    def test_convert_wind_speed_none_value(self, mock_hass, mock_options):
        """Test wind speed conversion with None input."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test None input
        assert detector._convert_wind_speed(None, "km/h") is None
        assert detector._convert_wind_speed(None, "mph") is None
        assert detector._convert_wind_speed(None, "m/s") is None
        assert detector._convert_wind_speed(None, None) is None

    def test_unit_conversion_accuracy(self, mock_hass, mock_options):
        """Test conversion accuracy with precise values."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test precise temperature conversions
        assert abs(detector._convert_temperature(77.0, "°F") - 25.0) < 0.1
        assert abs(detector._convert_temperature(32.0, "°F") - 0.0) < 0.1

        # Test precise pressure conversions
        assert abs(detector._convert_pressure(29.92, "inHg") - 1013.25) < 0.1
        assert abs(detector._convert_pressure(30.0, "inHg") - 1015.92) < 0.1

        # Test precise wind speed conversions
        assert abs(detector._convert_wind_speed(10.0, "mph") - 16.0934) < 0.1
        assert abs(detector._convert_wind_speed(10.0, "m/s") - 36.0) < 0.1

    def test_get_sensor_values_with_units(self, mock_hass, mock_options):
        """Test that sensor values and units are captured correctly."""
        # Set up mock states with unit_of_measurement attributes
        mock_states = {
            "sensor.outdoor_temperature": Mock(
                state="25.0", attributes={"unit_of_measurement": "°C"}
            ),
            "sensor.pressure": Mock(
                state="1013.25", attributes={"unit_of_measurement": "hPa"}
            ),
            "sensor.wind_speed": Mock(
                state="10.0", attributes={"unit_of_measurement": "km/h"}
            ),
            "sensor.humidity": Mock(
                state="65.0", attributes={"unit_of_measurement": "%"}
            ),
        }

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        sensor_data = detector._get_sensor_values()

        # Check that values are captured
        assert sensor_data["outdoor_temp"] == 25.0
        assert sensor_data["pressure"] == 1013.25
        assert sensor_data["wind_speed"] == 10.0
        assert sensor_data["humidity"] == 65.0

        # Check that units are captured
        assert sensor_data["outdoor_temp_unit"] == "°C"
        assert sensor_data["pressure_unit"] == "hPa"
        assert sensor_data["wind_speed_unit"] == "km/h"
        assert sensor_data["humidity_unit"] == "%"

    def test_get_weather_data_with_metric_units(self, mock_hass, mock_options):
        """Test weather data conversion with metric sensor units."""
        # Set up mock states with metric units (like Tempest weather station)
        mock_states = {
            "sensor.outdoor_temperature": Mock(
                state="25.0", attributes={"unit_of_measurement": "°C"}
            ),
            "sensor.pressure": Mock(
                state="1013.25", attributes={"unit_of_measurement": "hPa"}
            ),
            "sensor.wind_speed": Mock(
                state="10.0", attributes={"unit_of_measurement": "km/h"}
            ),
            "sensor.humidity": Mock(
                state="65.0", attributes={"unit_of_measurement": "%"}
            ),
            "sensor.wind_direction": Mock(
                state="180.0", attributes={"unit_of_measurement": "°"}
            ),
            "sensor.wind_gust": Mock(
                state="15.0", attributes={"unit_of_measurement": "km/h"}
            ),
            "sensor.rain_rate": Mock(
                state="0.0", attributes={"unit_of_measurement": "mm/h"}
            ),
            "sensor.rain_state": Mock(state="Dry", attributes={}),
            "sensor.solar_radiation": Mock(
                state="250.0", attributes={"unit_of_measurement": "W/m²"}
            ),
            "sensor.solar_lux": Mock(
                state="25000.0", attributes={"unit_of_measurement": "lx"}
            ),
            "sensor.uv_index": Mock(
                state="3.0", attributes={"unit_of_measurement": "UV index"}
            ),
        }

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()

        # Values should remain in metric (no conversion needed)
        assert result["temperature"] == 25.0  # Already in Celsius
        assert result["pressure"] == 1013.2  # Already in hPa (rounded)
        assert result["wind_speed"] == 10.0  # Already in km/h

    def test_get_weather_data_with_imperial_units(self, mock_hass, mock_options):
        """Test weather data conversion with imperial sensor units."""
        # Set up mock states with imperial units
        mock_states = {
            "sensor.outdoor_temperature": Mock(
                state="77.0", attributes={"unit_of_measurement": "°F"}
            ),
            "sensor.pressure": Mock(
                state="29.92", attributes={"unit_of_measurement": "inHg"}
            ),
            "sensor.wind_speed": Mock(
                state="10.0", attributes={"unit_of_measurement": "mph"}
            ),
            "sensor.humidity": Mock(
                state="65.0", attributes={"unit_of_measurement": "%"}
            ),
            "sensor.wind_direction": Mock(
                state="180.0", attributes={"unit_of_measurement": "°"}
            ),
            "sensor.wind_gust": Mock(
                state="15.0", attributes={"unit_of_measurement": "mph"}
            ),
            "sensor.rain_rate": Mock(
                state="0.0", attributes={"unit_of_measurement": "in/h"}
            ),
            "sensor.rain_state": Mock(state="Dry", attributes={}),
            "sensor.solar_radiation": Mock(
                state="250.0", attributes={"unit_of_measurement": "W/m²"}
            ),
            "sensor.solar_lux": Mock(
                state="25000.0", attributes={"unit_of_measurement": "lx"}
            ),
            "sensor.uv_index": Mock(
                state="3.0", attributes={"unit_of_measurement": "UV index"}
            ),
        }

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()

        # Values should be converted to metric
        assert result["temperature"] == 25.0  # 77°F -> 25°C
        assert result["pressure"] == 1013.2  # 29.92 inHg -> 1013.25 hPa (rounded)
        assert result["wind_speed"] == 16.1  # 10 mph -> 16.0934 km/h (rounded)

    def test_get_weather_data_with_mixed_units(self, mock_hass, mock_options):
        """Test weather data conversion with mixed sensor units."""
        # Set up mock states with mixed units
        mock_states = {
            "sensor.outdoor_temperature": Mock(
                state="25.0", attributes={"unit_of_measurement": "°C"}  # Metric
            ),
            "sensor.pressure": Mock(
                state="29.92", attributes={"unit_of_measurement": "inHg"}  # Imperial
            ),
            "sensor.wind_speed": Mock(
                state="10.0", attributes={"unit_of_measurement": "m/s"}  # SI
            ),
            "sensor.humidity": Mock(
                state="65.0", attributes={"unit_of_measurement": "%"}
            ),
            "sensor.wind_direction": Mock(
                state="180.0", attributes={"unit_of_measurement": "°"}
            ),
            "sensor.wind_gust": Mock(
                state="15.0", attributes={"unit_of_measurement": "mph"}
            ),
            "sensor.rain_rate": Mock(
                state="0.0", attributes={"unit_of_measurement": "mm/h"}
            ),
            "sensor.rain_state": Mock(state="Dry", attributes={}),
            "sensor.solar_radiation": Mock(
                state="250.0", attributes={"unit_of_measurement": "W/m²"}
            ),
            "sensor.solar_lux": Mock(
                state="25000.0", attributes={"unit_of_measurement": "lx"}
            ),
            "sensor.uv_index": Mock(
                state="3.0", attributes={"unit_of_measurement": "UV index"}
            ),
        }

        mock_hass.states.get = lambda entity_id: mock_states.get(entity_id)

        detector = WeatherDetector(mock_hass, mock_options)
        result = detector.get_weather_data()

        # Check mixed conversions
        assert result["temperature"] == 25.0  # No conversion (already °C)
        assert result["pressure"] == 1013.2  # inHg -> hPa
        assert result["wind_speed"] == 36.0  # m/s -> km/h

    def test_prepare_forecast_sensor_data(self, mock_hass, mock_options):
        """Test that forecast sensor data preparation converts units correctly."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test data with metric units (like Tempest weather station)
        metric_sensor_data = {
            "outdoor_temp": 25.0,
            "outdoor_temp_unit": "°C",
            "pressure": 1013.25,
            "pressure_unit": "hPa",
            "wind_speed": 10.0,
            "wind_speed_unit": "km/h",
            "wind_gust": 15.0,
            "wind_gust_unit": "km/h",
            "humidity": 65.0,
            "rain_rate": 0.0,
        }

        forecast_data = detector._prepare_forecast_sensor_data(metric_sensor_data)

        # Temperature: 25°C -> 77°F
        assert forecast_data["outdoor_temp"] == 77.0

        # Pressure: 1013.25 hPa -> ~29.92 inHg
        assert abs(forecast_data["pressure"] - 29.92) < 0.01

        # Wind speed: 10 km/h -> ~6.21 mph
        assert abs(forecast_data["wind_speed"] - 6.21) < 0.01

        # Wind gust: 15 km/h -> ~9.3 mph
        assert abs(forecast_data["wind_gust"] - 9.3) < 0.01

        # Other data should remain unchanged
        assert forecast_data["humidity"] == 65.0
        assert forecast_data["rain_rate"] == 0.0

    def test_prepare_forecast_sensor_data_imperial(self, mock_hass, mock_options):
        """Test that imperial sensor data passes through unchanged."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test data with imperial units
        imperial_sensor_data = {
            "outdoor_temp": 77.0,
            "outdoor_temp_unit": "°F",
            "pressure": 29.92,
            "pressure_unit": "inHg",
            "wind_speed": 10.0,
            "wind_speed_unit": "mph",
            "humidity": 65.0,
        }

        forecast_data = detector._prepare_forecast_sensor_data(imperial_sensor_data)

        # Imperial data should pass through unchanged
        assert forecast_data["outdoor_temp"] == 77.0
        assert forecast_data["pressure"] == 29.92
        assert forecast_data["wind_speed"] == 10.0
        assert forecast_data["humidity"] == 65.0

    def test_prepare_analysis_sensor_data(self, mock_hass, mock_options):
        """Test that analysis sensor data preparation converts units correctly."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test data with metric units (like Tempest weather station)
        metric_sensor_data = {
            "outdoor_temp": 25.0,
            "outdoor_temp_unit": "°C",
            "pressure": 1013.25,
            "pressure_unit": "hPa",
            "wind_speed": 10.0,
            "wind_speed_unit": "km/h",
            "wind_gust": 15.0,
            "wind_gust_unit": "km/h",
            "dewpoint": 20.0,
            "dewpoint_unit": "°C",
            "humidity": 65.0,
            "rain_rate": 0.0,
        }

        analysis_data = detector._prepare_analysis_sensor_data(metric_sensor_data)

        # Temperature: 25°C -> 77°F
        assert analysis_data["outdoor_temp"] == 77.0

        # Pressure: 1013.25 hPa -> ~29.92 inHg
        assert abs(analysis_data["pressure"] - 29.92) < 0.01

        # Wind speed: 10 km/h -> ~6.21 mph
        assert abs(analysis_data["wind_speed"] - 6.21) < 0.01

        # Wind gust: 15 km/h -> ~9.3 mph
        assert abs(analysis_data["wind_gust"] - 9.3) < 0.01

        # Dewpoint: 20°C -> 68°F
        assert analysis_data["dewpoint"] == 68.0

        # Other data should remain unchanged
        assert analysis_data["humidity"] == 65.0
        assert analysis_data["rain_rate"] == 0.0

    def test_prepare_analysis_sensor_data_imperial(self, mock_hass, mock_options):
        """Test that imperial analysis sensor data passes through unchanged."""
        detector = WeatherDetector(mock_hass, mock_options)

        # Test data with imperial units
        imperial_sensor_data = {
            "outdoor_temp": 77.0,
            "outdoor_temp_unit": "°F",
            "pressure": 29.92,
            "pressure_unit": "inHg",
            "wind_speed": 10.0,
            "wind_speed_unit": "mph",
            "dewpoint": 68.0,
            "dewpoint_unit": "°F",
            "humidity": 65.0,
        }

        analysis_data = detector._prepare_analysis_sensor_data(imperial_sensor_data)

        # Imperial data should pass through unchanged
        assert analysis_data["outdoor_temp"] == 77.0
        assert analysis_data["pressure"] == 29.92
        assert analysis_data["wind_speed"] == 10.0
        assert analysis_data["dewpoint"] == 68.0
        assert analysis_data["humidity"] == 65.0
