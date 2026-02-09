"""Acond API Client."""

from __future__ import annotations

from re import L
import socket
from typing import Any

import aiohttp
import async_timeout

from bs4 import BeautifulSoup
from custom_components.acond.const import LOGGER

PAGE_LOGIN = "SYSWWW/LOGIN.XML"
PAGE_DATA = "PAGE214.XML"

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

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        response = await self._api_wrapper_retry_unauthenticated(
            method="get",
            url=f"http://{self._ip_address}/{PAGE_DATA}",
        )

        LOGGER.debug("async_get_data response: %s", response)

        return self._map_response(await response.text())

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

    async def _api_wrapper_retry_unauthenticated(
        self,
        method: str,
        url: str,
        data: aiohttp.FormData | None = None,
        headers: dict | None = None,
        attempt=0,
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

        return {elem.get("NAME"): elem.get("VALUE") for elem in soup.find_all("INPUT")}
