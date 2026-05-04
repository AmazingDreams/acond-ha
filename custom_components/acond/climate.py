"""Climate platform for acond."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .const import ACOND_ACONOMIS_DATA_MAPPINGS, AcondOperatingMode, AcondRegulationMode
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
    """Set up the climate platform."""
    async_add_entities(
        (
            AcondHeatingWaterHeater(
                coordinator=entry.runtime_data.coordinator,
            ),
        )
    )


class AcondHeatingWaterHeater(AcondEntity, ClimateEntity):
    """Acond Heating Water Heater climate entity."""

    def __init__(
        self,
        coordinator: AcondDataUpdateCoordinator,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._attr_unique_id = "heating_water_heater"
        self._attr_name = "Heating Water Heater"
        self._attr_icon = "mdi:heating-coil"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = 10
        self._attr_max_temp = 60
        self._attr_hvac_mode = HVACMode.AUTO
        self._attr_hvac_modes = [
            HVACMode.AUTO,
        ]

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        features = super().supported_features

        if (
            self.coordinator.get_regulation_mode() == AcondRegulationMode.MANUALLY
            or self.coordinator.get_operating_mode() == AcondOperatingMode.COOLING
        ):
            features |= ClimateEntityFeature.TARGET_TEMPERATURE

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
        if self.coordinator.get_operating_mode() == AcondOperatingMode.COOLING:
            return self.coordinator.data.get(
                ACOND_ACONOMIS_DATA_MAPPINGS[
                    "MANUAL_TARGET_RETURN_WATER_COOLING_TEMPERATURE"
                ]
            )

        key = (
            ACOND_ACONOMIS_DATA_MAPPINGS["MANUAL_TARGET_RETURN_WATER_TEMPERATURE"]
            if self.coordinator.get_regulation_mode() == AcondRegulationMode.MANUALLY
            else ACOND_ACONOMIS_DATA_MAPPINGS[
                "EQUITHERM_TARGET_RETURN_WATER_TEMPERATURE"
            ]
        )

        return self.coordinator.data.get(key)

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current HVAC action."""
        compressor_active = self.coordinator.is_compressor_active()
        dhw_active = self.coordinator.is_dhw_active()

        if compressor_active and not dhw_active:
            return (
                HVACAction.COOLING
                if self.coordinator.get_operating_mode() == AcondOperatingMode.COOLING
                else HVACAction.HEATING
            )

        return HVACAction.OFF

    def set_hvac_mode(self, hvac_mode) -> None:
        """Set new target hvac mode."""
        # Managed by heat pump - do not allow manual control of HVAC mode

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            if self.coordinator.get_operating_mode() == AcondOperatingMode.COOLING:
                await self.coordinator.config_entry.runtime_data.client.async_set_cooling_temperature(
                    temperature
                )
            else:
                await self.coordinator.config_entry.runtime_data.client.async_set_heating_temperature(
                    temperature
                )
