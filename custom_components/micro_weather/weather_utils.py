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
