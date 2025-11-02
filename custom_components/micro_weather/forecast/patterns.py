"""Historical pattern analysis for weather forecasting.

This module handles pattern recognition and analysis including:
- Historical weather pattern analysis
- Seasonal factor calculations
- Pressure cycle detection
- Weather correlations
"""

import logging
from typing import Any, Dict, Optional

from homeassistant.util import dt as dt_util

from ..analysis.trends import TrendsAnalyzer
from ..const import KEY_HUMIDITY, KEY_PRESSURE, KEY_TEMPERATURE

_LOGGER = logging.getLogger(__name__)


class PatternAnalyzer:
    """Analyzes historical weather patterns for forecasting."""

    def __init__(self, trends_analyzer: TrendsAnalyzer):
        """Initialize pattern analyzer.

        Args:
            trends_analyzer: TrendsAnalyzer instance for historical data
        """
        self.analysis = trends_analyzer

    def analyze_historical_patterns(self) -> Dict[str, Any]:
        """Analyze historical weather patterns for pattern recognition.

        Returns:
            Dictionary with comprehensive pattern analysis
        """
        # Get extended historical data (1 week)
        temp_history = self.analysis.get_historical_trends("outdoor_temp", hours=168)
        pressure_history = self.analysis.get_historical_trends(KEY_PRESSURE, hours=168)
        humidity_history = self.analysis.get_historical_trends(KEY_HUMIDITY, hours=168)

        # Pattern recognition - look for recurring patterns
        patterns: Dict[str, Any] = {}

        # Temperature patterns
        if temp_history:
            temp_volatility = temp_history.get("volatility", 5)
            temp_trend = temp_history.get("trend", 0)
            # Ensure temp_trend is a valid number before using in abs()
            if not isinstance(temp_trend, (int, float)):
                temp_trend = 0.0
            patterns[KEY_TEMPERATURE] = {
                "volatility": temp_volatility,
                "trend_strength": abs(temp_trend),
                "seasonal_factor": self.calculate_seasonal_factor(),
            }
            patterns["temperature_trend"] = temp_trend
            patterns["daily_temperature_variation"] = temp_volatility * 2

        # Seasonal pattern detection (only if we have historical data)
        if temp_history or pressure_history or humidity_history:
            month = dt_util.now().month
            if month in [12, 1, 2]:
                patterns["seasonal_pattern"] = "winter"
            elif month in [3, 4, 5]:
                patterns["seasonal_pattern"] = "spring"
            elif month in [6, 7, 8]:
                patterns["seasonal_pattern"] = "summer"
            elif month in [9, 10, 11]:
                patterns["seasonal_pattern"] = "fall"
            else:
                patterns["seasonal_pattern"] = "normal"
        else:
            patterns["seasonal_pattern"] = "normal"

        # Pressure patterns
        if pressure_history:
            pressure_volatility = pressure_history.get("volatility", 0.5)
            patterns[KEY_PRESSURE] = {
                "volatility": pressure_volatility,
                "cyclical_patterns": self.detect_pressure_cycles(pressure_history),
            }

        # Correlation analysis
        correlations = self.analyze_weather_correlations(
            temp_history, pressure_history, humidity_history
        )
        patterns["correlations"] = correlations

        return patterns

    def calculate_seasonal_factor(self) -> float:
        """Calculate seasonal temperature variation factor.

        Returns:
            Seasonal factor (0.3-0.9, higher = more variable weather)
        """
        month = dt_util.now().month
        # Simplified seasonal factors (0-1, higher = more variable)
        seasonal_factors = {
            12: 0.8,
            1: 0.9,
            2: 0.7,  # Winter - stable but cold
            3: 0.6,
            4: 0.5,
            5: 0.4,  # Spring - variable
            6: 0.3,
            7: 0.4,
            8: 0.5,  # Summer - relatively stable
            9: 0.6,
            10: 0.7,
            11: 0.8,  # Fall - variable
        }
        return seasonal_factors.get(month, 0.5)

    def detect_pressure_cycles(
        self, pressure_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect cyclical patterns in pressure data.

        Args:
            pressure_history: Historical pressure data with volatility

        Returns:
            Dictionary with detected cycle information
        """
        # Simplified cycle detection based on volatility
        volatility = pressure_history.get("volatility", 0.5)

        if volatility > 1.0:
            cycle_type = "active"  # Frequent system changes
        elif volatility > 0.5:
            cycle_type = "moderate"  # Normal system changes
        else:
            cycle_type = "stable"  # Persistent systems

        return {
            "cycle_type": cycle_type,
            "cycle_frequency": volatility * 2,  # Rough estimate of change frequency
        }

    def analyze_weather_correlations(
        self,
        temp_history: Optional[Dict[str, Any]],
        pressure_history: Optional[Dict[str, Any]],
        humidity_history: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Analyze correlations between weather variables.

        Args:
            temp_history: Temperature history data
            pressure_history: Pressure history data
            humidity_history: Humidity history data

        Returns:
            Dictionary of correlation coefficients
        """
        correlations = {}

        # Temperature-pressure correlation (simplified)
        if temp_history and pressure_history:
            temp_trend = temp_history.get("trend", 0)
            pressure_trend = pressure_history.get("trend", 0)
            # Ensure trends are valid numbers before using in abs()
            if not isinstance(temp_trend, (int, float)):
                temp_trend = 0.0
            if not isinstance(pressure_trend, (int, float)):
                pressure_trend = 0.0
            # Negative correlation often exists (high pressure = warm, low pressure = cool)
            correlations["temp_pressure"] = (
                -0.6 if abs(temp_trend) > 0 and abs(pressure_trend) > 0 else 0.0
            )

        # Temperature-humidity correlation
        if temp_history and humidity_history:
            temp_trend = temp_history.get("trend", 0)
            humidity_trend = humidity_history.get("trend", 0)
            # Ensure trends are valid numbers before using in abs()
            if not isinstance(temp_trend, (int, float)):
                temp_trend = 0.0
            if not isinstance(humidity_trend, (int, float)):
                humidity_trend = 0.0
            # Often inverse relationship in many climates
            correlations["temp_humidity"] = (
                -0.4 if abs(temp_trend) > 0 and abs(humidity_trend) > 0 else 0.0
            )

        return correlations
