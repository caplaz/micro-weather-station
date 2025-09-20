"""Constants for the Virtual Weather Station integration."""

DOMAIN = "virtual_weather"

# Configuration options
CONF_TEMPERATURE_RANGE = "temperature_range"
CONF_HUMIDITY_RANGE = "humidity_range"
CONF_PRESSURE_RANGE = "pressure_range"
CONF_WIND_SPEED_RANGE = "wind_speed_range"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_WEATHER_PATTERNS = "weather_patterns"

# Default configuration values
DEFAULT_TEMPERATURE_RANGE = (-10, 35)  # Celsius
DEFAULT_HUMIDITY_RANGE = (30, 90)  # Percentage
DEFAULT_PRESSURE_RANGE = (990, 1030)  # hPa
DEFAULT_WIND_SPEED_RANGE = (0, 25)  # km/h
DEFAULT_UPDATE_INTERVAL = 5  # minutes

# Weather patterns
WEATHER_PATTERNS = [
    "sunny",
    "cloudy", 
    "partly_cloudy",
    "rainy",
    "snowy",
    "stormy",
    "foggy"
]

# Sensor types
SENSOR_TYPES = {
    "temperature": {
        "name": "Temperature",
        "device_class": "temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
    },
    "humidity": {
        "name": "Humidity", 
        "device_class": "humidity",
        "unit": "%",
        "icon": "mdi:water-percent",
    },
    "pressure": {
        "name": "Pressure",
        "device_class": "pressure", 
        "unit": "hPa",
        "icon": "mdi:gauge",
    },
    "wind_speed": {
        "name": "Wind Speed",
        "device_class": "wind_speed",
        "unit": "km/h", 
        "icon": "mdi:weather-windy",
    },
    "wind_direction": {
        "name": "Wind Direction",
        "unit": "°",
        "icon": "mdi:compass",
    },
    "visibility": {
        "name": "Visibility",
        "unit": "km",
        "icon": "mdi:eye",
    },
}