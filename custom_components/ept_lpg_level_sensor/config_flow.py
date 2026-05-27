"""Config flow for EPT Tech LPG Level Sensor integration."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CAPACITY_UNIT,
    CONF_MAX_LEVEL,
    CONF_MIN_LEVEL,
    CONF_TANK_CAPACITY,
    CONF_TANK_HEIGHT,
    CONF_TANK_SHAPE,
    CONF_UPDATE_INTERVAL,
    CONF_GAS_TYPE,
    DEFAULT_CAPACITY_UNIT,
    DEFAULT_MAX_LEVEL,
    DEFAULT_MIN_LEVEL,
    DEFAULT_TANK_CAPACITY,
    DEFAULT_TANK_HEIGHT,
    DEFAULT_TANK_SHAPE,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_GAS_TYPE,
    DOMAIN,
    GAS_TYPE_BUTANE,
    GAS_TYPE_LPG,
    GAS_TYPE_PROPANE,
    SERVICE_UUID,
    TANK_SHAPE_HORIZONTAL,
    TANK_SHAPE_LINEAR,
)

_LOGGER = logging.getLogger(__name__)


def is_valid_mac(address: str) -> bool:
    """Check if address is a valid MAC address."""
    return bool(re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", address))


class EPTLpgFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EPT Tech LPG Level Sensor."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.address: str | None = None

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle discovery via Bluetooth."""
        address = discovery_info.address
        self.address = address
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": discovery_info.name or "EPT LPG Sensor"}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return await self.async_step_tank()

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": self.address},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        errors = {}
        if user_input is not None:
            address = user_input.get("address")
            if address == "manual":
                return await self.async_step_manual()

            self.address = address
            await self.async_set_unique_id(self.address)
            self._abort_if_unique_id_configured()
            return await self.async_step_tank()

        # Discover devices
        discovered = bluetooth.async_discovered_service_info(self.hass)
        device_options = {}
        for d in discovered:
            name = d.name or d.address
            # If the device advertises our service UUID, prioritize it or mark it
            is_ept = SERVICE_UUID in d.service_uuids or SERVICE_UUID.lower() in [
                uuid.lower() for uuid in d.service_uuids
            ]
            suffix = " (EPT LPG Sensor)" if is_ept else ""
            device_options[d.address] = f"{name} [{d.address}]{suffix}"

        device_options["manual"] = "Manually enter MAC address"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("address"): vol.In(device_options)
            }),
            errors=errors,
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual MAC address entry."""
        errors = {}
        if user_input is not None:
            address = user_input["address"].upper()
            if not is_valid_mac(address):
                errors["address"] = "invalid_mac"
            else:
                self.address = address
                await self.async_set_unique_id(self.address)
                self._abort_if_unique_id_configured()
                return await self.async_step_tank()

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required("address"): str
            }),
            errors=errors,
        )

    async def async_step_tank(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle tank configuration."""
        errors = {}
        if user_input is not None:
            if user_input[CONF_TANK_CAPACITY] <= 0:
                errors[CONF_TANK_CAPACITY] = "invalid_capacity"
            elif user_input[CONF_TANK_HEIGHT] <= 0:
                errors[CONF_TANK_HEIGHT] = "invalid_height"
            elif user_input[CONF_MIN_LEVEL] < 0:
                errors[CONF_MIN_LEVEL] = "invalid_min_level"
            elif user_input[CONF_MAX_LEVEL] <= user_input[CONF_MIN_LEVEL]:
                errors[CONF_MAX_LEVEL] = "invalid_max_level"
            elif user_input[CONF_MAX_LEVEL] > user_input[CONF_TANK_HEIGHT]:
                errors[CONF_MAX_LEVEL] = "max_level_too_high"
            elif user_input[CONF_UPDATE_INTERVAL] < 1:
                errors[CONF_UPDATE_INTERVAL] = "invalid_update_interval"
            else:
                return self.async_create_entry(
                    title=f"EPT LPG Sensor ({self.address})",
                    data={
                        "address": self.address,
                    },
                    options={
                        CONF_TANK_SHAPE: user_input[CONF_TANK_SHAPE],
                        CONF_TANK_CAPACITY: user_input[CONF_TANK_CAPACITY],
                        CONF_CAPACITY_UNIT: user_input[CONF_CAPACITY_UNIT],
                        CONF_TANK_HEIGHT: user_input[CONF_TANK_HEIGHT],
                        CONF_MIN_LEVEL: user_input[CONF_MIN_LEVEL],
                        CONF_MAX_LEVEL: user_input[CONF_MAX_LEVEL],
                        CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                        CONF_GAS_TYPE: user_input[CONF_GAS_TYPE],
                    },
                )

        data_schema = vol.Schema({
            vol.Required(CONF_GAS_TYPE, default=DEFAULT_GAS_TYPE): vol.In({
                GAS_TYPE_LPG: "LPG (Liquefied Petroleum Gas)",
                GAS_TYPE_PROPANE: "Propane",
                GAS_TYPE_BUTANE: "Butane",
            }),
            vol.Required(CONF_TANK_SHAPE, default=DEFAULT_TANK_SHAPE): vol.In({
                TANK_SHAPE_LINEAR: "Vertical Cylinder / Linear",
                TANK_SHAPE_HORIZONTAL: "Horizontal Cylinder",
            }),
            vol.Required(CONF_TANK_CAPACITY, default=DEFAULT_TANK_CAPACITY): vol.Coerce(float),
            vol.Required(CONF_CAPACITY_UNIT, default=DEFAULT_CAPACITY_UNIT): vol.In(["L", "kg", "gal", "%"]),
            vol.Required(CONF_TANK_HEIGHT, default=DEFAULT_TANK_HEIGHT): vol.Coerce(float),
            vol.Required(CONF_MIN_LEVEL, default=DEFAULT_MIN_LEVEL): vol.Coerce(float),
            vol.Required(CONF_MAX_LEVEL, default=DEFAULT_MAX_LEVEL): vol.Coerce(float),
            vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.Coerce(int),
        })

        return self.async_show_form(
            step_id="tank",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EPTLpgOptionsFlowHandler:
        """Get the options flow handler."""
        return EPTLpgOptionsFlowHandler(config_entry)


class EPTLpgOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for EPT Tech LPG Level Sensor."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__(config_entry)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}
        if user_input is not None:
            if user_input[CONF_TANK_CAPACITY] <= 0:
                errors[CONF_TANK_CAPACITY] = "invalid_capacity"
            elif user_input[CONF_TANK_HEIGHT] <= 0:
                errors[CONF_TANK_HEIGHT] = "invalid_height"
            elif user_input[CONF_MIN_LEVEL] < 0:
                errors[CONF_MIN_LEVEL] = "invalid_min_level"
            elif user_input[CONF_MAX_LEVEL] <= user_input[CONF_MIN_LEVEL]:
                errors[CONF_MAX_LEVEL] = "invalid_max_level"
            elif user_input[CONF_MAX_LEVEL] > user_input[CONF_TANK_HEIGHT]:
                errors[CONF_MAX_LEVEL] = "max_level_too_high"
            elif user_input[CONF_UPDATE_INTERVAL] < 1:
                errors[CONF_UPDATE_INTERVAL] = "invalid_update_interval"
            else:
                return self.async_create_entry(title="", data=user_input)

        # Prepopulate with current settings (options fallback to data, fallback to defaults)
        current_shape = self.config_entry.options.get(
            CONF_TANK_SHAPE,
            self.config_entry.data.get(CONF_TANK_SHAPE, DEFAULT_TANK_SHAPE),
        )
        current_capacity = self.config_entry.options.get(
            CONF_TANK_CAPACITY,
            self.config_entry.data.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY),
        )
        current_unit = self.config_entry.options.get(
            CONF_CAPACITY_UNIT,
            self.config_entry.data.get(CONF_CAPACITY_UNIT, DEFAULT_CAPACITY_UNIT),
        )
        current_height = self.config_entry.options.get(
            CONF_TANK_HEIGHT,
            self.config_entry.data.get(CONF_TANK_HEIGHT, DEFAULT_TANK_HEIGHT),
        )
        current_min = self.config_entry.options.get(
            CONF_MIN_LEVEL,
            self.config_entry.data.get(CONF_MIN_LEVEL, DEFAULT_MIN_LEVEL),
        )
        current_max = self.config_entry.options.get(
            CONF_MAX_LEVEL,
            self.config_entry.data.get(CONF_MAX_LEVEL, DEFAULT_MAX_LEVEL),
        )
        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )
        current_gas_type = self.config_entry.options.get(
            CONF_GAS_TYPE,
            self.config_entry.data.get(CONF_GAS_TYPE, DEFAULT_GAS_TYPE),
        )

        data_schema = vol.Schema({
            vol.Required(CONF_GAS_TYPE, default=current_gas_type): vol.In({
                GAS_TYPE_LPG: "LPG (Liquefied Petroleum Gas)",
                GAS_TYPE_PROPANE: "Propane",
                GAS_TYPE_BUTANE: "Butane",
            }),
            vol.Required(CONF_TANK_SHAPE, default=current_shape): vol.In({
                TANK_SHAPE_LINEAR: "Vertical Cylinder / Linear",
                TANK_SHAPE_HORIZONTAL: "Horizontal Cylinder",
            }),
            vol.Required(CONF_TANK_CAPACITY, default=current_capacity): vol.Coerce(float),
            vol.Required(CONF_CAPACITY_UNIT, default=current_unit): vol.In(["L", "kg", "gal", "%"]),
            vol.Required(CONF_TANK_HEIGHT, default=current_height): vol.Coerce(float),
            vol.Required(CONF_MIN_LEVEL, default=current_min): vol.Coerce(float),
            vol.Required(CONF_MAX_LEVEL, default=current_max): vol.Coerce(float),
            vol.Required(CONF_UPDATE_INTERVAL, default=current_interval): vol.Coerce(int),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
