#!/usr/bin/env python3
"""Step 809: source evidence for subsys_modem open; never touch device."""
import json
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-modem-subsys-char-device-first-start-audit.json"
YES={"character_device_created_during_subsys_registration","character_open_calls_subsystem_get_with_fwname","character_open_selects_registered_subsystem_name","character_open_may_trigger_initial_subsystem_powerup","character_release_calls_subsystem_put","character_fops_contains_open_and_release_only","per_mgr_has_read_file_permissions_for_modem_device","per_mgr_is_intended_modem_boot_service_in_init"}
NO={"per_mgr_binary_actually_opens_subsys_modem","live_first_firmware_start_trace_captured","opening_device_proves_item134_published","selinux_permission_alone_proves_device_open","modem_pil_registration_alone_starts_firmware"}
MISSING={"actual_pm_service_open_read_close_behavior","effective_runtime_device_permissions_and_SELinux","first_modem_open_or_other_first_subsystem_get_requester","when_modemsmem_probe_completed_relative_to_open","item134_original_owner_and_non_destructive_reuse","payload_memory_visibility_and_MPSS_acknowledgment","compiled_Barbet_vendor_boot_and_DTB","first_boot_recovery_and_live_telephony"}
def violations(d):
    bad=[]
    s=d.get("sources",{});k=s.get("kernel",{});a=s.get("android",{})
    if (d.get("schema_version"),d.get("step"),d.get("scope"),k.get("commit"),k.get("blob"),a.get("commit"),a.get("file_contexts_blob"),a.get("policy_blob"))!=(
      1,809,"pinned_kernel_subsystem_character_device_open_and_Android_SELinux_permission_chain_not_runtime_trace",
      "929e7e2f3658867d51a1d423c7e000f5cf1d4043","e304cb58b65037237b2a231a52dadb3bccd618c7",
      "9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770","f53709a48e090c7faa3af51da725688876747955","edafb01e6199964607b294d44287e9fcbfeae79f"):
        bad.append("source")
    o=d.get("observed",{})
    if (o.get("char_device_name_pattern"),o.get("modem_device_path"),o.get("modem_device_label"),o.get("per_mgr_domain"),o.get("per_mgr_device_permission"))!=(
       "subsys_%s","/dev/subsys_modem","modem_ssr_device","vendor_per_mgr",
       "allow vendor_per_mgr modem_ssr_device:chr_file r_file_perms;"):
        bad.append("name or permission")
    if set(o)!=(YES|NO|{"char_device_name_pattern","modem_device_path","modem_device_label","per_mgr_domain","per_mgr_device_permission"}) or any(o.get(x) is not True for x in YES) or any(o.get(x) is not False for x in NO):
        bad.append("runtime promotion")
    if set(d.get("unknowns",[]))!=MISSING:bad.append("unverified dependency")
    flags=d.get("safety",{})
    if set(flags)!={"device_open","device_read","smem_read","smem_write","modem_start","flash"} or any(x is not False for x in flags.values()) or d.get("hardware_tested") is not False:
        bad.append("hardware")
    return bad
class SourceTests(unittest.TestCase):
    def setUp(self):self.d=json.loads(P.read_text())
    def test_baseline(self):self.assertEqual(violations(self.d),[])
    def test_open_can_start(self):
        self.d["observed"]["character_open_may_trigger_initial_subsystem_powerup"]=False
        self.assertTrue(violations(self.d))
    def test_open_method_is_fwname_get(self):
        self.d["observed"]["character_open_calls_subsystem_get_with_fwname"]=False
        self.assertTrue(violations(self.d))
    def test_close_method(self):
        self.d["observed"]["character_release_calls_subsystem_put"]=False
        self.assertTrue(violations(self.d))
    def test_device_path(self):
        self.d["observed"]["modem_device_path"]="/dev/other"
        self.assertTrue(violations(self.d))
    def test_no_verified_per_mgr_open(self):
        self.d["observed"]["per_mgr_binary_actually_opens_subsys_modem"]=True
        self.assertTrue(violations(self.d))
    def test_permission_not_action(self):
        self.d["observed"]["selinux_permission_alone_proves_device_open"]=True
        self.assertTrue(violations(self.d))
    def test_open_not_payload_ack(self):
        self.d["observed"]["opening_device_proves_item134_published"]=True
        self.assertTrue(violations(self.d))
    def test_no_live_trace(self):
        self.d["observed"]["live_first_firmware_start_trace_captured"]=True
        self.assertTrue(violations(self.d))
    def test_no_registration_start(self):
        self.d["observed"]["modem_pil_registration_alone_starts_firmware"]=True
        self.assertTrue(violations(self.d))
    def test_smem_order_unknown(self):
        self.d["unknowns"].remove("when_modemsmem_probe_completed_relative_to_open")
        self.assertTrue(violations(self.d))
    def test_no_hardware_open(self):
        self.d["safety"]["device_open"]=True
        self.assertTrue(violations(self.d))
    def test_label_source_pin(self):
        self.d["sources"]["android"]["file_contexts_blob"]="main"
        self.assertTrue(violations(self.d))
if __name__=="__main__":
    unittest.main()
