"""
Custom integration to integrate acond with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/acond
"""

from __future__ import annotations

from datetime import timedelta
from ipaddress import ip_address
from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_IP_ADDRESS, Platform
from homeassistant.loader import async_get_loaded_integration

from .api import AcondApiClient
from .const import DOMAIN, LOGGER
from .coordinator import AcondDataUpdateCoordinator
from .data import AcondData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import AcondConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: AcondConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = AcondDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=30),
    )
    entry.runtime_data = AcondData(
        client=AcondApiClient(
            ip_address=entry.data[CONF_IP_ADDRESS],
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AcondConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: AcondConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
