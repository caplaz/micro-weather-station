"""Weather utility functions for unit conversions and calculations."""

from datetime import datetime
from typing import Optional

from homeassistant.core import HomeAssistant


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


def get_sun_times(hass: HomeAssistant) -> tuple[datetime | None, datetime | None]:
    """Get sunrise and sunset times from the sun.sun entity.

    Args:
        hass: Home Assistant instance

    Returns:
        tuple: (sunrise_time, sunset_time) as datetime objects, or (None, None) if unavailable
    """
    try:
        sun_state = hass.states.get("sun.sun")
        if sun_state and sun_state.attributes:
            next_rising = sun_state.attributes.get("next_rising")
            next_setting = sun_state.attributes.get("next_setting")

            sunrise_time = None
            sunset_time = None

            if next_rising:
                try:
                    sunrise_time = datetime.fromisoformat(
                        next_rising.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass

            if next_setting:
                try:
                    sunset_time = datetime.fromisoformat(
                        next_setting.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass

            return sunrise_time, sunset_time
    except (AttributeError, KeyError, TypeError):
        pass

    return None, None


def is_forecast_hour_daytime(
    forecast_time: datetime,
    sunrise_time: datetime | None,
    sunset_time: datetime | None,
) -> bool:
    """Determine if a forecast hour is daytime using sunrise/sunset data.

    Falls back to hardcoded 6 AM/6 PM times if sunrise/sunset data is unavailable.

    Args:
        forecast_time: The datetime of the forecast hour
        sunrise_time: Sunrise time from sun.sun entity (can be None)
        sunset_time: Sunset time from sun.sun entity (can be None)

    Returns:
        bool: True if the forecast hour is daytime, False if nighttime
    """
    if sunrise_time and sunset_time:
        # Use actual sunrise/sunset times
        # Handle timezone awareness mismatches
        if forecast_time.tzinfo is None and sunrise_time.tzinfo is not None:
            # Make forecast_time timezone-aware to match sunrise/sunset
            forecast_time = forecast_time.replace(tzinfo=sunrise_time.tzinfo)
        elif forecast_time.tzinfo is not None and sunrise_time.tzinfo is None:
            # Make sunrise/sunset timezone-aware to match forecast_time
            sunrise_time = sunrise_time.replace(tzinfo=forecast_time.tzinfo)
            sunset_time = sunset_time.replace(tzinfo=forecast_time.tzinfo)
        # If both are offset-naive or both are offset-aware, compare directly
        return sunrise_time <= forecast_time < sunset_time
    else:
        # Fallback to hardcoded times (6 AM to 6 PM)
        return 6 <= forecast_time.hour < 18
