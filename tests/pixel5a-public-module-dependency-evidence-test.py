#!/usr/bin/env python3
"""Step 823: source-only dependency artifact search with explicit unknowns."""
import copy,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-public-module-dependency-evidence-audit.json"
CI={"step822_commit":"7da0ed056d9937af721d528c694d49f40db15b1a","android_validation":{"run":44961612743,"conclusion":"success"},"official_source":{"run":44961612700,"conclusion":"success"},"arm64_compile":{"run":44961612745,"conclusion":"failure","failed_step":"Retrieve exact pinned Linux source (never checkout into Armada)","failure_class":"HTTP 429 from GitHub archive","compile_attempted":False},"remediation":"same commit pinned codeload.github.com archive fallback with unchanged Linux 7.2.6 and ARM64 compile guards","remediation_success_verified":False}
SOURCE={"kernel_repo":"LineageOS/android_kernel_google_redbull","kernel_commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043","kernel_depmod_script":"scripts/depmod.sh","kernel_depmod_script_url":"https://github.com/LineageOS/android_kernel_google_redbull/blob/929e7e2f3658867d51a1d423c7e000f5cf1d4043/scripts/depmod.sh","android_repo":"LineageOS/android_device_google_redbull","android_commit":"9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770","source_module_list":"modules.load","source_module_list_blob":"b116d1f234682a1f7e7275f36e6c7a2feb79ddb5"}
ARTIFACTS=["pixel5a-aosp-lineage-12l-comparison-metadata","pixel5a-lineage-module-projection-source-only","pixel5a-aosp-12l-source-metadata","pixel5a-aosp-lineage-12l-source-diff"]
OBS={"searched_android_source_index_for_modules_dep":True,"android_source_index_modules_dep_matches":0,"searched_pinned_kernel_source_index_for_modules_dep":True,"kernel_source_matches_build_or_docs_not_generated_dependency_file":True,"checked_source_probe_run":44957899925,"source_probe_artifact_names":ARTIFACTS,"inspected_run_artifacts_contain_validated_vendor_modules_dep":False,"actual_vendor_modules_dep_retrieved":False,"public_dependency_metadata_exhaustively_searched":False,"source_module_list_equivalent_to_dep_graph":False,"kbuild_compile_order_equivalent_to_probe_order":False,"modemsmem_item134_first_start_order_verified":False}
UNKNOWN={"public_archived_stock_vendor_modules_dep_or_modules_dep_bin","actual_dependency_graph_of_pil_bus_modemsmem_modules","module_alias_softdep_metadata_and_first_stage_modprobe_resolution","runtime_bus_client_registration_and_modem_start_order","smem134_ownership_publishing_and_telephony","whether_codeload_fallback_succeeds_in_step823_ci"}
SAFE={"adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}
def violations(d):
 b=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,823,"bounded_public_dependency_artifact_search_and_pinned_archive_download_failure_not_live_modprobe"):b.append("scope")
 if d.get("ci")!=CI:b.append("CI")
 if d.get("source")!=SOURCE:b.append("source")
 if d.get("public_inspection")!=OBS:b.append("evidence")
 if set(d.get("unknowns",[]))!=UNKNOWN:b.append("unknown")
 s=d.get("safety",{})
 if set(s)!=SAFE or any(v is not False for v in s.values()) or d.get("hardware_tested") is not False:b.append("hardware")
 return b
class Evidence(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def reject(self,section,key,value):
  d=copy.deepcopy(self.d);d[section][key]=value;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_kernel_pin(self):self.reject("source","kernel_commit","tip")
 def test_module_pin(self):self.reject("source","source_module_list_blob","tip")
 def test_ci_failure(self):
  d=copy.deepcopy(self.d);d["ci"]["arm64_compile"]["conclusion"]="success";self.assertTrue(violations(d))
 def test_failure_class(self):
  d=copy.deepcopy(self.d);d["ci"]["arm64_compile"]["failure_class"]="compiler error";self.assertTrue(violations(d))
 def test_compile_not_attempted(self):
  d=copy.deepcopy(self.d);d["ci"]["arm64_compile"]["compile_attempted"]=True;self.assertTrue(violations(d))
 def test_fallback_unverified(self):self.reject("ci","remediation_success_verified",True)
 def test_public_search(self):self.reject("public_inspection","searched_android_source_index_for_modules_dep",False)
 def test_source_no_dep(self):self.reject("public_inspection","android_source_index_modules_dep_matches",1)
 def test_kernel_build_match(self):self.reject("public_inspection","kernel_source_matches_build_or_docs_not_generated_dependency_file",False)
 def test_probe_run(self):self.reject("public_inspection","checked_source_probe_run",1)
 def test_artifact_names(self):self.reject("public_inspection","source_probe_artifact_names",[])
 def test_no_dep_artifact(self):self.reject("public_inspection","inspected_run_artifacts_contain_validated_vendor_modules_dep",True)
 def test_no_dependency_retrieval(self):self.reject("public_inspection","actual_vendor_modules_dep_retrieved",True)
 def test_search_bounded(self):self.reject("public_inspection","public_dependency_metadata_exhaustively_searched",True)
 def test_load_list_not_dep(self):self.reject("public_inspection","source_module_list_equivalent_to_dep_graph",True)
 def test_kbuild_not_probe(self):self.reject("public_inspection","kbuild_compile_order_equivalent_to_probe_order",True)
 def test_not_item134(self):self.reject("public_inspection","modemsmem_item134_first_start_order_verified",True)
 def test_unknowns(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_device_open(self):self.reject("safety","device_open",True)
 def test_no_flash(self):self.reject("safety","flash",True)
if __name__=="__main__":unittest.main()
