"""Weather simulator for virtual weather station."""
import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict

from .const import (
    CONF_TEMPERATURE_RANGE,
    CONF_HUMIDITY_RANGE,
    CONF_PRESSURE_RANGE,
    CONF_WIND_SPEED_RANGE,
    CONF_WEATHER_PATTERNS,
    DEFAULT_TEMPERATURE_RANGE,
    DEFAULT_HUMIDITY_RANGE,
    DEFAULT_PRESSURE_RANGE,
    DEFAULT_WIND_SPEED_RANGE,
    WEATHER_PATTERNS,
)


class WeatherSimulator:
    """Simulate realistic weather data."""

    def __init__(self, options: Dict[str, Any]) -> None:
        """Initialize the weather simulator."""
        self.temperature_range = options.get(CONF_TEMPERATURE_RANGE, DEFAULT_TEMPERATURE_RANGE)
        self.humidity_range = options.get(CONF_HUMIDITY_RANGE, DEFAULT_HUMIDITY_RANGE)
        self.pressure_range = options.get(CONF_PRESSURE_RANGE, DEFAULT_PRESSURE_RANGE)
        self.wind_speed_range = options.get(CONF_WIND_SPEED_RANGE, DEFAULT_WIND_SPEED_RANGE)
        self.enabled_patterns = options.get(CONF_WEATHER_PATTERNS, WEATHER_PATTERNS)
        
        # Internal state for continuity
        self._last_values = {}
        self._current_pattern = random.choice(self.enabled_patterns)
        self._pattern_change_time = datetime.now()

    def generate_weather_data(self) -> Dict[str, Any]:
        """Generate current weather data."""
        now = datetime.now()
        
        # Change weather pattern occasionally
        if (now - self._pattern_change_time).total_seconds() > random.randint(1800, 7200):  # 30min to 2hr
            self._current_pattern = random.choice(self.enabled_patterns)
            self._pattern_change_time = now

        # Generate base values with some continuity
        temperature = self._generate_temperature()
        humidity = self._generate_humidity(temperature)
        pressure = self._generate_pressure()
        wind_speed = self._generate_wind_speed()
        wind_direction = self._generate_wind_direction()
        visibility = self._generate_visibility()
        
        # Generate forecast data
        forecast = self._generate_forecast()

        weather_data = {
            "temperature": round(temperature, 1),
            "humidity": round(humidity),
            "pressure": round(pressure, 1),
            "wind_speed": round(wind_speed, 1),
            "wind_direction": round(wind_direction),
            "visibility": round(visibility, 1),
            "condition": self._current_pattern,
            "forecast": forecast,
            "last_updated": now.isoformat(),
        }

        # Store for continuity
        self._last_values = weather_data.copy()
        
        return weather_data

    def _generate_temperature(self) -> float:
        """Generate temperature with daily and seasonal variation."""
        base_temp = self._get_base_value("temperature", self.temperature_range)
        
        # Add daily variation (warmer during day)
        hour = datetime.now().hour
        daily_variation = 3 * math.sin((hour - 6) * math.pi / 12)
        
        # Add pattern-specific adjustments
        pattern_adjustment = self._get_pattern_temperature_adjustment()
        
        # Add some random variation
        random_variation = random.uniform(-1, 1)
        
        temp = base_temp + daily_variation + pattern_adjustment + random_variation
        return max(self.temperature_range[0], min(self.temperature_range[1], temp))

    def _generate_humidity(self, temperature: float) -> float:
        """Generate humidity correlated with temperature and weather pattern."""
        base_humidity = self._get_base_value("humidity", self.humidity_range)
        
        # Inverse correlation with temperature
        temp_effect = -(temperature - 20) * 1.5
        
        # Pattern-specific adjustments
        pattern_adjustment = self._get_pattern_humidity_adjustment()
        
        # Random variation
        random_variation = random.uniform(-5, 5)
        
        humidity = base_humidity + temp_effect + pattern_adjustment + random_variation
        return max(self.humidity_range[0], min(self.humidity_range[1], humidity))

    def _generate_pressure(self) -> float:
        """Generate atmospheric pressure."""
        base_pressure = self._get_base_value("pressure", self.pressure_range)
        
        # Pattern-specific adjustments
        pattern_adjustment = self._get_pattern_pressure_adjustment()
        
        # Small random variation
        random_variation = random.uniform(-2, 2)
        
        pressure = base_pressure + pattern_adjustment + random_variation
        return max(self.pressure_range[0], min(self.pressure_range[1], pressure))

    def _generate_wind_speed(self) -> float:
        """Generate wind speed based on weather pattern."""
        base_wind = self._get_base_value("wind_speed", self.wind_speed_range)
        
        # Pattern-specific adjustments
        pattern_adjustment = self._get_pattern_wind_adjustment()
        
        # Random variation
        random_variation = random.uniform(-2, 2)
        
        wind = base_wind + pattern_adjustment + random_variation
        return max(self.wind_speed_range[0], min(self.wind_speed_range[1], wind))

    def _generate_wind_direction(self) -> float:
        """Generate wind direction."""
        last_direction = self._last_values.get("wind_direction", random.randint(0, 359))
        
        # Small variation from last direction
        variation = random.uniform(-30, 30)
        direction = (last_direction + variation) % 360
        
        return direction

    def _generate_visibility(self) -> float:
        """Generate visibility based on weather pattern."""
        if self._current_pattern == "foggy":
            return random.uniform(0.1, 2.0)
        elif self._current_pattern in ["rainy", "snowy"]:
            return random.uniform(2.0, 8.0)
        elif self._current_pattern == "stormy":
            return random.uniform(1.0, 5.0)
        else:
            return random.uniform(8.0, 20.0)

    def _generate_forecast(self) -> list:
        """Generate 5-day forecast."""
        forecast = []
        current_temp = self._last_values.get("temperature", 20)
        
        for i in range(5):
            date = datetime.now() + timedelta(days=i + 1)
            
            # Gradual temperature change
            temp_change = random.uniform(-3, 3)
            current_temp += temp_change
            current_temp = max(self.temperature_range[0], min(self.temperature_range[1], current_temp))
            
            # Random condition for forecast
            condition = random.choice(self.enabled_patterns)
            
            forecast.append({
                "datetime": date.isoformat(),
                "temperature": round(current_temp, 1),
                "templow": round(current_temp - random.uniform(3, 8), 1),
                "condition": condition,
                "precipitation": self._get_precipitation_for_condition(condition),
                "wind_speed": round(random.uniform(*self.wind_speed_range), 1),
            })
        
        return forecast

    def _get_base_value(self, key: str, value_range: tuple) -> float:
        """Get base value with some continuity from last reading."""
        if key in self._last_values:
            # Small variation from last value
            last_value = self._last_values[key]
            variation = (value_range[1] - value_range[0]) * 0.1  # 10% of range
            return last_value + random.uniform(-variation, variation)
        else:
            # Random value in range
            return random.uniform(*value_range)

    def _get_pattern_temperature_adjustment(self) -> float:
        """Get temperature adjustment based on weather pattern."""
        adjustments = {
            "sunny": 2,
            "cloudy": -1,
            "partly_cloudy": 0,
            "rainy": -3,
            "snowy": -8,
            "stormy": -2,
            "foggy": -1,
        }
        return adjustments.get(self._current_pattern, 0)

    def _get_pattern_humidity_adjustment(self) -> float:
        """Get humidity adjustment based on weather pattern."""
        adjustments = {
            "sunny": -10,
            "cloudy": 5,
            "partly_cloudy": 0,
            "rainy": 20,
            "snowy": 15,
            "stormy": 15,
            "foggy": 25,
        }
        return adjustments.get(self._current_pattern, 0)

    def _get_pattern_pressure_adjustment(self) -> float:
        """Get pressure adjustment based on weather pattern."""
        adjustments = {
            "sunny": 5,
            "cloudy": 0,
            "partly_cloudy": 2,
            "rainy": -8,
            "snowy": -5,
            "stormy": -15,
            "foggy": -3,
        }
        return adjustments.get(self._current_pattern, 0)

    def _get_pattern_wind_adjustment(self) -> float:
        """Get wind speed adjustment based on weather pattern."""
        adjustments = {
            "sunny": -2,
            "cloudy": 0,
            "partly_cloudy": 1,
            "rainy": 3,
            "snowy": 2,
            "stormy": 8,
            "foggy": -3,
        }
        return adjustments.get(self._current_pattern, 0)

    def _get_precipitation_for_condition(self, condition: str) -> float:
        """Get precipitation amount for weather condition."""
        precipitation_map = {
            "sunny": 0,
            "cloudy": 0,
            "partly_cloudy": 0,
            "rainy": random.uniform(0.5, 15),
            "snowy": random.uniform(0.2, 8),
            "stormy": random.uniform(5, 25),
            "foggy": random.uniform(0, 0.5),
        }
        return round(precipitation_map.get(condition, 0), 1)