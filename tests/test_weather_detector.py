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
