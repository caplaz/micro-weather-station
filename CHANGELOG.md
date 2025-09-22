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
