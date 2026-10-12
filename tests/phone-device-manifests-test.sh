#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "===== PHONE MANIFEST VALIDATION ====="
python3 "$ROOT/scripts/validate-phone-devices.py"

echo "===== NEGATIVE VALIDATION TESTS ====="

python3 - "$ROOT" <<'INNER'
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
script = root / "scripts/validate-phone-devices.py"

spec = importlib.util.spec_from_file_location(
    "phone_validator", script
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

original = json.loads(
    (root / "devices/phones/google/barbet/device.json").read_text()
)

def rejected(change):
    data = json.loads(json.dumps(original))
    change(data)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "google/barbet/device.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(data))

        try:
            module.validate(path)
        except (ValueError, KeyError):
            return

        raise AssertionError("Invalid manifest was accepted")

rejected(lambda d: d.update(schema_version=2))
rejected(lambda d: d.update(architecture="x86_64"))
rejected(lambda d: d.update(codename="wrong"))
rejected(lambda d: d.update(status="unknown"))
rejected(lambda d: d["kernel"].update(build_verified="yes"))
rejected(lambda d: d.pop("boot_image"))

print("PASS: six invalid manifests rejected")
INNER

echo "Phone device manifest tests passed"
