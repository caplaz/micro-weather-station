"""Test the daily forecast generation functionality."""

from unittest.mock import Mock

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
)
import pytest

from custom_components.micro_weather.const import KEY_HUMIDITY, KEY_TEMPERATURE
from custom_components.micro_weather.forecast.daily import DailyForecastGenerator


@pytest.fixture
def mock_analyzers():
    """Create mock analyzer instances."""
    atmospheric = Mock()
    solar = Mock()
    trends = Mock()

    # Configure atmospheric methods
    atmospheric.analyze_pressure_trends = Mock(
        return_value={
            "pressure_system": "normal",
            "storm_probability": 20.0,
            "current_trend": 0.0,
            "long_term_trend": 0.0,
        }
    )
    atmospheric.analyze_wind_direction_trends = Mock(
        return_value={
            "average_direction": 180.0,
            "direction_stability": 0.8,
            "direction_change_rate": 10.0,
            "significant_shift": False,
            "prevailing_direction": "south",
        }
    )
    atmospheric.adjust_pressure_for_altitude = Mock(return_value=29.92)
    atmospheric.calculate_circular_mean = Mock(return_value=180.0)
    atmospheric.calculate_angular_difference = Mock(return_value=90.0)
    atmospheric.analyze_fog_conditions = Mock(return_value=ATTR_CONDITION_FOG)

    # Configure trends methods
    trends.get_historical_trends = Mock(
        side_effect=lambda sensor, hours=24: {
            "current": 60.0,
            "average": 58.0,
            "trend": 0.2,
            "min": 50.0,
            "max": 70.0,
            "volatility": 5.0,
        }
    )

    # Configure solar methods
    def mock_analyze_cloud_cover(*args, **kwargs):
        # Check if pressure trends indicate storm conditions
        if len(args) > 4 and isinstance(args[4], dict):
            pressure_trends = args[4]
            storm_prob = pressure_trends.get("storm_probability", 0)
            current_trend = pressure_trends.get("current_trend", 0)
            # Falling pressure (negative trend) increases cloud cover
            if storm_prob > 60 or current_trend < -0.3:
                return 85.0  # High cloud cover for storms/falling pressure
            elif current_trend < 0:
                return 65.0  # Moderate cloud cover for falling pressure
        return 40.0  # Normal cloud cover

    solar.analyze_cloud_cover = Mock(side_effect=mock_analyze_cloud_cover)

    return {
        "atmospheric": atmospheric,
        "solar": solar,
        "trends": trends,
    }


@pytest.fixture
def daily_forecast_generator(mock_analyzers):
    """Create DailyForecastGenerator instance for testing."""
    return DailyForecastGenerator(mock_analyzers["trends"])


class TestDailyForecastGenerator:
    """Test the DailyForecastGenerator class."""

    def test_init(self, daily_forecast_generator):
        """Test DailyForecastGenerator initialization."""
        assert daily_forecast_generator is not None
        assert daily_forecast_generator.trends_analyzer is not None

    def test_generate_forecast(self, daily_forecast_generator, mock_analyzers):
        """Test daily forecast generation."""
        current_condition = ATTR_CONDITION_PARTLYCLOUDY
        sensor_data = {
            "outdoor_temp": 72.0,
            "humidity": 60.0,
            "wind_speed": 5.0,
        }
        altitude = 100.0

        # Mock meteorological state
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 10.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.7,
            "cloud_analysis": {"cloud_cover": 40.0},
            "moisture_analysis": {"condensation_potential": 0.3},
            "wind_pattern_analysis": {
                "direction_stability": 0.8,
                "gradient_wind_effect": 3.0,
            },
            "current_conditions": {
                "humidity": 60.0,
            },
        }

        historical_patterns = {
            "temperature": {"volatility": 3.0},
            "seasonal_pattern": "normal",
        }

        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        result = daily_forecast_generator.generate_forecast(
            current_condition,
            sensor_data,
            altitude,
            meteorological_state,
            historical_patterns,
            system_evolution,
        )

        assert isinstance(result, list)
        assert len(result) == 5  # Should generate 5 days of forecast

        # Check forecast structure
        forecast_item = result[0]
        assert "datetime" in forecast_item
        assert "temperature" in forecast_item
        assert "templow" in forecast_item
        assert "condition" in forecast_item
        assert "precipitation" in forecast_item
        assert "wind_speed" in forecast_item
        assert "humidity" in forecast_item

        # Check temperature is reasonable
        assert isinstance(forecast_item["temperature"], float)
        assert forecast_item["temperature"] > 0

    def test_forecast_temperature(self, daily_forecast_generator, mock_analyzers):
        """Test temperature forecasting."""
        day_idx = 0
        current_temp = 70.0
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "current_trend": 0.1,
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns = {
            "temperature": {"volatility": 3.0},
        }
        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        result = daily_forecast_generator.forecast_temperature(
            day_idx,
            current_temp,
            meteorological_state,
            historical_patterns,
            system_evolution,
        )

        assert isinstance(result, float)
        assert 65 <= result <= 75  # Should be close to input temperature

    def test_forecast_condition(self, daily_forecast_generator, mock_analyzers):
        """Test condition forecasting."""
        day_idx = 0
        current_condition = ATTR_CONDITION_PARTLYCLOUDY
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 10.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.7,
            "cloud_analysis": {"cloud_cover": 40.0},
            "moisture_analysis": {"condensation_potential": 0.3},
        }
        historical_patterns = {}
        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        result = daily_forecast_generator.forecast_condition(
            day_idx,
            current_condition,
            meteorological_state,
            historical_patterns,
            system_evolution,
        )

        assert isinstance(result, str)
        assert result in [
            ATTR_CONDITION_SUNNY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
            ATTR_CONDITION_LIGHTNING_RAINY,
            ATTR_CONDITION_FOG,
            ATTR_CONDITION_SNOWY,
        ]

    def test_forecast_precipitation(self, daily_forecast_generator, mock_analyzers):
        """Test precipitation forecasting."""
        day_idx = 0
        condition = ATTR_CONDITION_PARTLYCLOUDY
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 20.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "moisture_analysis": {
                "transport_potential": 5.0,
                "condensation_potential": 0.3,
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns = {}
        sensor_data = {
            "rain_rate_unit": "mm",
        }

        result = daily_forecast_generator._forecast_precipitation(
            day_idx,
            condition,
            meteorological_state,
            historical_patterns,
            sensor_data,
        )

        assert isinstance(result, float)
        assert result >= 0

    def test_forecast_wind(self, daily_forecast_generator, mock_analyzers):
        """Test wind forecasting."""
        day_idx = 0
        current_wind = 5.0
        condition = ATTR_CONDITION_PARTLYCLOUDY
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
            },
            "wind_pattern_analysis": {
                "direction_stability": 0.8,
                "gradient_wind_effect": 3.0,
            },
        }
        historical_patterns = {
            "wind": {"volatility": 2.0},
        }

        result = daily_forecast_generator._forecast_wind(
            day_idx,
            current_wind,
            condition,
            meteorological_state,
            historical_patterns,
        )

        assert isinstance(result, float)
        assert result > 0

    def test_forecast_humidity(self, daily_forecast_generator, mock_analyzers):
        """Test humidity forecasting."""
        day_idx = 0
        current_humidity = 60.0
        meteorological_state = {
            "moisture_analysis": {"trend_direction": "increasing"},
            "atmospheric_stability": 0.7,
        }
        historical_patterns = {}
        condition = ATTR_CONDITION_PARTLYCLOUDY

        result = daily_forecast_generator._forecast_humidity(
            day_idx,
            current_humidity,
            meteorological_state,
            historical_patterns,
            condition,
        )

        assert isinstance(result, int)
        assert 10 <= result <= 100

    def test_calculate_seasonal_temperature_adjustment(self, daily_forecast_generator):
        """Test seasonal temperature adjustment calculation."""
        # Test all days in the 5-day cycle
        adjustments = []
        for day in range(5):
            adjustment = (
                daily_forecast_generator._calculate_seasonal_temperature_adjustment(day)
            )
            assert isinstance(adjustment, (int, float))
            adjustments.append(adjustment)

        # Should have some variation
        assert len(set(adjustments)) > 1  # Not all the same

        # Should be reasonable adjustments (±1-2 degrees)
        for adj in adjustments:
            assert -2 <= adj <= 2

    def test_calculate_pressure_temperature_influence(self, daily_forecast_generator):
        """Test pressure temperature influence calculation."""
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "high_pressure",
                "current_trend": 0.2,
                "long_term_trend": 0.1,
            }
        }

        result = daily_forecast_generator._calculate_pressure_temperature_influence(
            meteorological_state, 0
        )

        assert isinstance(result, float)

    def test_calculate_historical_pattern_influence(self, daily_forecast_generator):
        """Test historical pattern influence calculation."""
        historical_patterns = {
            "temperature": {"volatility": 3.0},
        }

        result = daily_forecast_generator._calculate_historical_pattern_influence(
            historical_patterns, 0, "temperature"
        )

        assert isinstance(result, float)

    def test_calculate_system_evolution_influence(self, daily_forecast_generator):
        """Test system evolution influence calculation."""
        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        result = daily_forecast_generator._calculate_system_evolution_influence(
            system_evolution, 0, "temperature"
        )

        assert isinstance(result, float)

    def test_calculate_temperature_range(self, daily_forecast_generator):
        """Test temperature range calculation."""
        meteorological_state = {
            "atmospheric_stability": 0.6,
            "current_conditions": {"humidity": 50.0},
        }

        # Test different conditions
        range_sunny = daily_forecast_generator._calculate_temperature_range(
            ATTR_CONDITION_SUNNY, meteorological_state
        )
        range_cloudy = daily_forecast_generator._calculate_temperature_range(
            ATTR_CONDITION_CLOUDY, meteorological_state
        )

        assert 2.0 <= range_sunny <= 15.0
        assert 2.0 <= range_cloudy <= 15.0

        # Sunny should have larger range than cloudy
        assert range_sunny >= range_cloudy

    def test_fog_condition_evolves_over_days(self, daily_forecast_generator):
        """Test that fog condition evolves differently for each day.

        Fog should progressively clear over multiple days, not remain static.
        This tests the fix for the bug where fog returned the same condition
        for all forecast days.
        """
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 10.0,
                "current_trend": 0.0,  # Neutral trajectory
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.7,
            "cloud_analysis": {"cloud_cover": 40.0},
            "moisture_analysis": {"condensation_potential": 0.3},
        }
        historical_patterns = {"humidity": {"trend": 0.0}}
        system_evolution = {}

        # Get conditions for each day starting from fog
        conditions = []
        for day_idx in range(5):
            condition = daily_forecast_generator.forecast_condition(
                day_idx,
                ATTR_CONDITION_FOG,
                meteorological_state,
                historical_patterns,
                system_evolution,
            )
            conditions.append(condition)

        # Fog should evolve over days - not all the same
        # Day 0 should be cloudy (trajectory 0), later days should improve
        assert conditions[0] == ATTR_CONDITION_CLOUDY  # Day 0: trajectory ~0
        # At least one later day should be different (clearer)
        assert (
            ATTR_CONDITION_PARTLYCLOUDY in conditions
            or ATTR_CONDITION_SUNNY in conditions
        )
        # Last day should be clearer than first day (fog clears over time)
        condition_order = [
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_SUNNY,
        ]
        first_day_idx = (
            condition_order.index(conditions[0])
            if conditions[0] in condition_order
            else 0
        )
        last_day_idx = (
            condition_order.index(conditions[4])
            if conditions[4] in condition_order
            else 0
        )
        assert last_day_idx >= first_day_idx, "Fog should clear over time, not worsen"

    def test_snowy_condition_evolves_over_days(self, daily_forecast_generator):
        """Test that snowy condition evolves differently for each day.

        Snow should progressively change over multiple days based on trajectory,
        not remain static for all forecast days.
        """
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 10.0,
                "current_trend": 0.0,  # Neutral trajectory
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.7,
            "cloud_analysis": {"cloud_cover": 40.0},
            "moisture_analysis": {"condensation_potential": 0.3},
        }
        historical_patterns = {"humidity": {"trend": 0.0}}
        system_evolution = {}

        # Get conditions for each day starting from snowy
        conditions = []
        for day_idx in range(5):
            condition = daily_forecast_generator.forecast_condition(
                day_idx,
                ATTR_CONDITION_SNOWY,
                meteorological_state,
                historical_patterns,
                system_evolution,
            )
            conditions.append(condition)

        # Snow should evolve over days - not all the same
        # With neutral trajectory, early days stay snowy, later days transition
        assert conditions[0] == ATTR_CONDITION_SNOWY  # Day 0: still snowing
        # At least one later day should be different
        unique_conditions = set(conditions)
        assert (
            len(unique_conditions) > 1
        ), "Snow should evolve over 5 days, not stay static"

    def test_fog_clears_faster_with_improving_trajectory(
        self, daily_forecast_generator
    ):
        """Test that fog clears faster when trajectory is improving (rising pressure)."""
        # Improving conditions (rising pressure)
        improving_state = {
            "pressure_analysis": {
                "pressure_system": "high",
                "storm_probability": 5.0,
                "current_trend": 0.5,  # Rising pressure
                "long_term_trend": 0.3,
            },
            "atmospheric_stability": 0.8,
            "cloud_analysis": {"cloud_cover": 20.0},
            "moisture_analysis": {"condensation_potential": 0.2},
        }
        historical_patterns = {"humidity": {"trend": -1.0}}  # Falling humidity
        system_evolution = {}

        # With improving trajectory, fog should clear quickly
        day_0 = daily_forecast_generator.forecast_condition(
            0,
            ATTR_CONDITION_FOG,
            improving_state,
            historical_patterns,
            system_evolution,
        )
        day_2 = daily_forecast_generator.forecast_condition(
            2,
            ATTR_CONDITION_FOG,
            improving_state,
            historical_patterns,
            system_evolution,
        )

        # Day 2 should be clearer than Day 0 with improving conditions
        condition_order = [
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_PARTLYCLOUDY,
            ATTR_CONDITION_SUNNY,
        ]
        if day_0 in condition_order and day_2 in condition_order:
            assert condition_order.index(day_2) >= condition_order.index(day_0)

    def test_forecast_variation_with_historical_patterns(
        self, daily_forecast_generator
    ):
        """Test that forecast days vary when historical patterns are provided."""
        current_condition = ATTR_CONDITION_SUNNY
        sensor_data = {
            "outdoor_temp": 70.0,
            "humidity": 50.0,
            "wind_speed": 5.0,
        }
        altitude = 100.0

        # Mock meteorological state
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 10.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.7,
            "cloud_analysis": {"cloud_cover": 20.0},
            "moisture_analysis": {"condensation_potential": 0.3},
            "wind_pattern_analysis": {
                "direction_stability": 0.8,
                "gradient_wind_effect": 3.0,
            },
            "current_conditions": {KEY_HUMIDITY: 50.0},
        }

        # Provide historical patterns with a trend
        historical_patterns = {
            "temperature": {"trend": -0.5, "volatility": 2.0},  # Cooling trend
            "seasonal_pattern": "normal",
        }

        system_evolution = {
            "evolution_path": ["stable_high", "transitional", "stable_high"],
            "confidence_levels": [0.8, 0.6, 0.7],
        }

        result = daily_forecast_generator.generate_forecast(
            current_condition,
            sensor_data,
            altitude,
            meteorological_state,
            historical_patterns,
            system_evolution,
        )

        # Extract temperatures
        temps = [day["temperature"] for day in result]

        # Verify temperatures are NOT all identical
        assert len(set(temps)) > 1, "Forecast temperatures should vary across days"

        # Verify cooling trend (first day vs last day)
        # Note: Day 0 is current day, Day 4 is 4 days out
        # With -0.5 trend, later days should be cooler
        assert temps[4] < temps[0], "Temperature should decrease with cooling trend"

    def test_humidity_dampening_on_temperature_range(self, daily_forecast_generator):
        """Test that high humidity reduces the diurnal temperature range."""
        condition = ATTR_CONDITION_SUNNY

        # Base state with high stability (which usually increases range)
        base_state = {"atmospheric_stability": 0.8, "current_conditions": {}}

        # Case 1: Low Humidity (30%) - Should have large range
        low_humidity_state = base_state.copy()
        low_humidity_state["current_conditions"] = {KEY_HUMIDITY: 30.0}

        range_low_humidity = daily_forecast_generator._calculate_temperature_range(
            condition, low_humidity_state
        )

        # Case 2: High Humidity (90%) - Should have reduced range
        high_humidity_state = base_state.copy()
        high_humidity_state["current_conditions"] = {KEY_HUMIDITY: 90.0}

        range_high_humidity = daily_forecast_generator._calculate_temperature_range(
            condition, high_humidity_state
        )

        # Verify high humidity results in smaller range
        assert (
            range_high_humidity < range_low_humidity
        ), f"High humidity range ({range_high_humidity}) should be smaller than low humidity range ({range_low_humidity})"

        # Verify the reduction is significant (at least 20% reduction)
        # 90% humidity -> factor 0.6 (40% reduction)
        assert range_high_humidity < range_low_humidity * 0.8

    def test_temperature_range_values_are_reasonable(self, daily_forecast_generator):
        """Test that calculated temperature ranges are within reasonable Fahrenheit bounds."""
        condition = ATTR_CONDITION_SUNNY
        meteorological_state = {
            "atmospheric_stability": 0.5,
            "current_conditions": {KEY_HUMIDITY: 50.0},
        }

        temp_range = daily_forecast_generator._calculate_temperature_range(
            condition, meteorological_state
        )

        # Should be between 3°F and 25°F
        assert (
            3.0 <= temp_range <= 25.0
        ), f"Temperature range {temp_range} is out of reasonable bounds"

    def test_forecast_min_temperature_calculation(self, daily_forecast_generator):
        """Test that min temperature is calculated correctly from max and range."""
        # Setup a specific scenario
        # Current temp 46, Sunny, High Humidity (91%)
        # This mimics the user's report

        current_temp = 46.0

        meteorological_state = {
            "atmospheric_stability": 0.8,  # High stability
            "current_conditions": {KEY_HUMIDITY: 91.0},  # High humidity
        }

        # We need to mock forecast_temperature to return 46.0
        daily_forecast_generator.forecast_temperature = Mock(return_value=current_temp)

        # Calculate range directly to verify dampening
        temp_range = daily_forecast_generator._calculate_temperature_range(
            ATTR_CONDITION_SUNNY, meteorological_state
        )

        # With 91% humidity, dampening factor is 1.0 - (21/50) = 0.58
        # Base Sunny (12.0) * Stability (1.3) = 15.6
        # 15.6 * 0.58 = ~9.05

        expected_range = 9.05
        tolerance = 1.0  # Allow some float variance

        assert (
            abs(temp_range - expected_range) < tolerance
        ), f"Calculated range {temp_range} should be close to {expected_range}"

        # Verify the resulting low would be ~37°F
        forecast_low = current_temp - temp_range
        assert (
            36.0 <= forecast_low <= 38.0
        ), f"Forecast low {forecast_low} should be around 37°F"

    def test_precipitation_reduction_and_cap(self, daily_forecast_generator):
        """Test that precipitation forecasts are reduced and capped (Fix for Issue #31)."""
        day_idx = 0
        condition = ATTR_CONDITION_RAINY  # Base 5.0 mm

        # Scenario from issue: Falling pressure, Stormy, High humidity (implied by 97%)
        # Let's create an aggressive scenario that previously caused 30mm+
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "low",
                "storm_probability": 80.0,  # High storm probability
                "current_trend": -0.6,  # Rapidly falling pressure
                "long_term_trend": -0.2,
            },
            "moisture_analysis": {
                "transport_potential": 5.0,
                "condensation_potential": 0.8,  # High condensation
            },
            "atmospheric_stability": 0.3,  # Unstable
        }

        historical_patterns = {KEY_HUMIDITY: {"trend": 2.0}}  # Rising humidity

        sensor_data = {"rain_rate_unit": "mm"}

        result = daily_forecast_generator._forecast_precipitation(
            day_idx,
            condition,
            meteorological_state,
            historical_patterns,
            sensor_data,
        )

        # Base: 5.0mm
        # Previous logic multipliers:
        #   Humidity: 1.5 (max)
        #   Pressure: 1.5 (Rapid fall)
        #   Storm Probability: 1.8 (High)
        #   Condensation: 1.5 (High)
        #   Total Multiplier: 1.5 * 1.5 * 1.8 * 1.5 = ~6.075
        #   Previous Result: 5.0 * 6.075 = ~30.375 mm (Matching the issue report of ~28mm)

        # New Logic Multipliers:
        #   Humidity: 1.2 (max cap reduced to 0.2)
        #   Pressure: 1.25 (Rapid fall reduced)
        #   Storm Probability: 1.2 (High reduced)
        #   Condensation: 1.16 (1 + 0.8*0.2)
        #   Uncapped Result: 5.0 * 1.2 * 1.25 * 1.2 * 1.16 = ~10.44 mm

        # Global Cap: Base * 2.0 = 10.0 mm

        # Verify result is significantly reduced from the 28-30mm seen in the issue
        assert (
            result < 20.0
        ), f"Precipitation {result} should be much less than the reported 28-30mm"

        # Verify it respects the cap (approx 10.0)
        assert (
            result <= 10.1
        ), f"Precipitation {result} should be close to or under the cap (10.0)"

        # Verify it's still reasonable (not zero)
        assert (
            result > 5.0
        ), "Precipitation should be increased from base due to conditions"

    def test_precipitation_by_condition(self, daily_forecast_generator, mock_analyzers):
        """Test base precipitation amounts for each weather condition."""
        day_idx = 0
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 0.0,  # No storm probability to avoid overrides
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "moisture_analysis": {
                "transport_potential": 0.0,
                "condensation_potential": 0.0,  # No condensation boost
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns = {}  # No trends
        sensor_data = {"rain_rate_unit": "mm"}

        # Test each condition's base precipitation
        test_cases = [
            (ATTR_CONDITION_LIGHTNING_RAINY, 7.0),
            (ATTR_CONDITION_POURING, 10.0),
            (ATTR_CONDITION_RAINY, 5.0),
            (ATTR_CONDITION_SNOWY, 3.0),
            (ATTR_CONDITION_CLOUDY, 0.5),
            (ATTR_CONDITION_FOG, 0.1),
            (ATTR_CONDITION_SUNNY, 0.0),
            (ATTR_CONDITION_PARTLYCLOUDY, 0.0),
        ]

        for condition, expected_base in test_cases:
            result = daily_forecast_generator._forecast_precipitation(
                day_idx,
                condition,
                meteorological_state,
                historical_patterns,
                sensor_data,
            )
            assert (
                abs(result - expected_base) < 0.1
            ), f"Condition {condition} should have base precipitation {expected_base}, got {result}"

    def test_precipitation_multipliers(self, daily_forecast_generator, mock_analyzers):
        """Test individual precipitation multiplier effects."""
        day_idx = 0
        condition = ATTR_CONDITION_RAINY  # Base 5.0 mm
        sensor_data = {"rain_rate_unit": "mm"}

        # Test humidity multiplier
        meteorological_state_humidity = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 0.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "moisture_analysis": {
                "transport_potential": 0.0,
                "condensation_potential": 0.0,
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns_humidity = {
            KEY_HUMIDITY: {"trend": 3.0}  # High rising humidity
        }

        result_humidity = daily_forecast_generator._forecast_precipitation(
            day_idx,
            condition,
            meteorological_state_humidity,
            historical_patterns_humidity,
            sensor_data,
        )
        # Should be increased from base 5.0 due to humidity
        assert (
            result_humidity > 5.0
        ), f"Humidity boost should increase precipitation from 5.0, got {result_humidity}"

        # Test pressure multiplier
        meteorological_state_pressure = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 0.0,
                "current_trend": -1.0,  # Rapidly falling pressure
                "long_term_trend": 0.0,
            },
            "moisture_analysis": {
                "transport_potential": 0.0,
                "condensation_potential": 0.0,
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns_pressure = {}

        result_pressure = daily_forecast_generator._forecast_precipitation(
            day_idx,
            condition,
            meteorological_state_pressure,
            historical_patterns_pressure,
            sensor_data,
        )
        # Should be increased from base 5.0 due to falling pressure
        assert (
            result_pressure > 5.0
        ), f"Pressure trend should increase precipitation from 5.0, got {result_pressure}"

        # Test storm probability multiplier
        meteorological_state_storm = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 80.0,  # High storm probability
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "moisture_analysis": {
                "transport_potential": 0.0,
                "condensation_potential": 0.0,
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns_storm = {}

        result_storm = daily_forecast_generator._forecast_precipitation(
            day_idx,
            condition,
            meteorological_state_storm,
            historical_patterns_storm,
            sensor_data,
        )
        # Should be increased from base 5.0 due to storm probability
        assert (
            result_storm > 5.0
        ), f"Storm probability should increase precipitation from 5.0, got {result_storm}"

    def test_precipitation_unit_conversion(
        self, daily_forecast_generator, mock_analyzers
    ):
        """Test precipitation unit conversion in forecasting."""
        day_idx = 0
        condition = ATTR_CONDITION_RAINY
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 0.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "moisture_analysis": {
                "transport_potential": 0.0,
                "condensation_potential": 0.0,
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns = {}

        # Test mm units (should remain unchanged)
        sensor_data_mm = {"rain_rate_unit": "mm"}
        result_mm = daily_forecast_generator._forecast_precipitation(
            day_idx,
            condition,
            meteorological_state,
            historical_patterns,
            sensor_data_mm,
        )
        assert (
            result_mm == 5.0
        ), f"MM units should give base precipitation 5.0, got {result_mm}"

        # Test inch units (should convert to inches)
        sensor_data_inches = {"rain_rate_unit": "in"}
        result_inches = daily_forecast_generator._forecast_precipitation(
            day_idx,
            condition,
            meteorological_state,
            historical_patterns,
            sensor_data_inches,
        )
        # Should be converted from mm to inches (5.0 mm / 25.4 = ~0.197 inches)
        expected_inches = 5.0 / 25.4
        assert (
            abs(result_inches - expected_inches) < 0.01
        ), f"Inch units should convert to inches: expected {expected_inches}, got {result_inches}"

    def test_precipitation_distance_dampening(
        self, daily_forecast_generator, mock_analyzers
    ):
        """Test that precipitation forecasts decrease for future days."""
        condition = ATTR_CONDITION_RAINY
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 0.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "moisture_analysis": {
                "transport_potential": 0.0,
                "condensation_potential": 0.0,
            },
            "atmospheric_stability": 0.7,
        }
        historical_patterns = {}
        sensor_data = {"rain_rate_unit": "mm"}

        # Get precipitation for each day
        results = []
        for day_idx in range(5):
            result = daily_forecast_generator._forecast_precipitation(
                day_idx,
                condition,
                meteorological_state,
                historical_patterns,
                sensor_data,
            )
            results.append(result)

        # Verify day 0 has base precipitation
        assert (
            results[0] == 5.0
        ), f"Day 0 should have base precipitation 5.0, got {results[0]}"

        # Verify subsequent days are reduced
        for i in range(1, 5):
            assert (
                results[i] < results[0]
            ), f"Day {i} precipitation {results[i]} should be less than day 0 {results[0]}"
            # Should decrease by approximately 15% per day
            expected_reduction = results[0] * max(0.3, 1.0 - (i * 0.15))
            assert (
                abs(results[i] - expected_reduction) < 0.1
            ), f"Day {i} should be dampened to ~{expected_reduction}, got {results[i]}"

    def test_temperature_forecast_has_daily_variation(self, daily_forecast_generator):
        """Test that temperature forecasts vary day-to-day based on historical volatility.

        When temperature trends are 0 and pressure is stable, forecasts should
        still show natural day-to-day variation based on observed volatility
        to avoid identical values for all 5 forecast days.
        """
        # Stable conditions with no trends but observed volatility
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 10.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.5,
            "cloud_analysis": {"cloud_cover": 50.0},
            "moisture_analysis": {"condensation_potential": 0.3},
            "current_conditions": {KEY_HUMIDITY: 60.0},
        }
        # Volatility of 5.0 means we've observed ~5°F swings in temperature
        historical_patterns = {KEY_TEMPERATURE: {"trend": 0.0, "volatility": 5.0}}
        system_evolution = {"confidence_levels": [0.9, 0.8, 0.7, 0.6, 0.5]}
        current_temp = 50.0

        # Get temperatures for all 5 days
        temps = []
        for day_idx in range(5):
            temp = daily_forecast_generator.forecast_temperature(
                day_idx,
                current_temp,
                meteorological_state,
                historical_patterns,
                system_evolution,
            )
            temps.append(temp)

        # Temperatures should NOT all be identical
        unique_temps = set(round(t, 1) for t in temps)
        assert (
            len(unique_temps) > 1
        ), f"Forecasts should vary day-to-day, but got identical values: {temps}"

        # Verify reasonable spread based on volatility
        temp_range = max(temps) - min(temps)
        assert (
            temp_range >= 2.0
        ), f"With volatility=5.0, temp range should be at least 2°F, but was {temp_range}"

    def test_temperature_variation_scales_with_volatility(
        self, daily_forecast_generator
    ):
        """Test that temperature variation scales with historical volatility.

        Higher volatility in historical data should produce larger day-to-day
        variations in the forecast. Low volatility should produce smaller swings.
        """
        meteorological_state = {
            "pressure_analysis": {
                "pressure_system": "normal",
                "storm_probability": 10.0,
                "current_trend": 0.0,
                "long_term_trend": 0.0,
            },
            "atmospheric_stability": 0.5,
            "cloud_analysis": {"cloud_cover": 50.0},
            "moisture_analysis": {"condensation_potential": 0.3},
            "current_conditions": {KEY_HUMIDITY: 60.0},
        }
        system_evolution = {"confidence_levels": [0.9, 0.8, 0.7, 0.6, 0.5]}
        current_temp = 50.0

        # Test with LOW volatility (stable weather history)
        low_volatility_patterns = {KEY_TEMPERATURE: {"trend": 0.0, "volatility": 1.0}}
        low_temps = []
        for day_idx in range(5):
            temp = daily_forecast_generator.forecast_temperature(
                day_idx,
                current_temp,
                meteorological_state,
                low_volatility_patterns,
                system_evolution,
            )
            low_temps.append(temp)
        low_range = max(low_temps) - min(low_temps)

        # Test with HIGH volatility (variable weather history)
        high_volatility_patterns = {KEY_TEMPERATURE: {"trend": 0.0, "volatility": 8.0}}
        high_temps = []
        for day_idx in range(5):
            temp = daily_forecast_generator.forecast_temperature(
                day_idx,
                current_temp,
                meteorological_state,
                high_volatility_patterns,
                system_evolution,
            )
            high_temps.append(temp)
        high_range = max(high_temps) - min(high_temps)

        # Higher volatility should produce larger variation
        assert (
            high_range > low_range
        ), f"High volatility range ({high_range}) should exceed low ({low_range})"
