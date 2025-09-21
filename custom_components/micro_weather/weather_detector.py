"""Weather condition detector using real sensor data."""

from datetime import datetime, timedelta
import logging
import math
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
        indoor_temp = sensor_data.get("indoor_temp", outdoor_temp)

        # Calculate derived meteorological parameters
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
        wind_moderate = 8 <= wind_speed < 19  # 8-18 mph: Gentle to fresh breeze
        wind_strong = 19 <= wind_speed < 32  # 19-31 mph: Strong breeze to near gale
        wind_gale = wind_speed >= 32  # 32+ mph: Gale force

        gust_factor = wind_gust / max(wind_speed, 1)  # Gust ratio for turbulence
        is_gusty = gust_factor > 1.5 and wind_gust > 10
        is_very_gusty = gust_factor > 2.0 and wind_gust > 15

        _LOGGER.info(
            f"Weather Analysis - Rain: {rain_rate:.2f} in/h ({rain_state}), "
            f"Wind: {wind_speed:.1f} mph (gust: {wind_gust:.1f}, ratio: {gust_factor:.1f}), "
            f"Pressure: {pressure:.2f} inHg, Solar: {solar_radiation:.0f} W/m² ({solar_lux:.0f} lx), "
            f"Temp: {outdoor_temp:.1f}°F, Humidity: {humidity:.0f}%, "
            f"Dewpoint: {dewpoint:.1f}°F (spread: {temp_dewpoint_spread:.1f}°F)"
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

        # PRIORITY 2: SEVERE WEATHER CONDITIONS (No precipitation but extreme conditions)
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
        """Calculate dewpoint using Magnus formula (meteorologically accurate)."""
        if humidity <= 0:
            return temp_f - 50  # Approximate for very dry conditions

        # Convert to Celsius for calculation
        temp_c = (temp_f - 32) * 5 / 9

        # Magnus formula constants
        a = 17.27
        b = 237.7

        # Calculate dewpoint in Celsius
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
        """
        Advanced fog analysis using meteorological principles.

        Fog formation requires:
        - High humidity (>90%)
        - Small temperature-dewpoint spread (<4°F)
        - Light winds (<7 mph) for radiation fog
        - Specific conditions for other fog types
        """

        # Radiation fog (most common - clear nights, light winds)
        if (
            humidity >= 95
            and spread <= 3
            and wind_speed <= 5
            and (not is_daytime or solar_rad < 10)
        ):
            return "foggy"

        # Dense fog conditions
        if humidity >= 98 and spread <= 2 and wind_speed <= 3:
            return "foggy"

        # Advection fog (moist air over cooler surface)
        if humidity >= 92 and spread <= 4 and 3 <= wind_speed <= 12:
            return "foggy"

        # Evaporation fog (after rain, warm ground)
        if humidity >= 90 and spread <= 5 and wind_speed <= 8 and temp > 40:
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

        # Special handling for fog - it's often localized and temporary
        if current_condition == "foggy":
            if day == 0:
                return "foggy"  # Fog may persist for a day
            elif day == 1:
                # Fog often clears to cloudy or partly cloudy
                return "cloudy" if humidity > 85 else "partly_cloudy"
            else:
                # After fog clears, normal weather patterns resume
                if pressure_hpa > 1020:
                    return "partly_cloudy"
                elif pressure_hpa < 1000:
                    return "cloudy"
                else:
                    return "partly_cloudy"

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
            # More conservative precipitation calculation
            if condition == "rainy":
                base_precip = 2.0  # Reduced from 5.0
            else:  # stormy
                base_precip = 5.0  # Reduced from 10.0

            # More realistic humidity and pressure factors
            humidity_factor = max(1.0, (humidity - 60) / 40)  # Only boost above 60%
            pressure_factor = max(1.0, (1013 - pressure_hpa) / 40)  # More conservative
            return round(base_precip * humidity_factor * pressure_factor, 1)
        elif condition == "snowy":
            return 2.0  # Reduced from 3.0
        elif condition == "cloudy" and humidity > 80:  # Raised threshold
            return 0.5  # Reduced from 1.0
        elif condition == "foggy":
            # Fog rarely leads to significant precipitation
            return 0.1 if humidity > 95 else 0.0
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
