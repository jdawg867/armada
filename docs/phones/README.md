# Armada Android Phone Platform

Experimental ARM64 Android phone support for Armada.

## Initial devices

- Google Pixel 5a (barbet): initial development target
- Google Pixel 9 Pro Fold (comet): future development target

## Current implementation

- JSON device manifests
- Python manifest validator
- Automated positive and negative tests

These manifests are metadata only.
Neither device has been verified booting Armada.

## Planned development

1. Verify kernel sources and device trees.
2. Develop Android-compatible boot image support.
3. Preserve Fedora bootc and OSTree compatibility.
4. Establish safe boot and recovery procedures.
5. Enable display, touchscreen, Wi-Fi and GPU.
6. Integrate Plasma Mobile and Steam Gaming Mode.

## Git workflow

feature/* -> development -> main

## Validation

Run: bash tests/phone-device-manifests-test.sh
