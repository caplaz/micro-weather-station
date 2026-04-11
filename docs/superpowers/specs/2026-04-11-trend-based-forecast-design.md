# Trend-Based Forecast: Weather System Lifecycle Engine

**Date:** 2026-04-11
**Status:** Approved
**Scope:** `forecast/evolution.py`, `forecast/daily.py`, `forecast/hourly.py`, `analysis/trends.py`, `weather_detector.py`, `weather.py`, `WEATHER_FORECAST_ALGORITHM.md`, tests

---

## Problem

The current forecast propagates the current weather condition forward with small trajectory-based adjustments. Every forecast day is scored independently against *today's* pressure/humidity trend, then evolved ±1–2 steps on a condition ladder from `current_condition`. This produces "sticky" forecasts: sunny today → sunny all week; cloudy today → cloudy all week.

The root cause is twofold:
1. `EvolutionModeler` exists but is never called — `system_evolution` is hardcoded to `{}` in both `weather_detector.py` and `weather.py`.
2. The trajectory score uses the same snapshot trend for all days, with only a distance dampening factor. There is no modeling of *when* a system arrives, how long it lasts, or how conditions recover afterward.

---

## Goal

Replace the snapshot-propagation approach with a **weather system lifecycle engine** that:
- Infers the timing of incoming (or outgoing) weather system phases from the pressure trend and its acceleration
- Assigns each forecast slot (day or hour) to a named lifecycle phase
- Derives conditions from the phase rather than stepping from the current condition
- Applies confidence-based clamping so distant uncertain days show safe middle-ground conditions

---

## Architecture

### Data flow (new)

```
TrendsAnalyzer.compute_pressure_acceleration()
    ↓
EvolutionModeler.compute_lifecycle(trend, accel, storm_prob, current_condition)
    → List[LifecyclePhase(start_h, end_h, name, condition, base_confidence)]
    ↓
weather_detector.py / weather.py
    → pass lifecycle to DailyForecastGenerator and HourlyForecastGenerator
    ↓
DailyForecastGenerator.forecast_condition(day_idx)
    → maps (day_idx * 24) → phase → condition + confidence clamping
HourlyForecastGenerator._forecast_hourly_condition(hour_idx)
    → maps hour_idx → phase → condition + confidence clamping
```

---

## Components

### 1. `TrendsAnalyzer.compute_pressure_acceleration()` (new method)

Splits the last 24h of pressure readings in `_sensor_history["pressure"]` into two equal halves, computes the linear trend slope for each half using the existing `calculate_trend()` method, and returns:

```
acceleration = slope_second_half - slope_first_half  (inHg/3h²)
```

- Positive acceleration: pressure fall is slowing (front decelerating or stalling)
- Negative acceleration: pressure fall is speeding up (fast-moving front)
- Returns `0.0` if fewer than 4 readings are available

### 2. `LifecyclePhase` dataclass (new, in `evolution.py`)

```python
@dataclass
class LifecyclePhase:
    name: str           # see phase names below
    start_hour: float   # hours from now (0.0 = present)
    end_hour: float     # hours from now
    condition: str      # HA weather condition string
    confidence: float   # base confidence for this phase (0.0–1.0)
```

**Phase names:** `stable`, `pre_frontal`, `frontal`, `post_frontal`, `clearing`, `stabilizing`

### 3. `EvolutionModeler.compute_lifecycle()` (new method)

Accepts `(trend, acceleration, storm_prob, current_condition)` and returns a `List[LifecyclePhase]` covering at least 120 hours.

**Uses only existing constants** — no new entries in `meteorological_constants.py`. Specifically:
- Storm probability thresholds from `AtmosphericAnalyzer` (already used for storm detection)
- Trend cut-offs (`< -0.2`, `> +0.2` inHg/3h) already present in `EvolutionConstants`

**Deteriorating scenario (falling pressure):**

```
hours_to_frontal = pressure_gap_to_storm_threshold / abs(trend_rate)
peak_duration    = 6h if |acceleration| > 0.1 else 12h  (fast vs slow front)
rebound_hours    = peak_duration * (1 + abs(acceleration))

Phases:
  stable        0h → (hours_to_frontal - 6h)     condition = current_condition
  pre_frontal   → hours_to_frontal                condition = partlycloudy/cloudy
  frontal       → + peak_duration                 condition = rainy/pouring/lightning-rainy
  post_frontal  → + rebound_hours                 condition = cloudy
  clearing      → + rebound_hours                 condition = partlycloudy
  stabilizing   → 120h                            condition = sunny
```

**Improving scenario (rising pressure):**

```
hours_to_clear = pressure_gap_to_high_threshold / trend_rate

Phases:
  post_frontal  0h → hours_to_clear               condition = cloudy
  clearing      → + 12h                           condition = partlycloudy
  stabilizing   → 120h                            condition = sunny
```

**Stable scenario (|trend| < 0.2 inHg/3h):**

```
Phases:
  stable        0h → 120h                         condition = current_condition
```

The `model_system_evolution()` method is updated to call `compute_lifecycle()` internally and include the `lifecycle` list in its return dict (backwards-compatible addition).

### 4. Wiring in `weather_detector.py` and `weather.py`

Replace the two `{}` placeholders with a real call to `EvolutionModeler.model_system_evolution(meteorological_state)`. The returned dict (including the `lifecycle` key) is passed as `system_evolution` to both generators.

### 5. `DailyForecastGenerator.forecast_condition()` (replacement)

Replaces `_calculate_condition_trajectory()` + `_evolve_condition_by_trajectory()` with:

```python
def forecast_condition(self, day_idx, current_condition, meteorological_state,
                       historical_patterns, system_evolution):
    lifecycle = system_evolution.get("lifecycle", [])
    slot_hour = (day_idx + 0.5) * 24  # midpoint of the day
    phase = _find_phase(lifecycle, slot_hour)
    if phase is None:
        return current_condition  # graceful fallback
    condition = phase.condition
    confidence = phase.confidence * math.exp(-slot_hour / 72)
    return _apply_confidence_clamping(condition, confidence)
```

Storm probability overrides (`_apply_storm_probability_overrides`) are retained as a final pass.

### 6. `HourlyForecastGenerator._forecast_hourly_condition()` (replacement)

Same lifecycle lookup replacing the `_calculate_hourly_trajectory` step-based logic. `slot_hour = hour_idx`. `_find_phase(lifecycle, slot_hour)` returns the phase where `start_hour ≤ slot_hour < end_hour`; if `slot_hour` exceeds all phases' `end_hour`, it returns the last phase. Daytime/nighttime conversion applied on top as before.

---

## Confidence Clamping

```
slot_confidence = phase.base_confidence × exp(−slot_hours / 72)
```

| Confidence | Allowed conditions |
|---|---|
| ≥ 0.6 | any (full phase condition applies) |
| 0.4 – 0.59 | rainy, cloudy, partlycloudy, sunny — no extremes (no pouring, no lightning-rainy) |
| < 0.4 | cloudy or partlycloudy only |

Phase base confidence values:

| Phase | Base confidence |
|---|---|
| stable | 0.85 |
| pre_frontal | 0.80 |
| frontal | 0.75 |
| post_frontal | 0.65 |
| clearing | 0.55 |
| stabilizing | 0.45 |

---

## Files Changed

| File | Change |
|---|---|
| `analysis/trends.py` | Add `compute_pressure_acceleration()` |
| `forecast/evolution.py` | Add `LifecyclePhase` dataclass + `compute_lifecycle()` to `EvolutionModeler`; update `model_system_evolution()` to include `lifecycle` key |
| `forecast/daily.py` | Replace `_calculate_condition_trajectory` + `_evolve_condition_by_trajectory` with lifecycle phase lookup; add `_find_phase()` + `_apply_confidence_clamping()` helpers |
| `forecast/hourly.py` | Replace `_calculate_hourly_trajectory` + inline step logic with lifecycle phase lookup |
| `weather_detector.py` | Wire `EvolutionModeler.model_system_evolution()` instead of `{}` |
| `weather.py` | Same wiring |
| `WEATHER_FORECAST_ALGORITHM.md` | Rewrite condition-forecasting sections to describe the lifecycle model |
| `tests/test_weather_detector.py` | New test cases (see Testing section) |

---

## Testing

All tests are `async` following project conventions. New test cases:

1. **`test_pressure_acceleration_falling_fast`** — negative acceleration returns negative float
2. **`test_pressure_acceleration_stable`** — flat pressure returns ~0.0
3. **`test_lifecycle_deteriorating`** — falling trend produces pre_frontal → frontal → post_frontal → clearing phases in correct hour order
4. **`test_lifecycle_improving`** — rising trend produces post_frontal → clearing → stabilizing
5. **`test_lifecycle_stable`** — flat trend returns single `stable` phase spanning 0–120h
6. **`test_condition_clamping_low_confidence`** — slot at hour 100 returns cloudy/partlycloudy regardless of phase condition
7. **`test_daily_forecast_deteriorating_arc`** — end-to-end: falling pressure → day 0 partlycloudy, day 1–2 rainy, day 3 cloudy, day 4 partlycloudy (clamped)
8. **`test_daily_forecast_improving_arc`** — end-to-end: rising pressure → cloudy → partlycloudy → sunny arc
9. **`test_daily_forecast_stable`** — flat pressure → all days match current condition
10. **`test_hourly_forecast_lifecycle_phases`** — hourly slots map correctly to lifecycle phases within 24h
11. **`test_system_evolution_empty_fallback`** — if `system_evolution` is `{}`, forecast falls back to `current_condition` gracefully

---

## Branch & PR

All work on branch `feature/trend-based-lifecycle-forecast`. PR targeting `main`.

---

## Out of Scope

- Temperature, wind, humidity, and precipitation forecasting are not changed by this spec
- No new entries in `meteorological_constants.py`
- No changes to the 7-priority weather condition detection logic in `analysis/core.py`
- No neural network / external NWP data integration
