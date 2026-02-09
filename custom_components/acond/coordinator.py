"""DataUpdateCoordinator for acond."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from custom_components.acond.const import LOGGER
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    AcondApiClientAuthenticationError,
    AcondApiClientError,
)

if TYPE_CHECKING:
    from .data import AcondConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class AcondDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: AcondConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            data = await self.config_entry.runtime_data.client.async_get_data()

            LOGGER.debug("Data updated: %s", data)

            return data

        except AcondApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except AcondApiClientError as exception:
            raise UpdateFailed(exception) from exception
