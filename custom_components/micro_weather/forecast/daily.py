"""Daily forecast generation module.

This module provides comprehensive 5-day daily forecast generation using:
- Multi-factor meteorological analysis
- Historical pattern recognition
- Weather system evolution modeling
- Advanced precipitation forecasting
"""

from datetime import timedelta
import logging
import math
from typing import Any, Dict, List

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
)
from homeassistant.util import dt as dt_util

from ..analysis.trends import TrendsAnalyzer
from ..const import (
    KEY_CONDITION,
    KEY_HUMIDITY,
    KEY_OUTDOOR_TEMP,
    KEY_PRECIPITATION,
    KEY_RAIN_RATE,
    KEY_TEMPERATURE,
    KEY_WIND_SPEED,
)
from ..meteorological_constants import (
    CloudCoverThresholds,
    ForecastConstants,
    HumidityTargetConstants,
    PrecipitationConstants,
    WindAdjustmentConstants,
)
from ..weather_utils import convert_to_kmh

_LOGGER = logging.getLogger(__name__)


class DailyForecastGenerator:
    """Handles generation of 5-day daily forecasts."""

    def __init__(self, trends_analyzer: TrendsAnalyzer):
        """Initialize daily forecast generator.

        Args:
            trends_analyzer: TrendsAnalyzer instance for historical data
        """
        self.trends_analyzer = trends_analyzer

    def generate_forecast(
        self,
        current_condition: str,
        sensor_data: Dict[str, Any],
        altitude: float | None,
        meteorological_state: Dict[str, Any],
        historical_patterns: Dict[str, Any],
        system_evolution: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive 5-day daily forecast.

        Args:
            current_condition: Current weather condition
            sensor_data: Current sensor data in imperial units
            altitude: Altitude in meters above sea level
            meteorological_state: Comprehensive meteorological analysis
            historical_patterns: Historical weather patterns
            system_evolution: Weather system evolution model

        Returns:
            List[Dict[str, Any]]: 5-day forecast with enhanced accuracy
        """
        forecast = []

        # Current baseline values
        current_temp = (
            sensor_data.get(KEY_TEMPERATURE)
            or sensor_data.get(KEY_OUTDOOR_TEMP)
            or ForecastConstants.DEFAULT_TEMPERATURE
        )
        current_humidity = sensor_data.get(
            KEY_HUMIDITY, ForecastConstants.DEFAULT_HUMIDITY
        )
        current_wind = sensor_data.get(
            KEY_WIND_SPEED, ForecastConstants.DEFAULT_WIND_SPEED
        )

        for day_idx in range(5):
            date = dt_util.now() + timedelta(days=day_idx)

            # Advanced temperature forecasting using multi-factor analysis
            forecast_temp = self.forecast_temperature(
                day_idx,
                current_temp,
                meteorological_state,
                historical_patterns,
                system_evolution,
            )

            # Advanced condition forecasting using all meteorological factors
            forecast_condition = self.forecast_condition(
                day_idx,
                current_condition,
                meteorological_state,
                historical_patterns,
                system_evolution,
            )

            # Advanced precipitation forecasting using atmospheric analysis
            precipitation = self._forecast_precipitation(
                day_idx,
                forecast_condition,
                meteorological_state,
                historical_patterns,
                sensor_data,
            )

            # Advanced wind forecasting using pressure gradients and historical patterns
            wind_forecast = self._forecast_wind(
                day_idx,
                current_wind,
                forecast_condition,
                meteorological_state,
                historical_patterns,
            )

            # Advanced humidity forecasting using moisture analysis
            humidity_forecast = self._forecast_humidity(
                day_idx,
                current_humidity,
                meteorological_state,
                historical_patterns,
                forecast_condition,
            )

            forecast.append(
                {
                    "datetime": date.isoformat(),
                    KEY_TEMPERATURE: round(
                        forecast_temp or ForecastConstants.DEFAULT_TEMPERATURE, 1
                    ),
                    "templow": round(
                        (forecast_temp or ForecastConstants.DEFAULT_TEMPERATURE)
                        - self._calculate_temperature_range(
                            forecast_condition, meteorological_state
                        ),
                        1,
                    ),
                    KEY_CONDITION: forecast_condition,
                    KEY_PRECIPITATION: precipitation,
                    KEY_WIND_SPEED: wind_forecast,
                    KEY_HUMIDITY: humidity_forecast,
                }
            )

        return forecast

    def forecast_temperature(
        self,
        day_idx: int,
        current_temp: float,
        meteorological_state: Dict[str, Any],
        historical_patterns: Dict[str, Any],
        system_evolution: Dict[str, Any],
    ) -> float:
        """Forecast temperature for a specific day using multi-factor analysis.

        Args:
            day_idx: Day index (0-4)
            current_temp: Current temperature
            meteorological_state: Meteorological state analysis
            historical_patterns: Historical patterns
            system_evolution: System evolution model

        Returns:
            float: Forecasted temperature
        """
        forecast_temp = current_temp

        # Base astronomical seasonal adjustment
        seasonal_adjustment = self._calculate_seasonal_temperature_adjustment(day_idx)
        forecast_temp += seasonal_adjustment

        # Pressure system influence
        pressure_influence = self._calculate_pressure_temperature_influence(
            meteorological_state, day_idx
        )
        forecast_temp += pressure_influence

        # Historical pattern influence
        pattern_influence = self._calculate_historical_pattern_influence(
            historical_patterns, day_idx, KEY_TEMPERATURE
        )
        forecast_temp += pattern_influence

        # Weather system evolution influence
        evolution_influence = self._calculate_system_evolution_influence(
            system_evolution, day_idx, KEY_TEMPERATURE
        )
        forecast_temp += evolution_influence

        # Atmospheric stability dampening
        stability = meteorological_state["atmospheric_stability"]
        stability_dampening = (
            1.0 - stability * ForecastConstants.STABILITY_DAMPENING_FACTOR
        )  # Stable systems have less variation
        forecast_temp = (
            current_temp + (forecast_temp - current_temp) * stability_dampening
        )

        # Distance-based uncertainty using exponential decay (more realistic than linear)
        # Day 1 = 95% confidence, Day 2 = 85%, Day 3 = 70%, Day 4 = 55%, Day 5 = 35%
        # This reflects that forecast skill degrades exponentially with time
        uncertainty_factor = (
            math.exp(-ForecastConstants.UNCERTAINTY_DECAY_RATE * day_idx)
            * ForecastConstants.MAX_FORECAST_CONFIDENCE
            + ForecastConstants.MIN_FORECAST_CONFIDENCE
        )
        forecast_temp = (
            current_temp + (forecast_temp - current_temp) * uncertainty_factor
        )

        return forecast_temp

    def forecast_condition(
        self,
        day_idx: int,
        current_condition: str,
        meteorological_state: Dict[str, Any],
        historical_patterns: Dict[str, Any],
        system_evolution: Dict[str, Any],
    ) -> str:
        """Forecast condition for a specific day using all meteorological factors.

        Args:
            day_idx: Day index (0-4)
            current_condition: Current weather condition
            meteorological_state: Meteorological state analysis
            historical_patterns: Historical patterns
            system_evolution: System evolution model

        Returns:
            str: Forecasted weather condition
        """
        # Start with current condition as base
        forecast_condition = current_condition

        # Apply evolution stage mapping for future days
        forecast_condition = self._apply_evolution_stage_mapping(
            forecast_condition, day_idx, system_evolution, current_condition
        )

        # Apply pressure system overrides for day 0
        forecast_condition = self._apply_pressure_system_overrides(
            forecast_condition, day_idx, meteorological_state, system_evolution
        )

        # Apply cloud cover analysis for future days
        forecast_condition = self._apply_cloud_cover_analysis(
            forecast_condition, day_idx, meteorological_state, system_evolution
        )

        # Apply moisture analysis for precipitation potential
        forecast_condition = self._apply_moisture_precipitation_logic(
            forecast_condition, meteorological_state, day_idx
        )

        # Apply storm probability overrides (highest priority)
        forecast_condition = self._apply_storm_probability_overrides(
            forecast_condition, day_idx, meteorological_state
        )

        return forecast_condition

    def _apply_evolution_stage_mapping(
        self,
        forecast_condition: str,
        day_idx: int,
        system_evolution: Dict[str, Any],
        current_condition: str,
    ) -> str:
        """Apply evolution stage mapping for future days.

        Args:
            forecast_condition: Current forecast condition
            day_idx: Day index (0-4)
            system_evolution: System evolution model
            current_condition: Current weather condition

        Returns:
            str: Updated forecast condition based on evolution stage
        """
        # Get evolution stage for this day (skip for day 0)
        if day_idx > 0:
            evolution_path = system_evolution.get("evolution_path", [])
            if day_idx < len(evolution_path):
                evolution_stage = evolution_path[day_idx]

                # Map evolution stages to conditions
                evolution_condition_map = {
                    "stable_high": ATTR_CONDITION_SUNNY,
                    "weakening_high": ATTR_CONDITION_PARTLYCLOUDY,
                    "active_low": ATTR_CONDITION_CLOUDY,
                    "frontal_passage": ATTR_CONDITION_RAINY,
                    "frontal_approach": ATTR_CONDITION_CLOUDY,
                    "post_frontal": ATTR_CONDITION_PARTLYCLOUDY,
                    "clearing": ATTR_CONDITION_SUNNY,
                    "transitional": ATTR_CONDITION_PARTLYCLOUDY,
                    "new_system": ATTR_CONDITION_CLOUDY,
                    "current": current_condition,
                    "transitioning": ATTR_CONDITION_PARTLYCLOUDY,
                    "new_pattern": ATTR_CONDITION_CLOUDY,
                    "stabilizing": ATTR_CONDITION_SUNNY,
                }

                forecast_condition = evolution_condition_map.get(
                    evolution_stage, current_condition
                )

        return forecast_condition

    def _apply_pressure_system_overrides(
        self,
        forecast_condition: str,
        day_idx: int,
        meteorological_state: Dict[str, Any],
        system_evolution: Dict[str, Any],
    ) -> str:
        """Apply pressure system overrides for day 0 forecasting.

        Args:
            forecast_condition: Current forecast condition
            day_idx: Day index (0-4)
            meteorological_state: Meteorological state analysis
            system_evolution: System evolution model

        Returns:
            str: Updated forecast condition based on pressure systems
        """
        if day_idx != 0:
            return forecast_condition

        pressure_system = meteorological_state["pressure_analysis"].get(
            "pressure_system", "normal"
        )
        storm_probability = meteorological_state["pressure_analysis"].get(
            "storm_probability", 0
        )
        cloud_analysis = meteorological_state["cloud_analysis"]
        cloud_cover = cloud_analysis.get("cloud_cover", 50)

        # Get confidence value
        confidence = system_evolution.get("confidence_levels", [0.5])
        confidence_value = confidence[0] if confidence else 0.5
        confidence_value = max(
            confidence_value, ForecastConstants.DAY_ZERO_MIN_CONFIDENCE
        )

        current_trend = meteorological_state["pressure_analysis"].get(
            "current_trend", 0
        )

        # High pressure systems improve conditions
        if (
            pressure_system == "high_pressure"
            and confidence_value > ForecastConstants.CONFIDENCE_THRESHOLD_HIGH
        ):
            if cloud_cover < CloudCoverThresholds.THRESHOLD_CLOUDY:  # < 75%
                forecast_condition = (
                    ATTR_CONDITION_SUNNY
                    if cloud_cover < CloudCoverThresholds.THRESHOLD_SUNNY
                    else ATTR_CONDITION_PARTLYCLOUDY
                )

        # Low pressure systems worsen conditions
        elif (
            pressure_system == "low_pressure"
            and confidence_value > ForecastConstants.CONFIDENCE_THRESHOLD_HIGH
        ):
            if cloud_cover > CloudCoverThresholds.THRESHOLD_SUNNY:  # > 20%
                forecast_condition = ATTR_CONDITION_CLOUDY

        # Normal pressure systems: use trend direction
        elif (
            pressure_system == "normal"
            and confidence_value > ForecastConstants.CONFIDENCE_THRESHOLD_HIGH
        ):
            if (
                current_trend < -ForecastConstants.PRESSURE_TREND_FALLING_THRESHOLD
            ):  # Falling pressure in normal system
                if cloud_cover > CloudCoverThresholds.THRESHOLD_SUNNY:
                    forecast_condition = ATTR_CONDITION_CLOUDY
            elif (
                current_trend > ForecastConstants.PRESSURE_TREND_RISING_THRESHOLD
            ):  # Rising pressure in normal system
                if cloud_cover < CloudCoverThresholds.THRESHOLD_CLOUDY:
                    forecast_condition = (
                        ATTR_CONDITION_SUNNY
                        if cloud_cover < CloudCoverThresholds.THRESHOLD_SUNNY
                        else ATTR_CONDITION_PARTLYCLOUDY
                    )

        # High storm probability always indicates precipitation
        if storm_probability > ForecastConstants.STORM_PRECIPITATION_THRESHOLD:
            forecast_condition = (
                ATTR_CONDITION_LIGHTNING_RAINY
                if storm_probability >= ForecastConstants.STORM_THRESHOLD_SEVERE
                else ATTR_CONDITION_RAINY
            )

        return forecast_condition

    def _apply_cloud_cover_analysis(
        self,
        forecast_condition: str,
        day_idx: int,
        meteorological_state: Dict[str, Any],
        system_evolution: Dict[str, Any],
    ) -> str:
        """Apply cloud cover analysis for future days.

        Args:
            forecast_condition: Current forecast condition
            day_idx: Day index (0-4)
            meteorological_state: Meteorological state analysis
            system_evolution: System evolution model

        Returns:
            str: Updated forecast condition based on cloud cover
        """
        if day_idx == 0:
            return forecast_condition

        cloud_analysis = meteorological_state["cloud_analysis"]
        cloud_cover = cloud_analysis.get("cloud_cover", 50)

        # Get confidence value
        confidence = system_evolution.get("confidence_levels", [0.5])
        if confidence and len(confidence) > min(day_idx, len(confidence) - 1):
            confidence_value = confidence[min(day_idx, len(confidence) - 1)]
        else:
            confidence_value = 0.5

        # For future days, apply normal cloud cover logic
        if confidence_value > ForecastConstants.CONFIDENCE_THRESHOLD_HIGH:
            if cloud_cover < CloudCoverThresholds.THRESHOLD_SUNNY:
                forecast_condition = ATTR_CONDITION_SUNNY
            elif (
                cloud_cover > ForecastConstants.CLOUD_COVER_CLOUDY_THRESHOLD
            ):  # Lower threshold for cloudy
                forecast_condition = ATTR_CONDITION_CLOUDY

        return forecast_condition

    def _apply_moisture_precipitation_logic(
        self,
        forecast_condition: str,
        meteorological_state: Dict[str, Any],
        day_idx: int,
    ) -> str:
        """Apply moisture analysis for precipitation potential.

        Only applies to current day (day_idx == 0) to avoid false rain predictions
        for future days based on current moisture conditions.

        Args:
            forecast_condition: Current forecast condition
            meteorological_state: Meteorological state analysis
            day_idx: Day index (0-4)

        Returns:
            str: Updated forecast condition based on moisture analysis
        """
        # Only apply moisture precipitation logic to the current day
        # Future days should rely on pressure systems and evolution patterns
        if day_idx != 0:
            return forecast_condition

        moisture_analysis = meteorological_state["moisture_analysis"]
        condensation_potential = moisture_analysis.get("condensation_potential", 0.3)

        if (
            condensation_potential > ForecastConstants.CONDENSATION_RAIN_THRESHOLD
            and forecast_condition == ATTR_CONDITION_CLOUDY
        ):
            forecast_condition = ATTR_CONDITION_RAINY

        return forecast_condition

    def _apply_storm_probability_overrides(
        self,
        forecast_condition: str,
        day_idx: int,
        meteorological_state: Dict[str, Any],
    ) -> str:
        """Apply storm probability overrides (highest priority).

        Args:
            forecast_condition: Current forecast condition
            day_idx: Day index (0-4)
            meteorological_state: Meteorological state analysis

        Returns:
            str: Updated forecast condition based on storm probability
        """
        storm_probability = meteorological_state["pressure_analysis"].get(
            "storm_probability", 0
        )
        pressure_system = meteorological_state["pressure_analysis"].get(
            "pressure_system", "normal"
        )

        # Storm probability override (highest priority)
        if storm_probability >= ForecastConstants.STORM_THRESHOLD_SEVERE:
            if day_idx >= ForecastConstants.POURING_DAY_THRESHOLD:
                forecast_condition = ATTR_CONDITION_POURING
            else:
                forecast_condition = ATTR_CONDITION_LIGHTNING_RAINY
        elif (
            storm_probability > ForecastConstants.STORM_THRESHOLD_MODERATE
            and pressure_system == "low_pressure"
        ):
            if forecast_condition in [
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_CLOUDY,
            ]:
                forecast_condition = ATTR_CONDITION_RAINY

        return forecast_condition

    def _calculate_seasonal_temperature_adjustment(self, day_index: int) -> float:
        """Calculate seasonal temperature adjustment for forecast days.

        Returns small adjustments (±2°C) based on seasonal patterns.

        Args:
            day_index: Day index (0-4)

        Returns:
            float: Temperature adjustment in degrees
        """
        # Simple seasonal pattern - slightly cooler in early days, warmer later
        base_adjustment = (
            day_index - ForecastConstants.SEASONAL_ADJUSTMENT_CENTER
        ) * ForecastConstants.SEASONAL_ADJUSTMENT_BASE_RATE
        seasonal_variation = ForecastConstants.SEASONAL_ADJUSTMENT_VARIATION * (
            (day_index % ForecastConstants.SEASONAL_ADJUSTMENT_CYCLE)
            - ForecastConstants.SEASONAL_ADJUSTMENT_CYCLE_OFFSET
        )

        adjustment = base_adjustment + seasonal_variation
        return max(
            -ForecastConstants.SEASONAL_ADJUSTMENT_MAX_RANGE,
            min(ForecastConstants.SEASONAL_ADJUSTMENT_MAX_RANGE, adjustment),
        )

    def _calculate_pressure_temperature_influence(
        self, meteorological_state: Dict[str, Any], day_idx: int
    ) -> float:
        """Calculate temperature influence from pressure systems.

        Args:
            meteorological_state: Meteorological state analysis
            day_idx: Day index (0-4)

        Returns:
            float: Temperature influence in degrees
        """
        pressure_analysis = meteorological_state["pressure_analysis"]
        pressure_system = pressure_analysis.get("pressure_system", "normal")

        # Base influence by pressure system
        if pressure_system == "high_pressure":
            base_influence = (
                ForecastConstants.HIGH_PRESSURE_TEMP_INFLUENCE
            )  # High pressure = warmer
        elif pressure_system == "low_pressure":
            base_influence = (
                ForecastConstants.LOW_PRESSURE_TEMP_INFLUENCE
            )  # Low pressure = cooler
        else:
            base_influence = 0.0

        # Trend influence
        current_trend = pressure_analysis.get("current_trend", 0)
        long_trend = pressure_analysis.get("long_term_trend", 0)

        trend_influence = (current_trend * ForecastConstants.CURRENT_TREND_WEIGHT) + (
            long_trend * ForecastConstants.LONG_TERM_TREND_WEIGHT
        )

        # Dampen for forecast distance
        distance_dampening = max(
            ForecastConstants.DAILY_MIN_DAMPENING,
            1.0 - (day_idx * ForecastConstants.DAILY_DAMPENING_RATE),
        )
        total_influence = (base_influence + trend_influence) * distance_dampening

        # Use absolute value of LOW_PRESSURE influence as max
        max_influence = abs(ForecastConstants.LOW_PRESSURE_TEMP_INFLUENCE) + abs(
            ForecastConstants.HIGH_PRESSURE_TEMP_INFLUENCE
        )
        return max(-max_influence, min(max_influence, total_influence))

    def _calculate_historical_pattern_influence(
        self, historical_patterns: Dict[str, Any], day_idx: int, variable: str
    ) -> float:
        """Calculate influence from historical patterns.

        Args:
            historical_patterns: Historical weather patterns
            day_idx: Day index (0-4)
            variable: Variable name (e.g., KEY_TEMPERATURE)

        Returns:
            float: Pattern influence value
        """
        if variable not in historical_patterns:
            return 0.0

        pattern_data = historical_patterns[variable]
        volatility = pattern_data.get("volatility", 1.0)

        # Use volatility to estimate likely variation
        # Higher volatility = more potential for change
        max_influence = volatility * ForecastConstants.PATTERN_VOLATILITY_MULTIPLIER

        # Dampen based on forecast distance and pattern strength
        distance_factor = max(
            ForecastConstants.MIN_PATTERN_INFLUENCE,
            1.0 - (day_idx * ForecastConstants.PATTERN_DISTANCE_DECAY),
        )
        influence = max_influence * distance_factor

        # Random component based on historical patterns (±influence)
        # In a real implementation, this would use actual pattern recognition
        return influence * (
            ForecastConstants.PATTERN_ALTERNATION_BASELINE - (day_idx % 2)
        )  # Simplified alternating pattern

    def _calculate_system_evolution_influence(
        self, system_evolution: Dict[str, Any], day_idx: int, variable: str
    ) -> float:
        """Calculate influence from weather system evolution.

        Args:
            system_evolution: System evolution model
            day_idx: Day index (0-4)
            variable: Variable name (e.g., KEY_TEMPERATURE)

        Returns:
            float: Evolution influence value
        """
        evolution_path = system_evolution.get("evolution_path", [])
        confidence_levels = system_evolution.get("confidence_levels", [])

        if day_idx >= len(evolution_path):
            return 0.0

        # Get confidence for this day's evolution stage
        confidence = confidence_levels[min(day_idx, len(confidence_levels) - 1)]

        # Evolution influence based on system type
        # This is a simplified model - real implementation would be more sophisticated
        evolution_influence = (
            confidence * ForecastConstants.EVOLUTION_BASE_INFLUENCE
        )  # Base influence

        return evolution_influence

    def _forecast_precipitation(
        self,
        day_idx: int,
        condition: str,
        meteorological_state: Dict[str, Any],
        historical_patterns: Dict[str, Any],
        sensor_data: Dict[str, Any],
    ) -> float:
        """Comprehensive precipitation forecasting using atmospheric analysis and rain history.

        Args:
            day_idx: Day index (0-4)
            condition: Forecasted weather condition
            meteorological_state: Meteorological state analysis
            historical_patterns: Historical patterns
            sensor_data: Current sensor data

        Returns:
            float: Forecasted precipitation in mm (or inches based on sensor units)
        """
        # Get base precipitation by condition
        precipitation = self._get_base_precipitation_by_condition(condition)

        # Apply storm probability enhancement
        storm_probability = meteorological_state["pressure_analysis"].get(
            "storm_probability", 0
        )
        precipitation = self._apply_storm_probability_enhancement(
            precipitation, storm_probability
        )

        # Apply pressure trend adjustments
        pressure_trend = meteorological_state["pressure_analysis"].get(
            "current_trend", 0
        )
        precipitation = self._apply_pressure_trend_adjustment(
            precipitation, pressure_trend
        )

        # Apply moisture factors
        moisture_analysis = meteorological_state["moisture_analysis"]
        precipitation = self._apply_moisture_factors(precipitation, moisture_analysis)

        # Apply atmospheric stability
        stability = meteorological_state["atmospheric_stability"]
        precipitation = self._apply_atmospheric_stability(precipitation, stability)

        # Apply historical patterns
        precipitation = self._apply_historical_patterns(
            precipitation, historical_patterns, day_idx
        )

        # Apply distance dampening and unit conversion
        precipitation = self._apply_distance_dampening(
            precipitation, day_idx, sensor_data
        )

        return precipitation

    def _get_base_precipitation_by_condition(self, condition: str) -> float:
        """Get base precipitation amount based on weather condition.

        Args:
            condition: Weather condition string

        Returns:
            float: Base precipitation amount in mm
        """
        condition_precip = {
            ATTR_CONDITION_LIGHTNING_RAINY: PrecipitationConstants.LIGHTNING_RAINY,
            ATTR_CONDITION_POURING: PrecipitationConstants.POURING,
            ATTR_CONDITION_RAINY: PrecipitationConstants.RAINY,
            ATTR_CONDITION_SNOWY: PrecipitationConstants.SNOWY,
            ATTR_CONDITION_CLOUDY: PrecipitationConstants.CLOUDY,
            ATTR_CONDITION_FOG: PrecipitationConstants.FOG,
        }
        return condition_precip.get(condition, 0.0)

    def _apply_storm_probability_enhancement(
        self, precipitation: float, storm_probability: float
    ) -> float:
        """Apply storm probability enhancement to precipitation.

        Args:
            precipitation: Current precipitation amount
            storm_probability: Storm probability percentage

        Returns:
            float: Enhanced precipitation amount
        """
        if storm_probability > ForecastConstants.STORM_THRESHOLD_HIGH:
            precipitation *= ForecastConstants.PRECIP_MULT_STORM_HIGH
        elif storm_probability > ForecastConstants.STORM_THRESHOLD_MODERATE:
            precipitation *= ForecastConstants.PRECIP_MULT_STORM_MODERATE
        return precipitation

    def _apply_pressure_trend_adjustment(
        self, precipitation: float, pressure_trend: float
    ) -> float:
        """Apply pressure trend adjustments to precipitation.

        Args:
            precipitation: Current precipitation amount
            pressure_trend: Pressure trend value

        Returns:
            float: Adjusted precipitation amount
        """
        if pressure_trend < -abs(
            ForecastConstants.PRESSURE_RAPID_FALL
        ):  # Rapidly falling pressure
            precipitation *= ForecastConstants.PRECIP_MULT_RAPID_FALL
        elif pressure_trend < -abs(
            ForecastConstants.PRESSURE_SLOW_FALL
        ):  # Slowly falling pressure
            precipitation *= ForecastConstants.PRECIP_MULT_SLOW_FALL
        elif (
            pressure_trend > ForecastConstants.PRESSURE_MODERATE_RISE
        ):  # Rising pressure (clearing)
            precipitation *= ForecastConstants.PRECIP_MULT_RISING
        return precipitation

    def _apply_moisture_factors(
        self, precipitation: float, moisture_analysis: Dict[str, Any]
    ) -> float:
        """Apply moisture transport and condensation factors to precipitation.

        Args:
            precipitation: Current precipitation amount
            moisture_analysis: Moisture analysis dictionary

        Returns:
            float: Adjusted precipitation amount
        """
        transport_potential = moisture_analysis.get("transport_potential", 5)
        condensation_potential = moisture_analysis.get("condensation_potential", 0.3)

        moisture_factor = (
            transport_potential / ForecastConstants.MOISTURE_TRANSPORT_DIVISOR
        ) * condensation_potential
        precipitation *= 1.0 + moisture_factor
        return precipitation

    def _apply_atmospheric_stability(
        self, precipitation: float, stability: float
    ) -> float:
        """Apply atmospheric stability adjustments to precipitation.

        Args:
            precipitation: Current precipitation amount
            stability: Atmospheric stability index (0-1)

        Returns:
            float: Adjusted precipitation amount
        """
        instability_factor = 1.0 + (
            (1.0 - stability) * ForecastConstants.INSTABILITY_PRECIP_MULT
        )
        precipitation *= instability_factor
        return precipitation

    def _apply_historical_patterns(
        self,
        precipitation: float,
        historical_patterns: Dict[str, Any],
        day_idx: int,
    ) -> float:
        """Apply historical pattern influences to precipitation.

        Args:
            precipitation: Current precipitation amount
            historical_patterns: Historical patterns dictionary
            day_idx: Day index (0-4)

        Returns:
            float: Adjusted precipitation amount
        """
        # Use historical rain_rate patterns if available
        if KEY_RAIN_RATE in historical_patterns:
            rain_history = historical_patterns[KEY_RAIN_RATE]
            avg_rain = rain_history.get("mean", 0)
            if avg_rain > 0:
                # If there's a history of rain, increase forecast slightly
                precipitation *= max(
                    1.0, 1.0 + (avg_rain / ForecastConstants.RAIN_HISTORY_NORMALIZER)
                )

        # Historical pattern influence for precipitation variability
        pattern_influence = self._calculate_historical_pattern_influence(
            historical_patterns, day_idx, KEY_PRECIPITATION
        )
        precipitation += pattern_influence
        return precipitation

    def _apply_distance_dampening(
        self, precipitation: float, day_idx: int, sensor_data: Dict[str, Any]
    ) -> float:
        """Apply distance-based dampening and unit conversion to precipitation.

        Args:
            precipitation: Current precipitation amount
            day_idx: Day index (0-4)
            sensor_data: Sensor data dictionary

        Returns:
            float: Final precipitation amount
        """
        # Distance-based reduction (forecast uncertainty increases with time)
        distance_factor = max(
            ForecastConstants.DAILY_DISTANCE_FACTOR_MIN,
            1.0 - (day_idx * ForecastConstants.DAILY_DISTANCE_DECAY),
        )
        precipitation *= distance_factor

        # Convert to sensor units if needed
        rain_rate_unit = sensor_data.get("rain_rate_unit")
        if (
            rain_rate_unit
            and isinstance(rain_rate_unit, str)
            and any(unit in rain_rate_unit.lower() for unit in ["in", "inch", "inches"])
        ):
            precipitation /= PrecipitationConstants.MM_TO_INCHES

        return round(max(0.0, precipitation), 2)

    def _forecast_wind(
        self,
        day_idx: int,
        current_wind: float,
        condition: str,
        meteorological_state: Dict[str, Any],
        historical_patterns: Dict[str, Any],
    ) -> float:
        """Comprehensive wind forecasting using pressure gradients and patterns.

        Args:
            day_idx: Day index (0-4)
            current_wind: Current wind speed
            condition: Forecasted weather condition
            meteorological_state: Meteorological state analysis
            historical_patterns: Historical patterns

        Returns:
            float: Forecasted wind speed in km/h
        """
        # Convert current wind to km/h
        current_wind_kmh = convert_to_kmh(current_wind) or convert_to_kmh(
            ForecastConstants.DEFAULT_WIND_SPEED
        )
        assert current_wind_kmh is not None  # Should never be None with fallback

        forecast_wind = current_wind_kmh

        # Condition-based adjustments
        condition_wind_adjustment = {
            ATTR_CONDITION_LIGHTNING_RAINY: WindAdjustmentConstants.LIGHTNING_RAINY,
            ATTR_CONDITION_POURING: WindAdjustmentConstants.POURING,
            ATTR_CONDITION_RAINY: WindAdjustmentConstants.RAINY,
            "windy": WindAdjustmentConstants.WINDY,
            ATTR_CONDITION_CLOUDY: WindAdjustmentConstants.CLOUDY,
            ATTR_CONDITION_PARTLYCLOUDY: WindAdjustmentConstants.PARTLYCLOUDY,
            ATTR_CONDITION_SUNNY: WindAdjustmentConstants.SUNNY,
            ATTR_CONDITION_FOG: WindAdjustmentConstants.FOG,
            ATTR_CONDITION_SNOWY: WindAdjustmentConstants.SNOWY,
        }
        adjustment = condition_wind_adjustment.get(condition, 1.0)
        forecast_wind *= adjustment

        # Pressure system influence on wind
        pressure_system = meteorological_state["pressure_analysis"].get(
            "pressure_system", "normal"
        )
        if pressure_system == "low_pressure":
            forecast_wind *= (
                WindAdjustmentConstants.LOW_PRESSURE_MULT
            )  # Low pressure = stronger winds
        elif pressure_system == "high_pressure":
            forecast_wind *= (
                WindAdjustmentConstants.HIGH_PRESSURE_MULT
            )  # High pressure = lighter winds

        # Pressure gradient influence
        wind_pattern_analysis = meteorological_state["wind_pattern_analysis"]
        gradient_effect = wind_pattern_analysis.get("gradient_wind_effect", 0)
        forecast_wind += (
            gradient_effect * WindAdjustmentConstants.GRADIENT_WIND_MULTIPLIER
        )  # Pressure gradients drive wind

        # Wind pattern stability influence
        direction_stability = wind_pattern_analysis.get("direction_stability", 0.5)
        if (
            direction_stability < WindAdjustmentConstants.DIRECTION_UNSTABLE_THRESHOLD
        ):  # Unstable wind direction = variable winds
            forecast_wind *= WindAdjustmentConstants.DIRECTION_UNSTABLE_MULTIPLIER
        elif (
            direction_stability > WindAdjustmentConstants.DIRECTION_STABLE_THRESHOLD
        ):  # Stable direction = consistent winds
            forecast_wind *= WindAdjustmentConstants.DIRECTION_STABLE_MULTIPLIER

        # Historical pattern influence
        pattern_influence = self._calculate_historical_pattern_influence(
            historical_patterns, day_idx, "wind"
        )
        forecast_wind += pattern_influence

        # Distance dampening
        distance_factor = max(
            ForecastConstants.WIND_DISTANCE_FACTOR_MIN,
            1.0 - (day_idx * ForecastConstants.WIND_DISTANCE_DECAY),
        )
        forecast_wind *= distance_factor

        return round(max(ForecastConstants.MIN_WIND_SPEED, forecast_wind), 1)

    def _forecast_humidity(
        self,
        day_idx: int,
        current_humidity: float,
        meteorological_state: Dict[str, Any],
        historical_patterns: Dict[str, Any],
        condition: str,
    ) -> int:
        """Comprehensive humidity forecasting using moisture dynamics.

        Args:
            day_idx: Day index (0-4)
            current_humidity: Current humidity percentage
            meteorological_state: Meteorological state analysis
            historical_patterns: Historical patterns
            condition: Forecasted weather condition

        Returns:
            int: Forecasted humidity percentage (10-100)
        """
        forecast_humidity = current_humidity

        # Base humidity by condition
        condition_humidity = {
            ATTR_CONDITION_LIGHTNING_RAINY: HumidityTargetConstants.LIGHTNING_RAINY,
            ATTR_CONDITION_POURING: HumidityTargetConstants.POURING,
            ATTR_CONDITION_RAINY: HumidityTargetConstants.RAINY,
            ATTR_CONDITION_SNOWY: HumidityTargetConstants.SNOWY,
            ATTR_CONDITION_CLOUDY: HumidityTargetConstants.CLOUDY,
            ATTR_CONDITION_PARTLYCLOUDY: HumidityTargetConstants.PARTLYCLOUDY,
            ATTR_CONDITION_SUNNY: HumidityTargetConstants.SUNNY,
            "windy": HumidityTargetConstants.WINDY,
            ATTR_CONDITION_FOG: HumidityTargetConstants.FOG,
        }
        target_humidity = condition_humidity.get(condition, current_humidity)

        # Gradually move toward target
        humidity_change = (target_humidity - current_humidity) * (
            1 - day_idx * ForecastConstants.DAILY_DAMPENING_RATE
        )
        forecast_humidity += humidity_change

        # Moisture analysis influence
        moisture_analysis = meteorological_state["moisture_analysis"]
        trend_direction = moisture_analysis.get("trend_direction", "stable")

        if trend_direction == "increasing":
            forecast_humidity += HumidityTargetConstants.MOISTURE_TREND_ADJUSTMENT
        elif trend_direction == "decreasing":
            forecast_humidity -= HumidityTargetConstants.MOISTURE_TREND_ADJUSTMENT

        # Atmospheric stability influence
        stability = meteorological_state["atmospheric_stability"]
        if (
            stability > HumidityTargetConstants.STABILITY_HIGH_THRESHOLD
        ):  # Stable air holds moisture better
            forecast_humidity += HumidityTargetConstants.STABILITY_HUMIDITY_ADJUSTMENT
        elif (
            stability < HumidityTargetConstants.STABILITY_LOW_THRESHOLD
        ):  # Unstable air mixes and can reduce humidity
            forecast_humidity -= HumidityTargetConstants.STABILITY_HUMIDITY_ADJUSTMENT

        # Historical pattern influence
        pattern_influence = self._calculate_historical_pattern_influence(
            historical_patterns, day_idx, KEY_HUMIDITY
        )
        forecast_humidity += pattern_influence

        return int(
            max(
                ForecastConstants.MIN_HUMIDITY,
                min(ForecastConstants.MAX_HUMIDITY, round(forecast_humidity)),
            )
        )

    def _calculate_temperature_range(
        self, condition: str, meteorological_state: Dict[str, Any]
    ) -> float:
        """Calculate expected daily temperature range based on conditions.

        Args:
            condition: Weather condition
            meteorological_state: Meteorological state analysis

        Returns:
            float: Temperature range in degrees
        """
        base_range = ForecastConstants.DEFAULT_TEMP_RANGE  # Default range

        # Condition-based range adjustments
        condition_ranges = {
            ATTR_CONDITION_SUNNY: ForecastConstants.TEMP_RANGE_SUNNY,  # Large diurnal range on clear days
            ATTR_CONDITION_PARTLYCLOUDY: ForecastConstants.TEMP_RANGE_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY: ForecastConstants.TEMP_RANGE_CLOUDY,  # Small range on cloudy days
            ATTR_CONDITION_RAINY: ForecastConstants.TEMP_RANGE_RAINY,  # Very small range during rain
            ATTR_CONDITION_LIGHTNING_RAINY: ForecastConstants.TEMP_RANGE_LIGHTNING_RAINY,
            ATTR_CONDITION_FOG: ForecastConstants.TEMP_RANGE_FOG,  # Minimal range in fog
        }

        condition_range = condition_ranges.get(condition, base_range)

        # Atmospheric stability influence
        stability = meteorological_state["atmospheric_stability"]
        stability_factor = (
            ForecastConstants.TEMP_RANGE_STABILITY_BASE + stability
        )  # Stable air = larger range, unstable = smaller range
        condition_range *= stability_factor

        return max(
            ForecastConstants.MIN_TEMP_RANGE,
            min(ForecastConstants.MAX_TEMP_RANGE, condition_range),
        )
