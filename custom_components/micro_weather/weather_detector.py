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
import json
import logging
from typing import Any, Dict, Mapping, Optional

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
)
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from .const import (
    CONF_ALTITUDE,
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
from .weather_utils import (
    convert_altitude_to_meters,
    convert_to_celsius,
    convert_to_hpa,
    convert_to_kmh,
)

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

        # Initialize weather analysis and forecast modules with shared sensor history
        self.analysis = WeatherAnalysis(sensor_history=self._sensor_history)
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

        # Get altitude for forecast generation (converted to meters)
        altitude = convert_altitude_to_meters(
            self.options.get(CONF_ALTITUDE, 0.0),
            self.hass.config.units is US_CUSTOMARY_SYSTEM,
        )

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
                # Thunderstorm transitions (LIGHTNING_RAINY)
                (ATTR_CONDITION_SUNNY, ATTR_CONDITION_LIGHTNING_RAINY),
                (ATTR_CONDITION_LIGHTNING_RAINY, ATTR_CONDITION_SUNNY),
                (ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_LIGHTNING_RAINY),
                (ATTR_CONDITION_LIGHTNING_RAINY, ATTR_CONDITION_CLEAR_NIGHT),
                (ATTR_CONDITION_FOG, ATTR_CONDITION_LIGHTNING_RAINY),
                (ATTR_CONDITION_LIGHTNING_RAINY, ATTR_CONDITION_FOG),
                # Heavy rain transitions (POURING)
                (ATTR_CONDITION_SUNNY, ATTR_CONDITION_POURING),
                (ATTR_CONDITION_POURING, ATTR_CONDITION_SUNNY),
                (ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_POURING),
                (ATTR_CONDITION_POURING, ATTR_CONDITION_CLEAR_NIGHT),
                (ATTR_CONDITION_FOG, ATTR_CONDITION_POURING),
                (ATTR_CONDITION_POURING, ATTR_CONDITION_FOG),
                # Snow transitions (SNOWY)
                (ATTR_CONDITION_SUNNY, ATTR_CONDITION_SNOWY),
                (ATTR_CONDITION_SNOWY, ATTR_CONDITION_SUNNY),
                (ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_SNOWY),
                (ATTR_CONDITION_SNOWY, ATTR_CONDITION_CLEAR_NIGHT),
                (ATTR_CONDITION_FOG, ATTR_CONDITION_SNOWY),
                (ATTR_CONDITION_SNOWY, ATTR_CONDITION_FOG),
                # Lightning transitions (LIGHTNING)
                (ATTR_CONDITION_SUNNY, ATTR_CONDITION_LIGHTNING),
                (ATTR_CONDITION_LIGHTNING, ATTR_CONDITION_SUNNY),
                (ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_LIGHTNING),
                (ATTR_CONDITION_LIGHTNING, ATTR_CONDITION_CLEAR_NIGHT),
                (ATTR_CONDITION_FOG, ATTR_CONDITION_LIGHTNING),
                (ATTR_CONDITION_LIGHTNING, ATTR_CONDITION_FOG),
                # Windy transitions (WINDY)
                (ATTR_CONDITION_SUNNY, ATTR_CONDITION_WINDY),
                (ATTR_CONDITION_WINDY, ATTR_CONDITION_SUNNY),
                (ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_WINDY),
                (ATTR_CONDITION_WINDY, ATTR_CONDITION_CLEAR_NIGHT),
                (ATTR_CONDITION_FOG, ATTR_CONDITION_WINDY),
                (ATTR_CONDITION_WINDY, ATTR_CONDITION_FOG),
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

        # Log sensor data and determined weather condition
        try:
            # Add altitude to sensor data for logging purposes
            log_data = sensor_data.copy()
            log_data["altitude_m"] = altitude
            sensor_data_json = json.dumps(log_data)
        except (TypeError, ValueError):
            sensor_data_json = str(sensor_data)

        _LOGGER.debug(
            "Weather update - sensor data: %s, condition: %s",
            sensor_data_json,
            condition,
        )

        # Store condition history
        self._condition_history.append(
            {"timestamp": datetime.now(), "condition": condition}
        )

        # Prepare forecast data
        try:
            forecast_data = self.forecast.generate_enhanced_forecast(
                condition, self._prepare_forecast_sensor_data(sensor_data), altitude
            )
        except Exception as e:
            _LOGGER.error("Forecast generation failed: %s", e)
            forecast_data = []

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
            "precipitation": sensor_data.get("rain_rate"),
            "condition": condition,
            "forecast": forecast_data,
            "last_updated": datetime.now().isoformat(),
        }

        # Set precipitation_unit based on rain_rate_unit, mapping rate units to distance units
        rain_rate_unit = sensor_data.get("rain_rate_unit")
        if rain_rate_unit:
            rain_rate_unit_lower = rain_rate_unit.lower()
            if rain_rate_unit_lower in ["mm/h", "mm/hr", "mmh"]:
                weather_data["precipitation_unit"] = "mm"
            elif rain_rate_unit_lower in ["in/h", "inch/h", "inh", "inches/h"]:
                weather_data["precipitation_unit"] = "in"
            # Add more mappings if needed for other rate units

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
            # Don't set a default - let the analysis handle missing solar elevation
            pass

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
        # Get altitude from configuration options (converted to meters)
        altitude = float(
            convert_altitude_to_meters(
                self.options.get(CONF_ALTITUDE, 0.0),
                self.hass.config.units is US_CUSTOMARY_SYSTEM,
            )
            or 0.0
        )  # Ensure altitude is always a float

        # Prepare sensor data in imperial units for analysis
        analysis_data = self._prepare_analysis_sensor_data(sensor_data)

        # Use the weather analysis module for condition determination
        return self.analysis.determine_weather_condition(analysis_data, altitude)

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
