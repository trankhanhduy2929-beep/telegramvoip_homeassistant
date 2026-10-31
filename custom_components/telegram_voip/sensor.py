from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TelegramVoipCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TelegramVoipCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            AccountsOnlineSensor(coordinator, entry),
            ActiveCallsSensor(coordinator, entry),
        ]
    )


class TelegramVoipSensor(CoordinatorEntity[TelegramVoipCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TelegramVoipCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Telegram VoIP",
            manufacturer="apk-lab",
            model="Telegram add-on bridge",
            configuration_url=coordinator.api.base_url,
        )


class AccountsOnlineSensor(TelegramVoipSensor):
    _attr_translation_key = "accounts_online"
    _attr_icon = "mdi:account-multiple-check"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: TelegramVoipCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_accounts_online"

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get("accounts_online", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        accounts = self.coordinator.data.get("accounts", [])
        return {
            "accounts": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "phone": item.get("phone"),
                    "state": item.get("state"),
                    "me": item.get("me"),
                    "last_error": item.get("last_error"),
                }
                for item in accounts
            ],
            "version": self.coordinator.data.get("version"),
            "started_at": self.coordinator.data.get("started_at"),
        }


class ActiveCallsSensor(TelegramVoipSensor):
    _attr_translation_key = "active_calls"
    _attr_icon = "mdi:phone-in-talk"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: TelegramVoipCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_active_calls"

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get("active_calls", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "calls": self.coordinator.data.get("calls", []),
            "rings": self.coordinator.data.get("rings", []),
            "stats": self.coordinator.data.get("stats", {}),
            "tts": self.coordinator.data.get("tts", {}),
        }
