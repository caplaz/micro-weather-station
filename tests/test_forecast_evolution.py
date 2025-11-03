"""Test the weather system evolution modeling functionality."""

import pytest

from custom_components.micro_weather.forecast.evolution import EvolutionModeler


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
