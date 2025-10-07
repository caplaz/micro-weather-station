"""Weather analysis and trend calculation functions."""

from collections import deque
from datetime import datetime, timedelta
import logging
import math
import statistics
from typing import Any, Dict, List, Optional

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

_LOGGER = logging.getLogger(__name__)


class WeatherAnalysis:
    """Handles weather condition analysis and historical trend calculations."""

    def __init__(
        self, sensor_history: Optional[Dict[str, deque[Dict[str, Any]]]] = None
    ):
        """Initialize weather analysis with optional sensor history.

        Args:
            sensor_history: Dictionary of sensor historical data deques
        """
        self._sensor_history = sensor_history or {}

    def determine_weather_condition(
        self, sensor_data: Dict[str, Any], altitude: float | None = 0.0
    ) -> str:
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

        # Default altitude to 0.0 if None
        altitude = altitude or 0.0

        # Calculate derived meteorological parameters
        # Use dewpoint sensor if available, otherwise calculate from temp/humidity
        dewpoint_raw = sensor_data.get("dewpoint")
        if dewpoint_raw is not None:
            dewpoint = float(dewpoint_raw)
        else:
            dewpoint = self.calculate_dewpoint(outdoor_temp, humidity)
        temp_dewpoint_spread = outdoor_temp - dewpoint
        is_freezing = outdoor_temp <= 32.0

        # Advanced daytime detection (solar elevation proxy)
        is_daytime = solar_radiation > 5 or solar_lux > 50 or uv_index > 0.1
        is_twilight = (solar_lux > 10 and solar_lux < 100) or (
            solar_radiation > 1 and solar_radiation < 50
        )

        # Pressure analysis (meteorologically accurate thresholds)
        # Adjust pressure for altitude and pressure type
        adjusted_pressure = self.adjust_pressure_for_altitude(
            pressure, altitude, "relative"
        )
        pressure_thresholds = self.get_altitude_adjusted_pressure_thresholds(altitude)

        pressure_very_high = adjusted_pressure > pressure_thresholds["very_high"]
        pressure_high = adjusted_pressure > pressure_thresholds["high"]
        pressure_normal = (
            pressure_thresholds["normal_low"]
            <= adjusted_pressure
            <= pressure_thresholds["normal_high"]
        )
        pressure_low = adjusted_pressure < pressure_thresholds["low"]
        pressure_very_low = adjusted_pressure < pressure_thresholds["very_low"]
        pressure_extremely_low = (
            adjusted_pressure < pressure_thresholds["extremely_low"]
        )

        # Enhanced wind analysis (Beaufort scale adapted with turbulence detection)
        wind_calm = wind_speed < 1  # 0-1 mph: Calm
        wind_light = 1 <= wind_speed < 8  # 1-7 mph: Light air to light breeze
        wind_strong = 19 <= wind_speed < 32  # 19-31 mph: Strong breeze to near gale
        wind_gale = wind_speed >= 32  # 32+ mph: Gale force

        # Enhanced gust analysis for better storm detection
        gust_factor = wind_gust / max(wind_speed, 1)  # Gust ratio for turbulence
        is_gusty = gust_factor > 1.5 and wind_gust > 10
        is_very_gusty = gust_factor > 2.0 and wind_gust > 15

        # Severe turbulence indicator (suggests thunderstorm activity)
        is_severe_turbulence = (gust_factor > 3.0 and wind_gust > 20) or wind_gust > 40

        # PRIORITY 1: ACTIVE PRECIPITATION (Highest Priority)
        # First check if we have clear precipitation indicators
        significant_rain = rain_rate > 0.01

        # If rain_state is "wet" but no significant rain_rate, check if
        # it might be fog first
        if rain_state == "wet" and not significant_rain:
            # Check for fog conditions before assuming precipitation
            fog_conditions = self.analyze_fog_conditions(
                outdoor_temp,
                humidity,
                dewpoint,
                temp_dewpoint_spread,
                wind_speed,
                solar_radiation,
                is_daytime,
            )
            if fog_conditions is not None:
                # PRIORITY 1A: FOG CONDITIONS (when moisture sensor shows
                # wet but it's fog)
                return fog_conditions

        # Now check for precipitation (either significant rain_rate OR wet
        # sensor without fog conditions)
        if significant_rain or rain_state == "wet":
            precipitation_intensity = self.classify_precipitation_intensity(rain_rate)

            # Determine precipitation type based on temperature
            if is_freezing:
                # Snow conditions (temperature at or below freezing)
                return ATTR_CONDITION_SNOWY

            # Enhanced storm detection with turbulence analysis
            # Only trigger for significant storm conditions with meaningful precipitation
            if (
                pressure_extremely_low  # Severe storm pressure (< 29.20 inHg)
                or (
                    pressure_very_low and wind_strong and rain_rate > 0.1
                )  # Storm pressure + strong winds + moderate+ rain
                or (
                    pressure_very_low and is_very_gusty and rain_rate > 0.25
                )  # Storm pressure + very gusty + heavy rain
                or (
                    is_severe_turbulence and rain_rate > 0.05
                )  # Severe wind turbulence + any precipitation (thunderstorm indicator)
            ):
                return ATTR_CONDITION_LIGHTNING_RAINY  # Thunderstorm/severe weather

            # Regular rain classification
            if precipitation_intensity == "heavy" or rain_rate > 0.25:
                return ATTR_CONDITION_POURING  # Heavy rain
            elif precipitation_intensity == "moderate" or rain_rate > 0.1:
                return ATTR_CONDITION_RAINY  # Moderate rain
            else:
                return ATTR_CONDITION_RAINY  # Light rain/drizzle

        # PRIORITY 2: SEVERE WEATHER CONDITIONS
        # (No precipitation but extreme conditions suggesting thunderstorm activity)
        if (
            pressure_extremely_low and (wind_strong or is_very_gusty)
        ) or is_severe_turbulence:  # Enhanced: severe turbulence indicates thunderstorm
            return ATTR_CONDITION_LIGHTNING  # Dry thunderstorm or severe weather system

        if wind_gale:  # Gale force winds
            return ATTR_CONDITION_WINDY  # Windstorm

        # PRIORITY 2.5: WINDY CONDITIONS
        # (Gusty or strong winds without precipitation)
        if is_very_gusty or wind_strong:
            return ATTR_CONDITION_WINDY  # Windy conditions

        # PRIORITY 3: FOG CONDITIONS (Critical for safety)
        # Check for fog in dry conditions (wet conditions already checked above)
        if rain_state != "wet":
            fog_conditions = self.analyze_fog_conditions(
                outdoor_temp,
                humidity,
                dewpoint,
                temp_dewpoint_spread,
                wind_speed,
                solar_radiation,
                is_daytime,
            )
            if fog_conditions is not None:
                return fog_conditions

        # PRIORITY 4: DAYTIME CONDITIONS (Solar radiation analysis)
        if is_daytime:
            # Get solar elevation from sensor data for accurate cloud cover calculation
            # If solar_elevation is missing, check if we have solar sensor data
            solar_elevation = sensor_data.get("solar_elevation")
            has_solar_data = solar_radiation > 0 or solar_lux > 0 or uv_index > 0

            # If we have solar data but no elevation, use a reasonable default
            # If we have neither, fall back to atmospheric analysis
            if solar_elevation is None:
                if has_solar_data:
                    solar_elevation = (
                        45.0  # Default when we have solar data but no elevation
                    )
                else:
                    # No solar data and no elevation - use atmospheric fallback
                    _LOGGER.debug(
                        "Solar sensors and elevation unavailable during daytime - "
                        "using atmospheric fallback analysis"
                    )
                    # Use atmospheric conditions for weather determination
                    if humidity < 50 and temp_dewpoint_spread > 10:
                        return ATTR_CONDITION_SUNNY
                    elif humidity < 70 and temp_dewpoint_spread > 5 and pressure_normal:
                        return ATTR_CONDITION_SUNNY
                    elif pressure_high and humidity < 75:
                        return ATTR_CONDITION_SUNNY
                    elif pressure_low and humidity < 80:
                        return ATTR_CONDITION_PARTLYCLOUDY
                    elif humidity >= 85:
                        return ATTR_CONDITION_CLOUDY
                    else:
                        return ATTR_CONDITION_PARTLYCLOUDY

            cloud_cover = self.analyze_cloud_cover(
                solar_radiation, solar_lux, uv_index, solar_elevation
            )

            # Daytime clear sky conditions: low cloud cover = sunny
            if cloud_cover <= 40:
                return ATTR_CONDITION_SUNNY
            elif cloud_cover <= 60:
                return ATTR_CONDITION_PARTLYCLOUDY
            elif cloud_cover <= 85:
                return ATTR_CONDITION_CLOUDY
            else:
                # Very overcast (cloud_cover > 85%)
                return ATTR_CONDITION_CLOUDY

        # PRIORITY 5: TWILIGHT CONDITIONS
        elif is_twilight:
            if solar_lux > 50 and pressure_normal:
                return ATTR_CONDITION_PARTLYCLOUDY
            else:
                return ATTR_CONDITION_CLOUDY

        # PRIORITY 6: NIGHTTIME CONDITIONS
        else:
            # Night analysis based on atmospheric conditions
            # Prioritize clear conditions when pressure is favorable, even with moderate humidity
            # Order conditions from most specific to least specific

            # Most specific: Combined conditions
            if pressure_low and humidity > 90 and wind_speed < 3:
                return ATTR_CONDITION_CLOUDY  # Low pressure + very high humidity + calm = cloudy

            # Clear night conditions (favorable pressure/humidity combinations)
            elif pressure_very_high and wind_calm and humidity < 70:
                return ATTR_CONDITION_CLEAR_NIGHT  # Perfect clear night
            elif pressure_high and not is_gusty and humidity < 80:
                return ATTR_CONDITION_CLEAR_NIGHT  # Clear night
            elif pressure_low and humidity < 65:
                return ATTR_CONDITION_CLEAR_NIGHT  # Low pressure, low humidity = clear

            # Partly cloudy night (moderate conditions)
            elif pressure_normal and wind_light and humidity < 85:
                return ATTR_CONDITION_PARTLYCLOUDY  # Partly cloudy night (moderate humidity OK)
            elif pressure_low and humidity < 90:
                return (
                    ATTR_CONDITION_PARTLYCLOUDY  # Low pressure with moderate humidity
                )

            # Cloudy night (high humidity)
            elif humidity > 90:
                return ATTR_CONDITION_CLOUDY  # Very high humidity = likely cloudy/overcast night

            # Default night condition
            else:
                return ATTR_CONDITION_PARTLYCLOUDY  # Default night condition

        # FALLBACK: Should rarely be reached
        return ATTR_CONDITION_PARTLYCLOUDY

    def adjust_pressure_for_altitude(
        self, pressure_inhg: float, altitude_m: float | None, pressure_type: str
    ) -> float:
        """Adjust pressure thresholds based on altitude and pressure type.

        This method corrects pressure readings for altitude effects:
        - If pressure_type is "atmospheric", assumes the sensor already
          provides sea-level pressure
        - If pressure_type is "relative", converts station pressure to sea-level equivalent

        Uses the barometric formula for accurate altitude correction.

        Args:
            pressure_inhg: Pressure reading in inches of mercury
            altitude_m: Altitude in meters above sea level
            pressure_type: "relative" (station pressure) or
            "atmospheric" (sea-level pressure)

        Returns:
            float: Pressure adjusted to sea-level equivalent in inches
            of mercury
        """
        altitude_m = altitude_m or 0.0  # Default to 0.0 if None

        if pressure_type == "atmospheric" or altitude_m == 0:
            # Already sea-level pressure or at sea level
            return pressure_inhg

        # Convert station pressure to sea-level pressure using barometric formula
        # P0 = P * (1 - (L * h) / T0)^(g * M / (R * L))
        # Where:
        # P0 = sea level pressure
        # P = station pressure
        # h = altitude in meters
        # L = temperature lapse rate (0.0065 K/m)
        # T0 = standard temperature at sea level (288.15 K)
        # g = gravitational acceleration (9.80665 m/s²)
        # M = molar mass of air (0.0289644 kg/mol)
        # R = universal gas constant (8.31432 J/(mol·K))

        # Convert pressure from inHg to hPa for calculation
        pressure_hpa = pressure_inhg * 33.8639

        # Standard atmospheric constants
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
        sea_level_pressure_inhg = sea_level_pressure_hpa / 33.8639

        return sea_level_pressure_inhg

    def get_altitude_adjusted_pressure_thresholds(
        self, altitude_m: float | None
    ) -> Dict[str, float]:
        """Get pressure thresholds adjusted for altitude.

        Pressure systems behave differently at various altitudes. This method
        adjusts the standard sea-level pressure thresholds to account for
        the thinner atmosphere at higher elevations.

        Args:
            altitude_m: Altitude in meters above sea level

        Returns:
            dict: Altitude-adjusted pressure thresholds in inches of mercury
        """
        altitude_m = altitude_m or 0.0  # Default to 0.0 if None

        # Base thresholds at sea level (inHg)
        base_thresholds = {
            "very_high": 30.20,  # High pressure system
            "high": 30.00,  # Above normal
            "normal_high": 30.20,  # Upper normal range
            "normal_low": 29.80,  # Lower normal range
            "low": 29.80,  # Low pressure system
            "very_low": 29.50,  # Storm system
            "extremely_low": 29.20,  # Severe storm
        }

        if altitude_m == 0:
            return base_thresholds

        # Adjust thresholds based on altitude
        # At higher altitudes, pressure is naturally lower, so thresholds need adjustment
        # Using approximate barometric formula: pressure decreases by ~1 hPa per 8 meters
        altitude_adjustment_hpa = altitude_m / 8.0  # Approximate hPa reduction
        altitude_adjustment_inhg = altitude_adjustment_hpa / 33.8639  # Convert to inHg

        # Apply altitude adjustment (reduce thresholds at higher altitudes)
        adjusted_thresholds = {}
        for key, threshold_inhg in base_thresholds.items():
            adjusted_thresholds[key] = threshold_inhg - altitude_adjustment_inhg

        return adjusted_thresholds

    def calculate_dewpoint(self, temp_f: float, humidity: float) -> float:
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

    def classify_precipitation_intensity(self, rain_rate: float) -> str:
        """Classify precipitation intensity (meteorological standards)."""
        if rain_rate >= 0.5:
            return "heavy"  # Heavy rain
        elif rain_rate >= 0.1:
            return "moderate"  # Moderate rain
        elif rain_rate >= 0.01:
            return "light"  # Light rain/drizzle
        else:
            return "trace"  # Trace amounts

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
        """Advanced fog analysis using meteorological principles.

        Analyzes atmospheric conditions to determine fog likelihood using
        scientific criteria for fog formation. The algorithm considers:

        - Humidity levels (fog requires near-saturation)
        - Temperature-dewpoint spread (closer = higher fog probability)
        - Wind speed (light winds favor fog formation)
        - Solar radiation (low radiation indicates existing fog)
        - Time of day (radiation fog typically forms at night/early morning)
        - Dawn/twilight conditions (prevent false fog detection during sunrise/sunset)

        Fog Types Detected:
        - Dense fog: Extremely high humidity (99%+) with minimal spread AND very low solar radiation
        - Radiation fog: High humidity (98%+) with light winds at night AND no solar radiation
        - Advection fog: Moist air moving over cooler surface
        - Evaporation fog: After rain with warm ground

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
            Uses conservative thresholds to reduce false positives. Special handling
            for dawn/twilight conditions when solar radiation is present but low,
            which indicates sunrise/sunset rather than fog.
        """

        # Detect dawn/twilight conditions (solar radiation present but sun is low)
        # During dawn/twilight: 5-100 W/m² with increasing light = not fog
        is_twilight = 5 < solar_rad < 100

        # If we're in twilight with any meaningful solar radiation,
        # require much stricter conditions for fog detection
        if is_twilight:
            _LOGGER.debug(
                "Twilight conditions detected (solar_rad: %.1f W/m²) - "
                "humidity: %.1f%%, spread: %.1f°F, wind: %.1f mph",
                solar_rad,
                humidity,
                spread,
                wind_speed,
            )
            # During twilight, only detect fog if conditions are extreme
            # AND solar radiation is very suppressed (indicating actual fog blocking light)
            if humidity >= 99.8 and spread <= 0.5 and solar_rad < 15:
                # Dense fog blocking twilight sun
                _LOGGER.debug("Extreme fog conditions during twilight - reporting fog")
                return ATTR_CONDITION_FOG
            # Otherwise, it's just high humidity during dawn/dusk - not fog
            _LOGGER.debug(
                "Twilight with high humidity but not fog - skipping fog detection"
            )
            return None

        # Adjust thresholds based on time of day
        if not is_daytime:
            # True nighttime (no solar radiation): More restrictive thresholds
            dense_humidity_threshold = 99.5
            radiation_humidity_threshold = 99.5  # Increased from 99
            radiation_spread_threshold = (
                0.5  # Decreased from 1.0 - require very tight spread
            )
            advection_humidity_threshold = 98
        else:
            # Daytime: Original thresholds
            dense_humidity_threshold = 99
            radiation_humidity_threshold = 98
            radiation_spread_threshold = 2
            advection_humidity_threshold = 95

        # Dense fog conditions (extremely restrictive, requires
        # virtually no solar radiation at night)
        if (
            humidity >= dense_humidity_threshold
            and spread <= 0.5  # Very tight spread
            and wind_speed <= 2
            and solar_rad <= 2  # Essentially no solar radiation
        ):
            return ATTR_CONDITION_FOG

        # Radiation fog (only in true darkness - no solar radiation at all)
        if (
            humidity >= radiation_humidity_threshold
            and spread <= radiation_spread_threshold
            and wind_speed <= 3
            and solar_rad <= 2
        ):
            return ATTR_CONDITION_FOG

        # Advection fog (moist air over cooler surface) - also requires low solar radiation
        if (
            humidity >= advection_humidity_threshold
            and spread <= 3
            and 3 <= wind_speed <= 12
            and solar_rad < 10  # Added solar radiation check
        ):
            return ATTR_CONDITION_FOG

        # Evaporation fog (after rain, warm ground) - requires low solar radiation
        if (
            humidity >= advection_humidity_threshold
            and spread <= 3
            and wind_speed <= 6
            and temp > 40
            and solar_rad < 10  # Added solar radiation check
        ):
            return ATTR_CONDITION_FOG

        return None

    def analyze_cloud_cover(
        self,
        solar_radiation: float,
        solar_lux: float,
        uv_index: float,
        solar_elevation: float = 45.0,
    ) -> float:
        """
        Estimate cloud cover percentage using solar radiation analysis.

        Uses advanced astronomical calculations for accurate clear-sky maximums:
        - Solar constant variation throughout the year
        - Air mass correction for atmospheric path length
        - Atmospheric extinction (Rayleigh scattering, ozone absorption)
        - Elevation-based scaling with scientific accuracy

        Args:
            solar_radiation: Current solar radiation in W/m²
            solar_lux: Current solar illuminance in lux
            uv_index: Current UV index value
            solar_elevation: Solar elevation angle in degrees from sun.sun sensor
                           (defaults to 45° if not configured)

        Returns:
            float: Estimated cloud cover percentage (0-100)
        """

        # Use moving average of solar radiation to filter temporary fluctuations
        # like passing clouds, while still responding to genuine weather changes
        avg_solar_radiation = self._get_solar_radiation_average(solar_radiation)

        # Handle very low solar radiation cases more intelligently
        # Very low values during daytime indicate heavy overcast conditions
        if avg_solar_radiation < 200 and solar_lux < 20000 and uv_index < 1:
            # If all solar measurements are extremely low, it indicates heavy clouds
            if avg_solar_radiation < 50 and solar_lux < 5000 and uv_index == 0:
                return 85.0  # Heavy overcast conditions
            elif avg_solar_radiation < 100 and solar_lux < 10000:
                return 70.0  # Mostly cloudy conditions
            else:
                return 40.0  # Partly cloudy when data is inconclusive

        # Calculate theoretical clear-sky maximum using astronomical principles
        max_solar_radiation = self._calculate_clear_sky_max_radiation(solar_elevation)

        # Calculate lux maximum (roughly 100-150 lux per W/m² depending on spectrum)
        # Use 120 lx/W/m² as a reasonable average
        max_solar_lux = max_solar_radiation * 120

        # UV index maximum scales with solar elevation and air mass
        # UV is more sensitive to elevation and atmospheric path than total radiation
        air_mass = self._calculate_air_mass(solar_elevation)
        max_uv_index = max(
            0.5, 12 * math.exp(-0.05 * air_mass)
        )  # Exponential decay with air mass

        # Calculate cloud cover from each measurement using realistic maximums
        radiation_ratio = avg_solar_radiation / max_solar_radiation
        cloud_cover_reduction = radiation_ratio * 100
        solar_cloud_cover = max(0, min(100, 100 - cloud_cover_reduction))
        lux_cloud_cover = max(0, min(100, 100 - (solar_lux / max_solar_lux * 100)))
        uv_cloud_cover = max(0, min(100, 100 - (uv_index / max_uv_index * 100)))

        # Weight the measurements (solar radiation is most reliable for cloud cover)
        if avg_solar_radiation > 10:  # Only use if we have meaningful solar data
            # Only include UV in weighting if we have a meaningful UV reading
            if uv_index > 0:
                cloud_cover = (
                    solar_cloud_cover * 0.8
                    + lux_cloud_cover * 0.15
                    + uv_cloud_cover * 0.05
                )
            else:
                # No UV data - redistribute weights to solar and lux
                cloud_cover = solar_cloud_cover * 0.85 + lux_cloud_cover * 0.15
        elif solar_lux > 1000:  # Fallback to lux if radiation is low
            cloud_cover = (
                lux_cloud_cover * 0.9 + uv_cloud_cover * 0.1
                if uv_index > 0
                else lux_cloud_cover
            )
        elif uv_index > 0.5:  # Last resort
            cloud_cover = uv_cloud_cover
        elif avg_solar_radiation == 0 and solar_lux == 0 and uv_index == 0:
            # No solar input at all - assume complete overcast (night or very cloudy)
            cloud_cover = 100
        else:
            cloud_cover = 50  # Unknown - assume partly cloudy

        return cloud_cover

    def _get_solar_radiation_average(self, current_radiation: float) -> float:
        """
        Calculate moving average of solar radiation to filter temporary fluctuations.

        Uses recent historical data to smooth out short-term variations like
        passing clouds, while still responding to genuine weather changes.
        This prevents rapid condition changes due to brief solar interruptions.

        Args:
            current_radiation: Current solar radiation reading in W/m²

        Returns:
            float: Averaged solar radiation value
        """
        if "solar_radiation" not in self._sensor_history:
            return current_radiation

        # Get readings from the last 15 minutes (assuming 1-minute update intervals)
        # This provides ~15 readings for averaging while being responsive to changes
        cutoff_time = datetime.now() - timedelta(minutes=15)
        recent_readings = [
            entry["value"]
            for entry in self._sensor_history["solar_radiation"]
            if entry["timestamp"] > cutoff_time and entry["value"] > 0
        ]

        # Need at least 3 readings for meaningful averaging
        if len(recent_readings) < 3:
            return current_radiation

        # Calculate weighted average favoring recent readings
        # Give more weight to recent values to remain responsive
        weights = []
        for i in range(len(recent_readings)):
            # Linear weighting: most recent = 1.0, oldest = 0.3
            weight = 0.3 + (0.7 * i / (len(recent_readings) - 1))
            weights.append(weight)

        weighted_sum = sum(
            value * weight for value, weight in zip(recent_readings, weights)
        )
        total_weight = sum(weights)

        if total_weight > 0:
            averaged_radiation = weighted_sum / total_weight
            _LOGGER.debug(
                "Solar radiation average: %.1f W/m² "
                "(from %d readings, current: %.1f)",
                averaged_radiation,
                len(recent_readings),
                current_radiation,
            )
            return averaged_radiation

        return current_radiation

    def _calculate_clear_sky_max_radiation(
        self, solar_elevation: float, current_date: datetime | None = None
    ) -> float:
        """
        Calculate theoretical clear-sky maximum solar radiation using astronomical principles.

        This method computes the maximum possible solar irradiance under clear sky conditions
        by accounting for:
        - Solar constant variation throughout the year (Earth-Sun distance)
        - Air mass correction for atmospheric path length
        - Atmospheric extinction (Rayleigh scattering, ozone absorption, water vapor)
        - Local calibration factor for your specific location/setup

        Args:
            solar_elevation: Solar elevation angle in degrees
            current_date: Optional datetime to use for seasonal calculations (for testing)

        Returns:
            float: Theoretical clear-sky maximum solar radiation in W/m²
        """
        if solar_elevation <= 0:
            return 50.0  # Minimum value for very low elevation

        # Get current date for seasonal calculations
        now = current_date if current_date is not None else datetime.now()
        day_of_year = now.timetuple().tm_yday

        # 1. Solar constant variation (Earth-Sun distance)
        # The solar constant varies by ±3.3% throughout the year due to elliptical orbit
        # Day 4 (Jan 4) = closest to sun, Day 183-184 (Jun 21-22) = farthest
        solar_constant_variation = 1 + 0.033 * math.cos(
            2 * math.pi * (day_of_year - 4) / 365.25
        )
        base_solar_constant = 1366.0  # W/m² (standard solar constant at 1 AU)

        _LOGGER.debug(
            "Date: %s, day_of_year: %d, solar_constant_variation: %.4f",
            now,
            day_of_year,
            solar_constant_variation,
        )

        # 2. Air mass calculation
        air_mass = self._calculate_air_mass(solar_elevation)

        # 3. Atmospheric extinction correction
        # Rayleigh scattering: ~0.1 per air mass
        # Ozone absorption: ~0.02 per air mass
        # Water vapor absorption: ~0.05 per air mass (typical mid-latitude)
        # Aerosol scattering: ~0.1 per air mass (typical clear conditions)
        rayleigh_extinction = math.exp(-0.1 * air_mass)
        ozone_extinction = math.exp(-0.02 * air_mass)
        water_vapor_extinction = math.exp(-0.05 * air_mass)
        aerosol_extinction = math.exp(-0.1 * air_mass)  # Clear sky assumption

        # Combined atmospheric transmission
        atmospheric_transmission = (
            rayleigh_extinction
            * ozone_extinction
            * water_vapor_extinction
            * aerosol_extinction
        )

        # 4. Calculate theoretical clear-sky irradiance
        theoretical_irradiance = (
            base_solar_constant
            * solar_constant_variation
            * atmospheric_transmission
            * math.sin(math.radians(solar_elevation))  # Elevation correction
        )

        # 5. Apply local calibration factor
        # This accounts for your specific location, sensor calibration, and typical
        # atmospheric conditions
        # We use 700 W/m² as the calibrated maximum at zenith (90° elevation) as
        # requested, then apply astronomical corrections for the current solar
        # elevation
        zenith_max_radiation = 700.0  # Your calibrated maximum at zenith

        # Calculate the astronomical scaling factor (what fraction of zenith
        # irradiance we should expect)
        astronomical_zenith_max = (
            base_solar_constant * solar_constant_variation * atmospheric_transmission
        )
        astronomical_scaling = (
            theoretical_irradiance / astronomical_zenith_max
            if astronomical_zenith_max > 0
            else 1.0
        )

        # Apply astronomical scaling to your calibrated zenith maximum
        # Include seasonal solar constant variation in the final calculation
        calibrated_max_radiation = (
            zenith_max_radiation * solar_constant_variation * astronomical_scaling
        )

        # Ensure reasonable bounds
        calibrated_max_radiation = max(50.0, min(1200.0, calibrated_max_radiation))

        _LOGGER.debug(
            "Clear-sky max radiation: %.1f W/m² "
            "(elevation: %.1f°, air_mass: %.3f, "
            "zenith_max: %.1f, astronomical_scaling: %.3f)",  # noqa: E501
            calibrated_max_radiation,
            solar_elevation,
            air_mass,
            zenith_max_radiation,
            astronomical_scaling,
        )

        return calibrated_max_radiation

    def _calculate_air_mass(self, solar_elevation: float) -> float:
        """
        Calculate air mass for solar radiation calculations.

        Air mass is the path length through the atmosphere relative to the path
        when the sun is directly overhead (zenith). It accounts for the increased
        atmospheric absorption at lower solar elevations.

        Uses the Kasten-Young air mass formula for improved accuracy at low elevations.

        Args:
            solar_elevation: Solar elevation angle in degrees

        Returns:
            float: Air mass (dimensionless, ≥ 1.0)
        """
        if solar_elevation <= 0:
            return 38.0  # Very large air mass for sun below horizon

        # Convert elevation to zenith angle
        zenith_angle = 90.0 - solar_elevation
        zenith_rad = math.radians(zenith_angle)

        # Kasten-Young formula (more accurate than simple 1/cos for low elevations)
        # AM = 1 / (cos(Z) + 0.50572 * (96.07995 - Z)^(-1.6364))
        air_mass = 1.0 / (
            math.cos(zenith_rad) + 0.50572 * math.pow(96.07995 - zenith_angle, -1.6364)
        )

        # Ensure minimum air mass of 1.0 (zenith)
        return max(1.0, air_mass)

    def estimate_visibility(self, condition: str, sensor_data: Dict[str, Any]) -> float:
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
        dewpoint = self.calculate_dewpoint(outdoor_temp, humidity)
        temp_dewpoint_spread = outdoor_temp - dewpoint

        is_daytime = solar_radiation > 5 or solar_lux > 50

        if condition == ATTR_CONDITION_FOG:
            # Fog visibility based on density (dewpoint spread)
            if temp_dewpoint_spread <= 1:
                return 0.3  # Dense fog: <0.5 km
            elif temp_dewpoint_spread <= 2:
                return 0.8  # Thick fog: <1 km
            elif temp_dewpoint_spread <= 3:
                return 1.5  # Moderate fog: 1-2 km
            else:
                return 2.5  # Light fog/mist: 2-3 km

        elif condition in [ATTR_CONDITION_RAINY, ATTR_CONDITION_SNOWY]:
            # Precipitation visibility reduction
            base_visibility = 15.0 if condition == ATTR_CONDITION_RAINY else 8.0

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

        elif condition == ATTR_CONDITION_LIGHTNING_RAINY:
            # Storm visibility varies greatly
            if rain_rate > 0.1:  # Rain with storm
                storm_vis = 3.0 - (rain_rate * 2)
            else:  # Dry storm (dust, debris)
                storm_vis = 8.0 - (wind_gust / 10)
            return round(max(0.8, storm_vis), 1)

        elif condition == ATTR_CONDITION_CLEAR_NIGHT:
            # Excellent night visibility
            if humidity < 50:
                return 25.0  # Very clear, dry air
            elif humidity < 70:
                return 20.0  # Clear
            else:
                return 15.0  # Slight haze

        elif condition == ATTR_CONDITION_SUNNY:
            # Daytime clear conditions
            if solar_radiation > 800:  # Very clear atmosphere
                return 30.0
            elif solar_radiation >= 600:  # Clear
                return 25.0
            elif solar_radiation > 400:  # Good
                return 20.0
            else:  # Hazy
                return 15.0

        elif condition in [ATTR_CONDITION_PARTLYCLOUDY, ATTR_CONDITION_CLOUDY]:
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

    def store_historical_data(self, sensor_data: Dict[str, Any]) -> None:
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

    def get_historical_trends(self, sensor_key: str, hours: int = 24) -> Dict[str, Any]:
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
            trend = self.calculate_trend(time_diffs, values)

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

    def calculate_trend(self, x_values: List[float], y_values: List[float]) -> float:
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

    def analyze_pressure_trends(self, altitude: float | None = 0.0) -> Dict[str, Any]:
        """Analyze pressure trends for weather prediction.

        Args:
            altitude: Altitude in meters above sea level for threshold adjustment

        Returns:
            dict: Pressure trend analysis including:
                - current_trend: Short-term pressure change
                - long_term_trend: 24-hour pressure trend
                - pressure_system: Type of pressure system
                - storm_probability: Probability of storm development
        """
        altitude = altitude or 0.0  # Default to 0.0 if None
        # Get pressure trends over different time periods
        short_trend = self.get_historical_trends("pressure", hours=3)  # 3-hour trend
        long_trend = self.get_historical_trends("pressure", hours=24)  # 24-hour trend

        if not short_trend or not long_trend:
            return {"pressure_system": "unknown", "storm_probability": 0.0}

        current_pressure = long_trend["current"]
        short_term_change = short_trend["trend"] * 3  # 3-hour change
        long_term_change = long_trend["trend"] * 24  # 24-hour change

        # Get altitude-adjusted pressure thresholds
        pressure_thresholds = self.get_altitude_adjusted_pressure_thresholds(altitude)

        # Classify pressure system using altitude-adjusted thresholds
        if current_pressure > pressure_thresholds["very_high"]:
            pressure_system = "high_pressure"
        elif current_pressure < pressure_thresholds["low"]:
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

        # Very low pressure indicates storm (using altitude-adjusted threshold)
        if current_pressure < pressure_thresholds["very_low"]:
            storm_probability += 30

        # Incorporate wind direction analysis for enhanced storm prediction
        wind_direction_analysis = self.analyze_wind_direction_trends()
        direction_stability = wind_direction_analysis.get("direction_stability", 0.5)
        significant_shift = wind_direction_analysis.get("significant_shift", False)
        direction_change_rate = wind_direction_analysis.get(
            "direction_change_rate", 0.0
        )

        # Wind direction changes can indicate approaching weather systems
        if significant_shift:
            # Major wind direction shift often precedes weather changes
            storm_probability += 15

        # Rapid wind direction changes with pressure drops = strong storm signal
        if direction_change_rate > 30 and (
            short_term_change < -1 or long_term_change < -3
        ):
            storm_probability += 20

        # Unstable winds with low pressure = increased storm probability
        if direction_stability < 0.3 and pressure_system == "low_pressure":
            storm_probability += 10

        # Cap storm probability
        storm_probability = min(100.0, storm_probability)

        return {
            "current_trend": short_term_change,
            "long_term_trend": long_term_change,
            "pressure_system": pressure_system,
            "storm_probability": storm_probability,
        }

    def analyze_wind_direction_trends(self) -> Dict[str, Any]:
        """Analyze wind direction trends for weather prediction.

        Wind direction analysis is complex due to circular nature (0-360°).
        This method handles direction changes that may indicate approaching
        weather systems or changing weather patterns.

        Returns:
            dict: Wind direction trend analysis including:
                - average_direction: Mean wind direction in degrees
                - direction_stability: How consistent direction has been (0-1)
                - direction_change_rate: Rate of direction change in °/hour
                - significant_shift: Boolean indicating major direction change
                - prevailing_direction: Most common direction sector
        """
        # Get wind direction trends over different time periods
        short_trend = self.get_historical_trends(
            "wind_direction", hours=6
        )  # 6-hour trend
        long_trend = self.get_historical_trends(
            "wind_direction", hours=24
        )  # 24-hour trend

        if not short_trend or not long_trend:
            return {
                "average_direction": None,
                "direction_stability": 0.0,
                "direction_change_rate": 0.0,
                "significant_shift": False,
                "prevailing_direction": "unknown",
            }

        # Get recent wind direction data for detailed analysis
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_data = [
            entry
            for entry in self._sensor_history["wind_direction"]
            if entry["timestamp"] > cutoff_time
        ]

        if len(recent_data) < 3:
            return {
                "average_direction": long_trend["current"],
                "direction_stability": 0.0,
                "direction_change_rate": 0.0,
                "significant_shift": False,
                "prevailing_direction": "unknown",
            }

        directions = [entry["value"] for entry in recent_data]
        timestamps = [entry["timestamp"] for entry in recent_data]

        # Calculate average direction (circular mean)
        avg_direction = self.calculate_circular_mean(directions)

        # Calculate direction stability (lower volatility = more stable)
        stability = max(0.0, 1.0 - (long_trend.get("volatility", 0) / 180.0))

        # Calculate direction change rate
        if len(directions) >= 2:
            # Calculate angular differences (handling wraparound)
            direction_changes = []
            for i in range(1, len(directions)):
                change = self.calculate_angular_difference(
                    directions[i - 1], directions[i]
                )
                direction_changes.append(change)

            # Average change per hour
            total_time_hours = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
            if total_time_hours > 0:
                avg_change_per_hour = (
                    sum(abs(c) for c in direction_changes) / total_time_hours
                )
            else:
                avg_change_per_hour = 0.0
        else:
            avg_change_per_hour = 0.0

        # Detect significant direction shift (rapid change > 45° in 6 hours)
        significant_shift = False
        if len(directions) >= 2:
            recent_change = self.calculate_angular_difference(
                directions[0], directions[-1]
            )
            if abs(recent_change) > 45:  # More than 45° change in 24 hours
                significant_shift = True

        # Determine prevailing direction (most common 90° sector)
        prevailing_direction = self.calculate_prevailing_direction(directions)

        return {
            "average_direction": avg_direction,
            "direction_stability": stability,
            "direction_change_rate": avg_change_per_hour,
            "significant_shift": significant_shift,
            "prevailing_direction": prevailing_direction,
        }

    def calculate_circular_mean(self, directions: List[float]) -> float:
        """Calculate the circular mean of wind directions.

        Args:
            directions: List of wind directions in degrees (0-360)

        Returns:
            float: Circular mean direction in degrees
        """
        if not directions:
            return 0.0

        # Convert to radians
        radians = [math.radians(d) for d in directions]

        # Calculate circular mean
        sin_sum = sum(math.sin(r) for r in radians)
        cos_sum = sum(math.cos(r) for r in radians)

        mean_radians = math.atan2(sin_sum, cos_sum)

        # Convert back to degrees (0-360)
        mean_degrees = math.degrees(mean_radians) % 360

        return mean_degrees

    def calculate_angular_difference(self, dir1: float, dir2: float) -> float:
        """Calculate the smallest angular difference between two directions.

        Args:
            dir1: First direction in degrees
            dir2: Second direction in degrees

        Returns:
            float: Angular difference in degrees (-180 to +180)
        """
        diff = (dir2 - dir1) % 360
        if diff > 180:
            diff -= 360
        return diff

    def calculate_prevailing_direction(self, directions: List[float]) -> str:
        """Determine the prevailing wind direction sector.

        Args:
            directions: List of wind directions in degrees

        Returns:
            str: Prevailing direction as cardinal direction
        """
        if not directions:
            return "unknown"

        # Count directions in each 90° sector
        sectors = {
            "north": 0,  # 315-45°
            "east": 0,  # 45-135°
            "south": 0,  # 135-225°
            "west": 0,  # 225-315°
        }

        for direction in directions:
            normalized = direction % 360
            if 315 <= normalized or normalized < 45:
                sectors["north"] += 1
            elif 45 <= normalized < 135:
                sectors["east"] += 1
            elif 135 <= normalized < 225:
                sectors["south"] += 1
            else:  # 225 <= normalized < 315
                sectors["west"] += 1

        # Return the sector with the most observations
        prevailing = max(sectors, key=lambda k: sectors[k])
        return prevailing
