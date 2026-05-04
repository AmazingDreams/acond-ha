"""Water Heater platform for acond."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.water_heater import (
    STATE_HEAT_PUMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    STATE_OFF,
    UnitOfTemperature,
)

from .const import ACOND_ACONOMIS_DATA_MAPPINGS
from .data import AcondConfigEntry
from .entity import AcondEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import AcondDataUpdateCoordinator
    from .data import AcondConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: AcondConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        (
            AcondDomesticHotWaterHeater(
                coordinator=entry.runtime_data.coordinator,
            ),
        )
    )


class AcondDomesticHotWaterHeater(AcondEntity, WaterHeaterEntity):
    """Acond Domestic Hot Water Heater class."""

    def __init__(
        self,
        coordinator: AcondDataUpdateCoordinator,
    ) -> None:
        """Initialize the water heater class."""
        super().__init__(coordinator)
        self._attr_unique_id = "domestic_hot_water_heater"
        self._attr_name = "Domestic Hot Water Heater"
        self._attr_icon = "mdi:water-boiler"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = WaterHeaterEntityFeature.TARGET_TEMPERATURE
        self._attr_min_temp = 10
        self._attr_max_temp = 56

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data.get(
            ACOND_ACONOMIS_DATA_MAPPINGS["DHW_TEMPERATURE"]
        )

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self.coordinator.data.get(
            ACOND_ACONOMIS_DATA_MAPPINGS["DHW_TEMPERATURE_REQUIRED"]
        )

    @property
    def current_operation(self):
        """Return current operation ie. on, off."""
        dhw_active = self.coordinator.is_dhw_active()
        return STATE_HEAT_PUMP if dhw_active else STATE_OFF

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return [STATE_OFF, STATE_HEAT_PUMP]

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self.coordinator.config_entry.runtime_data.client.async_set_dhw_temperature(
                temperature
            )
