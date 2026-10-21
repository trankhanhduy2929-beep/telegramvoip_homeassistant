from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, NoReturn

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import (
    TelegramVoipApi,
    TelegramVoipApiError,
    TelegramVoipAuthError,
    TelegramVoipConnectionError,
)
from .const import (
    ATTR_ACCOUNT,
    ATTR_ATTEMPTS,
    ATTR_CALL_ID,
    ATTR_CAPTION,
    ATTR_INTERVAL,
    ATTR_MESSAGE,
    ATTR_PARSE_MODE,
    ATTR_RATE,
    ATTR_RING_TIMEOUT,
    ATTR_SEND_MESSAGE,
    ATTR_SILENT,
    ATTR_TO,
    ATTR_VOICE,
    ATTR_WAIT,
    ATTR_WAIT_SECONDS,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_CALL,
    SERVICE_HANGUP,
    SERVICE_RING,
    SERVICE_SEND_MESSAGE,
    SERVICE_SEND_TTS,
)
from .coordinator import TelegramVoipCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORM_LIST = [Platform.SENSOR]


@dataclass(slots=True)
class TelegramVoipRuntime:
    api: TelegramVoipApi
    coordinator: TelegramVoipCoordinator


def _text(minimum: int = 1, maximum: int = 4096) -> Any:
    return vol.All(cv.string, vol.Length(min=minimum, max=maximum))


def _int_range(minimum: int, maximum: int) -> Any:
    return vol.All(vol.Coerce(int), vol.Range(min=minimum, max=maximum))


SEND_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TO): _text(1, 128),
        vol.Required(ATTR_MESSAGE): _text(1, 4096),
        vol.Optional(ATTR_ACCOUNT): _text(1, 64),
        vol.Optional(ATTR_PARSE_MODE): vol.In(["", "plain", "markdown", "html"]),
        vol.Optional(ATTR_SILENT, default=False): vol.Boolean(),
    }
)

SEND_TTS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TO): _text(1, 128),
        vol.Required(ATTR_MESSAGE): _text(1, 2000),
        vol.Optional(ATTR_ACCOUNT): _text(1, 64),
        vol.Optional(ATTR_VOICE): _text(1, 64),
        vol.Optional(ATTR_RATE): _text(1, 12),
        vol.Optional(ATTR_CAPTION): _text(1, 1024),
    }
)

CALL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TO): _text(1, 128),
        vol.Required(ATTR_MESSAGE): _text(1, 2000),
        vol.Optional(ATTR_ACCOUNT): _text(1, 64),
        vol.Optional(ATTR_VOICE): _text(1, 64),
        vol.Optional(ATTR_RATE): _text(1, 12),
        vol.Optional(ATTR_RING_TIMEOUT): _int_range(10, 180),
        vol.Optional(ATTR_WAIT, default=False): vol.Boolean(),
        vol.Optional(ATTR_WAIT_SECONDS, default=60): _int_range(5, 180),
    }
)

RING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TO): _text(1, 128),
        vol.Required(ATTR_MESSAGE): _text(1, 2000),
        vol.Optional(ATTR_ACCOUNT): _text(1, 64),
        vol.Optional(ATTR_VOICE): _text(1, 64),
        vol.Optional(ATTR_RATE): _text(1, 12),
        vol.Optional(ATTR_ATTEMPTS): _int_range(1, 10),
        vol.Optional(ATTR_INTERVAL): _int_range(0, 600),
        vol.Optional(ATTR_RING_TIMEOUT): _int_range(10, 180),
        vol.Optional(ATTR_SEND_MESSAGE, default=True): vol.Boolean(),
    }
)

HANGUP_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CALL_ID): _text(1, 64),
        vol.Optional(ATTR_ACCOUNT): _text(1, 64),
    }
)


def _get_api(hass: HomeAssistant) -> TelegramVoipApi:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is not ConfigEntryState.LOADED:
            continue
        runtime = getattr(entry, "runtime_data", None)
        if isinstance(runtime, TelegramVoipRuntime):
            return runtime.api
    raise HomeAssistantError("Telegram VoIP add-on is not configured or not loaded")


def _raise_api_error(err: Exception) -> NoReturn:
    if isinstance(err, TelegramVoipAuthError):
        raise HomeAssistantError(
            "Telegram VoIP add-on rejected the API token"
        ) from err
    if isinstance(err, TelegramVoipConnectionError):
        raise HomeAssistantError(
            f"Cannot reach the Telegram VoIP add-on: {err}"
        ) from err
    raise HomeAssistantError(str(err)) from err


async def _handle_send_message(call: ServiceCall) -> dict[str, Any]:
    try:
        api = _get_api(call.hass)
        return await api.async_send_message(
            to=call.data[ATTR_TO],
            message=call.data[ATTR_MESSAGE],
            account=call.data.get(ATTR_ACCOUNT),
            parse_mode=call.data.get(ATTR_PARSE_MODE),
            silent=call.data.get(ATTR_SILENT, False),
        )
    except TelegramVoipApiError as err:
        _raise_api_error(err)


async def _handle_send_tts(call: ServiceCall) -> dict[str, Any]:
    try:
        api = _get_api(call.hass)
        return await api.async_send_tts(
            to=call.data[ATTR_TO],
            message=call.data[ATTR_MESSAGE],
            account=call.data.get(ATTR_ACCOUNT),
            voice=call.data.get(ATTR_VOICE),
            rate=call.data.get(ATTR_RATE),
            caption=call.data.get(ATTR_CAPTION),
        )
    except TelegramVoipApiError as err:
        _raise_api_error(err)


async def _handle_call(call: ServiceCall) -> dict[str, Any]:
    try:
        api = _get_api(call.hass)
        return await api.async_call(
            to=call.data[ATTR_TO],
            message=call.data[ATTR_MESSAGE],
            account=call.data.get(ATTR_ACCOUNT),
            voice=call.data.get(ATTR_VOICE),
            rate=call.data.get(ATTR_RATE),
            ring_timeout=call.data.get(ATTR_RING_TIMEOUT),
            wait=call.data.get(ATTR_WAIT, False),
            wait_seconds=call.data.get(ATTR_WAIT_SECONDS, 60),
        )
    except TelegramVoipApiError as err:
        _raise_api_error(err)


async def _handle_ring(call: ServiceCall) -> dict[str, Any]:
    try:
        api = _get_api(call.hass)
        return await api.async_ring(
            to=call.data[ATTR_TO],
            message=call.data[ATTR_MESSAGE],
            account=call.data.get(ATTR_ACCOUNT),
            voice=call.data.get(ATTR_VOICE),
            rate=call.data.get(ATTR_RATE),
            attempts=call.data.get(ATTR_ATTEMPTS),
            interval=call.data.get(ATTR_INTERVAL),
            ring_timeout=call.data.get(ATTR_RING_TIMEOUT),
            send_message=call.data.get(ATTR_SEND_MESSAGE, True),
        )
    except TelegramVoipApiError as err:
        _raise_api_error(err)


async def _handle_hangup(call: ServiceCall) -> dict[str, Any]:
    try:
        api = _get_api(call.hass)
        return await api.async_hangup(
            call_id=call.data.get(ATTR_CALL_ID),
            account=call.data.get(ATTR_ACCOUNT),
        )
    except TelegramVoipApiError as err:
        _raise_api_error(err)


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SEND_MESSAGE):
        return
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_MESSAGE,
        _handle_send_message,
        schema=SEND_MESSAGE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_TTS,
        _handle_send_tts,
        schema=SEND_TTS_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CALL,
        _handle_call,
        schema=CALL_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RING,
        _handle_ring,
        schema=RING_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_HANGUP,
        _handle_hangup,
        schema=HANGUP_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = TelegramVoipApi(
        hass,
        entry.data[CONF_URL],
        entry.data[CONF_TOKEN],
    )
    coordinator = TelegramVoipCoordinator(
        hass,
        api,
        int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = TelegramVoipRuntime(api=api, coordinator=coordinator)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    _async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORM_LIST)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORM_LIST)
    if unloaded:
        entry.runtime_data = None
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
