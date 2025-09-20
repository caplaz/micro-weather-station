"""Sensor entities for Virtual Weather Station."""
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Virtual Weather Station sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = []
    for sensor_type in SENSOR_TYPES:
        sensors.append(VirtualWeatherSensor(coordinator, config_entry, sensor_type))
    
    async_add_entities(sensors)


class VirtualWeatherSensor(CoordinatorEntity, SensorEntity):
    """Virtual Weather Station sensor entity."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config_entry, sensor_type):
        """Initialize the sensor entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._sensor_config = SENSOR_TYPES[sensor_type]
        
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_name = self._sensor_config["name"]
        self._attr_native_unit_of_measurement = self._sensor_config["unit"]
        self._attr_icon = self._sensor_config["icon"]
        
        # Set device class if available
        if "device_class" in self._sensor_config:
            self._attr_device_class = getattr(
                SensorDeviceClass, 
                self._sensor_config["device_class"].upper(), 
                None
            )
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Virtual Weather Station",
            "manufacturer": "Virtual Weather",
            "model": "VWS-1",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._sensor_type)
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success