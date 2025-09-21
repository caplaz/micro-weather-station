"""Constants for the Micro Weather Station integration."""

DOMAIN = "micro_weather"

# Configuration options
CONF_TEMPERATURE_RANGE = "temperature_range"
CONF_HUMIDITY_RANGE = "humidity_range"
CONF_PRESSURE_RANGE = "pressure_range"
CONF_WIND_SPEED_RANGE = "wind_speed_range"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_WEATHER_PATTERNS = "weather_patterns"

# Sensor entity configuration
CONF_OUTDOOR_TEMP_SENSOR = "outdoor_temp_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_DEWPOINT_SENSOR = "dewpoint_sensor"
CONF_PRESSURE_SENSOR = "pressure_sensor"
CONF_WIND_SPEED_SENSOR = "wind_speed_sensor"
CONF_WIND_DIRECTION_SENSOR = "wind_direction_sensor"
CONF_WIND_GUST_SENSOR = "wind_gust_sensor"
CONF_RAIN_RATE_SENSOR = "rain_rate_sensor"
CONF_RAIN_STATE_SENSOR = "rain_state_sensor"
CONF_SOLAR_RADIATION_SENSOR = "solar_radiation_sensor"
CONF_SOLAR_LUX_SENSOR = "solar_lux_sensor"
CONF_UV_INDEX_SENSOR = "uv_index_sensor"

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
    "foggy",
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
