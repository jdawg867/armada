#!/usr/bin/env python3
"""Step 820 Barbet DT/module evidence: no ADB, build, load or modem access."""
import copy
import json
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-barbet-modem-bus-overlay-module-order-audit.json"
PINS={
 "kernel_repo":"LineageOS/android_kernel_google_redbull",
 "kernel_commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043",
 "google_dt_makefile":"arch/arm64/boot/dts/google/Makefile",
 "google_dt_makefile_blob":"852a844e147eba2dc9f2a2cf7b2483ff3e91894e",
 "barbet_mp_overlay":"arch/arm64/boot/dts/google/lito-v2-barbet-mp-overlay.dts",
 "barbet_mp_overlay_blob":"12c699a75dd1e8d3815e98b0e0ba59e454f14c08",
 "barbet_mp_dtsi":"arch/arm64/boot/dts/google/lito-v2-barbet-mp.dtsi",
 "barbet_mp_dtsi_blob":"277ae16bb06ebb5c945fe02a579298af45aba3ff",
 "barbet_dtsi":"arch/arm64/boot/dts/google/lito-barbet.dtsi",
 "barbet_dtsi_blob":"cbfbedb711ae7bdba17e0513a8f924ce1fdaeeb1",
 "barbet_common_dtsi":"arch/arm64/boot/dts/google/lito-barbet-common.dtsi",
 "barbet_common_blob":"4aeed8583a96230c89b11ac85ec6b156abadc2db",
 "lito_v2_dtsi":"arch/arm64/boot/dts/vendor/qcom/lito-v2.dtsi",
 "lito_v2_blob":"97affc51181d437ee4d37797b261b41c5fe00e24",
 "lito_dtsi":"arch/arm64/boot/dts/vendor/qcom/lito.dtsi",
 "lito_blob":"24b013a4b166456be0a1f8a4a278d9fb3dcfccd1",
 "vendor_lito_v2_dts":"arch/arm64/boot/dts/vendor/qcom/lito-v2.dts",
 "vendor_lito_v2_dts_blob":"a3da016a653d65cb310deb32aa2895615fb8b7f1",
 "android_repo":"LineageOS/android_device_google_redbull",
 "android_commit":"9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770",
 "modules_load":"modules.load",
 "modules_load_blob":"b116d1f234682a1f7e7275f36e6c7a2feb79ddb5",
 "board_common":"BoardConfig-common.mk",
 "board_common_blob":"a70253537c0da383ac0c96c9f02f526faba89ef4",
 "board_lineage":"BoardConfigLineage.mk",
 "board_lineage_blob":"73921b90f308b6adbf6ba6b0d31c563eedede37e",
}
FIELDS={
 "barbet_mp_dtbo_base":"qcom-base/lito-v2.dtb",
 "barbet_mp_overlay_includes":"lito-v2-barbet-mp.dtsi",
 "mp_dtsi_includes":"lito-barbet.dtsi",
 "barbet_dtsi_includes":"lito-barbet-common.dtsi",
 "barbet_common_includes":"lito-redbull-common.dtsi",
 "lito_v2_dtsi_includes":"lito.dtsi",
 "vendor_lito_v2_dts_includes":"lito-v2.dtsi",
 "modem_node_name":"pil_modem: qcom,mss@4080000",
 "modem_bus_name":"pil-modem",
 "modem_bus_cases":2,
 "modem_bus_paths":1,
 "published_module_list_order":["smem.ko","subsys-pil-tz.ko","msm_bus.ko","msm_bus_rpmh.ko","modemsmem.ko"],
}
TRUE={"modem_base_bus_definition_present","mp_overlay_uses_lito_v2_base_source","pil_before_bus_modules_in_source_list","bus_modules_before_modemsmem_in_source_list","board_boot_modules_lists_pil_bus_and_modemsmem","board_lineage_filters_module_basename_into_vendor_ramdisk_and_vendor_load"}
FALSE={"source_list_proves_probe_completion_order","source_list_proves_bus_client_registered_before_modem_start","all_final_barbet_dt_overrides_resolved","compiled_final_dtb_verified","installed_device_dtbo_verified","stock_module_load_execution_verified","actual_phone_modem_boot_and_item134_ready_verified"}
UNKNOWN={"complete_Barbet_overlay_property_mutations_and_final_preprocessed_DTB","compiled_base_DTB_and_MP_DTBO_effective_modem_node","effective_modules_order_after_dependencies_and_modprobe","probe_completion_of_bus_client_PIL_and_modemsmem","first_firmware_start_relative_to_bus_client_and_item134_publication","modem_recovery_and_calls_SMS_cellular_data"}
SAFE={"adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}
def violations(d):
 errors=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,820,"pinned_Barbet_MP_DT_base_includes_and_module_list_projection_not_compiled_runtime"):errors.append("scope")
 if d.get("sources")!=PINS:errors.append("sources")
 o=d.get("observed",{})
 if set(o)!=set(FIELDS)|TRUE|FALSE:errors.append("schema")
 if any(o.get(k)!=v for k,v in FIELDS.items()):errors.append("source content")
 if any(o.get(k) is not True for k in TRUE):errors.append("positive evidence")
 if any(o.get(k) is not False for k in FALSE):errors.append("runtime promotion")
 if set(d.get("unknowns",[]))!=UNKNOWN:errors.append("unknowns")
 s=d.get("safety",{})
 if set(s)!=SAFE or any(v is not False for v in s.values()) or d.get("hardware_tested") is not False:errors.append("device")
 return errors
class Step820Tests(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def reject(self,k,value,section="observed"):
  d=copy.deepcopy(self.d);d[section][k]=value;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_kernel_commit(self):self.reject("kernel_commit","tip","sources")
 def test_makefile_pin(self):self.reject("google_dt_makefile_blob","tip","sources")
 def test_overlay_pin(self):self.reject("barbet_mp_overlay_blob","tip","sources")
 def test_base_pin(self):self.reject("lito_blob","tip","sources")
 def test_module_pin(self):self.reject("modules_load_blob","tip","sources")
 def test_makefile_base(self):self.reject("barbet_mp_dtbo_base","other.dtb")
 def test_mp_overlay_include(self):self.reject("barbet_mp_overlay_includes","other.dtsi")
 def test_mp_include(self):self.reject("mp_dtsi_includes","other.dtsi")
 def test_barbet_common(self):self.reject("barbet_dtsi_includes","other.dtsi")
 def test_v2_base(self):self.reject("lito_v2_dtsi_includes","other.dtsi")
 def test_modem_name(self):self.reject("modem_node_name","other")
 def test_bus_name(self):self.reject("modem_bus_name","other")
 def test_bus_cases(self):self.reject("modem_bus_cases",1)
 def test_bus_paths(self):self.reject("modem_bus_paths",3)
 def test_module_order(self):self.reject("published_module_list_order",["modemsmem.ko"])
 def test_base_present(self):self.reject("modem_base_bus_definition_present",False)
 def test_pil_before_bus(self):self.reject("pil_before_bus_modules_in_source_list",False)
 def test_source_not_probe(self):self.reject("source_list_proves_probe_completion_order",True)
 def test_source_not_client(self):self.reject("source_list_proves_bus_client_registered_before_modem_start",True)
 def test_no_full_override(self):self.reject("all_final_barbet_dt_overrides_resolved",True)
 def test_no_compiled_dtb(self):self.reject("compiled_final_dtb_verified",True)
 def test_no_installed_dtbo(self):self.reject("installed_device_dtbo_verified",True)
 def test_no_stock_load(self):self.reject("stock_module_load_execution_verified",True)
 def test_no_telephony(self):self.reject("actual_phone_modem_boot_and_item134_ready_verified",True)
 def test_unknowns(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_modem_start(self):self.reject("modem_start",True,"safety")
 def test_no_flash(self):self.reject("flash",True,"safety")
if __name__=="__main__":unittest.main()
