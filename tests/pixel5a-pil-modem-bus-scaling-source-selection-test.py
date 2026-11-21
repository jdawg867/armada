#!/usr/bin/env python3
"""Step 819 Redbull/Lito bus config provenance; host-only assertions."""
import copy,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-pil-modem-bus-scaling-source-selection-audit.json"
SRC={"kernel_repo":"LineageOS/android_kernel_google_redbull","commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043","pil_driver":"drivers/soc/qcom/subsys-pil-tz.c","pil_blob":"f17f9e57b0d1f671017032df9224ada0bbea15c2","lito_dtsi":"arch/arm64/boot/dts/vendor/qcom/lito.dtsi","lito_blob":"24b013a4b166456be0a1f8a4a278d9fb3dcfccd1","redbull_defconfig":"arch/arm64/configs/redbull_defconfig","redbull_defconfig_blob":"55e2088384d7189da77f5cd31ccf11dd75e58e4d","redbull_gki_defconfig":"arch/arm64/configs/redbull-gki_defconfig","redbull_gki_blob":"4e120207857deb2a5faab7fedb4bf89b874f0b50","lito_defconfig":"arch/arm64/configs/vendor/lito_defconfig","lito_defconfig_blob":"bae5311e7c3969672fb7721d308878aea686185c"}
FIELDS={"bus_scaling_symbol":"CONFIG_QCOM_BUS_SCALING","pil_driver_bus_guard":"IS_ENABLED(CONFIG_QCOM_BUS_SCALING)","redbull_bus_scaling_value":"m","redbull_gki_bus_scaling_value":"m","lito_bus_scaling_value":"m","redbull_bus_rpmh_value":"m","redbull_gki_bus_rpmh_value":"m","lito_bus_rpmh_value":"m","lito_modem_node":"pil_modem: qcom,mss@4080000","lito_modem_bus_name":"pil-modem","lito_modem_num_cases":2,"lito_modem_num_paths":1,"lito_modem_bus_vectors":"<129 512 0 0>, <129 512 0 8171520>"}
YES={"driver_pdata_requires_bus_properties","driver_registers_bus_client_from_pdata","driver_bus_client_registration_may_fail_without_error_return","build_time_bus_scaling_real_branch_selected_under_cited_defconfigs"}
NO={"live_pixel5a_bus_module_loaded_verified","final_barbet_dt_node_verified","actual_bus_client_registered_verified","device_bus_vote_failure_and_leak_observed","modemsmem_item134_ready_and_telephony_verified"}
UNKNOWN={"final_vendor_boot_flattened_barbet_modem_DT_overrides","real_loaded_module_and_effective_kernel_config","runtime_bus_client_registration_and_vote_outcomes","failed_vote_hardware_resource_ownership","upstreamable_cleanup_fix_behavior_and_test_scope","first_modem_start_vs_item134_and_phone_calls_SMS_data"}
SAFE={"adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}
def violations(d):
 bad=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,819,"pinned_Redbull_Lito_MSM_bus_scaling_defconfig_and_modem_DT_source_only"):bad.append("scope")
 if d.get("sources")!=SRC:bad.append("source")
 o=d.get("observed",{})
 if set(o)!=set(FIELDS)|YES|NO:bad.append("schema")
 if any(o.get(k)!=v for k,v in FIELDS.items()):bad.append("config")
 if any(o.get(k) is not True for k in YES):bad.append("source behavior")
 if any(o.get(k) is not False for k in NO):bad.append("runtime overclaim")
 if set(d.get("unknowns",[]))!=UNKNOWN:bad.append("unknown")
 s=d.get("safety",{})
 if set(s)!=SAFE or any(v is not False for v in s.values()) or d.get("hardware_tested") is not False:bad.append("hardware")
 return bad
class PinnedBusTests(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def reject(self,k,v,section="observed"):
  d=copy.deepcopy(self.d);d[section][k]=v;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_kernel_pin(self):self.reject("commit","main","sources")
 def test_lito_pin(self):self.reject("lito_blob","main","sources")
 def test_redbull_pin(self):self.reject("redbull_defconfig_blob","main","sources")
 def test_gki_pin(self):self.reject("redbull_gki_blob","main","sources")
 def test_symbol(self):self.reject("bus_scaling_symbol","CONFIG_MSM_BUS_SCALING")
 def test_compile_guard(self):self.reject("pil_driver_bus_guard","ifdef")
 def test_redbull_module(self):self.reject("redbull_bus_scaling_value","n")
 def test_gki_module(self):self.reject("redbull_gki_bus_scaling_value","n")
 def test_lito_module(self):self.reject("lito_bus_scaling_value","n")
 def test_redbull_rpmh_module(self):self.reject("redbull_bus_rpmh_value","n")
 def test_modem_node(self):self.reject("lito_modem_node","other")
 def test_bus_name(self):self.reject("lito_modem_bus_name","unknown")
 def test_num_cases(self):self.reject("lito_modem_num_cases",1)
 def test_num_paths(self):self.reject("lito_modem_num_paths",2)
 def test_bus_vectors(self):self.reject("lito_modem_bus_vectors","none")
 def test_pdata(self):self.reject("driver_pdata_requires_bus_properties",False)
 def test_registration(self):self.reject("driver_registers_bus_client_from_pdata",False)
 def test_register_error_contract(self):self.reject("driver_bus_client_registration_may_fail_without_error_return",False)
 def test_real_branch(self):self.reject("build_time_bus_scaling_real_branch_selected_under_cited_defconfigs",False)
 def test_no_loaded_module(self):self.reject("live_pixel5a_bus_module_loaded_verified",True)
 def test_no_final_dtb(self):self.reject("final_barbet_dt_node_verified",True)
 def test_no_client_proof(self):self.reject("actual_bus_client_registered_verified",True)
 def test_no_runtime_leak(self):self.reject("device_bus_vote_failure_and_leak_observed",True)
 def test_no_telephony_proof(self):self.reject("modemsmem_item134_ready_and_telephony_verified",True)
 def test_unknowns(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_open(self):self.reject("device_open",True,"safety")
 def test_no_flash(self):self.reject("flash",True,"safety")
if __name__=="__main__":unittest.main()
