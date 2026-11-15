#!/usr/bin/env python3
"""Static consistency checks for four copied SM7250 memory ranges; never probes hardware."""
import json
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "validation/pixel5a-modem-reserved-memory.json"
EXPECTED = {
    "smem_mem": (0x80900000, 0x200000),
    "ipa_fw_mem": (0x8bc00000, 0x10000),
    "ipa_gsi_mem": (0x8bc10000, 0x5400),
    "modem_wlan_mem": (0x8c000000, 0xf800000),
}
PINNED_BLOB = "8c32955827e9bd17873b5660db4cfa0037e9585c"

def audit(manifest):
    errors = []
    if (manifest.get("schema_version"), manifest.get("codename")) != (1, "barbet"):
        errors.append("wrong device/schema")
    if manifest.get("hardware_verified") is not False:
        errors.append("unsupported hardware verification claim")
    if manifest.get("source", {}).get("blob_sha") != PINNED_BLOB:
        errors.append("unrecognized pinned patch blob")
    entries = manifest.get("regions")
    if not isinstance(entries, list):
        return errors + ["regions not a list"]
    seen = set()
    ranges = []
    for entry in entries:
        try:
            name = entry["name"]
            start, size = int(entry["start"], 0), int(entry["size"], 0)
            if not isinstance(name, str) or name in seen:
                errors.append("duplicate or invalid region")
            seen.add(name)
            if start < 0 or size <= 0 or start + size > (1 << 64):
                errors.append("range outside u64: " + name)
            if name in EXPECTED and (start, size) != EXPECTED[name]:
                errors.append("pinned region mismatch: " + name)
            ranges.append((start, start + size, name))
        except (KeyError, TypeError, ValueError, AttributeError):
            errors.append("invalid region")
    if seen != set(EXPECTED):
        errors.append("missing or extra region")
    ranges.sort()
    for left, right in zip(ranges, ranges[1:]):
        if left[1] > right[0]:
            errors.append("overlap: " + left[2] + "/" + right[2])
    return errors

class StaticTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(SOURCE.read_text(encoding="utf-8"))
    def test_preserved_data(self):
        self.assertEqual(audit(self.data), [])
    def test_invalid_blob(self):
        self.data["source"]["blob_sha"] = "unverified"
        self.assertIn("unrecognized pinned patch blob", audit(self.data))
    def test_modified_range(self):
        self.data["regions"][0]["size"] = "0x100000"
        self.assertTrue(any("pinned region mismatch" in e for e in audit(self.data)))
    def test_overlap(self):
        self.data["regions"][2]["start"] = "0x8bc00000"
        self.assertTrue(any("overlap:" in e for e in audit(self.data)))
    def test_u64_limit(self):
        self.data["regions"][0]["start"] = "0xffffffffffffffff"
        self.assertTrue(any("outside u64" in e for e in audit(self.data)))
    def test_no_hardware_claim(self):
        self.data["hardware_verified"] = True
        self.assertIn("unsupported hardware verification claim", audit(self.data))
    def test_missing_region(self):
        self.data["regions"].pop()
        self.assertIn("missing or extra region", audit(self.data))

if __name__ == "__main__":
    unittest.main()
