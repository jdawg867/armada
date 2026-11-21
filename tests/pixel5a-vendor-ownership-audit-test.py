#!/usr/bin/env python3
"""Fail-closed source contract for the non-publishing modem vendor item audit."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "research/pixel5a-modemsmem/kernel_vendor_ownership_audit.h"
PROBE = ROOT / "research/pixel5a-modemsmem/modemsmem_kernel_header_probe.c"

def strip_comments(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)

def validate(header, probe):
    errors = []
    code = strip_comments(header)
    for signature in (
        "ARMADA_VENDOR_AUDIT_ITEM 134U",
        "ARMADA_VENDOR_AUDIT_SIZE 64U",
        "ARMADA_VENDOR_PRESENT_UNOWNED",
        "ARMADA_VENDOR_ABSENT_UNOWNED",
        "ARMADA_VENDOR_UNAVAILABLE",
        "ARMADA_VENDOR_INVALID_SIZE",
        "ARMADA_VENDOR_OTHER_ERROR",
        "armada_modemsmem_kernel_get(",
        "ret == -EPROBE_DEFER",
        "ret == -ENXIO || ret == -ENOENT",
        "length != ARMADA_VENDOR_AUDIT_SIZE",
    ):
        if signature not in code:
            errors.append("missing evidence contract: " + signature)
    if re.search(r"\b(?:qcom_smem_alloc|armada_modemsmem_kernel_alloc|memset_io|memcpy_toio|writel|rproc_boot|module_init|platform_driver_register)\s*\(",code):
        errors.append("unsafe write, allocate, or activation call")
    if 'armada_vendor_item_inspect(&observation)' not in probe:
        errors.append("not compiled by real kernel probe")
    return errors

class OwnershipAuditTests(unittest.TestCase):
    def setUp(self):
        self.h = PATH.read_text()
        self.p = PROBE.read_text()
    def test_baseline(self):
        self.assertEqual(validate(self.h,self.p),[])
    def test_forbid_allocation(self):
        self.assertTrue(validate(self.h+"\nqcom_smem_alloc(0,134,64);",self.p))
    def test_forbid_overwrite(self):
        self.assertTrue(validate(self.h+"\nmemcpy_toio(0,0,64);",self.p))
    def test_missing_unowned_state(self):
        self.assertTrue(validate(self.h.replace("ARMADA_VENDOR_PRESENT_UNOWNED","OWNED"),self.p))
    def test_missing_defer(self):
        self.assertTrue(validate(self.h.replace("ret == -EPROBE_DEFER","ret == 0"),self.p))
    def test_missing_absence(self):
        self.assertTrue(validate(self.h.replace("ret == -ENXIO || ret == -ENOENT","ret == -ENXIO"),self.p))
    def test_missing_size(self):
        self.assertTrue(validate(self.h.replace("length != ARMADA_VENDOR_AUDIT_SIZE","length == ARMADA_VENDOR_AUDIT_SIZE"),self.p))
    def test_probe_wiring(self):
        self.assertTrue(validate(self.h,self.p.replace("armada_vendor_item_inspect(&observation)","return 0")))
if __name__ == "__main__":
    unittest.main()
