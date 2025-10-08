# Changelog

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
