"""DataUpdateCoordinator for acond."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    AcondApiClientAuthenticationError,
    AcondApiClientError,
)
from .const import ACOND_ACONOMIS_DATA_MAPPINGS

if TYPE_CHECKING:
    from .data import AcondConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class AcondDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: AcondConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self.config_entry.runtime_data.client.async_get_all()
        except AcondApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except AcondApiClientError as exception:
            raise UpdateFailed(exception) from exception

    def get_regulation_mode(self) -> str | None:
        """Get current operating mode."""

        key = ACOND_ACONOMIS_DATA_MAPPINGS["REGULATION_MODE"]
        return self.data.get(key) if self.data else None

    def is_compressor_active(self) -> bool | None:
        """Get whether the heat pump is active."""

        key = ACOND_ACONOMIS_DATA_MAPPINGS["COMPRESSOR_ACTIVE"]

        return self.data.get(key) if self.data else None

    def is_dhw_active(self) -> bool | None:
        """Get whether domestic hot water is active."""

        key = ACOND_ACONOMIS_DATA_MAPPINGS["DHW_ACTIVE"]
        return self.data.get(key) if self.data else None
