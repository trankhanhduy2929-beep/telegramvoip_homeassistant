from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    TelegramVoipApi,
    TelegramVoipApiError,
    TelegramVoipAuthError,
    TelegramVoipConnectionError,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TelegramVoipCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: TelegramVoipApi,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_status()
        except TelegramVoipAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except TelegramVoipConnectionError as err:
            raise UpdateFailed(f"Cannot reach Telegram VoIP add-on: {err}") from err
        except TelegramVoipApiError as err:
            raise UpdateFailed(str(err)) from err
