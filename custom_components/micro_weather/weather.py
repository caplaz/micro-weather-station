"""Weather entity for Micro Weather Station."""

import logging

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
    Forecast,
    WeatherEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .version import __version__

_LOGGER = logging.getLogger(__name__)

# Map our conditions to HA weather conditions
CONDITION_MAP = {
    "sunny": ATTR_CONDITION_SUNNY,
    "cloudy": ATTR_CONDITION_CLOUDY,
    "partly_cloudy": ATTR_CONDITION_PARTLYCLOUDY,
    "rainy": ATTR_CONDITION_RAINY,
    "snowy": ATTR_CONDITION_SNOWY,
    "stormy": ATTR_CONDITION_LIGHTNING_RAINY,
    "foggy": ATTR_CONDITION_FOG,
    "clear-night": ATTR_CONDITION_SUNNY,  # Clear night maps to sunny
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Micro Weather Station weather entity."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([MicroWeatherEntity(coordinator, config_entry)])


class MicroWeatherEntity(CoordinatorEntity, WeatherEntity):
    """Micro Weather Station weather entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = 3  # FORECAST_DAILY | FORECAST_HOURLY
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
            "sw_version": __version__,
        }
        # Set initial state to unavailable until we have data
        self._attr_available = bool(coordinator.data)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(self.coordinator.data)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        # Trigger immediate refresh when entity is first added
        # This ensures data is available quickly after HA restart
        if not self.coordinator.data:
            await self.coordinator.async_request_refresh()

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        if self.coordinator.data:
            condition = self.coordinator.data.get("condition")
            return CONDITION_MAP.get(condition, condition)
        # Return None until we have data - don't show default partly cloudy
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

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        if self.coordinator.data and "forecast" in self.coordinator.data:
            forecast_data = []
            for day_data in self.coordinator.data["forecast"]:
                forecast_data.append(
                    {
                        "datetime": day_data["datetime"],
                        "native_temperature": day_data["temperature"],
                        "native_templow": day_data["templow"],
                        "condition": CONDITION_MAP.get(
                            day_data["condition"], day_data["condition"]
                        ),
                        "native_precipitation": day_data.get("precipitation", 0),
                        "native_wind_speed": day_data.get("wind_speed", 0),
                        "humidity": day_data.get("humidity", 50),
                    }
                )
            return forecast_data
        return None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast."""
        if not self.coordinator.data:
            return None

        # Generate hourly forecast for next 24 hours based on current conditions
        hourly_data = []
        current_temp = self.coordinator.data.get("temperature", 20)
        current_condition = self.coordinator.data.get("condition", "cloudy")
        current_humidity = self.coordinator.data.get("humidity", 50)
        current_wind = self.coordinator.data.get("wind_speed", 5)

        for i in range(24):  # 24 hours
            from datetime import datetime, timedelta

            hour_time = datetime.now() + timedelta(hours=i + 1)

            # Simple hourly temperature variation (diurnal cycle)
            if 6 <= hour_time.hour <= 18:  # Daytime
                temp_variation = 2 * (1 - abs(hour_time.hour - 12) / 6)  # Peak at noon
            else:  # Nighttime
                temp_variation = -2

            # Condition persistence with some hourly variation
            if i < 6:  # Next 6 hours - current condition persists
                hour_condition = current_condition
            elif i < 12:  # 6-12 hours - slight variation
                hour_condition = current_condition if i % 3 != 0 else "partly_cloudy"
            else:  # 12-24 hours - more variation
                hour_condition = ["partly_cloudy", "cloudy", current_condition][i % 3]

            hourly_data.append(
                {
                    "datetime": hour_time.isoformat(),
                    "native_temperature": round(current_temp + temp_variation, 1),
                    "condition": CONDITION_MAP.get(hour_condition, hour_condition),
                    "native_precipitation": (
                        2.0 if hour_condition in ["rainy", "stormy"] else 0.0
                    ),
                    "native_wind_speed": max(1, current_wind + (i * 0.1)),
                    "humidity": max(30, min(90, current_humidity + (i * 0.5))),
                }
            )

        return hourly_data
