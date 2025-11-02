# Micro Weather Station - Development Setup

This directory contains a Docker-based development environment for testing the Micro Weather Station Home Assistant integration.

## Prerequisites

- Docker and Docker Compose installed
- Git

## Quick Start

1. **Clone and setup the project:**

   ```bash
   git clone <repository-url>
   cd micro-weather-station
   ```

2. **Start the development environment:**

   ```bash
   docker-compose up -d
   ```

3. **Access Home Assistant:**

   - Open your browser to `http://localhost:8123`
   - Complete the initial setup wizard
   - The integration will be automatically available

4. **Monitor logs:**
   ```bash
   docker-compose logs -f homeassistant
   ```

## Development Workflow

### Making Code Changes

1. Edit the integration code in `custom_components/micro_weather/`
2. Restart Home Assistant to reload the integration:
   ```bash
   docker-compose restart homeassistant
   ```
3. Check the logs for any errors:
   ```bash
   docker-compose logs homeassistant
   ```

### Testing the Integration

The development environment includes sample sensors that provide realistic weather data:

- **Temperature**: Varies throughout the day (simulates diurnal cycle)
- **Humidity**: Fluctuates between 40-70%
- **Pressure**: Atmospheric pressure with small variations
- **Wind**: Speed and direction that change over time
- **Rain**: Occasional rain events every 15 minutes
- **Solar**: Radiation based on time of day

### Configuration

The integration is pre-configured in `config/configuration.yaml` with:

- Altitude: 350m (to test altitude correction)
- Pressure type: atmospheric
- All required sensors mapped to template sensors

### Debugging

Enable debug logging by adding to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.micro_weather: debug
```

## Available Services

### Docker Services

- **homeassistant**: Home Assistant development instance on port 8123

### Useful Commands

```bash
# Start development environment
docker-compose up -d

# Stop development environment
docker-compose down

# Restart Home Assistant
docker-compose restart homeassistant

# View logs
docker-compose logs -f homeassistant

# Execute commands in the container
docker-compose exec homeassistant bash

# Clean up (remove containers and volumes)
docker-compose down -v
```

## Integration Testing

Once Home Assistant is running:

1. Go to **Settings > Devices & Services**
2. Look for "Micro Weather Station" in the discovered integrations
3. Configure the integration (sensors are pre-mapped)
4. Check the weather card on your dashboard
5. Monitor the logs for altitude correction in action

## Troubleshooting

### Common Issues

1. **Integration not loading**: Check that `custom_components/micro_weather/` is properly mounted
2. **Sensors not found**: Ensure the template sensors are working in Developer Tools > Template
3. **Permission errors**: Make sure Docker has access to the project directory

### Resetting the Environment

To completely reset the development environment:

```bash
docker-compose down -v
rm -rf config/.storage config/.uuid
docker-compose up -d
```

This will give you a fresh Home Assistant installation.

## Architecture

### Modular Structure

The integration uses a modular architecture organized into specialized components for maintainability and extensibility:

```
custom_components/micro_weather/
├── __init__.py                    # Integration entry point
├── config_flow.py                 # Configuration UI
├── const.py                       # Constants and keys
├── meteorological_constants.py    # Scientific thresholds
├── sensor.py                      # Sensor platform
├── weather.py                     # Weather platform
├── weather_detector.py            # Main weather detection orchestration
├── weather_analysis.py            # Analysis coordination (facade)
├── weather_forecast.py            # Forecast coordination (facade)
├── weather_utils.py               # Utility functions
│
├── analysis/                      # Weather Analysis Modules
│   ├── __init__.py
│   ├── core.py                    # Core weather condition determination
│   ├── atmospheric.py             # Pressure and fog analysis
│   ├── solar.py                   # Solar radiation and cloud cover
│   └── trends.py                  # Historical data trends
│
└── forecast/                      # Forecast Generation Modules
    ├── __init__.py
    ├── meteorological.py          # Meteorological state analysis
    ├── patterns.py                # Historical pattern recognition
    ├── evolution.py               # Weather system evolution modeling
    ├── astronomical.py            # Astronomical calculations
    ├── daily.py                   # 5-day forecast generation
    └── hourly.py                  # 24-hour forecast generation
```

### Weather Analysis Modules

The analysis system is organized into specialized modules, each responsible for a specific aspect of weather condition determination:

#### **analysis/core.py - Core Weather Conditions**

Determines primary weather conditions using a sophisticated priority system:

- **Priority-based condition detection**: Hierarchical analysis of all weather factors
- **Precipitation analysis**: Rain rate and moisture sensor evaluation
- **Dewpoint calculations**: Magnus formula implementation with fallback support
- **Visibility estimation**: Fog and precipitation effects on visibility
- **Condition mapping**: Translation of analyzed data to Home Assistant weather states

#### **analysis/atmospheric.py - Atmospheric Analysis**

Analyzes atmospheric conditions and pressure systems:

- **Pressure altitude corrections**: Sea level pressure calculations using hypsometric equation
- **Fog condition detection**: Multi-factor fog scoring using humidity, dewpoint, and solar data
- **Pressure trend analysis**: 3-hour and long-term pressure change detection
- **Wind direction analysis**: Circular statistics for wind direction trends and stability
- **Storm probability**: Pressure-based storm prediction algorithms

#### **analysis/solar.py - Solar Radiation Analysis**

Processes solar data to determine cloud cover and sky conditions:

- **Cloud cover estimation**: Solar radiation analysis against clear-sky models
- **Clear-sky radiation calculations**: Theoretical maximum solar radiation for current sun position
- **Astronomical calculations**: Solar elevation, air mass, and solar constant variation
- **Historical weather bias**: Adaptive algorithms that learn from local weather patterns
- **Low-elevation adjustments**: Enhanced accuracy during sunrise and sunset

#### **analysis/trends.py - Historical Data Analysis**

Manages historical weather data and trend detection:

- **Historical data storage**: Circular buffer of sensor readings with automatic pruning
- **Trend calculation**: Linear regression analysis of temperature, pressure, and humidity
- **Pattern recognition**: Detection of recurring weather patterns and cycles
- **Circular statistics**: Specialized handling of wind direction (0-360° wrap-around)
- **Volatility analysis**: Measurement of weather parameter variability

### Forecast Generation Modules

The forecast system is organized into specialized modules that provide the foundation for future enhancements. Currently, the main forecasting logic is implemented in `weather_forecast.py`, with the modules serving as the architectural framework:

#### **forecast/meteorological.py - Meteorological State Analysis**

Framework for comprehensive meteorological state analysis:

- **Multi-factor analysis**: Integration of pressure, wind, temperature, and humidity data
- **Atmospheric stability index**: Calculation of air mass stability (0-1 scale)
- **Weather system classification**: Categorization of current weather patterns
- **Cloud cover analysis**: Comprehensive solar data integration with pressure trends
- **Moisture transport analysis**: Humidity dynamics and condensation potential

#### **forecast/patterns.py - Historical Pattern Recognition**

Framework for pattern analysis from historical weather data:

- **Seasonal factors**: Month-based temperature variation patterns
- **Pressure cycle detection**: Identification of weather system frequencies
- **Correlation analysis**: Temperature-pressure and temperature-humidity relationships
- **Pattern-based predictions**: Use of historical patterns to improve forecast accuracy

#### **forecast/evolution.py - Weather System Evolution**

Framework for modeling how weather systems evolve over time:

- **System evolution paths**: Prediction of weather system transitions
- **Confidence levels**: Time-dependent forecast reliability assessment
- **Transition probabilities**: Likelihood of changes in weather conditions
- **Persistence factors**: Measurement of weather pattern stability

#### **forecast/astronomical.py - Astronomical Calculations**

Handles solar position and diurnal cycle calculations:

- **Solar elevation**: Sun position calculations for any forecast time
- **Sunrise/sunset timing**: Precise day/night boundary determination
- **Diurnal temperature variation**: Natural temperature cycles throughout the day
- **Seasonal adjustments**: Yearly variation in solar radiation and day length

#### **forecast/daily.py - 5-Day Forecast Generation**

Framework for detailed 5-day daily forecasts:

- **Temperature forecasting**: Multi-factor analysis including seasonal patterns
- **Condition forecasting**: Priority system considering pressure, clouds, and evolution
- **Precipitation probability**: Humidity and pressure-based rain predictions
- **Wind forecasting**: Pressure gradient and system evolution analysis
- **Confidence dampening**: Accuracy decreases with forecast distance

#### **forecast/hourly.py - 24-Hour Forecast Generation**

Framework for detailed hourly forecasts for the next 24 hours:

- **Micro-evolution modeling**: Hour-by-hour weather system changes
- **Diurnal temperature cycles**: Natural warming and cooling patterns
- **Astronomical integration**: Day/night transitions and solar effects
- **Cloud evolution**: Hour-by-hour cloud cover changes
- **High-frequency updates**: Detailed short-term predictions

**Note**: The forecast modules currently provide the architectural structure, with the full implementation residing in `weather_forecast.py`. This modular organization allows for future expansion where functionality can be migrated into specialized modules as needed.

### Architecture Design

The integration uses a **facade pattern** where coordination modules (`weather_analysis.py` and `weather_forecast.py`) provide a simple interface to the complex specialized subsystems. This approach offers several benefits:

### Key Design Principles

1. **Single Responsibility**: Each module handles one specific aspect of weather analysis or forecasting
2. **Separation of Concerns**: Analysis and forecasting are cleanly separated into dedicated subsystems
3. **Dependency Injection**: Modules receive their dependencies through constructors
4. **Composition over Inheritance**: Components are composed rather than using deep inheritance hierarchies
5. **Facade Pattern**: Coordination modules provide simple interfaces to complex subsystems

### Working with the Architecture

#### Modifying Weather Analysis

To change how weather conditions are determined, edit the relevant analysis module:

**Core weather logic** (`analysis/core.py`):

```python
from .analysis.core import WeatherConditionAnalyzer
# Modify priority-based condition detection, precipitation analysis
```

**Atmospheric conditions** (`analysis/atmospheric.py`):

```python
from .analysis.atmospheric import AtmosphericAnalyzer
# Modify pressure corrections, fog detection, storm probability
```

**Cloud cover analysis** (`analysis/solar.py`):

```python
from .analysis.solar import SolarAnalyzer
# Modify cloud cover algorithms, clear-sky calculations
```

**Historical trends** (`analysis/trends.py`):

```python
from .analysis.trends import TrendsAnalyzer
# Modify trend calculations, pattern recognition
```

#### Modifying Forecast Generation

To change how forecasts are generated, edit the relevant forecast module:

**Meteorological analysis** (`forecast/meteorological.py`):

```python
from .forecast import MeteorologicalAnalyzer
# Modify atmospheric stability, weather system classification
```

**Pattern recognition** (`forecast/patterns.py`):

```python
from .forecast import PatternAnalyzer
# Modify seasonal factors, pressure cycles, correlations
```

**System evolution** (`forecast/evolution.py`):

```python
from .forecast import EvolutionModeler
# Modify weather system transition modeling
```

**Astronomical calculations** (`forecast/astronomical.py`):

```python
from .forecast import AstronomicalCalculator
# Modify solar position, diurnal variations
```

**Daily forecasts** (`forecast/daily.py`):

```python
from .forecast import DailyForecastGenerator
# Modify 5-day forecast algorithms
```

**Hourly forecasts** (`forecast/hourly.py`):

```python
from .forecast import HourlyForecastGenerator
# Modify 24-hour forecast algorithms
```

The facade modules (`weather_analysis.py` and `weather_forecast.py`) automatically coordinate calls to the appropriate specialized modules.

### Testing

The integration includes comprehensive test coverage:

- **Unit tests**: Test individual analyzer and generator modules
- **Integration tests**: Test full weather detection and forecasting workflows
- **Config flow tests**: Test configuration UI and validation
- **Validation tests**: Test constants and component structure

Run tests with:

```bash
python -m pytest tests/
```

Current test status: 246/368 tests passing (66.8% coverage)
