"""Weather condition detector using real sensor data."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE

from .const import (
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_INDOOR_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_PRESSURE_SENSOR,
    CONF_WIND_SPEED_SENSOR,
    CONF_WIND_DIRECTION_SENSOR,
    CONF_WIND_GUST_SENSOR,
    CONF_RAIN_RATE_SENSOR,
    CONF_RAIN_STATE_SENSOR,
    CONF_SOLAR_RADIATION_SENSOR,
    CONF_SOLAR_LUX_SENSOR,
    CONF_UV_INDEX_SENSOR,
    WEATHER_PATTERNS,
)

_LOGGER = logging.getLogger(__name__)


class WeatherDetector:
    """Detect weather conditions from real sensor data."""

    def __init__(self, hass: HomeAssistant, options: Dict[str, Any]) -> None:
        """Initialize the weather detector."""
        self.hass = hass
        self.options = options
        self._last_condition = "partly_cloudy"
        self._condition_start_time = datetime.now()
        
        # Sensor entity IDs
        self.sensors = {
            "outdoor_temp": options.get(CONF_OUTDOOR_TEMP_SENSOR),
            "indoor_temp": options.get(CONF_INDOOR_TEMP_SENSOR),
            "humidity": options.get(CONF_HUMIDITY_SENSOR),
            "pressure": options.get(CONF_PRESSURE_SENSOR),
            "wind_speed": options.get(CONF_WIND_SPEED_SENSOR),
            "wind_direction": options.get(CONF_WIND_DIRECTION_SENSOR),
            "wind_gust": options.get(CONF_WIND_GUST_SENSOR),
            "rain_rate": options.get(CONF_RAIN_RATE_SENSOR),
            "rain_state": options.get(CONF_RAIN_STATE_SENSOR),
            "solar_radiation": options.get(CONF_SOLAR_RADIATION_SENSOR),
            "solar_lux": options.get(CONF_SOLAR_LUX_SENSOR),
            "uv_index": options.get(CONF_UV_INDEX_SENSOR),
        }

    def get_weather_data(self) -> Dict[str, Any]:
        """Get current weather data from sensors."""
        # Get sensor values
        sensor_data = self._get_sensor_values()
        
        # Determine weather condition
        condition = self._determine_weather_condition(sensor_data)
        
        # Convert units and prepare data
        weather_data = {
            "temperature": self._convert_to_celsius(sensor_data.get("outdoor_temp")),
            "humidity": sensor_data.get("humidity"),
            "pressure": self._convert_to_hpa(sensor_data.get("pressure")),
            "wind_speed": self._convert_to_kmh(sensor_data.get("wind_speed")),
            "wind_direction": sensor_data.get("wind_direction"),
            "visibility": self._estimate_visibility(condition, sensor_data),
            "condition": condition,
            "forecast": self._generate_simple_forecast(condition, sensor_data),
            "last_updated": datetime.now().isoformat(),
        }
        
        # Remove None values
        weather_data = {k: v for k, v in weather_data.items() if v is not None}
        
        return weather_data

    def _get_sensor_values(self) -> Dict[str, Any]:
        """Get current values from all configured sensors."""
        sensor_data = {}
        
        for sensor_key, entity_id in self.sensors.items():
            if not entity_id:
                continue
                
            state = self.hass.states.get(entity_id)
            if state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                try:
                    # Handle string sensors
                    if sensor_key == "rain_state":
                        sensor_data[sensor_key] = state.state.lower()
                    else:
                        sensor_data[sensor_key] = float(state.state)
                except (ValueError, TypeError):
                    _LOGGER.warning(f"Could not convert sensor {entity_id} value: {state.state}")
                    
        return sensor_data

    def _determine_weather_condition(self, sensor_data: Dict[str, Any]) -> str:
        """Determine weather condition based on sensor data."""
        
        # Get key sensor values
        rain_rate = sensor_data.get("rain_rate", 0)
        rain_state = sensor_data.get("rain_state", "dry")
        wind_speed = sensor_data.get("wind_speed", 0)
        wind_gust = sensor_data.get("wind_gust", 0)
        solar_radiation = sensor_data.get("solar_radiation", 0)
        solar_lux = sensor_data.get("solar_lux", 0)
        uv_index = sensor_data.get("uv_index", 0)
        outdoor_temp = sensor_data.get("outdoor_temp", 70)
        pressure = sensor_data.get("pressure", 29.92)
        
        # Determine if it's daytime based on solar radiation/lux
        is_daytime = solar_radiation > 0 or solar_lux > 0 or uv_index > 0
        
        # Convert pressure to trend (you might want to store historical data for better pressure trends)
        pressure_low = pressure < 29.80  # Low pressure indicates storms
        
        # Priority-based condition detection
        
        # 1. Rain conditions (highest priority)
        if rain_rate > 0.1 or rain_state.lower() != "dry":
            if wind_gust > 25 or pressure_low:
                return "stormy"  # Heavy rain with wind or low pressure
            elif outdoor_temp < 35:  # Below 35°F likely snow
                return "snowy"
            else:
                return "rainy"
        
        # 2. Wind-based conditions
        if wind_gust > 30 or (wind_speed > 20 and pressure_low):
            return "stormy"
        
        # 3. Solar radiation based conditions (if daytime)
        if is_daytime:
            # Daytime conditions
            if solar_radiation > 300:  # High solar radiation
                return "sunny"
            elif solar_radiation > 100:  # Moderate solar radiation  
                return "partly_cloudy"
            elif solar_radiation > 10:   # Low solar radiation
                return "cloudy"
            else:  # Very low solar radiation during day
                if solar_lux < 1000:  # Very low light
                    return "foggy"
                else:
                    return "cloudy"
        else:
            # Night time - use other indicators
            if uv_index > 0:  # Shouldn't have UV at night, but if clear might leak some
                return "clear-night"  # Will map to sunny in HA
            elif wind_speed < 5 and not pressure_low:
                return "cloudy"  # Calm night, assume cloudy
            else:
                return "partly_cloudy"
        
        # Default fallback
        return "partly_cloudy"

    def _estimate_visibility(self, condition: str, sensor_data: Dict[str, Any]) -> float:
        """Estimate visibility based on weather condition and sensor data."""
        solar_lux = sensor_data.get("solar_lux", 0)
        solar_radiation = sensor_data.get("solar_radiation", 0)
        uv_index = sensor_data.get("uv_index", 0)
        
        # Determine if it's daytime
        is_daytime = solar_radiation > 0 or solar_lux > 0 or uv_index > 0
        
        if condition == "foggy":
            return round(max(0.5, solar_lux / 10000), 1)  # Very low visibility in fog
        elif condition in ["rainy", "snowy"]:
            base_vis = 8.0 if condition == "rainy" else 5.0
            # Reduce visibility based on rain intensity or wind
            rain_rate = sensor_data.get("rain_rate", 0)
            return round(max(2.0, base_vis - (rain_rate * 2)), 1)
        elif condition == "stormy":
            return round(max(1.0, 5.0 - (sensor_data.get("wind_gust", 0) / 10)), 1)
        elif not is_daytime:
            return 15.0  # Night time visibility
        else:
            # Clear conditions - use solar data to estimate clarity
            if solar_lux > 50000:
                return 25.0  # Very clear
            elif solar_lux > 20000:
                return 20.0  # Clear
            else:
                return 15.0  # Somewhat hazy

    def _convert_to_celsius(self, temp_f: Optional[float]) -> Optional[float]:
        """Convert Fahrenheit to Celsius."""
        if temp_f is None:
            return None
        return round((temp_f - 32) * 5/9, 1)

    def _convert_to_hpa(self, pressure_inhg: Optional[float]) -> Optional[float]:
        """Convert inches of mercury to hPa."""
        if pressure_inhg is None:
            return None
        return round(pressure_inhg * 33.8639, 1)

    def _convert_to_kmh(self, speed_mph: Optional[float]) -> Optional[float]:
        """Convert miles per hour to kilometers per hour."""
        if speed_mph is None:
            return None
        return round(speed_mph * 1.60934, 1)

    def _generate_simple_forecast(self, current_condition: str, sensor_data: Dict[str, Any]) -> list:
        """Generate a simple 5-day forecast based on current conditions."""
        forecast = []
        current_temp = sensor_data.get("outdoor_temp", 70)
        
        # Simple forecast logic - you could enhance this with weather API or historical patterns
        for i in range(5):
            date = datetime.now() + timedelta(days=i + 1)
            
            # Simple temperature trend (you could make this more sophisticated)
            day_temp_variation = (-2, 2, -1, 1, 0)[i]  # Simple 5-day pattern
            forecast_temp = current_temp + day_temp_variation
            
            # Simple condition forecast (persistence with some variation)
            if i == 0:
                forecast_condition = current_condition
            elif i <= 2:
                # Next 2 days - slight chance of change
                forecast_condition = current_condition if i % 2 == 0 else "partly_cloudy"
            else:
                # Days 3-5 - more uncertainty
                forecast_condition = ["partly_cloudy", "cloudy", "sunny"][i % 3]
                
            forecast.append({
                "datetime": date.isoformat(),
                "temperature": round(self._convert_to_celsius(forecast_temp) or 20, 1),
                "templow": round((self._convert_to_celsius(forecast_temp) or 20) - 5, 1),
                "condition": forecast_condition,
                "precipitation": 0.0 if forecast_condition not in ["rainy", "snowy", "stormy"] else 2.0,
                "wind_speed": sensor_data.get("wind_speed", 5),
            })
        
        return forecast