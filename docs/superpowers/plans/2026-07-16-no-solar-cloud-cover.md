# No-Solar Cloud-Cover Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent missing solar sensors from forcing a cloudy daytime condition, while preserving cloudy classification for actual zero readings and stabilizing the seasonal solar test.

**Architecture:** Record solar-source availability from raw sensor input before zero-normalization. Use that availability flag to select the atmospheric fallback only when all three solar measurements are absent. Keep the `SolarAnalyzer` unchanged so configured zero readings continue to model full cloud cover; freeze the test clock rather than changing seasonal production logic.

**Tech Stack:** Python 3.13, Home Assistant weather condition constants, pytest, unittest.mock.

---

### Task 1: Specify source-availability behavior with regression tests

**Files:**
- Modify: `tests/test_analysis_core.py:466-502`
- Modify: `tests/test_analysis_solar.py:1-110`

- [ ] **Step 1: Write the failing no-solar-sensor regression test**

Replace the solar input entries in `test_no_solar_sensors_uses_elevation_for_daytime` with no solar keys, retain `solar_elevation=34.22`, and require the clear atmospheric sample to classify as sunny:

```python
result = analyzers["core"].determine_condition(sensor_data, 0.0)

assert result == ATTR_CONDITION_SUNNY
```

- [ ] **Step 2: Verify the regression test fails against the current implementation**

Run:

```bash
/Users/ace/Projects/HA/micro-weather-station/test_env/bin/python -m pytest tests/test_analysis_core.py::TestWeatherConditionAnalyzer::test_no_solar_sensors_uses_elevation_for_daytime -v
```

Expected: FAIL because the current code normalizes missing values to `0.0`, sends them to `SolarAnalyzer`, and returns `cloudy`.

- [ ] **Step 3: Add a configured-zero control test**

Add a test in `TestWeatherConditionAnalyzer` that supplies a clear daytime sample with `solar_radiation=0.0`, `solar_lux=0.0`, `uv_index=0.0`, and `solar_elevation=45.0`. Assert `ATTR_CONDITION_CLOUDY` so the availability change cannot make true zero readings fall back to atmospheric classification.

```python
assert analyzers["core"].determine_condition(sensor_data, 0.0) == ATTR_CONDITION_CLOUDY
```

- [ ] **Step 4: Stabilize the date-sensitive solar assertion**

Import `patch` and wrap the first call in `test_analyze_cloud_cover_low_solar_radiation_fallback` with a fixed module clock:

```python
with patch("custom_components.micro_weather.analysis.solar.datetime") as mock_datetime:
    mock_datetime.now.return_value = datetime(2024, 1, 15)
    cloud_cover_heavy = analyzer.analyze_cloud_cover(20.0, 3000.0, 0.0, 15.0)

assert cloud_cover_heavy == pytest.approx(74.4, abs=0.5)
```

This preserves the test's intended numerical assertion while removing the live-clock dependency.

### Task 2: Preserve solar-source availability through normalization

**Files:**
- Modify: `custom_components/micro_weather/analysis/core.py:121-190`
- Modify: `custom_components/micro_weather/analysis/core.py:716-739`

- [ ] **Step 1: Add the availability flag to normalized sensor data**

Before the return dictionary in `_extract_sensors`, compute whether any raw solar key contains a non-`None` value:

```python
has_solar_measurements = any(
    sensor_data.get(key) is not None
    for key in (KEY_SOLAR_RADIATION, KEY_SOLAR_LUX_INTERNAL, KEY_UV_INDEX)
)
```

Include it in the returned dictionary without changing the normalized float fields:

```python
"has_solar_measurements": has_solar_measurements,
```

- [ ] **Step 2: Route only unavailable solar sources to the atmospheric fallback**

At the beginning of `_determine_daytime_condition`, replace the numeric `has_solar_data` calculation with:

```python
if not sensors["has_solar_measurements"]:
    return self._atmospheric_fallback_condition(sensors, params)
```

Keep the existing solar-elevation estimation block for available solar values with no `sun.sun` entity. This preserves all existing cloud-cover behavior whenever at least one solar source reports a value, including zero.

- [ ] **Step 3: Run focused regression tests**

Run:

```bash
/Users/ace/Projects/HA/micro-weather-station/test_env/bin/python -m pytest tests/test_analysis_core.py tests/test_analysis_solar.py -v
```

Expected: PASS, including the new missing-source and zero-source cases and the fixed-date solar assertion.

### Task 3: Verify integration scope and quality gates

**Files:**
- Verify only: `custom_components/micro_weather/analysis/core.py`
- Verify only: `tests/test_weather_detector.py`
- Verify only: `tests/test_validation.py`

- [ ] **Step 1: Run the CI-targeted tests**

Run:

```bash
/Users/ace/Projects/HA/micro-weather-station/test_env/bin/python -m pytest tests/test_weather_detector.py tests/test_validation.py -v
```

Expected: PASS.

- [ ] **Step 2: Run style and type checks**

Run:

```bash
/Users/ace/Projects/HA/micro-weather-station/test_env/bin/python -m black --check --diff custom_components/ tests/
/Users/ace/Projects/HA/micro-weather-station/test_env/bin/python -m isort --check-only --diff custom_components/ tests/
/Users/ace/Projects/HA/micro-weather-station/test_env/bin/python -m flake8 custom_components/ tests/ --max-complexity=10 --max-line-length=88
/Users/ace/Projects/HA/micro-weather-station/test_env/bin/python -m mypy custom_components/ --ignore-missing-imports
```

Expected: PASS.

- [ ] **Step 3: Run the complete test suite**

Run:

```bash
/Users/ace/Projects/HA/micro-weather-station/test_env/bin/python -m pytest tests/ -v
```

Expected: PASS with no date-dependent solar failure.

- [ ] **Step 4: Commit the implementation**

Run:

```bash
git add custom_components/micro_weather/analysis/core.py tests/test_analysis_core.py tests/test_analysis_solar.py docs/superpowers/specs/2026-07-16-no-solar-cloud-cover-design.md docs/superpowers/plans/2026-07-16-no-solar-cloud-cover.md
git commit -m "fix: distinguish missing solar sensors from zero readings"
```
