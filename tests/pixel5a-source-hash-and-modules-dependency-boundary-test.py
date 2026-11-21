#!/usr/bin/env python3
"""Step 822: CI hash recheck and pinned Kbuild evidence, offline only."""
import copy
import json
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"validation/pixel5a-source-hash-and-modules-dependency-boundary-audit.json"
CI={
 "step821_commit":"fed57a6f949270da740eb173646dbd9d9e7afba7",
 "android_validation":{"run_id":44957899973,"conclusion":"success"},
 "aosp_source":{"run_id":44957899925,"job_id":137009976814,"conclusion":"success","retrieved_diffs":3,"all_diffs_available":True,"strict_expected_sha_assertions_passed":True,"sha_mismatch_diagnostic_emitted":False},
 "arm64_compile":{"run_id":44957900008,"conclusion":"success"},
 "prior_failed_source_run_id":44954804193,
 "prior_failure_class":"AssertionError in pinned AOSP-versus-Lineage SHA comparison",
 "prior_failure_cause_established":False,
 "expected_digest_update_authorized":False,
}
SOURCE={
 "kernel_repo":"LineageOS/android_kernel_google_redbull",
 "kernel_commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043",
 "soc_makefile":"drivers/soc/qcom/Makefile",
 "soc_makefile_blob":"ba295cb355875e8a2905eea8b6f7aadead3338cf",
 "bus_makefile":"drivers/soc/qcom/msm_bus/Makefile",
 "bus_makefile_blob":"f7d007d78bd81e9e4358eaff15b186c88ef6e821",
 "modemsmem_makefile":"drivers/soc/qcom/modemsmem/Makefile",
 "modemsmem_makefile_blob":"b7c435d9f9e09a203818b3e491e8696ff212d34d",
 "soc_kconfig":"drivers/soc/qcom/Kconfig",
 "soc_kconfig_blob":"ee5bcb896a9985c04709d0947b5ab0e39a9f309d",
 "redbull_defconfig":"arch/arm64/configs/redbull_defconfig",
 "redbull_defconfig_blob":"55e2088384d7189da77f5cd31ccf11dd75e58e4d",
 "android_repo":"LineageOS/android_device_google_redbull",
 "android_commit":"9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770",
 "modules_load":"modules.load",
 "modules_load_blob":"b116d1f234682a1f7e7275f36e6c7a2feb79ddb5",
}
FIELDS={
 "kbuild_subsys_pil_tz_symbol":"CONFIG_MSM_PIL_SSR_GENERIC",
 "kbuild_peripheral_loader_symbol":"CONFIG_MSM_PIL",
 "kbuild_bus_symbol":"CONFIG_QCOM_BUS_SCALING",
 "kbuild_bus_rpmh_symbol":"CONFIG_QCOM_BUS_CONFIG_RPMH",
 "kbuild_modemsmem_symbol":"CONFIG_MODEMSMEM",
 "module_list_count_from_step821_run":329,
 "first_stage_projection_count_from_step821_run":220,
}
TRUE={"bus_rpmh_kconfig_depends_on_bus_scaling","redbull_bus_scaling_module","redbull_bus_rpmh_module","redbull_modemsmem_module","module_list_pil_before_bus","module_list_bus_before_modemsmem","published_makefile_Kconfig_are_module_build_selection_evidence"}
FALSE={"makefile_Kconfig_define_final_modules_dep_graph","actual_modules_dep_content_verified","modprobe_resolved_order_verified","successful_module_probe_order_verified","actual_first_modem_start_verified","modemsmem_item134_ready_verified","live_phone_functions_verified"}
UNKNOWN={"why_prior_source_hash_assertion_failed_when_later_pinned_recheck_passed","actual_modules_dep_softdep_and_alias_metadata_from_built_vendor_modules","dependencies_of_subsys_pil_tz_and_modemsmem_binary_modules","driver_probe_completion_order_and_bus_client_registration","item134_first_modem_start_ownership_and_acknowledgement","live_calls_SMS_data_and_SSR_recovery"}
SAFE={"adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}

def violations(d):
    b=[]
    if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,822,"source_hash_CI_recheck_and_Kbuild_module_dependency_boundary_offline_only"):b.append("scope")
    if d.get("ci") != CI:b.append("ci")
    if d.get("source") != SOURCE:b.append("source")
    o=d.get("observed",{})
    if set(o)!=set(FIELDS)|TRUE|FALSE:b.append("schema")
    if any(o.get(k)!=v for k,v in FIELDS.items()):b.append("symbols")
    if any(o.get(k) is not True for k in TRUE):b.append("evidence")
    if any(o.get(k) is not False for k in FALSE):b.append("runtime claims")
    if set(d.get("unknowns",[]))!=UNKNOWN:b.append("unknown")
    s=d.get("safety",{})
    if set(s)!=SAFE or any(v is not False for v in s.values()) or d.get("hardware_tested") is not False:b.append("device")
    return b

class Step822(unittest.TestCase):
    def setUp(self):self.d=json.loads(P.read_text(encoding="utf-8"))
    def reject(self,section,key,value):
        a=copy.deepcopy(self.d);a[section][key]=value;self.assertTrue(violations(a))
    def test_baseline(self):self.assertEqual(violations(self.d),[])
    def test_ci_pin(self):self.reject("ci","step821_commit","latest")
    def test_ci_failed_history(self):self.reject("ci","prior_failure_cause_established",True)
    def test_ci_digest_update(self):self.reject("ci","expected_digest_update_authorized",True)
    def test_ci_success(self):
        a=copy.deepcopy(self.d);a["ci"]["aosp_source"]["conclusion"]="failure";self.assertTrue(violations(a))
    def test_ci_assertions(self):
        a=copy.deepcopy(self.d);a["ci"]["aosp_source"]["strict_expected_sha_assertions_passed"]=False;self.assertTrue(violations(a))
    def test_kernel_pin(self):self.reject("source","kernel_commit","main")
    def test_bus_kbuild_pin(self):self.reject("source","bus_makefile_blob","main")
    def test_modemsmem_pin(self):self.reject("source","modemsmem_makefile_blob","main")
    def test_bus_symbol(self):self.reject("observed","kbuild_bus_symbol","CONFIG_MSM_BUS_SCALING")
    def test_pil_symbol(self):self.reject("observed","kbuild_subsys_pil_tz_symbol","unknown")
    def test_modemsmem_symbol(self):self.reject("observed","kbuild_modemsmem_symbol","unknown")
    def test_rpmh_dependency(self):self.reject("observed","bus_rpmh_kconfig_depends_on_bus_scaling",False)
    def test_bus_modular(self):self.reject("observed","redbull_bus_scaling_module",False)
    def test_module_list_count(self):self.reject("observed","module_list_count_from_step821_run",330)
    def test_boot_projection_count(self):self.reject("observed","first_stage_projection_count_from_step821_run",221)
    def test_not_dep_graph(self):self.reject("observed","makefile_Kconfig_define_final_modules_dep_graph",True)
    def test_no_dep_metadata(self):self.reject("observed","actual_modules_dep_content_verified",True)
    def test_no_modprobe_order(self):self.reject("observed","modprobe_resolved_order_verified",True)
    def test_no_probe_completion(self):self.reject("observed","successful_module_probe_order_verified",True)
    def test_no_item134(self):self.reject("observed","modemsmem_item134_ready_verified",True)
    def test_no_telephony(self):self.reject("observed","live_phone_functions_verified",True)
    def test_unknowns(self):
        a=copy.deepcopy(self.d);a["unknowns"].pop();self.assertTrue(violations(a))
    def test_no_modem_start(self):self.reject("safety","modem_start",True)
    def test_no_flash(self):self.reject("safety","flash",True)

if __name__=="__main__":unittest.main()
