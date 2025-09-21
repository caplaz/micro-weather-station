"""Weather condition detector using real sensor data."""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Mapping, Optional

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

from .const import (
    CONF_HUMIDITY_SENSOR,
    CONF_INDOOR_TEMP_SENSOR,
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_PRESSURE_SENSOR,
    CONF_RAIN_RATE_SENSOR,
    CONF_RAIN_STATE_SENSOR,
    CONF_SOLAR_LUX_SENSOR,
    CONF_SOLAR_RADIATION_SENSOR,
    CONF_UV_INDEX_SENSOR,
    CONF_WIND_DIRECTION_SENSOR,
    CONF_WIND_GUST_SENSOR,
    CONF_WIND_SPEED_SENSOR,
)

_LOGGER = logging.getLogger(__name__)


class WeatherDetector:
    """Detect weather conditions from real sensor data."""

    def __init__(self, hass: HomeAssistant, options: Mapping[str, Any]) -> None:
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
                        sensor_data[sensor_key] = float(state.state)  # type: ignore[assignment]
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        f"Could not convert sensor {entity_id} value: {state.state}"
                    )

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
            elif solar_radiation > 10:  # Low solar radiation
                return "cloudy"
            else:  # Very low solar radiation during day
                if solar_lux < 1000:  # Very low light
                    return "foggy"
                else:
                    return "cloudy"
        else:
            # Night time - use other indicators
            if wind_speed < 3 and pressure >= 29.80 and solar_lux == 0:
                return "clear-night"  # Clear night sky
            elif wind_speed < 5 and not pressure_low:
                return "cloudy"  # Calm night, assume cloudy
            else:
                return "partly_cloudy"

        # Default fallback
        return "partly_cloudy"

    def _estimate_visibility(
        self, condition: str, sensor_data: Dict[str, Any]
    ) -> float:
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
        return round((temp_f - 32) * 5 / 9, 1)

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

    def _generate_simple_forecast(
        self, current_condition: str, sensor_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate an intelligent 5-day forecast based on current sensor data and patterns."""
        forecast = []
        current_temp = sensor_data.get("outdoor_temp", 70)
        current_pressure = sensor_data.get("pressure", 29.92)
        current_humidity = sensor_data.get("humidity", 50)
        current_wind_speed = sensor_data.get("wind_speed", 5)

        # Pressure trend analysis for weather prediction
        pressure_hpa = self._convert_to_hpa(current_pressure) or 1013
        is_high_pressure = pressure_hpa > 1020
        is_low_pressure = pressure_hpa < 1000

        for i in range(5):
            date = datetime.now() + timedelta(days=i + 1)

            # Enhanced temperature forecast with seasonal and pressure influence
            day_temp_variation = self._calculate_temp_trend(
                i, current_temp, pressure_hpa
            )
            forecast_temp = current_temp + day_temp_variation

            # Enhanced condition forecast based on pressure trends and patterns
            forecast_condition = self._predict_condition(
                i, current_condition, pressure_hpa, current_humidity, current_wind_speed
            )

            # Calculate precipitation probability
            precipitation = self._calculate_precipitation(
                forecast_condition, pressure_hpa, current_humidity
            )

            # Wind speed forecast
            wind_forecast = self._forecast_wind_speed(
                current_wind_speed, forecast_condition, i
            )

            forecast.append(
                {
                    "datetime": date.isoformat(),
                    "temperature": round(
                        self._convert_to_celsius(forecast_temp) or 20, 1
                    ),
                    "templow": round(
                        (self._convert_to_celsius(forecast_temp) or 20) - 6, 1
                    ),
                    "condition": forecast_condition,
                    "precipitation": precipitation,
                    "wind_speed": wind_forecast,
                    "humidity": max(
                        30, min(90, current_humidity + (i * 2))
                    ),  # Simple humidity trend
                }
            )

        return forecast

    def _calculate_temp_trend(
        self, day: int, current_temp: float, pressure_hpa: float
    ) -> float:
        """Calculate temperature trend based on pressure and time."""
        # Base seasonal variation (simplified)
        seasonal_variation = [0, -1, 1, -2, 1][day]

        # Pressure influence on temperature
        if pressure_hpa > 1020:  # High pressure - generally stable/clear
            pressure_effect = 1 + (day * 0.5)  # Slight warming trend
        elif pressure_hpa < 1000:  # Low pressure - storm systems
            pressure_effect = -2 - (day * 0.3)  # Cooling trend
        else:
            pressure_effect = 0

        return seasonal_variation + pressure_effect

    def _predict_condition(
        self,
        day: int,
        current_condition: str,
        pressure_hpa: float,
        humidity: float,
        wind_speed: float,
    ) -> str:
        """Predict weather condition based on atmospheric patterns."""

        # Day 0-1: Current conditions persist with pressure influence
        if day <= 1:
            if pressure_hpa > 1025:  # Very high pressure
                return "sunny" if day == 0 else "partly_cloudy"
            elif pressure_hpa < 995:  # Very low pressure
                return "stormy" if wind_speed > 15 else "rainy"
            else:
                return current_condition

        # Day 2-3: Transition based on pressure trends
        elif day <= 3:
            if pressure_hpa > 1020:
                return ["sunny", "partly_cloudy"][day % 2]
            elif pressure_hpa < 1000:
                return ["rainy", "cloudy", "partly_cloudy"][day % 3]
            else:
                return ["partly_cloudy", "cloudy"][day % 2]

        # Day 4-5: Longer term patterns (return to average conditions)
        else:
            if humidity > 80:
                return "cloudy"
            elif humidity < 40:
                return "sunny"
            else:
                return "partly_cloudy"

    def _calculate_precipitation(
        self, condition: str, pressure_hpa: float, humidity: float
    ) -> float:
        """Calculate precipitation probability based on conditions."""
        if condition in ["rainy", "stormy"]:
            base_precip = 5.0 if condition == "rainy" else 10.0
            # High humidity and low pressure increase precipitation
            humidity_factor = max(1.0, humidity / 60)
            pressure_factor = max(1.0, (1020 - pressure_hpa) / 20)
            return round(base_precip * humidity_factor * pressure_factor, 1)
        elif condition == "snowy":
            return 3.0
        elif condition == "cloudy" and humidity > 75:
            return 1.0  # Light chance of rain
        else:
            return 0.0

    def _forecast_wind_speed(
        self, current_wind: float, condition: str, day: int
    ) -> float:
        """Forecast wind speed based on conditions."""
        base_wind = current_wind

        if condition == "stormy":
            return round(base_wind * 1.5 + day, 1)
        elif condition in ["rainy", "cloudy"]:
            return round(base_wind * 1.1 + (day * 0.5), 1)
        elif condition == "sunny":
            return round(max(2.0, base_wind * 0.8), 1)
        else:
            return round(base_wind + (day * 0.2), 1)
