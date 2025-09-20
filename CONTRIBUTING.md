# Developer Guide

## Development Setup

### Prerequisites
- Python 3.11 or higher
- Home Assistant development environment (optional)
- Git

### Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### Code Quality Tools

#### Format Code
```bash
black custom_components/
isort custom_components/
```

#### Lint Code
```bash
flake8 custom_components/
mypy custom_components/
bandit -r custom_components/
```

#### Run Tests
```bash
pytest tests/ -v
pytest tests/ -v --cov=custom_components/micro_weather
```

## Project Structure

```
custom_components/micro_weather/
├── __init__.py              # Integration setup
├── config_flow.py           # UI configuration flow
├── const.py                 # Constants and configuration
├── manifest.json            # Integration manifest
├── sensor.py                # Individual sensor entities
├── strings.json             # UI strings
├── version.py               # Version information
├── weather.py               # Main weather entity
├── weather_detector.py      # Weather detection algorithm
└── translations/
    └── en.json              # English translations

tests/
├── conftest.py              # Test configuration and fixtures
├── test_config_flow.py      # Configuration flow tests
└── test_weather_detector.py # Weather detection algorithm tests

.github/
├── workflows/
│   ├── ci.yml               # Main CI workflow
│   ├── dependencies.yml     # Dependency updates
│   └── release.yml          # Automated releases
├── ISSUE_TEMPLATE/          # GitHub issue templates
└── pull_request_template.md # PR template
```

## Testing

### Running Tests Locally
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components/micro_weather --cov-report=html

# Run specific test file
pytest tests/test_weather_detector.py -v

# Run specific test
pytest tests/test_weather_detector.py::TestWeatherDetector::test_detect_sunny_condition -v
```

### Test Structure
- `conftest.py`: Shared fixtures and test configuration
- `test_weather_detector.py`: Tests for weather detection logic
- `test_config_flow.py`: Tests for UI configuration flow

### Mock Data
Tests use mock sensor data defined in `conftest.py`. Modify the `mock_sensor_data` fixture to test different scenarios.

## CI/CD Workflows

### Main CI Workflow (`.github/workflows/ci.yml`)
Runs on every push and pull request:
- **Code Quality**: Black, isort, flake8, mypy
- **HACS Validation**: Validates integration structure
- **Testing**: Multi-version Python and Home Assistant testing
- **Security**: Bandit security scanning
- **Documentation**: README and manifest validation

### Release Workflow (`.github/workflows/release.yml`)
Triggers on version tags (e.g., `v1.0.0`):
- **Version Validation**: Ensures tag matches manifest.json
- **Release Creation**: Creates GitHub release with assets
- **Archive Generation**: Creates zip and tar.gz files

### Dependency Updates (`.github/workflows/dependencies.yml`)
Runs weekly:
- **HA Version Check**: Monitors new Home Assistant releases
- **Security Scan**: Trivy vulnerability scanning
- **Issue Creation**: Auto-creates update issues

## Release Process

### Creating a New Release

1. **Update Version**:
   ```bash
   # Update version in both files
   vim custom_components/micro_weather/manifest.json
   vim custom_components/micro_weather/version.py
   ```

2. **Update Changelog**:
   ```bash
   vim CHANGELOG.md
   # Add new version section at the top
   ```

3. **Commit Changes**:
   ```bash
   git add -A
   git commit -m "Bump version to X.Y.Z"
   git push
   ```

4. **Create Tag**:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

5. **Release Workflow**: Automatically creates GitHub release

### Version Numbering
Follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes (backward compatible)

## Code Guidelines

### Python Style
- Use [Black](https://black.readthedocs.io/) for code formatting
- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where possible
- Maximum line length: 88 characters

### Import Sorting
Use [isort](https://isort.readthedocs.io/) with Black profile:
```python
# Standard library imports
import logging
from datetime import datetime

# Third-party imports
import voluptuous as vol

# Home Assistant imports
from homeassistant.core import HomeAssistant

# Local imports
from .const import DOMAIN
```

### Documentation
- Add docstrings to all classes and methods
- Use Google-style docstrings
- Update README.md for user-facing changes
- Update CHANGELOG.md for all releases

### Commit Messages
Use conventional commit format:
```
type(scope): description

- feat: new feature
- fix: bug fix
- docs: documentation changes
- style: formatting changes
- refactor: code refactoring
- test: adding tests
- chore: maintenance tasks
```

## Debugging

### Local Development
1. Copy `custom_components/micro_weather` to your HA config directory
2. Restart Home Assistant
3. Add integration through UI
4. Check logs: Settings → System → Logs

### Common Issues
- **Import Errors**: Ensure all dependencies are installed
- **Sensor Not Found**: Check entity IDs in configuration
- **No Data**: Verify sensor entities have valid states
- **Integration Won't Load**: Check Home Assistant logs

### Logging
Add debug logging to your code:
```python
import logging
_LOGGER = logging.getLogger(__name__)

_LOGGER.debug("Debug message")
_LOGGER.info("Info message")
_LOGGER.warning("Warning message")
_LOGGER.error("Error message")
```

Enable debug logging in HA configuration.yaml:
```yaml
logger:
  default: info
  logs:
    custom_components.micro_weather: debug
```