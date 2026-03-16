"""Adds config flow for Acond."""

from __future__ import annotations
from tkinter import NO

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from slugify import slugify

from .api import (
    AcondApiClient,
    AcondApiClientAuthenticationError,
    AcondApiClientCommunicationError,
    AcondApiClientError,
)
from .const import DOMAIN, LOGGER


class AcondFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Acond."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    ip_address=user_input[CONF_IP_ADDRESS],
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except AcondApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except AcondApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except AcondApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    ## Do NOT use this in production code
                    ## The unique_id should never be something that can change
                    ## https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
                    unique_id=slugify(user_input[CONF_USERNAME])
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input,
                )

        return self._async_show_auth_form(
            step_id="user",
            user_input=user_input,
            errors=_errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, str]
    ) -> config_entries.ConfigFlowResult:
        """Handle re-authentication with the device."""
        return self._async_show_auth_form(
            step_id="reauth_confirm",
            user_input=entry_data,
            errors={},
        )

    async def async_step_reauth_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle re-authentication confirmation."""
        errors = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                await self._test_credentials(
                    ip_address=user_input[CONF_IP_ADDRESS],
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except AcondApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                errors["base"] = "auth"
            except AcondApiClientCommunicationError as exception:
                LOGGER.error(exception)
                errors["base"] = "connection"
            except AcondApiClientError as exception:
                LOGGER.exception(exception)
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data=user_input,
                )

        return self._async_show_auth_form(
            step_id="reauth_confirm",
            user_input=user_input,
            errors=errors,
        )

    def _async_show_auth_form(
        self, step_id: str, user_input: dict[str, str] | None, errors: dict[str, str]
    ) -> config_entries.ConfigFlowResult:
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_IP_ADDRESS,
                        default=(user_input or {}).get(CONF_IP_ADDRESS, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=errors,
        )

    async def _test_credentials(
        self, ip_address: str, username: str, password: str
    ) -> None:
        """Validate credentials."""
        client = AcondApiClient(
            ip_address=ip_address,
            username=username,
            password=password,
        )
        response = await client.login()

        LOGGER.debug("Response from login: %s", response)
