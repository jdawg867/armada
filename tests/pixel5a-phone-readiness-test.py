#!/usr/bin/env python3
"""Fail-closed Pixel 5a phone-function evidence gate (metadata-only; no ADB)."""
import json
from pathlib import Path
import sys
import unittest

PATH = Path(__file__).resolve().parents[1] / "validation/pixel5a-phone-capabilities.json"
REQUIRED = {
    "voice_calls", "sms", "mms", "mobile_data", "emergency_calls",
    "wifi", "bluetooth", "gnss", "touchscreen", "display", "audio",
    "cameras", "battery_charging", "suspend_resume", "sensors",
    "fingerprint", "nfc", "notifications", "recovery"
}
MANDATORY = REQUIRED - {"fingerprint", "nfc"}
VALID_STATUSES = {"not_tested", "blocked", "failed", "passed"}

def validate(m):
    errors = []
    if m.get("schema_version") != 1 or m.get("codename") != "barbet" or m.get("soc") != "SM7250":
        errors.append("invalid target/schema")
    if m.get("purpose") != "daily-driver smartphone":
        errors.append("phone use must remain the goal")
    capabilities = m.get("capabilities")
    if not isinstance(capabilities, list):
        return errors + ["capabilities must be list"]
    by_id = {}
    for item in capabilities:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            errors.append("malformed capability")
            continue
        ident = item["id"]
        if ident in by_id:
            errors.append("duplicate capability: " + ident)
        by_id[ident] = item
        status = item.get("status")
        evidence = item.get("evidence")
        if status not in VALID_STATUSES:
            errors.append("unknown status: " + ident)
        if not isinstance(item.get("requirement"), str) or not item["requirement"].strip():
            errors.append("missing requirement: " + ident)
        if not isinstance(evidence, list) or any(not isinstance(x, str) or not x.strip() for x in evidence):
            errors.append("invalid evidence list: " + ident)
        if status == "passed" and (not evidence or any(not x.strip() for x in evidence)):
            errors.append("passed without evidence: " + ident)
        if ident in REQUIRED and item.get("mandatory") is not (ident in MANDATORY):
            errors.append("incorrect mandatory flag: " + ident)
    if set(by_id) != REQUIRED:
        errors.append("capability set mismatch missing=" + repr(sorted(REQUIRED - set(by_id))) +
                      " extra=" + repr(sorted(set(by_id) - REQUIRED)))
    for field in ("hardware_testing_authorized", "driver_activation_authorized",
                  "firmware_modification_authorized", "release_ready"):
        if type(m.get(field)) is not bool:
            errors.append("invalid boolean gate: " + field)
    # A release claim needs independent permission to test hardware and evidence
    # from every mandatory capability; this gate does not grant permission.
    if m.get("release_ready"):
        if not m.get("hardware_testing_authorized"):
            errors.append("release without hardware authorization")
        for ident in MANDATORY:
            item = by_id.get(ident, {})
            if item.get("status") != "passed" or not item.get("evidence"):
                errors.append("release blocked: " + ident)
    if m.get("phase") == "source-research":
        if any(m.get(f) for f in ("hardware_testing_authorized", "driver_activation_authorized",
                                  "firmware_modification_authorized", "release_ready")):
            errors.append("source-research must not authorize hardware, activation or release")
        if any(item.get("status") == "passed" for item in by_id.values()):
            errors.append("source-research cannot assert phone hardware PASS")
    return errors

class GateTests(unittest.TestCase):
    def setUp(self):
        self.base = json.loads(PATH.read_text(encoding="utf-8"))
    def test_current_manifest(self):
        self.assertEqual(validate(self.base), [])
    def test_release_without_phone_fails(self):
        self.base["phase"] = "device-validation"
        self.base["release_ready"] = True
        self.assertTrue(any("release blocked:" in x for x in validate(self.base)))
    def test_unsubstantiated_pass_fails(self):
        self.base["phase"] = "device-validation"
        self.base["capabilities"][0]["status"] = "passed"
        self.assertTrue(any("without evidence" in x for x in validate(self.base)))
    def test_disabled_hardware_in_research(self):
        self.base["hardware_testing_authorized"] = True
        self.assertTrue(any("source-research" in x for x in validate(self.base)))
    def test_duplicate_fails(self):
        self.base["capabilities"].append(dict(self.base["capabilities"][0]))
        self.assertTrue(any("duplicate" in x for x in validate(self.base)))
    def test_missing_fails(self):
        self.base["capabilities"].pop()
        self.assertTrue(any("capability set mismatch" in x for x in validate(self.base)))
    def test_nonmandatory_does_not_satisfy_core(self):
        self.base["phase"] = "device-validation"
        self.base["release_ready"] = True
        self.base["hardware_testing_authorized"] = True
        for item in self.base["capabilities"]:
            if not item["mandatory"]:
                item["status"] = "passed"
                item["evidence"] = ["example-hardware-run"]
        self.assertTrue(any("release blocked: voice_calls" == x for x in validate(self.base)))

if __name__ == "__main__":
    result = unittest.main(exit=False)
    sys.exit(0 if result.result.wasSuccessful() else 1)
