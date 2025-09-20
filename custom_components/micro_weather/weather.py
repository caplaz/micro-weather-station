"""Weather entity for Micro Weather Station."""
import logging
from typing import Any

from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    ATTR_CONDITION_CLEAR,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_FOG,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Map our conditions to HA weather conditions
CONDITION_MAP = {
    "sunny": ATTR_CONDITION_CLEAR,
    "cloudy": ATTR_CONDITION_CLOUDY,
    "partly_cloudy": ATTR_CONDITION_PARTLYCLOUDY,
    "rainy": ATTR_CONDITION_RAINY,
    "snowy": ATTR_CONDITION_SNOWY,
    "stormy": ATTR_CONDITION_LIGHTNING_RAINY,
    "foggy": ATTR_CONDITION_FOG,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Micro Weather Station weather entity."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([VirtualWeatherEntity(coordinator, config_entry)])


class VirtualWeatherEntity(CoordinatorEntity, WeatherEntity):
    """Micro Weather Station weather entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY
    )
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS

    def __init__(self, coordinator, config_entry):
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_weather"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Micro Weather Station",
            "manufacturer": "Micro Weather",
            "model": "MWS-1",
            "sw_version": "1.0.0",
        }

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        if self.coordinator.data:
            condition = self.coordinator.data.get("condition")
            return CONDITION_MAP.get(condition, condition)
        return None

    @property
    def native_temperature(self) -> float | None:
        """Return the temperature."""
        if self.coordinator.data:
            return self.coordinator.data.get("temperature")
        return None

    @property
    def humidity(self) -> float | None:
        """Return the humidity."""
        if self.coordinator.data:
            return self.coordinator.data.get("humidity")
        return None

    @property
    def native_pressure(self) -> float | None:
        """Return the pressure."""
        if self.coordinator.data:
            return self.coordinator.data.get("pressure")
        return None

    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        if self.coordinator.data:
            return self.coordinator.data.get("wind_speed")
        return None

    @property
    def wind_bearing(self) -> float | None:
        """Return the wind bearing."""
        if self.coordinator.data:
            return self.coordinator.data.get("wind_direction")
        return None

    @property
    def native_visibility(self) -> float | None:
        """Return the visibility."""
        if self.coordinator.data:
            return self.coordinator.data.get("visibility")
        return None

    async def async_forecast_daily(self) -> list[dict[str, Any]] | None:
        """Return the daily forecast."""
        if self.coordinator.data and "forecast" in self.coordinator.data:
            forecast_data = []
            for day_data in self.coordinator.data["forecast"]:
                forecast_data.append({
                    "datetime": day_data["datetime"],
                    "native_temperature": day_data["temperature"],
                    "native_templow": day_data["templow"],
                    "condition": CONDITION_MAP.get(day_data["condition"], day_data["condition"]),
                    "native_precipitation": day_data.get("precipitation", 0),
                    "native_wind_speed": day_data.get("wind_speed", 0),
                })
            return forecast_data
        return None