#!/usr/bin/env python3
"""Source-only contract checks; real ARM64 compatibility uses separate Kbuild CI."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEADER = ROOT / "research/pixel5a-modemsmem/kernel_readonly_preflight.h"
PROBE = ROOT / "research/pixel5a-modemsmem/modemsmem_kernel_header_probe.c"

FORBIDDEN = (
    r"\bqcom_smem_alloc\s*\(",
    r"\barmada_modemsmem_kernel_alloc\s*\(",
    r"\b(?:memcpy_toio|memset_io|writel|writeb|rproc_boot|"
    r"platform_driver_register|module_init|request_firmware)\s*\(",
)

def audit(source, probe):
    errors = []
    for pattern in FORBIDDEN:
        if re.search(pattern, source):
            errors.append("forbidden publication or activation in preflight")
    for marker in (
        "ARMADA_VENDOR_SMEM_ITEM 134U",
        "ARMADA_VENDOR_SMEM_LENGTH 64U",
        "ARMADA_SOCINFO_PREFIX_LENGTH 68U",
        "SMEM_HW_SW_BUILD_ID",
        "armada_modemsmem_kernel_get",
        "get_unaligned_le32",
        "vendor_size != ARMADA_VENDOR_SMEM_LENGTH",
        "if (ret)",
        "return -EMSGSIZE;",
        "return -EOPNOTSUPP;",
        "*result = candidate;",
    ):
        if marker not in source:
            errors.append("missing guard: " + marker)
    if source.count("armada_modemsmem_kernel_get(") != 2:
        errors.append("expected only two read-only lookups")
    if source.index("*result = candidate;") < source.index(
        "vendor_size != ARMADA_VENDOR_SMEM_LENGTH"
    ):
        errors.append("candidate published before vendor size check")
    if "#include \"kernel_readonly_preflight.h\"" not in probe or (
        "armada_pixel5a_readonly_preflight(&candidate)" not in probe
    ):
        errors.append("compile probe not wired to preflight")
    return errors

class ReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.source = HEADER.read_text()
        self.probe = PROBE.read_text()
    def test_baseline(self):
        self.assertEqual(audit(self.source, self.probe), [])
    def test_allocation_rejected(self):
        self.assertTrue(audit(self.source + "\nqcom_smem_alloc(0,134,64);", self.probe))
    def test_publication_rejected(self):
        self.assertTrue(audit(self.source + "\nmemcpy_toio(0,0,64);", self.probe))
    def test_remoteproc_start_rejected(self):
        self.assertTrue(audit(self.source + "\nrproc_boot(0);", self.probe))
    def test_missing_vendor_size_guard(self):
        self.assertTrue(audit(
            self.source.replace("vendor_size != ARMADA_VENDOR_SMEM_LENGTH",
                                "vendor_size == ARMADA_VENDOR_SMEM_LENGTH"),
            self.probe))
    def test_preflight_not_compiled(self):
        self.assertTrue(audit(self.source, self.probe.replace(
            "armada_pixel5a_readonly_preflight(&candidate)", "return 0")))
    def test_invalid_format_guard_removed(self):
        self.assertTrue(audit(self.source.replace("return -EOPNOTSUPP;", "return 0;"),
                              self.probe))

if __name__ == "__main__":
    unittest.main()
