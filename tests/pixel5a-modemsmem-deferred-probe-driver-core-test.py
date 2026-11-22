#!/usr/bin/env python3
"""Step 831 source-only deferred-probe error mapping evidence guards."""
import copy,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-modemsmem-deferred-probe-driver-core-audit.json"
CI={"previous_commit":"e7db146263e2004924cf2bbfb4cd81dfc35d1aab","android_run":44989098178,"android_conclusion":"success","aosp_run":44989098128,"aosp_conclusion":"success","compile_run":44989098131,"compile_conclusion":"success"}
SRC={"kernel_repo":"LineageOS/android_kernel_google_redbull","kernel_commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043","driver_core_path":"drivers/base/dd.c","driver_core_blob":"3a7200ebe1eb3aa19aeed70f37f415abedaecd9d","smem_path":"drivers/soc/qcom/smem.c","smem_blob":"de4d8aba7e366d5a3594731674dcfa310b3a8713","modemsmem_path":"drivers/soc/qcom/modemsmem/modemsmem.c","modemsmem_blob":"428143562894e6d8ca7b656174c72ee4b096f510"}
YES={"driver_core_handles_EPROBE_DEFER_separately","driver_core_enqueues_deferred_probes","driver_core_retries_on_trigger","driver_core_regular_ENOMEM_is_not_deferred","smem_alloc_can_return_EPROBE_DEFER","smem_get_can_return_ERR_PTR_EPROBE_DEFER","modemsmem_accepts_EEXIST","modemsmem_maps_non_EEXIST_alloc_failures_to_ENOMEM","modemsmem_maps_get_errors_to_ENOMEM"}
NO={"modemsmem_preserves_EPROBE_DEFER_from_alloc","modemsmem_preserves_EPROBE_DEFER_from_get","proposed_fix_validation_on_stock_barbet","compiled_corrected_driver_verified","actual_probe_failure_on_stock_phone_verified","smem134_start_barrier_verified"}
CAND={"category":"general_kernel_error_propagation","status":"isolated_review_candidate_no_kernel_source_change","required_behavior":"preserve_-EPROBE_DEFER_only_when_reported_by_smem_api_without_weakening_other_error_or_size_guards","must_preserve_existing_item_size_check":True,"upstream_submission_authorized":False,"merge_authorized":False}
UNKNOWN={"probe_timing_relative_to_SMEM_provider_on_stock_Pixel5a","whether_platform_probe_is_already_complete_before_MPSS_first_start","actual_error_codes_seen_in_field","exact_error_propagation_patch_and_mock_fault_injection_validation","firmware_SMEM_item134_ABI_and_consumer_barrier"}
SAFE={"adb","device_open","device_read","smem_read","smem_write","modem_start","flash"}
def violations(d):
 out=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,831,"pinned_driver_core_deferred_probe_vs_modemsmem_error_mapping_source_only"):out.append("scope")
 if d.get("ci")!=CI:out.append("ci")
 if d.get("sources")!=SRC:out.append("sources")
 f=d.get("findings",{})
 if set(f)!=YES|NO:out.append("schema")
 if any(f.get(x) is not True for x in YES):out.append("source")
 if any(f.get(x) is not False for x in NO):out.append("unverified")
 if d.get("candidate")!=CAND:out.append("candidate")
 if set(d.get("unknowns",[]))!=UNKNOWN:out.append("unknowns")
 s=d.get("safety",{})
 if set(s)!=SAFE or any(v is not False for v in s.values()) or d.get("hardware_tested") is not False:out.append("hardware")
 return out
class Defer(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def reject(self,section,key,value):
  d=copy.deepcopy(self.d);d[section][key]=value;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_ci(self):self.reject("ci","previous_commit","main")
 def test_core_pin(self):self.reject("sources","driver_core_blob","main")
 def test_provider_pin(self):self.reject("sources","smem_blob","main")
 def test_client_pin(self):self.reject("sources","modemsmem_blob","main")
 def test_defer_case(self):self.reject("findings","driver_core_handles_EPROBE_DEFER_separately",False)
 def test_enqueue(self):self.reject("findings","driver_core_enqueues_deferred_probes",False)
 def test_retry(self):self.reject("findings","driver_core_retries_on_trigger",False)
 def test_nomem_not_retry(self):self.reject("findings","driver_core_regular_ENOMEM_is_not_deferred",False)
 def test_alloc_can_defer(self):self.reject("findings","smem_alloc_can_return_EPROBE_DEFER",False)
 def test_get_can_defer(self):self.reject("findings","smem_get_can_return_ERR_PTR_EPROBE_DEFER",False)
 def test_existing(self):self.reject("findings","modemsmem_accepts_EEXIST",False)
 def test_alloc_mapping(self):self.reject("findings","modemsmem_maps_non_EEXIST_alloc_failures_to_ENOMEM",False)
 def test_get_mapping(self):self.reject("findings","modemsmem_maps_get_errors_to_ENOMEM",False)
 def test_not_propagated_alloc(self):self.reject("findings","modemsmem_preserves_EPROBE_DEFER_from_alloc",True)
 def test_not_propagated_get(self):self.reject("findings","modemsmem_preserves_EPROBE_DEFER_from_get",True)
 def test_not_compiled(self):self.reject("findings","compiled_corrected_driver_verified",True)
 def test_no_hardware_fault(self):self.reject("findings","actual_probe_failure_on_stock_phone_verified",True)
 def test_no_barrier(self):self.reject("findings","smem134_start_barrier_verified",True)
 def test_isolated(self):self.reject("candidate","status","merged")
 def test_preserve_size(self):self.reject("candidate","must_preserve_existing_item_size_check",False)
 def test_no_upstream(self):self.reject("candidate","upstream_submission_authorized",True)
 def test_no_merge(self):self.reject("candidate","merge_authorized",True)
 def test_unknown(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_smem(self):self.reject("safety","smem_write",True)
 def test_no_phone(self):self.reject("safety","device_open",True)
 def test_no_flash(self):self.reject("safety","flash",True)
if __name__=="__main__":unittest.main()
