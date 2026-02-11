"""Water Heater platform for acond."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.water_heater import (
    STATE_HEAT_PUMP,
    WaterHeaterEntity,
    WaterHeaterEntityDescription,
    WaterHeaterEntityFeature,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    STATE_OFF,
    UnitOfTemperature,
)

from .const import ACOND_ACONOMIS_DATA_MAPPINGS, AcondRegulationMode
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
            AcondHeatingWaterHeater(
                coordinator=entry.runtime_data.coordinator,
            ),
        )
    )


class AcondHeatingWaterHeater(AcondEntity, WaterHeaterEntity):
    """Acond Heating Water Heater class."""

    def __init__(
        self,
        coordinator: AcondDataUpdateCoordinator,
    ) -> None:
        """Initialize the water heater class."""
        super().__init__(coordinator)
        self._attr_unique_id = "heating_water_heater"
        self._attr_name = "Heating Water Heater"
        self._attr_icon = "mdi:heating-coil"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = 20
        self._attr_max_temp = 60

    @property
    def supported_features(self) -> WaterHeaterEntityFeature:
        """Return the list of supported features."""
        features = super().supported_features

        if self.coordinator.get_regulation_mode() == AcondRegulationMode.MANUALLY:
            features |= WaterHeaterEntityFeature.TARGET_TEMPERATURE

        return features

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data.get(
            ACOND_ACONOMIS_DATA_MAPPINGS["INLET_TEMPERATURE"]
        )

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        key = (
            ACOND_ACONOMIS_DATA_MAPPINGS["MANUAL_TARGET_RETURN_WATER_TEMPERATURE"]
            if self.coordinator.get_regulation_mode() == AcondRegulationMode.MANUALLY
            else ACOND_ACONOMIS_DATA_MAPPINGS[
                "EQUITHERM_TARGET_RETURN_WATER_TEMPERATURE"
            ]
        )

        return self.coordinator.data.get(key)

    @property
    def current_operation(self):
        """Return current operation ie. on, off."""
        compressor_active = self.coordinator.is_compressor_active()
        dhw_active = self.coordinator.is_dhw_active()

        return STATE_HEAT_PUMP if compressor_active and not dhw_active else STATE_OFF

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return [STATE_OFF, STATE_HEAT_PUMP]

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        # TODO
        # if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
        #    await self.coordinator.config_entry.runtime_data.client.async_set_dhw_temperature(
        #        temperature
        #    )


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
