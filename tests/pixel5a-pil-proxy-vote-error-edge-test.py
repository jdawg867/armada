#!/usr/bin/env python3
"""Step 818 pinned loader proxy-vote failure edge; source-only, no device operations."""
import copy
import json
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"validation/pixel5a-pil-proxy-vote-error-edge-audit.json"
PINS={"repository":"LineageOS/android_kernel_google_redbull","commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043","loader_path":"drivers/soc/qcom/peripheral-loader.c","loader_blob":"c7920af7ab0c010c24078c72809a5d83667ce765","tz_path":"drivers/soc/qcom/subsys-pil-tz.c","tz_blob":"f17f9e57b0d1f671017032df9224ada0bbea15c2","loader_wrapper_lines":"605-680","loader_boot_lines":"1279-1290,1381-1411","tz_proxy_lines":"565-607"}
FIELDS={"loader_boot_failed_proxy_vote_jumps_to":"release_fw"}
YES={"tz_proxy_vote_acquires_bus_first","tz_regulator_error_returns_without_local_bus_unvote","tz_clock_error_unwinds_regs_but_no_local_bus_unvote","tz_proxy_unvote_callback_releases_bus","loader_proxy_vote_invokes_callback","loader_proxy_vote_wake_lock_relaxed_on_callback_error","loader_proxy_vote_enables_irq_even_if_callback_errors","loader_proxy_vote_notifies_even_if_callback_errors","loader_boot_err_boot_calls_unvote","loader_boot_failed_proxy_vote_bypasses_err_boot","loader_boot_release_fw_releases_firmware","loader_boot_out_releases_mmap_and_sends_aop_off_on_error"}
NO={"loader_boot_failed_proxy_vote_calls_unvote_directly","delayed_unvote_scheduled_for_failed_proxy_vote_in_boot_path","actual_lito_bus_vote_leak_verified","compiled_bus_scaling_config_verified","live_telephony_recovery_verified"}
UNKNOWN={"effective_MSM_BUS_SCALING_and_bus_client_configuration","whether_irq_or_external_actor_can_trigger_proxy_unvote_after_failed_callback","proxy_irq_and_notification_effects_when_vote_failed","resource_ownership_if_callback_returns_error_after_bus_vote","SMEM_item134_publication_and_first_modem_start_order","working_Pixel5a_calls_SMS_data_and_SSR_recovery"}
SAFE={"adb","device_open","device_read","smem_read","smem_write","modem_start","flash"}

def violations(d):
 bad=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,818,"pinned_PIL_proxy_vote_error_edge_and_unvote_control_flow_not_live_bus_leak"):bad.append("scope")
 if d.get("sources")!=PINS:bad.append("source")
 o=d.get("observed",{})
 if set(o)!=set(FIELDS)|YES|NO:bad.append("schema")
 if any(o.get(k)!=v for k,v in FIELDS.items()):bad.append("error edge")
 if any(o.get(k) is not True for k in YES):bad.append("source")
 if any(o.get(k) is not False for k in NO):bad.append("runtime overclaim")
 if set(d.get("unknowns",[]))!=UNKNOWN:bad.append("unknowns")
 s=d.get("safety",{})
 if set(s)!=SAFE or any(v is not False for v in s.values()) or d.get("hardware_tested") is not False:bad.append("device")
 return bad

class ProxyVoteErrorTests(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def reject(self,key,value,section="observed"):
  d=copy.deepcopy(self.d);d[section][key]=value;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_loader_pin(self):self.reject("loader_blob","latest","sources")
 def test_tz_pin(self):self.reject("tz_blob","latest","sources")
 def test_bus_first(self):self.reject("tz_proxy_vote_acquires_bus_first",False)
 def test_reg_error_no_unvote(self):self.reject("tz_regulator_error_returns_without_local_bus_unvote",False)
 def test_clk_error_no_unvote(self):self.reject("tz_clock_error_unwinds_regs_but_no_local_bus_unvote",False)
 def test_separate_unvote_callback(self):self.reject("tz_proxy_unvote_callback_releases_bus",False)
 def test_callback_called(self):self.reject("loader_proxy_vote_invokes_callback",False)
 def test_wake_lock(self):self.reject("loader_proxy_vote_wake_lock_relaxed_on_callback_error",False)
 def test_irq_even_on_error(self):self.reject("loader_proxy_vote_enables_irq_even_if_callback_errors",False)
 def test_notify_even_on_error(self):self.reject("loader_proxy_vote_notifies_even_if_callback_errors",False)
 def test_goto_target(self):self.reject("loader_boot_failed_proxy_vote_jumps_to","err_boot")
 def test_err_boot_unvote(self):self.reject("loader_boot_err_boot_calls_unvote",False)
 def test_error_skips_unvote(self):self.reject("loader_boot_failed_proxy_vote_bypasses_err_boot",False)
 def test_no_direct_unvote(self):self.reject("loader_boot_failed_proxy_vote_calls_unvote_directly",True)
 def test_no_delayed_unvote(self):self.reject("delayed_unvote_scheduled_for_failed_proxy_vote_in_boot_path",True)
 def test_firmware_release(self):self.reject("loader_boot_release_fw_releases_firmware",False)
 def test_cleanup_out(self):self.reject("loader_boot_out_releases_mmap_and_sends_aop_off_on_error",False)
 def test_no_verified_leak(self):self.reject("actual_lito_bus_vote_leak_verified",True)
 def test_no_runtime_config(self):self.reject("compiled_bus_scaling_config_verified",True)
 def test_no_telephony(self):self.reject("live_telephony_recovery_verified",True)
 def test_unknowns_preserved(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_open(self):self.reject("device_open",True,"safety")
 def test_no_flash(self):self.reject("flash",True,"safety")

if __name__=="__main__":unittest.main()
