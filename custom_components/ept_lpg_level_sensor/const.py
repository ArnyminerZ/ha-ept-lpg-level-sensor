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
CONF_GAS_TYPE = "gas_type"

# Tank shapes
TANK_SHAPE_LINEAR = "linear"
TANK_SHAPE_HORIZONTAL = "horizontal_cylinder"

TANK_SHAPE_CHOICES = [
    TANK_SHAPE_LINEAR,
    TANK_SHAPE_HORIZONTAL,
]

# Gas types
GAS_TYPE_LPG = "lpg"
GAS_TYPE_PROPANE = "propane"
GAS_TYPE_BUTANE = "butane"

GAS_TYPE_CHOICES = [
    GAS_TYPE_LPG,
    GAS_TYPE_PROPANE,
    GAS_TYPE_BUTANE,
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
DEFAULT_GAS_TYPE = GAS_TYPE_LPG

# Speed of sound in cm/us
# LPG: 940 m/s = 0.094 cm/us
# Propane: 800 m/s = 0.080 cm/us
# Butane: 1000 m/s = 0.100 cm/us
GAS_SPEEDS = {
    GAS_TYPE_LPG: 0.094,
    GAS_TYPE_PROPANE: 0.080,
    GAS_TYPE_BUTANE: 0.100,
}

