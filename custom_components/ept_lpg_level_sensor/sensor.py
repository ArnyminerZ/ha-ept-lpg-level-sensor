"""Sensor platform for EPT Tech LPG Level Sensor."""

from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfLength,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CAPACITY_UNIT,
    CONF_MAX_LEVEL,
    CONF_MIN_LEVEL,
    CONF_TANK_CAPACITY,
    CONF_TANK_HEIGHT,
    CONF_TANK_SHAPE,
    DEFAULT_CAPACITY_UNIT,
    DEFAULT_MAX_LEVEL,
    DEFAULT_MIN_LEVEL,
    DEFAULT_TANK_CAPACITY,
    DEFAULT_TANK_HEIGHT,
    DEFAULT_TANK_SHAPE,
    DOMAIN,
    TANK_SHAPE_HORIZONTAL,
    TANK_SHAPE_LINEAR,
)
from .coordinator import EPTLpgCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up EPT Tech LPG Level Sensor entities."""
    coordinator: EPTLpgCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EPTLpgDistanceSensor(coordinator),
        EPTLpgVolumeSensor(coordinator),
        EPTLpgPercentageSensor(coordinator),
        EPTLpgRssiSensor(coordinator),
        EPTLpgRawSensor(coordinator),
    ]

    async_add_entities(entities)


class EPTLpgSensorBase(CoordinatorEntity[EPTLpgCoordinator], SensorEntity):
    """Base class for EPT LPG Level Sensor entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EPTLpgCoordinator, key: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.address}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.address)},
            name=self.coordinator.config_entry.title,
            manufacturer="EPT Tech",
            model="LPG-2412 BLE Level Sensor",
            sw_version="1.0.0",
            connections={(CONNECTION_BLUETOOTH, self.coordinator.address)},
        )


class EPTLpgDistanceSensor(EPTLpgSensorBase):
    """Sensor for the liquid level/distance."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_icon = "mdi:ruler"

    def __init__(self, coordinator: EPTLpgCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "distance")
        self._attr_name = "Liquid Level"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if (
            self.coordinator.data is None
            or "distance" not in self.coordinator.data
        ):
            return None
        return round(float(self.coordinator.data["distance"]), 2)


class EPTLpgVolumeSensor(EPTLpgSensorBase):
    """Sensor for the remaining volume/capacity."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gas-cylinder"

    def __init__(self, coordinator: EPTLpgCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "volume")
        self._attr_name = "LPG Remaining"

        # Get capacity unit from options/data
        unit = coordinator.config_entry.options.get(
            CONF_CAPACITY_UNIT,
            coordinator.config_entry.data.get(CONF_CAPACITY_UNIT, DEFAULT_CAPACITY_UNIT),
        )

        # Map string unit to HA constant if possible
        if unit == "L":
            self._attr_native_unit_of_measurement = UnitOfVolume.LITERS
            self._attr_device_class = SensorDeviceClass.VOLUME
        elif unit == "gal":
            self._attr_native_unit_of_measurement = UnitOfVolume.GALLONS
            self._attr_device_class = SensorDeviceClass.VOLUME
        else:
            self._attr_native_unit_of_measurement = unit
            self._attr_device_class = None

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if (
            self.coordinator.data is None
            or "distance" not in self.coordinator.data
        ):
            return None

        distance = float(self.coordinator.data["distance"])
        options = self.coordinator.config_entry.options
        data = self.coordinator.config_entry.data

        shape = options.get(CONF_TANK_SHAPE, data.get(CONF_TANK_SHAPE, DEFAULT_TANK_SHAPE))
        capacity = float(
            options.get(CONF_TANK_CAPACITY, data.get(CONF_TANK_CAPACITY, DEFAULT_TANK_CAPACITY))
        )
        height = float(
            options.get(CONF_TANK_HEIGHT, data.get(CONF_TANK_HEIGHT, DEFAULT_TANK_HEIGHT))
        )
        min_level = float(
            options.get(CONF_MIN_LEVEL, data.get(CONF_MIN_LEVEL, DEFAULT_MIN_LEVEL))
        )
        max_level = float(
            options.get(CONF_MAX_LEVEL, data.get(CONF_MAX_LEVEL, DEFAULT_MAX_LEVEL))
        )

        # Clamp and compute
        h = max(min_level, min(distance, max_level))
        height_range = max_level - min_level
        if height_range <= 0:
            return 0.0

        if shape == TANK_SHAPE_LINEAR:
            # Linear / Vertical Cylinder
            percentage = (h - min_level) / height_range
            val = percentage * capacity
        elif shape == TANK_SHAPE_HORIZONTAL:
            # Horizontal Cylinder
            # Scale height to the cylinder's actual diameter (height)
            h_scaled = ((h - min_level) / height_range) * height

            R = height / 2.0
            h_clamped = max(0.0, min(h_scaled, height))
            val_ratio = (R - h_clamped) / R
            val_clamped = max(-1.0, min(val_ratio, 1.0))

            theta = math.acos(val_clamped)
            fraction = (theta - val_clamped * math.sqrt(1.0 - val_clamped**2)) / math.pi
            val = fraction * capacity
        else:
            val = 0.0

        return round(val, 2)


class EPTLpgPercentageSensor(EPTLpgSensorBase):
    """Sensor for the remaining level percentage."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:gas-cylinder"

    def __init__(self, coordinator: EPTLpgCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "percentage")
        self._attr_name = "LPG Percentage"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if (
            self.coordinator.data is None
            or "distance" not in self.coordinator.data
        ):
            return None

        distance = float(self.coordinator.data["distance"])
        options = self.coordinator.config_entry.options
        data = self.coordinator.config_entry.data

        shape = options.get(CONF_TANK_SHAPE, data.get(CONF_TANK_SHAPE, DEFAULT_TANK_SHAPE))
        height = float(
            options.get(CONF_TANK_HEIGHT, data.get(CONF_TANK_HEIGHT, DEFAULT_TANK_HEIGHT))
        )
        min_level = float(
            options.get(CONF_MIN_LEVEL, data.get(CONF_MIN_LEVEL, DEFAULT_MIN_LEVEL))
        )
        max_level = float(
            options.get(CONF_MAX_LEVEL, data.get(CONF_MAX_LEVEL, DEFAULT_MAX_LEVEL))
        )

        # Clamp and compute percentage
        h = max(min_level, min(distance, max_level))
        height_range = max_level - min_level
        if height_range <= 0:
            return 0.0

        if shape == TANK_SHAPE_LINEAR:
            percentage = (h - min_level) / height_range * 100.0
        elif shape == TANK_SHAPE_HORIZONTAL:
            h_scaled = ((h - min_level) / height_range) * height
            R = height / 2.0
            h_clamped = max(0.0, min(h_scaled, height))
            val_ratio = (R - h_clamped) / R
            val_clamped = max(-1.0, min(val_ratio, 1.0))

            theta = math.acos(val_clamped)
            fraction = (theta - val_clamped * math.sqrt(1.0 - val_clamped**2)) / math.pi
            percentage = fraction * 100.0
        else:
            percentage = 0.0

        return round(percentage, 1)


class EPTLpgRssiSensor(EPTLpgSensorBase):
    """Sensor for BLE signal strength (RSSI)."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: EPTLpgCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "rssi")
        self._attr_name = "Signal Strength"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if (
            self.coordinator.data is None
            or "rssi" not in self.coordinator.data
        ):
            return None
        val = self.coordinator.data.get("rssi")
        return int(val) if val is not None else None


class EPTLpgRawSensor(EPTLpgSensorBase):
    """Sensor for raw time of flight/distance value."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:radar"

    def __init__(self, coordinator: EPTLpgCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, "raw_time_of_flight")
        self._attr_name = "Raw Time of Flight"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if (
            self.coordinator.data is None
            or "raw" not in self.coordinator.data
        ):
            return None
        val = self.coordinator.data.get("raw")
        return int(val) if val is not None else None
