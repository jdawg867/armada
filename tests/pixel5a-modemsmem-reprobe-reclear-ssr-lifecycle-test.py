#!/usr/bin/env python3
"""Step 829 pinned modemsmem lifecycle source assertions; no hardware operations."""
import copy,json,unittest
from pathlib import Path
FILE=Path(__file__).resolve().parents[1]/"validation/pixel5a-modemsmem-reprobe-reclear-ssr-lifecycle-audit.json"
SOURCE={"kernel_repo":"LineageOS/android_kernel_google_redbull","commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043","modemsmem_path":"drivers/soc/qcom/modemsmem/modemsmem.c","modemsmem_blob":"428143562894e6d8ca7b656174c72ee4b096f510","header_path":"drivers/soc/qcom/modemsmem/modemsmem.h","header_blob":"a6b9d991fe7c023f44c21cc5c597746414c532a2"}
CI={"previous_commit":"d11e50c14f11937d49d4bb2195a9ed65a38acf62","android_run":44980761594,"android_conclusion":"success","source_run":44980761608,"source_conclusion":"success","compile_run":44980761600,"compile_conclusion":"success"}
YES={"probe_allocates_item134","accepts_existing_item_EEXIST","gets_existing_item_after_EEXIST","zeroes_item_unconditionally_after_get","sets_fields_after_zeroing","alloc_failure_returns_ENOMEM","get_error_or_wrong_size_returns_ENOMEM","sysfs_group_creation_error_logged","sysfs_group_failure_probe_returns_success","platform_driver_register_called","platform_driver_unregister_called_at_module_exit"}
NO={"explicit_ssr_notifier_registration_in_driver","explicit_restart_republication_callback_in_driver","existing_item_zeroing_proven_safe_for_live_modem","probe_reinvoked_during_ssr_verified","smem_readiness_acknowledgment_verified","live_modem_state_corruption_verified","telephony_function_verified"}
RISK={"existing_item_reclear":"source_visible_possible_lifecycle_hazard_requires_boot_and_consumer_order_validation","sysfs_failure":"diagnostic_endpoint_failure_not_fatal_in_source","restart":"no_explicit_local_restart_handler_inspected_not_proof_of_failed_SSR"}
UNKNOWN={"first_and_repeated_probe_behavior_on_actual_Pixel5a","whether_remote_modem_reads_item134_during_any_reinitialization","whether_kernel_bus_or_platform_device_rebinds_on_SSR","external_ssr_framework_republication_and_consumer_acknowledgment","recovery_call_SMS_cellular_data_after_modem_restart","safe_isolated_patch_and_firmware_ABI_compatibility"}
SAFE={"adb","device_open","device_read","smem_read","smem_write","modem_start","flash"}
def violations(d):
    failures=[]
    if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,829,"pinned_modemsmem_error_reinitialization_and_SSR_source_lifecycle_not_hardware"):failures.append("scope")
    if d.get("sources")!=SOURCE:failures.append("source")
    if d.get("ci")!=CI:failures.append("ci")
    obs=d.get("observed",{})
    if set(obs)!=YES|NO:failures.append("schema")
    if any(obs.get(x) is not True for x in YES):failures.append("positive")
    if any(obs.get(x) is not False for x in NO):failures.append("runtime overclaim")
    if d.get("risk_classification")!=RISK:failures.append("risk")
    if set(d.get("unknowns",[]))!=UNKNOWN:failures.append("unknowns")
    safety=d.get("safety",{})
    if set(safety)!=SAFE or any(v is not False for v in safety.values()) or d.get("hardware_tested") is not False:failures.append("hardware")
    return failures
class Lifecycle(unittest.TestCase):
    def setUp(self):self.d=json.loads(FILE.read_text())
    def reject(self,section,key,value):
        d=copy.deepcopy(self.d);d[section][key]=value;self.assertTrue(violations(d))
    def test_baseline(self):self.assertEqual(violations(self.d),[])
    def test_kernel_pin(self):self.reject("sources","commit","main")
    def test_source_blob(self):self.reject("sources","modemsmem_blob","tip")
    def test_header_blob(self):self.reject("sources","header_blob","tip")
    def test_ci_pin(self):self.reject("ci","previous_commit","tip")
    def test_alloc(self):self.reject("observed","probe_allocates_item134",False)
    def test_eexist(self):self.reject("observed","accepts_existing_item_EEXIST",False)
    def test_get(self):self.reject("observed","gets_existing_item_after_EEXIST",False)
    def test_reclear(self):self.reject("observed","zeroes_item_unconditionally_after_get",False)
    def test_repopulate(self):self.reject("observed","sets_fields_after_zeroing",False)
    def test_alloc_error(self):self.reject("observed","alloc_failure_returns_ENOMEM",False)
    def test_get_error(self):self.reject("observed","get_error_or_wrong_size_returns_ENOMEM",False)
    def test_sysfs_log(self):self.reject("observed","sysfs_group_creation_error_logged",False)
    def test_sysfs_nonfatal(self):self.reject("observed","sysfs_group_failure_probe_returns_success",False)
    def test_driver_register(self):self.reject("observed","platform_driver_register_called",False)
    def test_driver_unregister(self):self.reject("observed","platform_driver_unregister_called_at_module_exit",False)
    def test_no_local_ssr_callback(self):self.reject("observed","explicit_ssr_notifier_registration_in_driver",True)
    def test_no_republish(self):self.reject("observed","explicit_restart_republication_callback_in_driver",True)
    def test_no_reclear_safety_claim(self):self.reject("observed","existing_item_zeroing_proven_safe_for_live_modem",True)
    def test_no_reprobe_claim(self):self.reject("observed","probe_reinvoked_during_ssr_verified",True)
    def test_no_ack(self):self.reject("observed","smem_readiness_acknowledgment_verified",True)
    def test_no_corruption_claim(self):self.reject("observed","live_modem_state_corruption_verified",True)
    def test_no_telephony_claim(self):self.reject("observed","telephony_function_verified",True)
    def test_risk_bounds(self):self.reject("risk_classification","restart","SSR proven faulty")
    def test_unknowns(self):
        d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
    def test_no_device_open(self):self.reject("safety","device_open",True)
    def test_no_modem_start(self):self.reject("safety","modem_start",True)
    def test_no_smem_write(self):self.reject("safety","smem_write",True)
    def test_no_flash(self):self.reject("safety","flash",True)
if __name__=="__main__":unittest.main()
