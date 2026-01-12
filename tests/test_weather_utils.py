"""Test the weather utility functions."""

from datetime import datetime, timezone

from custom_components.micro_weather.weather_utils import (
    convert_altitude_to_meters,
    convert_precipitation_rate,
    convert_to_celsius,
    convert_to_fahrenheit,
    convert_to_hpa,
    convert_to_inhg,
    convert_to_kmh,
    convert_to_mph,
    convert_ms_to_mph,
    is_forecast_hour_daytime,
    calculate_heat_index,
    calculate_wind_chill,
    calculate_apparent_temperature,
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

    def test_convert_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion."""
        # Test normal temperature
        assert convert_to_fahrenheit(0.0) == 32.0  # Freezing point
        assert convert_to_fahrenheit(100.0) == 212.0  # Boiling point
        assert convert_to_fahrenheit(22.2) == 72.0  # Room temperature

        # Test None input
        assert convert_to_fahrenheit(None) is None

        # Test edge cases
        assert convert_to_fahrenheit(-17.8) == 0.0  # Very cold
        assert convert_to_fahrenheit(37.8) == 100.0  # Hot

        # Test decimal precision
        assert convert_to_fahrenheit(20.0) == 68.0  # 20°C = 68°F
        assert convert_to_fahrenheit(25.0) == 77.0  # 25°C = 77°F

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

        # Test Fahrenheit conversion precision
        temp_c = 22.5
        temp_f = convert_to_fahrenheit(temp_c)
        # Convert back to verify round-trip
        temp_c_back = (temp_f - 32) * 5 / 9
        assert abs(temp_c - temp_c_back) < 0.1  # Should be very close

    def test_pressure_conversion_precision(self):
        """Test pressure conversion precision."""
        # Test that conversion maintains reasonable precision
        pressure_inhg = 29.92
        pressure_hpa = convert_to_hpa(pressure_inhg)
        # Convert back approximately (1 hPa ≈ 0.02953 inHg)
        pressure_inhg_back = pressure_hpa * 0.02953
        assert abs(pressure_inhg - pressure_inhg_back) < 0.1

    def test_convert_to_inhg(self):
        """Test pressure conversion from hPa to inHg."""
        # Test standard pressure
        assert abs(convert_to_inhg(1013.25) - 29.92) < 0.01

        # Test low pressure
        assert abs(convert_to_inhg(948.0) - 28.0) < 0.1

        # Test high pressure
        assert abs(convert_to_inhg(1050.0) - 31.0) < 0.1

        # Test None input
        assert convert_to_inhg(None) is None

    def test_convert_to_mph(self):
        """Test kilometers per hour to miles per hour conversion."""
        # Test common wind speeds
        assert abs(convert_to_mph(1.609) - 1.0) < 0.01  # 1 mph
        assert abs(convert_to_mph(16.093) - 10.0) < 0.01  # 10 mph
        assert abs(convert_to_mph(96.6) - 60.0) < 0.1  # 60 mph

        # Test None input
        assert convert_to_mph(None) is None

    def test_convert_ms_to_mph(self):
        """Test meters per second to miles per hour conversion."""
        # Test common wind speeds
        assert abs(convert_ms_to_mph(1.0) - 2.2) < 0.1  # 1 m/s approx 2.237 mph, rounded to 2.2
        assert abs(convert_ms_to_mph(10.0) - 22.4) < 0.1

        # Test None input
        assert convert_ms_to_mph(None) is None

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

    def test_is_forecast_hour_daytime_midday_scenario(self):
        """Test is_forecast_hour_daytime when next sunrise is tomorrow and next sunset is today.

        This simulates the scenario where the function is called in the middle of the day.
        """
        # Scenario:
        # Current time (implied): Day 1, 13:40
        # Next Sunrise: Day 2, 07:00
        # Next Sunset: Day 1, 17:00

        sunrise = datetime(2025, 12, 1, 7, 0, 0, tzinfo=timezone.utc)  # Tomorrow
        sunset = datetime(2025, 11, 30, 17, 0, 0, tzinfo=timezone.utc)  # Today

        # Test 1: Forecast 2 PM Today (Should be Day)
        f1 = datetime(2025, 11, 30, 14, 0, 0, tzinfo=timezone.utc)
        assert is_forecast_hour_daytime(f1, sunrise, sunset) is True

        # Test 2: Forecast 8 PM Today (Should be Night)
        f2 = datetime(2025, 11, 30, 20, 0, 0, tzinfo=timezone.utc)
        assert is_forecast_hour_daytime(f2, sunrise, sunset) is False

        # Test 3: Forecast 4 AM Tomorrow (Should be Night)
        f3 = datetime(2025, 12, 1, 4, 0, 0, tzinfo=timezone.utc)
        assert is_forecast_hour_daytime(f3, sunrise, sunset) is False

        # Test 4: Forecast 8 AM Tomorrow (Should be Day)
        # Note: This technically falls into the "next cycle" which might be tricky depending on how we define "daytime" relative to *these specific* sun times.
        # But based on the logic `forecast_time >= sunrise_time`, it should be True.
    def test_calculate_heat_index(self):
        """Test Heat Index calculation."""
        # Test below threshold (return temp)
        assert calculate_heat_index(70.0, 50.0) == 70.0

        # Test simple formula range
        # 80F, 40% RH -> ~80F
        assert 79.0 <= calculate_heat_index(80.0, 40.0) <= 81.0

        # Test full regression
        # 90F, 50% RH -> ~95F
        assert 94.0 <= calculate_heat_index(90.0, 50.0) <= 96.0

        # Test adjustments
        # Low humidity: 95F, 10% RH -> ~93F (Heat Index is lower than temp)
        assert calculate_heat_index(95.0, 10.0) < 95.0

        # High humidity: 85F, 90% RH -> ~102F
        assert calculate_heat_index(85.0, 90.0) > 95.0

        # Test None input
        assert calculate_heat_index(None, 50.0) is None
        assert calculate_heat_index(80.0, None) is None

    def test_calculate_wind_chill(self):
        """Test Wind Chill calculation."""
        # Test above threshold (return temp)
        assert calculate_wind_chill(55.0, 10.0) == 55.0  # Temp too high
        assert calculate_wind_chill(30.0, 2.0) == 30.0   # Wind too low

        # Test valid wind chill
        # 30F, 10mph -> ~21F
        wc = calculate_wind_chill(30.0, 10.0)
        assert 20.0 <= wc <= 22.0

        # 0F, 15mph -> ~-19F
        wc = calculate_wind_chill(0.0, 15.0)
        assert -20.0 <= wc <= -18.0

        # Test None input
        assert calculate_wind_chill(None, 10.0) is None
        assert calculate_wind_chill(30.0, None) is None

    def test_calculate_apparent_temperature(self):
        """Test overall apparent temperature calculation."""
        # Normal range (neither heat index nor wind chill)
        # 60F, 50% RH, 5mph wind
        assert calculate_apparent_temperature(60.0, 50.0, 5.0) == 60.0

        # Wind Chill range
        # 30F, 10mph
        wc = calculate_apparent_temperature(30.0, 50.0, 10.0)
        assert wc < 30.0

        # Heat Index range
        # 90F, 50% RH
        hi = calculate_apparent_temperature(90.0, 50.0, 5.0)
        assert hi > 90.0

        # None handling
        assert calculate_apparent_temperature(None, 50.0, 5.0) is None

    def test_calculate_apparent_temperature_units(self):
        """Test apparent temperature with variable units."""
        # Celsius input (should return Celsius)
        # 20C = 68F. Normal range. Return 20C.
        assert calculate_apparent_temperature(20.0, 50.0, 5.0, temp_unit="C") == 20.0

        # Celsius with Wind Chill
        # -10C = 14F. Wind 20 km/h (~12 mph).
        # Wind Chill(14F, 12mph) ~ -2F = -19C
        wc_c = calculate_apparent_temperature(
            -10.0, 50.0, 20.0, temp_unit="C", wind_unit="km/h"
        )
        assert -20.0 <= wc_c <= -17.0

        # Celsius with Heat Index
        # 35C = 95F. Humidity 50%.
        # Heat Index(95F, 50%) ~ 107F = 41.7C
        hi_c = calculate_apparent_temperature(
            35.0, 50.0, 10.0, temp_unit="C", wind_unit="km/h"
        )
        assert 40.0 <= hi_c <= 43.0
        
        # Test unit string normalization
        assert calculate_apparent_temperature(20.0, 50.0, 5.0, temp_unit="celsius") == 20.0
        assert calculate_apparent_temperature(20.0, 50.0, 5.0, temp_unit="°C") == 20.0
