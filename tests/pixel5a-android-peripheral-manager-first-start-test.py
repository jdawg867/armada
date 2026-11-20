#!/usr/bin/env python3
"""Step 807 offline assertions: Android Peripheral Manager triggers are not a boot trace."""
import json
import unittest
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[1]/"validation/pixel5a-android-peripheral-manager-first-start-audit.json"
TRUE={
"esim_done_triggers_per_mgr","esim_noneed_triggers_per_mgr",
"boot_completed_fallback_triggers_per_mgr","source_comment_describes_per_mgr_as_modem_boot",
"per_mgr_running_triggers_per_proxy","init_modem_script_started_on_boot",
"init_modem_script_is_identifier_property_publisher","insmod_script_sets_ready_unconditionally",
"peripheral_manager_policy_allows_modem_ssr_device_read",
"peripheral_manager_policy_allows_sysfs_ssr_read",
"modemsmem_accepts_EEXIST","modemsmem_unconditionally_zeros_existing_item"}
FALSE={
"init_modem_script_directly_starts_modem","init_modem_script_writes_smem134",
"ready_properties_prove_driver_probe_completed",
"peripheral_manager_binary_source_inspected","init_trigger_proves_subsystem_get_modem_call",
"first_MPSS_start_exact_call_trace_verified","non_destructive_reuse_currently_implemented"}
POLICY={
"deny_start_by_default","deny_write_to_existing_item_without_authoritative_owner_agreement",
"inspect_existing_item_without_mutation_only_with_authorized_mechanism",
"do_not_infer_stale_payload_safe_to_reuse",
"require_exact_64_byte_layout_and_owner_provenance",
"require_payload_visibility_and_consumer_acknowledgement",
"require_first_start_and_recovery_order_proof",
"require_manual_approval_before_any_device_operation"}
GAPS={
"pm_service_and_pm_proxy_proprietary_implementation",
"actual_modem_start_kernel_call_origin",
"timing_of_per_mgr_vs_modemsmem_probe_completion",
"binary_vendor_boot_and_runtime_Android_services",
"item134_existing_owner_and_data_lifetime",
"safe_non_destructive_reuse_protocol",
"MPSS_payload_consumption_acknowledgement_mechanism",
"modem_restart_republication_safety",
"real_calls_SMS_mobile_data"}
def invalid(d):
    result=[]
    a=d.get("android_source",{}); k=d.get("kernel_source",{})
    if (d.get("schema_version"),d.get("step"),a.get("commit"),k.get("commit"))!=(
        1,807,"9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770",
        "929e7e2f3658867d51a1d423c7e000f5cf1d4043"):
        result.append("source pins")
    if (a.get("init_blob"),a.get("modem_script_blob"),a.get("insmod_script_blob"),
        a.get("peripheral_manager_policy_blob"),k.get("modemsmem_blob"))!=(
        "ec3c3edf7e72fb394bde8e9dc669e4a07ced854b",
        "75520c7055a56930ba4e7c1fab9fd7a2aefa1f5c",
        "a222838cc855392838a69fbd9ea3951273078658",
        "edafb01e6199964607b294d44287e9fcbfeae79f",
        "428143562894e6d8ca7b656174c72ee4b096f510"):
        result.append("blob pins")
    o=d.get("observed",{})
    if set(o)!=(TRUE|FALSE|{"init_per_mgr_service_binary","init_per_mgr_service_name"}) or any(o.get(x) is not True for x in TRUE) or any(o.get(x) is not False for x in FALSE):
        result.append("promoted unverified runtime")
    if (o.get("init_per_mgr_service_binary"),o.get("init_per_mgr_service_name"))!=("/vendor/bin/pm-service","vendor.per_mgr"):
        result.append("wrong daemon")
    p=d.get("non_destructive_requirements",{})
    if p.get("mode")!="requirements_only_not_implemented" or any(p.get(x) is not True for x in POLICY):
        result.append("unimplemented policy promotion")
    if set(d.get("unverified",[]))!=GAPS:
        result.append("missing blockers")
    safety=d.get("safety",{})
    if set(safety)!={"device_access","firmware_boot","smem_read","smem_write","flash","activate_drivers"} or any(v is not False for v in safety.values()) or d.get("hardware_tested") is not False:
        result.append("device safety")
    return result

class FirstStartSourceTests(unittest.TestCase):
    def setUp(self): self.d=json.loads(EVIDENCE.read_text())
    def test_baseline(self): self.assertEqual(invalid(self.d),[])
    def test_no_binary_visibility(self):
        self.d["observed"]["peripheral_manager_binary_source_inspected"]=True
        self.assertTrue(invalid(self.d))
    def test_no_proven_kernel_call(self):
        self.d["observed"]["init_trigger_proves_subsystem_get_modem_call"]=True
        self.assertTrue(invalid(self.d))
    def test_no_first_boot_trace(self):
        self.d["observed"]["first_MPSS_start_exact_call_trace_verified"]=True
        self.assertTrue(invalid(self.d))
    def test_esim_reset_gate_preserved(self):
        self.d["observed"]["esim_done_triggers_per_mgr"]=False
        self.assertTrue(invalid(self.d))
    def test_boot_completed_fallback_preserved(self):
        self.d["observed"]["boot_completed_fallback_triggers_per_mgr"]=False
        self.assertTrue(invalid(self.d))
    def test_modem_init_not_boot_script(self):
        self.d["observed"]["init_modem_script_directly_starts_modem"]=True
        self.assertTrue(invalid(self.d))
    def test_insmod_ready_not_probe_ack(self):
        self.d["observed"]["ready_properties_prove_driver_probe_completed"]=True
        self.assertTrue(invalid(self.d))
    def test_existing_item_reset_is_not_safe(self):
        self.d["observed"]["non_destructive_reuse_currently_implemented"]=True
        self.assertTrue(invalid(self.d))
    def test_no_stale_item_trust(self):
        self.d["non_destructive_requirements"]["do_not_infer_stale_payload_safe_to_reuse"]=False
        self.assertTrue(invalid(self.d))
    def test_no_item_write(self):
        self.d["safety"]["smem_write"]=True
        self.assertTrue(invalid(self.d))
    def test_proprietary_unknowns_preserved(self):
        self.d["unverified"].remove("pm_service_and_pm_proxy_proprietary_implementation")
        self.assertTrue(invalid(self.d))
    def test_no_hardware_access(self):
        self.d["hardware_tested"]=True
        self.assertTrue(invalid(self.d))
if __name__=="__main__":
    unittest.main()
