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
from datetime import datetime, timedelta
import logging
import math
import statistics
from typing import Any, Dict, List, Mapping, Optional

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
        self._sensor_history: Dict[str, deque] = {
            "outdoor_temp": deque(maxlen=self._history_maxlen),
            "humidity": deque(maxlen=self._history_maxlen),
            "pressure": deque(maxlen=self._history_maxlen),
            "wind_speed": deque(maxlen=self._history_maxlen),
            "solar_radiation": deque(maxlen=self._history_maxlen),
            "rain_rate": deque(maxlen=self._history_maxlen),
        }
        self._condition_history = deque(maxlen=self._history_maxlen)

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
        self._store_historical_data(sensor_data)

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
            "visibility": self._estimate_visibility(condition, sensor_data),
            "condition": condition,
            "forecast": self._generate_enhanced_forecast(condition, sensor_data),
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
            dewpoint = self._calculate_dewpoint(outdoor_temp, humidity)
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
            precipitation_intensity = self._classify_precipitation_intensity(rain_rate)

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
        fog_conditions = self._analyze_fog_conditions(
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
            cloud_cover = self._analyze_cloud_cover(
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

    def _calculate_dewpoint(self, temp_f: float, humidity: float) -> float:
        """Calculate dewpoint using Magnus formula (meteorologically accurate).

        The dewpoint is the temperature at which air becomes saturated with
        water vapor. This implementation uses the Magnus-Tetens formula,
        which is accurate for typical atmospheric conditions.

        Args:
            temp_f: Temperature in Fahrenheit
            humidity: Relative humidity as percentage (0-100)

        Returns:
            float: Dewpoint temperature in Fahrenheit

        Note:
            Falls back to approximation for very dry conditions (humidity <= 0)
        """
        if humidity <= 0:
            return temp_f - 50  # Approximate for very dry conditions

        # Convert to Celsius for calculation
        temp_c = (temp_f - 32) * 5 / 9

        # Magnus formula constants (Tetens 1930, Murray 1967)
        a = 17.27
        b = 237.7

        # Calculate dewpoint in Celsius using Magnus-Tetens approximation
        gamma = (a * temp_c) / (b + temp_c) + math.log(humidity / 100.0)
        dewpoint_c = (b * gamma) / (a - gamma)

        # Convert back to Fahrenheit
        return dewpoint_c * 9 / 5 + 32

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

    def _analyze_fog_conditions(
        self,
        temp: float,
        humidity: float,
        dewpoint: float,
        spread: float,
        wind_speed: float,
        solar_rad: float,
        is_daytime: bool,
    ) -> str:
        """Advanced fog analysis using meteorological principles.

        Analyzes atmospheric conditions to determine fog likelihood using
        scientific criteria for fog formation. The algorithm considers:

        - Humidity levels (fog requires near-saturation)
        - Temperature-dewpoint spread (closer = higher fog probability)
        - Wind speed (light winds favor fog formation)
        - Solar radiation (low radiation indicates existing fog)
        - Time of day (radiation fog typically forms at night/early morning)

        Fog Types Detected:
        - Dense fog: Extremely high humidity (99%+) with minimal spread
        - Radiation fog: High humidity (98%+) with light winds at night
        - Advection fog: Moist air moving over cooler surface

        Args:
            temp: Current temperature in Fahrenheit
            humidity: Relative humidity percentage
            dewpoint: Dewpoint temperature in Fahrenheit
            spread: Temperature minus dewpoint in Fahrenheit
            wind_speed: Wind speed in mph
            solar_rad: Solar radiation in W/m²
            is_daytime: Boolean indicating if it's currently daytime

        Returns:
            str: "foggy" if fog conditions are met, "clear" otherwise

        Note:
            Uses conservative thresholds to reduce false positives after
            user feedback about incorrect fog detection.
        """

        # Dense fog conditions
        # (very restrictive - must be extremely close to saturation)
        if humidity >= 99 and spread <= 1 and wind_speed <= 2:
            return "foggy"

        # Radiation fog (more restrictive than before to reduce false positives)
        if (
            humidity >= 98  # Raised from 95 to 98 - requires near saturation
            and spread <= 2  # Reduced from 3 to 2 - closer to dewpoint required
            and wind_speed <= 3  # Reduced from 5 to 3 - lighter winds required
            and (not is_daytime or solar_rad < 5)  # More restrictive solar condition
        ):
            return "foggy"

        # Advection fog (moist air over cooler surface) - kept similar
        if (
            humidity >= 95 and spread <= 3 and 3 <= wind_speed <= 12
        ):  # Raised humidity threshold
            return "foggy"

        # Evaporation fog (after rain, warm ground) - more restrictive
        if (
            humidity >= 95 and spread <= 3 and wind_speed <= 6 and temp > 40
        ):  # Raised thresholds
            # Check if conditions suggest recent precipitation
            return "foggy"

        return "none"

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

    def _estimate_visibility(
        self, condition: str, sensor_data: Dict[str, Any]
    ) -> float:
        """
        Estimate visibility based on weather condition and meteorological data.

        Uses scientific visibility reduction factors:
        - Fog: Major visibility reduction (0.1-2 km)
        - Rain: Moderate reduction based on intensity
        - Snow: Severe reduction, especially with wind
        - Storms: Variable based on precipitation and wind
        - Clear: Excellent visibility based on atmospheric clarity
        """
        solar_lux = sensor_data.get("solar_lux", 0)
        solar_radiation = sensor_data.get("solar_radiation", 0)
        rain_rate = sensor_data.get("rain_rate", 0)
        wind_speed = sensor_data.get("wind_speed", 0)
        wind_gust = sensor_data.get("wind_gust", 0)
        humidity = sensor_data.get("humidity", 50)
        outdoor_temp = sensor_data.get("outdoor_temp", 70)

        # Calculate dewpoint for more accurate fog assessment
        dewpoint = self._calculate_dewpoint(outdoor_temp, humidity)
        temp_dewpoint_spread = outdoor_temp - dewpoint

        is_daytime = solar_radiation > 5 or solar_lux > 50

        if condition == "foggy":
            # Fog visibility based on density (dewpoint spread)
            if temp_dewpoint_spread <= 1:
                return 0.3  # Dense fog: <0.5 km
            elif temp_dewpoint_spread <= 2:
                return 0.8  # Thick fog: <1 km
            elif temp_dewpoint_spread <= 3:
                return 1.5  # Moderate fog: 1-2 km
            else:
                return 2.5  # Light fog/mist: 2-3 km

        elif condition in ["rainy", "snowy"]:
            # Precipitation visibility reduction
            base_visibility = 15.0 if condition == "rainy" else 8.0

            # Intensity-based reduction
            if rain_rate > 0.5:  # Heavy precipitation
                intensity_factor = 0.3
            elif rain_rate > 0.25:  # Moderate precipitation
                intensity_factor = 0.5
            elif rain_rate > 0.1:  # Light precipitation
                intensity_factor = 0.7
            else:  # Very light/drizzle
                intensity_factor = 0.85

            # Wind effect (blowing precipitation reduces visibility)
            wind_factor = max(0.6, 1.0 - (wind_speed / 50))

            visibility = base_visibility * intensity_factor * wind_factor
            return round(max(0.5, visibility), 1)

        elif condition == "stormy":
            # Storm visibility varies greatly
            if rain_rate > 0.1:  # Rain with storm
                storm_vis = 3.0 - (rain_rate * 2)
            else:  # Dry storm (dust, debris)
                storm_vis = 8.0 - (wind_gust / 10)
            return round(max(0.8, storm_vis), 1)

        elif condition == "clear-night":
            # Excellent night visibility
            if humidity < 50:
                return 25.0  # Very clear, dry air
            elif humidity < 70:
                return 20.0  # Clear
            else:
                return 15.0  # Slight haze

        elif condition == "sunny":
            # Daytime clear conditions
            if solar_radiation > 800:  # Very clear atmosphere
                return 30.0
            elif solar_radiation > 600:  # Clear
                return 25.0
            elif solar_radiation > 400:  # Good
                return 20.0
            else:  # Hazy
                return 15.0

        elif condition in ["partly_cloudy", "cloudy"]:
            # Cloud-based visibility
            if is_daytime:
                # Use solar data to estimate atmospheric clarity
                if solar_lux > 50000:
                    return 25.0  # High clouds, clear air
                elif solar_lux > 20000:
                    return 20.0  # Some haze
                elif solar_lux > 5000:
                    return 15.0  # Moderate haze
                else:
                    return 12.0  # Overcast, some haze
            else:
                # Night visibility with clouds
                if humidity < 75:
                    return 18.0  # Clear air
                elif humidity < 85:
                    return 15.0  # Slight haze
                else:
                    return 12.0  # More humid, reduced visibility

        # Default visibility
        return 15.0

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

    def _generate_enhanced_forecast(
        self, current_condition: str, sensor_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate an intelligent 5-day forecast using historical trends and patterns.

        Uses historical data, trend analysis, and meteorological patterns to create
        more accurate forecasts than simple rule-based approaches.
        """
        forecast = []

        # Get comprehensive trend analysis
        pressure_analysis = self._analyze_pressure_trends()
        temp_patterns = self._analyze_temperature_patterns()
        humidity_trend = self._get_historical_trends("humidity", hours=24)
        wind_trend = self._get_historical_trends("wind_speed", hours=24)

        # Current baseline values
        current_temp = sensor_data.get("outdoor_temp", 70)
        current_humidity = sensor_data.get("humidity", 50)
        current_wind = sensor_data.get("wind_speed", 5)

        for i in range(5):
            date = datetime.now() + timedelta(days=i + 1)

            # Enhanced temperature forecasting using patterns and trends
            forecast_temp = self._forecast_temperature_enhanced(
                i, current_temp, temp_patterns, pressure_analysis
            )

            # Enhanced condition forecasting using multiple data sources
            forecast_condition = self._forecast_condition_enhanced(
                i, current_condition, pressure_analysis, sensor_data
            )

            # Enhanced precipitation forecasting
            precipitation = self._forecast_precipitation_enhanced(
                i, forecast_condition, pressure_analysis, humidity_trend
            )

            # Enhanced wind forecasting
            wind_forecast = self._forecast_wind_enhanced(
                i, current_wind, forecast_condition, wind_trend, pressure_analysis
            )

            # Calculate humidity forecast
            humidity_forecast = self._forecast_humidity(
                i, current_humidity, humidity_trend, forecast_condition
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
                    "humidity": humidity_forecast,
                }
            )

        return forecast

    def _forecast_temperature_enhanced(
        self,
        day: int,
        current_temp: float,
        temp_patterns: Dict[str, Any],
        pressure_analysis: Dict[str, Any],
    ) -> float:
        """Enhanced temperature forecasting using historical patterns
        and pressure systems.

        Args:
            day: Day ahead to forecast (0-4)
            current_temp: Current temperature in Fahrenheit
            temp_patterns: Temperature pattern analysis
            pressure_analysis: Pressure trend analysis

        Returns:
            float: Forecasted temperature in Fahrenheit
        """
        # Base temperature from current reading
        forecast_temp = current_temp

        # Apply diurnal and seasonal patterns
        seasonal_adjustment = self._calculate_seasonal_temperature_adjustment(day)
        forecast_temp += seasonal_adjustment

        # Apply pressure system influence
        pressure_system = pressure_analysis.get("pressure_system", "normal")
        if pressure_system == "high_pressure":
            # High pressure systems are generally warmer and more stable
            pressure_adjustment = 2 - (day * 0.3)  # Warming effect diminishes over time
        elif pressure_system == "low_pressure":
            # Low pressure systems are generally cooler
            pressure_adjustment = -3 + (day * 0.5)  # Cooling effect lessens over time
        else:
            pressure_adjustment = 0

        forecast_temp += pressure_adjustment

        # Apply historical trend influence
        # (dampened for longer forecasts)
        trend_influence = temp_patterns.get("trend", 0) * (
            24 - day * 4
        )  # Less influence for distant days
        forecast_temp += min(max(trend_influence, -5), 5)  # Cap the trend influence

        return forecast_temp

    def _calculate_seasonal_temperature_adjustment(self, day: int) -> float:
        """Calculate seasonal temperature variation for forecasting."""
        # Simplified seasonal patterns (would be enhanced with actual seasonal data)
        # This is a basic implementation - could be enhanced with
        # astronomical calculations
        base_variation = [0, -1, 1, -0.5, 0.5][day]  # Day-to-day variation

        # Add some randomness based on typical weather patterns
        # In reality, this would use historical seasonal data
        return base_variation

    def _forecast_condition_enhanced(
        self,
        day: int,
        current_condition: str,
        pressure_analysis: Dict[str, Any],
        sensor_data: Dict[str, Any],
    ) -> str:
        """Enhanced condition forecasting using pressure trends and historical patterns.

        Args:
            day: Day ahead to forecast (0-4)
            current_condition: Current weather condition
            pressure_analysis: Pressure trend analysis
            sensor_data: Current sensor data

        Returns:
            str: Forecasted weather condition
        """
        pressure_system = pressure_analysis.get("pressure_system", "normal")
        storm_probability = pressure_analysis.get("storm_probability", 0)

        # High confidence predictions for near-term
        if day == 0:
            if storm_probability > 60:
                return "stormy"
            elif storm_probability > 30:
                return "rainy"
            elif pressure_system == "high_pressure":
                return "sunny"
            else:
                return current_condition

        # Medium-term predictions (1-2 days)
        elif day <= 2:
            if storm_probability > 40:
                return "rainy" if storm_probability < 70 else "stormy"
            elif pressure_system == "high_pressure":
                return "partly_cloudy" if day == 1 else "sunny"
            elif pressure_system == "low_pressure":
                return "cloudy" if day == 1 else "rainy"
            else:
                # Default to improving conditions
                condition_progression = {
                    "stormy": ["rainy", "cloudy", "partly_cloudy"],
                    "rainy": ["cloudy", "partly_cloudy", "sunny"],
                    "cloudy": ["partly_cloudy", "sunny", "sunny"],
                    "partly_cloudy": ["sunny", "sunny", "partly_cloudy"],
                    "sunny": ["sunny", "partly_cloudy", "sunny"],
                    "foggy": ["cloudy", "partly_cloudy", "sunny"],
                    "snowy": ["cloudy", "partly_cloudy", "sunny"],
                }
                progression = condition_progression.get(
                    current_condition, ["partly_cloudy"]
                )
                return progression[min(day, len(progression) - 1)]

        # Long-term predictions (3-4 days)
        # - return to average conditions
        else:
            if pressure_system == "high_pressure":
                return "sunny"
            elif pressure_system == "low_pressure":
                return "cloudy"
            else:
                return "partly_cloudy"

    def _forecast_precipitation_enhanced(
        self,
        day: int,
        condition: str,
        pressure_analysis: Dict[str, Any],
        humidity_trend: Dict[str, Any],
    ) -> float:
        """Enhanced precipitation forecasting using multiple data sources.

        Args:
            day: Day ahead to forecast (0-4)
            condition: Forecasted weather condition
            pressure_analysis: Pressure trend analysis
            humidity_trend: Historical humidity trends

        Returns:
            float: Precipitation amount in mm
        """
        base_precipitation = 0.0
        storm_probability = pressure_analysis.get("storm_probability", 0)

        # Base precipitation by condition
        condition_precip = {
            "stormy": 15.0,
            "rainy": 5.0,
            "snowy": 3.0,
            "cloudy": 0.5,
            "foggy": 0.1,
        }
        base_precipitation = condition_precip.get(condition, 0.0)

        # Adjust by storm probability
        if storm_probability > 70:
            base_precipitation *= 1.5
        elif storm_probability > 40:
            base_precipitation *= 1.2

        # Adjust by humidity trends
        if humidity_trend and humidity_trend.get("average", 50) > 80:
            base_precipitation *= 1.3

        # Reduce precipitation for distant forecasts (less confidence)
        confidence_factor = max(0.3, 1.0 - (day * 0.15))
        base_precipitation *= confidence_factor

        return round(base_precipitation, 1)

    def _forecast_wind_enhanced(
        self,
        day: int,
        current_wind: float,
        condition: str,
        wind_trend: Dict[str, Any],
        pressure_analysis: Dict[str, Any],
    ) -> float:
        """Enhanced wind forecasting using trends and weather patterns.

        Args:
            day: Day ahead to forecast (0-4)
            current_wind: Current wind speed in mph
            condition: Forecasted weather condition
            wind_trend: Historical wind trends
            pressure_analysis: Pressure trend analysis

        Returns:
            float: Forecasted wind speed in km/h
        """
        # Convert current wind to km/h for consistency
        current_wind_kmh = self._convert_to_kmh(current_wind) or 10

        # Base wind by condition
        condition_wind = {
            "stormy": 30.0,  # Strong winds with storms
            "rainy": 15.0,  # Moderate winds with rain
            "cloudy": 10.0,  # Light winds
            "partly_cloudy": 8.0,
            "sunny": 5.0,  # Light winds on clear days
            "foggy": 3.0,  # Very light winds with fog
            "snowy": 12.0,  # Moderate winds with snow
        }
        forecast_wind = condition_wind.get(condition, current_wind_kmh)

        # Apply pressure system influence
        pressure_system = pressure_analysis.get("pressure_system", "normal")
        if pressure_system == "low_pressure":
            forecast_wind *= 1.3  # Stronger winds with low pressure
        elif pressure_system == "high_pressure":
            forecast_wind *= 0.8  # Lighter winds with high pressure

        # Apply historical trend influence (dampened)
        if wind_trend and wind_trend.get("trend"):
            trend_influence = wind_trend["trend"] * 24 * 0.1  # 10% of 24-hour trend
            forecast_wind += trend_influence

        # Reduce wind for distant forecasts
        distance_factor = max(0.5, 1.0 - (day * 0.1))
        forecast_wind *= distance_factor

        return round(max(1.0, forecast_wind), 1)

    def _forecast_humidity(
        self,
        day: int,
        current_humidity: float,
        humidity_trend: Dict[str, Any],
        condition: str,
    ) -> int:
        """Forecast humidity based on trends and weather conditions.

        Args:
            day: Day ahead to forecast (0-4)
            current_humidity: Current humidity percentage
            humidity_trend: Historical humidity trends
            condition: Forecasted weather condition

        Returns:
            int: Forecasted humidity percentage
        """
        forecast_humidity = current_humidity

        # Base humidity by condition
        condition_humidity = {
            "stormy": 85,
            "rainy": 80,
            "snowy": 75,
            "cloudy": 70,
            "partly_cloudy": 60,
            "sunny": 50,
            "foggy": 95,
        }
        target_humidity = condition_humidity.get(condition, current_humidity)

        # Gradually move toward target humidity
        humidity_change = (target_humidity - current_humidity) * (1 - day * 0.2)
        forecast_humidity += humidity_change

        # Apply historical trend influence
        if humidity_trend and humidity_trend.get("trend"):
            trend_influence = humidity_trend["trend"] * 24 * 0.05  # 5% of 24-hour trend
            forecast_humidity += trend_influence

        return max(10, min(100, int(round(forecast_humidity))))

    def _store_historical_data(self, sensor_data: Dict[str, Any]) -> None:
        """Store current sensor readings in historical buffer.

        Args:
            sensor_data: Current sensor readings to store
        """
        timestamp = datetime.now()

        for sensor_key, value in sensor_data.items():
            if sensor_key in self._sensor_history and value is not None:
                self._sensor_history[sensor_key].append(
                    {"timestamp": timestamp, "value": value}
                )

    def _get_historical_trends(
        self, sensor_key: str, hours: int = 24
    ) -> Dict[str, Any]:
        """Calculate historical trends for a sensor over the specified time period.

        Args:
            sensor_key: The sensor key to analyze
            hours: Number of hours to look back

        Returns:
            dict: Trend analysis including:
                - current: Most recent value
                - average: Average over the period
                - trend: Rate of change per hour
                - min/max: Min/max values
                - volatility: Standard deviation
        """
        if sensor_key not in self._sensor_history:
            return {}

        # Get data from the last N hours
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = [
            entry
            for entry in self._sensor_history[sensor_key]
            if entry["timestamp"] > cutoff_time
        ]

        if len(recent_data) < 2:
            return {}

        values = [entry["value"] for entry in recent_data]
        timestamps = [entry["timestamp"] for entry in recent_data]

        # Calculate time differences in hours
        time_diffs = [(t - timestamps[0]).total_seconds() / 3600 for t in timestamps]

        try:
            # Basic statistics
            current = values[-1]
            average = statistics.mean(values)
            minimum = min(values)
            maximum = max(values)
            volatility = statistics.stdev(values) if len(values) > 1 else 0

            # Trend calculation (linear regression slope)
            trend = self._calculate_trend(time_diffs, values)

            return {
                "current": current,
                "average": average,
                "trend": trend,  # Change per hour
                "min": minimum,
                "max": maximum,
                "volatility": volatility,
                "sample_count": len(values),
            }
        except statistics.StatisticsError:
            return {}

    def _calculate_trend(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate linear trend (slope) using simple linear regression.

        Args:
            x_values: Independent variable values (time)
            y_values: Dependent variable values (sensor readings)

        Returns:
            float: Slope of the trend line (change per unit time)
        """
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def _analyze_pressure_trends(self) -> Dict[str, Any]:
        """Analyze pressure trends for weather prediction.

        Returns:
            dict: Pressure trend analysis including:
                - current_trend: Short-term pressure change
                - long_term_trend: 24-hour pressure trend
                - pressure_system: Type of pressure system
                - storm_probability: Probability of storm development
        """
        # Get pressure trends over different time periods
        short_trend = self._get_historical_trends("pressure", hours=3)  # 3-hour trend
        long_trend = self._get_historical_trends("pressure", hours=24)  # 24-hour trend

        if not short_trend or not long_trend:
            return {"pressure_system": "unknown", "storm_probability": 0.0}

        current_pressure = long_trend["current"]
        short_term_change = short_trend["trend"] * 3  # 3-hour change
        long_term_change = long_trend["trend"] * 24  # 24-hour change

        # Classify pressure system
        if current_pressure > 1020:
            pressure_system = "high_pressure"
        elif current_pressure < 1000:
            pressure_system = "low_pressure"
        else:
            pressure_system = "normal"

        # Calculate storm probability based on pressure trends
        storm_probability = 0.0

        # Rapid pressure drop indicates approaching storm
        if short_term_change < -2:  # Falling >2 hPa in 3 hours
            storm_probability += 40

        # Sustained pressure drop over 24 hours
        if long_term_change < -5:  # Falling >5 hPa in 24 hours
            storm_probability += 30

        # Very low pressure indicates storm
        if current_pressure < 990:
            storm_probability += 30

        # Cap storm probability
        storm_probability = min(100.0, storm_probability)

        return {
            "current_trend": short_term_change,
            "long_term_trend": long_term_change,
            "pressure_system": pressure_system,
            "storm_probability": storm_probability,
        }
