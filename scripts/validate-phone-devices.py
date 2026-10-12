#!/usr/bin/env python3
"""Validate Armada phone device manifests."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEVICES = ROOT / "devices" / "phones"

FIELDS = (
    "device_id",
    "manufacturer",
    "model",
    "codename",
    "device_class",
    "architecture",
    "soc",
    "gpu",
    "status",
)


def validate(path):
    data = json.loads(path.read_text(encoding="utf-8"))

    if type(data.get("schema_version")) is not int:
        raise ValueError("invalid schema version")

    if data["schema_version"] != 1:
        raise ValueError("unsupported schema version")

    for key in FIELDS:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("invalid field: " + key)

    if data["device_class"] != "phone":
        raise ValueError("invalid device class")

    if data["architecture"] != "aarch64":
        raise ValueError("invalid architecture")

    if data["status"] not in (
        "planned", "experimental", "supported"
    ):
        raise ValueError("invalid status")

    vendor = path.parent.parent.name
    codename = path.parent.name

    if data["codename"] != codename:
        raise ValueError("codename mismatch")

    if data["device_id"] != vendor + "-" + codename:
        raise ValueError("device ID mismatch")

    boot = data.get("boot_image")
    kernel = data.get("kernel")

    if not isinstance(boot, dict):
        raise ValueError("missing boot_image")

    if not isinstance(kernel, dict):
        raise ValueError("missing kernel")

    if boot.get("format") != "android":
        raise ValueError("invalid boot image format")

    for section, keys in (
        (boot, ("verified",)),
        (kernel, ("source_verified", "build_verified")),
    ):
        for key in keys:
            if type(section.get(key)) is not bool:
                raise ValueError("invalid boolean: " + key)

    return data["device_id"]


def main():
    manifests = sorted(DEVICES.glob("*/*/device.json"))

    if not manifests:
        print("FAIL: no manifests found", file=sys.stderr)
        return 1

    seen = set()
    failures = 0

    for path in manifests:
        try:
            identifier = validate(path)

            if identifier in seen:
                raise ValueError("duplicate device ID")

            seen.add(identifier)
            print("PASS:", identifier)

        except (OSError, ValueError, KeyError) as exc:
            print("FAIL:", path, exc, file=sys.stderr)
            failures += 1

    if failures:
        return 1

    print("Validated", len(manifests), "phone manifests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
