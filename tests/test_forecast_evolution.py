"""Test the weather system evolution modeling functionality."""

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
)
import pytest

from custom_components.micro_weather.forecast.evolution import (
    EvolutionModeler,
    LifecyclePhase,
    apply_confidence_clamping,
    find_lifecycle_phase,
)


@pytest.fixture
def evolution_modeler():
    """Create EvolutionModeler instance for testing."""
    return EvolutionModeler()


class TestEvolutionModeler:
    """Test the EvolutionModeler class."""

    def test_init(self, evolution_modeler):
        """Test EvolutionModeler initialization."""
        assert evolution_modeler is not None

    def test_model_system_evolution_stable_high(self, evolution_modeler):
        """Test system evolution modeling for stable high pressure."""
        meteorological_state = {
            "weather_system": {"type": "stable_high"},
            "atmospheric_stability": 0.8,
            "pressure_analysis": {"current_trend": 0.2},
        }

        result = evolution_modeler.model_system_evolution(meteorological_state)

        assert isinstance(result, dict)
        assert "evolution_path" in result
        assert "confidence_levels" in result
        assert "transition_probabilities" in result

        assert isinstance(result["evolution_path"], list)
        assert isinstance(result["confidence_levels"], list)
        assert isinstance(result["transition_probabilities"], dict)

        # Validate transition probabilities
        transitions = result["transition_probabilities"]
        assert "persistence" in transitions
        assert "gradual_change" in transitions
        assert "rapid_change" in transitions

        total_prob = sum(transitions.values())
        assert abs(total_prob - 1.0) < 0.01  # Should sum to approximately 1.0

    def test_model_system_evolution_active_low(self, evolution_modeler):
        """Test system evolution modeling for active low pressure."""
        meteorological_state = {
            "weather_system": {"type": "active_low"},
            "atmospheric_stability": 0.2,
            "pressure_analysis": {"current_trend": -1.0},
        }

        result = evolution_modeler.model_system_evolution(meteorological_state)

        assert isinstance(result, dict)
        assert len(result["evolution_path"]) > 0
        assert len(result["confidence_levels"]) > 0

    def test_model_system_evolution_frontal_system(self, evolution_modeler):
        """Test system evolution modeling for frontal system."""
        meteorological_state = {
            "weather_system": {"type": "frontal_system"},
            "atmospheric_stability": 0.5,
            "pressure_analysis": {"current_trend": -0.5},
        }

        result = evolution_modeler.model_system_evolution(meteorological_state)

        assert isinstance(result, dict)
        assert len(result["evolution_path"]) > 0
        assert len(result["confidence_levels"]) > 0

    def test_model_system_evolution_transitional(self, evolution_modeler):
        """Test system evolution modeling for transitional system."""
        meteorological_state = {
            "weather_system": {"type": "transitional"},
            "atmospheric_stability": 0.5,
            "pressure_analysis": {"current_trend": 0.0},
        }

        result = evolution_modeler.model_system_evolution(meteorological_state)

        assert isinstance(result, dict)
        assert len(result["evolution_path"]) > 0
        assert len(result["confidence_levels"]) > 0

    def test_model_hourly_evolution(self, evolution_modeler):
        """Test hourly weather evolution modeling."""
        meteorological_state = {
            "atmospheric_stability": 0.7,
            "weather_system": {"type": "stable_high"},
        }

        result = evolution_modeler.model_hourly_evolution(
            meteorological_state, hours=12
        )

        assert isinstance(result, dict)
        assert "hourly_changes" in result
        assert "confidence" in result
        assert "evolution_phase" in result

        assert isinstance(result["hourly_changes"], list)
        assert len(result["hourly_changes"]) == 12

        # Check structure of hourly changes
        for change in result["hourly_changes"]:
            assert "hour" in change
            assert "confidence" in change
            assert "expected_change" in change

    def test_calculate_micro_patterns(self, evolution_modeler):
        """Test micro-pattern calculation for hourly forecasts."""
        # Test different hours
        for hour_idx in [0, 6, 12, 18]:
            result = evolution_modeler.calculate_micro_patterns(hour_idx)

            assert isinstance(result, dict)
            assert "temperature_adjustment" in result
            assert "cloud_adjustment" in result

            assert isinstance(result["temperature_adjustment"], float)
            assert isinstance(result["cloud_adjustment"], float)

            # Should be reasonable adjustments
            assert -2.0 <= result["temperature_adjustment"] <= 2.0
            assert -5.0 <= result["cloud_adjustment"] <= 5.0


class TestLifecyclePhase:
    """Test the LifecyclePhase dataclass."""

    def test_dataclass_fields(self):
        phase = LifecyclePhase(
            name="frontal",
            start_hour=12.0,
            end_hour=18.0,
            condition=ATTR_CONDITION_RAINY,
            confidence=0.75,
        )
        assert phase.name == "frontal"
        assert phase.start_hour == 12.0
        assert phase.end_hour == 18.0
        assert phase.condition == ATTR_CONDITION_RAINY
        assert phase.confidence == 0.75


class TestFindLifecyclePhase:
    """Test find_lifecycle_phase()."""

    def test_finds_correct_phase(self):
        lifecycle = [
            LifecyclePhase("stable", 0.0, 12.0, ATTR_CONDITION_PARTLYCLOUDY, 0.85),
            LifecyclePhase("frontal", 12.0, 24.0, ATTR_CONDITION_RAINY, 0.75),
        ]
        phase = find_lifecycle_phase(lifecycle, 15.0)
        assert phase is not None
        assert phase.name == "frontal"

    def test_returns_first_phase_for_hour_zero(self):
        lifecycle = [
            LifecyclePhase("stable", 0.0, 24.0, ATTR_CONDITION_PARTLYCLOUDY, 0.85),
        ]
        phase = find_lifecycle_phase(lifecycle, 0.0)
        assert phase is not None
        assert phase.name == "stable"

    def test_returns_last_phase_when_hour_exceeds_all(self):
        lifecycle = [
            LifecyclePhase("stable", 0.0, 24.0, ATTR_CONDITION_SUNNY, 0.85),
            LifecyclePhase("clearing", 24.0, 72.0, ATTR_CONDITION_PARTLYCLOUDY, 0.55),
        ]
        phase = find_lifecycle_phase(lifecycle, 200.0)
        assert phase is not None
        assert phase.name == "clearing"

    def test_returns_none_for_empty_lifecycle(self):
        assert find_lifecycle_phase([], 10.0) is None


class TestApplyConfidenceClamping:
    """Test apply_confidence_clamping()."""

    def test_high_confidence_allows_any_condition(self):
        assert (
            apply_confidence_clamping(ATTR_CONDITION_POURING, 0.7)
            == ATTR_CONDITION_POURING
        )
        assert (
            apply_confidence_clamping(ATTR_CONDITION_SUNNY, 0.8) == ATTR_CONDITION_SUNNY
        )

    def test_medium_confidence_removes_extremes(self):
        assert (
            apply_confidence_clamping(ATTR_CONDITION_POURING, 0.5)
            == ATTR_CONDITION_RAINY
        )
        assert (
            apply_confidence_clamping(ATTR_CONDITION_LIGHTNING_RAINY, 0.5)
            == ATTR_CONDITION_RAINY
        )
        assert (
            apply_confidence_clamping(ATTR_CONDITION_RAINY, 0.5) == ATTR_CONDITION_RAINY
        )
        assert (
            apply_confidence_clamping(ATTR_CONDITION_CLOUDY, 0.5)
            == ATTR_CONDITION_CLOUDY
        )

    def test_low_confidence_forces_middle_ground(self):
        assert (
            apply_confidence_clamping(ATTR_CONDITION_POURING, 0.3)
            == ATTR_CONDITION_CLOUDY
        )
        assert (
            apply_confidence_clamping(ATTR_CONDITION_RAINY, 0.3)
            == ATTR_CONDITION_PARTLYCLOUDY
        )
        assert (
            apply_confidence_clamping(ATTR_CONDITION_SUNNY, 0.3)
            == ATTR_CONDITION_PARTLYCLOUDY
        )
        assert (
            apply_confidence_clamping(ATTR_CONDITION_CLOUDY, 0.35)
            == ATTR_CONDITION_CLOUDY
        )


class TestComputeLifecycle:
    """Test EvolutionModeler.compute_lifecycle()."""

    @pytest.fixture
    def modeler(self):
        return EvolutionModeler()

    def test_stable_returns_single_stable_phase(self, modeler):
        lifecycle = modeler.compute_lifecycle(
            trend=0.05,
            acceleration=0.0,
            storm_prob=0.0,
            current_condition=ATTR_CONDITION_SUNNY,
        )
        assert len(lifecycle) == 1
        assert lifecycle[0].name == "stable"
        assert lifecycle[0].condition == ATTR_CONDITION_SUNNY
        assert lifecycle[0].end_hour >= 120.0

    def test_falling_trend_produces_deteriorating_arc(self, modeler):
        lifecycle = modeler.compute_lifecycle(
            trend=-0.5,
            acceleration=0.0,
            storm_prob=10.0,
            current_condition=ATTR_CONDITION_SUNNY,
        )
        names = [p.name for p in lifecycle]
        assert "frontal" in names
        assert "post_frontal" in names
        assert "clearing" in names
        assert names.index("frontal") < names.index("post_frontal")

    def test_rising_trend_produces_improving_arc(self, modeler):
        lifecycle = modeler.compute_lifecycle(
            trend=0.5,
            acceleration=0.0,
            storm_prob=30.0,
            current_condition=ATTR_CONDITION_CLOUDY,
        )
        names = [p.name for p in lifecycle]
        assert "clearing" in names
        assert "stabilizing" in names
        assert names.index("clearing") < names.index("stabilizing")

    def test_lifecycle_covers_120_hours(self, modeler):
        for trend, storm_prob in [(-0.5, 0.0), (0.5, 40.0), (0.0, 0.0)]:
            lifecycle = modeler.compute_lifecycle(
                trend=trend,
                acceleration=0.0,
                storm_prob=storm_prob,
                current_condition=ATTR_CONDITION_CLOUDY,
            )
            assert lifecycle[-1].end_hour >= 120.0, f"Short coverage for trend={trend}"

    def test_phases_are_contiguous(self, modeler):
        lifecycle = modeler.compute_lifecycle(
            trend=-0.6,
            acceleration=-0.05,
            storm_prob=5.0,
            current_condition=ATTR_CONDITION_SUNNY,
        )
        for i in range(1, len(lifecycle)):
            assert (
                abs(lifecycle[i].start_hour - lifecycle[i - 1].end_hour) < 0.01
            ), f"Gap between phase {i - 1} and {i}"

    def test_model_system_evolution_includes_lifecycle_key(self, modeler):
        state = {
            "weather_system": {"type": "stable_high"},
            "atmospheric_stability": 0.8,
            "pressure_analysis": {
                "current_trend": -0.4,
                "long_term_trend": -0.3,
                "storm_probability": 10,
            },
            "pressure_acceleration": -0.02,
        }
        result = modeler.model_system_evolution(
            state, current_condition=ATTR_CONDITION_SUNNY
        )
        assert "lifecycle" in result
        assert isinstance(result["lifecycle"], list)
        assert len(result["lifecycle"]) > 0
