"""Meteorological constants and thresholds for weather analysis.

This module contains scientifically-based thresholds and constants used
throughout the weather analysis system. Values are based on meteorological
research and observational standards.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FogThresholds:
    """Fog detection thresholds based on meteorological research.

    Fog forms when air near the surface becomes saturated (RH near 100%)
    and the temperature-dewpoint spread approaches zero. Light winds
    allow fog to form, while strong winds disperse it.

    References:
        - National Weather Service fog criteria
        - WMO fog classification guidelines
    """

    # Humidity thresholds (%)
    HUMIDITY_DENSE_FOG = 98  # Near saturation - dense fog highly likely
    HUMIDITY_PROBABLE_FOG = 95  # Very high - fog probable
    HUMIDITY_POSSIBLE_FOG = 92  # High - fog possible
    HUMIDITY_MARGINAL_FOG = 88  # Moderately high - marginal conditions

    # Scoring weights for humidity factor (max 40 points)
    SCORE_DENSE = 40
    SCORE_PROBABLE = 30
    SCORE_POSSIBLE = 20
    SCORE_MARGINAL = 10

    # Temperature-dewpoint spread thresholds (°F)
    SPREAD_SATURATED = 0.5  # Nearly saturated
    SPREAD_VERY_CLOSE = 1.0  # Very close to dewpoint
    SPREAD_CLOSE = 2.0  # Close to dewpoint
    SPREAD_MARGINAL = 3.0  # Marginal spread

    # Scoring weights for spread factor (max 30 points)
    SCORE_SPREAD_SATURATED = 30
    SCORE_SPREAD_VERY_CLOSE = 25
    SCORE_SPREAD_CLOSE = 15
    SCORE_SPREAD_MARGINAL = 5

    # Wind thresholds (mph)
    WIND_CALM = 2  # Calm - ideal for dense fog
    WIND_LIGHT = 5  # Light - fog can persist
    WIND_MODERATE = 8  # Moderate - fog may form but lighter

    # Scoring weights for wind factor (max 15 points)
    SCORE_WIND_CALM = 15
    SCORE_WIND_LIGHT = 10
    SCORE_WIND_MODERATE = 5
    PENALTY_WIND_STRONG = -10  # Strong winds disperse fog

    # Solar radiation thresholds (W/m²)
    SOLAR_VERY_LOW = 50  # Dense fog blocking sun
    SOLAR_LOW = 150  # Moderate fog or heavy overcast
    SOLAR_REDUCED = 300  # Light fog or overcast
    SOLAR_MINIMAL_NIGHT = 2  # No radiation at night
    SOLAR_TWILIGHT = 10  # Minimal twilight radiation
    SOLAR_MODERATE_TWILIGHT = 50  # Moderate twilight

    # Scoring weights for solar factor (max 15 points)
    SCORE_SOLAR_DENSE = 15
    SCORE_SOLAR_MODERATE = 10
    SCORE_SOLAR_LIGHT = 5
    SCORE_SOLAR_NIGHT = 10
    SCORE_SOLAR_TWILIGHT = 5
    PENALTY_SOLAR_STRONG = -15  # Strong radiation unlikely with fog

    # Temperature bonus thresholds
    TEMP_WARM_THRESHOLD = 40  # °F - warm enough for evaporation fog

    # Detection thresholds (fog score 0-100)
    THRESHOLD_DENSE_FOG = 70  # Dense fog
    THRESHOLD_MODERATE_FOG = 55  # Moderate fog
    THRESHOLD_LIGHT_FOG = 45  # Light fog (requires high humidity confirmation)


@dataclass(frozen=True)
class WindThresholds:
    """Wind speed thresholds based on Beaufort Wind Scale.

    The Beaufort scale is an empirical measure relating wind speed to
    observed conditions. Adapted for mph (US standard).

    References:
        - Beaufort Wind Scale (UK Met Office)
        - National Weather Service wind classification
    """

    # Wind speed thresholds (mph)
    CALM = 1  # Beaufort 0-1: Calm to light air
    LIGHT_BREEZE = 8  # Beaufort 2-3: Light to gentle breeze
    MODERATE_BREEZE = 13  # Beaufort 4: Moderate breeze
    FRESH_BREEZE = 19  # Beaufort 5-6: Fresh to strong breeze
    NEAR_GALE = 32  # Beaufort 7-8: Near gale to gale
    STRONG_GALE = 47  # Beaufort 9-10: Strong gale to storm
    VIOLENT_STORM = 64  # Beaufort 11-12: Violent storm to hurricane

    # Gust factor thresholds (ratio of gust to sustained wind)
    GUST_FACTOR_MODERATE = 1.5  # Moderate turbulence
    GUST_FACTOR_STRONG = 2.0  # Strong turbulence
    GUST_FACTOR_SEVERE = 3.0  # Severe turbulence (thunderstorm indicator)

    # Absolute gust thresholds (mph)
    GUST_MODERATE = 10  # Moderate gusts
    GUST_STRONG = 15  # Strong gusts
    GUST_SEVERE = 20  # Severe gusts
    GUST_EXTREME = 40  # Extreme gusts (likely thunderstorm)


@dataclass(frozen=True)
class PressureThresholds:
    """Atmospheric pressure thresholds and trend analysis parameters.

    Pressure values in inches of mercury (inHg) at sea level.
    Trends measured in hectopascals (hPa) or millibars (mb).

    References:
        - NOAA pressure system definitions
        - Aviation weather standards (altimeter settings)
    """

    # Absolute pressure thresholds (inHg at sea level)
    EXTREMELY_LOW = 29.20  # Severe storm/hurricane
    VERY_LOW = 29.50  # Strong storm system
    LOW = 29.80  # Low pressure system
    NORMAL_LOW = 29.90  # Lower end of normal
    NORMAL_HIGH = 30.20  # Upper end of normal
    HIGH = 30.40  # High pressure system
    VERY_HIGH = 30.70  # Very high pressure

    # Pressure change thresholds (hPa/period)
    # 3-hour trends (short-term)
    TREND_3H_RAPID_FALL = -0.5  # Rapid fall
    TREND_3H_MODERATE_FALL = -0.2  # Moderate fall
    TREND_3H_MODERATE_RISE = 0.2  # Moderate rise
    TREND_3H_RAPID_RISE = 0.5  # Rapid rise

    # 24-hour trends (long-term)
    TREND_24H_RAPID_FALL = -1.0  # Rapid fall
    TREND_24H_MODERATE_FALL = -0.3  # Moderate fall
    TREND_24H_MODERATE_RISE = 0.1  # Moderate rise
    TREND_24H_RAPID_RISE = 0.5  # Rapid rise

    # Cloud cover adjustment parameters
    CLOUD_ADJUSTMENT_MAX = 50.0  # Maximum adjustment (%)
    SHORT_TERM_MULTIPLIER_FALL = 8.0  # For falling pressure
    SHORT_TERM_MULTIPLIER_RISE = 15.0  # For rising pressure
    LONG_TERM_MULTIPLIER_FALL = 6.0  # For sustained fall
    LONG_TERM_MULTIPLIER_RISE = 12.0  # For sustained rise

    # System type adjustments (%)
    HIGH_PRESSURE_CLOUD_REDUCTION = -50.0  # Clear skies
    LOW_PRESSURE_CLOUD_INCREASE = 20.0  # Cloudy
    STORM_CLOUD_INCREASE = 40.0  # Very cloudy

    # System adjustment weight
    SYSTEM_WEIGHT = 0.30  # 30% weight for pressure system type


@dataclass(frozen=True)
class PrecipitationThresholds:
    """Precipitation intensity classification thresholds.

    Based on rain rate in inches per hour (in/h) or millimeters per hour (mm/h).

    References:
        - National Weather Service precipitation classification
        - NOAA rainfall intensity guidelines
    """

    # Rain rate thresholds (in/h)
    SIGNIFICANT = 0.01  # Minimum detectable precipitation
    LIGHT = 0.1  # Light rain threshold
    MODERATE = 0.25  # Moderate rain threshold
    HEAVY = 0.5  # Heavy rain threshold
    VERY_HEAVY = 1.0  # Very heavy rain/pouring

    # Storm detection thresholds
    STORM_MIN_RATE = 0.05  # Minimum rate for severe weather with turbulence
    STORM_MODERATE_RATE = 0.1  # Moderate rate for storm classification
    STORM_HEAVY_RATE = 0.25  # Heavy rate for storm classification


@dataclass(frozen=True)
class TemperatureThresholds:
    """Temperature-related thresholds for weather classification.

    Temperatures in Fahrenheit.
    """

    # Phase change thresholds
    FREEZING = 32.0  # Water freezing point

    # Fog-related temperature thresholds
    WARM_FOG_THRESHOLD = 40.0  # Warm enough for evaporation fog

    # Dewpoint spread thresholds (for various analyses)
    SPREAD_SATURATED = 2.0  # Nearly saturated (fog/precipitation likely)
    SPREAD_HUMID = 5.0  # High moisture content
    SPREAD_MODERATE = 10.0  # Moderate moisture
    SPREAD_DRY = 15.0  # Dry air

    # Humidity thresholds for condition analysis (%)
    HUMIDITY_HIGH = 90  # High humidity - fog/rain likely
    HUMIDITY_MODERATE_HIGH = 70  # Moderately high humidity
    HUMIDITY_MODERATE = 50  # Moderate humidity - comfortable


@dataclass(frozen=True)
class CloudCoverThresholds:
    """Cloud cover percentage thresholds for condition classification.

    Based on okta scale (0-8 eighths) converted to percentages.

    References:
        - WMO cloud classification (okta scale)
        - Aviation weather reporting standards (SKC/FEW/SCT/BKN/OVC)
    """

    # Cloud cover percentages
    CLEAR = 12.5  # 0-1 okta (0-12.5%) - Clear/Sunny
    FEW = 25.0  # 1-2 okta (12.5-25%) - Few clouds
    SCATTERED = 50.0  # 3-4 okta (25-50%) - Scattered/Partly cloudy
    BROKEN = 87.5  # 5-7 okta (50-87.5%) - Broken/Mostly cloudy
    OVERCAST = 100.0  # 8 okta (87.5-100%) - Overcast

    # Thresholds for condition mapping
    THRESHOLD_SUNNY = 20.0  # < 20% = Sunny/Clear
    THRESHOLD_PARTLY_CLOUDY = 50.0  # 20-50% = Partly cloudy
    THRESHOLD_CLOUDY = 75.0  # 50-75% = Cloudy
    # > 75% = Overcast (rainy if precipitation present)

    # Neutral threshold for unreliable measurements
    NEUTRAL = 50.0  # Neutral point (neither clear nor cloudy)
    RELIABILITY_BUFFER = 10.0  # +/- buffer around neutral (40-60% = unreliable)


# Conversion constants
MPH_TO_KMH = 1.60934  # Miles per hour to kilometers per hour
INCHES_TO_MM = 25.4  # Inches to millimeters
FAHRENHEIT_TO_CELSIUS_SCALE = 5.0 / 9.0  # F to C scale factor
FAHRENHEIT_OFFSET = 32.0  # F to C offset
HPA_TO_INHG = 0.02953  # Hectopascals to inches of mercury
INHG_TO_HPA = 33.8639  # Inches of mercury to hectopascals


# Default values for missing sensors
DEFAULT_TEMPERATURE_F = 70.0  # °F - Typical room/moderate temperature
DEFAULT_HUMIDITY = 50.0  # % - Mid-range humidity
DEFAULT_PRESSURE_INHG = 29.92  # inHg - Standard sea level pressure
DEFAULT_WIND_SPEED = 0.0  # mph - Calm
DEFAULT_SOLAR_RADIATION = 0.0  # W/m² - No radiation (night/clouds)
DEFAULT_ZENITH_MAX_RADIATION = 1000.0  # W/m² - Typical maximum at zenith
