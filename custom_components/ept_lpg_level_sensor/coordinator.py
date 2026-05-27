"""Coordinator for EPT Tech LPG Level Sensor."""

from datetime import timedelta
import logging
from typing import Any

from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CHARACTERISTIC_UUID,
    CONF_GAS_TYPE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_GAS_TYPE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    GAS_SPEEDS,
)

_LOGGER = logging.getLogger(__name__)


class EPTLpgCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching EPT LPG sensor data."""

    def __init__(self, hass: HomeAssistant, address: str, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.address = address
        self.config_entry = config_entry

        # Get update interval from options, fallback to config_entry data or default
        update_mins = config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )
        update_interval = timedelta(minutes=float(update_mins))

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from BLE device."""
        # Find BLE Device
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if not ble_device:
            raise UpdateFailed(f"Device with address {self.address} not found on any adapter/proxy")

        _LOGGER.debug("Connecting to EPT LPG sensor at %s", self.address)
        try:
            # Connect to device using BleakClientWithServiceCache
            client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                name=ble_device.name or "EPT LPG Sensor",
            )
        except Exception as err:
            raise UpdateFailed(f"Failed to connect to {self.address}: {err}") from err

        try:
            # Read characteristic
            _LOGGER.debug("Connected. Reading characteristic %s", CHARACTERISTIC_UUID)
            data = await client.read_gatt_char(CHARACTERISTIC_UUID)
            _LOGGER.debug("Raw data read: %s (length: %d)", data.hex(), len(data))
        except BleakError as err:
            raise UpdateFailed(f"Failed to read characteristic: {err}") from err
        finally:
            await client.disconnect()

        # Parse data
        if len(data) < 10:
            raise UpdateFailed(
                f"Invalid data length received from sensor: {len(data)} (expected at least 10)"
            )

        # Get gas type from options, fallback to config_entry data or default
        gas_type = self.config_entry.options.get(
            CONF_GAS_TYPE,
            self.config_entry.data.get(CONF_GAS_TYPE, DEFAULT_GAS_TYPE),
        )
        speed_of_sound = GAS_SPEEDS.get(gas_type, GAS_SPEEDS[DEFAULT_GAS_TYPE])

        # Parse raw time of flight (microseconds) from bytes 0-3
        tof_us = int.from_bytes(data[0:4], byteorder="little")

        # Calculate level/distance in cm:
        # Distance = (Time of Flight * Speed of Sound) / 2
        distance_cm = (tof_us * speed_of_sound) / 2.0

        # Parse battery voltage (millivolts) from bytes 8-9
        battery_mv = int.from_bytes(data[8:10], byteorder="little")

        # Estimate battery percentage (assuming 3.0V system, mapping 2.0V-2.8V to 0-100%)
        battery_pct = max(0, min(100, int((battery_mv - 2000) / 8)))

        # Get RSSI
        service_info = bluetooth.async_last_service_info(
            self.hass, self.address, connectable=True
        )
        rssi = service_info.rssi if service_info else None

        _LOGGER.info(
            "Successfully fetched data from EPT LPG Sensor: raw_tof=%d us, distance=%.2f cm, battery=%d mV (%d%%), RSSI=%s",
            tof_us,
            distance_cm,
            battery_mv,
            battery_pct,
            rssi,
        )

        return {
            "raw": tof_us,
            "distance": distance_cm,
            "battery_voltage": battery_mv,
            "battery_level": battery_pct,
            "rssi": rssi,
        }
