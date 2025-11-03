"""Core weather condition analysis.

This module contains the main weather condition determination logic,
simplified and focused on clarity and maintainability.
"""

import logging
import math
from typing import Any, Dict, Optional

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
)

from ..const import (
    KEY_DEWPOINT,
    KEY_HUMIDITY,
    KEY_OUTDOOR_TEMP,
    KEY_PRESSURE,
    KEY_RAIN_RATE,
    KEY_SOLAR_LUX_INTERNAL,
    KEY_SOLAR_RADIATION,
    KEY_UV_INDEX,
    KEY_WIND_GUST,
    KEY_WIND_SPEED,
)
from ..meteorological_constants import (
    PrecipitationThresholds,
    TemperatureThresholds,
    WindThresholds,
)

_LOGGER = logging.getLogger(__name__)


class WeatherConditionAnalyzer:
    """Analyzes weather conditions based on sensor data.

    This class focuses on the core logic of determining weather conditions
    from sensor readings, using a priority-based approach:
    1. Active precipitation (highest priority)
    2. Fog conditions
    3. Severe weather (thunderstorms, gales)
    4. Daytime/nighttime conditions (cloud cover)
    5. Default conditions
    """

    def __init__(self, atmospheric_analyzer, solar_analyzer, trends_analyzer):
        """Initialize with required analyzers.

        Args:
            atmospheric_analyzer: AtmosphericAnalyzer instance for pressure/fog
            solar_analyzer: SolarAnalyzer instance for cloud cover
            trends_analyzer: TrendsAnalyzer instance for historical trends
        """
        self.atmospheric = atmospheric_analyzer
        self.solar = solar_analyzer
        self.trends = trends_analyzer

    def determine_condition(
        self,
        sensor_data: Dict[str, Any],
        altitude: Optional[float] = 0.0,
    ) -> str:
        """Determine weather condition from sensor data.

        Uses a priority-based approach to determine the most appropriate
        weather condition. Each priority level can override lower priorities.

        Args:
            sensor_data: Dictionary of current sensor readings
            altitude: Altitude in meters for pressure correction

        Returns:
            Weather condition string (e.g., "sunny", "rainy", "cloudy")
        """
        # Extract and validate sensor data
        sensors = self._extract_sensors(sensor_data)

        # Calculate derived parameters
        params = self._calculate_parameters(sensors, altitude)

        # Priority 1: Active precipitation
        if condition := self._check_precipitation(sensors, params):
            return condition

        # Priority 2: Fog conditions
        if condition := self._check_fog(sensors, params):
            return condition

        # Priority 3: Severe weather (no precipitation)
        if condition := self._check_severe_weather(sensors, params):
            return condition

        # Priority 4: Daytime/nighttime cloud-based conditions
        if params["is_daytime"]:
            return self._determine_daytime_condition(sensors, params)
        elif params["is_twilight"]:
            return self._determine_twilight_condition(sensors, params)
        else:
            return self._determine_nighttime_condition(sensors, params)

    def _extract_sensors(self, sensor_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract and validate sensor values with defaults."""
        return {
            "rain_rate": sensor_data.get(KEY_RAIN_RATE, 0.0),
            "rain_state": sensor_data.get("rain_state", "dry").lower(),
            "wind_speed": sensor_data.get(KEY_WIND_SPEED, 0.0),
            "wind_gust": sensor_data.get(KEY_WIND_GUST, 0.0),
            "solar_radiation": sensor_data.get(KEY_SOLAR_RADIATION, 0.0),
            "solar_lux": sensor_data.get(KEY_SOLAR_LUX_INTERNAL, 0.0),
            "uv_index": sensor_data.get(KEY_UV_INDEX, 0.0),
            "outdoor_temp": sensor_data.get(KEY_OUTDOOR_TEMP, 70.0),
            "humidity": sensor_data.get(KEY_HUMIDITY, 50.0),
            "pressure": sensor_data.get(KEY_PRESSURE, 29.92),
            "dewpoint_raw": sensor_data.get(KEY_DEWPOINT),
            "solar_elevation": sensor_data.get("solar_elevation"),
        }

    def _calculate_parameters(
        self, sensors: Dict[str, float], altitude: Optional[float]
    ) -> Dict[str, Any]:
        """Calculate derived meteorological parameters."""
        # Calculate dewpoint (use sensor if available, otherwise calculate)
        if sensors["dewpoint_raw"] is not None:
            dewpoint = float(sensors["dewpoint_raw"])
        else:
            dewpoint = self.calculate_dewpoint(
                sensors["outdoor_temp"], sensors["humidity"]
            )

        return {
            "dewpoint": dewpoint,
            "temp_dewpoint_spread": sensors["outdoor_temp"] - dewpoint,
            "is_freezing": sensors["outdoor_temp"] <= TemperatureThresholds.FREEZING,
            "is_daytime": (
                sensors["solar_radiation"] > 5
                or sensors["solar_lux"] > 50
                or sensors["uv_index"] > 0.1
            ),
            "is_twilight": (
                (sensors["solar_lux"] > 10 and sensors["solar_lux"] < 100)
                or (sensors["solar_radiation"] > 1 and sensors["solar_radiation"] < 50)
            ),
            "adjusted_pressure": self.atmospheric.adjust_pressure_for_altitude(
                sensors["pressure"], altitude or 0.0, "relative"
            ),
            "pressure_thresholds": self.atmospheric.get_altitude_adjusted_pressure_thresholds(
                altitude or 0.0
            ),
            "gust_factor": sensors["wind_gust"] / max(sensors["wind_speed"], 1),
        }

    def _check_precipitation(
        self, sensors: Dict[str, float], params: Dict[str, Any]
    ) -> Optional[str]:
        """Check for active precipitation conditions."""
        significant_rain = sensors["rain_rate"] > PrecipitationThresholds.SIGNIFICANT

        if not (significant_rain or sensors["rain_state"] == "wet"):
            return None

        # Determine precipitation type based on temperature
        if params["is_freezing"]:
            return ATTR_CONDITION_SNOWY

        # Check for thunderstorm conditions
        if self._is_thunderstorm(sensors, params):
            return ATTR_CONDITION_LIGHTNING_RAINY

        # Classify rain intensity
        intensity = self.classify_precipitation_intensity(sensors["rain_rate"])

        if (
            intensity == "heavy"
            or sensors["rain_rate"] > PrecipitationThresholds.MODERATE
        ):
            return ATTR_CONDITION_POURING
        else:
            return ATTR_CONDITION_RAINY

    def _is_thunderstorm(
        self, sensors: Dict[str, float], params: Dict[str, Any]
    ) -> bool:
        """Determine if conditions indicate thunderstorm activity."""
        thresholds = params["pressure_thresholds"]
        pressure = params["adjusted_pressure"]
        gust_factor = params["gust_factor"]

        # Severe storm pressure
        if pressure < thresholds["extremely_low"]:
            return True

        # Storm pressure + strong winds + moderate+ rain
        if (
            pressure < thresholds["very_low"]
            and sensors["wind_speed"] >= WindThresholds.FRESH_BREEZE
            and sensors["rain_rate"] > PrecipitationThresholds.LIGHT
        ):
            return True

        # Storm pressure + very gusty + heavy rain
        if (
            pressure < thresholds["very_low"]
            and gust_factor > WindThresholds.GUST_FACTOR_STRONG
            and sensors["rain_rate"] > PrecipitationThresholds.MODERATE
        ):
            return True

        # Severe turbulence indicator
        is_severe_turbulence = (
            gust_factor > WindThresholds.GUST_FACTOR_SEVERE
            and sensors["wind_gust"] > WindThresholds.GUST_SEVERE
        ) or sensors["wind_gust"] > WindThresholds.GUST_EXTREME

        if (
            is_severe_turbulence
            and sensors["rain_rate"] > PrecipitationThresholds.STORM_MIN_RATE
        ):
            return True

        return False

    def _check_fog(
        self, sensors: Dict[str, float], params: Dict[str, Any]
    ) -> Optional[str]:
        """Check for fog conditions using atmospheric analyzer."""
        return self.atmospheric.analyze_fog_conditions(
            sensors["outdoor_temp"],
            sensors["humidity"],
            params["dewpoint"],
            params["temp_dewpoint_spread"],
            sensors["wind_speed"],
            sensors["solar_radiation"],
            params["is_daytime"],
        )

    def _check_severe_weather(
        self, sensors: Dict[str, float], params: Dict[str, Any]
    ) -> Optional[str]:
        """Check for severe weather without precipitation."""
        thresholds = params["pressure_thresholds"]
        pressure = params["adjusted_pressure"]
        gust_factor = params["gust_factor"]

        # Severe turbulence or very low pressure with strong winds
        is_severe = (
            gust_factor > WindThresholds.GUST_FACTOR_SEVERE
            and sensors["wind_gust"] > WindThresholds.GUST_SEVERE
        ) or sensors["wind_gust"] > WindThresholds.GUST_EXTREME

        wind_strong = (
            WindThresholds.FRESH_BREEZE
            <= sensors["wind_speed"]
            < WindThresholds.NEAR_GALE
        )

        if (
            pressure < thresholds["very_low"]
            and wind_strong
            and gust_factor > WindThresholds.GUST_FACTOR_STRONG
        ) or is_severe:
            return ATTR_CONDITION_LIGHTNING

        # Gale force winds
        if sensors["wind_speed"] >= WindThresholds.NEAR_GALE:
            return ATTR_CONDITION_WINDY

        return None

    def _determine_daytime_condition(
        self, sensors: Dict[str, float], params: Dict[str, Any]
    ) -> str:
        """Determine daytime condition based on cloud cover."""
        # Get solar elevation with fallback
        solar_elevation = sensors["solar_elevation"]
        has_solar_data = (
            sensors["solar_radiation"] > 0
            or sensors["solar_lux"] > 0
            or sensors["uv_index"] > 0
        )

        if solar_elevation is None:
            if has_solar_data:
                solar_elevation = 45.0  # Reasonable default
            else:
                # Fallback to atmospheric analysis
                return self._atmospheric_fallback_condition(sensors, params)

        # Analyze pressure trends for cloud prediction
        pressure_trends = self.trends.analyze_pressure_trends(
            params.get("altitude", 0.0)
        )

        # Analyze cloud cover
        cloud_cover = self.solar.analyze_cloud_cover(
            sensors["solar_radiation"],
            sensors["solar_lux"],
            sensors["uv_index"],
            solar_elevation,
            pressure_trends,
        )

        # Map cloud cover to condition with hysteresis
        proposed = self.solar.map_cloud_cover_to_condition(cloud_cover)
        final = self.solar.apply_condition_hysteresis(proposed, cloud_cover)

        # Override with windy if conditions are right
        wind_strong = (
            WindThresholds.FRESH_BREEZE
            <= sensors["wind_speed"]
            < WindThresholds.NEAR_GALE
        )
        gust_factor = params["gust_factor"]
        is_very_gusty = (
            gust_factor > WindThresholds.GUST_FACTOR_STRONG
            and sensors["wind_gust"] > WindThresholds.GUST_STRONG
        )

        if final == ATTR_CONDITION_SUNNY and (
            wind_strong
            or (is_very_gusty and sensors["wind_speed"] >= WindThresholds.LIGHT_BREEZE)
        ):
            return ATTR_CONDITION_WINDY

        return final

    def _atmospheric_fallback_condition(
        self, sensors: Dict[str, float], params: Dict[str, Any]
    ) -> str:
        """Fallback condition determination using atmospheric data."""
        humidity = sensors["humidity"]
        spread = params["temp_dewpoint_spread"]
        pressure = params["adjusted_pressure"]
        thresholds = params["pressure_thresholds"]

        # Clear conditions
        if (
            humidity < TemperatureThresholds.HUMIDITY_MODERATE
            and spread > TemperatureThresholds.SPREAD_MODERATE
        ):
            return ATTR_CONDITION_SUNNY
        elif (
            humidity < TemperatureThresholds.HUMIDITY_MODERATE_HIGH
            and spread > TemperatureThresholds.SPREAD_HUMID
            and thresholds["normal_low"] <= pressure <= thresholds["normal_high"]
        ):
            return ATTR_CONDITION_SUNNY
        elif pressure > thresholds["high"] and humidity < 75:
            return ATTR_CONDITION_SUNNY
        elif pressure < thresholds["low"] and humidity < 80:
            return ATTR_CONDITION_PARTLYCLOUDY
        elif humidity >= 85:
            return ATTR_CONDITION_CLOUDY
        else:
            return ATTR_CONDITION_PARTLYCLOUDY

    def _determine_twilight_condition(
        self, sensors: Dict[str, float], params: Dict[str, Any]
    ) -> str:
        """Determine twilight condition."""
        thresholds = params["pressure_thresholds"]
        pressure = params["adjusted_pressure"]

        if (
            sensors["solar_lux"] > 50
            and thresholds["normal_low"] <= pressure <= thresholds["normal_high"]
        ):
            return ATTR_CONDITION_PARTLYCLOUDY
        else:
            return ATTR_CONDITION_CLOUDY

    def _determine_nighttime_condition(
        self, sensors: Dict[str, float], params: Dict[str, Any]
    ) -> str:
        """Determine nighttime condition based on atmospheric data."""
        humidity = sensors["humidity"]
        pressure = params["adjusted_pressure"]
        thresholds = params["pressure_thresholds"]
        wind_speed = sensors["wind_speed"]
        gust_factor = params["gust_factor"]

        # Most specific: Combined conditions
        if (
            pressure < thresholds["low"]
            and humidity > TemperatureThresholds.HUMIDITY_HIGH
            and wind_speed < 3
        ):
            return ATTR_CONDITION_CLOUDY

        # Clear night conditions
        if (
            pressure > thresholds["very_high"]
            and wind_speed < WindThresholds.CALM
            and humidity < TemperatureThresholds.HUMIDITY_MODERATE_HIGH
        ):
            return ATTR_CONDITION_CLEAR_NIGHT
        elif (
            pressure > thresholds["high"]
            and gust_factor <= WindThresholds.GUST_FACTOR_MODERATE
            and humidity < 80
        ):
            return ATTR_CONDITION_CLEAR_NIGHT
        elif pressure < thresholds["low"] and humidity < 65:
            return ATTR_CONDITION_CLEAR_NIGHT

        # Partly cloudy night
        if (
            thresholds["normal_low"] <= pressure <= thresholds["normal_high"]
            and WindThresholds.CALM <= wind_speed < WindThresholds.LIGHT_BREEZE
            and humidity < 85
        ):
            return ATTR_CONDITION_PARTLYCLOUDY
        elif pressure < thresholds["low"] and humidity < 90:
            return ATTR_CONDITION_PARTLYCLOUDY

        # Cloudy night
        if humidity > 90:
            return ATTR_CONDITION_CLOUDY

        # Default night condition
        return ATTR_CONDITION_PARTLYCLOUDY

    def calculate_dewpoint(self, temp_f: float, humidity: Optional[float]) -> float:
        """Calculate dewpoint using Magnus formula.

        Args:
            temp_f: Temperature in Fahrenheit
            humidity: Relative humidity as percentage (0-100), or None

        Returns:
            Dewpoint temperature in Fahrenheit
        """
        if humidity is None or humidity <= 0:
            return temp_f - 50  # Approximate for very dry conditions

        # Convert to Celsius
        temp_c = (temp_f - 32) * 5 / 9

        # Magnus formula constants
        a = 17.27
        b = 237.7

        # Calculate dewpoint in Celsius
        gamma = (a * temp_c) / (b + temp_c) + math.log(humidity / 100.0)
        dewpoint_c = (b * gamma) / (a - gamma)

        # Convert back to Fahrenheit
        return dewpoint_c * 9 / 5 + 32

    def classify_precipitation_intensity(self, rain_rate: float) -> str:
        """Classify precipitation intensity.

        Args:
            rain_rate: Rain rate in inches/hour or mm/hour

        Returns:
            Intensity classification: "trace", "light", "moderate", or "heavy"
        """
        if rain_rate >= PrecipitationThresholds.HEAVY:
            return "heavy"
        elif rain_rate >= PrecipitationThresholds.LIGHT:
            return "moderate"
        elif rain_rate >= PrecipitationThresholds.SIGNIFICANT:
            return "light"
        else:
            return "trace"

    def estimate_visibility(self, condition: str, sensor_data: Dict[str, Any]) -> float:
        """Estimate visibility based on weather condition.

        Args:
            condition: Current weather condition
            sensor_data: Current sensor readings

        Returns:
            Estimated visibility in kilometers
        """
        sensors = self._extract_sensors(sensor_data)

        # Fog has most reduced visibility
        if condition == ATTR_CONDITION_FOG:
            if (
                sensors["humidity"] >= 98
                and (
                    sensors["outdoor_temp"]
                    - self.calculate_dewpoint(
                        sensors["outdoor_temp"], sensors["humidity"]
                    )
                )
                <= 0.5
            ):
                return 0.2  # Dense fog
            elif sensors["humidity"] >= 95:
                return 0.5  # Thick fog
            elif sensors["humidity"] >= 92:
                return 1.0  # Moderate fog
            else:
                return 2.0  # Light fog

        # Precipitation reduces visibility
        if condition in [ATTR_CONDITION_RAINY, ATTR_CONDITION_SNOWY]:
            base = 15.0 if condition == ATTR_CONDITION_RAINY else 8.0
            intensity_factor = 0.3 if sensors["rain_rate"] > 0.5 else 0.7
            wind_factor = max(0.6, 1.0 - (sensors["wind_speed"] / 50))
            return round(max(0.5, base * intensity_factor * wind_factor), 1)

        # Thunderstorms
        if condition == ATTR_CONDITION_LIGHTNING_RAINY:
            if sensors["rain_rate"] > 0.1:
                return round(max(0.8, 3.0 - (sensors["rain_rate"] * 2)), 1)
            else:
                return round(max(0.8, 8.0 - (sensors["wind_gust"] / 10)), 1)

        # Clear conditions
        if condition == ATTR_CONDITION_CLEAR_NIGHT:
            if sensors["humidity"] < 50:
                return 25.0
            elif sensors["humidity"] < 70:
                return 20.0
            else:
                return 15.0

        # Sunny conditions
        if condition == ATTR_CONDITION_SUNNY:
            if sensors["solar_radiation"] > 800:
                return 30.0
            elif sensors["solar_radiation"] >= 600:
                return 25.0
            elif sensors["solar_radiation"] > 400:
                return 20.0
            else:
                return 15.0

        # Cloudy/partly cloudy
        if condition in [ATTR_CONDITION_PARTLYCLOUDY, ATTR_CONDITION_CLOUDY]:
            is_daytime = (
                sensors["solar_radiation"] > 5
                or sensors["solar_lux"] > 50
                or sensors["uv_index"] > 0.1
            )
            if is_daytime:
                if sensors["solar_lux"] > 50000:
                    return 25.0
                elif sensors["solar_lux"] > 20000:
                    return 20.0
                elif sensors["solar_lux"] > 5000:
                    return 15.0
                else:
                    return 12.0
            else:
                if sensors["humidity"] < 75:
                    return 18.0
                elif sensors["humidity"] < 85:
                    return 15.0
                else:
                    return 12.0

        # Default
        return 15.0
