# Installation Guide - Micro Weather Station

This guide provides detailed step-by-step instructions for installing and configuring the Micro Weather Station integration in Home Assistant.

## Prerequisites

Before starting, ensure you have:

- Home Assistant 2025.9.4 or higher
- Admin access to Home Assistant
- At least one outdoor temperature sensor configured
- Basic understanding of Home Assistant entities

## Installation Methods

### Method 1: HACS Installation (Recommended)

HACS (Home Assistant Community Store) is the easiest and most reliable way to install custom integrations.

#### Step 1: Install HACS (if not already installed)

1. Follow the [HACS installation guide](https://hacs.xyz/docs/setup/download)
2. Restart Home Assistant
3. Configure HACS through the integration setup

#### Step 2: Add Custom Repository

1. **Open HACS**:

   - Go to your Home Assistant sidebar
   - Click on "HACS"

2. **Navigate to Integrations**:

   - Click on "Integrations" tab
   - This shows all available integrations

3. **Add Custom Repository**:

   - Click the three dots menu (⋮) in the top right corner
   - Select "Custom repositories"
   - A dialog will open

4. **Configure Repository**:

   - **Repository URL**: `https://github.com/caplaz/micro-weather-station`
   - **Category**: Select "Integration" from dropdown
   - Click "Add"

5. **Verify Addition**:
   - The repository should appear in your custom repositories list
   - You'll see a success message

#### Step 3: Install the Integration

1. **Search for Integration**:

   - In HACS Integrations, use the search box
   - Type "Micro Weather Station"
   - Click on the integration when it appears

2. **Download Integration**:

   - Click "Download" button
   - Select "Download" in the confirmation dialog
   - Choose the latest version (recommended)

3. **Installation Complete**:
   - You'll see a success message
   - The integration files are now downloaded

#### Step 4: Restart Home Assistant

1. **Navigate to Settings**:
   - Go to Settings → System → Restart
   - Click "Restart Home Assistant"
   - Wait for restart to complete (usually 1-2 minutes)

#### Step 5: Verify Installation

1. **Check Integration Availability**:
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Micro Weather Station"
   - It should appear in the search results

### Method 2: Manual Installation

For users who prefer manual installation or don't use HACS.

#### Step 1: Download Files

Choose one of these options:

**Option A: Download Release (Stable)**

1. Go to [GitHub Releases](https://github.com/caplaz/micro-weather-station/releases)
2. Download the latest release ZIP file
3. Extract the ZIP file on your computer

**Option B: Download Source (Latest)**

1. Go to the [GitHub repository](https://github.com/caplaz/micro-weather-station)
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file on your computer

**Option C: Git Clone (Advanced)**

```bash
git clone https://github.com/caplaz/micro-weather-station.git
cd micro-weather-station
```

#### Step 2: Locate Your Home Assistant Configuration

Find your Home Assistant configuration directory:

**Common Locations:**

- **Home Assistant OS**: `/config/`
- **Home Assistant Container**: Your mapped config volume
- **Home Assistant Core**: Usually `~/.homeassistant/`
- **Home Assistant Supervised**: `/usr/share/hassio/homeassistant/`

#### Step 3: Create Custom Components Directory

If it doesn't exist, create the custom_components directory:

```bash
# Navigate to your config directory
cd /config

# Create custom_components directory (if it doesn't exist)
mkdir -p custom_components
```

#### Step 4: Copy Integration Files

Copy the micro_weather folder to your custom_components directory:

```bash
# From the downloaded/extracted files
cp -r custom_components/micro_weather /config/custom_components/

# Verify the structure
ls -la /config/custom_components/micro_weather/
```

**Expected Directory Structure:**

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

#### Step 5: Set Permissions (Linux/Docker)

Ensure Home Assistant can read the files:

```bash
# For Docker/supervised installations
chown -R homeassistant:homeassistant /config/custom_components/micro_weather/

# For other installations, ensure files are readable
chmod -R 644 /config/custom_components/micro_weather/
chmod 755 /config/custom_components/micro_weather/
```

#### Step 6: Restart Home Assistant

Restart Home Assistant to load the new integration:

- Settings → System → Restart
- Wait for restart to complete

## Configuration Setup

### Step 1: Add the Integration

1. **Navigate to Integrations**:

   - Go to Settings → Devices & Services
   - Click "Add Integration" (blue button with + icon)

2. **Search and Select**:
   - Type "Micro Weather Station" in the search box
   - Click on "Micro Weather Station" when it appears
   - If it doesn't appear, check the troubleshooting section

### Step 2: Basic Configuration

The configuration flow will guide you through the setup:

#### Required Settings

1. **Outdoor Temperature Sensor**:

   - Select your outdoor temperature sensor from the dropdown
   - This is the only required sensor
   - Must be a sensor with temperature device class

2. **Update Interval**:
   - Set how often the integration updates (default: 5 minutes)
   - Range: 1-60 minutes
   - Consider your sensor update frequency

#### Example Configuration

```yaml
# Configuration values you'll set:
Outdoor Temperature: sensor.outdoor_temperature_sensor
Update Interval: 5 # minutes
```

### Step 3: Optional Sensor Configuration

Enhance weather detection by configuring additional sensors:

#### Available Optional Sensors

| Sensor Type        | Purpose                                 | Example Entity                |
| ------------------ | --------------------------------------- | ----------------------------- |
| Indoor Temperature | Temperature differential analysis       | `sensor.indoor_temperature`   |
| Humidity           | Humidity readings and fog detection     | `sensor.humidity_sensor`      |
| Pressure           | Storm prediction and forecasting        | `sensor.barometric_pressure`  |
| Wind Speed         | Wind condition detection                | `sensor.wind_speed`           |
| Wind Direction     | Wind data analysis                      | `sensor.wind_direction`       |
| Wind Gust          | Storm detection                         | `sensor.wind_gust_speed`      |
| Rain Rate          | Precipitation measurement               | `sensor.rain_rate_per_hour`   |
| Rain State         | Rain detection                          | `sensor.rain_detector_state`  |
| Solar Radiation    | Cloud cover analysis                    | `sensor.solar_radiation_wm2`  |
| Solar Lux          | Light level detection                   | `sensor.outdoor_light_sensor` |
| UV Index           | Clear sky detection                     | `sensor.uv_index_sensor`      |
| Sun Sensor         | Solar elevation for precise cloud cover | `sensor.sun_elevation`        |

#### Configuration Tips

- **Leave blank** sensors you don't have
- **Entity IDs must match exactly** - use Developer Tools → States to verify
- **Sensor values** should be numeric and update regularly
- **Units don't matter** - the integration handles conversion

### Step 4: Complete Setup

1. **Submit Configuration**:

   - Click "Submit" after configuring sensors
   - The integration will validate your settings

2. **Success Confirmation**:
   - You should see a success message
   - The integration appears in your Devices & Services list

## Post-Installation Verification

### Step 1: Check Integration Status

1. **Verify Integration**:

   - Go to Settings → Devices & Services
   - Look for "Micro Weather Station"
   - Status should be "Configured" with device count

2. **Check for Errors**:
   - Click on the integration name
   - Look for any error messages
   - All entities should be available

### Step 2: Verify Entities Created

1. **Go to Developer Tools**:

   - Settings → Developer Tools → States
   - Search for "micro_weather"

2. **Expected Entities**:

   ```yaml
   # Main weather entity
   weather.micro_weather_station

   # Individual sensor entities
   sensor.micro_weather_station_temperature
   sensor.micro_weather_station_humidity
   sensor.micro_weather_station_pressure
   sensor.micro_weather_station_wind_speed
   sensor.micro_weather_station_wind_direction
   sensor.micro_weather_station_visibility
   ```

3. **Check Entity States**:
   - Each entity should have a valid state
   - Weather entity should show current condition
   - Sensor entities should show current values

### Step 3: Test Weather Detection

1. **Check Weather State**:

   ```yaml
   # In Developer Tools → States
   weather.micro_weather_station:
     state: "sunny" # or cloudy, rainy, etc.
     attributes:
       temperature: 22.5
       humidity: 65
       pressure: 1013.2
       wind_speed: 10.5
       wind_bearing: 180
       visibility: 10
       forecast: [...] # Array of forecast data
   ```

2. **Verify Weather Logic**:
   - Check that weather conditions match your sensor readings
   - High solar radiation should show "sunny"
   - Active rain sensor should show "rainy"
   - Low solar + high humidity should show "foggy"

## Dashboard Integration

### Step 1: Add Weather Card

1. **Edit Dashboard**:

   - Go to your main dashboard
   - Click "Edit Dashboard" (pencil icon)

2. **Add Weather Card**:

   - Click "Add Card"
   - Search for "Weather Forecast"
   - Select the weather forecast card

3. **Configure Card**:
   - Entity: `weather.micro_weather_station`
   - Click "Save"

### Step 2: Add Sensor Cards

Add individual sensor monitoring:

```yaml
# Sensor entities card
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
  - entity: sensor.micro_weather_station_wind_speed
    name: Wind Speed
    icon: mdi:weather-windy
title: Weather Sensors
show_header_toggle: false
```

## Testing and Validation

### Basic Functionality Test

1. **Manual Update Test**:

   ```yaml
   # Developer Tools → Services
   service: homeassistant.update_entity
   target:
     entity_id: weather.micro_weather_station
   ```

2. **Sensor Response Test**:
   - Change a sensor value (if possible)
   - Wait for the update interval
   - Check if weather condition updates

### Create Test Automation

```yaml
# Test automation to verify integration works
automation:
  - alias: "Weather Integration Test"
    trigger:
      - platform: state
        entity_id: weather.micro_weather_station
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state != trigger.from_state.state }}"
    action:
      - service: notify.persistent_notification
        data:
          title: "Weather Update Test"
          message: >
            Weather condition changed from {{ trigger.from_state.state }}
            to {{ trigger.to_state.state }} at {{ now().strftime('%H:%M') }}
```

## Maintenance and Updates

### HACS Updates

1. **Check for Updates**:

   - HACS will notify you of available updates
   - Go to HACS → Integrations
   - Look for update notifications

2. **Update Process**:
   - Click "Update" when available
   - Restart Home Assistant after update

### Manual Updates

1. **Download New Version**:

   - Follow the same manual installation steps
   - Replace existing files

2. **Restart Home Assistant**:
   - Always restart after manual updates

## Next Steps

After successful installation:

1. **Explore Automations**: Create weather-based automations
2. **Monitor Performance**: Check logs and entity updates
3. **Customize Dashboard**: Add weather charts and additional cards
4. **Join Community**: Participate in discussions and provide feedback

## Getting Help

If you encounter issues:

1. **Check Logs**: Settings → System → Logs
2. **Review Entity States**: Developer Tools → States
3. **Verify Sensor Data**: Ensure your sensors are working
4. **Search Issues**: Check [GitHub Issues](https://github.com/caplaz/micro-weather-station/issues)
5. **Ask for Help**: [Home Assistant Community](https://community.home-assistant.io/)

---

**Congratulations!** Your Micro Weather Station integration is now installed and ready to provide intelligent weather detection based on your actual sensor data.
