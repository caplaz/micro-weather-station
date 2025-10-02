"""Weather utility functions for unit conversions and calculations."""

from typing import Optional


def convert_to_celsius(temp_f: Optional[float]) -> Optional[float]:
    """Convert Fahrenheit to Celsius."""
    if temp_f is None:
        return None
    return round((temp_f - 32) * 5 / 9, 1)


def convert_to_hpa(pressure_inhg: Optional[float]) -> Optional[float]:
    """Convert inches of mercury to hPa."""
    if pressure_inhg is None:
        return None
    return round(pressure_inhg * 33.8639, 1)


def convert_to_kmh(speed_mph: Optional[float]) -> Optional[float]:
    """Convert miles per hour to kilometers per hour."""
    if speed_mph is None:
        return None
    return round(speed_mph * 1.60934, 1)


def convert_altitude_to_meters(
    altitude: Optional[float], is_imperial: bool = False
) -> Optional[float]:
    """Convert altitude to meters if it's in feet."""
    if altitude is None:
        return None
    if is_imperial:
        return round(altitude * 0.3048, 1)  # 1 foot = 0.3048 meters
    return round(altitude, 1)


def convert_precipitation_rate(
    rain_rate: Optional[float], unit: Optional[str]
) -> Optional[float]:
    """Convert precipitation rate to mm/h."""
    if rain_rate is None:
        return None

    try:
        rain_rate = float(rain_rate)
    except (ValueError, TypeError):
        return None

    if unit is None:
        # Assume mm/h if no unit specified
        return round(rain_rate, 1)

    # Convert to mm/h based on input unit
    if unit.lower() in ["in/h", "in/hr", "inh", "inch/h", "inches/h"]:
        return round(rain_rate * 25.4, 1)  # inches to mm
    elif unit.lower() in ["mm/h", "mmh", "mm/hr"]:
        return round(rain_rate, 1)
    else:
        # Unknown unit, assume mm/h
        return round(rain_rate, 1)
