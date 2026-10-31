from __future__ import annotations

from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class TelegramVoipApiError(Exception):
    """Base API error."""


class TelegramVoipAuthError(TelegramVoipApiError):
    """Authentication failed."""


class TelegramVoipConnectionError(TelegramVoipApiError):
    """Cannot reach the add-on."""


class TelegramVoipApi:
    def __init__(self, hass: HomeAssistant, url: str, token: str) -> None:
        self._url = url.rstrip("/")
        self._token = token
        self._session = async_get_clientsession(hass)

    @property
    def base_url(self) -> str:
        return self._url

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with self._session.request(
                method,
                f"{self._url}/{path.lstrip('/')}",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status == 401:
                    raise TelegramVoipAuthError("invalid API token")
                if response.status >= 400:
                    detail = "request failed"
                    try:
                        data = await response.json()
                        detail = str(data.get("detail") or detail)
                    except (aiohttp.ContentTypeError, ValueError):
                        pass
                    raise TelegramVoipApiError(detail)
                if response.status == 204:
                    return {}
                return await response.json()
        except TelegramVoipAuthError:
            raise
        except TelegramVoipApiError:
            raise
        except (aiohttp.ClientError, TimeoutError, OSError) as err:
            raise TelegramVoipConnectionError(str(err)) from err

    async def async_status(self) -> dict[str, Any]:
        return await self._request("GET", "api/status")

    async def async_accounts(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "api/accounts")
        return list(data.get("accounts", []))

    async def async_send_message(
        self,
        to: str,
        message: str,
        account: str | None = None,
        parse_mode: str | None = None,
        silent: bool = False,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "api/messages",
            {
                "account": account,
                "to": to,
                "message": message,
                "parse_mode": parse_mode,
                "silent": silent,
            },
        )

    async def async_send_tts(
        self,
        to: str,
        message: str,
        account: str | None = None,
        voice: str | None = None,
        rate: str | None = None,
        caption: str | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "api/tts",
            {
                "account": account,
                "to": to,
                "message": message,
                "voice": voice,
                "rate": rate,
                "caption": caption,
            },
            timeout=120,
        )

    async def async_send_photo(
        self,
        to: str,
        image: str,
        account: str | None = None,
        caption: str | None = None,
        silent: bool = False,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "api/photos",
            {
                "account": account,
                "to": to,
                "image": image,
                "caption": caption,
                "silent": silent,
            },
            timeout=120,
        )

    async def async_call(
        self,
        to: str,
        message: str,
        account: str | None = None,
        voice: str | None = None,
        rate: str | None = None,
        ring_timeout: int | None = None,
        wait: bool = False,
        wait_seconds: int = 60,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "api/calls",
            {
                "account": account,
                "to": to,
                "message": message,
                "voice": voice,
                "rate": rate,
                "ring_timeout": ring_timeout,
                "wait": wait,
                "wait_seconds": wait_seconds,
            },
            timeout=max(120, wait_seconds + 15) if wait else 120,
        )

    async def async_ring(
        self,
        to: str,
        message: str,
        account: str | None = None,
        voice: str | None = None,
        rate: str | None = None,
        attempts: int | None = None,
        interval: int | None = None,
        ring_timeout: int | None = None,
        send_message: bool = True,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "api/rings",
            {
                "account": account,
                "to": to,
                "message": message,
                "voice": voice,
                "rate": rate,
                "attempts": attempts,
                "interval": interval,
                "ring_timeout": ring_timeout,
                "send_message": send_message,
            },
            timeout=120,
        )

    async def async_hangup(
        self,
        call_id: str | None = None,
        account: str | None = None,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "api/hangup",
            {"call_id": call_id, "account": account},
        )
