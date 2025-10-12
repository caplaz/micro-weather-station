# Weather Detection Algorithm

This document explains how the Micro Weather Station determines weather conditions from your real sensor data.

## Algorithm Overview

The weather detection system uses a sophisticated priority-based algorithm with meteorological principles to analyze sensor data and determine accurate weather conditions.

_For version-specific improvements and changes, see the [CHANGELOG](CHANGELOG.md)._

## Weather Condition Detection Logic

### Priority-Based Detection System

The algorithm uses a comprehensive 7-priority system with meteorological principles to analyze sensor data and determine accurate weather conditions. Each priority level has specific scientific criteria and thresholds to ensure accurate weather detection.

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
ELIF pressure < 29.20 inHg OR (pressure < 29.50 inHg AND wind_speed ≥19mph AND rain_rate > 0.1) OR (pressure < 29.50 inHg AND is_very_gusty AND rain_rate > 0.25):
    → "lightning-rainy" (thunderstorm/severe weather with precipitation)
ELIF rain_rate ≥ 0.25 in/h:
    → "pouring" (heavy rain)
ELIF rain_rate ≥ 0.1 in/h:
    → "rainy" (moderate rain)
ELSE:
    → "rainy" (light rain/drizzle)
```

#### Priority 2: Severe Weather Conditions (No Precipitation)

```
IF pressure < 29.50 inHg AND wind_speed ≥19mph AND gust_factor >2.0 AND wind_gust >15mph:
    → "lightning" (severe weather system approaching)
ELIF gust_factor >3.0 AND wind_gust >20mph OR wind_gust >40mph:
    → "lightning" (severe turbulence indicating thunderstorm activity)
IF wind_speed ≥ 32mph:
    → "windy" (gale force winds)
```

#### Priority 2.5: Windy Conditions (Gusty/Strong Winds Without Precipitation)

```
IF wind_gust ≥ 30 AND gust_factor > 2.0 AND rain_rate ≤ 0.02:
    → "windy" (very gusty winds with minimal precipitation)
ELIF wind_speed ≥ 19mph AND wind_speed < 32mph:
    → "windy" (strong winds without precipitation)
```

#### Priority 3: Fog Conditions (Critical for Safety)

**Advanced Fog Analysis (when rain_state ≠ "wet"):**

The system uses sophisticated meteorological principles to detect different types of fog based on atmospheric conditions, with special handling for dawn/twilight periods to prevent false detections.

**Twilight Detection (prevents false fog detection during dawn/dusk):**

```
IF 5 W/m² < solar_radiation < 100 W/m²:  # Dawn/twilight conditions
    IF humidity ≥99.8% AND dewpoint_spread ≤0.5°F AND solar_radiation <15 W/m²:
        → "fog" (extreme fog blocking twilight sun)
    ELSE:
        → NOT fog (high humidity during dawn/dusk is normal)
```

**Nighttime Fog Detection (solar_radiation ≤2 W/m²):**

```
Dense Fog: humidity ≥99.5% AND dewpoint_spread ≤0.5°F AND wind ≤2mph
Radiation Fog: humidity ≥99.5% AND dewpoint_spread ≤0.5°F AND wind ≤3mph
Advection Fog: humidity ≥98% AND dewpoint_spread ≤3°F AND 3mph ≤ wind ≤12mph AND solar <10 W/m²
Evaporation Fog: humidity ≥98% AND dewpoint_spread ≤3°F AND wind ≤6mph AND temp >40°F AND solar <10 W/m²
```

**Daytime Fog Detection:**

```
Dense Fog: humidity ≥99% AND dewpoint_spread ≤0.5°F AND wind ≤2mph AND solar ≤2 W/m²
Radiation Fog: humidity ≥98% AND dewpoint_spread ≤2°F AND wind ≤3mph AND solar ≤2 W/m²
Advection Fog: humidity ≥95% AND dewpoint_spread ≤3°F AND 3mph ≤ wind ≤12mph AND solar <10 W/m²
```

#### Priority 4: Daytime Conditions

**Daytime Detection:** `solar_radiation > 5 W/m² OR solar_lux > 50 lx OR uv_index > 0.1`

**Cloud Cover Analysis:**

```
IF cloud_cover ≤40%:
    → "sunny"
ELIF cloud_cover ≤60%:
    → "partly_cloudy"
ELIF cloud_cover ≤85%:
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
IF pressure_low AND humidity > 90 AND wind_speed < 3:
    → "cloudy" (low pressure + very high humidity + calm = cloudy)
ELIF pressure_very_high AND wind_speed < 1 AND humidity < 70:
    → "clear-night" (perfect clear night)
ELIF pressure_high AND not_gusty AND humidity < 80:
    → "clear-night" (clear night)
ELIF pressure_low AND humidity < 65:
    → "clear-night" (low pressure, low humidity = clear)
ELIF pressure_normal AND 1mph ≤ wind_speed < 8mph AND humidity < 85:
    → "partly_cloudy" (partly cloudy night with moderate humidity)
ELIF pressure_low AND humidity < 90:
    → "partly_cloudy" (low pressure with moderate humidity)
ELIF humidity > 90:
    → "cloudy" (very high humidity = likely cloudy/overcast night)
ELSE:
    → "partly_cloudy" (default night condition)
```

## Hysteresis and Condition Stability

The weather detection system implements **hysteresis** to prevent rapid oscillation between weather conditions, ensuring a stable and reliable user experience. Weather conditions can fluctuate rapidly due to sensor noise, brief weather events, or transitional periods, but the hysteresis mechanism filters out these false changes.

### How Hysteresis Works

**Condition Stability Check:**

```
IF new_condition ≠ previous_condition:
    → Check recent condition history (last 3 readings)
    → Count how many times new_condition appeared recently

    IF new_condition appeared ≥1 time recently:
        → Allow condition change (stable transition)
    ELIF condition pair is in major_changes list:
        → Allow immediate change (severe weather transition)
    ELSE:
        → Keep previous_condition (prevent oscillation)
        → Log: "Preventing condition oscillation: keeping X instead of Y"
```

### Major Changes (Immediate Transitions)

Certain weather condition transitions are considered **major changes** that should occur immediately, regardless of hysteresis, because they represent significant weather events that users need to know about right away:

**Severe Weather Transitions (Immediate):**

- **Thunderstorms**: `sunny ↔ lightning-rainy`, `clear-night ↔ lightning-rainy`, `fog ↔ lightning-rainy`
- **Heavy Rain**: `sunny ↔ pouring`, `clear-night ↔ pouring`, `fog ↔ pouring`
- **Snow**: `sunny ↔ snowy`, `clear-night ↔ snowy`, `fog ↔ snowy`
- **Lightning**: `sunny ↔ lightning`, `clear-night ↔ lightning`, `fog ↔ lightning`
- **High Winds**: `sunny ↔ windy`, `clear-night ↔ windy`, `fog ↔ windy`

**Why Major Changes Matter:**

Severe weather conditions like thunderstorms, heavy rain, snow, lightning, and high winds can develop or dissipate rapidly. Users need immediate notification of these changes for safety and planning purposes. The hysteresis would normally delay these transitions, but the major_changes mechanism ensures critical weather alerts are delivered promptly.

**Normal Conditions (Require Stability):**

Transitions between normal weather conditions (sunny ↔ partly_cloudy ↔ cloudy, etc.) require the new condition to be observed multiple times before changing, preventing flickering between states due to temporary sensor variations or brief weather fluctuations.

### Benefits of Hysteresis

1. **Stable Display**: Weather cards don't flicker between conditions
2. **Reliable Alerts**: Important weather changes still trigger immediately
3. **Noise Reduction**: Filters out sensor noise and brief weather variations
4. **User Experience**: Provides consistent, trustworthy weather information

## Pressure Analysis System

**Meteorologically Accurate Thresholds:**

- **Very High Pressure**: >30.20 inHg (high pressure system)
- **High Pressure**: >30.00 inHg (above normal)
- **Normal Pressure**: 29.80-30.20 inHg (normal range)
- **Low Pressure**: <29.80 inHg (low pressure system)
- **Very Low Pressure**: <29.50 inHg (storm system)
- **Extremely Low Pressure**: <29.20 inHg (severe storm)

## Altitude Correction System

The system automatically corrects pressure readings and thresholds based on your geographical elevation above sea level. This ensures accurate weather detection regardless of whether you're at sea level, in the mountains, or anywhere in between.

**Why Altitude Correction Matters:**

Atmospheric pressure naturally decreases with elevation due to the thinner air mass above higher locations. A pressure reading of 30.00 inHg at 5,000 feet elevation is equivalent to approximately 29.50 inHg at sea level. Without correction, the algorithm would misclassify pressure systems and weather conditions.

**How Altitude Correction Works:**

1. **Pressure Reading Adjustment**: Station pressure (measured at your location) is converted to sea-level equivalent pressure using the barometric formula
2. **Threshold Adjustment**: All pressure thresholds are adjusted based on your elevation to maintain meteorological accuracy
3. **Automatic Configuration**: Altitude is automatically detected from Home Assistant's location settings or can be manually configured

**Barometric Formula Implementation:**

```
P₀ = P × (1 - (L × h) / T₀)^{(g × M) / (R × L)}
```

Where:

- P₀ = Sea-level pressure
- P = Station pressure
- h = Altitude in meters
- L = Temperature lapse rate (0.0065 K/m)
- T₀ = Standard temperature (288.15 K)
- g = Gravitational acceleration (9.80665 m/s²)
- M = Molar mass of air (0.0289644 kg/mol)
- R = Universal gas constant (8.31432 J/(mol·K))

**Threshold Adjustment:**

Pressure thresholds are reduced by approximately 1 hPa (0.0295 inHg) per 8 meters of elevation to account for the thinner atmosphere at higher altitudes.

**Configuration:**

- **Automatic**: Uses Home Assistant's elevation setting (`hass.config.elevation`)
- **Manual**: Can be configured in the integration options
- **Default**: 0 meters (sea level) if not configured

This correction ensures that weather detection accuracy remains consistent across all elevations, from coastal areas to mountain tops.

## Wind Analysis (Enhanced Beaufort Scale)

- **Calm**: <1 mph
- **Light**: 1-7 mph (light air to light breeze)
- **Strong**: 19-31 mph (strong breeze to near gale)
- **Gale**: ≥32 mph (gale force)
- **Gusty**: gust_factor >1.5 AND wind_gust >10 mph
- **Very Gusty**: gust_factor >2.0 AND wind_gust >15 mph
- **Severe Turbulence**: gust_factor >3.0 AND wind_gust >20 mph OR wind_gust >40 mph

**Enhanced Storm Detection:**

Severe turbulence indicators (gust_factor >3.0 or gusts >40 mph) can indicate thunderstorm activity even without precipitation, improving detection of:

- Dry thunderstorms
- Approaching severe weather
- Microbursts and downbursts
- Tornadic activity

## Rain State Sensor Requirements

**Important:** The rain_state sensor must be a binary moisture sensor that reports only:

- `"wet"` - when moisture is detected
- `"dry"` - when no moisture is detected

**Invalid values** (will not work): `"rain"`, `"drizzle"`, `"precipitation"`

## Fog vs Precipitation Detection

When `rain_state` sensor shows "wet" with no significant `rain_rate`, the system checks for fog conditions first:

1. **Fog Moisture**: High humidity, minimal dewpoint spread, light winds, **AND very low solar radiation**
2. **Precipitation Moisture**: Measurable rain rate OR wet sensor without fog conditions

### Dawn/Twilight Handling

The system includes special logic to prevent false fog detection during sunrise/sunset:

- **Twilight Range**: 5-100 W/m² solar radiation
- **Normal Behavior**: High humidity (even 99%) during dawn is common due to overnight cooling
- **True Fog**: Only detected if solar radiation is severely suppressed (<15 W/m²) with extreme conditions
- **Example**: Solar radiation of 22 W/m² at solar elevation 3.7° indicates clear dawn, not fog, even with 99% humidity

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

Cloud cover percentage is estimated using solar radiation analysis with solar elevation compensation and intelligent fallback logic for low-light conditions:

**Primary Analysis:**

```
solar_cloud_cover = 100 - (solar_radiation / expected_solar_radiation * 100)
lux_cloud_cover = 100 - (solar_lux / 100000 * 100)
uv_cloud_cover = 100 - (uv_index / 11 * 100)

Weighted: solar_radiation × 0.8 + solar_lux × 0.15 + uv_index × 0.05
```

**Intelligent Weighting (adapts to sensor availability):**

```
When UV sensor working (uv_index > 0):
  solar_radiation × 0.8 + solar_lux × 0.15 + uv_index × 0.05

When UV sensor faulty/unavailable (uv_index = 0):
  solar_radiation × 0.85 + solar_lux × 0.15

Lux-only fallback (when solar radiation < 10 W/m²):
  solar_lux × 0.9 + uv_index × 0.1 (if UV available)
  solar_lux only (if UV unavailable)

UV-only fallback (when solar < 10 W/m² and lux < 1000):
  uv_index only
```

**Low Solar Radiation Fallback Logic:**

```
IF solar_radiation < 50 W/m² AND solar_lux < 5000 lx AND uv_index = 0:
    → 85% cloud cover (heavy overcast conditions)
ELIF solar_radiation < 100 W/m² AND solar_lux < 10000 lx:
    → 70% cloud cover (mostly cloudy conditions)
ELIF solar_radiation < 200 W/m² AND solar_lux < 20000 lx AND uv_index < 1:
    → 40% cloud cover (partly cloudy fallback when data is inconclusive)
```

### Astronomical Clear-Sky Radiation Calculations

The system uses advanced astronomical calculations to determine the theoretical maximum solar radiation under clear sky conditions, accounting for Earth's elliptical orbit and atmospheric effects.

**Solar Constant Variation (Earth-Sun Distance):**

Earth's orbit is elliptical, causing the solar constant to vary by ±3.3% throughout the year:

```
solar_constant_variation = 1 + 0.033 × cos(2π × (day_of_year - 4) / 365.25)
```

- **Day 4 (January 4)**: Closest to sun (+3.3% solar constant)
- **Day 186 (July 4)**: Farthest from sun (-3.3% solar constant)
- **Base solar constant**: 1366 W/m² at 1 AU (Earth-Sun distance)

**Air Mass Correction (Atmospheric Path Length):**

Uses the Gueymard 2003 formula for accurate air mass calculation at all solar elevations:

```
AM = (1.002432 × cos²(Z) + 0.148386 × cos(Z) + 0.0096467) /
     (cos³(Z) + 0.149864 × cos²(Z) + 0.0102963 × cos(Z) + 0.000303978)
```

Where Z is the zenith angle (90° - solar_elevation). This provides improved accuracy for low sun angles and all atmospheric conditions.

**Atmospheric Extinction (Rayleigh Scattering, Ozone, Water Vapor):**

```
rayleigh_extinction = exp(-0.1 × air_mass)      # Rayleigh scattering
ozone_extinction = exp(-0.02 × air_mass)        # Ozone absorption
water_vapor_extinction = exp(-0.05 × air_mass)  # Water vapor absorption
aerosol_extinction = exp(-0.1 × air_mass)       # Aerosol scattering (clear sky)

atmospheric_transmission = rayleigh × ozone × water_vapor × aerosol
```

**Theoretical Clear-Sky Irradiance:**

```
theoretical_irradiance = base_solar_constant × solar_constant_variation ×
                        atmospheric_transmission × sin(solar_elevation)
```

**Local Calibration and Seasonal Impact:**

The system uses a configurable zenith maximum solar radiation (default 1000 W/m²) adjusted for seasonal variations. This can be calibrated for your specific sensor and location using the config flow:

```
calibrated_max_radiation = zenith_max_radiation × solar_constant_variation ×
                          astronomical_scaling
```

Where `zenith_max_radiation` is user-configurable, and `astronomical_scaling` is based on solar elevation and atmospheric transmission.

**Seasonal Radiation Variations:**

- **Winter (Jan 4)**: ~626 W/m² maximum at 60° elevation
- **Summer (Jul 4)**: ~586 W/m² maximum at 60° elevation
- **Spring/Fall**: Intermediate values based on Earth-Sun distance

**Impact on Cloud Cover Detection:**

Seasonal variations ensure accurate cloud cover percentages year-round:

```
cloud_cover = 100 - (actual_solar_radiation / seasonal_max_radiation × 100)
```

- **Winter**: Same solar radiation gives higher cloud cover % (more conservative)
- **Summer**: Same solar radiation gives lower cloud cover % (less conservative)
- **Result**: More accurate weather condition detection throughout the year

**Solar Elevation Compensation:**

The system uses solar elevation data (from sun sensor) to calculate expected solar radiation:

```
expected_solar_radiation = max_solar_radiation × sin(solar_elevation)
```

- **Higher elevation** = More expected solar radiation (better cloud cover accuracy)
- **Lower elevation** = Less expected solar radiation (accounts for sun angle)
- **Fallback**: 45° elevation if sun sensor not configured

**Geographic Seasonal Adjustment:**

Solar radiation expectations are adjusted based on:

- **Month of year**: Different solar intensity by season
- **Latitude**: Higher latitudes have more extreme seasonal variations
- **Northern/Southern hemisphere**: Seasons are flipped in southern hemisphere

This provides more accurate cloud cover percentages throughout the day and year, accounting for the sun's position and seasonal variations.

## Astronomical Cloud Cover Analysis (Version 2.2.0)

Version 2.2.0 introduces revolutionary astronomical cloud cover detection using scientific principles for unprecedented accuracy, especially during early morning, late afternoon, and low-sun-angle conditions where traditional fixed-threshold methods fail.

### Breakthrough Technology Overview

The astronomical cloud cover analysis replaces fixed thresholds with dynamic calculations based on:

- **Theoretical clear-sky radiation** using solar elevation and astronomical principles
- **Relative percentage thresholds** instead of absolute values (30%, 20%, etc.)
- **Intelligent fallback logic** that only applies when astronomical calculations are unreliable (<15° solar elevation)
- **Scientific precision** employing meteorological principles for superior weather condition detection

### Solar Elevation Integration

**Dynamic Expected Radiation Calculation:**

```
expected_solar_radiation = theoretical_clear_sky_max × sin(solar_elevation)
```

- **Higher solar elevation** = More expected radiation (better cloud cover accuracy)
- **Lower solar elevation** = Less expected radiation (accounts for sun angle effects)
- **Real-time adjustment** = Cloud cover percentages adapt throughout the day

### Relative Threshold System

**Traditional Fixed Thresholds (Before 2.2.0):**

- Heavy overcast: solar_radiation < 200 W/m²
- Mostly cloudy: solar_radiation < 100 W/m²
- Partly cloudy: solar_radiation < 50 W/m²

**Astronomical Relative Thresholds (Version 2.2.0):**

- Heavy overcast: solar_radiation < 30% of expected clear-sky radiation
- Mostly cloudy: solar_radiation < 20% of expected clear-sky radiation
- Partly cloudy: solar_radiation < 10% of expected clear-sky radiation

### Theoretical Clear-Sky Radiation Calculations

The system calculates theoretical maximum solar radiation using advanced astronomical formulas:

**Earth-Sun Distance Variation:**

```
solar_constant_variation = 1 + 0.033 × cos(2π × (day_of_year - 4) / 365.25)
```

- **January 4**: +3.3% (closest to sun)
- **July 4**: -3.3% (farthest from sun)

**Air Mass Correction (Gueymard 2003 Formula):**

```
AM = (1.002432 × cos²(Z) + 0.148386 × cos(Z) + 0.0096467) /
     (cos³(Z) + 0.149864 × cos²(Z) + 0.0102963 × cos(Z) + 0.000303978)
```

Where Z is the zenith angle (90° - solar_elevation), providing superior accuracy at low solar elevations.

**Atmospheric Extinction:**

```
atmospheric_transmission = rayleigh_extinction × ozone_extinction ×
                          water_vapor_extinction × aerosol_extinction
```

**Final Theoretical Irradiance:**

```
theoretical_irradiance = base_solar_constant × solar_constant_variation ×
                        atmospheric_transmission × sin(solar_elevation)
```

### Intelligent Fallback Logic

**When Astronomical Calculations Are Reliable:**

- Use full astronomical calculations for all solar elevations ≥15°
- Apply relative percentage thresholds based on theoretical clear-sky radiation
- Provide scientifically accurate cloud cover percentages

**When Astronomical Calculations Are Unreliable:**

- Solar elevation <15° (very low sun angles)
- Apply intelligent fallback logic only when needed
- Use absolute thresholds with solar elevation context
- Maintain accuracy during dawn, dusk, and low-sun conditions

### Seasonal and Geographic Accuracy

**Seasonal Radiation Variations:**

- **Winter**: Same measured radiation gives higher cloud cover % (more conservative detection)
- **Summer**: Same measured radiation gives lower cloud cover % (less conservative detection)
- **Result**: Consistent accuracy year-round

**Geographic Considerations:**

- **Latitude effects**: Higher latitudes have more extreme seasonal variations
- **Hemisphere differences**: Seasons are appropriately flipped in southern hemisphere
- **Local calibration**: Adapts to your specific location's solar patterns

### Enhanced Weather Condition Detection

**Improved Accuracy Examples:**

- **Early morning (low sun)**: Traditional methods often show "cloudy" even on clear days
- **Late afternoon**: Astronomical calculations correctly identify clear vs. cloudy conditions
- **Seasonal variations**: Winter cloud detection is more accurate with astronomical scaling
- **Edge cases**: Better handling of transitional lighting conditions

**Scientific Validation:**

- Uses established astronomical formulas (Kasten-Young air mass)
- Accounts for Earth's elliptical orbit and seasonal solar constant variations
- Incorporates atmospheric extinction from Rayleigh scattering, ozone, and water vapor
- Provides meteorologically accurate cloud cover percentages

### Technical Implementation

**Algorithm Flow:**

1. Calculate theoretical clear-sky radiation using solar elevation
2. Apply astronomical scaling factors for season and location
3. Use relative percentage thresholds instead of fixed values
4. Fall back to intelligent absolute thresholds only when astronomical calculations are unreliable
5. Weight measurements: solar radiation (primary) > lux > UV index
6. Apply hysteresis to prevent condition oscillation

**Benefits:**

- **Unprecedented accuracy** in cloud cover detection
- **Scientific precision** using astronomical principles
- **Year-round consistency** across all seasons
- **Location awareness** adapting to your geographic position
- **Real-time adaptation** throughout the day as sun position changes

This breakthrough technology represents a significant advancement in home weather station accuracy, providing professional-grade cloud cover analysis using your existing sensor infrastructure.

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

**Altitude Configuration:**

- **Purpose**: Adjusts pressure readings to sea-level equivalent for accurate weather detection
- **Setting to 0**: Uses raw sensor pressure readings (no altitude adjustment)
- **Non-zero values**: Converts station pressure to sea-level equivalent using barometric formula
- **Automatic Detection**: Uses Home Assistant's elevation setting when available
- **Manual Configuration**: Can be set in integration options if auto-detection is incorrect
- **Units**: Meters above sea level
- **Default**: 0 meters (raw sensor pressure)
- **Impact**: Ensures consistent accuracy from sea level to mountain elevations

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

## Algorithm Accuracy

This advanced algorithm provides highly accurate weather detection by:

1. **Using Real Sensor Data**: No simulated or estimated values
2. **Meteorological Principles**: Based on scientific weather analysis
3. **Priority System**: Handles conflicting sensor readings intelligently
4. **Fog vs Rain Logic**: Distinguishes moisture sources accurately
5. **Pressure Analysis**: Incorporates atmospheric pressure systems
6. **Multi-Sensor Validation**: Cross-references multiple data sources

The result is weather detection that matches or exceeds professional weather stations while using your existing Home Assistant sensor infrastructure.

This advanced algorithm provides highly accurate weather detection by:

1. **Using Real Sensor Data**: No simulated or estimated values
2. **Meteorological Principles**: Based on scientific weather analysis
3. **Priority System**: Handles conflicting sensor readings intelligently
4. **Fog vs Rain Logic**: Distinguishes moisture sources accurately
5. **Pressure Analysis**: Incorporates atmospheric pressure systems
6. **Multi-Sensor Validation**: Cross-references multiple data sources

The result is weather detection that matches or exceeds professional weather stations while using your existing Home Assistant sensor infrastructure.
