#!/usr/bin/env python3
import argparse
from pathlib import Path

REQUIRED = (
    "CONFIG_MODULES",
    "CONFIG_BLK_DEV_INITRD",
    "CONFIG_RD_LZ4",
    "CONFIG_DEVTMPFS",
    "CONFIG_EXT4_FS",
    "CONFIG_BLK_DEV_DM",
    "CONFIG_DM_VERITY",
)

HARDWARE = (
    "CONFIG_SCSI_UFS_QCOM",
    "CONFIG_QCOM_SCM",
    "CONFIG_DRM_MSM",
    "CONFIG_USB_DWC3",
)

REVIEW = (
    "CONFIG_EROFS_FS",
    "CONFIG_SQUASHFS",
    "CONFIG_CGROUP2_FS",
    "CONFIG_CGROUP_PIDS",
    "CONFIG_OVERLAY_FS",
)

def load_config(path):
    values = {}
    for line in path.read_text().splitlines():
        if line.startswith("CONFIG_") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
        elif line.startswith("# CONFIG_") and line.endswith(" is not set"):
            key = line.split()[1]
            values[key] = "n"
    return values

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()

    config = load_config(args.config)
    failures = 0

    for name in REQUIRED:
        value = config.get(name, "n")
        passed = value == "y"
        print(("PASS" if passed else "FAIL"), name, value)
        failures += not passed

    for name in HARDWARE:
        value = config.get(name, "n")
        passed = value in ("y", "m")
        print(("FOUND" if passed else "MISSING"), name, value)
        failures += not passed

    for name in REVIEW:
        print("REVIEW", name, config.get(name, "n"))

    return int(failures > 0)

if __name__ == "__main__":
    raise SystemExit(main())
