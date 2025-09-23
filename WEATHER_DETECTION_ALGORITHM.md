# Weather Detection Algorithm

This document explains how the Micro Weather Station determines weather conditions from your real sensor data.

## Algorithm Overview

The weather detection system uses a sophisticated priority-based algorithm with meteorological principles to analyze sensor data and determine accurate weather conditions.

### Key Improvements (v1.2.0)

- **Enhanced Rain Detection**: Fixed rain_state logic to properly handle binary moisture sensors ("wet"/"dry" only)
- **Smart Fog Detection**: Distinguishes between fog moisture and precipitation when sensor shows "wet"
- **Advanced Pressure Analysis**: Uses meteorologically accurate pressure thresholds
- **Improved Daytime Detection**: Multi-sensor approach for accurate day/night/twilight detection

### Key Improvements (v1.3.3)

- **Nighttime Weather Detection**: Fixed false cloudy detection on clear nights with low pressure
  - Improved nighttime condition logic to consider humidity levels alongside pressure
  - Low pressure (< 29.80 inHg) no longer automatically triggers cloudy conditions
  - Added nuanced conditions: clear-night for low pressure + low humidity (< 65%), cloudy for high humidity (> 85%)
  - Fixes issue where clear nights were incorrectly reported as cloudy due to atmospheric pressure alone

### Key Improvements (v1.3.2)

- **Bug Fixes**: Fixed logging syntax errors showing literal `{entity_id}` instead of actual values
- **Sensor Validation**: Added validation for None/empty sensor states to prevent conversion warnings
- **Improved Error Handling**: Enhanced sensor state validation in weather detection logic

### Key Improvements (v1.3.1)

- **Solar Radiation Averaging**: Implemented 15-minute moving average for solar radiation readings to prevent rapid weather condition changes
- **Stable Cloud Detection**: Reduces false weather transitions caused by temporary cloud shadows or sensor noise
- **Enhanced Weather Stability**: Provides more reliable and consistent weather condition reporting
- **Solar Elevation Integration**: Added sun sensor support for precise cloud cover calculations based on solar position

## Weather Condition Detection Logic

### Priority-Based Detection System

The algorithm uses a comprehensive 6-priority system:

#### Priority 1: Active Precipitation (Highest Priority)

**Smart Moisture Analysis:**

```
Weather Analysis Module:
IF rain_rate > 0.01 in/h (significant precipitation):
    → Proceed to precipitation classification

Weather Detector Module:
IF rain_rate > 0.05 in/h (conservative threshold to avoid dew detection):
    → Proceed to precipitation classification

ELIF rain_state = "wet" AND rain_rate ≤ threshold:
    → Check for fog conditions first
    IF fog conditions detected (humidity ≥98%, dewpoint_spread ≤2°F, wind ≤3mph):
        → "foggy"
    ELSE:
        → Proceed to precipitation classification
```

**Note**: The system uses two different rain rate thresholds:

- **0.01 in/h** in weather_analysis.py (more sensitive)
- **0.05 in/h** in weather_detector.py (more conservative to avoid false positives from dew)

**Precipitation Classification:**

```
IF outdoor_temp ≤ 32°F:
    → "snowy" (any precipitation at freezing temps)
ELIF pressure < 29.20 inHg OR wind_gust ≥ 32mph:
    → "stormy" (severe weather conditions)
ELIF rain_rate ≥ 0.25 in/h:
    → "rainy" (heavy rain)
ELIF rain_rate ≥ 0.1 in/h:
    → "rainy" (moderate rain)
ELSE:
    → "rainy" (light rain/drizzle)
```

#### Priority 2: Severe Weather Conditions

```
IF pressure < 29.20 inHg AND (wind_speed ≥19mph OR wind_gust >15mph with gust_factor >2.0):
    → "stormy" (severe weather system)
IF wind_speed ≥ 32mph:
    → "stormy" (gale force winds)
```

#### Priority 3: Fog Conditions (Critical for Safety)

**Advanced Fog Analysis (when rain_state ≠ "wet"):**

```
Dense Fog: humidity ≥99% AND dewpoint_spread ≤1°F AND wind ≤2mph
Radiation Fog: humidity ≥98% AND dewpoint_spread ≤2°F AND wind ≤3mph AND (nighttime OR solar <5 W/m²)
Advection Fog: humidity ≥95% AND dewpoint_spread ≤3°F AND 3mph ≤ wind ≤12mph
Evaporation Fog: humidity ≥95% AND dewpoint_spread ≤3°F AND wind ≤6mph AND temp >40°F
```

#### Priority 4: Daytime Conditions

**Daytime Detection:** `solar_radiation > 5 W/m² OR solar_lux > 50 lx OR uv_index > 0.1`

**Cloud Cover Analysis:**

```
IF cloud_cover ≤10% AND pressure >30.00 inHg:
    → "sunny"
ELIF cloud_cover ≤25%:
    → "sunny"
ELIF cloud_cover ≤50%:
    → "partly_cloudy"
ELIF cloud_cover ≤75%:
    → "cloudy"
ELSE:
    → "cloudy" (overcast)
```

**Solar Elevation Enhancement:** When sun sensor is configured, cloud cover calculations are adjusted based on solar elevation angle, providing more accurate daytime weather detection throughout the day.

#### Priority 5: Twilight Conditions

**Twilight Detection:** `(10 lx < solar_lux < 100 lx) OR (1 W/m² < solar_radiation < 50 W/m²)`

```
IF solar_lux > 50 lx AND pressure normal:
    → "partly_cloudy"
ELSE:
    → "cloudy"
```

#### Priority 6: Nighttime Conditions

**Nighttime Detection:** All solar sensors ≤ threshold values

```
IF pressure >30.20 inHg AND wind <1mph AND humidity <70%:
    → "clear-night" (perfect clear night)
ELIF pressure >30.00 inHg AND not gusty AND humidity <80%:
    → "clear-night" (clear night)
ELIF pressure normal AND 1mph ≤ wind <8mph:
    → "partly_cloudy" (partly cloudy night)
ELIF humidity >85%:
    → "cloudy" (high humidity = likely cloudy/overcast night)
ELIF pressure <29.80 inHg AND humidity >75% AND wind <3mph:
    → "cloudy" (low pressure + high humidity + calm = cloudy)
ELIF pressure <29.80 inHg AND humidity <65%:
    → "clear-night" (low pressure but low humidity = can still be clear)
ELIF pressure <29.80 inHg:
    → "partly_cloudy" (low pressure with moderate conditions)
ELSE:
    → "partly_cloudy" (default night condition)
```

## Pressure Analysis System

**Meteorologically Accurate Thresholds:**

- **Very High Pressure**: >30.20 inHg (high pressure system)
- **High Pressure**: >30.00 inHg (above normal)
- **Normal Pressure**: 29.80-30.20 inHg (normal range)
- **Low Pressure**: <29.80 inHg (low pressure system)
- **Very Low Pressure**: <29.50 inHg (storm system)
- **Extremely Low Pressure**: <29.20 inHg (severe storm)

## Wind Analysis (Beaufort Scale Adapted)

- **Calm**: <1 mph
- **Light**: 1-7 mph (light air to light breeze)
- **Strong**: 19-31 mph (strong breeze to near gale)
- **Gale**: ≥32 mph (gale force)
- **Gusty**: gust_factor >1.5 AND wind_gust >10 mph
- **Very Gusty**: gust_factor >2.0 AND wind_gust >15 mph

## Rain State Sensor Requirements

**Important:** The rain_state sensor must be a binary moisture sensor that reports only:

- `"wet"` - when moisture is detected
- `"dry"` - when no moisture is detected

**Invalid values** (will not work): `"rain"`, `"drizzle"`, `"precipitation"`

## Fog vs Precipitation Detection

The system intelligently distinguishes between:

1. **Fog Moisture**: High humidity, minimal dewpoint spread, light winds
2. **Precipitation Moisture**: Measurable rain rate OR wet sensor without fog conditions

This prevents false precipitation alerts when fog causes the moisture sensor to read "wet".

## Visibility Estimation Algorithm

Visibility is scientifically estimated based on weather conditions and meteorological data:

**Fog Conditions:**

- Dense fog (dewpoint_spread ≤1°F): 0.3 km
- Thick fog (dewpoint_spread ≤2°F): 0.8 km
- Moderate fog (dewpoint_spread ≤3°F): 1.5 km
- Light fog/mist: 2.5 km

**Precipitation Conditions:**

- Heavy precipitation (≥0.5 in/h): Visibility × 0.3
- Moderate precipitation (≥0.25 in/h): Visibility × 0.5
- Light precipitation (≥0.1 in/h): Visibility × 0.7
- Drizzle: Visibility × 0.85
- Wind reduces visibility further

**Storm Conditions:**

- With precipitation: 3.0 - (rain_rate × 2) km
- Dry storm: 8.0 - (wind_gust ÷ 10) km

**Clear Conditions:**

- Clear night (low humidity): 20-25 km
- Sunny day (high solar): 25-30 km
- Cloudy conditions: 12-20 km (based on atmospheric clarity)

## Dewpoint Calculation

The system uses the Magnus-Tetens formula for accurate dewpoint calculation:

```
dewpoint_celsius = (b × γ) / (a - γ)
where γ = (a × temp_celsius) / (b + temp_celsius) + ln(humidity/100)
a = 17.27, b = 237.7 (Magnus constants)
```

This is critical for fog detection and humidity analysis.

## Cloud Cover Analysis

Cloud cover percentage is estimated using solar radiation analysis with solar elevation compensation:

```
solar_cloud_cover = 100 - (solar_radiation / expected_solar_radiation * 100)
lux_cloud_cover = 100 - (solar_lux / 100000 * 100)
uv_cloud_cover = 100 - (uv_index / 11 * 100)

Weighted: solar_radiation × 0.6 + solar_lux × 0.3 + uv_index × 0.1
```

**Solar Elevation Compensation:**

The system uses solar elevation data (from sun sensor) to calculate expected solar radiation:

```
expected_solar_radiation = max_solar_radiation × sin(solar_elevation)
```

- **Higher elevation** = More expected solar radiation (better cloud cover accuracy)
- **Lower elevation** = Less expected solar radiation (accounts for sun angle)
- **Fallback**: 45° elevation if sun sensor not configured

This provides more accurate cloud cover percentages throughout the day, accounting for the sun's position in the sky.

## Sensor Data Requirements

### Required Sensors

- **Outdoor Temperature**: Essential for all calculations
- **Humidity**: Required for fog detection and dewpoint calculations

### Optional but Recommended Sensors

- **Rain Rate**: Precipitation intensity measurement
- **Rain State**: Binary moisture sensor (wet/dry only)
- **Solar Radiation**: Primary cloud cover detection
- **Solar Lux**: Secondary daylight/cloud detection
- **UV Index**: Clear sky confirmation
- **Sun Sensor**: Solar elevation data for precise cloud cover calculations
- **Wind Speed**: Storm detection and fog analysis
- **Wind Gust**: Severe weather identification
- **Pressure**: Atmospheric system analysis

### Sensor Configuration Notes

**Rain State Sensor Requirements:**

- Must be binary moisture/precipitation sensor
- Valid states: "wet", "dry" (case insensitive)
- Invalid states: "rain", "drizzle", "precipitation"
- Examples: Rain sensors, leaf wetness sensors, moisture detectors

## Unit Conversions

The integration automatically handles unit conversions:

- **Temperature**: °F ↔ °C: `(°F - 32) × 5/9`
- **Pressure**: inHg → hPa: `inHg × 33.8639`
- **Wind Speed**: mph → km/h: `mph × 1.60934`

## Historical Data and Trends

The system maintains historical data for:

- **Pressure Trends**: 3-hour and 24-hour pressure changes
- **Wind Direction**: Circular averaging and stability analysis
- **Temperature Patterns**: Long-term trending
- **Storm Probability**: Based on pressure drops and wind shifts

## Weather Condition Mapping

Home Assistant weather entity mappings:

- `sunny` → Clear (day)
- `clear-night` → Clear (night)
- `cloudy` → Cloudy
- `partly_cloudy` → Partly Cloudy
- `rainy` → Rainy
- `snowy` → Snowy
- `stormy` → Lightning Rainy / Severe Weather
- `foggy` → Fog

## Algorithm Accuracy

This advanced algorithm provides highly accurate weather detection by:

1. **Using Real Sensor Data**: No simulated or estimated values
2. **Meteorological Principles**: Based on scientific weather analysis
3. **Priority System**: Handles conflicting sensor readings intelligently
4. **Fog vs Rain Logic**: Distinguishes moisture sources accurately
5. **Pressure Analysis**: Incorporates atmospheric pressure systems
6. **Multi-Sensor Validation**: Cross-references multiple data sources

The result is weather detection that matches or exceeds professional weather stations while using your existing Home Assistant sensor infrastructure.
