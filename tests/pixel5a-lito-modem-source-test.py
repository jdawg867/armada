#!/usr/bin/env python3
"""Source-only Qualcomm Lito reference gate; not a Pixel 5a hardware test."""
import json
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "validation/pixel5a-lito-modem-source.json"
EXPECTED_NAMES = [
    "qcom,wdog", "qcom,err-fatal", "qcom,err-ready",
    "qcom,proxy-unvote", "qcom,stop-ack", "qcom,shutdown-ack",
]
PENDING = {"Pixel 5a barbet overlays and DTS include chain",
           "MPSS smp2p node matching/SMEM indices",
           "exact GLINK/QRTR modem control transports",
           "mainline Linux 7.2.6 remoteproc compatible translation",
           "modem firmware boot and cellular voice/data"}

def validate(data):
    problems = []
    if data.get("schema_version") != 1 or data.get("device") != "Pixel 5a (barbet)":
        problems.append("device/schema mismatch")
    if data.get("evidence_scope") != "qualcomm_lito_reference_not_pixel5a_overlay":
        problems.append("unproven Pixel overlay assertion")
    if data.get("hardware_verified") is not False or data.get("enabled") is not False:
        problems.append("hardware activation claim prohibited")
    src = data.get("source", {})
    if src.get("git_blob") != "ab7d52cf0c446049d39f01c7d494f4b1a8b33a1a" or (
        src.get("tag") != "android-11.0.0_r0.56" or src.get("path") != "qcom/lito.dtsi"
    ):
        problems.append("unrecognized pinned Lito source")
    ipcc = data.get("ipcc", {})
    if any(ipcc.get(k) != v for k,v in {
        "register_base": "0x408000", "register_size": "0x1000",
        "gic_spi": 229, "trigger": "IRQ_TYPE_LEVEL_HIGH",
        "interrupt_cells": 3, "mailbox_cells": 2}.items()):
        problems.append("IPCC Lito reference mismatch")
    mpss = data.get("mpss", {})
    if any(mpss.get(k) != v for k,v in {
        "node": "qcom,mss@4080000", "compatible": "qcom,pil-tz-generic",
        "register_base": "0x4080000", "firmware": "modem",
        "memory_region": "modem_wlan_mem", "pas_id": 4,
        "smem_id": 421, "watchdog_spi": 266,
        "aop_mailbox": "qmp_aop", "smp2p_input": "mpss_smp2p_in",
        "smp2p_output": "mpss_smp2p_out"}.items()):
        problems.append("MPSS Lito reference mismatch")
    if mpss.get("interrupt_names") != EXPECTED_NAMES:
        problems.append("modem interrupt contract mismatch")
    if set(data.get("unverified", [])) != PENDING:
        problems.append("missing unresolved hardware dependencies")
    return problems

class GateTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(FILE.read_text())
    def test_baseline(self):
        self.assertEqual(validate(self.record), [])
    def test_no_hardware_claim(self):
        self.record["hardware_verified"] = True
        self.assertIn("hardware activation claim prohibited", validate(self.record))
    def test_no_enablement(self):
        self.record["enabled"] = True
        self.assertIn("hardware activation claim prohibited", validate(self.record))
    def test_ipcc_irq_tampering(self):
        self.record["ipcc"]["gic_spi"] = 228
        self.assertIn("IPCC Lito reference mismatch", validate(self.record))
    def test_pas_id_tampering(self):
        self.record["mpss"]["pas_id"] = 5
        self.assertIn("MPSS Lito reference mismatch", validate(self.record))
    def test_no_false_pixel_overlay_claim(self):
        self.record["evidence_scope"] = "pixel5a_verified"
        self.assertIn("unproven Pixel overlay assertion", validate(self.record))
    def test_incomplete_dependencies(self):
        self.record["unverified"].pop()
        self.assertIn("missing unresolved hardware dependencies", validate(self.record))
    def test_interrupt_contract(self):
        self.record["mpss"]["interrupt_names"].pop()
        self.assertIn("modem interrupt contract mismatch", validate(self.record))

if __name__ == "__main__":
    unittest.main()
