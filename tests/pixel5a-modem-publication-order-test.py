#!/usr/bin/env python3
"""Reject unsupported Pixel 5a MPSS-before-modemsmem publication claims."""
import json
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "validation/pixel5a-modem-publication-order-audit.json"
DOWNSTREAM = {
 "repository":"LineageOS/android_kernel_google_redbull",
 "commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043",
 "driver_path":"drivers/soc/qcom/modemsmem/modemsmem.c",
 "driver_blob":"428143562894e6d8ca7b656174c72ee4b096f510",
 "dt_path":"arch/arm64/boot/dts/google/lito-redbull-common.dtsi",
 "dt_blob":"9eea9dc7431c5ef6cc68f100789402c025b558ce",
 "defconfig_path":"arch/arm64/configs/redbull_defconfig",
 "defconfig_blob":"55e2088384d7189da77f5cd31ccf11dd75e58e4d",
 "config":"CONFIG_MODEMSMEM=m",
 "compatible":"modemsmem",
 "modem_probe_steps":["smem_alloc_accept_eexist","smem_get_size_check",
     "memset_io_64_bytes","populate_version_platform_and_flags",
     "sysfs_create_group_nonfatal"],
 "module_init_registers_platform_driver":True,
 "modem_probe_deferred_until_mpss_ready":False,
}
MAINLINE = {
 "repository":"torvalds/linux",
 "commit":"500df175a7f9e6bc1a9c328590ca5150f84f9ff0",
 "pas_driver_path":"drivers/remoteproc/qcom_q6v5_pas.c",
 "pas_driver_blob":"cb3e51d6f7cecbe5c2f5b72059001efab047f089",
 "remoteproc_core_path":"drivers/remoteproc/remoteproc_core.c",
 "remoteproc_core_blob":"527996e8ecdaaa840738b74b911a1192d769045c",
 "pas_probe_checks_scm":True,
 "pas_probe_assigns_auto_boot":True,
 "pas_probe_registers_rproc":True,
 "rproc_add_may_trigger_async_autoboot":True,
 "explicit_modemsmem_dependency_observed":False,
}
UNCERTAIN = {
 "vendor_item_134_before_mpss_start",
 "vendor_item_134_publication_completion_or_memory_visibility",
 "pixel5a_firmware_owns_existing_item_134",
 "modemsmem_platform_driver_probe_before_pas_probe",
 "device_links_supplier_consumer_correctness",
 "crash_recovery_requires_item_republication",
 "modemsmem_sysfs_and_probe_remove_cleanup",
 "stock_android12l_binary_equivalence",
 "cellular_calls_sms_data_or_modem_boot",
}
REQUIREMENTS = {
 "identify_pixel5a_authoritative_boot_and_firmware_contract",
 "define_vendor_item_owner_and_reprobe_rule",
 "enforce_start_dependency_covering_autoboot_manual_and_recovery",
 "synchronize_publication_and_crash_restart_under_verified_locks",
 "perform_actual_kernel_integration_build_and_recovery_tests_before_device_activation",
}
PERMISSIONS = {"permit_smem_write","permit_smem_alloc","permit_pas_enable",
               "permit_kernel_driver_registration","permit_device_flash"}

def violations(data):
    problems = []
    if (data.get("schema_version"),data.get("device"),data.get("classification")) != (
            1,"Pixel 5a barbet","source_only_no_order_guarantee"):
        problems.append("scope promoted")
    if data.get("downstream") != DOWNSTREAM:
        problems.append("downstream provenance or probe sequence changed")
    if data.get("mainline") != MAINLINE:
        problems.append("PAS or remoteproc source contract changed")
    if set(data.get("not_established",[])) != UNCERTAIN:
        problems.append("unproven ordering or runtime limitation omitted")
    if set(data.get("minimum_future_requirements",[])) != REQUIREMENTS:
        problems.append("integration prerequisite omitted")
    grants = data.get("authorization",{})
    if set(grants) != PERMISSIONS or any(grants.get(k) is not False for k in PERMISSIONS):
        problems.append("unsafe activation or write permission")
    if data.get("hardware_verified") is not False:
        problems.append("unsupported hardware verification")
    return problems

class OrderingEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FILE.read_text(encoding="utf8"))
    def test_baseline(self):
        self.assertEqual(violations(self.data),[])
    def test_downstream_commit(self):
        self.data["downstream"]["commit"]="unverified"
        self.assertIn("downstream provenance or probe sequence changed",violations(self.data))
    def test_modemsmem_module(self):
        self.data["downstream"]["config"]="CONFIG_MODEMSMEM=y"
        self.assertIn("downstream provenance or probe sequence changed",violations(self.data))
    def test_claims_ordering_dependency(self):
        self.data["mainline"]["explicit_modemsmem_dependency_observed"]=True
        self.assertIn("PAS or remoteproc source contract changed",violations(self.data))
    def test_hides_async_autoboot(self):
        self.data["mainline"]["rproc_add_may_trigger_async_autoboot"]=False
        self.assertIn("PAS or remoteproc source contract changed",violations(self.data))
    def test_hides_publication_hazard(self):
        self.data["not_established"].remove("vendor_item_134_before_mpss_start")
        self.assertIn("unproven ordering or runtime limitation omitted",violations(self.data))
    def test_hides_recovery_dependency(self):
        self.data["minimum_future_requirements"].remove(
            "enforce_start_dependency_covering_autoboot_manual_and_recovery")
        self.assertIn("integration prerequisite omitted",violations(self.data))
    def test_grants_write(self):
        self.data["authorization"]["permit_smem_write"]=True
        self.assertIn("unsafe activation or write permission",violations(self.data))
    def test_grants_pas(self):
        self.data["authorization"]["permit_pas_enable"]=True
        self.assertIn("unsafe activation or write permission",violations(self.data))
    def test_hardware_ready(self):
        self.data["hardware_verified"]=True
        self.assertIn("unsupported hardware verification",violations(self.data))

if __name__ == "__main__":
    unittest.main()
