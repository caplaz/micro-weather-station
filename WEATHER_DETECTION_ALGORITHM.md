# Weather Detection Algorithm

This document explains how the Micro Weather Station determines weather conditions from your real sensor data.

## Your Available Sensors

Based on your sensor list, here's how each sensor is used in weather detection:

### Primary Sensors for Weather Detection

1. **Outdoor Temperature** (59.9 °F) - Primary temperature source
2. **Rain Rate Piezo** (0.0 in/h) - Precipitation detection
3. **Rain State Piezo** (Dry) - Current precipitation state
4. **Solar Radiation** (0 W/m²) - Cloud cover and daylight conditions
5. **Solar Lux** (0.0 lx) - Light levels for cloud detection
6. **Wind Speed** (5.8 mph) - Wind conditions
7. **Wind Gust** (13.9 mph) - Storm detection
8. **Relative Pressure** (29.22 inHg) - Atmospheric pressure

### Supporting Sensors

- **Indoor Temperature** (72.3 °F) - Temperature differential
- **Indoor Humidity** (66%) - Humidity levels
- **UV Index** (0 UV index) - Clear sky indicator
- **Wind Direction** (233°) - Wind data
- **Indoor Dewpoint** (60.3 °F) - Humidity calculations

## Weather Condition Detection Logic

### Priority-Based Detection

The algorithm uses a priority system to determine weather conditions:

#### 1. **Rain Conditions** (Highest Priority)

```
IF rain_rate > 0.1 in/h OR rain_state != "Dry":
    IF wind_gust > 25 mph OR pressure < 29.80 inHg:
        → "stormy" (Heavy rain with wind or low pressure)
    ELIF outdoor_temp < 35°F:
        → "snowy" (Cold precipitation)
    ELSE:
        → "rainy" (Regular rain)
```

#### 2. **Wind-Based Storm Detection**

```
IF wind_gust > 30 mph OR (wind_speed > 20 mph AND pressure < 29.80 inHg):
    → "stormy"
```

#### 3. **Solar Radiation Based Conditions** (Daytime)

```
IF solar_radiation > 0 OR solar_lux > 0 OR uv_index > 0:  # Daytime detection
    IF solar_radiation > 300 W/m²:
        → "sunny" (High solar radiation)
    ELIF solar_radiation > 100 W/m²:
        → "partly_cloudy" (Moderate solar radiation)
    ELIF solar_radiation > 10 W/m²:
        → "cloudy" (Low solar radiation)
    ELSE:
        IF solar_lux < 1000 lx:
            → "foggy" (Very low visibility)
        ELSE:
            → "cloudy"
```

#### 4. **Nighttime Conditions**

```
IF solar_radiation = 0 AND solar_lux = 0 AND uv_index = 0:  # Nighttime
    IF wind_speed < 5 mph AND pressure >= 29.80 inHg:
        → "cloudy" (Calm night)
    ELSE:
        → "partly_cloudy"
```

## Current Reading Analysis

Based on your current sensor readings:

- **Solar Radiation**: 0 W/m² (no solar input - nighttime)
- **Solar Lux**: 0.0 lx (dark - nighttime)
- **UV Index**: 0 (no UV - nighttime)
- **Rain State**: Dry (no precipitation)
- **Rain Rate**: 0.0 in/h (no precipitation)
- **Wind Speed**: 5.8 mph (light winds)
- **Wind Gust**: 13.9 mph (moderate gusts)
- **Pressure**: 29.22 inHg (normal pressure)

**Predicted Condition**: `partly_cloudy` or `cloudy`

- It's nighttime (all solar sensors = 0)
- No precipitation
- Light winds (5.8 mph)
- Normal pressure (29.22 inHg)

## Visibility Estimation

Visibility is estimated based on weather conditions and sensor data:

- **Foggy**: 0.5-5 km (based on solar_lux/10000)
- **Rainy/Snowy**: 2-8 km (reduced by rain_rate)
- **Stormy**: 1-5 km (reduced by wind_gust)
- **Nighttime**: 15 km (standard night visibility)
- **Clear Day**: 15-25 km (based on solar_lux levels)

## Unit Conversions

The integration automatically converts between units:

- **Temperature**: Fahrenheit → Celsius: `(°F - 32) × 5/9`
- **Pressure**: inHg → hPa: `inHg × 33.8639`
- **Wind Speed**: mph → km/h: `mph × 1.60934`

## Forecast Generation

A simple 5-day forecast is generated based on:

- Current conditions with slight variations
- Temperature trends with ±2°C daily changes
- Weather pattern persistence with gradual changes

## Example Sensor Mappings

For your specific sensors, you would configure:

```yaml
Outdoor Temperature Sensor: sensor.outdoor_temperature
Indoor Temperature Sensor: sensor.indoor_temperature
Humidity Sensor: sensor.indoor_humidity
Pressure Sensor: sensor.relative_pressure
Wind Speed Sensor: sensor.wind_speed
Wind Direction Sensor: sensor.wind_direction
Wind Gust Sensor: sensor.wind_gust
Rain Rate Sensor: sensor.rain_rate_piezo
Rain State Sensor: sensor.rain_state_piezo
Solar Radiation Sensor: sensor.solar_radiation
Solar Lux Sensor: sensor.solar_lux
UV Index Sensor: sensor.uv_index
```

## Weather Condition Mapping

The integration maps conditions to Home Assistant weather states:

- `sunny` → Clear
- `cloudy` → Cloudy
- `partly_cloudy` → Partly Cloudy
- `rainy` → Rainy
- `snowy` → Snowy
- `stormy` → Lightning Rainy
- `foggy` → Fog

This algorithm provides realistic weather condition detection based on your actual sensor data, creating a much more accurate representation than simulated data.
