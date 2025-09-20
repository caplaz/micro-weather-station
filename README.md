# Micro Weather Station for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

A Home Assistant custom integration that creates a smart weather station by analyzing your existing sensor data to determine accurate weather conditions for your specific location and microclimate. Weather station data from external services can be unreliable or not reflect your specific environment - this integration uses your actual sensor readings to provide weather conditions that truly represent what's happening at your location.

![Micro Weather Station][logo]

## Why This Integration?

Weather station data can be unreliable or not reflect your specific microclimate. Here are better ways to detect weather conditions using your actual sensor data:

- **🎯 Microclimate Accuracy**: Your backyard might be sunny while the nearest weather station reports cloudy
- **🌡️ Local Temperature**: Your sensors know the exact temperature in your garden, not 10 miles away
- **🌧️ Precipitation Detection**: Know immediately when it starts raining at your location
- **💨 Wind Conditions**: Detect actual wind conditions affected by your local terrain and structures
- **☀️ Solar Analysis**: Use your solar radiation sensors to accurately detect cloud cover
- **🏠 Hyperlocal Weather**: Get weather conditions specific to your property and environment

This integration analyzes your real sensor data to provide weather conditions that truly represent what's happening at your exact location.

## Features

- 🌡️ **Smart Weather Detection**: Analyzes real sensor data to determine weather conditions
- 🧠 **Intelligent Algorithms**: Uses solar radiation, precipitation, wind, and pressure data
- 📊 **Individual Sensors**: Separate sensor entities for each weather parameter
- 🌦️ **Weather Entity**: Complete weather entity with current conditions and 5-day forecast
- ⚙️ **Flexible Configuration**: Works with any combination of available sensors
- 🔄 **Real-time Analysis**: Updates based on actual sensor readings
- 📱 **Easy Configuration**: Simple setup through Home Assistant UI with sensor selection

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS → Integrations
3. Click the three dots menu → Custom repositories
4. Add this repository: `https://github.com/caplaz/micro-weather-station`
5. Category: Integration
6. Click "Add"
7. Find "Micro Weather Station" in the list and install it
8. Restart Home Assistant

### Manual Installation

1. Download the `micro_weather` folder from the latest release
2. Copy the folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Adding the Integration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Micro Weather Station"
4. Select your sensor entities from the dropdown menus
5. Configure update interval

### Required Sensors

| Sensor Type         | Description                   | Required        |
| ------------------- | ----------------------------- | --------------- |
| Outdoor Temperature | Temperature sensor (°F or °C) | ✅ **Required** |

### Optional Sensors

| Sensor Type        | Description                   | Used For                          |
| ------------------ | ----------------------------- | --------------------------------- |
| Indoor Temperature | Indoor temperature sensor     | Temperature differential analysis |
| Humidity           | Humidity percentage sensor    | Humidity readings                 |
| Pressure           | Atmospheric pressure sensor   | Storm detection                   |
| Wind Speed         | Wind speed sensor             | Wind conditions                   |
| Wind Direction     | Wind direction sensor         | Wind data                         |
| Wind Gust          | Wind gust sensor              | Storm detection                   |
| Rain Rate          | Precipitation rate sensor     | Precipitation detection           |
| Rain State         | Rain state sensor (dry/wet)   | Precipitation detection           |
| Solar Radiation    | Solar radiation sensor (W/m²) | Cloud cover detection             |
| Solar Lux          | Light level sensor (lx)       | Day/night and cloud detection     |
| UV Index           | UV index sensor               | Clear sky detection               |

### Example Sensor Configuration

```yaml
# Example sensor mappings for weather station:
Outdoor Temperature: sensor.outdoor_temperature
Indoor Temperature: sensor.indoor_temperature
Humidity: sensor.indoor_humidity
Pressure: sensor.relative_pressure
Wind Speed: sensor.wind_speed
Wind Direction: sensor.wind_direction
Wind Gust: sensor.wind_gust
Rain Rate: sensor.rain_rate_piezo
Rain State: sensor.rain_state_piezo
Solar Radiation: sensor.solar_radiation
Solar Lux: sensor.solar_lux
UV Index: sensor.uv_index
```

## Entities Created

### Weather Entity

- `weather.micro_weather_station` - Main weather entity with current conditions and forecast

### Sensor Entities

- `sensor.micro_weather_station_temperature` - Current temperature (°C)
- `sensor.micro_weather_station_humidity` - Current humidity (%)
- `sensor.micro_weather_station_pressure` - Current pressure (hPa)
- `sensor.micro_weather_station_wind_speed` - Current wind speed (km/h)
- `sensor.micro_weather_station_wind_direction` - Current wind direction (°)
- `sensor.micro_weather_station_visibility` - Current visibility (km)

## Weather Detection Logic

The integration intelligently detects weather conditions using your real sensor data with the following priority system:

| Condition        | Detection Criteria                    | Priority    |
| ---------------- | ------------------------------------- | ----------- |
| ⛈️ Stormy        | Rain + High Wind (>25 km/h)           | 1 (Highest) |
| 🌧️ Rainy         | Active precipitation detected         | 2           |
| ❄️ Snowy         | Rain + Low temperature (<2°C)         | 3           |
| �️ Foggy         | Low solar radiation + High humidity   | 4           |
| ☀️ Sunny         | High solar radiation (>400 W/m²)      | 5           |
| ⛅ Partly Cloudy | Medium solar radiation (100-400 W/m²) | 6           |
| ☁️ Cloudy        | Low solar radiation (<100 W/m²)       | 7 (Default) |

The algorithm analyzes your sensor readings in real-time to provide accurate weather condition detection.

## Automation Examples

### Weather-Based Lighting

````yaml
automation:
  - alias: "Cloudy Day Lights"
    trigger:
      - platform: state
        entity_id: weather.micro_weather_station
        to: "cloudy"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness: 200

### Storm Preparation

```yaml
automation:
  - alias: "Storm Alert"
    trigger:
      - platform: state
        entity_id: weather.micro_weather_station
        to: "lightning-rainy"
    action:
      - service: notify.mobile_app
        data:
          message: "Storm detected! Secure outdoor items."
          title: "Weather Alert"

### Smart Irrigation

```yaml
automation:
  - alias: "Skip Irrigation on Rain"
    trigger:
      - platform: time
        at: "06:00:00"
    condition:
      - condition: not
        conditions:
          - condition: state
            entity_id: weather.micro_weather_station
            state: "rainy"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.garden_sprinklers
````

## Temperature Alerts

```yaml
automation:
  - alias: "High Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.micro_weather_station_temperature
        above: 30
    action:
      - service: notify.mobile_app
        data:
          message: "Temperature is high: {{ states('sensor.micro_weather_station_temperature') }}°C"
```

## Lovelcaplaz Cards

### Weather Card

```yaml
type: weather-forecast
entity: weather.micro_weather_station
```

### Sensor Dashboard

```yaml
type: entities
entities:
  - entity: sensor.micro_weather_station_temperature
    name: Temperature
  - entity: sensor.micro_weather_station_humidity
    name: Humidity
  - entity: sensor.micro_weather_station_pressure
    name: Pressure
  - entity: sensor.micro_weather_station_wind_speed
    name: Wind Speed
title: Weather Station
```

### Weather Chart

```yaml
type: history-graph
entities:
  - sensor.micro_weather_station_temperature
  - sensor.micro_weather_station_humidity
hours_to_show: 24
refresh_interval: 300
```

## Development and Testing

This integration is perfect for:

- 🌡️ **Smart Weather Detection**: Use your existing sensors to get intelligent weather condition detection
- 🏠 **Enhanced Automations**: Create more accurate weather-based automations using real sensor data
- � **Data Analysis**: Understand weather patterns based on your actual sensor readings
- � **Accurate Forecasting**: Get weather conditions that match your local environment
- 🔧 **Sensor Integration**: Make better use of your weather station investment

## Troubleshooting

### Integration Not Loading

- Check Home Assistant logs for errors
- Ensure all files are in the correct directory
- Restart Home Assistant after installation

### No Sensor Data

- Verify that your configured sensors exist and have valid states
- Check sensor entity IDs in the integration configuration
- Review entity states in Developer Tools → States

### Weather Conditions Not Updating

- Ensure your sensors are providing current data
- Check that sensor values are within expected ranges
- Verify the integration update interval in configuration
- Review logs for any sensor reading errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Home Assistant
5. Submit a pull request

## Support

- 🐛 [Report Issues](https://github.com/caplaz/micro-weather-station/issues)
- 💬 [Community Forum](https://community.home-assistant.io/)
- 📚 [Home Assistant Documentation](https://www.home-assistant.io/docs/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0

- Initial release
- Weather entity with intelligent condition detection
- Individual sensor entities for all weather parameters
- Configurable sensor mapping and detection thresholds
- Support for multiple weather condition types
- HACS compatibility

---

**Note**: This smart weather station uses your existing sensor data to intelligently detect weather conditions. Configure your sensors during setup to get accurate weather detection based on your local environment.

[commits-shield]: https://img.shields.io/github/commit-activity/y/caplaz/micro-weather-station.svg?style=for-the-badge
[commits]: https://github.com/caplaz/micro-weather-station/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/caplaz/micro-weather-station.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/caplaz/micro-weather-station.svg?style=for-the-badge
[releases]: https://github.com/caplaz/micro-weather-station/releases
[logo]: https://raw.githubusercontent.com/caplaz/micro-weather-station/main/images/logo.png
