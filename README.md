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
- **🌍 Multi-Unit Support**: Works seamlessly with both metric and imperial sensor units

This integration analyzes your real sensor data to provide weather conditions that truly represent what's happening at your exact location.

## Features

- 🌡️ **Smart Weather Detection**: Analyzes real sensor data to determine weather conditions
- 🧠 **Intelligent Algorithms**: Uses solar radiation, precipitation, wind, and pressure data
- 📊 **Individual Sensors**: Separate sensor entities for each weather parameter
- 🌦️ **Weather Entity**: Complete weather entity with current conditions and intelligent forecasts
- 📈 **Intelligent Forecasting**: 5-day daily and 24-hour hourly forecasts based on pressure trends
- ⚙️ **Flexible Configuration**: Works with any combination of available sensors
- 🔄 **Real-time Analysis**: Updates based on actual sensor readings
- 📱 **Easy Configuration**: Simple setup through Home Assistant UI with sensor selection
- 🌍 **Multilingual Support**: Available in English, Italian, German, Spanish, and French
- 🔄 **Multi-Unit Support**: Automatic detection and conversion between metric and imperial units

## Installation

### Method 1: HACS (Recommended)

HACS (Home Assistant Community Store) is the easiest way to install and manage custom integrations.

#### Prerequisites

- [HACS](https://hacs.xyz/) must be installed in your Home Assistant instance
- Home Assistant version 2023.1.0 or higher

#### Installation Steps

1. **Open HACS**: Go to HACS in your Home Assistant sidebar
2. **Navigate to Integrations**: Click on "Integrations"
3. **Add Custom Repository**:
   - Click the three dots menu (⋮) in the top right
   - Select "Custom repositories"
   - Add repository URL: `https://github.com/caplaz/micro-weather-station`
   - Set category to "Integration"
   - Click "Add"
4. **Install Integration**:
   - Search for "Micro Weather Station" in HACS
   - Click on it and select "Download"
   - Choose the latest version
5. **Restart Home Assistant**: Required for the integration to load

### Method 2: Manual Installation

For advanced users or custom setups.

#### Download Options

- **Latest Release**: Download from [GitHub Releases](https://github.com/caplaz/micro-weather-station/releases)
- **Development Version**: Clone the repository for latest features

#### Installation Steps

1. **Download Files**:

   ```bash
   # Option A: Download release
   wget https://github.com/caplaz/micro-weather-station/archive/refs/tags/v1.4.0.zip
   unzip v1.4.0.zip

   # Option B: Clone repository
   git clone https://github.com/caplaz/micro-weather-station.git
   ```

2. **Copy to Home Assistant**:

   ```bash
   # Copy the integration folder to your custom_components directory
   cp -r micro-weather-station/custom_components/micro_weather /config/custom_components/
   ```

3. **Verify Installation**:
   Your directory structure should look like:

   ```
   /config/custom_components/micro_weather/
   ├── __init__.py
   ├── config_flow.py
   ├── const.py
   ├── manifest.json
   ├── sensor.py
   ├── strings.json
   ├── version.py
   ├── weather_detector.py
   ├── weather.py
   └── translations/
       └── en.json
   ```

4. **Restart Home Assistant**: Go to Settings → System → Restart

### Method 3: Development/Testing Installation

For developers wanting to test or contribute.

#### Prerequisites

- Git installed
- Home Assistant development environment
- Python 3.11+ with virtual environment

#### Development Setup

1. **Clone Repository**:

   ```bash
   git clone https://github.com/caplaz/micro-weather-station.git
   cd micro-weather-station
   ```

2. **Create Symbolic Link** (preserves git history):

   ```bash
   # Link to your HA config directory
   ln -s $(pwd)/custom_components/micro_weather /config/custom_components/micro_weather
   ```

3. **Install Development Dependencies**:

   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Run Tests**:
   ```bash
   python -m pytest tests/
   ```

### Verification

After installation, verify the integration is loaded:

1. **Check Logs**: Go to Settings → System → Logs

   - Look for `micro_weather` entries
   - No errors should be present

2. **Integration Available**: Go to Settings → Devices & Services

   - Click "Add Integration"
   - Search for "Micro Weather Station"
   - It should appear in the list

3. **Version Check**: In Developer Tools → States, search for `sensor.micro_weather`
   - Entities should be available after configuration

## Configuration

### Step 1: Adding the Integration

1. **Navigate to Integrations**: Go to Settings → Devices & Services
2. **Add Integration**: Click "Add Integration" button
3. **Search**: Type "Micro Weather Station" in the search box
4. **Select**: Click on "Micro Weather Station" from the results

### Step 2: Sensor Configuration

The configuration flow will guide you through selecting your sensors:

#### Required Configuration

- **Outdoor Temperature**: Select your outdoor temperature sensor entity
- **Update Interval**: Set how often to check sensors (default: 5 minutes)

#### Optional Sensor Mapping

Configure additional sensors for enhanced weather detection:

| Configuration Field | Example Entity ID        | Purpose                                 |
| ------------------- | ------------------------ | --------------------------------------- |
| Dewpoint            | `sensor.dewpoint`        | Direct dewpoint measurement             |
| Humidity            | `sensor.humidity`        | Humidity readings and fog detection     |
| Pressure            | `sensor.pressure`        | Storm prediction and forecasting        |
| Wind Speed          | `sensor.wind_speed`      | Wind condition detection                |
| Wind Direction      | `sensor.wind_direction`  | Wind data and storm analysis            |
| Wind Gust           | `sensor.wind_gust`       | Storm and severe weather detection      |
| Rain Rate           | `sensor.rain_rate`       | Precipitation rate measurement          |
| Rain State          | `sensor.rain_detector`   | Precipitation state detection           |
| Solar Radiation     | `sensor.solar_radiation` | Cloud cover and solar analysis          |
| Solar Lux           | `sensor.light_sensor`    | Day/night and cloud detection           |
| UV Index            | `sensor.uv_index`        | Clear sky and sun intensity             |
| Sun Sensor          | `sensor.sun_elevation`   | Solar elevation for precise cloud cover |

### Unit Conversion Support

The integration automatically detects and converts between different sensor units:

- **Temperature**: °C ↔ °F (Celsius/Fahrenheit)
- **Pressure**: hPa/mbar ↔ inHg (hectopascals/inches of mercury)
- **Wind Speed**: km/h, mph, m/s (kilometers/hour, miles/hour, meters/second)

**Supported Sensors:**

- ✅ **Metric Weather Stations**: Full metric unit support (°C, hPa, km/h)
- ✅ **Imperial Weather Stations**: Imperial units (°F, inHg, mph)
- ✅ **Mixed Environments**: Any combination of metric and imperial sensors
- ✅ **SI Units**: Support for m/s wind speed sensors

The integration intelligently converts all sensor data to consistent internal units for accurate weather analysis, ensuring compatibility with both modern metric sensors and legacy imperial equipment.

### Step 3: Testing Your Configuration

#### Initial Verification

1. **Check Integration Status**:

   - Go to Settings → Devices & Services
   - Find "Micro Weather Station" integration
   - Should show status "Configured" with no errors

2. **Verify Entities Created**:

   - Go to Developer Tools → States
   - Search for `micro_weather`
   - Should see weather entity and sensor entities

3. **Test Weather Entity**:
   - Find `weather.micro_weather_station`
   - Check that it has a valid state (e.g., "sunny", "cloudy")
   - Verify attributes contain sensor data

#### Advanced Testing

1. **Sensor Data Validation**:

   ```yaml
   # Check in Developer Tools → States
   weather.micro_weather_station:
     state: sunny
     attributes:
       temperature: 22.5
       humidity: 65
       pressure: 1013.2
       wind_speed: 10.5
       wind_bearing: 180
       visibility: 10
   ```

2. **Weather Condition Testing**:

   - Change sensor values to test different conditions
   - Verify weather state updates accordingly
   - Test with different sensor combinations

3. **Forecast Validation**:
   - Check `forecast` attribute in weather entity
   - Verify daily and hourly forecasts are present
   - Test forecast updates over time

### Step 4: Dashboard Integration

#### Add Weather Card

1. **Edit Dashboard**: Go to your dashboard and click "Edit"
2. **Add Card**: Click "Add Card" → "Weather Forecast"
3. **Configure**: Select `weather.micro_weather_station`
4. **Save**: The weather card should display your data

#### Add Sensor Cards

```yaml
# Example sensor card configuration
type: entities
entities:
  - entity: sensor.micro_weather_station_temperature
    name: Temperature
    icon: mdi:thermometer
  - entity: sensor.micro_weather_station_humidity
    name: Humidity
    icon: mdi:water-percent
  - entity: sensor.micro_weather_station_pressure
    name: Pressure
    icon: mdi:gauge
title: Weather Sensors
```

### Step 5: Automation Testing

Create a test automation to verify the integration works:

```yaml
# Test automation
automation:
  - alias: "Test Weather Integration"
    trigger:
      - platform: state
        entity_id: weather.micro_weather_station
    action:
      - service: notify.persistent_notification
        data:
          message: >
            Weather changed to: {{ states('weather.micro_weather_station') }}
            Temperature: {{ state_attr('weather.micro_weather_station', 'temperature') }}°C
          title: "Weather Update"
```

### Required Sensors

| Sensor Type         | Description                   | Required        |
| ------------------- | ----------------------------- | --------------- |
| Outdoor Temperature | Temperature sensor (°F or °C) | ✅ **Required** |

### Optional Sensors

| Sensor Type     | Description                   | Used For                                               |
| --------------- | ----------------------------- | ------------------------------------------------------ |
| Dewpoint        | Dewpoint temperature sensor   | Direct dewpoint measurement for improved accuracy      |
| Humidity        | Humidity percentage sensor    | Humidity readings and fog detection                    |
| Pressure        | Atmospheric pressure sensor   | Storm detection and weather forecasting                |
| Wind Speed      | Wind speed sensor             | Wind conditions and storm detection                    |
| Wind Direction  | Wind direction sensor         | Wind data and storm tracking                           |
| Wind Gust       | Wind gust sensor              | Severe weather and storm detection                     |
| Rain Rate       | Precipitation rate sensor     | Precipitation intensity measurement                    |
| Rain State      | Rain state sensor (dry/wet)   | Boolean precipitation detection                        |
| Solar Radiation | Solar radiation sensor (W/m²) | Cloud cover detection and solar analysis               |
| Solar Lux       | Light level sensor (lx)       | Day/night and cloud detection (backup)                 |
| UV Index        | UV index sensor               | Clear sky detection and solar intensity                |
| Sun Sensor      | Solar elevation sensor        | Precise cloud cover calculations based on sun position |

### Example Sensor Configuration

```yaml
# Example sensor mappings for weather station:
Outdoor Temperature: sensor.outdoor_temperature # Required - base temperature readings
Dewpoint: sensor.dewpoint # Optional - direct dewpoint measurement
Humidity: sensor.indoor_humidity # Optional - fog detection, comfort calculations
Pressure: sensor.relative_pressure # Optional - storm prediction, forecasting
Wind Speed: sensor.wind_speed # Optional - wind conditions, storm detection
Wind Direction: sensor.wind_direction # Optional - wind patterns, storm tracking
Wind Gust: sensor.wind_gust # Optional - severe weather detection
Rain Rate: sensor.rain_rate_piezo # Optional - precipitation intensity
Rain State: sensor.rain_state_piezo # Optional - binary moisture/precipitation sensor (reports "wet" or "dry")
Solar Radiation: sensor.solar_radiation # Optional - cloud cover analysis
Solar Lux: sensor.solar_lux # Optional - day/night detection backup
UV Index: sensor.uv_index # Optional - clear sky confirmation
Sun Sensor: sensor.sun_elevation # Optional - solar elevation for precise cloud cover calculations
```

**Note**: Indoor temperature sensor has been removed. This integration focuses on outdoor weather conditions using only outdoor environmental sensors.

## Entities Created

### Weather Entity

- `weather.micro_weather_station` - Main weather entity with current conditions and forecast

This integration creates only the weather entity to avoid duplicating your existing sensor entities. All weather data is displayed through the main weather entity, which references your configured sensors directly.

## Enhanced Dewpoint Support

The integration now supports direct dewpoint sensors for improved accuracy:

- **Direct Dewpoint**: If you have a dewpoint sensor, it will be used directly for maximum accuracy
- **Calculated Dewpoint**: If no dewpoint sensor is available, it will be calculated from temperature and humidity using the Magnus formula
- **Improved Fog Detection**: Better fog detection using conservative humidity thresholds (>98%) combined with dewpoint analysis and solar radiation data
- **Fallback Mechanism**: Seamlessly falls back to calculated dewpoint when direct sensor unavailable

## Weather Detection Logic

The integration intelligently detects weather conditions using your real sensor data with the following priority system:

| Condition        | Detection Criteria                                   | Priority    |
| ---------------- | ---------------------------------------------------- | ----------- |
| ⛈️ Stormy        | Rain + High Wind (>25 km/h)                          | 1 (Highest) |
| 🌧️ Rainy         | Active precipitation detected                        | 2           |
| ❄️ Snowy         | Rain + Low temperature (<2°C)                        | 3           |
| 🌫️ Foggy         | High humidity (>98%) + Dewpoint analysis + Low solar | 4           |
| ☀️ Sunny         | High solar radiation (>400 W/m²) or High UV index    | 5           |
| ⛅ Partly Cloudy | Medium solar radiation (100-400 W/m²)                | 6           |
| ☁️ Cloudy        | Low solar radiation (<100 W/m²) or Default condition | 7 (Default) |

The algorithm analyzes your sensor readings in real-time to provide accurate weather condition detection:

**Enhanced Detection Features:**

- **Dewpoint Integration**: Uses direct dewpoint sensors when available, calculates from temperature/humidity as fallback
- **Scientific Fog Detection**: Combines humidity thresholds with dewpoint analysis and solar radiation for accurate fog detection
- **Multi-sensor Validation**: Cross-references multiple sensors for improved accuracy
- **Intelligent Fallbacks**: Seamlessly switches between sensor types when data unavailable

## Intelligent Forecasting

The integration provides both daily and hourly forecasts based on your sensor data:

### Daily Forecast (5 days)

- **Temperature Trends**: Based on pressure patterns and seasonal variations
- **Condition Prediction**: Uses pressure trends, humidity, and wind patterns
- **Precipitation Probability**: Calculated from atmospheric pressure and humidity levels
- **Wind Speed Forecasting**: Considers current conditions and weather pattern changes

### Hourly Forecast (24 hours)

- **Diurnal Temperature Cycle**: Natural daily temperature variations
- **Short-term Condition Changes**: Hour-by-hour weather evolution
- **Microclimate Patterns**: Based on your local sensor data trends

### Forecast Features

- **Pressure-based Prediction**: High pressure → clear weather, Low pressure → storms
- **Humidity Analysis**: High humidity + low pressure = increased rain probability
- **Wind Pattern Recognition**: Current wind trends influence forecast conditions
- **Local Calibration**: Adapts to your specific microclimate over time

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

## Lovelace Cards

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

### Common Installation Issues

#### Integration Not Found

**Problem**: "Micro Weather Station" doesn't appear when adding integrations.

**Solutions**:

1. **Verify Installation**:
   ```bash
   # Check if files exist
   ls -la /config/custom_components/micro_weather/
   ```
2. **Check Logs**: Settings → System → Logs, search for `micro_weather`
3. **Restart Required**: Restart Home Assistant after installation
4. **Clear Browser Cache**: Hard refresh (Ctrl+F5) or clear cache

#### Integration Loading Errors

**Problem**: Integration loads but shows errors in logs.

**Solutions**:

1. **Check Python Version**: Requires Python 3.11+
2. **Verify Dependencies**: All sensors should exist in HA
3. **Review Manifest**: Check `custom_components/micro_weather/manifest.json`
4. **File Permissions**: Ensure files are readable by HA user

### Configuration Issues

#### No Sensors Available

**Problem**: Dropdown menus are empty during configuration.

**Solutions**:

1. **Verify Sensor Entities**:
   - Go to Developer Tools → States
   - Search for your temperature sensors
   - Entity IDs must match exactly
2. **Check Sensor Types**:
   ```yaml
   # Valid temperature sensors should have device_class
   sensor.outdoor_temp:
     device_class: temperature
     unit_of_measurement: "°C" # or "°F"
   ```
3. **Sensor States**: Ensure sensors have valid numeric values

#### Weather Conditions Not Updating

**Problem**: Weather entity stuck on one condition.

**Diagnostic Steps**:

1. **Check Sensor Values**:

   ```bash
   # In Developer Tools → States, verify:
   sensor.outdoor_temperature: 22.5  # Valid number
   sensor.humidity: 65              # 0-100 range
   sensor.pressure: 1013.2          # Valid pressure
   ```

2. **Review Detection Logic**:

   - High solar radiation (>400 W/m²) = Sunny
   - Active rain sensor = Rainy
   - Low solar + high humidity = Foggy
   - Default = Cloudy

3. **Check Update Interval**: Verify sensors update within configured interval

#### Rain Detection Issues

**Problem**: Incorrect precipitation or fog detection.

**Common Causes & Solutions**:

1. **Invalid Rain State Values**:

   ```yaml
   # ❌ WRONG - These values don't work with moisture sensors:
   sensor.rain_state: "rain", "drizzle", "precipitation"

   # ✅ CORRECT - Binary moisture sensors only report:
   sensor.rain_state: "wet" or "dry"
   ```

2. **Fog vs Precipitation**:

   - Fog can make moisture sensors read "wet" without actual precipitation
   - The integration automatically distinguishes between fog moisture and rain
   - Check humidity (>95%) and dewpoint spread (<3°F) for fog conditions

3. **Rain Rate Sensitivity**:
   - Very light rain rates (<0.01 in/hr) may not trigger precipitation detection
   - This prevents false alerts from dew or light fog moisture
   - Increase rain gauge sensitivity if needed

### Testing and Validation

#### Manual Testing Steps

1. **Basic Functionality Test**:

   ```yaml
   # Developer Tools → Services
   service: homeassistant.update_entity
   target:
     entity_id: weather.micro_weather_station
   ```

2. **Sensor Response Test**:

   - Manually change a sensor value (if possible)
   - Wait for update interval
   - Check if weather condition changes

3. **Forecast Test**:
   ```python
   # Check forecast data exists
   forecast = state_attr('weather.micro_weather_station', 'forecast')
   # Should return list of forecast periods
   ```

#### Log Analysis

**Enable Debug Logging**:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.micro_weather: debug
```

**Key Log Messages**:

- `Setting up micro_weather` - Integration loading
- `Weather condition detected` - Condition changes
- `Sensor updated` - Individual sensor updates
- `Forecast generated` - Forecast calculations

#### Performance Monitoring

1. **Resource Usage**:

   - Monitor CPU usage during updates
   - Check memory consumption
   - Verify update frequency is appropriate

2. **Sensor Health**:
   ```yaml
   # Create automation to monitor sensor availability
   automation:
     - alias: "Weather Sensor Health Check"
       trigger:
         - platform: state
           entity_id: sensor.outdoor_temperature
           to: "unavailable"
       action:
         - service: notify.persistent_notification
           data:
             message: "Weather sensor offline: outdoor temperature"
   ```

### Advanced Debugging

#### Integration Reload

```yaml
# Developer Tools → Services
service: homeassistant.reload_config_entry
target:
  entity_id: weather.micro_weather_station
```

#### Custom Component Debugging

1. **Check Integration Registry**:

   - Settings → Devices & Services
   - Find "Micro Weather Station"
   - Click "Configure" to verify settings

2. **Entity Registry Verification**:

   - Developer Tools → States
   - All micro_weather entities should be present
   - Check entity attributes for data consistency

3. **Component State Machine**:
   ```python
   # Verify entity states in Developer Tools
   weather.micro_weather_station:
     state: "sunny"  # Valid weather condition
     attributes:
       temperature: float  # Numeric value
       humidity: float     # 0-100 range
       forecast: list      # Array of forecast data
   ```

### Getting Help

#### Information to Provide

When reporting issues, include:

1. **Home Assistant Version**: Settings → About
2. **Integration Version**: Check HACS or git tag
3. **Sensor Configuration**: List of configured sensors
4. **Error Logs**: Full error messages from logs
5. **Sensor States**: Current values of configured sensors

#### Useful Commands

```bash
# Check HA logs for errors
grep -i "micro_weather" /config/home-assistant.log

# Verify file integrity
find /config/custom_components/micro_weather -name "*.py" -exec python -m py_compile {} \;

# Check sensor availability
ha-cli state list | grep temperature
```

#### Support Channels

- 🐛 [GitHub Issues](https://github.com/caplaz/micro-weather-station/issues) - Bug reports and feature requests
- 💬 [Home Assistant Community](https://community.home-assistant.io/) - General questions and discussions
- 📚 [Documentation](https://github.com/caplaz/micro-weather-station#readme) - Complete setup guide

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

### v1.4.0

- **Complete Unit Conversion Support**: Full support for both metric and imperial sensor units
  - Automatic detection and conversion of temperature (°C/°F), pressure (hPa/inHg), and wind speed (km/h/mph/m/s)
  - Smart unit-aware conversion methods that preserve accuracy across different sensor types
  - Backward compatibility with existing imperial sensor setups
- **Enhanced Analysis Methods**: All meteorological analysis functions now receive consistent imperial units
  - Added `_prepare_analysis_sensor_data()` method for converting metric sensor data to imperial units
  - Updated historical data storage to use imperial units for consistent trend analysis
  - Improved accuracy of weather condition detection with mixed sensor units
- **Intelligent Forecast Wind Calculation**: Fixed forecast wind speeds to use actual sensor readings
  - Replaced condition-based fixed wind values with current wind speed as base
  - Applied realistic condition-based adjustments as multipliers (not absolute values)
  - Provides accurate forecast wind speeds that reflect real sensor data
- **Comprehensive Test Coverage**: Added extensive unit conversion tests (40+ new tests)
  - Tests for all unit conversion scenarios (metric, imperial, mixed)
  - Forecast preparation and analysis preparation validation
  - Integration tests ensuring end-to-end functionality with different sensor units

### v1.3.3

- **Nighttime Weather Detection**: Fixed false cloudy detection on clear nights with low pressure
  - Improved nighttime condition logic to consider humidity levels alongside pressure
  - Low pressure (< 29.80 inHg) no longer automatically triggers cloudy conditions
  - Added nuanced conditions: clear-night for low pressure + low humidity (< 65%), cloudy for high humidity (> 85%)
  - Fixes issue where clear nights were incorrectly reported as cloudy due to atmospheric pressure alone
  - Applied consistent logic to both weather_detector.py and weather_analysis.py

### v1.3.2

- **Bug Fixes**: Fixed logging syntax errors showing literal `{entity_id}` instead of actual values
- **Sensor Validation**: Added validation for None/empty sensor states to prevent conversion warnings
- **Improved Error Handling**: Enhanced sensor state validation in weather detection logic

### v1.3.1

- **Solar Radiation Averaging**: Implemented 15-minute moving average for solar radiation readings to prevent rapid weather condition changes
- Enhanced HACS validation workflow with scheduled runs and manual dispatch
- Added hassfest integration validation for improved Home Assistant compatibility
- Updated CI/CD pipeline for better automated testing and validation

### v1.3.0

- **Solar Elevation Integration**: Added sun sensor support for precise cloud cover calculations based on solar position

### v1.2.0

- **Fixed Rain State Logic**: Corrected moisture sensor handling to only recognize "wet" or "dry" states
- **Enhanced Fog Detection**: Improved fog vs precipitation detection when moisture sensor shows "wet"
- **Smart Moisture Analysis**: Added intelligent logic to distinguish between precipitation and fog moisture
- **Improved Accuracy**: Better weather condition detection in ambiguous moisture scenarios

### v1.1.0

- **Major Code Refactoring**: Split monolithic weather_detector.py (~1300 lines) into focused, maintainable modules
- **Modular Architecture**: Improved code organization with separate concerns:
  - `weather_utils.py`: Unit conversion functions (Celsius, hPa, km/h)
  - `weather_analysis.py`: Meteorological algorithms and trend analysis
  - `weather_forecast.py`: Advanced forecasting with historical patterns
  - `weather_detector.py`: Core integration and orchestration (refactored)
- **Enhanced Test Coverage**: Comprehensive test suites for each module (64 total tests)
- **Improved Maintainability**: Better separation of concerns and code reusability
- **Future-Ready Architecture**: Easier to extend with new features and algorithms

### v1.0.0

- Initial release
- Weather entity with intelligent condition detection
- Individual sensor entities for all weather parameters
- Configurable sensor mapping and detection thresholds
- Support for multiple weather condition types
- HACS compatibility

---

**Note**: This smart weather station uses your existing sensor data to intelligently detect weather conditions. Configure your sensors during setup to get accurate weather detection based on your local environment.

[commits-shield]: https://img.shields.io/github/commit-activity/y/caplaz/micro-weather-station.svg?style=for-the-badge&v=1.4.0
[commits]: https://github.com/caplaz/micro-weather-station/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/caplaz/micro-weather-station.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/caplaz/micro-weather-station.svg?style=for-the-badge&v=1.4.0
[releases]: https://github.com/caplaz/micro-weather-station/releases
[logo]: https://raw.githubusercontent.com/caplaz/micro-weather-station/main/images/logo.png
