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
    CONF_SUN_SENSOR,
    CONF_UV_INDEX_SENSOR,
    CONF_WIND_DIRECTION_SENSOR,
    CONF_WIND_GUST_SENSOR,
    CONF_WIND_SPEED_SENSOR,
)
from .weather_analysis import WeatherAnalysis
from .weather_forecast import WeatherForecast
from .weather_utils import convert_to_celsius, convert_to_hpa, convert_to_kmh

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
        self._previous_condition: str = (
            "partly_cloudy"  # Track previous condition for hysteresis
        )

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
            "sun": options.get(CONF_SUN_SENSOR),
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
        self.analysis.store_historical_data(
            self._prepare_analysis_sensor_data(sensor_data)
        )

        # Determine weather condition
        condition = self._determine_weather_condition(sensor_data)

        # Add hysteresis to prevent rapid oscillation between states
        # Only change condition if it's been stable for at least 2 updates
        # or is significantly different
        if len(self._condition_history) >= 2 and self._previous_condition != condition:
            # Count how many times we've seen this condition recently
            recent_conditions = [
                entry["condition"] for entry in list(self._condition_history)[-3:]
            ]
            condition_count = recent_conditions.count(condition)

            # Only change if this condition has been seen at least once recently
            # or if it's a major state change (e.g., clear to stormy)
            major_changes = [
                ("sunny", "stormy"),
                ("stormy", "sunny"),
                ("clear-night", "stormy"),
                ("stormy", "clear-night"),
                ("foggy", "stormy"),
                ("stormy", "foggy"),
            ]

            is_major_change = (self._previous_condition, condition) in major_changes

            if condition_count == 0 and not is_major_change:
                _LOGGER.debug(
                    "Preventing condition oscillation: keeping %s instead of %s",
                    self._previous_condition,
                    condition,
                )
                condition = self._previous_condition

        self._previous_condition = condition

        # Store condition history
        self._condition_history.append(
            {"timestamp": datetime.now(), "condition": condition}
        )

        # Convert units and prepare data
        weather_data = {
            "temperature": self._convert_temperature(
                sensor_data.get("outdoor_temp"), sensor_data.get("outdoor_temp_unit")
            ),
            "humidity": sensor_data.get("humidity"),
            "pressure": self._convert_pressure(
                sensor_data.get("pressure"), sensor_data.get("pressure_unit")
            ),
            "wind_speed": self._convert_wind_speed(
                sensor_data.get("wind_speed"), sensor_data.get("wind_speed_unit")
            ),
            "wind_direction": sensor_data.get("wind_direction"),
            "visibility": self.analysis.estimate_visibility(
                condition, self._prepare_analysis_sensor_data(sensor_data)
            ),
            "condition": condition,
            "forecast": self.forecast.generate_enhanced_forecast(
                condition, self._prepare_forecast_sensor_data(sensor_data)
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
        sensor_data: Dict[str, Any] = {}

        for sensor_key, entity_id in self.sensors.items():
            if not entity_id:
                continue

            # Skip sun sensor - it's handled separately below
            if sensor_key == "sun":
                continue

            state = self.hass.states.get(entity_id)
            if state and state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                # Additional validation: check if state is not None and not empty
                if state.state is None or state.state == "":
                    _LOGGER.warning(
                        "Sensor %s has empty or None state, skipping", entity_id
                    )
                    continue

                try:
                    # Handle string sensors (rain state detection)
                    if sensor_key == "rain_state":
                        sensor_data[sensor_key] = state.state.lower()
                    else:
                        sensor_data[sensor_key] = float(state.state)

                        # Store the unit of measurement for conversion logic
                        sensor_data[f"{sensor_key}_unit"] = state.attributes.get(
                            "unit_of_measurement"
                        )

                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "Could not convert sensor %s value: %s", entity_id, state.state
                    )

        # Get sun.sun sensor data for solar position calculations
        sun_entity_id = self.sensors.get("sun")
        if sun_entity_id:
            sun_state = self.hass.states.get(sun_entity_id)
            if sun_state and sun_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                # Additional validation for sun sensor
                if sun_state.state is None or sun_state.state == "":
                    _LOGGER.warning(
                        "Sun sensor %s has empty or None state, "
                        "using default elevation",
                        sun_entity_id,
                    )
                else:
                    try:
                        # Get solar elevation from sun.sun attributes
                        solar_elevation = float(
                            sun_state.attributes.get("elevation", 0)
                        )
                        sensor_data["solar_elevation"] = solar_elevation
                    except (ValueError, TypeError):
                        _LOGGER.warning(
                            "Could not get solar elevation from sun sensor %s",
                            sun_entity_id,
                        )
        else:
            # Fallback: use default elevation if no sun sensor configured
            sensor_data["solar_elevation"] = (
                45.0  # Reasonable default for moderate solar angle
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
        # Prepare sensor data in imperial units for analysis
        analysis_data = self._prepare_analysis_sensor_data(sensor_data)

        # Extract sensor values with better defaults
        rain_rate: float = analysis_data.get("rain_rate", 0.0)
        rain_state: str = analysis_data.get("rain_state", "dry").lower()
        wind_speed: float = analysis_data.get("wind_speed", 0.0)
        wind_gust: float = analysis_data.get("wind_gust", 0.0)
        solar_radiation: float = analysis_data.get("solar_radiation", 0.0)
        solar_lux: float = analysis_data.get("solar_lux", 0.0)
        uv_index: float = analysis_data.get("uv_index", 0.0)
        outdoor_temp: float = analysis_data.get("outdoor_temp", 70.0)
        humidity: float = analysis_data.get("humidity", 50.0)
        pressure: float = analysis_data.get("pressure", 29.92)

        # Calculate derived meteorological parameters
        # Use dewpoint sensor if available, otherwise calculate from temp/humidity
        dewpoint_raw = analysis_data.get("dewpoint")
        if dewpoint_raw is not None:
            dewpoint: float = float(dewpoint_raw)
        else:
            dewpoint = self.analysis.calculate_dewpoint(outdoor_temp, humidity)
        temp_dewpoint_spread: float = outdoor_temp - dewpoint
        is_freezing: bool = outdoor_temp <= 32.0

        # Advanced daytime detection (solar elevation proxy)
        is_daytime: bool = solar_radiation > 5 or solar_lux > 50 or uv_index > 0.1
        is_twilight: bool = (solar_lux > 10 and solar_lux < 100) or (
            solar_radiation > 1 and solar_radiation < 50
        )

        # Pressure analysis (meteorologically accurate thresholds)
        pressure_very_high: bool = pressure > 30.20  # High pressure system
        pressure_high: bool = pressure > 30.00  # Above normal
        pressure_normal: bool = 29.80 <= pressure <= 30.20  # Normal range
        pressure_low: bool = pressure < 29.80  # Low pressure system
        pressure_very_low: bool = pressure < 29.50  # Storm system
        pressure_extremely_low: bool = pressure < 29.20  # Severe storm

        # Wind analysis (Beaufort scale adapted)
        wind_calm: bool = wind_speed < 1  # 0-1 mph: Calm
        wind_light: bool = 1 <= wind_speed < 8  # 1-7 mph: Light air to light breeze
        wind_strong: bool = (
            19 <= wind_speed < 32
        )  # 19-31 mph: Strong breeze to near gale
        wind_gale: bool = wind_speed >= 32  # 32+ mph: Gale force

        gust_factor: float = wind_gust / max(wind_speed, 1)  # Gust ratio for turbulence
        is_gusty: bool = gust_factor > 1.5 and wind_gust > 10
        is_very_gusty: bool = gust_factor > 2.0 and wind_gust > 15

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
        # Use more conservative thresholds to avoid false positives from dew/moisture
        significant_rain: bool = (
            rain_rate > 0.05
        )  # Increased from 0.01 to avoid dew detection

        # If rain_state is "wet" but no significant rain_rate, check if
        # it might be fog first
        if rain_state == "wet" and not significant_rain:
            # Check for fog conditions before assuming precipitation
            fog_conditions: str = self.analysis.analyze_fog_conditions(
                outdoor_temp,
                humidity,
                dewpoint,
                temp_dewpoint_spread,
                wind_speed,
                solar_radiation,
                is_daytime,
            )
            if fog_conditions != "none":
                _LOGGER.info(
                    "Fog conditions detected with wet sensor: %s",
                    fog_conditions,
                )
                return fog_conditions

        # Now check for precipitation (either significant rain_rate OR wet
        # sensor without fog conditions)
        active_precipitation: bool = rain_state == "wet"
        # Consider "wet" as active precipitation when moisture sensor detects wetness
        # The moisture sensor (binary sensor) only reports "wet" or "dry"

        if significant_rain or active_precipitation:
            _LOGGER.info(
                "Precipitation detected: rain_rate=%.2f (>0.05), rain_state='%s'",
                rain_rate,
                rain_state,
            )
            precipitation_intensity: str = (
                self.analysis.classify_precipitation_intensity(rain_rate)
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
        # Check for fog in dry conditions (wet conditions already checked above)
        if rain_state != "wet":
            dry_fog_conditions: str = self.analysis.analyze_fog_conditions(
                outdoor_temp,
                humidity,
                dewpoint,
                temp_dewpoint_spread,
                wind_speed,
                solar_radiation,
                is_daytime,
            )
            if dry_fog_conditions != "none":
                _LOGGER.info("Fog conditions detected: %s", dry_fog_conditions)
                return dry_fog_conditions

        # PRIORITY 4: DAYTIME CONDITIONS (Solar radiation analysis)
        if is_daytime:
            solar_elevation: float = analysis_data.get(
                "solar_elevation", 45.0
            )  # Default to 45° if not available
            cloud_cover: float = self.analysis.analyze_cloud_cover(
                solar_radiation, solar_lux, uv_index, solar_elevation
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
            elif humidity > 85:
                return "cloudy"  # High humidity = likely cloudy/overcast night
            elif pressure_low and humidity > 75 and wind_speed < 3:
                return "cloudy"  # Low pressure + high humidity + calm = cloudy
            elif pressure_low and humidity < 65:
                return (
                    "clear-night"  # Low pressure but low humidity = can still be clear
                )
            elif pressure_low:
                return "partly_cloudy"  # Low pressure with moderate conditions
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

    def _convert_temperature(
        self, temp: Optional[float], unit: Optional[str]
    ) -> Optional[float]:
        """Convert temperature to Celsius if needed."""
        if temp is None:
            return None

        # If unit is Celsius or not specified, assume it's already in Celsius
        if unit in ["°C", "C", "celsius"]:
            return round(temp, 1)
        # If unit is Fahrenheit, convert to Celsius using utils function
        elif unit in ["°F", "F", "fahrenheit"]:
            return convert_to_celsius(temp)
        else:
            # Unknown unit, assume Celsius (most common for weather stations)
            _LOGGER.debug("Unknown temperature unit '%s', assuming Celsius", unit)
            return round(temp, 1)

    def _convert_pressure(
        self, pressure: Optional[float], unit: Optional[str]
    ) -> Optional[float]:
        """Convert pressure to hPa if needed."""
        if pressure is None:
            return None

        # If unit is hPa, mbar, or not specified, assume it's already in hPa
        if unit in ["hPa", "mbar", "mb"]:
            return round(pressure, 1)
        # If unit is inHg, convert to hPa using utils function
        elif unit in ["inHg", "inhg", '"Hg']:
            return convert_to_hpa(pressure)
        else:
            # Unknown unit, assume hPa (most common for weather stations)
            _LOGGER.debug("Unknown pressure unit '%s', assuming hPa", unit)
            return round(pressure, 1)

    def _convert_wind_speed(
        self, speed: Optional[float], unit: Optional[str]
    ) -> Optional[float]:
        """Convert wind speed to km/h if needed."""
        if speed is None:
            return None

        # If unit is km/h or not specified, assume it's already in km/h
        if unit in ["km/h", "kmh", "kph"]:
            return round(speed, 1)
        # If unit is mph, convert to km/h using utils function
        elif unit in ["mph", "mi/h"]:
            return convert_to_kmh(speed)
        # If unit is m/s, convert to km/h
        elif unit in ["m/s", "ms"]:
            return round(speed * 3.6, 1)
        else:
            # Unknown unit, assume km/h (most common for weather stations)
            _LOGGER.debug("Unknown wind speed unit '%s', assuming km/h", unit)
            return round(speed, 1)

    def _prepare_forecast_sensor_data(
        self, sensor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare sensor data for forecast module by converting to imperial units.

        The forecast module expects imperial units (Fahrenheit, mph, inHg) for its
        calculations, so we need to convert metric sensor data back to imperial.

        Args:
            sensor_data: Raw sensor data with units stored in {key}_unit fields

        Returns:
            dict: Sensor data converted to imperial units for forecast compatibility
        """
        forecast_data = sensor_data.copy()

        # Convert temperature back to Fahrenheit if it was in Celsius
        temp_unit = sensor_data.get("outdoor_temp_unit")
        if temp_unit in ["°C", "C", "celsius"]:
            temp_c = sensor_data.get("outdoor_temp")
            if temp_c is not None:
                forecast_data["outdoor_temp"] = round(temp_c * 9 / 5 + 32, 1)

        # Convert wind speed back to mph if it was in km/h or m/s
        wind_unit = sensor_data.get("wind_speed_unit")
        if wind_unit in ["km/h", "kmh", "kph"]:
            wind_kmh = sensor_data.get("wind_speed")
            if wind_kmh is not None:
                forecast_data["wind_speed"] = round(wind_kmh / 1.60934, 1)
        elif wind_unit in ["m/s", "ms"]:
            wind_ms = sensor_data.get("wind_speed")
            if wind_ms is not None:
                forecast_data["wind_speed"] = round(wind_ms / 0.44704, 1)  # m/s to mph

        # Convert pressure back to inHg if it was in hPa
        pressure_unit = sensor_data.get("pressure_unit")
        if pressure_unit in ["hPa", "mbar", "mb"]:
            pressure_hpa = sensor_data.get("pressure")
            if pressure_hpa is not None:
                forecast_data["pressure"] = round(pressure_hpa / 33.8639, 2)

        # Wind gust also needs conversion if present
        gust_unit = sensor_data.get("wind_gust_unit")
        if gust_unit in ["km/h", "kmh", "kph"]:
            gust_kmh = sensor_data.get("wind_gust")
            if gust_kmh is not None:
                forecast_data["wind_gust"] = round(gust_kmh / 1.60934, 1)
        elif gust_unit in ["m/s", "ms"]:
            gust_ms = sensor_data.get("wind_gust")
            if gust_ms is not None:
                forecast_data["wind_gust"] = round(gust_ms / 0.44704, 1)

        return forecast_data

    def _prepare_analysis_sensor_data(
        self, sensor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare sensor data for analysis module by converting to imperial units.

        The analysis module expects imperial units (Fahrenheit, mph, inHg) for its
        calculations, so we need to convert metric sensor data to imperial.

        Args:
            sensor_data: Raw sensor data with units stored in {key}_unit fields

        Returns:
            dict: Sensor data converted to imperial units for analysis compatibility
        """
        analysis_data = sensor_data.copy()

        # Convert temperature to Fahrenheit if it was in Celsius
        temp_unit = sensor_data.get("outdoor_temp_unit")
        if temp_unit in ["°C", "C", "celsius"]:
            temp_c = sensor_data.get("outdoor_temp")
            if temp_c is not None:
                analysis_data["outdoor_temp"] = round(temp_c * 9 / 5 + 32, 1)

        # Convert wind speed to mph if it was in km/h or m/s
        wind_unit = sensor_data.get("wind_speed_unit")
        if wind_unit in ["km/h", "kmh", "kph"]:
            wind_kmh = sensor_data.get("wind_speed")
            if wind_kmh is not None:
                analysis_data["wind_speed"] = round(wind_kmh / 1.60934, 1)
        elif wind_unit in ["m/s", "ms"]:
            wind_ms = sensor_data.get("wind_speed")
            if wind_ms is not None:
                analysis_data["wind_speed"] = round(wind_ms / 0.44704, 1)  # m/s to mph

        # Convert pressure to inHg if it was in hPa
        pressure_unit = sensor_data.get("pressure_unit")
        if pressure_unit in ["hPa", "mbar", "mb"]:
            pressure_hpa = sensor_data.get("pressure")
            if pressure_hpa is not None:
                analysis_data["pressure"] = round(pressure_hpa / 33.8639, 2)

        # Wind gust also needs conversion if present
        gust_unit = sensor_data.get("wind_gust_unit")
        if gust_unit in ["km/h", "kmh", "kph"]:
            gust_kmh = sensor_data.get("wind_gust")
            if gust_kmh is not None:
                analysis_data["wind_gust"] = round(gust_kmh / 1.60934, 1)
        elif gust_unit in ["m/s", "ms"]:
            gust_ms = sensor_data.get("wind_gust")
            if gust_ms is not None:
                analysis_data["wind_gust"] = round(gust_ms / 0.44704, 1)

        # Convert dewpoint to Fahrenheit if it was in Celsius
        dewpoint_unit = sensor_data.get("dewpoint_unit")
        if dewpoint_unit in ["°C", "C", "celsius"]:
            dewpoint_c = sensor_data.get("dewpoint")
            if dewpoint_c is not None:
                analysis_data["dewpoint"] = round(dewpoint_c * 9 / 5 + 32, 1)

        return analysis_data
