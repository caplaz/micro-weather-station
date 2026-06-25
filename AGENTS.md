# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Commands

```bash
# Tests
python -m pytest tests/ -v                                          # full suite
python -m pytest tests/test_weather_detector.py -v                 # single file
python -m pytest tests/test_analysis_core.py::ClassName::test_name # single test

# Formatting & lint (must pass CI)
black custom_components/
isort custom_components/
flake8 custom_components/ --max-complexity=10 --max-line-length=88
mypy custom_components/ --ignore-missing-imports
bandit -r custom_components/

# CI check (non-destructive)
black --check --diff custom_components/
isort --check-only --diff custom_components/
```

Pre-commit hooks enforce black, isort, and flake8 automatically.

## Architecture

The integration lives entirely in `custom_components/micro_weather/`. It reads HA sensor entities, derives weather conditions and forecasts through a modular analyzer pipeline, and exposes 1 weather entity + 9 sensor entities.

### Data flow

```
HA sensor entities (15 configurable inputs)
    ↓
WeatherDetector.get_weather_data()          ← orchestrator in weather_detector.py
    ├─ TrendsAnalyzer                       ← stores 48h of readings (192-entry deque)
    ├─ AtmosphericAnalyzer                  ← pressure correction, fog scoring
    ├─ SolarAnalyzer                        ← cloud cover from solar radiation vs. clear-sky model
    └─ WeatherConditionAnalyzer             ← 7-priority condition determination (see below)
    ↓
MeteorologicalAnalyzer                      ← atmospheric stability, wind, moisture state
    ↓
DailyForecastGenerator + HourlyForecastGenerator
    ↓
MicroWeatherEntity (weather.py) + MicroWeatherSensor ×9 (sensor.py)
```

The coordinator (`__init__.py` → `MicroWeatherCoordinator`) drives periodic updates (default 5 min) and calls `WeatherDetector`.

### Weather condition priority (WeatherConditionAnalyzer)

Conditions are resolved top-down; the first match wins:

| Priority | Condition |
|----------|-----------|
| 0 | Lightning sensor active (Ecowitt WH57 or similar) |
| 1 | Precipitation (rain/snow) |
| 2 | Fog (humidity >98% + solar radiation <50 W/m²) |
| 3 | Storm (lightning + rain, high wind) |
| 4 | Severe weather (gales, extremes) |
| 5 | Daytime/nighttime cloud cover (uses solar elevation) |
| 6 | Default (cloudy) |

### Key files

| File | Role |
|------|------|
| `weather_detector.py` | Orchestrator; entry point for all analysis |
| `analysis/core.py` | `WeatherConditionAnalyzer` — priority-based condition logic |
| `analysis/atmospheric.py` | Pressure trends, altitude correction, fog scoring |
| `analysis/solar.py` | Clear-sky model, cloud cover estimation |
| `analysis/trends.py` | 48h historical data storage and pattern queries |
| `forecast/meteorological.py` | Atmospheric stability, moisture, wind state |
| `forecast/daily.py` | 5-day pressure-trend-driven forecast |
| `forecast/hourly.py` | 24h micro-evolution forecast |
| `forecast/evolution.py` | Weather system transitions + confidence dampening |
| `meteorological_constants.py` | Physics constants and thresholds (35KB — the source of truth for all tunable values) |
| `weather_utils.py` | Unit conversions (temp, pressure, wind, altitude) |
| `config_flow.py` | HA config UI; sensor entity mapping + altitude |

### Algorithm documentation

Two detailed design docs exist at the repo root:
- `WEATHER_DETECTION_ALGORITHM.md` — detection logic
- `WEATHER_FORECAST_ALGORITHM.md` — forecasting principles

Read these before modifying analyzer logic or threshold values.

### Testing notes

- All tests are `async`; `asyncio_mode=auto` is set in `pyproject.toml` — no `@pytest.mark.asyncio` needed.
- CI only runs `test_weather_detector.py` and `test_validation.py` (full config_flow tests require a heavier HA setup).
- `conftest.py` provides `mock_config_entry`, `mock_sensor_data` (imperial units: °F/inHg/mph), and `mock_hass` fixtures.
- Only `outdoor_temperature` sensor is required; all others are optional with graceful degradation.
