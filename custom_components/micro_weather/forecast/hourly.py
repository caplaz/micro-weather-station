"""Hourly forecast generation module.

This module provides comprehensive 24-hour hourly forecast generation using:
- Astronomical diurnal cycles
- Pressure trend modulation
- Wind pattern analysis
- Moisture transport modeling
- Weather system micro-evolution
"""

from datetime import datetime, timedelta
import logging
import math
import random
from typing import Any, Dict, List, Optional

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
)
from homeassistant.util import dt as dt_util

from ..analysis.atmospheric import AtmosphericAnalyzer
from ..analysis.solar import SolarAnalyzer
from ..analysis.trends import TrendsAnalyzer
from ..const import (
    KEY_CONDITION,
    KEY_HUMIDITY,
    KEY_PRECIPITATION,
    KEY_TEMPERATURE,
    KEY_WIND_SPEED,
)
from ..meteorological_constants import (
    DiurnalPatternConstants,
    ForecastConstants,
    HumidityTargetConstants,
    PressureTrendConstants,
    WindAdjustmentConstants,
)
from ..weather_utils import convert_to_kmh, is_forecast_hour_daytime

_LOGGER = logging.getLogger(__name__)


class HourlyForecastGenerator:
    """Handles generation of 24-hour hourly forecasts."""

    def __init__(
        self,
        atmospheric_analyzer: AtmosphericAnalyzer,
        solar_analyzer: SolarAnalyzer,
        trends_analyzer: TrendsAnalyzer,
    ):
        """Initialize hourly forecast generator.

        Args:
            atmospheric_analyzer: AtmosphericAnalyzer instance
            solar_analyzer: SolarAnalyzer instance
            trends_analyzer: TrendsAnalyzer instance
        """
        self.atmospheric_analyzer = atmospheric_analyzer
        self.solar_analyzer = solar_analyzer
        self.trends_analyzer = trends_analyzer

    def generate_forecast(
        self,
        current_temp: float,
        current_condition: str,
        sensor_data: Dict[str, Any],
        sunrise_time: Optional[datetime],
        sunset_time: Optional[datetime],
        altitude: float | None,
        meteorological_state: Dict[str, Any],
        hourly_patterns: Dict[str, Any],
        micro_evolution: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive 24-hour hourly forecast.

        Args:
            current_temp: Current temperature in Celsius
            current_condition: Current weather condition
            sensor_data: Current sensor data in imperial units
            sunrise_time: Sunrise time for astronomical calculations
            sunset_time: Sunset time for astronomical calculations
            altitude: Altitude for pressure corrections
            meteorological_state: Comprehensive meteorological state analysis
            hourly_patterns: Hourly weather patterns
            micro_evolution: Micro-evolution model
            astronomical_calculator: AstronomicalCalculator instance

        Returns:
            List[Dict[str, Any]]: 24-hour forecast with detailed hourly predictions
        """
        try:
            hourly_forecast: List[Dict[str, Any]] = []

            for hour_idx in range(24):
                # Start from the current hour (rounded down) and add hourly intervals
                current_hour = dt_util.now().replace(minute=0, second=0, microsecond=0)
                forecast_time = current_hour + timedelta(hours=hour_idx)

                # Determine astronomical context
                astronomical_context = self._calculate_astronomical_context(
                    forecast_time, sunrise_time, sunset_time, hour_idx
                )

                # Advanced hourly temperature with multi-factor modulation
                forecast_temp = self.forecast_temperature(
                    hour_idx,
                    current_temp,
                    astronomical_context,
                    meteorological_state,
                    hourly_patterns,
                    micro_evolution,
                )

                # Advanced hourly condition with micro-evolution
                # Use previous hour's condition as base for current hour (except first hour)
                base_condition = current_condition
                if hour_idx > 0:
                    base_condition = hourly_forecast[hour_idx - 1][KEY_CONDITION]

                forecast_condition = self.forecast_condition(
                    hour_idx,
                    base_condition,
                    astronomical_context,
                    meteorological_state,
                    hourly_patterns,
                    micro_evolution,
                )

                # Advanced hourly precipitation with moisture transport
                precipitation = self._forecast_precipitation(
                    hour_idx,
                    forecast_condition,
                    meteorological_state,
                    hourly_patterns,
                    sensor_data,
                )

                # Advanced hourly wind with boundary layer effects
                wind_speed = self._forecast_wind(
                    hour_idx,
                    sensor_data.get(
                        KEY_WIND_SPEED, ForecastConstants.DEFAULT_WIND_SPEED
                    ),
                    forecast_condition,
                    meteorological_state,
                    hourly_patterns,
                )

                # Advanced hourly humidity with moisture dynamics
                humidity = self._forecast_humidity(
                    hour_idx,
                    sensor_data.get(KEY_HUMIDITY, ForecastConstants.DEFAULT_HUMIDITY),
                    meteorological_state,
                    hourly_patterns,
                    forecast_condition,
                )

                hourly_forecast.append(
                    {
                        "datetime": forecast_time.replace(tzinfo=None).isoformat(),
                        KEY_TEMPERATURE: round(forecast_temp, 1),
                        KEY_CONDITION: forecast_condition,
                        KEY_PRECIPITATION: round(precipitation, 2),
                        KEY_WIND_SPEED: round(wind_speed, 1),
                        KEY_HUMIDITY: round(humidity, 0),
                        "is_nighttime": not astronomical_context["is_daytime"],
                    }
                )

            return hourly_forecast
        except Exception as e:
            # Log error and return a simple default forecast to prevent UI issues
            _LOGGER.warning("Comprehensive hourly forecast generation failed: %s", e)
            fallback_forecast: List[Dict[str, Any]] = []
            base_temp = (
                current_temp
                if isinstance(current_temp, (int, float))
                else ForecastConstants.DEFAULT_TEMPERATURE
            )
            base_condition = (
                current_condition
                if isinstance(current_condition, str)
                else ATTR_CONDITION_CLOUDY
            )
            for hour_idx in range(24):
                # Start from the current hour (rounded down) and add hourly intervals
                current_hour = dt_util.now().replace(minute=0, second=0, microsecond=0)
                forecast_time = current_hour + timedelta(hours=hour_idx)

                # Use previous hour's condition as base for current hour (except first hour)
                forecast_condition = base_condition
                if hour_idx > 0:
                    forecast_condition = fallback_forecast[hour_idx - 1][KEY_CONDITION]

                # Apply day/night conversion to fallback forecast too
                astronomical_context = self._calculate_astronomical_context(
                    forecast_time, sunrise_time, sunset_time, hour_idx
                )
                if not astronomical_context["is_daytime"]:
                    if forecast_condition == ATTR_CONDITION_SUNNY:
                        forecast_condition = ATTR_CONDITION_CLEAR_NIGHT
                    elif forecast_condition == ATTR_CONDITION_PARTLYCLOUDY:
                        forecast_condition = ATTR_CONDITION_CLEAR_NIGHT
                else:
                    if forecast_condition == ATTR_CONDITION_CLEAR_NIGHT:
                        forecast_condition = ATTR_CONDITION_SUNNY
                    elif forecast_condition == ATTR_CONDITION_CLOUDY:
                        forecast_condition = ATTR_CONDITION_PARTLYCLOUDY

                fallback_forecast.append(
                    {
                        "datetime": forecast_time.isoformat(),
                        KEY_TEMPERATURE: base_temp,
                        KEY_CONDITION: forecast_condition,
                        KEY_PRECIPITATION: 0.0,
                        KEY_WIND_SPEED: ForecastConstants.DEFAULT_WIND_SPEED,
                        KEY_HUMIDITY: ForecastConstants.DEFAULT_HUMIDITY,
                        "is_nighttime": False,
                    }
                )
            return fallback_forecast

    def forecast_temperature(
        self,
        hour_idx: int,
        current_temp: float,
        astronomical_context: Dict[str, Any],
        meteorological_state: Dict[str, Any],
        hourly_patterns: Dict[str, Any],
        micro_evolution: Dict[str, Any],
    ) -> float:
        """Forecast temperature for a specific hour with comprehensive modulation."""
        # Ensure current_temp is not None
        if current_temp is None:
            current_temp = ForecastConstants.DEFAULT_TEMPERATURE
        forecast_temp = current_temp

        # Astronomical diurnal variation (inlined from AstronomicalCalculator)
        hour = astronomical_context["hour_of_day"]
        diurnal_patterns = hourly_patterns.get("diurnal_patterns", {}).get(
            KEY_TEMPERATURE, {}
        )

        # Default diurnal patterns
        default_patterns = {
            "dawn": DiurnalPatternConstants.TEMP_DAWN,
            "morning": DiurnalPatternConstants.TEMP_MORNING,
            "noon": DiurnalPatternConstants.TEMP_NOON,
            "afternoon": DiurnalPatternConstants.TEMP_AFTERNOON,
            "evening": DiurnalPatternConstants.TEMP_EVENING,
            "night": DiurnalPatternConstants.TEMP_NIGHT,
            "midnight": DiurnalPatternConstants.TEMP_MIDNIGHT,
        }

        # Merge provided patterns with defaults
        patterns = {**default_patterns, **diurnal_patterns}

        # Map hour to diurnal period
        if 5 <= hour < 7:
            diurnal_variation = patterns["dawn"]
        elif 7 <= hour < 12:
            diurnal_variation = patterns["morning"]
        elif 12 <= hour < 15:
            diurnal_variation = patterns["noon"]
        elif 15 <= hour < 19:
            diurnal_variation = patterns["afternoon"]
        elif 19 <= hour < 22:
            diurnal_variation = patterns["evening"]
        elif 22 <= hour < 24 or hour < 2:
            diurnal_variation = patterns["night"]
        else:  # 2-5 AM
            diurnal_variation = patterns["midnight"]

        # Apply distance-based dampening to diurnal variation for distant forecasts
        diurnal_dampening = max(
            ForecastConstants.HOURLY_MIN_DAMPENING,
            1.0 - (hour_idx * ForecastConstants.HOURLY_DAMPENING_RATE),
        )
        diurnal_variation *= diurnal_dampening
        forecast_temp += diurnal_variation

        # Pressure trend modulation
        pressure_modulation = self._calculate_hourly_pressure_modulation(
            meteorological_state, hour_idx
        )
        forecast_temp += pressure_modulation

        # Micro-evolution influence
        evolution_influence = self._calculate_hourly_evolution_influence(
            micro_evolution, hour_idx
        )
        forecast_temp += evolution_influence

        # Natural variation
        natural_variation = (
            hour_idx % ForecastConstants.NATURAL_VARIATION_PERIOD - 1
        ) * ForecastConstants.NATURAL_VARIATION_AMPLITUDE
        distance_dampening = max(
            ForecastConstants.HOURLY_NATURAL_VARIATION_DAMPENING,
            1.0 - (hour_idx * ForecastConstants.HOURLY_VARIATION_DECAY),
        )
        natural_variation *= distance_dampening
        forecast_temp += natural_variation

        return forecast_temp

    def forecast_condition(
        self,
        hour_idx: int,
        current_condition: str,
        astronomical_context: Dict[str, Any],
        meteorological_state: Dict[str, Any],
        hourly_patterns: Dict[str, Any],
        micro_evolution: Dict[str, Any],
    ) -> str:
        """Forecast condition for a specific hour with micro-evolution."""
        if current_condition is None:
            current_condition = ATTR_CONDITION_CLOUDY
        forecast_condition = current_condition

        cloud_analysis = meteorological_state.get("cloud_analysis", {})
        cloud_cover = cloud_analysis.get("cloud_cover", 50)
        is_daytime = astronomical_context["is_daytime"]

        # Apply time-of-day conversion
        if is_daytime:
            if forecast_condition == ATTR_CONDITION_CLEAR_NIGHT:
                forecast_condition = ATTR_CONDITION_SUNNY
            elif (
                forecast_condition == ATTR_CONDITION_CLOUDY
                and cloud_cover <= ForecastConstants.CLOUD_COVER_CLOUDY_THRESHOLD + 10
            ):
                forecast_condition = ATTR_CONDITION_PARTLYCLOUDY
        else:
            if forecast_condition == ATTR_CONDITION_SUNNY:
                forecast_condition = ATTR_CONDITION_CLEAR_NIGHT
            elif forecast_condition == ATTR_CONDITION_PARTLYCLOUDY:
                pressure_analysis = meteorological_state.get("pressure_analysis", {})
                pressure_trend = pressure_analysis.get("current_trend", 0)
                storm_prob = pressure_analysis.get("storm_probability", 0)

                if not isinstance(pressure_trend, (int, float)):
                    pressure_trend = 0.0
                if not isinstance(storm_prob, (int, float)):
                    storm_prob = 0.0

                if (
                    pressure_trend < -abs(ForecastConstants.PRESSURE_SLOW_FALL)
                    or storm_prob > ForecastConstants.STORM_THRESHOLD_MODERATE
                    or cloud_cover > 70
                ):
                    forecast_condition = ATTR_CONDITION_CLOUDY
                else:
                    forecast_condition = ATTR_CONDITION_CLEAR_NIGHT

        # Pressure-aware micro-evolution
        pressure_analysis = meteorological_state.get("pressure_analysis", {})
        storm_probability = pressure_analysis.get("storm_probability", 0)

        should_evolve = self._calculate_pressure_aware_evolution_frequency(
            pressure_analysis, hour_idx
        )

        if should_evolve:
            current_trend = pressure_analysis.get("current_trend", 0)
            long_term_trend = pressure_analysis.get("long_term_trend", 0)
            if not isinstance(current_trend, (int, float)):
                current_trend = 0.0
            if not isinstance(long_term_trend, (int, float)):
                long_term_trend = 0.0

            pressure_driven_condition = self._determine_pressure_driven_condition(
                pressure_analysis,
                storm_probability,
                cloud_cover,
                is_daytime,
                forecast_condition,
            )

            if pressure_driven_condition:
                forecast_condition = pressure_driven_condition

        return forecast_condition

    def _calculate_astronomical_context(
        self,
        forecast_time: datetime,
        sunrise_time: Optional[datetime],
        sunset_time: Optional[datetime],
        hour_idx: int,
    ) -> Dict[str, Any]:
        """Calculate astronomical context for hourly forecasting."""
        is_daytime = is_forecast_hour_daytime(forecast_time, sunrise_time, sunset_time)

        if is_daytime and sunrise_time and sunset_time:
            day_length = (sunset_time - sunrise_time).total_seconds() / 3600
            time_since_sunrise = (forecast_time - sunrise_time).total_seconds() / 3600
            solar_position = time_since_sunrise / day_length if day_length > 0 else 0.5
            solar_elevation = 90 * math.sin(math.pi * solar_position)
        else:
            solar_elevation = 0

        return {
            "is_daytime": is_daytime,
            "solar_elevation": solar_elevation,
            "hour_of_day": forecast_time.hour,
            "forecast_hour": hour_idx,
        }

    def _calculate_hourly_pressure_modulation(
        self, meteorological_state: Dict[str, Any], hour_idx: int
    ) -> float:
        """Calculate pressure-based temperature modulation for the hour."""
        pressure_analysis = meteorological_state.get("pressure_analysis", {})
        current_trend = pressure_analysis.get("current_trend", 0)
        modulation = current_trend * ForecastConstants.PRESSURE_TEMP_MODULATION
        time_dampening = max(
            ForecastConstants.HOURLY_MIN_DAMPENING,
            1.0 - (hour_idx * ForecastConstants.HOURLY_DAMPENING_RATE),
        )
        modulation *= time_dampening
        return max(-1.0, min(1.0, modulation))

    def _calculate_hourly_evolution_influence(
        self, micro_evolution: Dict[str, Any], hour_idx: int
    ) -> float:
        """Calculate micro-evolution influence on temperature."""
        evolution_rate = micro_evolution.get(
            "evolution_rate", ForecastConstants.NATURAL_VARIATION_AMPLITUDE
        )
        max_change = micro_evolution.get("micro_changes", {}).get(
            "max_change_per_hour", ForecastConstants.EVOLUTION_BASE_INFLUENCE
        )
        influence = evolution_rate * max_change * (0.5 - (hour_idx % 2))
        distance_dampening = max(
            ForecastConstants.HOURLY_DISTANCE_FACTOR_MIN,
            1.0 - (hour_idx * ForecastConstants.HOURLY_DISTANCE_DECAY),
        )
        influence *= distance_dampening
        return influence

    def _analyze_pressure_trend_severity(
        self, current_trend: float, long_term_trend: float
    ) -> Dict[str, Any]:
        """Analyze pressure trend magnitude and classify severity."""
        if not isinstance(current_trend, (int, float)):
            current_trend = 0.0
        if not isinstance(long_term_trend, (int, float)):
            long_term_trend = 0.0

        current_abs = abs(current_trend)
        if current_abs < PressureTrendConstants.STABLE_THRESHOLD:
            severity = "stable"
        elif current_abs < PressureTrendConstants.SLOW_THRESHOLD:
            severity = "slow"
        elif current_abs < PressureTrendConstants.MODERATE_THRESHOLD:
            severity = "moderate"
        else:
            severity = "rapid"

        if abs(current_trend) < 0.1:
            direction = "stable"
        elif current_trend < 0:
            direction = "falling"
        else:
            direction = "rising"

        if abs(long_term_trend) < PressureTrendConstants.SLOW_THRESHOLD:
            long_term_direction = "stable"
        elif long_term_trend < 0:
            long_term_direction = "falling"
        else:
            long_term_direction = "rising"

        urgency_factor = min(1.0, current_abs / 3.0)
        trend_agreement = 1.0 - min(1.0, abs(current_trend - long_term_trend) / 5.0)
        confidence = 0.5 + (trend_agreement * 0.5)

        return {
            "severity": severity,
            "direction": direction,
            "long_term_direction": long_term_direction,
            "urgency_factor": urgency_factor,
            "confidence": confidence,
        }

    def _calculate_pressure_aware_evolution_frequency(
        self, pressure_analysis: Dict[str, Any], hour_idx: int
    ) -> bool:
        """Determine if conditions should evolve at this hour based on pressure trends."""
        current_trend = pressure_analysis.get("current_trend", 0)
        long_term_trend = pressure_analysis.get("long_term_trend", 0)
        trend_analysis = self._analyze_pressure_trend_severity(
            current_trend, long_term_trend
        )
        severity = trend_analysis["severity"]

        if severity == "rapid":
            return hour_idx > 0 and hour_idx % 2 == 0
        elif severity == "moderate":
            return hour_idx > 0 and hour_idx % 3 == 0
        else:
            return hour_idx > 0 and hour_idx % 6 == 0

    def _determine_pressure_driven_condition(
        self,
        pressure_analysis: Dict[str, Any],
        storm_probability: float,
        cloud_cover: float,
        is_daytime: bool,
        current_condition: str,
    ) -> Optional[str]:
        """Determine condition based on pressure trends and storm probability."""
        current_trend = pressure_analysis.get("current_trend", 0)

        if storm_probability > ForecastConstants.STORM_THRESHOLD_SEVERE:
            if cloud_cover > ForecastConstants.STORM_PRECIPITATION_THRESHOLD:
                return ATTR_CONDITION_LIGHTNING_RAINY
            else:
                return ATTR_CONDITION_RAINY
        elif storm_probability > ForecastConstants.STORM_THRESHOLD_MODERATE:
            if current_trend < -abs(ForecastConstants.PRESSURE_SLOW_FALL) or (
                cloud_cover > 70
            ):
                return ATTR_CONDITION_RAINY

        if abs(current_trend) > PressureTrendConstants.MODERATE_THRESHOLD:
            if current_trend < -PressureTrendConstants.MODERATE_THRESHOLD:
                if current_condition == ATTR_CONDITION_SUNNY:
                    return ATTR_CONDITION_PARTLYCLOUDY
                elif current_condition == ATTR_CONDITION_PARTLYCLOUDY:
                    return ATTR_CONDITION_CLOUDY
            elif current_trend > PressureTrendConstants.MODERATE_THRESHOLD:
                if current_condition == ATTR_CONDITION_CLOUDY:
                    return ATTR_CONDITION_PARTLYCLOUDY
                elif current_condition == ATTR_CONDITION_PARTLYCLOUDY:
                    return (
                        ATTR_CONDITION_SUNNY
                        if is_daytime
                        else ATTR_CONDITION_CLEAR_NIGHT
                    )
        return None

    def _forecast_precipitation(
        self,
        hour_idx: int,
        condition: str,
        meteorological_state: Dict[str, Any],
        hourly_patterns: Dict[str, Any],
        sensor_data: Dict[str, Any],
    ) -> float:
        """Comprehensive hourly precipitation forecasting."""
        current_precipitation = sensor_data.get(KEY_PRECIPITATION, 0.0)
        if hasattr(current_precipitation, "_mock_name") or not isinstance(
            current_precipitation, (int, float)
        ):
            current_precipitation = 0.0

        precipitation = current_precipitation
        condition_variation = {
            ATTR_CONDITION_LIGHTNING_RAINY: 1.5,
            ATTR_CONDITION_POURING: 1.3,
            ATTR_CONDITION_RAINY: 1.1,
            ATTR_CONDITION_SNOWY: 0.8,
            ATTR_CONDITION_CLOUDY: 0.5,
            ATTR_CONDITION_FOG: 0.3,
        }

        variation_factor = condition_variation.get(condition, 1.0)
        precipitation *= variation_factor
        variation = random.uniform(0.8, 1.2)  # nosec B311
        precipitation *= variation

        if condition in [
            ATTR_CONDITION_LIGHTNING_RAINY,
            ATTR_CONDITION_POURING,
            ATTR_CONDITION_RAINY,
        ]:
            precipitation = max(precipitation, 0.1)

        return round(max(0.0, precipitation), 2)

    def _forecast_wind(
        self,
        hour_idx: int,
        current_wind: float,
        condition: str,
        meteorological_state: Dict[str, Any],
        hourly_patterns: Dict[str, Any],
    ) -> float:
        """Comprehensive hourly wind forecasting."""
        wind_kmh = convert_to_kmh(current_wind) or convert_to_kmh(
            ForecastConstants.DEFAULT_WIND_SPEED
        )
        hour = (dt_util.now() + timedelta(hours=hour_idx + 1)).hour
        diurnal_patterns = hourly_patterns.get("diurnal_patterns", {}).get("wind", {})

        default_wind_patterns = {
            "dawn": DiurnalPatternConstants.WIND_DAWN,
            "morning": DiurnalPatternConstants.WIND_MORNING,
            "noon": DiurnalPatternConstants.WIND_NOON,
            "afternoon": DiurnalPatternConstants.WIND_AFTERNOON,
            "evening": DiurnalPatternConstants.WIND_EVENING,
            "night": DiurnalPatternConstants.WIND_NIGHT,
            "midnight": DiurnalPatternConstants.WIND_MIDNIGHT,
        }

        diurnal_patterns = {**default_wind_patterns, **diurnal_patterns}

        if 5 <= hour < 7:
            diurnal_factor = diurnal_patterns["dawn"]
        elif 7 <= hour < 12:
            diurnal_factor = diurnal_patterns["morning"]
        elif 12 <= hour < 15:
            diurnal_factor = diurnal_patterns["noon"]
        elif 15 <= hour < 19:
            diurnal_factor = diurnal_patterns["afternoon"]
        elif 19 <= hour < 22:
            diurnal_factor = diurnal_patterns["evening"]
        else:
            diurnal_factor = diurnal_patterns["night"]

        wind_kmh += diurnal_factor

        condition_factors = {
            ATTR_CONDITION_WINDY: WindAdjustmentConstants.WINDY,
            ATTR_CONDITION_LIGHTNING_RAINY: WindAdjustmentConstants.LIGHTNING_RAINY,
            ATTR_CONDITION_RAINY: WindAdjustmentConstants.RAINY,
            ATTR_CONDITION_CLOUDY: WindAdjustmentConstants.CLOUDY,
            ATTR_CONDITION_SUNNY: WindAdjustmentConstants.SUNNY,
        }
        wind_kmh *= condition_factors.get(condition, 1.0)
        return round(max(ForecastConstants.MIN_WIND_SPEED, wind_kmh), 1)

    def _forecast_humidity(
        self,
        hour_idx: int,
        current_humidity: float,
        meteorological_state: Dict[str, Any],
        hourly_patterns: Dict[str, Any],
        condition: str,
    ) -> float:
        """Comprehensive hourly humidity forecasting."""
        if current_humidity is None:
            current_humidity = ForecastConstants.DEFAULT_HUMIDITY
        humidity = current_humidity

        hour = (dt_util.now() + timedelta(hours=hour_idx + 1)).hour
        diurnal_patterns = hourly_patterns.get("diurnal_patterns", {}).get(
            KEY_HUMIDITY, {}
        )

        default_humidity_patterns = {
            "dawn": DiurnalPatternConstants.HUMIDITY_DAWN,
            "morning": DiurnalPatternConstants.HUMIDITY_MORNING,
            "noon": DiurnalPatternConstants.HUMIDITY_NOON,
            "afternoon": DiurnalPatternConstants.HUMIDITY_AFTERNOON,
            "evening": DiurnalPatternConstants.HUMIDITY_EVENING,
            "night": DiurnalPatternConstants.HUMIDITY_NIGHT,
            "midnight": DiurnalPatternConstants.HUMIDITY_MIDNIGHT,
        }

        diurnal_patterns = {**default_humidity_patterns, **diurnal_patterns}

        if 5 <= hour < 7:
            diurnal_change = diurnal_patterns["dawn"]
        elif 7 <= hour < 12:
            diurnal_change = diurnal_patterns["morning"]
        elif 12 <= hour < 15:
            diurnal_change = diurnal_patterns["noon"]
        elif 15 <= hour < 19:
            diurnal_change = diurnal_patterns["afternoon"]
        elif 19 <= hour < 22:
            diurnal_change = diurnal_patterns["evening"]
        else:
            diurnal_change = diurnal_patterns["night"]

        humidity += diurnal_change

        condition_humidity = {
            ATTR_CONDITION_LIGHTNING_RAINY: HumidityTargetConstants.LIGHTNING_RAINY,
            ATTR_CONDITION_POURING: HumidityTargetConstants.POURING,
            ATTR_CONDITION_RAINY: HumidityTargetConstants.RAINY,
            ATTR_CONDITION_FOG: HumidityTargetConstants.FOG,
            ATTR_CONDITION_CLOUDY: HumidityTargetConstants.CLOUDY,
            ATTR_CONDITION_PARTLYCLOUDY: HumidityTargetConstants.PARTLYCLOUDY,
            ATTR_CONDITION_SUNNY: HumidityTargetConstants.SUNNY,
            ATTR_CONDITION_CLEAR_NIGHT: HumidityTargetConstants.CLEAR_NIGHT,
        }

        target_humidity = condition_humidity.get(condition, current_humidity)
        humidity = current_humidity + (target_humidity - current_humidity) * 0.1
        return int(
            max(
                ForecastConstants.MIN_HUMIDITY,
                min(ForecastConstants.MAX_HUMIDITY, humidity),
            )
        )
