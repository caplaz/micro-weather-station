"""Weather analysis and trend calculation functions.

BACKWARD COMPATIBILITY MODULE - This module now serves as a proxy to the refactored
analysis modules. All functionality has been reorganized into specialized modules:
- analysis.core: Core weather condition determination
- analysis.atmospheric: Pressure and fog analysis
- analysis.solar: Solar radiation and cloud cover
- analysis.trends: Historical data trends

This module maintains the original WeatherAnalysis class interface for
backward compatibility with existing code.
"""

from collections import deque
from typing import Any, Dict, Optional

from .analysis.atmospheric import AtmosphericAnalyzer
from .analysis.core import WeatherConditionAnalyzer
from .analysis.solar import SolarAnalyzer
from .analysis.trends import TrendsAnalyzer
from .const import DEFAULT_ZENITH_MAX_RADIATION


class WeatherAnalysis:
    """Handles weather condition analysis and historical trend calculations.

    This class now serves as a facade/proxy to the refactored analyzer modules,
    maintaining the original API for backward compatibility while delegating
    to specialized components.
    """

    def __init__(
        self,
        sensor_history: Optional[Dict[str, deque[Dict[str, Any]]]] = None,
        zenith_max_radiation: float = DEFAULT_ZENITH_MAX_RADIATION,
    ):
        """Initialize weather analysis with optional sensor history.

        Args:
            sensor_history: Dictionary of sensor historical data deques
            zenith_max_radiation: Maximum solar radiation at zenith (W/m2) for calibration
        """
        self._sensor_history = sensor_history or {}
        self.zenith_max_radiation = zenith_max_radiation

        # Initialize specialized analyzers
        self.atmospheric = AtmosphericAnalyzer(self._sensor_history)
        self.solar = SolarAnalyzer(self._sensor_history, zenith_max_radiation)
        self.trends = TrendsAnalyzer(self._sensor_history)
        self.core = WeatherConditionAnalyzer(self.atmospheric, self.solar)

    # Core weather condition methods - delegate to core analyzer
    def determine_weather_condition(
        self, sensor_data: Dict[str, Any], altitude: Optional[float] = 0.0
    ) -> str:
        """Determine weather condition from sensor data.

        Args:
            sensor_data: Dictionary of current sensor readings
            altitude: Altitude in meters for pressure correction

        Returns:
            Weather condition string
        """
        return self.core.determine_condition(sensor_data, altitude)

    def calculate_dewpoint(self, temp_f: float, humidity: Optional[float]) -> float:
        """Calculate dewpoint using Magnus formula.

        Args:
            temp_f: Temperature in Fahrenheit
            humidity: Relative humidity as percentage

        Returns:
            Dewpoint temperature in Fahrenheit
        """
        return self.core.calculate_dewpoint(temp_f, humidity)

    def classify_precipitation_intensity(self, rain_rate: float) -> str:
        """Classify precipitation intensity.

        Args:
            rain_rate: Rain rate in inches/hour or mm/hour

        Returns:
            Intensity classification
        """
        return self.core.classify_precipitation_intensity(rain_rate)

    def estimate_visibility(self, condition: str, sensor_data: Dict[str, Any]) -> float:
        """Estimate visibility based on weather condition.

        Args:
            condition: Current weather condition
            sensor_data: Current sensor readings

        Returns:
            Estimated visibility in kilometers
        """
        return self.core.estimate_visibility(condition, sensor_data)

    # Atmospheric methods - delegate to atmospheric analyzer
    def adjust_pressure_for_altitude(
        self, pressure_inhg: float, altitude_m: Optional[float], pressure_type: str
    ) -> float:
        """Adjust pressure for altitude using barometric formula.

        Args:
            pressure_inhg: Pressure reading in inches of mercury
            altitude_m: Altitude in meters above sea level
            pressure_type: "relative" (station) or "atmospheric" (sea-level)

        Returns:
            Pressure adjusted to sea-level equivalent
        """
        return self.atmospheric.adjust_pressure_for_altitude(
            pressure_inhg, altitude_m, pressure_type
        )

    def get_altitude_adjusted_pressure_thresholds(
        self, altitude_m: Optional[float]
    ) -> Dict[str, float]:
        """Get pressure thresholds adjusted for altitude.

        Args:
            altitude_m: Altitude in meters above sea level

        Returns:
            Dictionary of pressure thresholds in inHg
        """
        return self.atmospheric.get_altitude_adjusted_pressure_thresholds(altitude_m)

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
        """Analyze atmospheric conditions for fog.

        Args:
            temp: Temperature in Fahrenheit
            humidity: Relative humidity percentage
            dewpoint: Dewpoint temperature in Fahrenheit
            spread: Temperature minus dewpoint in Fahrenheit
            wind_speed: Wind speed in mph
            solar_rad: Solar radiation in W/m2
            is_daytime: Boolean indicating daytime

        Returns:
            ATTR_CONDITION_FOG if fog detected, None otherwise
        """
        return self.atmospheric.analyze_fog_conditions(
            temp, humidity, dewpoint, spread, wind_speed, solar_rad, is_daytime
        )

    def analyze_pressure_trends(
        self, altitude: Optional[float] = 0.0
    ) -> Dict[str, Any]:
        """Analyze pressure trends for weather prediction.

        Args:
            altitude: Altitude in meters for pressure thresholds

        Returns:
            Dictionary with pressure analysis
        """
        return self.atmospheric.analyze_pressure_trends(altitude)

    def analyze_wind_direction_trends(self) -> Dict[str, Any]:
        """Analyze wind direction trends for weather prediction.

        Returns:
            Dictionary with wind direction analysis
        """
        return self.atmospheric._analyze_wind_direction()

    # Solar methods - delegate to solar analyzer
    def analyze_cloud_cover(
        self,
        solar_radiation: float,
        solar_lux: float,
        uv_index: float,
        solar_elevation: float = 45.0,
        pressure_trends: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Estimate cloud cover percentage using solar radiation.

        Args:
            solar_radiation: Current solar radiation in W/m2
            solar_lux: Current solar illuminance in lux
            uv_index: Current UV index value
            solar_elevation: Solar elevation angle in degrees
            pressure_trends: Optional pressure trend analysis

        Returns:
            Estimated cloud cover percentage (0-100)
        """
        return self.solar.analyze_cloud_cover(
            solar_radiation, solar_lux, uv_index, solar_elevation, pressure_trends
        )

    # Trends methods - delegate to trends analyzer
    def store_historical_data(
        self, sensor_data: Dict[str, Any], weather_condition: Optional[str] = None
    ) -> None:
        """Store current sensor readings in historical buffer.

        Args:
            sensor_data: Current sensor readings to store
            weather_condition: Current weather condition (optional)
        """
        self.trends.store_historical_data(sensor_data, weather_condition)

    def get_historical_trends(self, sensor_key: str, hours: int = 24) -> Dict[str, Any]:
        """Calculate historical trends for a sensor.

        Args:
            sensor_key: The sensor key to analyze
            hours: Number of hours to look back

        Returns:
            Dictionary with trend analysis
        """
        return self.trends.get_historical_trends(sensor_key, hours)

    def calculate_trend(self, x_values: list[float], y_values: list[float]) -> float:
        """Calculate linear trend (slope) using simple linear regression.

        Args:
            x_values: Independent variable values (time)
            y_values: Dependent variable values (sensor readings)

        Returns:
            Slope of the trend line
        """
        return self.trends.calculate_trend(x_values, y_values)

    # Additional helper methods for backward compatibility
    def get_altitude_adjusted_pressure_thresholds_hpa(
        self, altitude: float
    ) -> Dict[str, float]:
        """Get pressure thresholds in hPa adjusted for altitude.

        Args:
            altitude: Altitude in meters above sea level

        Returns:
            Dictionary of pressure thresholds in hPa
        """
        return self.atmospheric._get_altitude_adjusted_thresholds_hpa(altitude)

    def calculate_circular_mean(self, directions: list[float]) -> float:
        """Calculate the circular mean of wind directions.

        Args:
            directions: List of wind directions in degrees (0-360)

        Returns:
            Circular mean direction in degrees
        """
        return self.trends.calculate_circular_mean(directions)

    def calculate_angular_difference(self, dir1: float, dir2: float) -> float:
        """Calculate the smallest angular difference between two directions.

        Args:
            dir1: First direction in degrees
            dir2: Second direction in degrees

        Returns:
            Angular difference in degrees (-180 to +180)
        """
        return self.atmospheric._calculate_angular_difference(dir1, dir2)

    def calculate_prevailing_direction(self, directions: list[float]) -> str:
        """Determine the prevailing wind direction sector.

        Args:
            directions: List of wind directions in degrees

        Returns:
            Prevailing direction as cardinal direction
        """
        return self.trends.calculate_prevailing_direction(directions)

    def get_historical_weather_bias(self, hours: int = 6) -> Dict[str, Any]:
        """Calculate historical weather bias for low-elevation adjustments.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary with bias analysis
        """
        return self.solar._get_historical_weather_bias(hours)
