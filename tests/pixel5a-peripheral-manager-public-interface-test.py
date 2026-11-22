#!/usr/bin/env python3
"""Step 812: bounded public SSR evidence; no device interactions."""
import copy
import json
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"validation/pixel5a-peripheral-manager-public-interface-audit.json"
PINS={
 "redbull_android":("9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770","ec3c3edf7e72fb394bde8e9dc669e4a07ced854b"),
 "redbull_kernel":("929e7e2f3658867d51a1d423c7e000f5cf1d4043","e304cb58b65037237b2a231a52dadb3bccd618c7"),
 "historical_comparison":("5cef16f959fe119986fe3d295d420e5f53f08d63","343899d329b260e1f335a54ec441a16d5e9e9786"),
}
FIELDS={
 "redbull_service_binary":"/vendor/bin/pm-service",
 "redbull_service_name":"vendor.per_mgr",
 "redbull_policy_domain":"vendor_per_mgr",
 "redbull_device_type":"modem_ssr_device",
 "redbull_device_node":"/dev/subsys_modem",
 "kernel_char_device_open_handler":"subsys_device_open",
 "kernel_char_device_get_call":"subsystem_get_with_fwname",
}
TRUE={"kernel_character_open_can_trigger_subsystem_start","redbull_source_contains_service_definition","redbull_source_contains_selinux_read_grant","bullhead_historical_policy_has_per_mgr_ssr_chr_file_open_read"}
FALSE={"historical_bullhead_proves_redbull_behavior","github_search_proves_absence_of_implementation","public_redbull_pm_service_implementation_verified","proprietary_pm_service_actual_open_verified","publicly_verified_first_requester","first_modem_boot_runtime_verified","modemsmem_item134_ready_before_first_boot_verified"}
UNKNOWN={"installed_proprietary_pm_service_code_or_documented_call_flow","other_userspace_or_kernel_requesters_of_first_modem_start","effective_runtime_device_and_policy","first_open_vs_modemsmem_probe_and_payload_visibility","SMEM_item134_ownership_ack_reuse_and_reset","phone_calls_SMS_data_and_SSR_recovery"}
SEARCH={"GitHub indexed code search: subsys_modem within redbull device tree","GitHub indexed code search: subsys_modem peripheral_manager","GitHub indexed code search: pm-service subsystem_get","Pinned Redbull init service, SELinux and kernel subsystem char-device handlers","Historical Bullhead Peripheral Manager policy as cross-device comparison only"}
SAFETY={"hardware_tested","adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}

def violations(d):
 bad=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,812,"bounded_public_interface_and_historical_policy_search_not_proprietary_redbull_runtime_trace"):bad.append("scope")
 s=d.get("sources",{})
 for key,(commit,blob) in PINS.items():
  v=s.get(key,{})
  blobkey={"redbull_android":"init_blob","redbull_kernel":"subsystem_restart_blob","historical_comparison":"policy_blob"}[key]
  if v.get("commit")!=commit or v.get(blobkey)!=blob:bad.append(key)
 if set(d.get("search_scope",[]))!=SEARCH:bad.append("search")
 o=d.get("observed",{})
 if set(o)!=set(FIELDS)|TRUE|FALSE:bad.append("observed schema")
 if any(o.get(k)!=v for k,v in FIELDS.items()):bad.append("fields")
 if any(o.get(k) is not True for k in TRUE):bad.append("source facts")
 if any(o.get(k) is not False for k in FALSE):bad.append("runtime overclaim")
 if set(d.get("unknowns",[]))!=UNKNOWN:bad.append("unknowns")
 safety=d.get("safety",{})
 if set(safety)!=SAFETY or any(v is not False for v in safety.values()):bad.append("device")
 return bad

class OfflineEvidenceTests(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def flip(self,key,value,section="observed"):
  d=copy.deepcopy(self.d);d[section][key]=value;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_binary(self):self.flip("redbull_service_binary","/vendor/bin/other")
 def test_node(self):self.flip("redbull_device_node","/dev/other")
 def test_handler(self):self.flip("kernel_char_device_open_handler","read")
 def test_get(self):self.flip("kernel_char_device_get_call","subsystem_put")
 def test_active_open(self):self.flip("kernel_character_open_can_trigger_subsystem_start",False)
 def test_historical_boundary(self):self.flip("historical_bullhead_proves_redbull_behavior",True)
 def test_search_nonexhaustive(self):self.flip("github_search_proves_absence_of_implementation",True)
 def test_no_pm_source(self):self.flip("public_redbull_pm_service_implementation_verified",True)
 def test_no_actual_open(self):self.flip("proprietary_pm_service_actual_open_verified",True)
 def test_no_first_requester(self):self.flip("publicly_verified_first_requester",True)
 def test_no_runtime_modem(self):self.flip("first_modem_boot_runtime_verified",True)
 def test_no_item134_ready(self):self.flip("modemsmem_item134_ready_before_first_boot_verified",True)
 def test_android_pin(self):
  d=copy.deepcopy(self.d);d["sources"]["redbull_android"]["commit"]="main";self.assertTrue(violations(d))
 def test_kernel_pin(self):
  d=copy.deepcopy(self.d);d["sources"]["redbull_kernel"]["subsystem_restart_blob"]="main";self.assertTrue(violations(d))
 def test_bullhead_pin(self):
  d=copy.deepcopy(self.d);d["sources"]["historical_comparison"]["policy_blob"]="main";self.assertTrue(violations(d))
 def test_unknown(self):
  d=copy.deepcopy(self.d);d["unknowns"].remove("other_userspace_or_kernel_requesters_of_first_modem_start");self.assertTrue(violations(d))
 def test_search_scope(self):
  d=copy.deepcopy(self.d);d["search_scope"].append("all repositories exhaustive");self.assertTrue(violations(d))
 def test_no_open(self):self.flip("device_open",True,"safety")
 def test_no_flash(self):self.flip("flash",True,"safety")

if __name__=="__main__":unittest.main()
