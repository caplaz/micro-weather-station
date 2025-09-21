"""Weather condition detector using real sensor data.

This module implements advanced meteorological analysis algorithms to determine
accurate weather conditions based on real sensor readings. It analyzes:

- Precipitation patterns (rain rate, state detection)
- Atmospheric pressure systems and trends
- Solar radiation for cloud cover assessment
- Wind patterns for storm identification
- Temperature and humidity for fog detection
- Dewpoint analysis for precipitation potential

The detector uses scientific weather analysis principles to provide more accurate
local weather conditions than external weather services.

Classes:
    WeatherDetector: Main weather analysis engine

Author: caplaz
License: MIT
"""

from collections import deque
from datetime import datetime
import logging
from typing import Any, Dict, Mapping, Optional

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEWPOINT_SENSOR,
    CONF_HUMIDITY_SENSOR,
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
from .weather_analysis import WeatherAnalysis
from .weather_forecast import WeatherForecast

_LOGGER = logging.getLogger(__name__)


class WeatherDetector:
    """Detect weather conditions from real sensor data.

    This class analyzes real-time sensor data to determine accurate weather
    conditions using meteorological principles. It supports multiple sensor
    types and implements intelligent algorithms for:

    - Storm detection (precipitation + wind analysis)
    - Fog detection (humidity + dewpoint + solar radiation)
    - Cloud cover assessment (solar radiation patterns)
    - Snow detection (temperature-based precipitation type)
    - Weather forecasting (pressure trends)

    Attributes:
        hass: Home Assistant instance for accessing sensor states
        options: Configuration options with sensor entity mappings
        sensors: Dictionary mapping sensor types to entity IDs
    """

    def __init__(self, hass: HomeAssistant, options: Mapping[str, Any]) -> None:
        """Initialize the weather detector.

        Args:
            hass: Home Assistant instance for accessing entity states
            options: Configuration mapping sensor types to entity IDs
        """
        self.hass = hass
        self.options = options
        self._last_condition = "partly_cloudy"
        self._condition_start_time = datetime.now()

        # Historical data storage (last 48 hours, 15-minute intervals = ~192 readings)
        self._history_maxlen = 192  # 48 hours * 4 readings per hour
        self._sensor_history: Dict[str, deque[Dict[str, Any]]] = {
            "outdoor_temp": deque(maxlen=self._history_maxlen),
            "humidity": deque(maxlen=self._history_maxlen),
            "pressure": deque(maxlen=self._history_maxlen),
            "wind_speed": deque(maxlen=self._history_maxlen),
            "wind_direction": deque(maxlen=self._history_maxlen),
            "solar_radiation": deque(maxlen=self._history_maxlen),
            "rain_rate": deque(maxlen=self._history_maxlen),
        }
        self._condition_history: deque[Dict[str, Any]] = deque(
            maxlen=self._history_maxlen
        )

        # Initialize analysis and forecast modules
        self.analysis = WeatherAnalysis(self._sensor_history)
        self.forecast = WeatherForecast(self.analysis)

        # Sensor entity IDs mapping
        self.sensors = {
            "outdoor_temp": options.get(CONF_OUTDOOR_TEMP_SENSOR),
            "humidity": options.get(CONF_HUMIDITY_SENSOR),
            "dewpoint": options.get(CONF_DEWPOINT_SENSOR),
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
        """Get current weather data from sensors.

        Orchestrates the complete weather analysis process:
        1. Reads current sensor values
        2. Determines weather condition using meteorological algorithms
        3. Converts units to standard formats
        4. Generates forecast data

        Returns:
            dict: Complete weather data including:
                - temperature: Current temperature in Celsius
                - humidity: Relative humidity percentage
                - pressure: Atmospheric pressure in hPa
                - wind_speed: Wind speed in km/h
                - wind_direction: Wind direction in degrees
                - visibility: Estimated visibility in km
                - condition: Current weather condition string
                - forecast: Weather forecast data
                - last_updated: ISO timestamp of last update
        """
        # Get sensor values
        sensor_data = self._get_sensor_values()

        # Store historical data
        self.analysis.store_historical_data(sensor_data)

        # Determine weather condition
        condition = self._determine_weather_condition(sensor_data)

        # Store condition history
        self._condition_history.append(
            {"timestamp": datetime.now(), "condition": condition}
        )

        # Convert units and prepare data
        weather_data = {
            "temperature": self._convert_to_celsius(sensor_data.get("outdoor_temp")),
            "humidity": sensor_data.get("humidity"),
            "pressure": self._convert_to_hpa(sensor_data.get("pressure")),
            "wind_speed": self._convert_to_kmh(sensor_data.get("wind_speed")),
            "wind_direction": sensor_data.get("wind_direction"),
            "visibility": self.analysis.estimate_visibility(condition, sensor_data),
            "condition": condition,
            "forecast": self.forecast.generate_enhanced_forecast(
                condition, sensor_data
            ),
            "last_updated": datetime.now().isoformat(),
        }

        # Remove None values
        weather_data = {k: v for k, v in weather_data.items() if v is not None}

        return weather_data

    def _get_sensor_values(self) -> Dict[str, Any]:
        """Get current values from all configured sensors.

        Reads the current state of all configured sensor entities and converts
        them to appropriate data types. Handles errors gracefully by logging
        warnings for invalid sensor states.

        Returns:
            dict: Sensor data with keys matching sensor types and values as
                  floats (for numeric sensors) or strings (for state sensors)
        """
        sensor_data = {}

        for sensor_key, entity_id in self.sensors.items():
            if not entity_id:
                continue

            state = self.hass.states.get(entity_id)
            if state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                try:
                    # Handle string sensors (rain state detection)
                    if sensor_key == "rain_state":
                        sensor_data[sensor_key] = state.state.lower()
                    else:
                        sensor_data[sensor_key] = float(
                            state.state
                        )  # type: ignore[assignment]
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "Could not convert sensor {entity_id} value: {state.state}"
                    )

        return sensor_data

    def _determine_weather_condition(self, sensor_data: Dict[str, Any]) -> str:
        """
        Advanced meteorological weather condition detection.

        Uses scientific weather analysis principles:
        - Precipitation analysis (intensity, type, persistence)
        - Atmospheric pressure systems
        - Solar radiation for cloud cover assessment
        - Wind patterns for storm identification
        - Temperature/humidity for fog and frost conditions
        - Dewpoint analysis for precipitation potential
        """

        # Extract sensor values with better defaults
        rain_rate = sensor_data.get("rain_rate", 0.0)
        rain_state = sensor_data.get("rain_state", "dry").lower()
        wind_speed = sensor_data.get("wind_speed", 0.0)
        wind_gust = sensor_data.get("wind_gust", 0.0)
        solar_radiation = sensor_data.get("solar_radiation", 0.0)
        solar_lux = sensor_data.get("solar_lux", 0.0)
        uv_index = sensor_data.get("uv_index", 0.0)
        outdoor_temp = sensor_data.get("outdoor_temp", 70.0)
        humidity = sensor_data.get("humidity", 50.0)
        pressure = sensor_data.get("pressure", 29.92)

        # Calculate derived meteorological parameters
        # Use dewpoint sensor if available, otherwise calculate from temp/humidity
        dewpoint_raw = sensor_data.get("dewpoint")
        if dewpoint_raw is not None:
            dewpoint = float(dewpoint_raw)
        else:
            dewpoint = self.analysis.calculate_dewpoint(outdoor_temp, humidity)
        temp_dewpoint_spread = outdoor_temp - dewpoint
        is_freezing = outdoor_temp <= 32.0

        # Advanced daytime detection (solar elevation proxy)
        is_daytime = solar_radiation > 5 or solar_lux > 50 or uv_index > 0.1
        is_twilight = (solar_lux > 10 and solar_lux < 100) or (
            solar_radiation > 1 and solar_radiation < 50
        )

        # Pressure analysis (meteorologically accurate thresholds)
        pressure_very_high = pressure > 30.20  # High pressure system
        pressure_high = pressure > 30.00  # Above normal
        pressure_normal = 29.80 <= pressure <= 30.20  # Normal range
        pressure_low = pressure < 29.80  # Low pressure system
        pressure_very_low = pressure < 29.50  # Storm system
        pressure_extremely_low = pressure < 29.20  # Severe storm

        # Wind analysis (Beaufort scale adapted)
        wind_calm = wind_speed < 1  # 0-1 mph: Calm
        wind_light = 1 <= wind_speed < 8  # 1-7 mph: Light air to light breeze
        wind_strong = 19 <= wind_speed < 32  # 19-31 mph: Strong breeze to near gale
        wind_gale = wind_speed >= 32  # 32+ mph: Gale force

        gust_factor = wind_gust / max(wind_speed, 1)  # Gust ratio for turbulence
        is_gusty = gust_factor > 1.5 and wind_gust > 10
        is_very_gusty = gust_factor > 2.0 and wind_gust > 15

        _LOGGER.info(
            "Weather Analysis - Rain: %.2f in/h (%s), "
            "Wind: %.1f mph (gust: %.1f, ratio: %.1f), "
            "Pressure: %.2f inHg, Solar: %d W/m² (%d lx), "
            "Temp: %.1f°F, Humidity: %d%%, "
            "Dewpoint: %.1f°F (spread: %.1f°F)",
            rain_rate,
            rain_state,
            wind_speed,
            wind_gust,
            gust_factor,
            pressure,
            solar_radiation,
            solar_lux,
            outdoor_temp,
            humidity,
            dewpoint,
            temp_dewpoint_spread,
        )

        # PRIORITY 1: ACTIVE PRECIPITATION (Highest Priority)
        if rain_rate > 0.01 or rain_state in [
            "wet",
            "rain",
            "drizzle",
            "precipitation",
        ]:
            precipitation_intensity = self.analysis.classify_precipitation_intensity(
                rain_rate
            )

            # Determine precipitation type based on temperature
            if is_freezing:
                if rain_rate > 0.1:
                    return "snowy"  # Heavy snow
                else:
                    return "snowy"  # Light snow/flurries

            # Rain with storm conditions
            if (
                pressure_extremely_low
                or wind_gale
                or (pressure_very_low and wind_strong)
                or (is_very_gusty and wind_gust > 25)
            ):
                return "stormy"  # Thunderstorm/severe weather

            # Regular rain classification
            if precipitation_intensity == "heavy" or rain_rate > 0.25:
                return "rainy"  # Heavy rain
            elif precipitation_intensity == "moderate" or rain_rate > 0.1:
                return "rainy"  # Moderate rain
            else:
                return "rainy"  # Light rain/drizzle

        # PRIORITY 2: SEVERE WEATHER CONDITIONS
        # (No precipitation but extreme conditions)
        if pressure_extremely_low and (wind_strong or is_very_gusty):
            return "stormy"  # Severe weather system approaching

        if wind_gale:  # Gale force winds
            return "stormy"  # Windstorm

        # PRIORITY 3: FOG CONDITIONS (Critical for safety)
        fog_conditions = self.analysis.analyze_fog_conditions(
            outdoor_temp,
            humidity,
            dewpoint,
            temp_dewpoint_spread,
            wind_speed,
            solar_radiation,
            is_daytime,
        )
        if fog_conditions != "none":
            return fog_conditions

        # PRIORITY 4: DAYTIME CONDITIONS (Solar radiation analysis)
        if is_daytime:
            cloud_cover = self.analysis.analyze_cloud_cover(
                solar_radiation, solar_lux, uv_index
            )

            # Clear conditions
            if cloud_cover <= 10 and pressure_high:
                return "sunny"
            elif cloud_cover <= 25:
                return "sunny"
            elif cloud_cover <= 50:
                return "partly_cloudy"
            elif cloud_cover <= 75:
                return "cloudy"
            else:
                # Overcast with potential for development
                if pressure_low and humidity > 80:
                    return "cloudy"  # Threatening overcast
                else:
                    return "cloudy"

        # PRIORITY 5: TWILIGHT CONDITIONS
        elif is_twilight:
            if solar_lux > 50 and pressure_normal:
                return "partly_cloudy"
            else:
                return "cloudy"

        # PRIORITY 6: NIGHTTIME CONDITIONS
        else:
            # Night analysis based on atmospheric conditions
            if pressure_very_high and wind_calm and humidity < 70:
                return "clear-night"  # Perfect clear night
            elif pressure_high and not is_gusty and humidity < 80:
                return "clear-night"  # Clear night
            elif pressure_normal and wind_light:
                return "partly_cloudy"  # Partly cloudy night
            elif pressure_low or humidity > 85:
                return "cloudy"  # Cloudy/overcast night
            else:
                return "partly_cloudy"  # Default night condition

        # FALLBACK: Should rarely be reached
        return "partly_cloudy"

    def _classify_precipitation_intensity(self, rain_rate: float) -> str:
        """Classify precipitation intensity (meteorological standards)."""
        if rain_rate >= 0.5:
            return "heavy"  # Heavy rain
        elif rain_rate >= 0.1:
            return "moderate"  # Moderate rain
        elif rain_rate >= 0.01:
            return "light"  # Light rain/drizzle
        else:
            return "trace"  # Trace amounts

    def _analyze_cloud_cover(
        self, solar_radiation: float, solar_lux: float, uv_index: float
    ) -> float:
        """
        Estimate cloud cover percentage using solar radiation analysis.

        Based on theoretical clear-sky solar radiation models and
        actual measured values to determine cloud opacity.
        """

        # Rough clear-sky solar radiation estimates (varies by season/location)
        # These would ideally be calculated based on solar position
        max_solar_radiation = 1000  # W/m² theoretical maximum
        max_solar_lux = 100000  # lx theoretical maximum
        max_uv_index = 11  # UV Index maximum

        # Calculate cloud cover from each measurement
        solar_cloud_cover = max(
            0, min(100, 100 - (solar_radiation / max_solar_radiation * 100))
        )
        lux_cloud_cover = max(0, min(100, 100 - (solar_lux / max_solar_lux * 100)))
        uv_cloud_cover = max(0, min(100, 100 - (uv_index / max_uv_index * 100)))

        # Weight the measurements (solar radiation is most reliable for cloud cover)
        if solar_radiation > 0:
            cloud_cover = (
                solar_cloud_cover * 0.6 + lux_cloud_cover * 0.3 + uv_cloud_cover * 0.1
            )
        elif solar_lux > 0:
            cloud_cover = lux_cloud_cover * 0.8 + uv_cloud_cover * 0.2
        elif uv_index > 0:
            cloud_cover = uv_cloud_cover
        else:
            cloud_cover = 100  # No solar input = complete overcast or night

        return cloud_cover

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
