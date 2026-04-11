# Trend-Based Lifecycle Forecast Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the snapshot-propagation forecast with a weather system lifecycle engine that infers when a front arrives/departs and assigns each forecast slot a lifecycle phase with confidence-based clamping.

**Architecture:** `TrendsAnalyzer` gains pressure acceleration; `EvolutionModeler` gains `LifecyclePhase` dataclass + `compute_lifecycle()` method, and is now actually wired up in `weather_detector.py`/`weather.py` instead of passing `{}`; `DailyForecastGenerator.forecast_condition()` and `HourlyForecastGenerator.forecast_condition()` replace their trajectory-step logic with a lifecycle phase lookup.

**Tech Stack:** Python 3.13, pytest (asyncio_mode=auto), homeassistant stubs

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `custom_components/micro_weather/analysis/trends.py` | Add `compute_pressure_acceleration()` |
| Modify | `custom_components/micro_weather/forecast/evolution.py` | Add `LifecyclePhase`, `find_lifecycle_phase()`, `apply_confidence_clamping()`, `compute_lifecycle()`, update `model_system_evolution()` |
| Modify | `custom_components/micro_weather/forecast/__init__.py` | Export new public names |
| Modify | `custom_components/micro_weather/forecast/daily.py` | Replace `forecast_condition()` body; remove `_calculate_condition_trajectory`, `_evolve_condition_by_trajectory` |
| Modify | `custom_components/micro_weather/forecast/hourly.py` | Replace `forecast_condition()` body; remove `_calculate_hourly_trajectory`, `_evolve_hourly_condition` |
| Modify | `custom_components/micro_weather/weather_detector.py` | Instantiate `EvolutionModeler`; compute lifecycle; pass it as `system_evolution` |
| Modify | `custom_components/micro_weather/weather.py` | Same wiring for both daily and hourly forecasts |
| Modify | `tests/test_analysis_trends.py` | Tests for `compute_pressure_acceleration()` |
| Modify | `tests/test_forecast_evolution.py` | Tests for `LifecyclePhase`, `compute_lifecycle()`, helpers |
| Modify | `tests/test_forecast_daily.py` | Tests for lifecycle-based `forecast_condition()` in daily |
| Modify | `tests/test_forecast_hourly.py` | Tests for lifecycle-based `forecast_condition()` in hourly |
| Modify | `tests/test_weather_detector.py` | End-to-end arc tests: deteriorating / improving / stable |
| Modify | `WEATHER_FORECAST_ALGORITHM.md` | Rewrite condition-forecasting sections |

---

## Task 1: Create feature branch

**Files:** none

- [ ] **Step 1: Create and switch to feature branch**

```bash
git checkout -b feature/trend-based-lifecycle-forecast
```

Expected: `Switched to a new branch 'feature/trend-based-lifecycle-forecast'`

---

## Task 2: `TrendsAnalyzer.compute_pressure_acceleration()`

**Files:**
- Modify: `custom_components/micro_weather/analysis/trends.py` (add after `analyze_pressure_trends`)
- Test: `tests/test_analysis_trends.py` (add to `TestTrendsAnalyzer`)

### What it does

Splits the last N pressure readings in `_sensor_history["pressure"]` into two equal halves, computes the linear trend slope for each using the existing `calculate_trend()` method, and returns `slope_second_half - slope_first_half`.

- Negative result → fall is accelerating (fast-moving front)
- Positive result → fall is decelerating (stalling front)
- ~0.0 → steady trend or insufficient data

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_analysis_trends.py` inside `TestTrendsAnalyzer`:

```python
def test_compute_pressure_acceleration_falling_fast(self):
    """Acceleration is negative when pressure fall speeds up."""
    from collections import deque
    from datetime import datetime, timedelta

    history = {"pressure": deque(maxlen=192)}
    base_time = datetime.now()
    # First 6 readings: slow fall (-0.01/h), next 6: fast fall (-0.05/h)
    for i in range(6):
        history["pressure"].append(
            {"timestamp": base_time - timedelta(hours=11 - i), "value": 30.0 - i * 0.01}
        )
    for i in range(6):
        history["pressure"].append(
            {"timestamp": base_time - timedelta(hours=5 - i), "value": 29.94 - i * 0.05}
        )
    analyzer = TrendsAnalyzer(history)
    accel = analyzer.compute_pressure_acceleration()
    assert accel < 0, f"Expected negative acceleration, got {accel}"

def test_compute_pressure_acceleration_stable(self):
    """Acceleration is near zero for flat pressure."""
    from collections import deque
    from datetime import datetime, timedelta

    history = {"pressure": deque(maxlen=192)}
    base_time = datetime.now()
    for i in range(12):
        history["pressure"].append(
            {"timestamp": base_time - timedelta(hours=11 - i), "value": 29.92}
        )
    analyzer = TrendsAnalyzer(history)
    accel = analyzer.compute_pressure_acceleration()
    assert abs(accel) < 0.01, f"Expected near-zero acceleration, got {accel}"

def test_compute_pressure_acceleration_insufficient_data(self):
    """Returns 0.0 when fewer than 4 readings are available."""
    from collections import deque
    from datetime import datetime

    history = {"pressure": deque(maxlen=192)}
    history["pressure"].append({"timestamp": datetime.now(), "value": 29.92})
    analyzer = TrendsAnalyzer(history)
    assert analyzer.compute_pressure_acceleration() == 0.0

def test_compute_pressure_acceleration_missing_key(self):
    """Returns 0.0 when no pressure history exists."""
    analyzer = TrendsAnalyzer({})
    assert analyzer.compute_pressure_acceleration() == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_analysis_trends.py::TestTrendsAnalyzer::test_compute_pressure_acceleration_falling_fast tests/test_analysis_trends.py::TestTrendsAnalyzer::test_compute_pressure_acceleration_stable tests/test_analysis_trends.py::TestTrendsAnalyzer::test_compute_pressure_acceleration_insufficient_data tests/test_analysis_trends.py::TestTrendsAnalyzer::test_compute_pressure_acceleration_missing_key -v
```

Expected: 4 FAILs — `AttributeError: 'TrendsAnalyzer' object has no attribute 'compute_pressure_acceleration'`

- [ ] **Step 3: Implement `compute_pressure_acceleration()` in `trends.py`**

Add this method after `analyze_pressure_trends` (around line 334):

```python
def compute_pressure_acceleration(self) -> float:
    """Compute pressure trend acceleration from the last 24h of readings.

    Splits pressure history into two equal halves, computes the linear
    trend slope for each using calculate_trend(), and returns the
    difference (slope_second - slope_first).

    Returns:
        float: Acceleration in inHg/3h² (negative = fall speeding up,
               positive = fall slowing, ~0.0 = steady or insufficient data)
    """
    if "pressure" not in self._sensor_history:
        return 0.0

    entries = list(self._sensor_history["pressure"])
    if len(entries) < 4:
        return 0.0

    midpoint = len(entries) // 2
    first_half = entries[:midpoint]
    second_half = entries[midpoint:]

    def _slope(half: list) -> float:
        timestamps = [e["timestamp"] for e in half]
        values = [e["value"] for e in half]
        if isinstance(timestamps[0], (int, float)):
            time_diffs = [float(t - timestamps[0]) for t in timestamps]
        else:
            time_diffs = [
                (t - timestamps[0]).total_seconds() / 3600 for t in timestamps
            ]
        return self.calculate_trend(time_diffs, values)

    return _slope(second_half) - _slope(first_half)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_analysis_trends.py::TestTrendsAnalyzer::test_compute_pressure_acceleration_falling_fast tests/test_analysis_trends.py::TestTrendsAnalyzer::test_compute_pressure_acceleration_stable tests/test_analysis_trends.py::TestTrendsAnalyzer::test_compute_pressure_acceleration_insufficient_data tests/test_analysis_trends.py::TestTrendsAnalyzer::test_compute_pressure_acceleration_missing_key -v
```

Expected: 4 PASSED

- [ ] **Step 5: Run the full trends test suite to confirm nothing broke**

```bash
python -m pytest tests/test_analysis_trends.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add custom_components/micro_weather/analysis/trends.py tests/test_analysis_trends.py
git commit -m "feat: add TrendsAnalyzer.compute_pressure_acceleration()"
```

---

## Task 3: Lifecycle types and compute logic in `evolution.py`

**Files:**
- Modify: `custom_components/micro_weather/forecast/evolution.py`
- Modify: `custom_components/micro_weather/forecast/__init__.py`
- Test: `tests/test_forecast_evolution.py`

### What it does

Adds to `evolution.py`:
- `LifecyclePhase` — frozen dataclass with `name, start_hour, end_hour, condition, confidence`
- `find_lifecycle_phase(lifecycle, slot_hour)` — returns the phase containing `slot_hour`
- `apply_confidence_clamping(condition, confidence)` — clamps extreme conditions at low confidence
- `EvolutionModeler.compute_lifecycle(trend, acceleration, storm_prob, current_condition)` — builds the phase list
- Update `EvolutionModeler.model_system_evolution()` to accept optional `current_condition` and return `lifecycle` key

### Confidence clamping rules
- `confidence >= 0.6`: any condition allowed
- `0.4 <= confidence < 0.6`: no extremes — `pouring`/`lightning-rainy` → `rainy`; `snowy` → `cloudy`
- `confidence < 0.4`: only `cloudy` or `partlycloudy` — rainy/sunny → partlycloudy; pouring/lightning → cloudy

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_forecast_evolution.py`:

```python
from custom_components.micro_weather.forecast.evolution import (
    LifecyclePhase,
    apply_confidence_clamping,
    find_lifecycle_phase,
)
from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
)


class TestLifecyclePhase:
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
    def test_high_confidence_allows_any_condition(self):
        assert apply_confidence_clamping(ATTR_CONDITION_POURING, 0.7) == ATTR_CONDITION_POURING
        assert apply_confidence_clamping(ATTR_CONDITION_SUNNY, 0.8) == ATTR_CONDITION_SUNNY

    def test_medium_confidence_removes_extremes(self):
        assert apply_confidence_clamping(ATTR_CONDITION_POURING, 0.5) == ATTR_CONDITION_RAINY
        assert apply_confidence_clamping(ATTR_CONDITION_LIGHTNING_RAINY, 0.5) == ATTR_CONDITION_RAINY
        assert apply_confidence_clamping(ATTR_CONDITION_RAINY, 0.5) == ATTR_CONDITION_RAINY
        assert apply_confidence_clamping(ATTR_CONDITION_CLOUDY, 0.5) == ATTR_CONDITION_CLOUDY

    def test_low_confidence_forces_middle_ground(self):
        assert apply_confidence_clamping(ATTR_CONDITION_POURING, 0.3) == ATTR_CONDITION_CLOUDY
        assert apply_confidence_clamping(ATTR_CONDITION_RAINY, 0.3) == ATTR_CONDITION_PARTLYCLOUDY
        assert apply_confidence_clamping(ATTR_CONDITION_SUNNY, 0.3) == ATTR_CONDITION_PARTLYCLOUDY
        assert apply_confidence_clamping(ATTR_CONDITION_CLOUDY, 0.35) == ATTR_CONDITION_CLOUDY


class TestComputeLifecycle:
    """Test EvolutionModeler.compute_lifecycle()."""

    def test_stable_returns_single_stable_phase(self, evolution_modeler):
        """Near-zero trend → single stable phase spanning full horizon."""
        lifecycle = evolution_modeler.compute_lifecycle(
            trend=0.05,
            acceleration=0.0,
            storm_prob=0.0,
            current_condition=ATTR_CONDITION_SUNNY,
        )
        assert len(lifecycle) == 1
        assert lifecycle[0].name == "stable"
        assert lifecycle[0].condition == ATTR_CONDITION_SUNNY
        assert lifecycle[0].end_hour >= 120.0

    def test_falling_trend_produces_deteriorating_arc(self, evolution_modeler):
        """Falling pressure → pre_frontal, frontal, post_frontal, clearing, stabilizing."""
        lifecycle = evolution_modeler.compute_lifecycle(
            trend=-0.5,
            acceleration=0.0,
            storm_prob=10.0,
            current_condition=ATTR_CONDITION_SUNNY,
        )
        names = [p.name for p in lifecycle]
        assert "frontal" in names
        assert "post_frontal" in names
        assert "clearing" in names
        # Frontal must come before post_frontal
        assert names.index("frontal") < names.index("post_frontal")

    def test_rising_trend_produces_improving_arc(self, evolution_modeler):
        """Rising pressure → post_frontal, clearing, stabilizing."""
        lifecycle = evolution_modeler.compute_lifecycle(
            trend=0.5,
            acceleration=0.0,
            storm_prob=30.0,
            current_condition=ATTR_CONDITION_CLOUDY,
        )
        names = [p.name for p in lifecycle]
        assert "clearing" in names
        assert "stabilizing" in names
        clearing_idx = names.index("clearing")
        stabilizing_idx = names.index("stabilizing")
        assert clearing_idx < stabilizing_idx

    def test_lifecycle_covers_120_hours(self, evolution_modeler):
        """All lifecycle lists must cover at least 120 hours."""
        for trend, storm_prob in [(-0.5, 0.0), (0.5, 40.0), (0.0, 0.0)]:
            lifecycle = evolution_modeler.compute_lifecycle(
                trend=trend, acceleration=0.0, storm_prob=storm_prob,
                current_condition=ATTR_CONDITION_CLOUDY,
            )
            assert lifecycle[-1].end_hour >= 120.0, f"Short coverage for trend={trend}"

    def test_phases_are_contiguous(self, evolution_modeler):
        """Each phase must start exactly where the previous one ended."""
        lifecycle = evolution_modeler.compute_lifecycle(
            trend=-0.6, acceleration=-0.05, storm_prob=5.0,
            current_condition=ATTR_CONDITION_SUNNY,
        )
        for i in range(1, len(lifecycle)):
            assert abs(lifecycle[i].start_hour - lifecycle[i - 1].end_hour) < 0.01, \
                f"Gap between phase {i-1} and {i}"

    def test_model_system_evolution_includes_lifecycle_key(self, evolution_modeler):
        """model_system_evolution now returns a 'lifecycle' key."""
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
        result = evolution_modeler.model_system_evolution(
            state, current_condition=ATTR_CONDITION_SUNNY
        )
        assert "lifecycle" in result
        assert isinstance(result["lifecycle"], list)
        assert len(result["lifecycle"]) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_forecast_evolution.py::TestLifecyclePhase tests/test_forecast_evolution.py::TestFindLifecyclePhase tests/test_forecast_evolution.py::TestApplyConfidenceClamping tests/test_forecast_evolution.py::TestComputeLifecycle -v
```

Expected: FAILs — `ImportError` / `AttributeError`

- [ ] **Step 3: Implement in `evolution.py`**

At the top of `evolution.py`, after the existing imports, add:

```python
import math
from dataclasses import dataclass

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
)
```

After the imports and before the `EvolutionModeler` class, add:

```python
@dataclass
class LifecyclePhase:
    """A named phase in a weather system's lifecycle.

    Attributes:
        name: Phase identifier (stable, pre_frontal, frontal,
              post_frontal, clearing, stabilizing)
        start_hour: Hours from now when this phase begins (0 = present)
        end_hour: Hours from now when this phase ends
        condition: HA weather condition string for this phase
        confidence: Base confidence for this phase (0.0–1.0)
    """

    name: str
    start_hour: float
    end_hour: float
    condition: str
    confidence: float


def find_lifecycle_phase(
    lifecycle: list["LifecyclePhase"], slot_hour: float
) -> "LifecyclePhase | None":
    """Return the phase that contains slot_hour.

    Returns the phase where start_hour <= slot_hour < end_hour.
    If slot_hour falls beyond all phases, returns the last phase.
    Returns None if lifecycle is empty.

    Args:
        lifecycle: Ordered list of LifecyclePhase objects
        slot_hour: Hours from now to look up

    Returns:
        Matching LifecyclePhase or None
    """
    if not lifecycle:
        return None
    for phase in lifecycle:
        if phase.start_hour <= slot_hour < phase.end_hour:
            return phase
    return lifecycle[-1]


def apply_confidence_clamping(condition: str, confidence: float) -> str:
    """Clamp extreme weather conditions at low confidence levels.

    Confidence tiers:
    - >= 0.6: any condition allowed
    - 0.4–0.59: no extremes (pouring/lightning-rainy → rainy)
    - < 0.4: only cloudy or partlycloudy

    Args:
        condition: HA weather condition string
        confidence: Confidence score (0.0–1.0)

    Returns:
        Possibly-clamped condition string
    """
    if confidence >= 0.6:
        return condition

    if confidence >= 0.4:
        # Remove extremes
        if condition in (ATTR_CONDITION_POURING, ATTR_CONDITION_LIGHTNING_RAINY):
            return ATTR_CONDITION_RAINY
        return condition

    # Very low confidence — only middle ground
    if condition in (ATTR_CONDITION_POURING, ATTR_CONDITION_LIGHTNING_RAINY):
        return ATTR_CONDITION_CLOUDY
    if condition in (ATTR_CONDITION_RAINY, ATTR_CONDITION_SUNNY):
        return ATTR_CONDITION_PARTLYCLOUDY
    if condition in (ATTR_CONDITION_CLOUDY, ATTR_CONDITION_PARTLYCLOUDY):
        return condition
    return ATTR_CONDITION_PARTLYCLOUDY
```

Add these methods to `EvolutionModeler`:

```python
def compute_lifecycle(
    self,
    trend: float,
    acceleration: float,
    storm_prob: float,
    current_condition: str = ATTR_CONDITION_CLOUDY,
) -> list[LifecyclePhase]:
    """Compute weather system lifecycle phases from pressure trend data.

    Uses pressure trend and its acceleration to estimate when incoming
    or outgoing weather system phases occur. All timings are relative
    to "now" (hour 0). The returned list always covers at least 120
    hours (5 days).

    Args:
        trend: Current pressure trend in inHg/3h (negative = falling)
        acceleration: Trend acceleration in inHg/3h² (from
                      TrendsAnalyzer.compute_pressure_acceleration)
        storm_prob: Current storm probability 0–100
        current_condition: Current HA condition for the stable phase

    Returns:
        List[LifecyclePhase]: Ordered phases with no gaps
    """
    from ..meteorological_constants import PressureTrendConstants

    total_hours = 120.0

    if abs(trend) < PressureTrendConstants.STABLE_THRESHOLD:
        return [
            LifecyclePhase(
                name="stable",
                start_hour=0.0,
                end_hour=total_hours,
                condition=current_condition,
                confidence=0.85,
            )
        ]

    if trend < 0:
        return self._compute_deteriorating_lifecycle(
            trend, acceleration, storm_prob, total_hours
        )
    return self._compute_improving_lifecycle(
        trend, acceleration, storm_prob, total_hours
    )

def _compute_deteriorating_lifecycle(
    self,
    trend: float,
    acceleration: float,
    storm_prob: float,
    total_hours: float,
) -> list[LifecyclePhase]:
    """Build lifecycle phases for a deteriorating (falling pressure) scenario."""
    from ..meteorological_constants import ForecastConstants

    abs_trend = max(abs(trend), 0.1)

    # Hours until storm probability threshold is reached
    hours_to_frontal = max(
        0.0,
        (ForecastConstants.STORM_THRESHOLD_SEVERE - storm_prob) / (abs_trend * 5.0),
    )
    # Fast front (high acceleration magnitude) = short peak
    peak_duration = 6.0 if abs(acceleration) > 0.1 else 12.0
    rebound_hours = max(6.0, peak_duration * (1.0 + abs(acceleration)))

    # Frontal condition severity based on current storm_prob
    if storm_prob > ForecastConstants.STORM_THRESHOLD_SEVERE:
        frontal_condition = ATTR_CONDITION_LIGHTNING_RAINY
    elif storm_prob > ForecastConstants.STORM_THRESHOLD_MODERATE:
        frontal_condition = ATTR_CONDITION_POURING
    else:
        frontal_condition = ATTR_CONDITION_RAINY

    phases: list[LifecyclePhase] = []
    t = 0.0

    # Quiet period before clouds build (stable → pre_frontal boundary is 6h before arrival)
    pre_frontal_start = max(0.0, hours_to_frontal - 6.0)
    if pre_frontal_start > 0.0:
        phases.append(
            LifecyclePhase("stable", t, pre_frontal_start, ATTR_CONDITION_PARTLYCLOUDY, 0.85)
        )
        t = pre_frontal_start

    # Clouds building ahead of the front
    if hours_to_frontal > t:
        phases.append(
            LifecyclePhase("pre_frontal", t, hours_to_frontal, ATTR_CONDITION_CLOUDY, 0.80)
        )
        t = hours_to_frontal

    # Frontal passage
    frontal_end = t + peak_duration
    phases.append(LifecyclePhase("frontal", t, frontal_end, frontal_condition, 0.75))
    t = frontal_end

    # Post-frontal (unsettled)
    post_frontal_end = t + rebound_hours
    phases.append(
        LifecyclePhase("post_frontal", t, post_frontal_end, ATTR_CONDITION_CLOUDY, 0.65)
    )
    t = post_frontal_end

    # Clearing
    clearing_end = t + rebound_hours
    phases.append(
        LifecyclePhase("clearing", t, clearing_end, ATTR_CONDITION_PARTLYCLOUDY, 0.55)
    )
    t = clearing_end

    # Stabilizing — fill to total_hours
    if t < total_hours:
        phases.append(
            LifecyclePhase("stabilizing", t, total_hours, ATTR_CONDITION_SUNNY, 0.45)
        )

    return phases

def _compute_improving_lifecycle(
    self,
    trend: float,
    acceleration: float,
    storm_prob: float,
    total_hours: float,
) -> list[LifecyclePhase]:
    """Build lifecycle phases for an improving (rising pressure) scenario."""
    abs_trend = max(abs(trend), 0.1)

    # Hours until conditions clear (storm_prob → 0 at current rate)
    hours_to_clear = max(0.0, storm_prob / (abs_trend * 5.0))
    rebound_hours = max(12.0, 12.0 * (1.0 + abs(acceleration)))

    phases: list[LifecyclePhase] = []
    t = 0.0

    # Still unsettled at the start
    if hours_to_clear > 0.0:
        phases.append(
            LifecyclePhase("post_frontal", t, hours_to_clear, ATTR_CONDITION_CLOUDY, 0.65)
        )
        t = hours_to_clear

    # Clearing
    clearing_end = t + rebound_hours
    phases.append(
        LifecyclePhase("clearing", t, clearing_end, ATTR_CONDITION_PARTLYCLOUDY, 0.55)
    )
    t = clearing_end

    # Stabilizing — fill to total_hours
    if t < total_hours:
        phases.append(
            LifecyclePhase("stabilizing", t, total_hours, ATTR_CONDITION_SUNNY, 0.45)
        )

    return phases
```

Update `model_system_evolution()` signature and return value. Change the method signature from:

```python
def model_system_evolution(
    self, meteorological_state: Dict[str, Any]
) -> EvolutionModel:
```

to:

```python
def model_system_evolution(
    self,
    meteorological_state: Dict[str, Any],
    current_condition: str = ATTR_CONDITION_CLOUDY,
) -> EvolutionModel:
```

At the end of `model_system_evolution()`, change the return from:

```python
return {
    "evolution_path": evolution_path,
    "confidence_levels": confidence_levels,
    "transition_probabilities": transition_probabilities,
}
```

to:

```python
acceleration = meteorological_state.get("pressure_acceleration", 0.0)
if not isinstance(acceleration, (int, float)):
    acceleration = 0.0

lifecycle = self.compute_lifecycle(
    trend=current_trend,
    acceleration=acceleration,
    storm_prob=storm_probability,
    current_condition=current_condition,
)

return {
    "evolution_path": evolution_path,
    "confidence_levels": confidence_levels,
    "transition_probabilities": transition_probabilities,
    "lifecycle": lifecycle,
}
```

- [ ] **Step 4: Update `forecast/__init__.py`** to export the new public names:

```python
from .evolution import (
    EvolutionModeler,
    LifecyclePhase,
    apply_confidence_clamping,
    find_lifecycle_phase,
)
```

And add to `__all__`:

```python
__all__ = [
    "DailyForecastGenerator",
    "EvolutionModeler",
    "HourlyForecastGenerator",
    "LifecyclePhase",
    "MeteorologicalAnalyzer",
    "apply_confidence_clamping",
    "find_lifecycle_phase",
]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_forecast_evolution.py::TestLifecyclePhase tests/test_forecast_evolution.py::TestFindLifecyclePhase tests/test_forecast_evolution.py::TestApplyConfidenceClamping tests/test_forecast_evolution.py::TestComputeLifecycle -v
```

Expected: all PASSED

- [ ] **Step 6: Run full evolution test suite**

```bash
python -m pytest tests/test_forecast_evolution.py -v
```

Expected: all PASSED (existing tests must still pass)

- [ ] **Step 7: Commit**

```bash
git add custom_components/micro_weather/forecast/evolution.py custom_components/micro_weather/forecast/__init__.py tests/test_forecast_evolution.py
git commit -m "feat: add LifecyclePhase, compute_lifecycle(), and confidence clamping helpers"
```

---

## Task 4: Lifecycle-based `DailyForecastGenerator.forecast_condition()`

**Files:**
- Modify: `custom_components/micro_weather/forecast/daily.py`
- Test: `tests/test_forecast_daily.py`

### What changes

`forecast_condition()` replaces its body to:
1. Get `lifecycle` from `system_evolution`
2. Find the phase for `(day_idx + 0.5) * 24` hours
3. Compute per-slot confidence via `phase.confidence * exp(-slot_hour / 72)`
4. Apply `apply_confidence_clamping()`
5. Retain the existing `_apply_storm_probability_overrides()` as final step

`_calculate_condition_trajectory()` and `_evolve_condition_by_trajectory()` are deleted.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_forecast_daily.py` (check the existing class structure and add inside `TestDailyForecastGenerator` or as a new class):

```python
import math
from custom_components.micro_weather.forecast.evolution import LifecyclePhase
from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
)


class TestDailyForecastConditionLifecycle:
    """Tests for lifecycle-based DailyForecastGenerator.forecast_condition()."""

    @pytest.fixture
    def generator(self):
        from custom_components.micro_weather.analysis.trends import TrendsAnalyzer
        from custom_components.micro_weather.forecast.daily import DailyForecastGenerator
        return DailyForecastGenerator(TrendsAnalyzer({}))

    def _make_evolution(self, lifecycle):
        return {
            "lifecycle": lifecycle,
            "evolution_path": [],
            "confidence_levels": [],
            "transition_probabilities": {},
        }

    def _make_met_state(self, storm_prob=0, pressure_system="normal", trend=0.0):
        return {
            "pressure_analysis": {
                "storm_probability": storm_prob,
                "pressure_system": pressure_system,
                "current_trend": trend,
                "long_term_trend": trend,
            },
            "atmospheric_stability": 0.7,
        }

    def test_day0_uses_stable_phase_condition(self, generator):
        """Day 0 slot (hour 12) returns the stable phase condition."""
        lifecycle = [
            LifecyclePhase("stable", 0.0, 120.0, ATTR_CONDITION_SUNNY, 0.85)
        ]
        result = generator.forecast_condition(
            0, ATTR_CONDITION_SUNNY,
            self._make_met_state(),
            {},
            self._make_evolution(lifecycle),
        )
        assert result == ATTR_CONDITION_SUNNY

    def test_deteriorating_arc_day_by_day(self, generator):
        """Falling pressure → day 0 cloudy, day 1 rainy, day 2 post-frontal cloudy."""
        # Front arrives at hour 18, peak 6h, post_frontal 6h, clearing 6h
        lifecycle = [
            LifecyclePhase("pre_frontal", 0.0, 18.0, ATTR_CONDITION_CLOUDY, 0.80),
            LifecyclePhase("frontal", 18.0, 24.0, ATTR_CONDITION_RAINY, 0.75),
            LifecyclePhase("post_frontal", 24.0, 48.0, ATTR_CONDITION_CLOUDY, 0.65),
            LifecyclePhase("clearing", 48.0, 72.0, ATTR_CONDITION_PARTLYCLOUDY, 0.55),
            LifecyclePhase("stabilizing", 72.0, 120.0, ATTR_CONDITION_SUNNY, 0.45),
        ]
        met_state = self._make_met_state(storm_prob=5)
        evolution = self._make_evolution(lifecycle)

        # Day 0 midpoint = hour 12 → pre_frontal → cloudy
        day0 = generator.forecast_condition(0, ATTR_CONDITION_PARTLYCLOUDY, met_state, {}, evolution)
        assert day0 == ATTR_CONDITION_CLOUDY

        # Day 1 midpoint = hour 36 → post_frontal → cloudy
        day1 = generator.forecast_condition(1, ATTR_CONDITION_PARTLYCLOUDY, met_state, {}, evolution)
        assert day1 == ATTR_CONDITION_CLOUDY

        # Day 2 midpoint = hour 60 → clearing → partlycloudy (but confidence check)
        day2 = generator.forecast_condition(2, ATTR_CONDITION_PARTLYCLOUDY, met_state, {}, evolution)
        # confidence at hour 60: 0.55 * exp(-60/72) ≈ 0.55 * 0.435 ≈ 0.24 → clamped to partlycloudy
        assert day2 in (ATTR_CONDITION_PARTLYCLOUDY, ATTR_CONDITION_CLOUDY)

    def test_empty_lifecycle_falls_back_to_current_condition(self, generator):
        """Empty lifecycle returns current_condition (graceful fallback)."""
        result = generator.forecast_condition(
            0, ATTR_CONDITION_CLOUDY,
            self._make_met_state(),
            {},
            {"lifecycle": [], "evolution_path": [], "confidence_levels": [], "transition_probabilities": {}},
        )
        assert result == ATTR_CONDITION_CLOUDY

    def test_low_confidence_slots_clamped(self, generator):
        """Day 4 (hour 108) gets heavy confidence decay → clamped to partlycloudy."""
        lifecycle = [
            LifecyclePhase("stabilizing", 0.0, 120.0, ATTR_CONDITION_SUNNY, 0.45)
        ]
        result = generator.forecast_condition(
            4, ATTR_CONDITION_SUNNY,
            self._make_met_state(),
            {},
            self._make_evolution(lifecycle),
        )
        # confidence = 0.45 * exp(-108/72) ≈ 0.45 * 0.22 ≈ 0.10 → clamped
        assert result in (ATTR_CONDITION_PARTLYCLOUDY, ATTR_CONDITION_CLOUDY)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_forecast_daily.py::TestDailyForecastConditionLifecycle -v
```

Expected: FAILs — current `forecast_condition` ignores `lifecycle` key

- [ ] **Step 3: Update `daily.py`**

Add at the top of `daily.py` (after existing imports):

```python
import math

from .evolution import apply_confidence_clamping, find_lifecycle_phase
```

Replace the body of `forecast_condition()` (lines ~307–349) with:

```python
def forecast_condition(
    self,
    day_idx: int,
    current_condition: str,
    meteorological_state: Dict[str, Any],
    historical_patterns: Dict[str, Any],
    system_evolution: Dict[str, Any],
) -> str:
    """Forecast condition using weather system lifecycle phases.

    Maps the day's midpoint hour to a lifecycle phase and derives the
    condition from that phase, then applies confidence-based clamping
    so that distant uncertain days show safe middle-ground conditions.

    Args:
        day_idx: Day index (0–4)
        current_condition: Current weather condition (used as fallback)
        meteorological_state: Meteorological state analysis
        historical_patterns: Historical weather patterns (unused — kept for API compat)
        system_evolution: Must contain a "lifecycle" key from EvolutionModeler

    Returns:
        str: Forecasted weather condition
    """
    lifecycle = system_evolution.get("lifecycle", [])
    slot_hour = (day_idx + 0.5) * 24.0  # midpoint of the day

    phase = find_lifecycle_phase(lifecycle, slot_hour)
    if phase is None:
        # Graceful fallback: lifecycle not yet computed
        return self._apply_storm_probability_overrides(
            current_condition, day_idx, meteorological_state
        )

    confidence = phase.confidence * math.exp(-slot_hour / 72.0)
    condition = apply_confidence_clamping(phase.condition, confidence)
    return self._apply_storm_probability_overrides(condition, day_idx, meteorological_state)
```

Delete the methods `_calculate_condition_trajectory()` and `_evolve_condition_by_trajectory()` entirely — they are no longer called.

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_forecast_daily.py::TestDailyForecastConditionLifecycle -v
```

Expected: all PASSED

- [ ] **Step 5: Run full daily test suite**

```bash
python -m pytest tests/test_forecast_daily.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add custom_components/micro_weather/forecast/daily.py tests/test_forecast_daily.py
git commit -m "feat: replace daily forecast_condition with lifecycle phase lookup"
```

---

## Task 5: Lifecycle-based `HourlyForecastGenerator.forecast_condition()`

**Files:**
- Modify: `custom_components/micro_weather/forecast/hourly.py`
- Test: `tests/test_forecast_hourly.py`

### What changes

`forecast_condition()` replaces its body to use `find_lifecycle_phase` + `apply_confidence_clamping`.
The `lifecycle` is read from `micro_evolution.get("lifecycle", [])` (the lifecycle will be passed as `micro_evolution` from `weather.py` in Task 6).
`_calculate_hourly_trajectory()` and `_evolve_hourly_condition()` are deleted.
`_apply_day_night_conversion()` is retained and called last.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_forecast_hourly.py`:

```python
class TestHourlyForecastConditionLifecycle:
    """Tests for lifecycle-based HourlyForecastGenerator.forecast_condition()."""

    @pytest.fixture
    def generator(self):
        from unittest.mock import MagicMock
        from custom_components.micro_weather.forecast.hourly import HourlyForecastGenerator
        return HourlyForecastGenerator(
            atmospheric_analyzer=MagicMock(),
            solar_analyzer=MagicMock(),
            trends_analyzer=MagicMock(),
        )

    def _make_astro(self, is_daytime=True, hour=12):
        return {"is_daytime": is_daytime, "hour_of_day": hour, "solar_elevation": 45.0}

    def _make_met_state(self, trend=0.0, storm_prob=0):
        return {
            "pressure_analysis": {
                "current_trend": trend,
                "storm_probability": storm_prob,
                "pressure_system": "normal",
            },
            "cloud_analysis": {"cloud_cover": 50},
            "atmospheric_stability": 0.7,
        }

    def _make_micro_evolution(self, lifecycle):
        return {"lifecycle": lifecycle}

    def test_hour0_returns_stable_phase_condition(self, generator):
        from custom_components.micro_weather.forecast.evolution import LifecyclePhase
        from homeassistant.components.weather import ATTR_CONDITION_SUNNY
        lifecycle = [LifecyclePhase("stable", 0.0, 120.0, ATTR_CONDITION_SUNNY, 0.85)]
        result = generator.forecast_condition(
            0, ATTR_CONDITION_SUNNY,
            self._make_astro(is_daytime=True),
            self._make_met_state(),
            {},
            self._make_micro_evolution(lifecycle),
        )
        assert result == ATTR_CONDITION_SUNNY

    def test_hourly_lifecycle_maps_to_correct_phase(self, generator):
        """Hour 20 maps to the frontal phase when front arrives at hour 18."""
        from custom_components.micro_weather.forecast.evolution import LifecyclePhase
        from homeassistant.components.weather import (
            ATTR_CONDITION_CLOUDY,
            ATTR_CONDITION_RAINY,
        )
        lifecycle = [
            LifecyclePhase("pre_frontal", 0.0, 18.0, ATTR_CONDITION_CLOUDY, 0.80),
            LifecyclePhase("frontal", 18.0, 24.0, ATTR_CONDITION_RAINY, 0.75),
        ]
        result = generator.forecast_condition(
            20, ATTR_CONDITION_CLOUDY,
            self._make_astro(is_daytime=False, hour=20),
            self._make_met_state(),
            {},
            self._make_micro_evolution(lifecycle),
        )
        # Frontal at hour 20, is_daytime=False → but rainy stays rainy at night
        assert result == ATTR_CONDITION_RAINY

    def test_empty_lifecycle_fallback(self, generator):
        """Empty lifecycle falls back gracefully to current condition."""
        from homeassistant.components.weather import ATTR_CONDITION_CLOUDY
        result = generator.forecast_condition(
            5, ATTR_CONDITION_CLOUDY,
            self._make_astro(),
            self._make_met_state(),
            {},
            {"lifecycle": []},
        )
        assert isinstance(result, str)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_forecast_hourly.py::TestHourlyForecastConditionLifecycle -v
```

Expected: FAILs

- [ ] **Step 3: Update `hourly.py`**

Add to the top-level imports in `hourly.py`:

```python
import math

from .evolution import apply_confidence_clamping, find_lifecycle_phase
```

Replace the body of `forecast_condition()` (currently lines ~366–416) with:

```python
def forecast_condition(
    self,
    hour_idx: int,
    current_condition: str,
    astronomical_context: Dict[str, Any],
    meteorological_state: Dict[str, Any],
    hourly_patterns: Dict[str, Any],
    micro_evolution: Dict[str, Any],
) -> str:
    """Forecast condition using weather system lifecycle phases.

    Maps hour_idx to a lifecycle phase (from micro_evolution["lifecycle"]),
    applies confidence decay and clamping, then converts for day/night.

    Args:
        hour_idx: Hour index 0–23
        current_condition: Previous hour's condition (fallback only)
        astronomical_context: Dict with 'is_daytime' and 'hour_of_day'
        meteorological_state: Meteorological state (for day/night conversion)
        hourly_patterns: Unused — kept for API compatibility
        micro_evolution: Must contain a "lifecycle" key from EvolutionModeler

    Returns:
        str: Forecasted condition
    """
    if current_condition is None:
        current_condition = ATTR_CONDITION_CLOUDY

    lifecycle = micro_evolution.get("lifecycle", [])
    phase = find_lifecycle_phase(lifecycle, float(hour_idx))

    if phase is None:
        # Graceful fallback when lifecycle is empty
        forecast_condition = current_condition
    else:
        confidence = phase.confidence * math.exp(-float(hour_idx) / 72.0)
        forecast_condition = apply_confidence_clamping(phase.condition, confidence)

    return self._apply_day_night_conversion(
        forecast_condition,
        astronomical_context["is_daytime"],
        meteorological_state,
    )
```

Delete `_calculate_hourly_trajectory()` and `_evolve_hourly_condition()` — they are no longer called.

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_forecast_hourly.py::TestHourlyForecastConditionLifecycle -v
```

Expected: all PASSED

- [ ] **Step 5: Run full hourly test suite**

```bash
python -m pytest tests/test_forecast_hourly.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add custom_components/micro_weather/forecast/hourly.py tests/test_forecast_hourly.py
git commit -m "feat: replace hourly forecast_condition with lifecycle phase lookup"
```

---

## Task 6: Wire `EvolutionModeler` in `weather_detector.py` and `weather.py`

**Files:**
- Modify: `custom_components/micro_weather/weather_detector.py`
- Modify: `custom_components/micro_weather/weather.py`

### What changes

Both files currently pass `{}` as `system_evolution`. They now:
1. Instantiate `EvolutionModeler`
2. Before each forecast call, compute `meteorological_state`, then add `pressure_acceleration` to it
3. Call `evolution_modeler.model_system_evolution(meteorological_state, current_condition)` to get `system_evolution`
4. Pass `system_evolution` as `system_evolution` to daily generator and as `micro_evolution` to hourly generator

- [ ] **Step 1: Update `weather_detector.py`**

In `weather_detector.py`, add `EvolutionModeler` to the existing forecast import (line ~74):

```python
from .forecast import DailyForecastGenerator, EvolutionModeler, MeteorologicalAnalyzer
```

In `WeatherDetector.__init__()`, after `self.daily_generator = DailyForecastGenerator(...)` (line ~164):

```python
self.evolution_modeler = EvolutionModeler()
```

In `get_weather_data()`, find the block that builds `forecast_data` (around line ~245). Replace:

```python
forecast_data = self.daily_generator.generate_forecast(
    condition,
    self._prepare_forecast_sensor_data(sensor_data),
    altitude,
    self.meteorological_analyzer.analyze_state(
        self._prepare_analysis_sensor_data(sensor_data), altitude
    ),
    historical_patterns,
    {},  # system_evolution - empty for now
)
```

with:

```python
_analysis_data = self._prepare_analysis_sensor_data(sensor_data)
meteorological_state = self.meteorological_analyzer.analyze_state(
    _analysis_data, altitude
)
meteorological_state["pressure_acceleration"] = (
    self.trends_analyzer.compute_pressure_acceleration()
)
system_evolution = self.evolution_modeler.model_system_evolution(
    meteorological_state, current_condition=condition
)
forecast_data = self.daily_generator.generate_forecast(
    condition,
    self._prepare_forecast_sensor_data(sensor_data),
    altitude,
    meteorological_state,
    historical_patterns,
    system_evolution,
)
```

- [ ] **Step 2: Update `weather.py`**

`EvolutionModeler` is already in the import at line 42–46. No import change needed.

In `MicroWeatherEntity.__init__()`, in both branches (the `if hasattr(coordinator, "atmospheric_analyzer")` branch, line ~94, and the `else` fallback branch, line ~108), add after creating `_daily_generator`:

```python
self._evolution_modeler = EvolutionModeler()
```

In `async_forecast_daily()` (around line ~360), replace:

```python
forecast_data = self._daily_generator.generate_forecast(
    current_condition,
    sensor_data,
    altitude,
    self._meteorological_analyzer.analyze_state(sensor_data, altitude),
    historical_patterns,
    {},  # system_evolution - empty for now
    sunrise_time=sunrise_time,
    sunset_time=sunset_time,
)
```

with:

```python
_met_state = self._meteorological_analyzer.analyze_state(sensor_data, altitude)
_met_state["pressure_acceleration"] = (
    self.coordinator.trends_analyzer.compute_pressure_acceleration()
    if hasattr(self.coordinator, "trends_analyzer")
    else 0.0
)
_system_evolution = self._evolution_modeler.model_system_evolution(
    _met_state, current_condition=current_condition
)
forecast_data = self._daily_generator.generate_forecast(
    current_condition,
    sensor_data,
    altitude,
    _met_state,
    historical_patterns,
    _system_evolution,
    sunrise_time=sunrise_time,
    sunset_time=sunset_time,
)
```

In `async_forecast_hourly()` (around line ~467), replace:

```python
forecast_data = self._hourly_generator.generate_forecast(
    current_temp=float(convert_to_fahrenheit(current_temp) or 68.0),
    current_condition=current_condition,
    sensor_data=sensor_data,
    sunrise_time=sunrise_time,
    sunset_time=sunset_time,
    altitude=altitude,
    meteorological_state=self._meteorological_analyzer.analyze_state(
        sensor_data, altitude
    ),
    hourly_patterns={},  # hourly_patterns - empty for now
    micro_evolution={},  # micro_evolution - empty for now
)
```

with:

```python
_met_state_hourly = self._meteorological_analyzer.analyze_state(sensor_data, altitude)
_met_state_hourly["pressure_acceleration"] = (
    self.coordinator.trends_analyzer.compute_pressure_acceleration()
    if hasattr(self.coordinator, "trends_analyzer")
    else 0.0
)
_system_evolution_hourly = self._evolution_modeler.model_system_evolution(
    _met_state_hourly, current_condition=current_condition
)
forecast_data = self._hourly_generator.generate_forecast(
    current_temp=float(convert_to_fahrenheit(current_temp) or 68.0),
    current_condition=current_condition,
    sensor_data=sensor_data,
    sunrise_time=sunrise_time,
    sunset_time=sunset_time,
    altitude=altitude,
    meteorological_state=_met_state_hourly,
    hourly_patterns={},
    micro_evolution=_system_evolution_hourly,
)
```

- [ ] **Step 3: Run the CI test suite to confirm nothing broke**

```bash
python -m pytest tests/test_weather_detector.py tests/test_validation.py -v
```

Expected: all PASSED

- [ ] **Step 4: Commit**

```bash
git add custom_components/micro_weather/weather_detector.py custom_components/micro_weather/weather.py
git commit -m "feat: wire EvolutionModeler into weather_detector and weather entity"
```

---

## Task 7: End-to-end arc tests

**Files:**
- Test: `tests/test_weather_detector.py`

These tests verify the complete pipeline: sensor data → lifecycle → forecast condition arc.

- [ ] **Step 1: Add the tests**

Add to `tests/test_weather_detector.py` inside `TestWeatherDetector`:

```python
def _build_detector_with_pressure_history(
    self, mock_hass, mock_options, pressure_entries
):
    """Helper: build a WeatherDetector with pre-loaded pressure history."""
    from datetime import datetime, timedelta
    detector = WeatherDetector(mock_hass, mock_options)
    base_time = datetime.now()
    for i, value in enumerate(pressure_entries):
        detector._sensor_history["pressure"].append(
            {"timestamp": base_time - timedelta(hours=len(pressure_entries) - 1 - i), "value": value}
        )
    return detector

def test_forecast_deteriorating_arc(self, mock_hass, mock_options):
    """Falling pressure → day 0 cloudy/partlycloudy, days 2-3 not sunny."""
    import numpy as np
    # 24 readings falling from 30.1 to 29.3 inHg (fast front)
    pressures = [30.1 - i * (0.8 / 23) for i in range(24)]
    detector = self._build_detector_with_pressure_history(mock_hass, mock_options, pressures)

    from custom_components.micro_weather.analysis.trends import TrendsAnalyzer
    from custom_components.micro_weather.forecast.evolution import EvolutionModeler
    from custom_components.micro_weather.forecast.daily import DailyForecastGenerator
    from custom_components.micro_weather.forecast.meteorological import MeteorologicalAnalyzer

    trends = TrendsAnalyzer(detector._sensor_history)
    modeler = EvolutionModeler()
    met_state = {"pressure_analysis": {"current_trend": -0.5, "long_term_trend": -0.4, "storm_probability": 15}, "atmospheric_stability": 0.5, "pressure_acceleration": trends.compute_pressure_acceleration()}
    system_evolution = modeler.model_system_evolution(met_state, current_condition="partlycloudy")

    generator = DailyForecastGenerator(trends)
    forecast = []
    for day_idx in range(5):
        forecast.append(generator.forecast_condition(
            day_idx, "partlycloudy", met_state, {}, system_evolution
        ))

    # Day 0 and 1 should not be sunny (front incoming)
    assert forecast[0] not in ("sunny",), f"Day 0 was sunny with falling pressure: {forecast}"
    assert forecast[1] not in ("sunny",), f"Day 1 was sunny with falling pressure: {forecast}"

def test_forecast_improving_arc(self, mock_hass, mock_options):
    """Rising pressure → days 2-4 progressively clearer."""
    pressures = [29.3 + i * (0.8 / 23) for i in range(24)]
    detector = self._build_detector_with_pressure_history(mock_hass, mock_options, pressures)

    from custom_components.micro_weather.forecast.evolution import EvolutionModeler
    from custom_components.micro_weather.forecast.daily import DailyForecastGenerator
    from custom_components.micro_weather.analysis.trends import TrendsAnalyzer

    trends = TrendsAnalyzer(detector._sensor_history)
    modeler = EvolutionModeler()
    met_state = {"pressure_analysis": {"current_trend": 0.5, "long_term_trend": 0.4, "storm_probability": 30}, "atmospheric_stability": 0.6, "pressure_acceleration": trends.compute_pressure_acceleration()}
    system_evolution = modeler.model_system_evolution(met_state, current_condition="cloudy")
    generator = DailyForecastGenerator(trends)

    forecast = []
    for day_idx in range(5):
        forecast.append(generator.forecast_condition(
            day_idx, "cloudy", met_state, {}, system_evolution
        ))

    # Day 0 should be cloudy or partlycloudy (still recovering)
    assert forecast[0] in ("cloudy", "partlycloudy"), f"Day 0 unexpected: {forecast[0]}"

def test_forecast_stable_arc(self, mock_hass, mock_options):
    """Flat pressure → all days return a condition (no crash)."""
    pressures = [29.92] * 24
    detector = self._build_detector_with_pressure_history(mock_hass, mock_options, pressures)

    from custom_components.micro_weather.forecast.evolution import EvolutionModeler
    from custom_components.micro_weather.forecast.daily import DailyForecastGenerator
    from custom_components.micro_weather.analysis.trends import TrendsAnalyzer

    trends = TrendsAnalyzer(detector._sensor_history)
    modeler = EvolutionModeler()
    met_state = {"pressure_analysis": {"current_trend": 0.0, "long_term_trend": 0.0, "storm_probability": 0}, "atmospheric_stability": 0.8, "pressure_acceleration": 0.0}
    system_evolution = modeler.model_system_evolution(met_state, current_condition="sunny")
    generator = DailyForecastGenerator(trends)

    forecast = [
        generator.forecast_condition(day_idx, "sunny", met_state, {}, system_evolution)
        for day_idx in range(5)
    ]
    assert all(isinstance(c, str) and len(c) > 0 for c in forecast)
    # Stable pressure with sunny current condition → day 0 is sunny
    assert forecast[0] == "sunny"
```

- [ ] **Step 2: Run the new tests**

```bash
python -m pytest tests/test_weather_detector.py::TestWeatherDetector::test_forecast_deteriorating_arc tests/test_weather_detector.py::TestWeatherDetector::test_forecast_improving_arc tests/test_weather_detector.py::TestWeatherDetector::test_forecast_stable_arc -v
```

Expected: all PASSED

- [ ] **Step 3: Run the full CI test suite**

```bash
python -m pytest tests/test_weather_detector.py tests/test_validation.py -v
```

Expected: all PASSED

- [ ] **Step 4: Run the full test suite**

```bash
python -m pytest tests/ -v
```

Expected: all PASSED

- [ ] **Step 5: Run lint and type checks**

```bash
black --check --diff custom_components/
isort --check-only --diff custom_components/
flake8 custom_components/ --max-complexity=10 --max-line-length=88
mypy custom_components/ --ignore-missing-imports
```

Fix any issues, then re-run until clean.

- [ ] **Step 6: Commit**

```bash
git add tests/test_weather_detector.py
git commit -m "test: add end-to-end arc tests for lifecycle-based forecast"
```

---

## Task 8: Update `WEATHER_FORECAST_ALGORITHM.md`

**Files:**
- Modify: `WEATHER_FORECAST_ALGORITHM.md`

- [ ] **Step 1: Rewrite the condition-forecasting sections**

Replace the "Condition Forecasting" subsection under "Meteorological Analysis Module" (currently starting around line 88) with:

```markdown
#### Condition Forecasting

**Algorithm:** `EvolutionModeler.compute_lifecycle()` + phase lookup in both generators

Condition prediction now follows a weather system lifecycle model rather than
evolving step-by-step from the current condition snapshot.

**1. Pressure acceleration**

`TrendsAnalyzer.compute_pressure_acceleration()` splits the last 24h of pressure
readings into two equal halves, fits a linear trend to each, and returns the
slope difference (slope₂ − slope₁). A negative value means the fall is speeding
up (fast-moving front); positive means it is decelerating (stalling front).

**2. Lifecycle computation**

`EvolutionModeler.compute_lifecycle(trend, acceleration, storm_prob, current_condition)`
returns an ordered `List[LifecyclePhase]` covering 120 hours (5 days):

| Scenario | Phase sequence |
|---|---|
| Falling pressure | stable → pre_frontal → frontal → post_frontal → clearing → stabilizing |
| Rising pressure | post_frontal → clearing → stabilizing |
| Stable (|trend| < 0.2 inHg/3h) | single stable phase, condition = current |

Timing is derived from existing thresholds:
- `hours_to_frontal = (STORM_THRESHOLD_SEVERE − storm_prob) / (|trend| × 5)`
- `peak_duration = 6h` if |acceleration| > 0.1 else `12h`
- `rebound_hours = peak_duration × (1 + |acceleration|)`

**3. Per-slot lookup and confidence clamping**

For each forecast slot (daily: midpoint of the day; hourly: hour index), the
corresponding `LifecyclePhase` is found via `find_lifecycle_phase()`. Per-slot
confidence is:

```
confidence = phase.base_confidence × exp(−slot_hours / 72)
```

Conditions are then clamped by `apply_confidence_clamping()`:

| Confidence | Allowed conditions |
|---|---|
| ≥ 0.6 | any |
| 0.4 – 0.59 | no extremes (pouring/lightning-rainy → rainy) |
| < 0.4 | cloudy or partlycloudy only |

Storm probability overrides (high storm_prob → lightning-rainy/pouring) are applied
last as a safety net.
```

Replace the "Trajectory-Based Evolution (Version 4.0.0)" section in the hourly forecast documentation with:

```markdown
**Lifecycle-Based Condition Evolution:**

The hourly forecast derives conditions from the same `LifecyclePhase` list as
the daily forecast. `hour_idx` is used directly as `slot_hour` for the phase
lookup. Confidence decay uses the same 72-hour half-life formula. The
day/night conversion (`_apply_day_night_conversion`) is applied after clamping.
```

- [ ] **Step 2: Commit**

```bash
git add WEATHER_FORECAST_ALGORITHM.md
git commit -m "docs: update forecast algorithm documentation for lifecycle model"
```

---

## Task 9: Create PR

- [ ] **Step 1: Push branch**

```bash
git push -u origin feature/trend-based-lifecycle-forecast
```

- [ ] **Step 2: Create PR**

```bash
gh pr create \
  --title "feat: trend-based weather system lifecycle forecast" \
  --body "$(cat <<'EOF'
## Summary

- Replaces snapshot-propagation forecast (all days = current condition ± 1-2 steps) with a **weather system lifecycle engine**
- `TrendsAnalyzer` gains `compute_pressure_acceleration()` to detect fast vs slow fronts
- `EvolutionModeler` gains `compute_lifecycle()` which infers front arrival timing from the pressure trend rate, maps the 5-day window to named phases (pre_frontal → frontal → post_frontal → clearing → stabilizing), and returns a `List[LifecyclePhase]`
- `DailyForecastGenerator.forecast_condition()` and `HourlyForecastGenerator.forecast_condition()` both replaced with lifecycle phase lookup + confidence-based clamping (uncertain day 4-5 clamped to partlycloudy/cloudy)
- `EvolutionModeler` now actually wired up in `weather_detector.py` and `weather.py` (was previously always `{}`)

## Test plan

- [ ] `python -m pytest tests/ -v` — full suite passes
- [ ] `python -m pytest tests/test_weather_detector.py tests/test_validation.py -v` — CI suite passes
- [ ] Verify deteriorating arc: falling pressure → day 0 cloudy, day 1-2 rainy/cloudy, day 3-4 partlycloudy
- [ ] Verify improving arc: rising pressure → cloudy → partlycloudy → sunny over 5 days
- [ ] Verify stable: flat pressure → current condition holds with no crash
- [ ] `black --check custom_components/ && isort --check-only custom_components/ && flake8 custom_components/` — lint clean

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review Checklist

- **Spec coverage:** All 8 spec requirements covered:
  - ✅ `compute_pressure_acceleration()` — Task 2
  - ✅ `LifecyclePhase` dataclass — Task 3
  - ✅ `compute_lifecycle()` — Task 3
  - ✅ `find_lifecycle_phase()` + `apply_confidence_clamping()` — Task 3
  - ✅ `model_system_evolution()` updated + wired — Tasks 3 & 6
  - ✅ `DailyForecastGenerator.forecast_condition()` replaced — Task 4
  - ✅ `HourlyForecastGenerator.forecast_condition()` replaced — Task 5
  - ✅ `WEATHER_FORECAST_ALGORITHM.md` updated — Task 8
  - ✅ Branch + PR — Tasks 1 & 9
  - ✅ All 11 test cases from spec — distributed across Tasks 2–7
- **Placeholder scan:** No TBDs or TODOs in any step
- **Type consistency:** `LifecyclePhase` defined once in Task 3, imported by name in Tasks 4 and 5. `find_lifecycle_phase` and `apply_confidence_clamping` named consistently throughout.
