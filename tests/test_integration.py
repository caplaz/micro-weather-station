"""Integration tests for Micro Weather Station setup and unload flows."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SUNNY,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.micro_weather import (
    MicroWeatherCoordinator,
    async_setup_entry,
    async_unload_entry,
    async_update_options,
)
from custom_components.micro_weather.const import DOMAIN


@pytest.mark.integration
class TestIntegrationSetup:
    """Test integration setup and unload flows."""

    async def test_async_setup_entry_success(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test successful setup of the integration."""
        # Mock the weather detector to return valid data
        mock_weather_data = {
            "condition": ATTR_CONDITION_SUNNY,
            "temperature": 22.5,
            "humidity": 65.0,
            "pressure": 1013.25,
            "wind_speed": 5.2,
            "wind_direction": 180.0,
            "visibility": 10.0,
        }

        with (
            patch(
                "custom_components.micro_weather.weather_detector.WeatherDetector"
            ) as mock_detector_class,
            patch(
                "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
            ) as mock_forward,
        ):
            mock_detector = MagicMock()
            mock_detector.get_weather_data.return_value = mock_weather_data
            mock_detector_class.return_value = mock_detector

            # Setup the entry
            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            assert DOMAIN in hass.data
            assert mock_config_entry.entry_id in hass.data[DOMAIN]

            # Check coordinator was created and stored
            coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
            assert isinstance(coordinator, MicroWeatherCoordinator)

            # Verify platform setup was called
            mock_forward.assert_called_once_with(mock_config_entry, ["weather"])

    async def test_async_setup_entry_coordinator_refresh_failure(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test setup failure when coordinator refresh fails."""
        from homeassistant.exceptions import ConfigEntryNotReady

        with patch(
            "custom_components.micro_weather.weather_detector.WeatherDetector"
        ) as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector.get_weather_data.side_effect = Exception("Sensor unavailable")
            mock_detector_class.return_value = mock_detector

            # Setup should fail when initial refresh fails
            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, mock_config_entry)

    async def test_async_unload_entry_success(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test successful unload of the integration."""
        # First set up the integration
        mock_weather_data = {"condition": ATTR_CONDITION_CLOUDY, "temperature": 20.0}

        with (
            patch(
                "custom_components.micro_weather.weather_detector.WeatherDetector"
            ) as mock_detector_class,
            patch(
                "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
            ),
            patch(
                "homeassistant.config_entries.ConfigEntries.async_unload_platforms"
            ) as mock_unload,
        ):
            mock_detector = MagicMock()
            mock_detector.get_weather_data.return_value = mock_weather_data
            mock_detector_class.return_value = mock_detector

            # Setup first
            await async_setup_entry(hass, mock_config_entry)
            mock_unload.reset_mock()

            # Mock successful platform unload
            mock_unload.return_value = True

            # Now test unload
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            mock_unload.assert_called_once_with(mock_config_entry, ["weather"])

            # Check data was cleaned up
            assert mock_config_entry.entry_id not in hass.data[DOMAIN]

    async def test_async_unload_entry_platform_unload_failure(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test unload failure when platform unload fails."""
        # First set up the integration
        mock_weather_data = {"condition": ATTR_CONDITION_RAINY, "temperature": 18.0}

        with (
            patch(
                "custom_components.micro_weather.weather_detector.WeatherDetector"
            ) as mock_detector_class,
            patch(
                "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
            ),
            patch(
                "homeassistant.config_entries.ConfigEntries.async_unload_platforms"
            ) as mock_unload,
        ):
            mock_detector = MagicMock()
            mock_detector.get_weather_data.return_value = mock_weather_data
            mock_detector_class.return_value = mock_detector

            # Setup first
            await async_setup_entry(hass, mock_config_entry)

            # Mock platform unload failure
            mock_unload.return_value = False

            # Test unload
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is False
            # Data should NOT be cleaned up when platform unload fails
            assert mock_config_entry.entry_id in hass.data[DOMAIN]

    async def test_async_update_options(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test options update triggers coordinator refresh."""
        # First set up the integration
        mock_weather_data = {"condition": ATTR_CONDITION_SUNNY, "temperature": 25.0}

        with (
            patch(
                "custom_components.micro_weather.weather_detector.WeatherDetector"
            ) as mock_detector_class,
            patch(
                "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
            ),
        ):
            mock_detector = MagicMock()
            mock_detector.get_weather_data.return_value = mock_weather_data
            mock_detector_class.return_value = mock_detector

            # Setup first
            await async_setup_entry(hass, mock_config_entry)

            coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
            coordinator.async_request_refresh = AsyncMock()

            # Update options
            await async_update_options(hass, mock_config_entry)

            # Verify refresh was called
            coordinator.async_request_refresh.assert_called_once()


@pytest.mark.integration
class TestCoordinatorIntegration:
    """Test the MicroWeatherCoordinator integration."""

    async def test_coordinator_update_success(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test successful data update by coordinator."""
        mock_weather_data = {
            "condition": ATTR_CONDITION_PARTLYCLOUDY,
            "temperature": 23.5,
            "humidity": 70.0,
            "pressure": 1015.0,
            "wind_speed": 3.2,
            "forecast": [
                {
                    "datetime": "2025-09-30T12:00:00",
                    "temperature": 24.0,
                    "templow": 18.0,
                    "condition": ATTR_CONDITION_SUNNY,
                    "precipitation": 0.0,
                    "wind_speed": 4.0,
                    "humidity": 65.0,
                }
            ],
        }

        with patch(
            "custom_components.micro_weather.weather_detector.WeatherDetector"
        ) as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector.get_weather_data.return_value = mock_weather_data
            mock_detector_class.return_value = mock_detector

            coordinator = MicroWeatherCoordinator(hass, mock_config_entry)

            # Test update
            result = await coordinator._async_update_data()

            assert result == mock_weather_data
            mock_detector_class.assert_called_once_with(hass, mock_config_entry.options)

    async def test_coordinator_update_failure(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test coordinator handles update failures gracefully."""
        with patch(
            "custom_components.micro_weather.weather_detector.WeatherDetector"
        ) as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector.get_weather_data.side_effect = ValueError(
                "Invalid sensor data"
            )
            mock_detector_class.return_value = mock_detector

            coordinator = MicroWeatherCoordinator(hass, mock_config_entry)

            # Test update failure
            with pytest.raises(UpdateFailed, match="Failed to update weather data"):
                await coordinator._async_update_data()

    async def test_coordinator_initialization(
        self, hass: HomeAssistant, mock_config_entry: MockConfigEntry
    ):
        """Test coordinator initialization with proper config."""
        coordinator = MicroWeatherCoordinator(hass, mock_config_entry)

        assert coordinator.entry == mock_config_entry
        assert coordinator.name == DOMAIN
        assert coordinator.update_interval is not None  # Should be set to 5 minutes
        assert coordinator.hass == hass
