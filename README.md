# EPT Tech LPG Level Sensor for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![hacs_badge](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg?style=for-the-badge)](https://home-assistant.io)

A custom Home Assistant integration that connects to the **EPT Tech LPG-2412 BLE Level Sensor** via Bluetooth. 

This integration is designed to work out-of-the-box with any Bluetooth adapters or **ESPHome Bluetooth proxies** in your Home Assistant installation. It operates in a battery-friendly manner by connecting to the sensor, reading the data, and immediately disconnecting.

---

## Features

- **Direct BLE Connection**: Communicates over Bluetooth Low Energy with automatic routing via Home Assistant's central bluetooth stack.
- **Proxy Friendly**: Does not hold persistent connections, freeing up BLE proxy connection slots and conserving the sensor's battery.
- **Physical Shape Conversion**: Automatically calculates volume and percentage using configurable physical tank profiles.
  - **Vertical Cylinder / Linear**: Linear scaling of remaining volume based on fill level height.
  - **Horizontal Cylinder (Dome/Bullet Tanks)**: Mathematical segment computation to accurately reflect non-linear volume changes as liquid levels change.
- **Entities Exposed**:
  - **Liquid Level** (`cm`)
  - **LPG Remaining** (configurable unit: `L`, `kg`, `gal`, `%`)
  - **LPG Percentage** (`%`)
  - **Signal Strength (RSSI)** (`dBm`)
  - **Raw Time of Flight** (diagnostic, disabled by default)
- **Localizations**: Available in English, Spanish (`es`), and Catalan (`ca`).

---

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in your Home Assistant interface.
2. Click on **Integrations** (three dots in the top right corner).
3. Select **Custom repositories**.
4. Paste the URL of this repository into the **Repository** field.
5. Select **Integration** as the Category and click **Add**.
6. Find the **EPT Tech LPG Level Sensor** integration and click **Download**.
7. Restart Home Assistant to load the component.

### Method 2: Manual Installation

1. Download the latest release of this repository.
2. Copy the `custom_components/ept_lpg_level_sensor/` folder into your Home Assistant's `config/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings** -> **Devices & Services**.
2. Click **+ Add Integration** in the bottom right corner.
3. Search for **EPT Tech LPG Level Sensor** and click to begin setup.
4. If the sensor is broadcasting and nearby, select it from the list. Otherwise, select **Manually enter MAC address** and enter the sensor's MAC address (e.g. `E8:FA:8C:8A:2F:10`).
5. Configure the tank properties in the second step:
   - **Tank Shape**: Select *Vertical Cylinder / Linear* or *Horizontal Cylinder*.
   - **Total Tank Capacity**: The maximum quantity of LPG the tank holds (e.g., `100`).
   - **Unit of Capacity**: The unit to display for remaining volume (e.g., `L`, `kg`, `gal`, `%`).
   - **Tank Height / Diameter (cm)**: The total height (for vertical) or diameter (for horizontal) of the tank.
   - **Minimum Level (0% Capacity) (cm)**: The level at which the tank is considered empty (accounts for sensor dead-zones).
   - **Maximum Level (100% Capacity) (cm)**: The level at which the tank is considered full (e.g. 80% maximum filling limit for safety).
   - **Update Interval (minutes)**: How often the integration connects to the sensor to poll for updates (default: 10 minutes).

### Adjusting Tank Configuration Later

To change any dimensions, units, shape, or the update interval after setup:
1. Go to **Settings** -> **Devices & Services** -> **EPT Tech LPG Level Sensor**.
2. Click **Configure**.
3. Modify the parameters and submit. The changes will be applied instantly to all entities.
