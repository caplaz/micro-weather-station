"""Atmospheric pressure and fog analysis.

This module handles:
- Pressure altitude corrections
- Fog condition detection
- Pressure trend analysis
- Atmospheric stability calculations
"""

from collections import deque
from datetime import datetime, timedelta
import logging
import statistics
from typing import Any, Dict, List, Optional

from homeassistant.components.weather import ATTR_CONDITION_FOG

from ..meteorological_constants import FogThresholds

_LOGGER = logging.getLogger(__name__)


class AtmosphericAnalyzer:
    """Analyzes atmospheric conditions including pressure and fog."""

    def __init__(self, sensor_history: Optional[Dict[str, deque]] = None):
        """Initialize with sensor history.

        Args:
            sensor_history: Dictionary of sensor historical data deques
        """
        self._sensor_history = sensor_history or {}

    def adjust_pressure_for_altitude(
        self, pressure_inhg: float, altitude_m: Optional[float], pressure_type: str
    ) -> float:
        """Adjust pressure for altitude using barometric formula.

        Args:
            pressure_inhg: Pressure reading in inches of mercury
            altitude_m: Altitude in meters above sea level
            pressure_type: "relative" (station) or "atmospheric" (sea-level)

        Returns:
            Pressure adjusted to sea-level equivalent in inHg
        """
        altitude_m = altitude_m or 0.0

        if pressure_type == "atmospheric" or altitude_m == 0:
            return pressure_inhg

        # Convert to hPa for calculation
        pressure_hpa = pressure_inhg * 33.8639

        # Barometric formula constants
        L = 0.0065  # Temperature lapse rate (K/m)
        T0 = 288.15  # Standard temperature at sea level (K)
        g = 9.80665  # Gravitational acceleration (m/s²)
        M = 0.0289644  # Molar mass of air (kg/mol)
        R = 8.31432  # Universal gas constant (J/(mol·K))

        # Calculate exponent
        exponent = (g * M) / (R * L)

        # Calculate sea-level pressure
        if altitude_m > 0:
            sea_level_pressure_hpa = (
                pressure_hpa * (1 - (L * altitude_m) / T0) ** exponent
            )
        else:
            sea_level_pressure_hpa = pressure_hpa

        # Convert back to inHg
        return sea_level_pressure_hpa / 33.8639

    def get_altitude_adjusted_pressure_thresholds(
        self, altitude_m: Optional[float]
    ) -> Dict[str, float]:
        """Get pressure thresholds adjusted for altitude.

        Args:
            altitude_m: Altitude in meters above sea level

        Returns:
            Dictionary of pressure thresholds in inHg
        """
        altitude_m = altitude_m or 0.0

        # Base thresholds at sea level
        base_thresholds = {
            "very_high": 30.20,
            "high": 30.00,
            "normal_high": 30.20,
            "normal_low": 29.80,
            "low": 29.80,
            "very_low": 29.50,
            "extremely_low": 29.20,
        }

        if altitude_m == 0:
            return base_thresholds

        # Adjust for altitude (~1 hPa per 8 meters)
        altitude_adjustment_hpa = altitude_m / 8.0
        altitude_adjustment_inhg = altitude_adjustment_hpa / 33.8639

        # Apply adjustment
        adjusted_thresholds = {}
        for key, threshold_inhg in base_thresholds.items():
            adjusted_thresholds[key] = threshold_inhg - altitude_adjustment_inhg

        return adjusted_thresholds

    def analyze_fog_conditions(
        self,
        temp: float,
        humidity: float,
        dewpoint: float,
        spread: float,
        wind_speed: float,
        solar_rad: float,
        is_daytime: bool,
    ) -> Optional[str]:
        """Analyze atmospheric conditions for fog using scoring system.

        Uses meteorological principles:
        - High humidity (near-saturation)
        - Small temperature-dewpoint spread
        - Light winds (fog formation/persistence)
        - Reduced solar radiation (fog indicator)

        Args:
            temp: Temperature in Fahrenheit
            humidity: Relative humidity percentage
            dewpoint: Dewpoint temperature in Fahrenheit
            spread: Temperature minus dewpoint in Fahrenheit
            wind_speed: Wind speed in mph
            solar_rad: Solar radiation in W/m²
            is_daytime: Boolean indicating daytime

        Returns:
            ATTR_CONDITION_FOG if fog detected, None otherwise
        """
        fog_score = 0

        # 1. Humidity factor (0-40 points)
        if humidity >= FogThresholds.HUMIDITY_DENSE_FOG:
            fog_score += FogThresholds.SCORE_DENSE
        elif humidity >= FogThresholds.HUMIDITY_PROBABLE_FOG:
            fog_score += FogThresholds.SCORE_PROBABLE
        elif humidity >= FogThresholds.HUMIDITY_POSSIBLE_FOG:
            fog_score += FogThresholds.SCORE_POSSIBLE
        elif humidity >= FogThresholds.HUMIDITY_MARGINAL_FOG:
            fog_score += FogThresholds.SCORE_MARGINAL

        # 2. Temperature-dewpoint spread (0-30 points)
        if spread <= FogThresholds.SPREAD_SATURATED:
            fog_score += FogThresholds.SCORE_SPREAD_SATURATED
        elif spread <= FogThresholds.SPREAD_VERY_CLOSE:
            fog_score += FogThresholds.SCORE_SPREAD_VERY_CLOSE
        elif spread <= FogThresholds.SPREAD_CLOSE:
            fog_score += FogThresholds.SCORE_SPREAD_CLOSE
        elif spread <= FogThresholds.SPREAD_MARGINAL:
            fog_score += FogThresholds.SCORE_SPREAD_MARGINAL

        # 3. Wind factor (0-15 points)
        if wind_speed <= FogThresholds.WIND_CALM:
            fog_score += FogThresholds.SCORE_WIND_CALM
        elif wind_speed <= FogThresholds.WIND_LIGHT:
            fog_score += FogThresholds.SCORE_WIND_LIGHT
        elif wind_speed <= FogThresholds.WIND_MODERATE:
            fog_score += FogThresholds.SCORE_WIND_MODERATE
        else:
            fog_score += FogThresholds.PENALTY_WIND_STRONG

        # 4. Solar radiation factor (0-15 points)
        if is_daytime:
            if solar_rad < FogThresholds.SOLAR_VERY_LOW:
                fog_score += FogThresholds.SCORE_SOLAR_DENSE
            elif solar_rad < FogThresholds.SOLAR_LOW:
                fog_score += FogThresholds.SCORE_SOLAR_MODERATE
            elif solar_rad < FogThresholds.SOLAR_REDUCED:
                fog_score += FogThresholds.SCORE_SOLAR_LIGHT
        else:
            if solar_rad <= FogThresholds.SOLAR_MINIMAL_NIGHT:
                fog_score += FogThresholds.SCORE_SOLAR_NIGHT
            elif solar_rad <= FogThresholds.SOLAR_TWILIGHT:
                fog_score += FogThresholds.SCORE_SOLAR_TWILIGHT
            elif solar_rad <= FogThresholds.SOLAR_MODERATE_TWILIGHT:
                fog_score += 0
            else:
                fog_score += FogThresholds.PENALTY_SOLAR_STRONG

        # 5. Temperature factor (bonus for evaporation fog)
        if (
            temp > FogThresholds.TEMP_WARM_THRESHOLD
            and humidity >= FogThresholds.HUMIDITY_PROBABLE_FOG
            and spread <= FogThresholds.SPREAD_CLOSE
        ):
            fog_score += 5

        _LOGGER.debug(
            "Fog score: %.1f (humidity=%.1f%%, spread=%.2f°F, "
            "wind=%.1f mph, solar=%.1f W/m², temp=%.1f°F, daytime=%s)",
            fog_score,
            humidity,
            spread,
            wind_speed,
            solar_rad,
            temp,
            is_daytime,
        )

        # Determine fog based on score
        if fog_score >= FogThresholds.THRESHOLD_DENSE_FOG:
            _LOGGER.debug("Dense fog detected (score: %.1f)", fog_score)
            return ATTR_CONDITION_FOG
        elif fog_score >= FogThresholds.THRESHOLD_MODERATE_FOG:
            _LOGGER.debug("Moderate fog detected (score: %.1f)", fog_score)
            return ATTR_CONDITION_FOG
        elif fog_score >= FogThresholds.THRESHOLD_LIGHT_FOG:
            if humidity >= FogThresholds.HUMIDITY_PROBABLE_FOG:
                _LOGGER.debug("Light fog detected (score: %.1f)", fog_score)
                return ATTR_CONDITION_FOG

        _LOGGER.debug("No fog detected (score: %.1f)", fog_score)
        return None

    def analyze_wind_direction_trends(self) -> Dict[str, Any]:
        """Analyze wind direction trends for weather prediction.

        Returns:
            Dictionary with wind direction analysis
        """
        return self._analyze_wind_direction()

    def _analyze_wind_direction(self) -> Dict[str, Any]:
        """Analyze wind direction for weather prediction."""
        if "wind_direction" not in self._sensor_history:
            return {
                "direction_stability": 0.5,
                "direction_change_rate": 0.0,
                "significant_shift": False,
            }

        if not self._sensor_history["wind_direction"]:
            return {
                "direction_stability": 0.5,
                "direction_change_rate": 0.0,
                "significant_shift": False,
            }

        # Separate numeric and datetime timestamps to handle mixed data
        numeric_data = []
        datetime_data = []

        for entry in self._sensor_history["wind_direction"]:
            timestamp = entry["timestamp"]
            if isinstance(timestamp, (int, float)):
                numeric_data.append(entry)
            elif isinstance(timestamp, datetime):
                datetime_data.append(entry)

        # Prefer datetime data if we have enough, otherwise use numeric
        cutoff_time = datetime.now() - timedelta(hours=24)
        if datetime_data:
            recent_data = [
                entry for entry in datetime_data if entry["timestamp"] > cutoff_time
            ]
            is_numeric_timestamp = False
        elif numeric_data:
            recent_data = numeric_data
            is_numeric_timestamp = True
        else:
            return {
                "direction_stability": 0.5,
                "direction_change_rate": 0.0,
                "significant_shift": False,
            }

        if len(recent_data) < 3:
            return {
                "direction_stability": 0.5,
                "direction_change_rate": 0.0,
                "significant_shift": False,
            }

        directions = [entry["value"] for entry in recent_data]
        timestamps = [entry["timestamp"] for entry in recent_data]

        # Calculate stability
        try:
            volatility = statistics.stdev(directions) if len(directions) > 1 else 0
            stability = max(0.0, 1.0 - (volatility / 180.0))
        except statistics.StatisticsError:
            stability = 0.5

        # Calculate change rate
        direction_changes = []
        for i in range(1, len(directions)):
            change = self._calculate_angular_difference(
                directions[i - 1], directions[i]
            )
            direction_changes.append(change)

        # Calculate time span
        if is_numeric_timestamp:
            total_time_hours = float(timestamps[-1] - timestamps[0])
        else:
            total_time_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
        if total_time_hours > 0:
            avg_change_per_hour = (
                sum(abs(c) for c in direction_changes) / total_time_hours
            )
        else:
            avg_change_per_hour = 0.0

        # Detect significant shift
        recent_change = self._calculate_angular_difference(
            directions[0], directions[-1]
        )
        significant_shift = abs(recent_change) > 45

        return {
            "direction_stability": stability,
            "direction_change_rate": avg_change_per_hour,
            "significant_shift": significant_shift,
        }

    def _calculate_angular_difference(self, dir1: float, dir2: float) -> float:
        """Calculate smallest angular difference between two directions."""
        diff = (dir2 - dir1) % 360
        if diff > 180:
            diff -= 360
        return diff

    def _get_historical_trends(
        self, sensor_key: str, hours: int = 24
    ) -> Dict[str, Any]:
        """Get historical trends for a sensor."""
        if sensor_key not in self._sensor_history:
            return {}

        if sensor_key not in self._sensor_history:
            return {}

        if not self._sensor_history[sensor_key]:
            return {}

        # Separate numeric and datetime timestamps to handle mixed data
        numeric_data = []
        datetime_data = []

        for entry in self._sensor_history[sensor_key]:
            timestamp = entry["timestamp"]
            if isinstance(timestamp, (int, float)):
                numeric_data.append(entry)
            elif isinstance(timestamp, datetime):
                datetime_data.append(entry)

        # Prefer datetime data if we have enough, otherwise use numeric
        cutoff_time = datetime.now() - timedelta(hours=hours)
        if datetime_data:
            recent_data = [
                entry for entry in datetime_data if entry["timestamp"] > cutoff_time
            ]
            is_numeric_timestamp = False
        elif numeric_data:
            recent_data = numeric_data
            is_numeric_timestamp = True
        else:
            return {}

        if len(recent_data) < 2:
            return {}

        values = [entry["value"] for entry in recent_data]
        timestamps = [entry["timestamp"] for entry in recent_data]

        # Calculate time differences in hours
        if is_numeric_timestamp:
            # For numeric timestamps (testing), use values directly as hours
            time_diffs = [float(t - timestamps[0]) for t in timestamps]
        else:
            # For datetime timestamps, calculate time differences
            time_diffs = [
                (t - timestamps[0]).total_seconds() / 3600 for t in timestamps
            ]

        try:
            current = values[-1]
            average = statistics.mean(values)
            minimum = min(values)
            maximum = max(values)
            volatility = statistics.stdev(values) if len(values) > 1 else 0

            # Calculate trend (linear regression slope)
            trend = self._calculate_trend(time_diffs, values)

            return {
                "current": current,
                "average": average,
                "trend": trend,
                "min": minimum,
                "max": maximum,
                "volatility": volatility,
                "sample_count": len(values),
            }
        except statistics.StatisticsError:
            return {}

    def _calculate_trend(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate linear trend (slope) using simple linear regression."""
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
