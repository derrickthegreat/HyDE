#!/usr/bin/env python
"""
sensorsinfo.py
A script to gather and display sensor information from the system.
It uses the `sensors` command to get sensor data and formats it for display.
This script is designed to be used with Waybar or similar status bars.


The bundled module runs it once per poll, so --next/--prev can refresh the
tooltip right away through the module's signal. --interval keeps it running
in a loop instead, which avoids restarting Python but can't be refreshed by a
signal: a page change then shows on the next tick.
"""

import json
import subprocess
import os
import argparse
import time
import sys

DEVICE_GLYPHS = {
    "iwlwifi": "",
    "nvme": "",
    "acpitz": "",
    "coretemp": "",
    "pch_cannonlake": "",
    "BAT": "",
    "acpi_fan": "󰈐",
    "default": "",
}


def get_device_glyph(device_name):
    return next(
        (glyph for key, glyph in DEVICE_GLYPHS.items() if key in device_name),
        DEVICE_GLYPHS["default"],
    )


def format_columns(data, max_entries_per_column=15):
    if not data:
        return []
    columns = []
    for i in range(0, len(data), max_entries_per_column):
        columns.append(data[i : i + max_entries_per_column])
    # Merge columns into rows
    rows = []
    max_rows = max(len(col) for col in columns)
    for i in range(max_rows):
        row = []
        for col in columns:
            if i < len(col):
                row.append(col[i])
            else:
                row.append("")
        rows.append("\t".join(row))
    return rows


PAGE_SIZE = 5
PAGE_FILE = "/tmp/sensorinfo_page"
# Must match "signal" in custom-sensorsinfo.jsonc
WAYBAR_SIGNAL = 23


def get_current_page(total_pages):
    try:
        with open(PAGE_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip()) % total_pages
    except (OSError, ValueError):
        return 0


def save_current_page(page):
    with open(PAGE_FILE, "w", encoding="utf-8") as f:
        f.write(str(page))


# Lower bound in °C -> colour, the same ramp as styles/classes/cpuinfo.css so a
# reading looks the same in the bar and here. 40-59 keeps the theme's text colour.
TEMP_COLORS = (
    (90, "#8b0000"),
    (85, "#ad1f2f"),
    (80, "#d22f2f"),
    (75, "#ff471a"),
    (70, "#ff6347"),
    (65, "#ff8c00"),
    (60, "#ffa500"),
    (40, ""),
    (25, "#87ceeb"),
    (15, "#4682b4"),
    (0, "#4169e1"),
)


def get_temp_color(temp):
    color = next((color for threshold, color in TEMP_COLORS if temp >= threshold), TEMP_COLORS[-1][1])
    if color:
        return f"<span color='{color}'><b>{temp:.0f}°C</b></span>"
    return f"{temp:.0f}°C"


def get_sensor_data(result_sensors, page=0):
    try:
        sensors_data = json.loads(result_sensors.stdout)
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from sensors output")
        return {
            "text": " N/A",
            "tooltip": "Error: Failed to decode JSON from sensors output",
        }

    # Initialize variables
    device_data = {}

    # Extract top-level sensor data
    for device in sorted(sensors_data.keys()):
        data = sensors_data[device]
        device_data[device] = {
            "temperatures": [],
            "fan_speeds": [],
            "voltages": [],
            "currents": [],
            "powers": [],
        }
        for sensor, values in data.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    if "temp" in key and "input" in key:
                        temp_color = get_temp_color(value)
                        device_data[device]["temperatures"].append(f"{sensor}: {temp_color}")
                    elif "fan" in key and "input" in key:
                        device_data[device]["fan_speeds"].append(f"{sensor}: {value} RPM")
                    elif "in" in key and "input" in key:
                        device_data[device]["voltages"].append(f"{sensor}: {value} V")
                    elif "curr" in key and "input" in key:
                        device_data[device]["currents"].append(f"{sensor}: {value} A")
                    elif "power" in key and "input" in key:
                        device_data[device]["powers"].append(f"{sensor}: {value} W")

    # Format the output
    text = " "
    tooltip_parts = []

    devices = list(device_data.keys())
    total_pages = (len(devices) + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(0, min(page, total_pages - 1))
    save_current_page(page)

    start_index = page * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    devices = devices[start_index:end_index]

    for device in devices:
        data = device_data[device]
        device_parts = [f"  Device: {device}       "]
        has_data = False
        if data["temperatures"]:
            has_data = True
            temp_columns = format_columns(data["temperatures"])
            device_parts.append(
                "        Temperatures:\n        " + "\n        ".join(temp_columns)
            )
        if data["fan_speeds"]:
            has_data = True
            fan_columns = format_columns(data["fan_speeds"])
            device_parts.append("       󰈐 Fan Speeds:\n        " + "\n        ".join(fan_columns))
        if data["voltages"]:
            has_data = True
            volt_columns = format_columns(data["voltages"])
            device_parts.append("        Voltages:\n        " + "\n        ".join(volt_columns))
        if data["currents"]:
            has_data = True
            curr_columns = format_columns(data["currents"])
            device_parts.append("        Currents:\n        " + "\n        ".join(curr_columns))
        if data["powers"]:
            has_data = True
            power_columns = format_columns(data["powers"])
            device_parts.append("       󰐧 Powers:\n        " + "\n        ".join(power_columns))
        if has_data:
            tooltip_parts.append("\n".join(device_parts))
            tooltip_parts.append("\n")  # Add a newline after each device's information

    # Add page indicator
    tooltip_parts.append(f"\nPage {page + 1}/{total_pages} ← →")

    tooltip = "\n".join(tooltip_parts)

    with open("/tmp/sensorinfo", "w", encoding="utf-8") as f:
        f.write(tooltip)

    return {"text": text, "tooltip": tooltip}


def read_sensors():
    """Return sensor readings shaped like `sensors -j`, or None when there are none."""
    try:
        import sensors

        sensors.init()
        sensors_data = {}
        for chip in sensors.iter_detected_chips():
            chip_name = str(chip)
            sensors_data[chip_name] = {}
            for feature in chip:
                label = feature.label
                value = feature.get_value()
                sensors_data[chip_name][label] = value
        return sensors_data or None
    except ImportError:
        pass
    # Fallback to subprocess if python-sensors is not available. `sensors` exits 1
    # when it finds nothing, which is normal in a VM or before sensors-detect.
    try:
        result = subprocess.run(
            ["sensors", "-j"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        )
        return json.loads(result.stdout) or None
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def no_sensors():
    return {
        "text": " ",
        "tooltip": "No sensors found\nInstall lm_sensors and run sensors-detect",
        "class": "no-sensors",
    }


def main():
    parser = argparse.ArgumentParser(description="Sensor Info")
    parser.add_argument(
        "--interval",
        type=float,
        default=0,
        help="Polling interval in seconds (default: 0, run once and exit; if >0, run in loop)",
    )
    parser.add_argument("--next", action="store_true", help="Go to next page")
    parser.add_argument("--prev", action="store_true", help="Go to previous page")
    args = parser.parse_args()

    while True:
        sensors_data = read_sensors()
        if sensors_data is None:
            sensor_info = no_sensors()
        else:
            total_pages = (len(sensors_data) + PAGE_SIZE - 1) // PAGE_SIZE
            page = get_current_page(total_pages)
            if args.next or args.prev:
                page = (page + (1 if args.next else -1)) % total_pages
                # Save before signalling so the refresh reads the new page
                save_current_page(page)
                subprocess.run(["pkill", f"-RTMIN+{WAYBAR_SIGNAL}", "waybar"], check=False)
                return
            result_sensors = type("Result", (), {"stdout": json.dumps(sensors_data)})()
            sensor_info = get_sensor_data(result_sensors, page)
        print(json.dumps(sensor_info, separators=(",", ":")))
        sys.stdout.flush()
        if args.interval <= 0:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
