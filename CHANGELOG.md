## 1.0.0 (2025-09-19)

### Features

- Initial release of Virtual Weather Station integration
- Weather entity with current conditions and 5-day forecast
- Individual sensor entities for temperature, humidity, pressure, wind speed, wind direction, and visibility
- Configurable weather simulation parameters (temperature range, humidity range, pressure range, wind speed range)
- Support for multiple weather patterns (sunny, cloudy, partly cloudy, rainy, snowy, stormy, foggy)
- Realistic weather data simulation with gradual transitions and continuity
- HACS compatibility with proper manifest and structure
- Configuration flow for easy setup through Home Assistant UI
- Options flow for modifying configuration after setup
- Comprehensive documentation and examples
- MIT license for open source distribution

### Technical Details

- Built following Home Assistant integration best practices
- Uses DataUpdateCoordinator for efficient data management
- Implements proper async/await patterns
- Includes comprehensive logging for debugging
- Supports both weather entity and individual sensor entities
- Weather patterns change automatically every 30 minutes to 2 hours
- Data updates every 5 minutes by default (configurable)
- Includes proper device information for device registry
- Supports translations and internationalization
- Compatible with Home Assistant 2023.1+