"""Acond API Client."""

from __future__ import annotations

import contextlib
import socket
from typing import Any
import asyncio

import aiohttp
import async_timeout
from bs4 import BeautifulSoup

from custom_components.acond.const import ACOND_ACONOMIS_DATA_MAPPINGS, LOGGER

PAGE_LOGIN = "SYSWWW/LOGIN.XML"
PAGE_MEASUREMENT = "PAGE214.XML"
PAGE_CONTROL = "PAGE206.XML"
PAGE_SETTINGS = "PAGE207.XML"
PAGE_EQUITHERM = "PAGE225.XML"

HTTP_FOUND = 302


class AcondApiClientError(Exception):
    """Exception to indicate a general API error."""


class AcondApiClientCommunicationError(
    AcondApiClientError,
):
    """Exception to indicate a communication error."""


class AcondApiClientAuthenticationError(
    AcondApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise AcondApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class AcondApiClient:
    """Sample API Client."""

    def __init__(
        self,
        ip_address: str,
        username: str,
        password: str,
    ) -> None:
        """Sample API Client."""
        self._ip_address = ip_address
        self._username = username
        self._password = password

        self._connector = aiohttp.TCPConnector(family=socket.AF_INET)
        self._cookie_jar = aiohttp.CookieJar(unsafe=True)
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            cookie_jar=self._cookie_jar,
        )

    async def async_get_all(self) -> Any:
        """Get data from the API."""
        tasks = (
            await self.async_get_measurements(),
            await self.async_get_controls(),
            # Currently gives encoding error, not needed anyway
            # await self.async_get_settings(),
            await self.async_get_equitherm(),
        )

        merged: dict[str, Any] = {}
        for result in tasks:
            if isinstance(result, dict):
                merged.update(result)

        return merged

    async def async_get_measurements(self) -> Any:
        """Get data from the API."""
        return await self._async_get_page(PAGE_MEASUREMENT)

    async def async_get_controls(self) -> Any:
        """Get data from the API."""
        return await self._async_get_page(PAGE_CONTROL)

    async def async_get_settings(self) -> Any:
        """Get data from the API."""
        return await self._async_get_page(PAGE_SETTINGS)

    async def async_get_equitherm(self) -> Any:
        """Get data from the API."""
        return await self._async_get_page(PAGE_EQUITHERM)

    async def login(self) -> Any:
        """Login to the API."""
        data = aiohttp.FormData()
        data.add_field("USER", self._username)
        data.add_field("PASS", self._password)

        login_response = await self._api_wrapper(
            method="post",
            url=f"http://{self._ip_address}/{PAGE_LOGIN}",
            data=data,
        )

        if login_response.status != HTTP_FOUND:
            raise AcondApiClientAuthenticationError("Login failed")

    async def async_set_dhw_temperature(self, temperature: float) -> None:
        """Set new target temperature for domestic hot water."""
        set_temperature_key = ACOND_ACONOMIS_DATA_MAPPINGS[
            "SET_DHW_TEMPERATURE_REQUIRED"
        ]

        data = aiohttp.FormData()
        data.add_field(f"{set_temperature_key}={temperature:.1f}", "")

        response = await self._api_wrapper_retry_unauthenticated(
            method="post",
            url=f"http://{self._ip_address}/{PAGE_CONTROL}",
            data=data,
        )

        _verify_response_or_raise(response)

    async def _async_get_page(self, page: str) -> Any:
        """Get a page from the API."""
        response = await self._api_wrapper_retry_unauthenticated(
            method="get",
            url=f"http://{self._ip_address}/{page}",
        )

        LOGGER.debug("async_get_page response: %s", response)

        return self._map_response(await response.text())

    async def _api_wrapper_retry_unauthenticated(
        self,
        method: str,
        url: str,
        data: aiohttp.FormData | None = None,
        headers: dict | None = None,
        attempt: int = 0,
    ) -> aiohttp.ClientResponse:
        response = await self._api_wrapper(
            method=method,
            url=url,
            data=data,
            headers=headers,
        )

        if (
            response.status == HTTP_FOUND
            and response.headers.get("Location") == f"/{PAGE_LOGIN}"
        ):
            if attempt == 0:
                await self.login()
                return await self._api_wrapper_retry_unauthenticated(
                    method=method,
                    url=url,
                    data=data,
                    headers=headers,
                    attempt=attempt + 1,
                )

            raise AcondApiClientAuthenticationError("Login failed after retry")

        return response

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: aiohttp.FormData | None = None,
        headers: dict | None = None,
    ) -> aiohttp.ClientResponse:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                return await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    allow_redirects=False,
                )

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise AcondApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise AcondApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise AcondApiClientError(
                msg,
            ) from exception

    def _map_response(self, str_response: str) -> Any:
        """Map response."""
        soup = BeautifulSoup(str_response, "lxml-xml")
        results = {}

        for elem in soup.find_all("INPUT"):
            name = str(elem.get("NAME"))
            value = str(elem.get("VALUE"))

            if name is None or value is None:
                LOGGER.warning("Input tag found without name or value: %s", elem)
                continue

            with contextlib.suppress(TypeError, ValueError):
                if name.endswith("f"):
                    value = float(value) or 0

                if name.endswith("BOOL_i"):
                    value = bool(int(value)) or False

            results[name] = value

        return results
