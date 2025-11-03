"""Test the solar analysis functionality."""

from collections import deque
from datetime import datetime, timedelta

import pytest

from custom_components.micro_weather.analysis.solar import SolarAnalyzer


class TestSolarAnalyzer:
    """Test the SolarAnalyzer class."""

    @pytest.fixture
    def mock_sensor_history(self):
        """Create mock sensor history for testing."""
        history = {
            "outdoor_temp": deque(maxlen=192),
            "humidity": deque(maxlen=192),
            "pressure": deque(maxlen=192),
            "wind_speed": deque(maxlen=192),
            "wind_direction": deque(maxlen=192),
            "solar_radiation": deque(maxlen=192),
            "rain_rate": deque(maxlen=192),
        }

        # Add some historical data
        base_time = datetime.now()
        for i in range(10):
            timestamp = base_time - timedelta(hours=i)
            history["outdoor_temp"].append({"timestamp": timestamp, "value": 70.0 + i})
            history["humidity"].append({"timestamp": timestamp, "value": 60.0 + i})
            history["pressure"].append(
                {"timestamp": timestamp, "value": 29.92 - i * 0.01}
            )
            history["wind_speed"].append(
                {"timestamp": timestamp, "value": 5.0 + i * 0.1}
            )
            history["wind_direction"].append(
                {"timestamp": timestamp, "value": 180.0 + i * 10}
            )
            history["solar_radiation"].append(
                {"timestamp": timestamp, "value": 200.0 + i * 10}
            )
            history["rain_rate"].append({"timestamp": timestamp, "value": 0.0})

        return history

    @pytest.fixture
    def analyzer(self, mock_sensor_history):
        """Create SolarAnalyzer instance for testing."""
        return SolarAnalyzer(mock_sensor_history)

    def test_analyze_cloud_cover(self, analyzer):
        """Test cloud cover analysis."""
        # Test clear skies
        cloud_cover = analyzer.analyze_cloud_cover(800.0, 80000.0, 8.0)
        assert cloud_cover <= 25  # Should be mostly clear (around 20%)

        # Clear cloud cover history to avoid hysteresis effects
        analyzer._sensor_history["cloud_cover"] = []

        # Test cloudy conditions
        cloud_cover_cloudy = analyzer.analyze_cloud_cover(50.0, 5000.0, 1.0)
        assert cloud_cover_cloudy > 80  # Should be mostly cloudy

        # Test no solar input (night/heavy overcast)
        # Note: After recent high/low readings, hysteresis prevents immediate jump to 100%
        # This is the correct behavior - actual night transitions happen gradually
        cloud_cover_night = analyzer.analyze_cloud_cover(0.0, 0.0, 0.0)
        assert (
            cloud_cover_night >= 50.0
        )  # Hysteresis prevents extreme jump from recent data

    def test_analyze_cloud_cover_low_solar_radiation_fallback(self, analyzer):
        """Test cloud cover analysis with improved low solar radiation logic."""
        # Test very low solar values (heavy overcast)
        cloud_cover_heavy = analyzer.analyze_cloud_cover(20.0, 3000.0, 0.0, 15.0)
        assert cloud_cover_heavy == pytest.approx(
            78.0, abs=0.5
        )  # Astronomical calculation

        # Test moderately low solar values (mostly cloudy)
        cloud_cover_mostly = analyzer.analyze_cloud_cover(75.0, 7500.0, 0.5, 15.0)
        assert cloud_cover_mostly == pytest.approx(
            48.0, abs=0.5
        )  # Astronomical calculation (UV ignored due to inconsistency)

        # Test borderline low solar values (partly cloudy fallback)
        cloud_cover_fallback = analyzer.analyze_cloud_cover(150.0, 15000.0, 0.8, 20.0)
        assert cloud_cover_fallback == pytest.approx(
            18.0, abs=0.5
        )  # Astronomical calculation (UV ignored due to inconsistency)

        # Test that higher values don't trigger fallback
        cloud_cover_normal = analyzer.analyze_cloud_cover(250.0, 25000.0, 2.0, 30.0)
        assert (
            cloud_cover_normal != 40.0
            and cloud_cover_normal != 70.0
            and cloud_cover_normal != 85.0
        )  # Should be calculated normally

    def test_analyze_cloud_cover_elevation_effects(self, analyzer):
        """Test cloud cover analysis with different solar elevations."""
        # Test with moderate radiation that shows elevation effects
        cloud_cover_high = analyzer.analyze_cloud_cover(
            200.0, 20000.0, 2.0, 80.0
        )  # High elevation
        cloud_cover_low = analyzer.analyze_cloud_cover(
            200.0, 20000.0, 2.0, 20.0
        )  # Low elevation

        # With the same actual radiation, lower elevation gives lower cloud cover
        # because the actual radiation represents a higher percentage of the lower max
        assert cloud_cover_low < cloud_cover_high

        # Test very low elevation (near horizon) - may show clear due to algorithm
        cloud_cover_horizon = analyzer.analyze_cloud_cover(100.0, 10000.0, 2.0, 5.0)
        assert isinstance(cloud_cover_horizon, float)
        assert 0 <= cloud_cover_horizon <= 100

        # Test zero elevation (should use minimum factor)
        cloud_cover_zero = analyzer.analyze_cloud_cover(50.0, 5000.0, 1.0, 0.0)
        assert isinstance(cloud_cover_zero, float)
        assert 0 <= cloud_cover_zero <= 100

    def test_analyze_cloud_cover_seasonal_adjustments(self, analyzer):
        """Test cloud cover analysis with different months."""
        # Test that the method runs without error for different months
        import datetime
        from unittest.mock import patch

        # Test winter conditions
        with patch(
            "custom_components.micro_weather.analysis.solar.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime(2024, 1, 15)
            winter_cover = analyzer.analyze_cloud_cover(300.0, 30000.0, 3.0, 60.0)

        # Test summer conditions
        with patch(
            "custom_components.micro_weather.analysis.solar.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime(2024, 7, 15)
            summer_cover = analyzer.analyze_cloud_cover(300.0, 30000.0, 3.0, 60.0)

        # Both should return valid cloud cover percentages
        assert isinstance(winter_cover, float)
        assert isinstance(summer_cover, float)
        assert 0 <= winter_cover <= 100
        assert 0 <= summer_cover <= 100

    def test_analyze_cloud_cover_measurement_weighting(self, analyzer):
        """Test cloud cover analysis measurement weighting logic."""
        # Test primary weighting (solar radiation > 10)
        cloud_cover_primary = analyzer.analyze_cloud_cover(500.0, 50000.0, 5.0, 45.0)
        assert isinstance(cloud_cover_primary, float)
        assert 0 <= cloud_cover_primary <= 100

        # Test lux fallback (low radiation, high lux)
        cloud_cover_lux = analyzer.analyze_cloud_cover(5.0, 5000.0, 0.5, 45.0)
        assert isinstance(cloud_cover_lux, float)
        assert 0 <= cloud_cover_lux <= 100

        # Test UV fallback (very low radiation and lux, some UV)
        cloud_cover_uv = analyzer.analyze_cloud_cover(2.0, 500.0, 1.0, 45.0)
        assert isinstance(cloud_cover_uv, float)
        assert 0 <= cloud_cover_uv <= 100

        # Test mostly cloudy conditions (very low solar measurements)
        # This should use astronomical calculation for very low measurements
        cloud_cover_mostly = analyzer.analyze_cloud_cover(1.0, 200.0, 0.2, 45.0)
        assert cloud_cover_mostly == pytest.approx(
            99.6, abs=0.1
        )  # Astronomical calculation

    def test_analyze_cloud_cover_edge_cases(self, analyzer):
        """Test cloud cover analysis edge cases."""
        # Clear historical data to avoid averaging effects
        analyzer._sensor_history["solar_radiation"] = []
        analyzer._sensor_history["cloud_cover"] = []

        # Test with zero values (triggers heavy overcast)
        cloud_cover_zero = analyzer.analyze_cloud_cover(0.0, 0.0, 0.0, 45.0)
        assert cloud_cover_zero == 100.0  # No solar input = complete overcast

        # Clear cloud cover history before next test
        analyzer._sensor_history["cloud_cover"] = []

        # Test with very high values (should cap at 0% cloud cover)
        cloud_cover_max = analyzer.analyze_cloud_cover(2000.0, 200000.0, 20.0, 90.0)
        assert cloud_cover_max == 0.0  # Completely clear

        # Test with negative values (should be handled gracefully)
        cloud_cover_negative = analyzer.analyze_cloud_cover(-10.0, -1000.0, -1.0, 45.0)
        assert isinstance(cloud_cover_negative, float)
        # Should still return a valid percentage

    def test_get_solar_radiation_average(self, analyzer):
        """Test solar radiation averaging."""
        # Test with no historical data
        average = analyzer._get_solar_radiation_average(100.0)
        assert average == 100.0  # Should return current value

        # Test with insufficient historical data
        analyzer._sensor_history["solar_radiation"] = [
            {"timestamp": datetime.now() - timedelta(minutes=5), "value": 90.0},
            {"timestamp": datetime.now() - timedelta(minutes=10), "value": 95.0},
        ]
        average_insufficient = analyzer._get_solar_radiation_average(100.0)
        assert average_insufficient == 100.0  # Should return current value

        # Test with sufficient historical data
        analyzer._sensor_history["solar_radiation"].extend(
            [
                {"timestamp": datetime.now() - timedelta(minutes=15), "value": 85.0},
                {"timestamp": datetime.now() - timedelta(minutes=20), "value": 80.0},
                {"timestamp": datetime.now() - timedelta(minutes=25), "value": 75.0},
            ]
        )
        average_sufficient = analyzer._get_solar_radiation_average(100.0)
        assert isinstance(average_sufficient, float)
        assert average_sufficient > 0

        # Test filtering out zero values
        analyzer._sensor_history["solar_radiation"].append(
            {"timestamp": datetime.now() - timedelta(minutes=30), "value": 0.0}
        )
        average_filtered = analyzer._get_solar_radiation_average(100.0)
        assert average_filtered > 0  # Should exclude zero values

    def test_get_solar_radiation_average_time_filtering(self, analyzer):
        """Test solar radiation averaging with time-based filtering."""
        base_time = datetime.now()

        # Add data from different time periods
        analyzer._sensor_history["solar_radiation"] = [
            # Recent data (within 15 minutes)
            {"timestamp": base_time - timedelta(minutes=1), "value": 100.0},
            {"timestamp": base_time - timedelta(minutes=5), "value": 110.0},
            {"timestamp": base_time - timedelta(minutes=10), "value": 105.0},
            {"timestamp": base_time - timedelta(minutes=14), "value": 95.0},
            # Older data (beyond 15 minutes)
            {"timestamp": base_time - timedelta(minutes=20), "value": 120.0},
            {"timestamp": base_time - timedelta(minutes=30), "value": 130.0},
        ]

        average = analyzer._get_solar_radiation_average(108.0)
        assert isinstance(average, float)

        # Should only consider recent readings (within 15 minutes)
        # Expected: weighted average of [100, 110, 105, 95] with current 108
        recent_values = [100.0, 110.0, 105.0, 95.0, 108.0]
        expected_avg = sum(recent_values) / len(
            recent_values
        )  # Simple average for test
        assert (
            abs(average - expected_avg) < 5.0
        )  # Should be close to recent data average

    def test_calculate_clear_sky_max_radiation(self, analyzer):
        """Test clear-sky maximum radiation calculation."""
        # Test at zenith (90° elevation)
        max_rad_zenith = analyzer._calculate_clear_sky_max_radiation(90.0)
        assert isinstance(max_rad_zenith, float)
        assert 600 < max_rad_zenith < 2000  # Should be in reasonable range

        # Test at moderate elevation (45°)
        max_rad_45 = analyzer._calculate_clear_sky_max_radiation(45.0)
        assert isinstance(max_rad_45, float)
        assert 200 < max_rad_45 < 1500  # Should be lower than zenith

        # Test at low elevation (20°)
        max_rad_20 = analyzer._calculate_clear_sky_max_radiation(20.0)
        assert isinstance(max_rad_20, float)
        assert 50 < max_rad_20 < 700  # Should be much lower

        # Test at horizon (0° elevation)
        max_rad_0 = analyzer._calculate_clear_sky_max_radiation(0.0)
        assert max_rad_0 == 50.0  # Should return minimum value

        # Test below horizon (negative elevation)
        max_rad_negative = analyzer._calculate_clear_sky_max_radiation(-10.0)
        assert max_rad_negative == 50.0  # Should return minimum value

        # Test that higher elevation gives higher radiation
        assert max_rad_zenith > max_rad_45 > max_rad_20

    def test_calculate_clear_sky_max_radiation_seasonal_variations(self, analyzer):
        """Test seasonal variations in clear-sky radiation calculation."""
        import datetime

        # Test perihelion (closest to sun, highest radiation)
        rad_perihelion = analyzer._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 1, 4)
        )
        print(f"Winter radiation: {rad_perihelion}")

        # Test aphelion (farthest from sun, lowest radiation)
        rad_aphelion = analyzer._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 7, 4)
        )
        print(f"Summer radiation: {rad_aphelion}")

        # Winter (perihelion) should have higher radiation due to closer distance to sun
        assert rad_perihelion > rad_aphelion

        # Check that the difference is meaningful (should be several W/m²)
        assert rad_perihelion - rad_aphelion > 10

    def test_calculate_clear_sky_max_radiation_bounds(self, analyzer):
        """Test bounds checking in clear-sky radiation calculation."""
        # Test that very high elevations don't exceed maximum
        max_rad_high = analyzer._calculate_clear_sky_max_radiation(85.0)
        assert max_rad_high <= 2000.0  # Should be capped at maximum

        # Test that very low elevations don't go below minimum
        max_rad_low = analyzer._calculate_clear_sky_max_radiation(1.0)
        assert max_rad_low >= 50.0  # Should be floored at minimum

    def test_calculate_air_mass(self, analyzer):
        """Test air mass calculation."""
        # Test at zenith (90° elevation)
        air_mass_zenith = analyzer._calculate_air_mass(90.0)
        assert abs(air_mass_zenith - 1.0) < 0.01  # Should be very close to 1.0

        # Test at moderate elevation (45°)
        air_mass_45 = analyzer._calculate_air_mass(45.0)
        assert 1.4 < air_mass_45 < 1.5  # Should be around 1.41

        # Test at low elevation (20°)
        air_mass_20 = analyzer._calculate_air_mass(20.0)
        assert 2.8 < air_mass_20 < 3.0  # Should be around 2.9

        # Test at very low elevation (5°)
        air_mass_5 = analyzer._calculate_air_mass(5.0)
        assert 10 < air_mass_5 < 15  # Should be high air mass

        # Test below horizon
        air_mass_negative = analyzer._calculate_air_mass(-10.0)
        assert air_mass_negative == 38.0  # Should return maximum air mass

        # Test that air mass increases as elevation decreases
        assert air_mass_zenith < air_mass_45 < air_mass_20 < air_mass_5

    def test_calculate_air_mass_edge_cases(self, analyzer):
        """Test air mass calculation edge cases."""
        # Test at exactly 0° elevation
        air_mass_zero = analyzer._calculate_air_mass(0.0)
        assert air_mass_zero == 38.0  # Should return maximum air mass

        # Test at very high elevation (near zenith)
        air_mass_89 = analyzer._calculate_air_mass(89.0)
        assert 1.0 <= air_mass_89 < 1.01  # Should be very close to 1.0

        # Test boundary values
        air_mass_90 = analyzer._calculate_air_mass(90.0)
        assert abs(air_mass_90 - 1.0) < 0.01

        air_mass_1 = analyzer._calculate_air_mass(1.0)
        assert air_mass_1 > 20  # Should be very high

    def test_calculate_air_mass_kasten_young_formula(self, analyzer):
        """Test that air mass uses Kasten-Young formula correctly."""
        # Test specific values to verify Kasten-Young implementation
        # At 45° elevation, air mass should be approximately 1.41
        air_mass_45 = analyzer._calculate_air_mass(45.0)
        expected_45 = 1.0 / (
            0.7071067811865476 + 0.50572 * (96.07995 - 45.0) ** (-1.6364)
        )  # Manual calculation
        assert abs(air_mass_45 - expected_45) < 0.01

        # At 30° elevation, air mass should be approximately 1.99
        air_mass_30 = analyzer._calculate_air_mass(30.0)
        expected_30 = 1.0 / (
            0.5 + 0.50572 * (96.07995 - 30.0) ** (-1.6364)
        )  # Manual calculation
        assert abs(air_mass_30 - expected_30) < 0.01

    def test_clear_sky_radiation_integration_with_cloud_cover(self, analyzer):
        """Test integration between clear-sky radiation and cloud cover analysis."""
        # Test that clear-sky radiation affects cloud cover calculation
        # Same actual radiation at different elevations should give different cloud cover

        # At high elevation (higher clear-sky max)
        cloud_cover_high = analyzer.analyze_cloud_cover(300.0, 30000.0, 3.0, 80.0)
        # At low elevation (lower clear-sky max)
        cloud_cover_low = analyzer.analyze_cloud_cover(300.0, 30000.0, 3.0, 30.0)

        # Same actual radiation should give lower cloud cover percentage at lower elevation
        # because the actual radiation represents a higher percentage of max
        assert cloud_cover_low < cloud_cover_high

        # Test extreme case: very low elevation
        cloud_cover_very_low = analyzer.analyze_cloud_cover(200.0, 20000.0, 2.0, 10.0)
        assert isinstance(cloud_cover_very_low, float)
        assert 0 <= cloud_cover_very_low <= 100

    def test_astronomical_calculations_with_different_dates(self, analyzer):
        """Test astronomical calculations vary correctly with date."""
        import datetime

        # Test perihelion (closest to sun, highest radiation)
        rad_perihelion = analyzer._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 1, 4)
        )

        # Test aphelion (farthest from sun, lowest radiation)
        rad_aphelion = analyzer._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 7, 4)
        )

        # Perihelion should have higher radiation
        assert rad_perihelion > rad_aphelion

        # Test equinoxes (intermediate radiation)
        rad_spring = analyzer._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 3, 20)
        )

        rad_fall = analyzer._calculate_clear_sky_max_radiation(
            60.0, datetime.datetime(2024, 9, 22)
        )

        # Equinoxes should be between perihelion and aphelion
        assert rad_aphelion < rad_spring < rad_perihelion
        assert rad_aphelion < rad_fall < rad_perihelion

    def test_apply_condition_hysteresis_no_history(self, analyzer):
        """Test hysteresis with no previous condition history."""
        # First call should always return the proposed condition
        result = analyzer.apply_condition_hysteresis("sunny", 25.0)
        assert result == "sunny"

        # Check that history was initialized
        assert len(analyzer._condition_history) == 1
        assert analyzer._condition_history[0]["condition"] == "sunny"
        assert analyzer._condition_history[0]["cloud_cover"] == 25.0

    def test_apply_condition_hysteresis_same_condition(self, analyzer):
        """Test hysteresis when proposed condition is same as previous."""
        # Set up initial history
        analyzer._condition_history.append(
            {
                "condition": "sunny",
                "cloud_cover": 25.0,
                "timestamp": datetime.now(),
            }
        )

        # Same condition should be returned immediately
        result = analyzer.apply_condition_hysteresis("sunny", 30.0)
        assert result == "sunny"

        # History should be updated
        assert len(analyzer._condition_history) == 2
        assert analyzer._condition_history[-1]["condition"] == "sunny"
        assert analyzer._condition_history[-1]["cloud_cover"] == 30.0

    def test_apply_condition_hysteresis_sunny_to_partlycloudy_below_threshold(
        self, analyzer
    ):
        """Test hysteresis prevents sunny to partlycloudy when change is too small."""
        # Set up initial history with sunny condition
        analyzer._condition_history.append(
            {
                "condition": "sunny",
                "cloud_cover": 35.0,
                "timestamp": datetime.now(),
            }
        )

        # Try to change to partlycloudy with small cloud cover increase (only 5%)
        # Threshold is 15%, so this should be rejected
        result = analyzer.apply_condition_hysteresis("partlycloudy", 40.0)
        assert result == "sunny"  # Should maintain previous condition

        # History should record the rejected change attempt
        assert len(analyzer._condition_history) == 2
        assert (
            analyzer._condition_history[-1]["condition"] == "sunny"
        )  # Kept old condition
        assert (
            analyzer._condition_history[-1]["cloud_cover"] == 40.0
        )  # Recorded new cloud cover

    def test_apply_condition_hysteresis_sunny_to_partlycloudy_above_threshold(
        self, analyzer
    ):
        """Test hysteresis allows sunny to partlycloudy when change exceeds threshold."""
        # Set up initial history with sunny condition
        analyzer._condition_history.append(
            {
                "condition": "sunny",
                "cloud_cover": 30.0,
                "timestamp": datetime.now(),
            }
        )

        # Try to change to partlycloudy with significant cloud cover increase (20%)
        # Threshold is 15%, so this should be allowed
        result = analyzer.apply_condition_hysteresis("partlycloudy", 50.0)
        assert result == "partlycloudy"  # Should allow the change

        # History should record the successful change
        assert len(analyzer._condition_history) == 2
        assert analyzer._condition_history[-1]["condition"] == "partlycloudy"
        assert analyzer._condition_history[-1]["cloud_cover"] == 50.0

    def test_apply_condition_hysteresis_partlycloudy_to_sunny_below_threshold(
        self, analyzer
    ):
        """Test hysteresis prevents partlycloudy to sunny when change is too small."""
        # Set up initial history with partlycloudy condition
        analyzer._condition_history.append(
            {
                "condition": "partlycloudy",
                "cloud_cover": 45.0,
                "timestamp": datetime.now(),
            }
        )

        # Try to change to sunny with small cloud cover decrease (only 8%)
        # Threshold is 15%, so this should be rejected
        result = analyzer.apply_condition_hysteresis("sunny", 37.0)
        assert result == "partlycloudy"  # Should maintain previous condition

    def test_apply_condition_hysteresis_partlycloudy_to_sunny_above_threshold(
        self, analyzer
    ):
        """Test hysteresis allows partlycloudy to sunny when change exceeds threshold."""
        # Set up initial history with partlycloudy condition
        analyzer._condition_history.append(
            {
                "condition": "partlycloudy",
                "cloud_cover": 50.0,
                "timestamp": datetime.now(),
            }
        )

        # Try to change to sunny with significant cloud cover decrease (25%)
        # Threshold is 15%, so this should be allowed
        result = analyzer.apply_condition_hysteresis("sunny", 25.0)
        assert result == "sunny"  # Should allow the change

    def test_apply_condition_hysteresis_partlycloudy_to_cloudy_above_threshold(
        self, analyzer
    ):
        """Test hysteresis for partlycloudy to cloudy transition."""
        # Set up initial history with partlycloudy condition
        analyzer._condition_history.append(
            {
                "condition": "partlycloudy",
                "cloud_cover": 50.0,
                "timestamp": datetime.now(),
            }
        )

        # Try to change to cloudy with moderate cloud cover increase (15%)
        # Threshold for partlycloudy->cloudy is 10%, so this should be allowed
        result = analyzer.apply_condition_hysteresis("cloudy", 65.0)
        assert result == "cloudy"  # Should allow the change

    def test_apply_condition_hysteresis_cloudy_to_partlycloudy_below_threshold(
        self, analyzer
    ):
        """Test hysteresis prevents cloudy to partlycloudy when change is too small."""
        # Set up initial history with cloudy condition
        analyzer._condition_history.append(
            {
                "condition": "cloudy",
                "cloud_cover": 70.0,
                "timestamp": datetime.now(),
            }
        )

        # Try to change to partlycloudy with small cloud cover decrease (only 5%)
        # Threshold is 10%, so this should be rejected
        result = analyzer.apply_condition_hysteresis("partlycloudy", 65.0)
        assert result == "cloudy"  # Should maintain previous condition

    def test_apply_condition_hysteresis_unknown_transition(self, analyzer):
        """Test hysteresis with unknown transition (uses default threshold)."""
        # Set up initial history
        analyzer._condition_history.append(
            {
                "condition": "sunny",
                "cloud_cover": 20.0,
                "timestamp": datetime.now(),
            }
        )

        # Try a transition that doesn't have a specific threshold (should use 5% default)
        # First try with change below default threshold
        result = analyzer.apply_condition_hysteresis("cloudy", 23.0)  # Only 3% change
        assert result == "sunny"  # Should be rejected due to low threshold

        # Now try with change above default threshold from the original baseline
        # Since hysteresis uses the most recent history entry, we need a bigger change
        result = analyzer.apply_condition_hysteresis(
            "cloudy", 28.0
        )  # 8% change from last (23.0)
        assert result == "cloudy"  # Should be allowed

    def test_apply_condition_hysteresis_history_limit(self, analyzer):
        """Test that condition history is properly managed with time-based cleanup."""
        from datetime import timedelta

        # Add entries spanning more than 24 hours
        base_time = datetime.now()
        for i in range(15):
            # Spread entries over 30 hours (some will be old, some recent)
            timestamp = base_time - timedelta(
                hours=30 - i * 2
            )  # 0, 2, 4, ..., 28 hours ago
            analyzer._condition_history.append(
                {
                    "condition": "sunny",
                    "cloud_cover": 25.0 + i,
                    "timestamp": timestamp,
                }
            )

        # Before cleanup, should have all 15 entries
        assert len(analyzer._condition_history) == 15

        # Trigger cleanup by calling hysteresis (which does cleanup)
        analyzer.apply_condition_hysteresis("sunny", 25.0)

        # After cleanup, should only have entries from last 24 hours
        # (entries from 0-22 hours ago = 12 entries)
        assert len(analyzer._condition_history) <= 12  # Should be cleaned up

        # All remaining entries should be within 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        for entry in analyzer._condition_history:
            assert entry["timestamp"] > cutoff_time

        # The most recent entries should be preserved
        # (entries from most recent timestamps should be there)
        recent_entries = [
            entry
            for entry in analyzer._condition_history
            if entry["timestamp"] > base_time - timedelta(hours=24)
        ]
        assert len(recent_entries) > 0
