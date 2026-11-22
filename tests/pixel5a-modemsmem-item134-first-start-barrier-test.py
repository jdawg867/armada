#!/usr/bin/env python3
"""Step 828: pinned item134 probe source audit, offline only."""
import copy
import json
import unittest
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "validation/pixel5a-modemsmem-item134-first-start-barrier-audit.json"
PINS = {"kernel_repo":"LineageOS/android_kernel_google_redbull",
"kernel_commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043",
"modemsmem_source":"drivers/soc/qcom/modemsmem/modemsmem.c",
"modemsmem_source_blob":"428143562894e6d8ca7b656174c72ee4b096f510",
"modemsmem_header":"drivers/soc/qcom/modemsmem/modemsmem.h",
"modemsmem_header_blob":"a6b9d991fe7c023f44c21cc5c597746414c532a2",
"android_repo":"LineageOS/android_device_google_redbull",
"android_commit":"9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770",
"hardware_rc":"init.hardware.rc",
"hardware_rc_blob":"ec3c3edf7e72fb394bde8e9dc669e4a07ced854b",
"modem_script":"init.modem.sh",
"modem_script_blob":"75520c7055a56930ba4e7c1fab9fd7a2aefa1f5c"}
CI = {"step827_commit":"bded58acacaa68c24b872f559d0eee4ad700102c",
"android_validation":{"id":44973489923,"conclusion":"success"},
"aosp_source":{"id":44973489907,"conclusion":"success"},
"arm64_compile":{"id":44973489900,"conclusion":"success"}}
FIELDS = {"smem_id_symbol":"SMEM_ID_VENDOR0","smem_item_number":134,"modem_smem_version":0}
YES = {"probe_uses_qcom_smem_alloc","probe_accepts_EEXIST","probe_uses_qcom_smem_get","probe_checks_expected_struct_size","probe_memset_io_zeroes_struct","probe_sets_version_platform_socinfo_fields","probe_conditionally_sets_modem_flag_from_cdt","probe_conditionally_sets_ftm_and_dsds_magic","probe_sysfs_group_failure_logged_but_probe_returns_zero","module_init_registers_platform_driver"}
NO = {"module_init_implies_probe_completed","probe_publishes_a_ready_property","probe_signals_first_modem_start_barrier","android_init_waits_on_item134_ack","per_mgr_binary_start_order_proven","item134_modem_consumption_acknowledged","live_radio_recovery_verified"}
UNKNOWN = {"effective_probe_success_and_platform_device_binding","whether_earlier_modem_boot_or_restart_races_item134_initialization","vendor_per_mgr_binary_and_modem_subsystem_get_request_timing","SMEM_item134_remote_consumer_contract_and_ack","SMEM_restart_republication_and_memory_ordering","real_calls_SMS_cellular_data_and_SSR_recovery"}
SAFE={"adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}

def violations(d):
    result=[]
    if (d.get("schema_version"),d.get("step"),d.get("scope")) != (1,828,"pinned_modemsmem_item134_probe_publication_without_proven_first_MPSS_barrier"):result.append("scope")
    if d.get("pinned_sources") != PINS:result.append("pins")
    if d.get("ci") != CI:result.append("ci")
    observed=d.get("observed",{})
    if set(observed) != set(FIELDS)|YES|NO:result.append("schema")
    if any(observed.get(k)!=v for k,v in FIELDS.items()):result.append("fields")
    if any(observed.get(k) is not True for k in YES):result.append("source behavior")
    if any(observed.get(k) is not False for k in NO):result.append("runtime overclaim")
    if set(d.get("unknowns",[]))!=UNKNOWN:result.append("unknowns")
    safety=d.get("safety",{})
    if set(safety)!=SAFE or any(v is not False for v in safety.values()) or d.get("hardware_tested") is not False:result.append("unsafe")
    return result

class Item134Tests(unittest.TestCase):
    def setUp(self):self.data=json.loads(P.read_text(encoding="utf-8"))
    def reject(self,group,key,value):
        d=copy.deepcopy(self.data);d[group][key]=value;self.assertTrue(violations(d))
    def test_baseline(self):self.assertEqual(violations(self.data),[])
    def test_kernel_pin(self):self.reject("pinned_sources","kernel_commit","tip")
    def test_source_pin(self):self.reject("pinned_sources","modemsmem_source_blob","tip")
    def test_header_pin(self):self.reject("pinned_sources","modemsmem_header_blob","tip")
    def test_android_pin(self):self.reject("pinned_sources","hardware_rc_blob","tip")
    def test_ci_pin(self):self.reject("ci","step827_commit","latest")
    def test_item(self):self.reject("observed","smem_item_number",135)
    def test_id_symbol(self):self.reject("observed","smem_id_symbol","SMEM_ID_VENDOR1")
    def test_alloc(self):self.reject("observed","probe_uses_qcom_smem_alloc",False)
    def test_eexist(self):self.reject("observed","probe_accepts_EEXIST",False)
    def test_get(self):self.reject("observed","probe_uses_qcom_smem_get",False)
    def test_size(self):self.reject("observed","probe_checks_expected_struct_size",False)
    def test_zeroing(self):self.reject("observed","probe_memset_io_zeroes_struct",False)
    def test_fields(self):self.reject("observed","probe_sets_version_platform_socinfo_fields",False)
    def test_modem_flag(self):self.reject("observed","probe_conditionally_sets_modem_flag_from_cdt",False)
    def test_bootmode(self):self.reject("observed","probe_conditionally_sets_ftm_and_dsds_magic",False)
    def test_sysfs_not_fatal(self):self.reject("observed","probe_sysfs_group_failure_logged_but_probe_returns_zero",False)
    def test_registration(self):self.reject("observed","module_init_registers_platform_driver",False)
    def test_registration_not_probe(self):self.reject("observed","module_init_implies_probe_completed",True)
    def test_no_ready_property(self):self.reject("observed","probe_publishes_a_ready_property",True)
    def test_no_start_barrier(self):self.reject("observed","probe_signals_first_modem_start_barrier",True)
    def test_no_init_ack(self):self.reject("observed","android_init_waits_on_item134_ack",True)
    def test_no_manager_order(self):self.reject("observed","per_mgr_binary_start_order_proven",True)
    def test_no_consumer_ack(self):self.reject("observed","item134_modem_consumption_acknowledged",True)
    def test_no_radio_proof(self):self.reject("observed","live_radio_recovery_verified",True)
    def test_unknowns(self):
        d=copy.deepcopy(self.data);d["unknowns"].pop();self.assertTrue(violations(d))
    def test_no_read(self):self.reject("safety","smem_read",True)
    def test_no_write(self):self.reject("safety","smem_write",True)
    def test_no_flash(self):self.reject("safety","flash",True)

if __name__=="__main__":unittest.main()
