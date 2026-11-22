#!/usr/bin/env python3
"""Step 789: source-pinned Lineage Barbet/Redbull module init audit, fail closed."""
import copy
import json
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/"validation/pixel5a-barbet-module-load-evidence.json"
BARBET={
"repository":"LineageOS/android_device_google_barbet",
"commit":"24101a383bb1951952adcd6f62668338dd048f03",
"files":{
"init.insmod.barbet.cfg":"f2728df28091a374ff6bfa6e4e50f3695420e722",
"barbet/init.barbet.rc":"e90914410f21493621e2f6ac6c3e00e117ed9c9c",
"device-barbet.mk":"750a8be1c808ec4e861e2627059d7022d0507560"}}
REDBULL={
"repository":"LineageOS/android_device_google_redbull",
"commit":"9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770",
"files":{
"modules.load":"b116d1f234682a1f7e7275f36e6c7a2feb79ddb5",
"BoardConfig-common.mk":"a70253537c0da383ac0c96c9f02f526faba89ef4",
"BoardConfigLineage.mk":"73921b90f308b6adbf6ba6b0d31c563eedede37e",
"init.hardware.rc":"ec3c3edf7e72fb394bde8e9dc669e4a07ced854b",
"init.insmod.sh":"a222838cc855392838a69fbd9ea3951273078658"}}
OBSERVED={
"boot_module_list_contains_modemsmem":True,
"boot_module_list_contains_smem":True,
"boot_module_list_contains_subsys_pil_tz":True,
"board_config_distinguishes_first_stage_modules":True,
"barbet_config_first_action":"modprobe|-b *",
"barbet_config_sets_modules_ready":True,
"barbet_config_sets_devices_ready":True,
"init_hardware_starts_insmod_sh_at_init":True,
"init_hardware_waits_on_modules_ready":True,
"init_script_modprobe_uses_vendor_modules_load":True,
"init_script_does_not_check_modprobe_status":True,
"init_script_sets_ready_even_without_config":True,
"modemsmem_precedes_qpnp_regulator_in_modules_load":True,
"modemsmem_first_stage_boot_module_listed":True,
"modemsmem_platform_probe_completion_before_pas_unproven":True,
"modemsmem_publication_fence_before_modem_boot_unproven":True}
UNCERTAIN={
"lineage_tree_matches_exact_stock_android12l_partition_contents",
"first_stage_modemsmem_module_probe_success",
"module_list_order_implies_driver_probe_completion",
"init_ready_property_implies_modemsmem_probe_success",
"mpss_pil_tz_probe_or_firmware_start_after_modemsmem_probe",
"modemsmem_64_byte_publication_happens_before_modem_reads_it",
"actual_barbet_init_boot_trace_and_uevent_probe_order",
"qcom_smem_item134_owner_reinitialization_on_crash",
"mainline_linux_7_2_6_pas_equivalent_to_downstream_subsys_pil_tz",
"kernel_modem_calls_sms_mobile_data_ready"}
SAFETY={"allow_module_loading","allow_smem_publish","allow_driver_register","allow_pas_start","allow_device_flash"}
def audit(d):
    errors=[]
    if (d.get("schema_version"),d.get("device"),d.get("classification"))!=(
      1,"Pixel 5a barbet","lineage_device_tree_module_loading_source_only_not_stock_android12l_verified"):
        errors.append("source classification promoted")
    r=d.get("repos",{})
    if r.get("barbet")!=BARBET or r.get("redbull")!=REDBULL:
        errors.append("source pinned identity changed")
    if d.get("observed")!=OBSERVED:
        errors.append("module-init evidence changed")
    if set(d.get("not_established",[]))!=UNCERTAIN:
        errors.append("missing unresolved ordering/hardware caveat")
    policy=d.get("safety",{})
    if set(policy)!=SAFETY or any(v is not False for v in policy.values()):
        errors.append("unsafe module or device activation")
    if d.get("hardware_verified") is not False:
        errors.append("unsupported hardware claim")
    return errors

class BarbetInitEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.d=json.loads(PATH.read_text(encoding="utf8"))
    def test_baseline(self):
        self.assertEqual(audit(self.d),[])
    def test_pinned_file_tampering(self):
        self.d["repos"]["redbull"]["files"]["modules.load"]="unknown"
        self.assertIn("source pinned identity changed",audit(self.d))
    def test_unproven_stock_equivalence(self):
        self.d["classification"]="verified_stock_android12l"
        self.assertIn("source classification promoted",audit(self.d))
    def test_modprobe_failure_not_observed(self):
        self.d["observed"]["init_script_does_not_check_modprobe_status"]=False
        self.assertIn("module-init evidence changed",audit(self.d))
    def test_modules_ready_not_probe_proof(self):
        self.d["not_established"].remove("init_ready_property_implies_modemsmem_probe_success")
        self.assertIn("missing unresolved ordering/hardware caveat",audit(self.d))
    def test_first_stage_not_assumed_success(self):
        self.d["not_established"].remove("first_stage_modemsmem_module_probe_success")
        self.assertIn("missing unresolved ordering/hardware caveat",audit(self.d))
    def test_pil_not_mainline_pas(self):
        self.d["not_established"].remove("mainline_linux_7_2_6_pas_equivalent_to_downstream_subsys_pil_tz")
        self.assertIn("missing unresolved ordering/hardware caveat",audit(self.d))
    def test_publish_not_authorized(self):
        self.d["safety"]["allow_smem_publish"]=True
        self.assertIn("unsafe module or device activation",audit(self.d))
    def test_hardware_not_tested(self):
        self.d["hardware_verified"]=True
        self.assertIn("unsupported hardware claim",audit(self.d))
    def test_no_false_order(self):
        self.d["observed"]["modemsmem_platform_probe_completion_before_pas_unproven"]=False
        self.assertIn("module-init evidence changed",audit(self.d))
if __name__=="__main__":
    unittest.main()
