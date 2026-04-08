"""Sensor platform for acond."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory

from .const import (
    ACOND_ACONOMIS_DATA_MAPPINGS,
    AcondOperatingMode,
    AcondRegulationMode,
    AcondSeasonMode,
)
from .data import AcondConfigEntry
from .entity import AcondEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import AcondDataUpdateCoordinator
    from .data import AcondConfigEntry

ACOND_ACONOMIS_ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="REGULATION_MODE",
        name="Regulation Mode",
        icon="mdi:heat-pump",
        device_class=SensorDeviceClass.ENUM,
        options=[
            AcondRegulationMode.MANUALLY,
            AcondRegulationMode.EQUITHERM,
        ],
    ),
    SensorEntityDescription(
        key="OPERATING_MODE",
        name="Operating Mode",
        icon="mdi:heat-pump",
        device_class=SensorDeviceClass.ENUM,
        options=[
            AcondOperatingMode.OFF,
            AcondOperatingMode.AUTO,
            AcondOperatingMode.HEATPUMP,
            AcondOperatingMode.BIVALENCE,
            AcondOperatingMode.COOLING,
        ],
    ),
    SensorEntityDescription(
        key="SEASON_MODE",
        name="Season Mode",
        icon="mdi:calendar",
        device_class=SensorDeviceClass.ENUM,
        options=[
            AcondSeasonMode.SUMMER,
            AcondSeasonMode.WINTER,
        ],
    ),
    # Power related sensors
    SensorEntityDescription(
        key="ENERGY_CONSUMPTION",
        name="Energy Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:meter-electric",
        native_unit_of_measurement="kWh",
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="ENERGY_CONSUMPTION_TODAY",
        name="Energy Consumption Today",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:meter-electric",
        native_unit_of_measurement="kWh",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="POWER_CONSUMPTION",
        name="Power Consumption",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        native_unit_of_measurement="kW",
        suggested_display_precision=2,
    ),
    # Heat related sensors
    SensorEntityDescription(
        key="HEAT_QUANTITY",
        name="Heat Quantity",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:water-boiler",
        native_unit_of_measurement="kWh",
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="HEAT_QUANTITY_TODAY",
        name="Heat Quantity Today",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:water-boiler",
        native_unit_of_measurement="kWh",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="HEAT_PRODUCTION",
        name="Heat Production",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fire",
        native_unit_of_measurement="kW",
        suggested_display_precision=2,
    ),
    # COP / SCOP sensors
    SensorEntityDescription(
        key="COP",
        name="Coefficient Of Performance",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heat-pump",
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="SCOP",
        name="Seasonal Coefficient Of Performance",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heat-pump",
        suggested_display_precision=2,
    ),
    # Temperatures
    SensorEntityDescription(
        key="OUTLET_TEMPERATURE",
        name="Outlet Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        native_unit_of_measurement="°C",
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="ELECTRIC_HEATER_OUTLET_TEMPERATURE",
        name="Electric Heater Outlet Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        native_unit_of_measurement="°C",
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="INLET_TEMPERATURE",
        name="Inlet Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        native_unit_of_measurement="°C",
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="OUTDOOR_TEMPERATURE",
        name="Outdoor Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        native_unit_of_measurement="°C",
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="OUTDOOR_TEMPERATURE_AVERAGE",
        name="Outdoor Temperature Average",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        native_unit_of_measurement="°C",
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="EQUITHERM_TARGET_RETURN_WATER_TEMPERATURE",
        name="Equitherm Target Return Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        native_unit_of_measurement="°C",
        suggested_display_precision=1,
    ),
    # Device info sensors
    SensorEntityDescription(
        key="SOFTWARE_VERSION",
        name="Software Version",
        icon="mdi:information",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: AcondConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        AcondSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ACOND_ACONOMIS_ENTITY_DESCRIPTIONS
    )


class AcondSensor(AcondEntity, SensorEntity):
    """Acond Sensor class."""

    def __init__(
        self,
        coordinator: AcondDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = entity_description.key

    @property
    def native_value(self) -> float | str | None:
        """Return the native value of the sensor."""
        value = self.coordinator.data.get(
            ACOND_ACONOMIS_DATA_MAPPINGS[self.entity_description.key]
        )

        match self.entity_description.key:
            case "OPERATING_MODE":
                value = AcondOperatingMode.from_value(value)
            case "SEASON_MODE":
                value = AcondSeasonMode.SUMMER if value else AcondSeasonMode.WINTER

        return value
