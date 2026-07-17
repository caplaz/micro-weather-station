"""End-to-end simulation of the full detection + forecast pipeline.

Drives the real WeatherDetector (no mocked analyzers) with synthetic
sensor data over many update cycles, the way the coordinator does in
production since the 4.4.1 persistent-detector change.

This is a structural guard against the producer/consumer mismatches
behind #35, #46, #49 and #51: every analyzer runs against the real dicts
its consumers read, with realistic accumulated history.
"""

from datetime import datetime, timedelta
import math
from unittest.mock import Mock

from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import METRIC_SYSTEM
import pytest

from custom_components.micro_weather.weather_detector import WeatherDetector

SENSOR_ENTITIES = {
    "outdoor_temp": "sensor.outdoor_temperature",
    "humidity": "sensor.humidity",
    "pressure": "sensor.pressure",
    "wind_speed": "sensor.wind_speed",
    "wind_direction": "sensor.wind_direction",
    "wind_gust": "sensor.wind_gust",
    "rain_rate": "sensor.rain_rate",
    "solar_radiation": "sensor.solar_radiation",
    "uv_index": "sensor.uv_index",
}

OPTIONS = {
    "outdoor_temp_sensor": SENSOR_ENTITIES["outdoor_temp"],
    "humidity_sensor": SENSOR_ENTITIES["humidity"],
    "pressure_sensor": SENSOR_ENTITIES["pressure"],
    "wind_speed_sensor": SENSOR_ENTITIES["wind_speed"],
    "wind_direction_sensor": SENSOR_ENTITIES["wind_direction"],
    "wind_gust_sensor": SENSOR_ENTITIES["wind_gust"],
    "rain_rate_sensor": SENSOR_ENTITIES["rain_rate"],
    "solar_radiation_sensor": SENSOR_ENTITIES["solar_radiation"],
    "uv_index_sensor": SENSOR_ENTITIES["uv_index"],
}

UNITS = {
    "outdoor_temp": "°F",
    "humidity": "%",
    "pressure": "inHg",
    "wind_speed": "mph",
    "wind_direction": "°",
    "wind_gust": "mph",
    "rain_rate": "in/h",
    "solar_radiation": "W/m²",
    "uv_index": "",
}


def _clear_day_reading(hour_float):
    """Synthetic clear summer day: sinusoidal sun, mild diurnal cycle."""
    # Solar elevation peaks ~60° at 13:00; day from 06:00 to 20:00
    if 6.0 <= hour_float <= 20.0:
        solar_fraction = math.sin(math.pi * (hour_float - 6.0) / 14.0)
    else:
        solar_fraction = 0.0
    radiation = 850.0 * solar_fraction
    return {
        "outdoor_temp": 68.0 + 12.0 * solar_fraction,
        "humidity": 60.0 - 15.0 * solar_fraction,
        "pressure": 30.05 + 0.02 * math.sin(hour_float / 6.0),  # gentle wobble
        "wind_speed": 4.0 + 3.0 * solar_fraction,
        "wind_direction": 200.0 + 10.0 * math.sin(hour_float),
        "wind_gust": 6.0 + 4.0 * solar_fraction,
        "rain_rate": 0.0,
        "solar_radiation": radiation,
        "uv_index": 8.0 * solar_fraction,
    }


def _make_hass(readings_ref):
    hass = Mock(spec=HomeAssistant)
    hass.config = Mock()
    hass.config.units = METRIC_SYSTEM

    def get_state(entity_id):
        for key, entity in SENSOR_ENTITIES.items():
            if entity == entity_id:
                state = Mock()
                state.state = str(readings_ref["current"][key])
                state.attributes = {"unit_of_measurement": UNITS[key]}
                return state
        return None

    hass.states = Mock()
    hass.states.get = get_state
    return hass


class TestClearDaySimulation:
    """Simulate a persistent detector through a clear day of updates."""

    @pytest.fixture
    def simulation(self, freezer):
        readings_ref = {"current": _clear_day_reading(8.0)}
        hass = _make_hass(readings_ref)
        detector = WeatherDetector(hass, OPTIONS)
        return detector, readings_ref, freezer

    def _run(self, simulation, start_hour, end_hour, step_minutes=15):
        detector, readings_ref, freezer = simulation
        # Anchor to a fixed summer morning
        start = datetime(2026, 7, 10, int(start_hour), 0, 0)
        freezer.move_to(start)
        results = []
        minutes_total = int((end_hour - start_hour) * 60)
        for elapsed in range(0, minutes_total + 1, step_minutes):
            now = start + timedelta(minutes=elapsed)
            freezer.move_to(now)
            hour_float = now.hour + now.minute / 60.0
            readings_ref["current"] = _clear_day_reading(hour_float)
            results.append((hour_float, detector.get_weather_data()))
        return results

    def test_clear_midday_reads_sunny_with_low_cloud_cover(self, simulation):
        """From 08:00 to 13:00 on a clear day, midday must be sunny with
        low cloud coverage and a populated 5-day forecast."""
        results = self._run(simulation, start_hour=8.0, end_hour=13.0)

        final_hour, final_data = results[-1]
        assert final_data["condition"] == "sunny", (
            f"clear midday read as {final_data['condition']!r} "
            f"(cloud={final_data.get('cloud_coverage')})"
        )
        assert final_data.get("cloud_coverage", 100) < 30

        forecast = final_data["forecast"]
        assert len(forecast) == 5
        for day in forecast:
            # No precipitation events invented from a stable clear day
            assert day["condition"] in {
                "sunny",
                "partlycloudy",
                "clear-night",
            }, f"stable clear day forecast produced {day['condition']!r}"
            # Temperatures converted to °C and physically plausible
            assert -40.0 < day["temperature"] < 55.0
            assert day["templow"] < day["temperature"]

    def test_no_storm_probability_from_stable_pressure(self, simulation):
        """A gently wobbling barometer must not fabricate storms."""
        self._run(simulation, start_hour=8.0, end_hour=12.0)
        detector = simulation[0]
        trends = detector.trends_analyzer.analyze_pressure_trends(0.0)
        assert trends["storm_probability"] == 0.0
        assert abs(trends["current_trend"]) < 1.0  # hPa/3h — stable

    def test_forecast_render_does_not_corrupt_cloud_history(self, simulation):
        """Simulate HA calling the meteorological analysis (hourly forecast
        path) between detector updates: the stored cloud history and the
        cloud_coverage attribute must be unaffected."""
        results = self._run(simulation, start_hour=9.0, end_hour=12.0)
        detector = simulation[0]

        before = [e["value"] for e in detector._sensor_history["cloud_cover"]]
        # Forecast-path analysis with a metric-style snapshot missing solar
        # keys (what weather.py builds from coordinator data)
        detector.meteorological_analyzer.analyze_state(
            {"temperature": 75.0, "humidity": 50.0, "pressure": 29.92}, 0.0
        )
        after = [e["value"] for e in detector._sensor_history["cloud_cover"]]
        assert before == after

        _, final_data = results[-1]
        assert final_data.get("cloud_coverage", 100) < 30


class TestApproachingFrontSimulation:
    """A genuine pressure fall must still register — the hPa retuning and
    noise guards must not have deadened real-front sensitivity."""

    def test_falling_pressure_produces_storm_signal_and_wet_forecast(self, freezer):
        readings_ref = {"current": _clear_day_reading(8.0)}
        hass = _make_hass(readings_ref)
        detector = WeatherDetector(hass, OPTIONS)

        start = datetime(2026, 7, 10, 6, 0, 0)
        freezer.move_to(start)
        # 8 hours of steadily falling pressure (~0.03 inHg/h ≈ 3 hPa/3h —
        # an unambiguous front), thickening clouds, rising humidity.
        data = None
        for elapsed in range(0, 8 * 60 + 1, 15):
            now = start + timedelta(minutes=elapsed)
            freezer.move_to(now)
            hour_float = now.hour + now.minute / 60.0
            reading = _clear_day_reading(hour_float)
            hours_in = elapsed / 60.0
            reading["pressure"] = 30.05 - 0.03 * hours_in
            fade = max(0.25, 1.0 - 0.1 * hours_in)  # clouds thicken
            reading["solar_radiation"] *= fade
            reading["uv_index"] *= fade
            reading["humidity"] = min(95.0, reading["humidity"] + 3.0 * hours_in)
            readings_ref["current"] = reading
            data = detector.get_weather_data()

        trends = detector.trends_analyzer.analyze_pressure_trends(0.0)
        assert trends["current_trend"] < -1.0, "front not detected"
        assert trends["storm_probability"] >= 40.0

        forecast_conditions = [day["condition"] for day in data["forecast"]]
        wet = {"rainy", "pouring", "lightning-rainy", "cloudy"}
        assert any(
            c in wet for c in forecast_conditions
        ), f"approaching front produced only {forecast_conditions}"
