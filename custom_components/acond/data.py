"""Custom types for acond."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import AcondApiClient
    from .coordinator import AcondDataUpdateCoordinator


type AcondConfigEntry = ConfigEntry[AcondData]


@dataclass
class AcondData:
    """Data for the Acond integration."""

    client: AcondApiClient
    coordinator: AcondDataUpdateCoordinator
    integration: Integration
