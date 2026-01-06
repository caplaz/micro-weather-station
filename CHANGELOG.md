# Changelog

## 4.1.0 (Unreleased)

### Features

- **"Feels Like" Temperature**: Added Apparent Temperature calculation (#Feature)
  - Calculates "Feels Like" temperature using Heat Index (Rothfusz algorithm) and Wind Chill (NOAA algorithm)
  - Automatically applies Wind Chill when temp ≤ 50°F and wind > 3 mph
  - Automatically applies Heat Index when temp ≥ 80°F
  - Exposed as `apparent_temperature` attribute on the weather entity
  - Smart unit handling (performs internal calculations in required Imperial units, converts output to match user preference)

## 4.0.1 (2025-12-02)

### Forecast Logic Improvements

- **Historical Volatility-Based Temperature Variation**: Replaced hardcoded day-to-day temperature patterns with calculations based on observed sensor volatility
  - Temperature forecasts now show realistic variation scaled to historical temperature swings
  - Natural day-to-day temperature changes based on actual weather patterns rather than static values
  - Added seasonal temperature adjustments for more accurate forecasts
  - Enhanced test coverage for volatility-scaled temperature variation

### Weather Detection Improvements

- **Improved Fog Detection at Sunrise**: Enhanced fog detection logic to prevent false positives at low solar elevations
  - Added clear-sky radiation model for sun angles below 15° to determine expected solar radiation
  - At sunrise/sunset, compares actual solar radiation to expected clear-sky values
  - Prevents false fog detection when low solar radiation is normal for the sun angle
  - Maintains fog detection when solar radiation is abnormally low for the elevation
  - Added comprehensive tests for sunrise fog scenarios

### Bug Fixes

- Placeholder for additional bug fixes in v4.0.1

## 4.0.0 (2025-11-30)

### Bug Fixes

- **Dewpoint Unit Conversion**: Fixed incorrect dewpoint display when using external dewpoint sensors (#18)
  - Dewpoint sensor values are now properly converted using the sensor's native unit
  - Previously, all dewpoint values were assumed to be Fahrenheit, causing Celsius values to be incorrectly converted
  - Example: Ecowitt sensor reporting 1.8°C was displayed as -16.7°C due to double conversion
  - Calculated dewpoints (from temp/humidity) still correctly use Fahrenheit internally

### Forecast Logic Overhaul

- **Trajectory-Based Condition Evolution**: Replaced static condition mapping with dynamic trajectory scoring

  - Conditions now evolve based on pressure trend direction and magnitude
  - Trajectory score (-100 to +100) determines condition ladder progression
  - Falling pressure moves conditions toward deterioration, rising toward improvement
  - Humidity trends influence precipitation/clearing transitions

- **Trend-Integrated Temperature Forecasting**: Temperature forecasts now properly use trend data

  - Temperature projected forward using trend \* hours (not arbitrary multipliers)
  - Pressure gradient effects applied to daily temperature swings
  - Distance dampening reduces confidence for distant forecasts

- **Deterministic Precipitation Forecasting**: Removed all random.uniform() calls

  - Precipitation now based on condition, humidity trends, and storm probability
  - Condensation potential only affects current day (not distant forecasts)
  - Rising humidity increases precipitation by up to 50%
  - Falling pressure amplifies precipitation amounts

- **Improved Humidity Convergence**: Faster, more realistic humidity evolution

  - Humidity now converges 30% per hour toward target (was 10%)
  - Target humidity based on forecasted condition
  - Eliminated arbitrary hour-based modulation

- **Evolution Model Improvements**: Weather system evolution based on actual trends

  - Evolution paths dynamically generated from pressure trend magnitude
  - Confidence degrades based on trend volatility (disagreement between short/long term)
  - Hourly change rate determined by trend magnitude (rapid/moderate/gradual)

- **Code Cleanup**: Removed unused imports, dead code, and obsolete tests
  - Removed `_apply_moisture_precipitation_logic` (logic integrated into `_forecast_precipitation`)
  - Cleaned up unused imports in daily.py, evolution.py
  - Updated tests to reflect new forecast logic

### Weather Detection Improvements

- **Improved Cloud Cover Thresholds**: Adjusted thresholds to be more conservative and accurate

  - Sunny threshold increased from 20% to 30% to avoid false sunny reports
  - Partly cloudy threshold increased from 50% to 60% for better gradation
  - Cloudy threshold increased from 75% to 85% for more accurate overcast detection
  - Improved documentation of cloud cover to condition mapping logic

- **Enhanced Dew/Condensation Detection**: Added intelligent dew detection to prevent false rain alerts

  - System now uses consistent threshold matching `PrecipitationThresholds.SIGNIFICANT` (0.01 in/h)
  - Prevents false "rainy" conditions on humid mornings when dew triggers rain sensors
  - Clearer logic separation between dew/condensation and actual precipitation

- **More Conservative Fog Detection**: Improved fog detection to reduce false positives

  - Added pre-validation requiring minimum 88% humidity before fog analysis
  - Added solar radiation check during daytime (fog should suppress radiation below expected minimum)
  - Added stricter dewpoint spread requirement (≤2.0°F) for moderate fog scores (55-70 range)
  - Added temperature trend consideration (cooling trend favorable for fog formation)
  - Better prevents false fog detection on humid but clear mornings

- **Improved Condition Hysteresis**: Enhanced stability to prevent rapid oscillation between conditions

  - Adjacent condition transitions (sunny↔partlycloudy, partlycloudy↔cloudy) require 15% change
  - Non-adjacent transitions (sunny↔cloudy) require 25% change to prevent unrealistic jumps
  - Added trend-based threshold reduction for consistent patterns

- **Solar Elevation Estimation**: Better cloud cover calculation when sun sensor is not configured

  - Estimates solar elevation based on radiation intensity (800+ W/m² → 60°, 500+ → 45°, 200+ → 25°, else → 15°)
  - Provides more accurate cloud cover percentages without explicit sun sensor data

- **Storm Probability Threshold Consistency**: Fixed inconsistent threshold comparisons

  - Unified storm threshold comparisons to use `>=` for `STORM_THRESHOLD_SEVERE` (70%)
  - Ensures conditions exactly at thresholds are handled correctly

- **Precipitation Threshold Documentation**: Clarified units in meteorological constants
  - Added clear documentation that `PrecipitationThresholds` are in inches per hour (in/h)
  - Added conversion reference table for mm/h equivalents

### Architecture Improvements

- **Modular Architecture**: Reorganized codebase into specialized modules for improved maintainability and extensibility

  - **Analysis Modules**: Split weather analysis into dedicated modules

    - `analysis/core.py`: Priority-based weather condition determination
    - `analysis/atmospheric.py`: Pressure systems, fog detection, and storm probability
    - `analysis/solar.py`: Cloud cover analysis using solar radiation
    - `analysis/trends.py`: Historical data analysis and pattern recognition

  - **Forecast Modules**: Organized forecasting into specialized components
    - `forecast/meteorological.py`: Meteorological state analysis and atmospheric stability
    - `forecast/patterns.py`: Historical pattern recognition and seasonal factors
    - `forecast/evolution.py`: Weather system transition prediction
    - `forecast/astronomical.py`: Solar position and diurnal cycle calculations
    - `forecast/daily.py`: 5-day forecast generation
    - `forecast/hourly.py`: 24-hour detailed predictions

- **Facade Pattern**: Implemented clean coordination layers

  - `weather_analysis.py`: Coordinates analysis modules
  - `weather_forecast.py`: Orchestrates forecast generators
  - Maintains 100% backward compatibility with existing code

- **Documentation Updates**: Comprehensive documentation describing the modular architecture
  - Updated `DEVELOPMENT.md` with detailed module descriptions
  - Enhanced `WEATHER_DETECTION_ALGORITHM.md` with module responsibilities
  - Improved `WEATHER_FORECAST_ALGORITHM.md` with architectural overview
  - Updated `README.md` with modular system description

### Benefits

- **Maintainability**: Each module has a single, well-defined responsibility
- **Testability**: Individual modules can be tested in isolation
- **Extensibility**: New features can be added to specific modules without affecting others
- **Code Quality**: Improved organization and separation of concerns
- **Developer Experience**: Easier to find and modify specific functionality

### Testing

- All 307 functional tests pass
- Zero breaking changes for end users
- Full backward compatibility maintained

## 3.0.2 (2025-10-26)

### Bug Fixes

- **Daily Forecast Temperature Units**: Fixed issue where daily forecast temperatures displayed in Fahrenheit instead of Celsius (#17)

  - Added temperature conversion in weather_detector.py for external forecast data before storage
  - Improved external forecast handling in weather.py with proper unit conversion
  - Added convert_to_fahrenheit utility function for forecast generation
  - Added comprehensive test coverage with 19 new test methods covering temperature unit conversion, external vs comprehensive forecasts, condition progression, and error handling

### Changes

- Enhanced forecast accuracy with proper temperature unit handling
- Improved test coverage for forecast functionality (78 total tests)
- Better reliability for both external and comprehensive forecast data

## 3.0.1 (2025-10-24)

### Bug Fixes

- **Temperature Conversion Bug**: Fixed double temperature conversion in weather forecasts causing incorrect temperature display

  - Removed unnecessary `convert_to_celsius()` calls in `generate_comprehensive_forecast` method
  - Fixed issue where Fahrenheit temperatures were being converted twice, resulting in wrong forecast temperatures
  - Removed unused import to maintain code quality standards

- **Forecast Timing Issues**: Fixed forecast timing bugs where forecasts started from wrong time periods
  - Daily forecast now correctly starts with the current day instead of tomorrow
  - Hourly forecast now shows hourly intervals starting from the current hour instead of the next hour
  - Fixed timing calculations in both comprehensive and fallback forecast methods
  - Updated test assertions to reflect correct forecast timing behavior

### Changes

- Improved forecast temperature accuracy by eliminating double conversion errors
- Enhanced forecast timing precision for better user experience
- Enhanced code quality with proper import management

## 3.0.0 (2025-10-22)

### Major Features

- **Enhanced Cloud Cover Analysis**: Major improvements to cloud cover calculation accuracy and responsiveness

  - Added hysteresis with 30% maximum change limit to prevent extreme condition jumps
  - Expanded solar radiation bounds to 2000 W/m² for better overcast detection
  - Implemented sensor miscalibration warnings for zenith max radiation outside 800-2000 W/m² range
  - Enhanced astronomical calculations with improved edge case handling

- **Advanced Weather Forecasting Engine**: Comprehensive overhaul of forecasting with pressure-aware evolution

  - Implemented pressure-aware forecast evolution with dynamic timing based on meteorological conditions
  - Added comprehensive diurnal condition variations for realistic 24-hour weather patterns
  - Enhanced storm probability integration with pressure-driven condition overrides
  - Improved micro-evolution modeling with intelligent frequency adjustments
  - Added safety checks and type validation throughout the forecasting pipeline

### Technical Improvements

- **Enhanced Hysteresis System**: Upgraded condition stability with time-based history (1-hour window) and extreme jump prevention
- **Robust Error Handling**: Added comprehensive type validation and error recovery throughout weather analysis
- **Algorithm Safety**: Implemented sensor validation and fallback mechanisms for reliable operation
- **Code Quality**: Maintained all pre-commit hooks (black, isort, flake8) with comprehensive test coverage

### Bug Fixes

- **Cloud Cover Responsiveness**: Fixed issues where 59.9%/56.8% cloud cover showed "cloudy" instead of "partly cloudy"
- **Condition Stability**: Resolved rapid oscillation between weather conditions due to sensor noise
- **Forecast Accuracy**: Improved forecast reliability with pressure-aware evolution timing

### Changes

- Significant improvements to weather detection accuracy and forecast reliability
- Enhanced user experience with more stable and responsive weather condition updates
- Better meteorological modeling with comprehensive safety checks and validation
- Improved code maintainability with enhanced error handling and type safety

## 2.3.1 (2025-10-13)

### Major Features

- **Pressure Trend Integration**: Enhanced cloud detection with pressure trends for more accurate weather forecasting

  - Integrate pressure trends into cloud detection algorithms (falling pressure = more clouds)
  - Add pressure-based cloud cover adjustments for meteorological accuracy
  - Enhance forecast system to use cloud cover analysis for near-term predictions (days 0-1)
  - Add comprehensive sensor unavailability testing (None values, missing keys, complete failure)
  - Improve error handling for missing solar, wind, and historical data
  - Add graceful fallbacks to pressure-based estimation when sensors unavailable

- **Dynamic Sunrise/Sunset Detection**: Replace hardcoded sunrise/sunset times with dynamic data from sun.sun entity

  - Add dynamic sunrise/sunset detection using Home Assistant's sun.sun entity
  - Implement fallback to hardcoded 6 AM/6 PM when sun.sun entity unavailable
  - Add condition conversion for nighttime hours (sunny→clear_night, partlycloudy→cloudy)
  - Ensure timezone-aware datetime handling for accurate comparisons

### Technical Improvements

- **Enhanced Error Handling**: Narrow exception handling from generic Exception to specific types (KeyError, ValueError, TypeError)
- **Test Infrastructure**: Fix datetime mocking in tests by patching module-specific datetime
- **Code Quality**: Add bandit-report.json to .gitignore for security scanning
- **Test Coverage**: Achieve 96% test coverage for forecast module with 30 comprehensive tests

### Bug Fixes

- **Datetime Mocking**: Fixed datetime mocking issues in test suite for proper timezone handling
- **Coordinator Data Validation**: Add coordinator data check in async_forecast_hourly method

### Changes

- More accurate weather forecasting through pressure trend integration
- Dynamic astronomical timing using Home Assistant's sun entity
- Improved robustness with comprehensive sensor failure handling
- Enhanced test coverage and error handling throughout the codebase

## 2.3.0 (2025-10-12)

### Major Features

- **Configurable Zenith Maximum Radiation**: Added user-configurable `zenith_max_radiation` setting for precise solar calibration

  - Allows fine-tuning of solar radiation calculations for your specific sensor and location
  - Improves cloud cover detection accuracy by accounting for local atmospheric conditions
  - Available in the integration's configuration flow for easy adjustment

- **Enhanced Wind Detection**: Improved wind condition analysis and classification

  - Better detection of gusts, turbulence, and severe wind events
  - More accurate wind-based weather condition determination
  - Enhanced handling of wind patterns for improved storm detection

- **Gueymard 2003 Air Mass Formula**: Upgraded solar radiation calculations with scientifically accurate air mass formula

  - Replaced previous formula with the industry-standard Gueymard 2003 air mass calculation
  - Provides superior accuracy for solar radiation analysis at all solar elevations
  - Improves cloud cover estimation, especially at low sun angles

### Technical Improvements

- **Solar Analysis Precision**: Enhanced astronomical calculations for better weather detection accuracy
- **Wind Algorithm Refinement**: Updated wind detection logic for more reliable severe weather identification
- **Configuration Flexibility**: Added new calibration options for advanced users

### Changes

- More accurate weather condition detection through improved solar and wind analysis
- Enhanced user calibration options for location-specific optimization
- Scientific accuracy improvements in meteorological calculations

## 2.2.1 (2025-10-10)

### Improvements

- **Weather Entity Initialization**: Restored async_added_to_hass method for proper Home Assistant lifecycle

  - Ensures coordinator data refresh when entity is added to Home Assistant
  - Prevents entity from showing as unavailable on first load

- **Enhanced Cloud Cover Analysis**: Improved astronomical calculations with better edge case handling

  - Complete overcast (100%) detection when no solar input detected
  - More accurate heavy overcast detection using astronomical principles
  - Better measurement weighting: solar radiation > lux > UV index

- **Hysteresis Improvements**: Enhanced condition stability with time-based history management

  - Changed condition history from count-based (max 10) to time-based (1 hour window)
  - Hysteresis now compares against recent conditions within last hour instead of fixed count
  - Prevents issues with infrequent updates comparing against very old conditions
  - Maintains 24-hour cleanup to prevent unbounded memory growth

- **Weather Condition Mapping**: Updated to use standard meteorological ranges

  - Sunny: ≤25% cloud cover (was ≤40%)
  - Partly cloudy: 25-50% cloud cover (was 40-60%)
  - Cloudy: 50-75% cloud cover (was 60-85%)
  - Reduced hysteresis threshold for sunny↔partlycloudy transitions from 15% to 10%

### Bug Fixes

- **Severe Weather Detection**: Made severe weather detection more conservative

  - Require pressure < 29.50 inHg AND wind_speed ≥19mph AND gusty conditions for severe weather
  - Add separate condition for severe turbulence (gust_factor >3.0 with gusts >20mph OR gust >40mph)
  - Prevent false 'lightning' alerts for low pressure systems with moderate gusty winds
  - Improve accuracy for weather conditions like approaching low pressure systems with wind gusts

### Technical Improvements

- **Updated Test Suite**: Modified tests to reflect new atmospheric extinction model, condition thresholds, and hysteresis behavior
- **Algorithm Refinement**: More accurate cloud cover analysis for early morning and late afternoon conditions
- **Enhanced Test Coverage**: Updated tests for improved weather entity initialization and astronomical calculations

### Changes

- Better weather entity reliability and initialization
- More responsive weather condition updates with refined hysteresis thresholds
- More conservative severe weather detection to reduce false alerts

## 2.2.0 (2025-10-07)

### Major Features

- **Astronomical Cloud Cover Analysis**: Complete overhaul of cloud cover calculation algorithm using astronomical principles

  - Replaced fixed thresholds with relative percentages of theoretical clear-sky radiation
  - Implemented solar elevation-based calculations for maximum expected solar radiation
  - Added intelligent fallback logic that only applies when astronomical calculations are unreliable (<15° solar elevation)
  - Improved measurement weighting: solar radiation (primary) > lux > UV index
  - Enhanced edge case handling with complete overcast detection (100%) when no solar input

### Technical Improvements

- **Enhanced Test Coverage**: Updated test suite to validate astronomical calculation accuracy
- **Code Quality**: All pre-commit hooks pass with black formatting and comprehensive linting
- **Algorithm Accuracy**: More precise weather condition detection across all solar elevation angles

### Changes

- Significant improvement in cloud cover detection accuracy using scientific astronomical calculations
- Better reliability for weather entity initialization and data availability
- Enhanced meteorological precision for both clear sky and cloudy conditions

## 2.1.1 (2025-10-06)

### Bug Fixes

- **Cloud Cover Calculation Improvements**: Enhanced accuracy for clear sky detection

  - Increased sunny threshold from 35% to 40% cloud cover
  - Balances meteorological accuracy with low sun angle conditions
  - Accommodates early morning/late afternoon when sun elevation is low

- **UV Sensor Fault Handling**: Added intelligent detection and handling of faulty UV sensors

  - Detects when UV sensor is faulty/unavailable (uv_index = 0)
  - Redistributes weights: solar radiation 85%, lux 15% (instead of including UV)
  - Prevents false high cloud cover readings from broken UV sensors

### Technical Improvements

- **Documentation Fixes**: Corrected malformed markdown code blocks in algorithm documentation
- **Improved Weighting Logic**: Enhanced explanation with clearer fallback logic for sensor combinations

### Changes

- Better accuracy for clear sky conditions, especially at low sun angles
- More robust handling of sensor faults and missing data
- Improved documentation quality and clarity

## 2.1.0 (2025-10-04)

### Bug Fixes

- **Precipitation Unit Compatibility**: Fixed "mm/h is not a recognized distance unit" error that prevented forecast display when rain rate sensors were configured

  - Map rain rate units (mm/h, in/h) to distance units (mm, in) for Home Assistant weather entity compatibility
  - Maintains accurate precipitation values while using HA-compatible unit labels
  - Added exception handling for forecast generation to prevent crashes from invalid data

### User Experience Improvements

- **Enhanced Sensor Selection**: Added device class filtering in configuration flow for better sensor discovery

  - Rain rate sensors now filter to `precipitation_intensity` device class only
  - Wind gust sensors now filter to `wind_speed` device class only
  - Prevents users from accidentally selecting inappropriate sensors (e.g., pressure sensors for rain rate)
  - Cleaner sensor dropdowns with relevant options only

- **Debug Logging Configuration**: Added debug logging option to sensor configuration table

  - Users can now enable detailed logging for troubleshooting and development
  - Debug logging helps diagnose weather detection and sensor issues
  - Documented in README configuration section for easy reference

### Technical Improvements

- **Robust Error Handling**: Added comprehensive exception handling for forecast generation
- **Updated Test Suite**: Modified tests to reflect new precipitation unit mapping behavior
- **Code Quality**: Applied black formatting and maintained all linting standards

### Changes

- Improved reliability when rain rate sensors are configured
- Better user experience during sensor configuration
- Enhanced error resilience for forecast calculations

## 2.0.3 (2025-10-03)

### Bug Fixes

- **Forecast Precipitation Unit Conversion**: Fixed precipitation unit mismatch in forecast generation when rain sensors are configured

  - Forecast precipitation values now properly convert to match weather entity's native units (mm vs inches)
  - Fixed issue where forecast would not display when rain rate sensor was configured
  - Added isinstance check to prevent errors with Mock objects during testing
  - Ensures consistent precipitation units between current conditions and forecast data

### Technical Improvements

- **Comprehensive Weather Entity Test Coverage**: Added extensive test suite for weather entity functionality

  - Created `test_weather.py` with 32 comprehensive tests covering all weather entity methods
  - Improved test coverage from 76% to 86% overall, weather.py from 0% to 94%
  - Added tests for entity initialization, properties, availability, daily/hourly forecasts, and unit handling
  - Enhanced regression detection to prevent forecast display issues
  - Applied code formatting with black and isort for consistent style

### Changes

- Enhanced test infrastructure to catch forecast and precipitation unit regressions
- Improved code quality with comprehensive linting and formatting
- Better reliability for forecast display with rain sensor configurations

## 2.0.2 (2025-10-03)

### Bug Fixes

- **Cloud Cover Calculation Accuracy**: Fixed inaccurate cloud cover estimates causing "cloudy" weather conditions despite clear skies

  - Cloud cover analysis now uses actual solar elevation from sun.sun sensor instead of defaulting to 45°
  - More accurate weather condition detection based on real solar position
  - Fixes false "cloudy" reports when solar radiation readings are actually good for clear conditions
  - Improved meteorological accuracy for daytime weather detection

## 2.0.1 (2025-10-02)

### Bug Fixes

- **Altitude Field Configuration**: Fixed options flow not remembering altitude value of 0

  - Altitude field now properly saves and restores 0 values (sea level)
  - Fixed falsy value handling in configuration saving logic
  - Added special handling for numeric fields that can legitimately be 0

- **Documentation Fixes**: Corrected various documentation issues
  - Fixed unicode character encoding issues in README.md
  - Corrected malformed code blocks in README Step 5 and automation examples
  - Updated directory structure documentation to reflect current modular architecture
  - Fixed PR reference number for altitude support feature

### New Features

- **Current Precipitation Support**: Weather entity now displays actual precipitation rate from rain_rate sensor

  - Added native_precipitation property to weather entity
  - Smart unit conversion between in/h and mm/h based on sensor units
  - Precipitation rate displayed in weather card reflects your actual local measurements

- **Enhanced Forecast Precipitation**: Replaced hardcoded forecast values with dynamic calculations
  - Hourly forecasts now use actual rain_rate sensor data instead of fixed 2.0 mm
  - Realistic precipitation variations (±20%) based on forecast conditions
  - Better estimates for different weather conditions (light drizzle to heavy storms)

### Technical Improvements

- **Configuration Flow Enhancements**: Improved handling of numeric configuration values
  - Better validation and saving of numeric fields in options flow
  - Enhanced schema building for optional configuration fields
  - Added comprehensive test coverage for edge cases

## 2.0.0 (2025-10-01)

### Major Features

- **New Config Flow with Single Panels**: Complete redesign of the configuration interface

  - Streamlined single-panel configuration flow for easier setup
  - Improved user experience with cleaner, more intuitive interface
  - Better sensor management and validation
  - Enhanced error handling and user feedback

- **Altitude Support**: Added comprehensive altitude and elevation support (#8)

  - Dynamic altitude units support (meters/feet based on HA system settings)
  - Automatic pressure correction for elevation differences
  - Improved weather detection accuracy at various altitudes
  - Enhanced documentation for elevation data usage

- **Enhanced Weather Detection Algorithms**: Major improvements to meteorological algorithms

  - Improved cloud cover thresholds for better sunny/partly cloudy detection
  - Enhanced wind turbulence analysis for severe weather detection
  - Low solar radiation fallback logic for cloudy conditions
  - Better storm classification with gust factor analysis (>3.0 indicates thunderstorms)
  - More accurate weather condition detection across all scenarios

### Technical Improvements

- **Comprehensive Forecast Documentation**: Added detailed `WEATHER_FORECAST_ALGORITHM.md`

  - Complete coverage of 5-day daily and 24-hour hourly forecasting algorithms
  - Meteorological principles and pressure-based prediction methods
  - Technical implementation details and validation methods

- **Enhanced Test Coverage**: Improved test suite with 136 total tests
  - Updated tests for enhanced storm classification accuracy
  - Better coverage of edge cases and weather detection scenarios
  - Comprehensive validation of all algorithm improvements

### Documentation

- **Algorithm Documentation**: Created comprehensive documentation for both weather detection and forecasting
- **README Updates**: Streamlined forecast section with links to detailed documentation
- **Enhanced Code Comments**: Improved inline documentation throughout the codebase

### Changes

- Significant improvements to weather detection accuracy and reliability
- Better user experience with streamlined configuration interface
- Enhanced altitude support for improved meteorological calculations
- Comprehensive documentation for all algorithms and features

## 1.4.3 (2025-09-25)

### Bug Fixes

- **Options Flow Sensor Management**: Major improvements to sensor configuration handling
  - Fixed ability to remove sensors by clearing fields in options flow
  - Removed problematic defaults from optional sensor fields to enable proper clearing
  - Convert empty strings to None when processing user input for better data integrity
  - Form now pre-populates with current configuration values automatically

### Technical Improvements

- **Enhanced Options Flow Architecture**: Complete refactor of options flow logic
  - Improved schema handling with proper separation between required and optional fields
  - More robust user input processing and validation
  - Better sensor field management with automatic None handling for missing fields
  - Enhanced type safety with corrected OptionsFlowHandler instantiation
  - Added comprehensive test coverage for all options flow scenarios
  - Fixed mypy type checking errors for better code quality

### Changes

- Improved user experience when configuring and reconfiguring sensors
- Better error handling and validation in configuration flows
- Enhanced code maintainability and type safety

## 1.4.2 (2025-09-25)

### Bug Fixes

- **Sensor Removal in Options Flow**: Fixed inability to remove sensors when editing configuration
  - Users can now clear sensor fields to remove them from the configuration
  - Removed defaults from optional sensor fields to allow proper clearing
  - Convert empty strings to None when processing user input
  - Form is pre-populated with current values automatically

### Technical Improvements

- **Enhanced Options Flow**: Improved schema handling for optional sensor fields
  - Better separation between required and optional field handling
  - More robust user input processing for configuration changes
  - Added comprehensive test for sensor removal functionality

## 1.4.1 (2025-09-25)

### Bug Fixes

- **Sun Sensor State Conversion**: Fixed ValueError when using sun.sun sensor with string states like "above_horizon"
  - Skip sun sensor in main sensor processing loop since it only provides elevation data from attributes
  - Sun sensor elevation is still properly retrieved for cloud cover calculations
  - Prevents runtime errors when sun sensor is configured
- **Options Flow Configuration Editing**: Fixed "Entity None is neither a valid entity ID nor a valid UUID" error when editing configuration
  - Only set defaults for optional EntitySelector fields when they have actual values (not None)
  - Allow users to add sensors like Sun Sensor after initial configuration setup
  - Empty optional fields now display correctly in the options form without validation errors

### Technical Improvements

- **Enhanced Test Coverage**: Added comprehensive tests for options flow with None values
  - Tests for configuration editing scenarios with unconfigured sensors
  - Validation of proper handling of optional sensor fields
  - Improved test reliability with proper mocking of ConfigEntry objects

### Changes

- Improved configuration flexibility for post-setup sensor additions
- Better error handling for optional sensor configurations
- Enhanced user experience when modifying integration settings
- **Atmospheric Pressure Support**: Added support for both `pressure` and `atmospheric_pressure` device classes for pressure sensors

## 1.4.0 (2025-09-24)

### Features

- **Complete Unit Conversion Support**: Full support for both metric and imperial sensor units
  - Automatic detection and conversion of temperature (°C/°F), pressure (hPa/inHg), and wind speed (km/h/mph/m/s)
  - Smart unit-aware conversion methods that preserve accuracy across different sensor types
  - Backward compatibility with existing imperial sensor setups

### Technical Improvements

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

### Bug Fixes

- **Forecast Wind Speed Accuracy**: Fixed unrealistic forecast wind speeds that didn't reflect actual sensor readings
- **Unit Conversion Consistency**: Ensured all analysis methods receive correct imperial units regardless of sensor input units
- **Historical Data Accuracy**: Fixed trend analysis to use consistent units for accurate meteorological predictions

### Changes

- Enhanced meteorological algorithms to work seamlessly with both metric and imperial sensor data
- Improved forecast accuracy by using real wind speed data instead of condition-based estimates
- Better handling of mixed sensor environments

## 1.3.3 (2025-09-23)

### Bug Fixes

- **Nighttime Weather Detection**: Fixed false cloudy detection on clear nights with low pressure
  - Improved nighttime condition logic to consider humidity levels alongside pressure
  - Low pressure (< 29.80 inHg) no longer automatically triggers cloudy conditions
  - Added nuanced conditions: clear-night for low pressure + low humidity (< 65%), cloudy for high humidity (> 85%)
  - Fixes issue where clear nights were incorrectly reported as cloudy due to atmospheric pressure alone
  - Applied consistent logic to both weather_detector.py and weather_analysis.py

### Changes

- Enhanced meteorological accuracy for nighttime weather conditions
- Better handling of low-pressure systems with clear skies

## 1.3.2 (2025-09-22)

### Bug Fixes

- **Sensor Value Conversion**: Fixed logging syntax for sensor conversion errors to properly display entity IDs and values
- **Improved Error Handling**: Added validation for None/empty sensor states before conversion attempts
- **Better Logging**: Enhanced error messages for sun sensor elevation data processing

### Changes

- Improved sensor state validation to reduce spurious warning messages
- Enhanced error handling for invalid sensor data

## 1.3.1 (2025-09-22)

### Features

- **Solar Radiation Averaging**: Implemented 15-minute moving average for solar radiation readings to prevent rapid weather condition changes
  - Reduces false weather transitions caused by temporary cloud shadows or sensor noise
  - Provides more stable and reliable cloud cover detection
  - Improves overall weather condition accuracy and user experience
  - Configurable averaging window for optimal performance

### Changes

- Enhanced HACS validation workflow with scheduled runs and manual dispatch
- Added hassfest integration validation for improved Home Assistant compatibility
- Updated CI/CD pipeline for better automated testing and validation

## 1.3.0 (2025-09-22)

### Features

- **Solar Elevation Integration**: Added sun sensor support for precise cloud cover calculations based on solar position
  - New optional sun sensor configuration field for solar elevation data
  - Enhanced cloud cover analysis using solar elevation angle for more accurate daytime weather detection
  - Improved weather condition accuracy throughout the day by accounting for sun position
  - Fallback to 45° elevation when sun sensor not configured
  - Added comprehensive translations for sun sensor in all supported languages (English, German, Spanish, French, Italian)

## 1.2.0 (2025-09-22)

### Bug Fixes

- **Fixed Rain State Logic**: Corrected rain_state sensor handling to only recognize valid moisture sensor values ("wet" or "dry")
  - Removed invalid rain_state values: "rain", "drizzle", "precipitation" which are not supported by binary moisture sensors
  - Updated both weather_analysis.py and weather_detector.py to use proper boolean moisture sensor logic
  - Fixed test cases to use correct "Wet" state instead of invalid "Rain" state
- **Enhanced Fog Detection**: Significantly improved fog vs precipitation detection when moisture sensor shows "wet"
  - Added intelligent two-stage detection: checks for fog conditions first when rain_state="wet" but rain_rate is low
  - Prevents false precipitation alerts when fog causes moisture sensor to read "wet"
  - Maintains accurate precipitation detection while enabling proper fog identification
  - Addresses real-world scenario where fog moisture triggers wet sensor but shouldn't be classified as rain

### Technical Improvements

- **Smart Moisture Analysis**: Implemented sophisticated logic to distinguish between precipitation moisture and fog moisture
- **Priority-Based Detection**: Enhanced the weather detection algorithm priority system to handle ambiguous wet sensor readings
- **Test Coverage**: Updated test suite to validate fog vs precipitation scenarios with comprehensive edge case testing
- **Code Quality**: Improved comments and documentation for moisture sensor handling logic

### Breaking Changes

- None - all changes are backward compatible and improve accuracy of existing functionality

## 1.1.0 (2025-09-21)

### Features

- **Major Code Refactoring**: Split monolithic weather_detector.py (~1300 lines) into focused, maintainable modules
- **Modular Architecture**: Improved code organization with separate concerns:
  - `weather_utils.py`: Unit conversion functions (Celsius, hPa, km/h)
  - `weather_analysis.py`: Meteorological algorithms and trend analysis
  - `weather_forecast.py`: Advanced forecasting with historical patterns
  - `weather_detector.py`: Core integration and orchestration (refactored)
- **Enhanced Test Coverage**: Comprehensive test suites for each module (64 total tests)
- **Improved Maintainability**: Better separation of concerns and code reusability
- **Future-Ready Architecture**: Easier to extend with new features and algorithms

### Technical Improvements

- **Code Quality**: All pre-commit hooks pass (black, isort, flake8)
- **Test Organization**: Split monolithic test file into focused test modules matching the new architecture
- **Performance**: Maintained all original functionality while improving code structure
- **Documentation**: Updated code documentation and module organization
- **Backward Compatibility**: All existing functionality preserved

### Bug Fixes

- Fixed test entity ID mappings to match configuration options
- Corrected forecast temperature bounds and expectations
- Resolved precipitation test logic and seasonal adjustment types
- Fixed unit conversion precision expectations in tests

## 1.0.0 (2025-09-19)

### Features

- Initial release of Micro Weather Station integration
- Weather entity with intelligent condition detection based on real sensor data
- Individual sensor entities that relay data from your configured weather sensors
- Priority-based weather detection algorithm using precipitation, wind, solar radiation, and environmental data
- Support for multiple weather conditions (sunny, cloudy, partly cloudy, rainy, snowy, stormy, foggy)
- Intelligent weather condition detection using your existing sensor infrastructure
- HACS compatibility with proper manifest and structure
- Configuration flow for sensor entity selection through Home Assistant UI
- Options flow for modifying sensor mappings after setup
- Comprehensive documentation and automation examples
- MIT license for open source distribution

### Technical Details

- Built following Home Assistant integration best practices
- Uses DataUpdateCoordinator for efficient sensor data management
- Implements proper async/await patterns for sensor state reading
- Includes comprehensive logging for debugging
- Supports both weather entity and individual sensor entities
- Weather conditions update based on real-time sensor data analysis
- Data updates every 30 seconds by default (configurable)
- Includes proper device information for device registry
- Supports translations and internationalization
- Compatible with Home Assistant 2023.1+
- Handles unit conversions and data validation for sensor inputs
