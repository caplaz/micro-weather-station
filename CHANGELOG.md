## 1.0.0 (2025-09-19)

### Features

- Initial release of Smart Weather Station integration
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
