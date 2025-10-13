"""Weather forecasting and prediction functions."""

from datetime import datetime, timedelta
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
    ATTR_CONDITION_WINDY,
)

from .weather_analysis import WeatherAnalysis
from .weather_utils import convert_to_celsius, convert_to_kmh


class WeatherForecast:
    """Handles weather forecasting and prediction algorithms."""

    def __init__(self, weather_analysis: WeatherAnalysis):
        """Initialize weather forecast with analysis instance.

        Args:
            weather_analysis: WeatherAnalysis instance for trend data
        """
        self.analysis = weather_analysis

    def generate_enhanced_forecast(
        self,
        current_condition: str,
        sensor_data: Dict[str, Any],
        altitude: float | None = 0.0,
    ) -> List[Dict[str, Any]]:
        """Generate an intelligent 5-day forecast using historical trends and patterns.

        Uses historical data, trend analysis, and meteorological patterns to create
        more accurate forecasts than simple rule-based approaches.

        Args:
            current_condition: Current weather condition
            sensor_data: Current sensor data in imperial units
            altitude: Altitude in meters above sea level for pressure threshold adjustment
        """
        forecast = []

        # Get comprehensive trend analysis with altitude correction
        pressure_analysis = self.analysis.analyze_pressure_trends(altitude)
        temp_patterns = self.analyze_temperature_patterns()
        humidity_trend = self.analysis.get_historical_trends("humidity", hours=24)
        wind_trend = self.analysis.get_historical_trends("wind_speed", hours=24)

        # Current baseline values
        current_temp = sensor_data.get("outdoor_temp", 70)
        current_humidity = sensor_data.get("humidity", 50)
        current_wind = sensor_data.get("wind_speed", 5)

        for i in range(5):
            date = datetime.now() + timedelta(days=i + 1)

            # Enhanced temperature forecasting using patterns and trends
            forecast_temp = self.forecast_temperature_enhanced(
                i, current_temp, temp_patterns, pressure_analysis
            )

            # Enhanced condition forecasting using multiple data sources
            forecast_condition = self.forecast_condition_enhanced(
                i, current_condition, pressure_analysis, sensor_data
            )

            # Enhanced precipitation forecasting
            precipitation = self.forecast_precipitation_enhanced(
                i, forecast_condition, pressure_analysis, humidity_trend, sensor_data
            )

            # Enhanced wind forecasting
            wind_forecast = self.forecast_wind_enhanced(
                i, current_wind, forecast_condition, wind_trend, pressure_analysis
            )

            # Calculate humidity forecast
            humidity_forecast = self.forecast_humidity(
                i, current_humidity, humidity_trend, forecast_condition
            )

            forecast.append(
                {
                    "datetime": date.isoformat(),
                    "temperature": round(convert_to_celsius(forecast_temp) or 20, 1),
                    "templow": round((convert_to_celsius(forecast_temp) or 20) - 6, 1),
                    "condition": forecast_condition,
                    "precipitation": precipitation,
                    "wind_speed": wind_forecast,
                    "humidity": humidity_forecast,
                }
            )

        return forecast

    def forecast_temperature_enhanced(
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
        seasonal_adjustment = self.calculate_seasonal_temperature_adjustment(day)
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

    def calculate_seasonal_temperature_adjustment(self, day: int) -> float:
        """Calculate seasonal temperature variation for forecasting."""
        # Simplified seasonal patterns (would be enhanced with actual seasonal data)
        # This is a basic implementation - could be enhanced with
        # astronomical calculations
        base_variation = [0, -1, 1, -0.5, 0.5][day]  # Day-to-day variation

        # Add some randomness based on typical weather patterns
        # In reality, this would use historical seasonal data
        return base_variation

    def forecast_condition_enhanced(
        self,
        day: int,
        current_condition: str,
        pressure_analysis: Dict[str, Any],
        sensor_data: Dict[str, Any],
    ) -> str:
        """Enhanced condition forecasting using cloud cover analysis with pressure trends.

        Uses the same cloud cover calculation methodology as current conditions,
        but adapted for forecast days with pressure trend projections.

        Args:
            day: Day ahead to forecast (0-4)
            current_condition: Current weather condition
            pressure_analysis: Pressure trend analysis
            sensor_data: Current sensor data

        Returns:
            str: Forecasted weather condition
        """
        # For near-term forecasts (day 0-1), use enhanced cloud cover analysis
        if day <= 1:
            return self._forecast_condition_with_cloud_cover(
                day, pressure_analysis, sensor_data
            )

        # For longer-term forecasts, fall back to pressure-based rules
        # but with cloud cover influence
        pressure_system = pressure_analysis.get("pressure_system", "normal")
        storm_probability = pressure_analysis.get("storm_probability", 0)

        # Get wind direction analysis for enhanced prediction
        wind_direction_analysis = self.analysis.analyze_wind_direction_trends()
        if wind_direction_analysis is None:
            direction_stability = 0.5
            significant_shift = False
        else:
            direction_stability = wind_direction_analysis.get(
                "direction_stability", 0.5
            )
            significant_shift = wind_direction_analysis.get("significant_shift", False)

        # Medium-term predictions (2 days)
        if day == 2:
            if storm_probability > 70:
                return ATTR_CONDITION_POURING
            elif storm_probability > 40:
                return (
                    ATTR_CONDITION_RAINY
                    if storm_probability < 70
                    else ATTR_CONDITION_LIGHTNING_RAINY
                )
            elif pressure_system == "high_pressure":
                if direction_stability > 0.8:
                    return ATTR_CONDITION_SUNNY
                else:
                    return ATTR_CONDITION_PARTLYCLOUDY
            elif pressure_system == "low_pressure":
                if significant_shift:
                    return ATTR_CONDITION_RAINY
                else:
                    return ATTR_CONDITION_CLOUDY
            else:
                # Default progression with some cloud cover influence
                return self._get_progressive_condition(current_condition, day)

        # Long-term predictions (3-4 days) - return to average conditions
        else:
            if pressure_system == "high_pressure" and direction_stability > 0.6:
                return ATTR_CONDITION_SUNNY
            elif pressure_system == "low_pressure" or significant_shift:
                return ATTR_CONDITION_CLOUDY
            else:
                return ATTR_CONDITION_PARTLYCLOUDY

    def _forecast_condition_with_cloud_cover(
        self,
        day: int,
        pressure_analysis: Dict[str, Any],
        sensor_data: Dict[str, Any],
    ) -> str:
        """Forecast condition using cloud cover analysis with pressure trend projections.

        Projects pressure trends forward and uses cloud cover calculations
        similar to current condition determination.

        Args:
            day: Day ahead to forecast (0-1 for near-term)
            pressure_analysis: Current pressure trend analysis
            sensor_data: Current sensor data

        Returns:
            str: Forecasted weather condition based on projected cloud cover
        """
        # Project pressure trends forward for forecast day
        projected_pressure_trends = self._project_pressure_trends_for_forecast(
            day, pressure_analysis
        )

        # Use current solar data but adjust for forecast day
        solar_radiation = sensor_data.get("solar_radiation", 0.0)
        solar_lux = sensor_data.get("solar_lux", 0.0)
        uv_index = sensor_data.get("uv_index", 0.0)

        # Check if solar data is available - if not, fall back to pressure-based estimation
        if solar_radiation is None or solar_lux is None or uv_index is None:
            cloud_cover = self._estimate_cloud_cover_from_pressure(pressure_analysis)
        else:
            # Adjust solar data for forecast day (less reliable further out)
            solar_reliability = max(0.3, 1.0 - (day * 0.3))  # Day 0: 100%, Day 1: 70%
            solar_radiation *= solar_reliability
            solar_lux *= solar_reliability
            uv_index *= solar_reliability

            # Estimate solar elevation for forecast time (simplified)
            # For day 0, use current elevation; for day 1, assume similar conditions
            solar_elevation = sensor_data.get("solar_elevation", 45.0)

            # Calculate projected cloud cover using enhanced analysis
            try:
                cloud_cover = self.analysis.analyze_cloud_cover(
                    solar_radiation,
                    solar_lux,
                    uv_index,
                    solar_elevation,
                    projected_pressure_trends,
                )
            except Exception:
                # Fallback to pressure-based estimation if cloud analysis fails
                cloud_cover = self._estimate_cloud_cover_from_pressure(
                    pressure_analysis
                )

        # Convert cloud cover to condition using same logic as current conditions
        return self.analysis._map_cloud_cover_to_condition(cloud_cover)

    def _project_pressure_trends_for_forecast(
        self,
        day: int,
        current_pressure_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Project pressure trends forward for forecast days.

        Extrapolates current pressure trends to estimate future pressure systems.

        Args:
            day: Days ahead to project (0-1)
            current_pressure_analysis: Current pressure trend analysis

        Returns:
            dict: Projected pressure trends for forecast day
        """
        # For near-term forecasts, pressure trends are relatively stable
        # but we can project some decay in trend strength

        projected_trends = current_pressure_analysis.copy()

        # Reduce trend magnitudes for future days (less certainty)
        trend_decay = max(0.5, 1.0 - (day * 0.2))  # Day 0: 100%, Day 1: 80%

        if "current_trend" in projected_trends:
            projected_trends["current_trend"] *= trend_decay
        if "long_term_trend" in projected_trends:
            projected_trends["long_term_trend"] *= trend_decay

        # Storm probability also decays with time
        if "storm_probability" in projected_trends:
            projected_trends["storm_probability"] *= trend_decay

        return projected_trends

    def _estimate_cloud_cover_from_pressure(
        self,
        pressure_analysis: Dict[str, Any],
    ) -> float:
        """Estimate cloud cover percentage from pressure analysis alone.

        Fallback method when solar data is insufficient for full cloud analysis.

        Args:
            pressure_analysis: Pressure trend analysis

        Returns:
            float: Estimated cloud cover percentage (0-100)
        """
        pressure_system = pressure_analysis.get("pressure_system", "normal")
        storm_probability = pressure_analysis.get("storm_probability", 0)

        # Base cloud cover by pressure system
        if pressure_system == "high_pressure":
            base_cloud_cover = 20.0  # Clear skies with high pressure
        elif pressure_system == "low_pressure":
            base_cloud_cover = 70.0  # Cloudy with low pressure
        else:
            base_cloud_cover = 40.0  # Partly cloudy normal pressure

        # Adjust by storm probability
        if storm_probability > 70:
            base_cloud_cover = min(95.0, base_cloud_cover + 25.0)
        elif storm_probability > 40:
            base_cloud_cover = min(85.0, base_cloud_cover + 15.0)
        elif storm_probability > 20:
            base_cloud_cover = min(75.0, base_cloud_cover + 10.0)

        return base_cloud_cover

    def _get_progressive_condition(self, current_condition: str, day: int) -> str:
        """Get progressive condition change for medium-term forecasts.

        Args:
            current_condition: Current weather condition
            day: Days ahead (2-4)

        Returns:
            str: Progressed weather condition
        """
        # Condition progression patterns (improving weather over time)
        condition_progression = {
            ATTR_CONDITION_LIGHTNING_RAINY: [
                ATTR_CONDITION_RAINY,
                ATTR_CONDITION_CLOUDY,
                ATTR_CONDITION_PARTLYCLOUDY,
            ],
            ATTR_CONDITION_RAINY: [
                ATTR_CONDITION_CLOUDY,
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_SUNNY,
            ],
            ATTR_CONDITION_POURING: [
                ATTR_CONDITION_RAINY,
                ATTR_CONDITION_CLOUDY,
                ATTR_CONDITION_PARTLYCLOUDY,
            ],
            ATTR_CONDITION_WINDY: [
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_SUNNY,
            ],
            ATTR_CONDITION_CLOUDY: [
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_SUNNY,
            ],
            ATTR_CONDITION_PARTLYCLOUDY: [
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_PARTLYCLOUDY,
            ],
            ATTR_CONDITION_SUNNY: [
                ATTR_CONDITION_SUNNY,
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_SUNNY,
            ],
            ATTR_CONDITION_FOG: [
                ATTR_CONDITION_CLOUDY,
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_SUNNY,
            ],
            ATTR_CONDITION_SNOWY: [
                ATTR_CONDITION_CLOUDY,
                ATTR_CONDITION_PARTLYCLOUDY,
                ATTR_CONDITION_SUNNY,
            ],
        }

        progression = condition_progression.get(
            current_condition, [ATTR_CONDITION_PARTLYCLOUDY]
        )
        # For days 2-4, use indices 0-2 of the progression
        progression_index = min(day - 2, len(progression) - 1)
        return progression[progression_index]

    def forecast_precipitation_enhanced(
        self,
        day: int,
        condition: str,
        pressure_analysis: Dict[str, Any],
        humidity_trend: Dict[str, Any],
        sensor_data: Dict[str, Any],
    ) -> float:
        """Enhanced precipitation forecasting using multiple data sources.

        Args:
            day: Day ahead to forecast (0-4)
            condition: Forecasted weather condition
            pressure_analysis: Pressure trend analysis
            humidity_trend: Historical humidity trends
            sensor_data: Current sensor data

        Returns:
            float: Precipitation amount in sensor units
        """
        base_precipitation = 0.0
        storm_probability = pressure_analysis.get("storm_probability", 0)

        # Base precipitation by condition (in mm)
        condition_precip = {
            ATTR_CONDITION_LIGHTNING_RAINY: 15.0,
            ATTR_CONDITION_POURING: 20.0,
            ATTR_CONDITION_RAINY: 5.0,
            ATTR_CONDITION_SNOWY: 3.0,
            ATTR_CONDITION_CLOUDY: 0.5,
            ATTR_CONDITION_FOG: 0.1,
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

        # Convert to sensor units if needed
        rain_rate_unit = sensor_data.get("rain_rate_unit")
        if (
            rain_rate_unit
            and isinstance(rain_rate_unit, str)
            and any(unit in rain_rate_unit.lower() for unit in ["in", "inch", "inches"])
        ):
            # Convert mm to in
            base_precipitation /= 25.4

        return round(base_precipitation, 2)

    def forecast_wind_enhanced(
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
        current_wind_kmh = convert_to_kmh(current_wind) or 10

        # Start with current wind speed as base
        forecast_wind = current_wind_kmh

        # Apply condition-based adjustments (not absolute values)
        condition_wind_adjustment = {
            ATTR_CONDITION_LIGHTNING_RAINY: 1.5,  # 50% increase for storms
            ATTR_CONDITION_POURING: 1.3,  # 30% increase for pouring rain
            ATTR_CONDITION_RAINY: 1.2,  # 20% increase for rain
            ATTR_CONDITION_WINDY: 2.0,  # 100% increase for windy
            ATTR_CONDITION_CLOUDY: 0.9,  # 10% decrease for clouds
            ATTR_CONDITION_PARTLYCLOUDY: 0.95,  # 5% decrease
            ATTR_CONDITION_SUNNY: 0.8,  # 20% decrease on clear days
            ATTR_CONDITION_FOG: 0.6,  # 40% decrease with fog
            ATTR_CONDITION_SNOWY: 1.1,  # 10% increase with snow
        }
        adjustment = condition_wind_adjustment.get(condition, 1.0)
        forecast_wind *= adjustment

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

    def forecast_humidity(
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
            ATTR_CONDITION_LIGHTNING_RAINY: 85,
            ATTR_CONDITION_POURING: 90,
            ATTR_CONDITION_RAINY: 80,
            ATTR_CONDITION_SNOWY: 75,
            ATTR_CONDITION_CLOUDY: 70,
            ATTR_CONDITION_PARTLYCLOUDY: 60,
            ATTR_CONDITION_SUNNY: 50,
            ATTR_CONDITION_WINDY: 55,  # Lower humidity with windy
            ATTR_CONDITION_FOG: 95,
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

    def analyze_temperature_patterns(self) -> Dict[str, Any]:
        """Analyze temperature patterns for forecasting.

        Returns:
            dict: Temperature pattern analysis including:
                - trend: Temperature trend over time
                - daily_variation: Typical daily temperature variation
                - seasonal_pattern: Seasonal temperature patterns
        """
        # Get temperature trends over different time periods
        short_trend = self.analysis.get_historical_trends("outdoor_temp", hours=6)
        long_trend = self.analysis.get_historical_trends("outdoor_temp", hours=24)

        if not short_trend or not long_trend:
            return {"trend": 0.0, "daily_variation": 10.0, "seasonal_pattern": "normal"}

        # Calculate overall trend
        overall_trend = long_trend.get("trend", 0.0)

        # Estimate daily variation from recent data
        daily_variation = long_trend.get("volatility", 10.0)

        # Determine seasonal pattern (simplified)
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:
            seasonal_pattern = "winter"
        elif current_month in [3, 4, 5]:
            seasonal_pattern = "spring"
        elif current_month in [6, 7, 8]:
            seasonal_pattern = "summer"
        else:
            seasonal_pattern = "fall"

        return {
            "trend": overall_trend,
            "daily_variation": daily_variation,
            "seasonal_pattern": seasonal_pattern,
        }
