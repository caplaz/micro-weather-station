# Virtual Weather Station for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

A Home Assistant custom integration that creates a virtual weather station with realistic simulated weather data. Perfect for testing, development, or areas where real weather data isn't available.

![Virtual Weather Station][logo]

## Features

- 🌡️ **Realistic Weather Simulation**: Temperature, humidity, pressure, wind speed and direction
- 🌤️ **Multiple Weather Patterns**: Sunny, cloudy, rainy, snowy, stormy, and foggy conditions
- 📊 **Individual Sensors**: Separate sensor entities for each weather parameter
- 🌦️ **Weather Entity**: Complete weather entity with current conditions and 5-day forecast
- ⚙️ **Configurable Parameters**: Customize temperature ranges, update intervals, and enabled weather patterns
- 🔄 **Realistic Transitions**: Gradual changes between weather conditions with continuity
- 📱 **Easy Configuration**: Simple setup through Home Assistant UI

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS → Integrations
3. Click the three dots menu → Custom repositories
4. Add this repository: `https://github.com/ace/virtual-weather-station`
5. Category: Integration
6. Click "Add"
7. Find "Virtual Weather Station" in the list and install it
8. Restart Home Assistant

### Manual Installation

1. Download the `virtual_weather` folder from the latest release
2. Copy the folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Adding the Integration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Virtual Weather Station"
4. Follow the configuration steps

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| Temperature Range | Min/max temperature in °C | -10, 35 |
| Humidity Range | Min/max humidity in % | 30, 90 |
| Pressure Range | Min/max pressure in hPa | 990, 1030 |
| Wind Speed Range | Min/max wind speed in km/h | 0, 25 |
| Update Interval | How often to update data (minutes) | 5 |
| Weather Patterns | Which weather conditions to simulate | All |

### Example Configuration

```yaml
# Example ranges for different climates:

# Tropical Climate
Temperature: 20, 35
Humidity: 60, 95
Pressure: 1005, 1020

# Arctic Climate  
Temperature: -30, 5
Humidity: 50, 85
Pressure: 980, 1030

# Desert Climate
Temperature: 5, 45
Humidity: 10, 40
Pressure: 1000, 1025
```

## Entities Created

### Weather Entity
- `weather.virtual_weather_station` - Main weather entity with current conditions and forecast

### Sensor Entities
- `sensor.virtual_weather_station_temperature` - Current temperature (°C)
- `sensor.virtual_weather_station_humidity` - Current humidity (%)
- `sensor.virtual_weather_station_pressure` - Current pressure (hPa)
- `sensor.virtual_weather_station_wind_speed` - Current wind speed (km/h)
- `sensor.virtual_weather_station_wind_direction` - Current wind direction (°)
- `sensor.virtual_weather_station_visibility` - Current visibility (km)

## Weather Patterns

The integration simulates the following weather conditions:

| Pattern | Description | Temperature | Humidity | Pressure | Wind |
|---------|-------------|-------------|----------|----------|------|
| ☀️ Sunny | Clear skies | +2°C | -10% | +5 hPa | -2 km/h |
| ☁️ Cloudy | Overcast | -1°C | +5% | 0 hPa | 0 km/h |
| ⛅ Partly Cloudy | Mixed conditions | 0°C | 0% | +2 hPa | +1 km/h |
| 🌧️ Rainy | Precipitation | -3°C | +20% | -8 hPa | +3 km/h |
| ❄️ Snowy | Snow conditions | -8°C | +15% | -5 hPa | +2 km/h |
| ⛈️ Stormy | Thunderstorms | -2°C | +15% | -15 hPa | +8 km/h |
| 🌫️ Foggy | Low visibility | -1°C | +25% | -3 hPa | -3 km/h |

## Automation Examples

### Weather-Based Lighting

```yaml
automation:
  - alias: "Cloudy Day Lights"
    trigger:
      - platform: state
        entity_id: weather.virtual_weather_station
        to: "cloudy"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness_pct: 80
```

### Temperature Alerts

```yaml
automation:
  - alias: "High Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.virtual_weather_station_temperature
        above: 30
    action:
      - service: notify.mobile_app
        data:
          message: "Temperature is high: {{ states('sensor.virtual_weather_station_temperature') }}°C"
```

### Storm Warning

```yaml
automation:
  - alias: "Storm Warning"
    trigger:
      - platform: state
        entity_id: weather.virtual_weather_station
        to: "lightning-rainy"
    action:
      - service: script.secure_outdoor_furniture
      - service: notify.family
        data:
          message: "Storm detected! Securing outdoor items."
```

## Lovelace Cards

### Weather Card

```yaml
type: weather-forecast
entity: weather.virtual_weather_station
```

### Sensor Dashboard

```yaml
type: entities
entities:
  - entity: sensor.virtual_weather_station_temperature
    name: Temperature
  - entity: sensor.virtual_weather_station_humidity  
    name: Humidity
  - entity: sensor.virtual_weather_station_pressure
    name: Pressure
  - entity: sensor.virtual_weather_station_wind_speed
    name: Wind Speed
title: Weather Station
```

### Weather Chart

```yaml
type: history-graph
entities:
  - sensor.virtual_weather_station_temperature
  - sensor.virtual_weather_station_humidity
hours_to_show: 24
refresh_interval: 300
```

## Development and Testing

This integration is perfect for:

- 🧪 **Testing Automations**: Test weather-based automations without waiting for real weather
- 🏠 **Development**: Develop weather-dependent features in controlled conditions  
- 📚 **Learning**: Understand how weather entities work in Home Assistant
- 🎭 **Demonstrations**: Show off weather automations with predictable data
- 🔧 **Prototyping**: Build weather-related integrations and dashboards

## Troubleshooting

### Integration Not Loading
- Check Home Assistant logs for errors
- Ensure all files are in the correct directory
- Restart Home Assistant after installation

### No Data Showing
- Verify the integration is configured correctly
- Check that the update interval isn't too long
- Review entity states in Developer Tools

### Weather Patterns Not Changing
- Patterns change randomly every 30 minutes to 2 hours
- Check that multiple patterns are enabled in configuration
- Restart the integration to force a pattern change

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Home Assistant
5. Submit a pull request

## Support

- 🐛 [Report Issues](https://github.com/ace/virtual-weather-station/issues)
- 💬 [Community Forum](https://community.home-assistant.io/)
- 📚 [Home Assistant Documentation](https://www.home-assistant.io/docs/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0
- Initial release
- Weather entity with current conditions and forecast
- Individual sensor entities for all weather parameters
- Configurable weather simulation parameters
- Support for multiple weather patterns
- HACS compatibility

---

**Note**: This is a virtual weather station that generates simulated data. It does not connect to any real weather services or hardware sensors.

[commits-shield]: https://img.shields.io/github/commit-activity/y/ace/virtual-weather-station.svg?style=for-the-badge
[commits]: https://github.com/ace/virtual-weather-station/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/ace/virtual-weather-station.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/ace/virtual-weather-station.svg?style=for-the-badge
[releases]: https://github.com/ace/virtual-weather-station/releases
[logo]: https://raw.githubusercontent.com/ace/virtual-weather-station/main/images/logo.png