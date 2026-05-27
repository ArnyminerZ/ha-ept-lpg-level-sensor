"""Constants for the EPT Tech LPG Level Sensor integration."""

DOMAIN = "ept_lpg_level_sensor"

# BLE UUIDs
SERVICE_UUID = "00001123-1212-efde-1523-785feabcd123"
CHARACTERISTIC_UUID = "00001124-1212-efde-1523-785feabcd123"

# Configuration and options keys
CONF_TANK_SHAPE = "tank_shape"
CONF_TANK_CAPACITY = "tank_capacity"
CONF_CAPACITY_UNIT = "capacity_unit"
CONF_TANK_HEIGHT = "tank_height"
CONF_MIN_LEVEL = "min_level"
CONF_MAX_LEVEL = "max_level"
CONF_UPDATE_INTERVAL = "update_interval"

# Tank shapes
TANK_SHAPE_LINEAR = "linear"
TANK_SHAPE_HORIZONTAL = "horizontal_cylinder"

TANK_SHAPE_CHOICES = [
    TANK_SHAPE_LINEAR,
    TANK_SHAPE_HORIZONTAL,
]

# Defaults
DEFAULT_NAME = "EPT LPG Sensor"
DEFAULT_TANK_SHAPE = TANK_SHAPE_LINEAR
DEFAULT_TANK_CAPACITY = 100.0
DEFAULT_CAPACITY_UNIT = "L"
DEFAULT_TANK_HEIGHT = 100.0
DEFAULT_MIN_LEVEL = 0.0
DEFAULT_MAX_LEVEL = 100.0
DEFAULT_UPDATE_INTERVAL = 10  # minutes
