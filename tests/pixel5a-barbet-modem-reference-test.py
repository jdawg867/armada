#!/usr/bin/env python3
"""Fail-closed pinned barbet modem source-evidence contract. No device access."""
import json
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "validation/pixel5a-barbet-modem-reference.json"
COMMIT = "929e7e2f3658867d51a1d423c7e000f5cf1d4043"
FILES = {
 "arch/arm64/boot/dts/google/lito-v2-barbet-mp.dtsi": "277ae16bb06ebb5c945fe02a579298af45aba3ff",
 "arch/arm64/boot/dts/google/lito-barbet.dtsi": "cbfbedb711ae7bdba17e0513a8f924ce1fdaeeb1",
 "arch/arm64/boot/dts/google/lito-barbet-common.dtsi": "4aeed8583a96230c89b11ac85ec6b156abadc2db",
 "arch/arm64/boot/dts/google/lito-redbull-common.dtsi": "9eea9dc7431c5ef6cc68f100789402c025b558ce",
 "drivers/soc/qcom/modemsmem/modemsmem.c": "428143562894e6d8ca7b656174c72ee4b096f510",
 "drivers/soc/qcom/modemsmem/modemsmem.h": "a6b9d991fe7c023f44c21cc5c597746414c532a2",
 "arch/arm64/configs/redbull_defconfig": "55e2088384d7189da77f5cd31ccf11dd75e58e4d",
 "arch/arm64/boot/dts/vendor/qcom/lito-smp2p.dtsi": "9a7ba151bed5dbec01bf8013e4de3f9fafc52f11",
 "arch/arm64/boot/dts/vendor/qcom/lito.dtsi": "24b013a4b166456be0a1f8a4a278d9fb3dcfccd1",
}
CHAIN = ["lito-v2-barbet-mp.dtsi", "lito-barbet.dtsi",
         "lito-barbet-common.dtsi", "lito-redbull-common.dtsi"]
UNVERIFIED = {"google stock barbet Android 12L exact source inclusion",
              "pixel 5a DTB compilation result",
              "modemsmem module load or correct SMEM init ordering",
              "mainline Linux 7.2.6 driver and DT binding port",
              "modem startup and phone calls/SMS/data"}

def audit(m):
    problems = []
    if (m.get("schema_version"), m.get("device"), m.get("reference_commit")) != (1, "barbet", COMMIT):
        problems.append("target or commit changed")
    if m.get("reference_repository") != "LineageOS/android_kernel_google_redbull":
        problems.append("unrecognized source")
    if m.get("scope") != "pinned_lineage_redbull_source_not_stock_android12l_or_hardware":
        problems.append("scope promoted beyond available evidence")
    if any(m.get(k) is not False for k in
           ("hardware_verified", "modem_ready", "driver_activation_authorized")):
        problems.append("unsupported hardware readiness/activation")
    if set(m.get("unverified", [])) != UNVERIFIED:
        problems.append("unverified limitations missing")
    records = m.get("source_files", [])
    if not isinstance(records, list):
        return problems + ["source files not array"]
    by_path = {}
    for f in records:
        if not isinstance(f, dict) or not isinstance(f.get("path"), str):
            problems.append("invalid record")
            continue
        p = f["path"]
        if p in by_path:
            problems.append("duplicate source record")
        by_path[p] = f
        if FILES.get(p) != f.get("blob"):
            problems.append("unpinned or altered source blob: " + p)
    if set(by_path) != set(FILES):
        problems.append("source file set incomplete")
    dts = "arch/arm64/boot/dts/google/"
    for parent, child in zip(CHAIN, CHAIN[1:]):
        f = by_path.get(dts + parent, {})
        if child not in f.get("includes", []):
            problems.append("include chain missing: " + parent)
    node = by_path.get(dts + "lito-redbull-common.dtsi", {})
    if (node.get("node"), node.get("compatible")) != ("modemsmem", "modemsmem"):
        problems.append("modemsmem node mismatch")
    drv = by_path.get("drivers/soc/qcom/modemsmem/modemsmem.c", {})
    if set(drv.get("uses", [])) != {"qcom_smem_alloc", "qcom_smem_get",
                                    "socinfo_get_g_platform_type"}:
        problems.append("modemsmem implementation mismatch")
    header = by_path.get("drivers/soc/qcom/modemsmem/modemsmem.h", {})
    if header.get("smem_item") != 134:
        problems.append("vendor SMEM ID mismatch")
    config = by_path.get("arch/arm64/configs/redbull_defconfig", {})
    if config.get("config") != "CONFIG_MODEMSMEM=m":
        problems.append("module config mismatch")
    smp = by_path.get("arch/arm64/boot/dts/vendor/qcom/lito-smp2p.dtsi", {})
    if (smp.get("mpss_smem"), smp.get("local_pid"), smp.get("remote_pid"),
        smp.get("interrupt_parent"), smp.get("mailbox_client"),
        smp.get("mailbox_signal")) != ([435,428], 0, 1, "ipcc_mproc",
                                        "IPCC_CLIENT_MPSS", "IPCC_MPROC_SIGNAL_SMP2P"):
        problems.append("MPSS SMP2P source mismatch")
    modem = by_path.get("arch/arm64/boot/dts/vendor/qcom/lito.dtsi", {}).get("mpass", {})
    if modem != {"pas_id":4,"smem_id":421,"watchdog_spi":266,"ipcc_spi":229,
                 "compatible":"qcom,pil-tz-generic","firmware":"modem",
                 "memory_region":"modem_wlan_mem"}:
        problems.append("MPSS PAS/IPCC source mismatch")
    return problems

class Tests(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(FILE.read_text(encoding="utf-8"))
    def assertProblem(self, expected):
        self.assertIn(expected, audit(self.m))
    def test_baseline(self):
        self.assertEqual(audit(self.m), [])
    def test_modified_source_sha(self):
        self.m["source_files"][0]["blob"] = "unknown"
        self.assertTrue(any("unpinned or altered" in p for p in audit(self.m)))
    def test_missing_include(self):
        self.m["source_files"][0]["includes"] = []
        self.assertTrue(any("include chain missing" in p for p in audit(self.m)))
    def test_wrong_smp2p_direction(self):
        self.m["source_files"][7]["mpss_smem"] = [428,435]
        self.assertProblem("MPSS SMP2P source mismatch")
    def test_wrong_vendor_smem(self):
        self.m["source_files"][5]["smem_item"] = 421
        self.assertProblem("vendor SMEM ID mismatch")
    def test_false_stock_source_claim(self):
        self.m["scope"] = "google_stock_verified"
        self.assertProblem("scope promoted beyond available evidence")
    def test_false_ready(self):
        self.m["modem_ready"] = True
        self.assertProblem("unsupported hardware readiness/activation")
    def test_false_enable(self):
        self.m["driver_activation_authorized"] = True
        self.assertProblem("unsupported hardware readiness/activation")
    def test_unverified_removed(self):
        self.m["unverified"].pop()
        self.assertProblem("unverified limitations missing")

if __name__ == "__main__":
    unittest.main()
