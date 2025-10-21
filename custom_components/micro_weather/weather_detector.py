"""Weather condition detector using real sensor data.

This module implements advanced meteorological analysis to determine
accurate weather conditions based on real sensor readings. It analyzes:

- Precipitation patterns (rain rate, state detection)
- Atmospheric pressure systems and trends
- Solar radiation for cloud cover assessment
- Wind patterns for storm identification
- Temperature and humidity for fog detection
- Dewpoint analysis for precipitation potential

The detector uses scientific weather analysis principles to provide more
accurate local weather conditions than external weather services.

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
    CONF_ZENITH_MAX_RADIATION,
    DEFAULT_ZENITH_MAX_RADIATION,
    KEY_CONDITION,
    KEY_DEWPOINT,
    KEY_FORECAST,
    KEY_HUMIDITY,
    KEY_LAST_UPDATED,
    KEY_OUTDOOR_TEMP,
    KEY_PRECIPITATION,
    KEY_PRESSURE,
    KEY_PRESSURE_UNIT,
    KEY_RAIN_RATE,
    KEY_SOLAR_RADIATION,
    KEY_TEMPERATURE,
    KEY_TEMPERATURE_UNIT,
    KEY_VISIBILITY,
    KEY_WIND_DIRECTION,
    KEY_WIND_GUST,
    KEY_WIND_GUST_UNIT,
    KEY_WIND_SPEED,
    KEY_WIND_SPEED_UNIT,
)
from .weather_analysis import WeatherAnalysis
from .weather_forecast import AdvancedWeatherForecast
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

        # Historical data storage (last 48 hours, 15-minute intervals =
        # ~192 readings)
        self._history_maxlen = 192  # 48 hours * 4 readings per hour
        self._sensor_history: Dict[str, deque[Dict[str, Any]]] = {
            KEY_OUTDOOR_TEMP: deque(maxlen=self._history_maxlen),
            KEY_HUMIDITY: deque(maxlen=self._history_maxlen),
            KEY_PRESSURE: deque(maxlen=self._history_maxlen),
            KEY_WIND_SPEED: deque(maxlen=self._history_maxlen),
            KEY_WIND_DIRECTION: deque(maxlen=self._history_maxlen),
            KEY_SOLAR_RADIATION: deque(maxlen=self._history_maxlen),
            KEY_RAIN_RATE: deque(maxlen=self._history_maxlen),
        }
        self._condition_history: deque[Dict[str, Any]] = deque(
            maxlen=self._history_maxlen
        )

        # Initialize weather analysis and forecast modules with shared
        # sensor history
        zenith_max_radiation = options.get(
            CONF_ZENITH_MAX_RADIATION, DEFAULT_ZENITH_MAX_RADIATION
        )
        self.analysis = WeatherAnalysis(
            sensor_history=self._sensor_history,
            zenith_max_radiation=zenith_max_radiation,
        )
        self.forecast = AdvancedWeatherForecast(self.analysis)

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

        # Get altitude for forecast generation (converted to meters)
        altitude = convert_altitude_to_meters(
            self.options.get(CONF_ALTITUDE, 0.0),
            self.hass.config.units is US_CUSTOMARY_SYSTEM,
        )

        # Determine weather condition
        condition = self._determine_weather_condition(sensor_data)

        # Store the final condition in historical data
        self.analysis.store_historical_data(
            {}, condition  # Empty sensor data, just the condition
        )

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

        # Prepare forecast data
        try:
            forecast_data = self.forecast.generate_enhanced_forecast(
                condition, self._prepare_forecast_sensor_data(sensor_data), altitude
            )
        except Exception as e:
            _LOGGER.error("Forecast generation failed: %s", e)
            forecast_data = []

        # Get or calculate dewpoint
        dewpoint_value = sensor_data.get(KEY_DEWPOINT)
        if not dewpoint_value:
            # Calculate dewpoint as fallback using temperature and humidity
            temp_f = sensor_data.get(KEY_OUTDOOR_TEMP) or sensor_data.get(
                KEY_TEMPERATURE
            )
            humidity = sensor_data.get("humidity")
            if temp_f is not None and humidity is not None:
                dewpoint_value = self.analysis.calculate_dewpoint(temp_f, humidity)
                _LOGGER.debug(
                    "Dewpoint calculated: %.1f°F", dewpoint_value
                )  # Convert units and prepare data
        weather_data = {
            KEY_TEMPERATURE: self._convert_temperature(
                sensor_data.get(KEY_OUTDOOR_TEMP), sensor_data.get(KEY_TEMPERATURE_UNIT)
            ),
            KEY_HUMIDITY: sensor_data.get("humidity"),
            KEY_PRESSURE: self._convert_pressure(
                sensor_data.get("pressure"), sensor_data.get(KEY_PRESSURE_UNIT)
            ),
            KEY_WIND_SPEED: self._convert_wind_speed(
                sensor_data.get("wind_speed"), sensor_data.get(KEY_WIND_SPEED_UNIT)
            ),
            KEY_WIND_DIRECTION: sensor_data.get("wind_direction"),
            KEY_VISIBILITY: self.analysis.estimate_visibility(
                condition, self._prepare_analysis_sensor_data(sensor_data)
            ),
            KEY_PRECIPITATION: sensor_data.get(KEY_RAIN_RATE),
            KEY_DEWPOINT: self._convert_temperature(
                dewpoint_value, "F"
            ),  # Convert dewpoint from Fahrenheit to Celsius per HA standards
            KEY_CONDITION: condition,
            KEY_FORECAST: forecast_data,
            KEY_LAST_UPDATED: datetime.now().isoformat(),
        }

        # Set precipitation_unit based on rain_rate_unit, mapping rate units
        # to distance units
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
                # Additional validation: check if state is not None and not
                # empty
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
            # Don't set a default - let the analysis handle missing
            # solar elevation
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
        """Prepare sensor data for forecast module by converting to
        imperial units.

        The forecast module expects imperial units (Fahrenheit, mph, inHg)
        for its calculations, so we need to convert metric sensor data back
        to imperial.

        Args:
            sensor_data: Raw sensor data with units stored in {key}_unit fields

        Returns:
            dict: Sensor data converted to imperial units for forecast
                  compatibility
        """
        forecast_data = sensor_data.copy()

        # Convert temperature back to Fahrenheit if it was in Celsius
        temp_unit = sensor_data.get(KEY_TEMPERATURE_UNIT)
        if temp_unit in ["°C", "C", "celsius"]:
            temp_c = sensor_data.get(KEY_OUTDOOR_TEMP)
            if temp_c is not None:
                forecast_data[KEY_OUTDOOR_TEMP] = round(temp_c * 9 / 5 + 32, 1)

        # Convert wind speed back to mph if it was in km/h or m/s
        wind_unit = sensor_data.get(KEY_WIND_SPEED_UNIT)
        if wind_unit in ["km/h", "kmh", "kph"]:
            wind_kmh = sensor_data.get(KEY_WIND_SPEED)
            if wind_kmh is not None:
                forecast_data[KEY_WIND_SPEED] = round(wind_kmh / 1.60934, 1)
        elif wind_unit in ["m/s", "ms"]:
            wind_ms = sensor_data.get(KEY_WIND_SPEED)
            if wind_ms is not None:
                forecast_data[KEY_WIND_SPEED] = round(
                    wind_ms / 0.44704, 1
                )  # m/s to mph

        # Convert pressure back to inHg if it was in hPa
        pressure_unit = sensor_data.get(KEY_PRESSURE_UNIT)
        if pressure_unit in ["hPa", "mbar", "mb"]:
            pressure_hpa = sensor_data.get(KEY_PRESSURE)
            if pressure_hpa is not None:
                forecast_data[KEY_PRESSURE] = round(pressure_hpa / 33.8639, 2)

        # Wind gust also needs conversion if present
        gust_unit = sensor_data.get(KEY_WIND_GUST_UNIT)
        if gust_unit in ["km/h", "kmh", "kph"]:
            gust_kmh = sensor_data.get(KEY_WIND_GUST)
            if gust_kmh is not None:
                forecast_data[KEY_WIND_GUST] = round(gust_kmh / 1.60934, 1)
        elif gust_unit in ["m/s", "ms"]:
            gust_ms = sensor_data.get(KEY_WIND_GUST)
            if gust_ms is not None:
                forecast_data[KEY_WIND_GUST] = round(gust_ms / 0.44704, 1)

        return forecast_data

    def _prepare_analysis_sensor_data(
        self, sensor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare sensor data for analysis module by converting to
        imperial units.

        The analysis module expects imperial units (Fahrenheit, mph, inHg) for
        its calculations, so we need to convert metric sensor data to imperial.

        Args:
            sensor_data: Raw sensor data with units stored in {key}_unit fields

        Returns:
            dict: Sensor data converted to imperial units for analysis
                  compatibility
        """
        analysis_data = sensor_data.copy()

        # Convert temperature to Fahrenheit if it was in Celsius
        temp_unit = sensor_data.get(KEY_TEMPERATURE_UNIT)
        if temp_unit in ["°C", "C", "celsius"]:
            temp_c = sensor_data.get(KEY_OUTDOOR_TEMP)
            if temp_c is not None:
                analysis_data[KEY_OUTDOOR_TEMP] = round(temp_c * 9 / 5 + 32, 1)

        # Convert wind speed to mph if it was in km/h or m/s
        wind_unit = sensor_data.get(KEY_WIND_SPEED_UNIT)
        if wind_unit in ["km/h", "kmh", "kph"]:
            wind_kmh = sensor_data.get(KEY_WIND_SPEED)
            if wind_kmh is not None:
                analysis_data[KEY_WIND_SPEED] = round(wind_kmh / 1.60934, 1)
        elif wind_unit in ["m/s", "ms"]:
            wind_ms = sensor_data.get(KEY_WIND_SPEED)
            if wind_ms is not None:
                analysis_data[KEY_WIND_SPEED] = round(
                    wind_ms / 0.44704, 1
                )  # m/s to mph

        # Convert pressure to inHg if it was in hPa
        pressure_unit = sensor_data.get(KEY_PRESSURE_UNIT)
        if pressure_unit in ["hPa", "mbar", "mb"]:
            pressure_hpa = sensor_data.get(KEY_PRESSURE)
            if pressure_hpa is not None:
                analysis_data[KEY_PRESSURE] = round(pressure_hpa / 33.8639, 2)

        # Wind gust also needs conversion if present
        gust_unit = sensor_data.get(KEY_WIND_GUST_UNIT)
        if gust_unit in ["km/h", "kmh", "kph"]:
            gust_kmh = sensor_data.get(KEY_WIND_GUST)
            if gust_kmh is not None:
                analysis_data[KEY_WIND_GUST] = round(gust_kmh / 1.60934, 1)
        elif gust_unit in ["m/s", "ms"]:
            gust_ms = sensor_data.get(KEY_WIND_GUST)
            if gust_ms is not None:
                analysis_data[KEY_WIND_GUST] = round(gust_ms / 0.44704, 1)

        # Convert dewpoint to Fahrenheit if it was in Celsius
        dewpoint_unit = sensor_data.get("dewpoint_unit")
        if dewpoint_unit in ["°C", "C", "celsius"]:
            dewpoint_c = sensor_data.get(KEY_DEWPOINT)
            if dewpoint_c is not None:
                analysis_data[KEY_DEWPOINT] = round(dewpoint_c * 9 / 5 + 32, 1)

        return analysis_data
