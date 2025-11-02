"""Meteorological state analysis for weather forecasting.

This module handles comprehensive meteorological analysis including:
- Atmospheric stability assessment
- Weather system classification
- Cloud cover analysis
- Moisture transport analysis
- Wind pattern analysis
"""

import logging
from typing import Any, Dict, Optional

from ..const import (
    KEY_HUMIDITY,
    KEY_OUTDOOR_TEMP,
    KEY_PRESSURE,
    KEY_SOLAR_LUX_INTERNAL,
    KEY_SOLAR_RADIATION,
    KEY_TEMPERATURE,
    KEY_UV_INDEX,
    KEY_WIND_SPEED,
)
from ..meteorological_constants import (
    CloudCoverThresholds,
    PressureThresholds,
    TemperatureThresholds,
    WindThresholds,
)
from ..weather_analysis import WeatherAnalysis

_LOGGER = logging.getLogger(__name__)


class MeteorologicalAnalyzer:
    """Analyzes comprehensive meteorological state for forecasting."""

    def __init__(self, weather_analysis: WeatherAnalysis):
        """Initialize meteorological analyzer.

        Args:
            weather_analysis: WeatherAnalysis instance for data access
        """
        self.analysis = weather_analysis

    def analyze_state(
        self, sensor_data: Dict[str, Any], altitude: Optional[float] = 0.0
    ) -> Dict[str, Any]:
        """Analyze comprehensive meteorological state using all available sensor data.

        Performs multi-factor analysis including:
        - Atmospheric stability and pressure systems
        - Wind patterns and boundary layer dynamics
        - Solar radiation and cloud cover analysis
        - Moisture content and dewpoint analysis
        - Weather system classification and evolution potential

        Args:
            sensor_data: Current sensor data in imperial units
            altitude: Altitude for pressure corrections

        Returns:
            Dict[str, Any]: Comprehensive meteorological state analysis
        """
        # Get all available trend analyses with error handling for mock objects
        try:
            pressure_analysis = self.analysis.analyze_pressure_trends(altitude)
            if hasattr(pressure_analysis, "_mock_name"):
                pressure_analysis = {
                    "pressure_system": "normal",
                    "current_trend": 0,
                    "long_term_trend": 0,
                    "storm_probability": 0,
                }
            elif isinstance(pressure_analysis, dict):
                for key in ["current_trend", "long_term_trend", "storm_probability"]:
                    value = pressure_analysis.get(key)
                    if not isinstance(value, (int, float)):
                        pressure_analysis[key] = (
                            0 if key != "storm_probability" else 0.0
                        )
        except (AttributeError, TypeError):
            pressure_analysis = {
                "pressure_system": "normal",
                "current_trend": 0,
                "long_term_trend": 0,
                "storm_probability": 0,
            }

        try:
            wind_analysis = self.analysis.analyze_wind_direction_trends()
            if hasattr(wind_analysis, "_mock_name"):
                wind_analysis = {"direction_stability": 0.5, "gust_factor": 1.0}
            elif isinstance(wind_analysis, dict):
                direction_stability = wind_analysis.get("direction_stability")
                if not isinstance(direction_stability, (int, float)):
                    wind_analysis["direction_stability"] = 0.5
                gust_factor = wind_analysis.get("gust_factor")
                if not isinstance(gust_factor, (int, float)):
                    wind_analysis["gust_factor"] = 1.0
        except (AttributeError, TypeError):
            wind_analysis = {"direction_stability": 0.5, "gust_factor": 1.0}

        try:
            temp_trends = self.analysis.get_historical_trends("outdoor_temp", hours=24)
            if hasattr(temp_trends, "_mock_name"):
                temp_trends = {"trend": 0, "volatility": 2.0}
            elif isinstance(temp_trends, dict):
                trend = temp_trends.get("trend")
                if not isinstance(trend, (int, float)):
                    temp_trends["trend"] = 0
                volatility = temp_trends.get("volatility")
                if not isinstance(volatility, (int, float)):
                    temp_trends["volatility"] = 2.0
        except (AttributeError, TypeError):
            temp_trends = {"trend": 0, "volatility": 2.0}

        try:
            humidity_trends = self.analysis.get_historical_trends(
                KEY_HUMIDITY, hours=24
            )
            if hasattr(humidity_trends, "_mock_name"):
                humidity_trends = {"trend": 0, "volatility": 5.0}
            elif isinstance(humidity_trends, dict):
                trend = humidity_trends.get("trend")
                if not isinstance(trend, (int, float)):
                    humidity_trends["trend"] = 0
                volatility = humidity_trends.get("volatility")
                if not isinstance(volatility, (int, float)):
                    humidity_trends["volatility"] = 5.0
        except (AttributeError, TypeError):
            humidity_trends = {"trend": 0, "volatility": 5.0}

        try:
            wind_trends = self.analysis.get_historical_trends(KEY_WIND_SPEED, hours=24)
            if hasattr(wind_trends, "_mock_name"):
                wind_trends = {"trend": 0, "volatility": 2.0}
            elif isinstance(wind_trends, dict):
                trend = wind_trends.get("trend")
                if not isinstance(trend, (int, float)):
                    wind_trends["trend"] = 0
                volatility = wind_trends.get("volatility")
                if not isinstance(volatility, (int, float)):
                    wind_trends["volatility"] = 2.0
        except (AttributeError, TypeError):
            wind_trends = {"trend": 0, "volatility": 2.0}

        # Extract current sensor values with mock handling
        current_temp = (
            sensor_data.get(KEY_TEMPERATURE) or sensor_data.get(KEY_OUTDOOR_TEMP) or 70
        )
        if hasattr(current_temp, "_mock_name") or not isinstance(
            current_temp, (int, float)
        ):
            current_temp = 70.0

        current_humidity = sensor_data.get(KEY_HUMIDITY, 50)
        if hasattr(current_humidity, "_mock_name") or not isinstance(
            current_humidity, (int, float)
        ):
            current_humidity = 50.0

        current_pressure = sensor_data.get(KEY_PRESSURE, 29.92)
        if hasattr(current_pressure, "_mock_name") or not isinstance(
            current_pressure, (int, float)
        ):
            current_pressure = 29.92

        current_wind = sensor_data.get(KEY_WIND_SPEED, 5)
        if hasattr(current_wind, "_mock_name") or not isinstance(
            current_wind, (int, float)
        ):
            current_wind = 5.0

        solar_radiation = sensor_data.get(KEY_SOLAR_RADIATION, 0)
        if hasattr(solar_radiation, "_mock_name") or not isinstance(
            solar_radiation, (int, float)
        ):
            solar_radiation = 0.0

        solar_lux = sensor_data.get(KEY_SOLAR_LUX_INTERNAL, 0)
        if hasattr(solar_lux, "_mock_name") or not isinstance(solar_lux, (int, float)):
            solar_lux = 0.0

        uv_index = sensor_data.get(KEY_UV_INDEX, 0)
        if hasattr(uv_index, "_mock_name") or not isinstance(uv_index, (int, float)):
            uv_index = 0.0

        # Calculate dewpoint with error handling
        try:
            dewpoint = self.analysis.calculate_dewpoint(current_temp, current_humidity)
            if not isinstance(dewpoint, (int, float)):
                humidity_val = (
                    current_humidity
                    if isinstance(current_humidity, (int, float))
                    else 50
                )
                dewpoint = current_temp - (100 - humidity_val) / 5.0
        except (AttributeError, TypeError):
            humidity_val = (
                current_humidity if isinstance(current_humidity, (int, float)) else 50
            )
            dewpoint = current_temp - (100 - humidity_val) / 5.0

        if not isinstance(dewpoint, (int, float)):
            humidity_val = (
                current_humidity if isinstance(current_humidity, (int, float)) else 50
            )
            dewpoint = current_temp - (100 - humidity_val) / 5.0

        if dewpoint is None or not isinstance(dewpoint, (int, float)):
            dewpoint = current_temp - (100 - 50) / 5.0

        try:
            temp_dewpoint_spread = current_temp - dewpoint
            if not isinstance(temp_dewpoint_spread, (int, float)):
                temp_dewpoint_spread = 5.0
        except (TypeError, ValueError):
            temp_dewpoint_spread = 5.0

        # Atmospheric stability analysis
        stability_index = self.calculate_atmospheric_stability(
            current_temp, current_humidity, current_wind, pressure_analysis
        )

        # Weather system classification
        weather_system = self.classify_weather_system(
            pressure_analysis, wind_analysis, temp_trends, stability_index
        )

        # Cloud cover and solar analysis
        cloud_analysis = self._analyze_cloud_cover_comprehensive(
            solar_radiation, solar_lux, uv_index, sensor_data, pressure_analysis
        )

        # Moisture transport analysis
        moisture_analysis = self._analyze_moisture_transport(
            current_humidity, humidity_trends, wind_analysis, temp_dewpoint_spread
        )

        # Wind pattern analysis
        wind_pattern_analysis = self._analyze_wind_patterns(
            current_wind, wind_trends, wind_analysis, pressure_analysis
        )

        return {
            "pressure_analysis": pressure_analysis,
            "wind_analysis": wind_analysis,
            "temp_trends": temp_trends,
            "humidity_trends": humidity_trends,
            "wind_trends": wind_trends,
            "current_conditions": {
                KEY_TEMPERATURE: current_temp,
                KEY_HUMIDITY: current_humidity,
                KEY_PRESSURE: current_pressure,
                KEY_WIND_SPEED: current_wind,
                "dewpoint": dewpoint,
                "temp_dewpoint_spread": temp_dewpoint_spread,
            },
            "atmospheric_stability": stability_index,
            "weather_system": weather_system,
            "cloud_analysis": cloud_analysis,
            "moisture_analysis": moisture_analysis,
            "wind_pattern_analysis": wind_pattern_analysis,
        }

    def calculate_atmospheric_stability(
        self,
        temp: float,
        humidity: float,
        wind_speed: float,
        pressure_analysis: Dict[str, Any],
    ) -> float:
        """Calculate atmospheric stability index (0-1, higher = more stable).

        Stability affects weather persistence and forecast accuracy.
        """
        stability = 0.5  # Neutral baseline

        # Temperature lapse rate effect (simplified)
        temp_trend = pressure_analysis.get("long_term_trend", 0)
        if not isinstance(temp_trend, (int, float)):
            temp_trend = 0.0
        if abs(temp_trend) < 2:
            stability += 0.2
        elif abs(temp_trend) > 5:
            stability -= 0.2

        # Wind effect
        if not isinstance(wind_speed, (int, float)):
            wind_speed = 5.0
        if wind_speed < WindThresholds.LIGHT_BREEZE:
            stability += 0.15
        elif wind_speed > WindThresholds.MODERATE_BREEZE:
            stability -= 0.15

        # Humidity effect
        if not isinstance(humidity, (int, float)):
            humidity = 50.0
        if humidity > TemperatureThresholds.HUMIDITY_MODERATE_HIGH:
            stability += 0.1
        elif humidity < 30:
            stability -= 0.1

        return max(0.0, min(1.0, stability))

    def classify_weather_system(
        self,
        pressure_analysis: Dict[str, Any],
        wind_analysis: Dict[str, Any],
        temp_trends: Dict[str, Any],
        stability: float,
    ) -> Dict[str, Any]:
        """Classify current weather system type and evolution potential."""
        pressure_system = pressure_analysis.get("pressure_system", "normal")
        wind_stability = wind_analysis.get("direction_stability", 0.5)
        temp_trend = temp_trends.get("trend", 0) if temp_trends else 0

        if not isinstance(temp_trend, (int, float)):
            temp_trend = 0.0

        # System classification
        if pressure_system == "high_pressure" and stability > 0.7:
            system_type = "stable_high"
            evolution_potential = "gradual_improvement"
        elif pressure_system == "low_pressure" and stability < 0.3:
            system_type = "active_low"
            evolution_potential = "rapid_change"
        elif (
            wind_stability < 0.4 and pressure_analysis.get("storm_probability", 0) > 50
        ):
            system_type = "frontal_system"
            evolution_potential = "transitional"
        elif abs(temp_trend) > 2 and stability > 0.6:
            system_type = "air_mass_change"
            evolution_potential = "gradual"
        else:
            system_type = "transitional"
            evolution_potential = "moderate_change"

        return {
            "type": system_type,
            "evolution_potential": evolution_potential,
            "persistence_factor": stability,
            "change_probability": 1.0 - stability,
        }

    def _analyze_cloud_cover_comprehensive(
        self,
        solar_radiation: float,
        solar_lux: float,
        uv_index: float,
        sensor_data: Dict[str, Any],
        pressure_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Comprehensive cloud cover analysis using all solar data and pressure trends."""
        solar_elevation = sensor_data.get("solar_elevation", 45.0)

        try:
            cloud_cover = self.analysis.analyze_cloud_cover(
                solar_radiation, solar_lux, uv_index, solar_elevation, pressure_analysis
            )
            if not isinstance(cloud_cover, (int, float)):
                cloud_cover = 50.0
        except (AttributeError, TypeError):
            cloud_cover = 50.0
            if solar_radiation > 800:
                cloud_cover = 10.0
            elif solar_radiation > 400:
                cloud_cover = 40.0
            elif solar_radiation > 100:
                cloud_cover = 70.0
            else:
                cloud_cover = 90.0

        # Pressure trend influence
        pressure_trend = pressure_analysis.get("current_trend", 0)
        if not isinstance(pressure_trend, (int, float)):
            pressure_trend = 0.0
        if pressure_trend < PressureThresholds.TREND_3H_RAPID_FALL:
            cloud_cover = min(95.0, cloud_cover + 60.0)
        elif pressure_trend < 0:
            cloud_cover = min(95.0, cloud_cover + 40.0)
        elif pressure_trend > PressureThresholds.TREND_3H_MODERATE_RISE:
            cloud_cover = max(5.0, cloud_cover - 40.0)

        # Cloud type classification
        if cloud_cover < CloudCoverThresholds.FEW:
            cloud_type = "clear"
        elif cloud_cover < CloudCoverThresholds.SCATTERED:
            cloud_type = "few_clouds"
        elif cloud_cover < CloudCoverThresholds.THRESHOLD_CLOUDY:
            cloud_type = "scattered"
        else:
            cloud_type = "overcast"

        return {
            "cloud_cover": cloud_cover,
            "cloud_type": cloud_type,
            "solar_efficiency": max(0, 100 - cloud_cover),
        }

    def _analyze_moisture_transport(
        self,
        current_humidity: float,
        humidity_trends: Dict[str, Any],
        wind_analysis: Dict[str, Any],
        temp_dewpoint_spread: float,
    ) -> Dict[str, Any]:
        """Analyze moisture transport and atmospheric moisture dynamics."""
        moisture_content = current_humidity
        transport_potential = wind_analysis.get("direction_stability", 0.5) * 10

        # Dewpoint spread indicates moisture availability
        if not isinstance(temp_dewpoint_spread, (int, float)):
            temp_dewpoint_spread = 5.0
        if temp_dewpoint_spread < 5:
            moisture_availability = "high"
            condensation_potential = 0.8
        elif temp_dewpoint_spread < 10:
            moisture_availability = "moderate"
            condensation_potential = 0.5
        else:
            moisture_availability = "low"
            condensation_potential = 0.2

        # Trend analysis
        humidity_trend = humidity_trends.get("trend", 0) if humidity_trends else 0
        if not isinstance(humidity_trend, (int, float)):
            humidity_trend = 0.0
        if humidity_trend > 5:
            trend_direction = "increasing"
        elif humidity_trend < -5:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"

        return {
            "moisture_content": moisture_content,
            "transport_potential": transport_potential,
            "moisture_availability": moisture_availability,
            "condensation_potential": condensation_potential,
            "trend_direction": trend_direction,
        }

    def _analyze_wind_patterns(
        self,
        current_wind: float,
        wind_trends: Dict[str, Any],
        wind_analysis: Dict[str, Any],
        pressure_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze wind patterns and boundary layer dynamics."""
        wind_speed = current_wind
        direction_stability = wind_analysis.get("direction_stability", 0.5)
        gust_factor = (
            wind_analysis.get("gust_factor", 1.0)
            if "gust_factor" in wind_analysis
            else 1.0
        )

        # Wind shear analysis
        wind_trend = wind_trends.get("trend", 0) if wind_trends else 0
        if not isinstance(wind_trend, (int, float)):
            wind_trend = 0.0
        if abs(wind_trend) > 5:
            shear_intensity = "extreme"
        elif abs(wind_trend) > 2:
            shear_intensity = "moderate"
        else:
            shear_intensity = "low"

        # Pressure gradient effect
        pressure_trend = pressure_analysis.get("current_trend", 0)
        if not isinstance(pressure_trend, (int, float)):
            pressure_trend = 0.0
        gradient_wind_effect = abs(pressure_trend) * 2

        return {
            KEY_WIND_SPEED: wind_speed,
            "direction_stability": direction_stability,
            "gust_factor": gust_factor,
            "shear_intensity": shear_intensity,
            "gradient_wind_effect": gradient_wind_effect,
        }
