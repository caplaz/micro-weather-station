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
