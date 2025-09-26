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
