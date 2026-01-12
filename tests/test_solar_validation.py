"""Test solar radiation validation logic."""
import logging
from unittest.mock import MagicMock

import pytest
from custom_components.micro_weather.analysis.solar import SolarAnalyzer
from custom_components.micro_weather.meteorological_constants import (
    SolarAnalysisConstants,
)


class TestSolarValidation:
    """Test solar radiation validation logic."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return SolarAnalyzer()

    def test_validation_suppresses_warning_for_small_ratio_excess(
        self, analyzer, caplog
    ):
        """Test that warning is suppressed when ratio is slightly high but within tolerance."""
        # Max: 100, Actual: 105 (Ratio 1.05)
        # Threshold is 1.10
        # Should NOT warn
        caplog.set_level(logging.WARNING)
        
        analyzer._calculate_cloud_cover_from_solar(
            avg_solar_radiation=105.0,
            solar_lux=50000.0,
            uv_index=5.0,
            max_solar_radiation=100.0,
            solar_elevation=45.0,
        )
        
        assert "Solar radiation exceeds clear-sky max" not in caplog.text

    def test_validation_suppresses_warning_for_small_absolute_excess(
        self, analyzer, caplog
    ):
        """Test that warning is suppressed when ratio is high but absolute diff is small."""
        # Max: 50, Actual: 60 (Ratio 1.20)
        # Ratio > 1.10 (True)
        # Abs Diff: 10.0 (Threshold 20.0) -> False
        # Should NOT warn
        caplog.set_level(logging.WARNING)
        
        analyzer._calculate_cloud_cover_from_solar(
            avg_solar_radiation=60.0,
            solar_lux=30000.0,
            uv_index=3.0,
            max_solar_radiation=50.0,
            solar_elevation=20.0,
        )
        
        assert "Solar radiation exceeds clear-sky max" not in caplog.text

    def test_validation_triggers_warning_for_large_excess(self, analyzer, caplog):
        """Test that warning triggers when both thresholds are exceeded."""
        # Max: 100, Actual: 150 (Ratio 1.5)
        # Ratio > 1.10 (True)
        # Abs Diff: 50.0 > 20.0 (True)
        # Should WARN
        caplog.set_level(logging.WARNING)
        
        analyzer._calculate_cloud_cover_from_solar(
            avg_solar_radiation=150.0,
            solar_lux=80000.0,
            uv_index=8.0,
            max_solar_radiation=100.0,
            solar_elevation=45.0,
        )
        
        assert "Solar radiation" in caplog.text
        assert "exceeds clear-sky max" in caplog.text
