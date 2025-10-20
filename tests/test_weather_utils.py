"""Test the weather utility functions."""

from datetime import datetime, timezone

from custom_components.micro_weather.weather_utils import (
    convert_altitude_to_meters,
    convert_precipitation_rate,
    convert_to_celsius,
    convert_to_hpa,
    convert_to_kmh,
    is_forecast_hour_daytime,
)


class TestWeatherUtils:
    """Test the weather utility functions."""

    def test_convert_to_celsius(self):
        """Test Fahrenheit to Celsius conversion."""
        # Test normal temperature
        assert convert_to_celsius(32.0) == 0.0  # Freezing point
        assert convert_to_celsius(212.0) == 100.0  # Boiling point
        assert convert_to_celsius(72.0) == 22.2  # Room temperature

        # Test None input
        assert convert_to_celsius(None) is None

        # Test edge cases
        assert convert_to_celsius(0.0) == -17.8  # Very cold
        assert convert_to_celsius(100.0) == 37.8  # Hot

    def test_convert_to_hpa(self):
        """Test pressure conversion from inHg to hPa."""
        # Test standard pressure
        assert abs(convert_to_hpa(29.92) - 1013.3) < 0.5

        # Test low pressure
        assert abs(convert_to_hpa(28.0) - 948.0) < 5

        # Test high pressure
        assert abs(convert_to_hpa(31.0) - 1050.0) < 5

        # Test None input
        assert convert_to_hpa(None) is None

        # Test string input (should handle gracefully or be removed if not needed)
        # Note: Function expects float, so this test case may not be valid
        # assert abs(convert_to_hpa("29.92") - 1013.3) < 0.5

    def test_convert_to_kmh(self):
        """Test miles per hour to kilometers per hour conversion."""
        # Test common wind speeds
        assert abs(convert_to_kmh(1.0) - 1.609) < 0.01  # 1 mph
        assert abs(convert_to_kmh(10.0) - 16.093) < 0.01  # 10 mph
        assert abs(convert_to_kmh(60.0) - 96.6) < 0.01  # 60 mph (highway speed)

        # Test None input
        assert convert_to_kmh(None) is None

        # Test edge cases
        assert convert_to_kmh(0.0) == 0.0  # No wind
        assert (
            abs(convert_to_kmh(100.0) - 160.9) < 0.1
        )  # Very high wind (rounded to 1 decimal)

    def test_temperature_conversion_precision(self):
        """Test temperature conversion precision."""
        # Test that conversion maintains reasonable precision
        temp_f = 72.5
        temp_c = convert_to_celsius(temp_f)
        # Convert back to verify round-trip
        temp_f_back = temp_c * 9 / 5 + 32
        assert abs(temp_f - temp_f_back) < 0.1  # Should be very close

    def test_pressure_conversion_precision(self):
        """Test pressure conversion precision."""
        # Test that conversion maintains reasonable precision
        pressure_inhg = 29.92
        pressure_hpa = convert_to_hpa(pressure_inhg)
        # Convert back approximately (1 hPa ≈ 0.02953 inHg)
        pressure_inhg_back = pressure_hpa * 0.02953
        assert abs(pressure_inhg - pressure_inhg_back) < 0.1

    def test_wind_speed_conversion_precision(self):
        """Test wind speed conversion precision."""
        # Test that conversion maintains reasonable precision
        speed_mph = 15.0
        speed_kmh = convert_to_kmh(speed_mph)
        # Convert back (1 km/h ≈ 0.621371 mph)
        speed_mph_back = speed_kmh * 0.621371
        assert abs(speed_mph - speed_mph_back) < 0.1

    def test_convert_altitude_to_meters(self):
        """Test altitude conversion from feet to meters."""
        # Test metric system (no conversion)
        assert convert_altitude_to_meters(100.0, False) == 100.0
        assert convert_altitude_to_meters(500.0, False) == 500.0

        # Test imperial system (feet to meters conversion)
        assert (
            convert_altitude_to_meters(100.0, True) == 30.5
        )  # 100 ft = 30.48 m, rounded to 30.5
        assert convert_altitude_to_meters(1000.0, True) == 304.8  # 1000 ft = 304.8 m

        # Test None input
        assert convert_altitude_to_meters(None, False) is None
        assert convert_altitude_to_meters(None, True) is None

        # Test zero altitude
        assert convert_altitude_to_meters(0.0, False) == 0.0
        assert convert_altitude_to_meters(0.0, True) == 0.0

    def test_convert_precipitation_rate(self):
        """Test precipitation rate conversion."""
        # Test inches per hour to mm per hour conversion
        assert convert_precipitation_rate(1.0, "in/h") == 25.4  # 1 inch = 25.4 mm
        assert (
            convert_precipitation_rate(0.1, "in/hr") == 2.5
        )  # 0.1 inch = 2.54 mm, rounded to 2.5
        assert convert_precipitation_rate(0.5, "inches/h") == 12.7  # 0.5 inch = 12.7 mm

        # Test mm per hour (no conversion needed)
        assert convert_precipitation_rate(10.0, "mm/h") == 10.0
        assert convert_precipitation_rate(5.5, "mmh") == 5.5

        # Test no unit specified (assume mm/h)
        assert convert_precipitation_rate(3.0, None) == 3.0
        assert convert_precipitation_rate(7.5, "") == 7.5

        # Test None value
        assert convert_precipitation_rate(None, "in/h") is None

        # Test invalid value
        assert convert_precipitation_rate("invalid", "in/h") is None

        # Test unknown unit (assume mm/h)
        assert convert_precipitation_rate(5.0, "unknown") == 5.0

    def test_is_forecast_hour_daytime_edge_cases(self):
        """Test the is_forecast_hour_daytime function with edge cases."""
        # Test with None sunrise/sunset (should use hardcoded fallback)
        result = is_forecast_hour_daytime(
            datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc), None, None  # 8 AM
        )
        assert result is True, "Should be daytime at 8 AM with None sunrise/sunset"

        result = is_forecast_hour_daytime(
            datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc), None, None  # 2 AM
        )
        assert result is False, "Should be nighttime at 2 AM with None sunrise/sunset"

        # Test with actual sunrise/sunset times
        sunrise = datetime(2024, 1, 1, 7, 0, 0, tzinfo=timezone.utc)
        sunset = datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

        # Before sunrise
        result = is_forecast_hour_daytime(
            datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc), sunrise, sunset
        )
        assert result is False, "Should be nighttime before sunrise"

        # At sunrise
        result = is_forecast_hour_daytime(
            datetime(2024, 1, 1, 7, 0, 0, tzinfo=timezone.utc), sunrise, sunset
        )
        assert result is True, "Should be daytime at sunrise"

        # During day
        result = is_forecast_hour_daytime(
            datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc), sunrise, sunset
        )
        assert result is True, "Should be daytime during day"

        # At sunset
        result = is_forecast_hour_daytime(
            datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc), sunrise, sunset
        )
        assert result is False, "Should be nighttime at sunset"

        # After sunset
        result = is_forecast_hour_daytime(
            datetime(2024, 1, 1, 20, 0, 0, tzinfo=timezone.utc), sunrise, sunset
        )
        assert result is False, "Should be nighttime after sunset"
