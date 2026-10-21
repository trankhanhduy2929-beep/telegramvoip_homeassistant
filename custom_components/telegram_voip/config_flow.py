from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .api import (
    TelegramVoipApi,
    TelegramVoipApiError,
    TelegramVoipAuthError,
    TelegramVoipConnectionError,
)
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_URL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_URL,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default=DEFAULT_URL): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=300)
        ),
    }
)

STEP_OPTIONS_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=300)
        ),
    }
)


def _normalize_url(value: str) -> str:
    url = value.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url


class TelegramVoipConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = _normalize_url(user_input[CONF_URL])
            token = user_input[CONF_TOKEN].strip()
            if not token:
                errors["base"] = "invalid_auth"
            else:
                api = TelegramVoipApi(self.hass, url, token)
                try:
                    await api.async_status()
                except TelegramVoipAuthError:
                    errors["base"] = "invalid_auth"
                except TelegramVoipConnectionError:
                    errors["base"] = "cannot_connect"
                except TelegramVoipApiError:
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(url)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="Telegram VoIP",
                        data={CONF_URL: url, CONF_TOKEN: token},
                        options={
                            CONF_SCAN_INTERVAL: user_input.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            )
                        },
                    )
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return TelegramVoipOptionsFlow(config_entry)


class TelegramVoipOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self._entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = self.add_suggested_values_to_schema(
            STEP_OPTIONS_DATA_SCHEMA,
            {CONF_SCAN_INTERVAL: current},
        )
        return self.async_show_form(step_id="init", data_schema=schema)
