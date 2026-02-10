"""Binary sensor platform for acond."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import ACOND_ACONOMIS_DATA_MAPPINGS, LOGGER
from .entity import AcondEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import AcondDataUpdateCoordinator
    from .data import AcondConfigEntry

ACOND_ACONOMIS_BINARY_SENSOR_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key=ACOND_ACONOMIS_DATA_MAPPINGS["FAN_ACTIVE"],
        name="Fan",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:fan",
    ),
    BinarySensorEntityDescription(
        key=ACOND_ACONOMIS_DATA_MAPPINGS["COMPRESSOR_ACTIVE"],
        name="Compressor",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:engine",
    ),
    BinarySensorEntityDescription(
        key=ACOND_ACONOMIS_DATA_MAPPINGS["PRIMARY_CIRCUIT_PUMP_ACTIVE"],
        name="Primary Circuit Pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:water-pump",
    ),
    BinarySensorEntityDescription(
        key=ACOND_ACONOMIS_DATA_MAPPINGS["SECONDARY_CIRCUIT_PUMP_ACTIVE"],
        name="Secondary Circuit Pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:water-pump",
    ),
    BinarySensorEntityDescription(
        key=ACOND_ACONOMIS_DATA_MAPPINGS["DEFROST_ACTIVE"],
        name="Defrost",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:snowflake",
    ),
    BinarySensorEntityDescription(
        key=ACOND_ACONOMIS_DATA_MAPPINGS["BIVALENCE_ACTIVE"],
        name="Bivalence",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:water-boiler",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: AcondConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    async_add_entities(
        AcondBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ACOND_ACONOMIS_BINARY_SENSOR_DESCRIPTIONS
    )


class AcondBinarySensor(AcondEntity, BinarySensorEntity):
    """Acond Binary Sensor class."""

    def __init__(
        self,
        coordinator: AcondDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = entity_description.key

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        key = self.entity_description.key
        return self.coordinator.data.get(key)
