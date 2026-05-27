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

from .const import CHARACTERISTIC_UUID, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

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

        # Parse raw time of flight/distance
        raw_val = (data[9] << 8) | data[8]
        # Calculate level/distance in cm using ESPHome's formula:
        # ((raw_val * 0.21) / 2.0) / 10.0 = raw_val * 0.0105
        distance_cm = ((raw_val * 0.21) / 2.0) / 10.0

        # Get RSSI
        service_info = bluetooth.async_last_service_info(
            self.hass, self.address, connectable=True
        )
        rssi = service_info.rssi if service_info else None

        _LOGGER.info(
            "Successfully fetched data from EPT LPG Sensor: raw=%d, distance=%.2f cm, RSSI=%s",
            raw_val,
            distance_cm,
            rssi,
        )

        return {
            "raw": raw_val,
            "distance": distance_cm,
            "rssi": rssi,
        }
