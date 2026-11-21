#!/usr/bin/env python3
"""Step 815: pinned PIL callback/loader source claims; never touch device."""
import copy
import json
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"validation/pixel5a-modem-pil-callback-rollback-audit.json"
PINS={"kernel_repo":"LineageOS/android_kernel_google_redbull","commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043","pil_tz_path":"drivers/soc/qcom/subsys-pil-tz.c","pil_tz_blob":"f17f9e57b0d1f671017032df9224ada0bbea15c2","loader_path":"drivers/soc/qcom/peripheral-loader.c","loader_blob":"c7920af7ab0c010c24078c72809a5d83667ce765","restart_path":"drivers/soc/qcom/subsystem_restart.c","restart_blob":"e304cb58b65037237b2a231a52dadb3bccd618c7"}
FIELDS={"registered_powerup_callback":"subsys_powerup","registered_shutdown_callback":"subsys_shutdown"}
YES={"powerup_sets_fw_name","powerup_resets_stop_ack_when_irq_present","powerup_returns_pil_boot_result","shutdown_invokes_pil_shutdown","shutdown_returns_zero_regardless_pil_shutdown_result","shutdown_force_stop_can_signal_smem_state_and_wait_stop_ack","loader_calls_aop_on_before_request_firmware","loader_aop_on_failure_returns_immediately","loader_releases_prior_memory_map_before_new_load","loader_request_firmware_failure_exits_through_out","loader_init_image_failure_has_err_boot_unvote","loader_mem_setup_failure_can_deinit_image","loader_auth_reset_failure_has_memory_reassignment_attempt","loader_error_path_attempts_proxy_unvote","loader_error_path_releases_firmware_when_acquired","loader_error_path_frees_region_when_allocated","loader_error_path_releases_mmap","loader_error_path_sends_aop_off","loader_shutdown_tracks_shutdown_fail","loader_shutdown_marks_modem_ssr","loader_shutdown_sends_aop_off"}
NO={"loader_shutdown_cleanup_and_modem_success_verified","loader_rollback_guaranteed_across_all_errors","first_modem_start_after_item134_ready_verified","device_testing_performed"}
UNKNOWN={"partial_clock_regulator_and_proxy_vote_unwind_effectiveness","memory_reassignment_and_SCM_failure_recovery","effective_Barbet_modem_device_tree_configuration","modemsmem_item134_ownership_publication_and_acknowledgement","runtime_modem_first_start_and_restart_generation","phone_calls_SMS_data_and_SSR_recovery"}
SAFE={"adb","device_open","device_read","smem_read","smem_write","modem_start","flash"}

def violations(d):
 bad=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,815,"pinned_Lito_PIL_callback_and_loader_unwind_source_only_not_verified_complete_rollback"):bad.append("scope")
 if d.get("sources")!=PINS:bad.append("pins")
 o=d.get("observed",{})
 if set(o)!=set(FIELDS)|YES|NO:bad.append("observed")
 if any(o.get(k)!=v for k,v in FIELDS.items()):bad.append("callback")
 if any(o.get(k) is not True for k in YES):bad.append("missing evidence")
 if any(o.get(k) is not False for k in NO):bad.append("runtime overclaim")
 if len(d.get("caveats",[]))!=6:bad.append("caveats")
 if set(d.get("unknowns",[]))!=UNKNOWN:bad.append("unknown")
 s=d.get("safety",{})
 if set(s)!=SAFE or any(x is not False for x in s.values()) or d.get("hardware_tested") is not False:bad.append("device")
 return bad

class SourceOnlyTests(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def reject(self,key,value,section="observed"):
  d=copy.deepcopy(self.d);d[section][key]=value;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_pil_source_pin(self):
  d=copy.deepcopy(self.d);d["sources"]["pil_tz_blob"]="main";self.assertTrue(violations(d))
 def test_loader_source_pin(self):
  d=copy.deepcopy(self.d);d["sources"]["loader_blob"]="main";self.assertTrue(violations(d))
 def test_callback(self):self.reject("registered_powerup_callback","unknown")
 def test_shutdown_callback(self):self.reject("registered_shutdown_callback","unknown")
 def test_pil_boot_propagation(self):self.reject("powerup_returns_pil_boot_result",False)
 def test_shutdown_result_mask(self):self.reject("shutdown_returns_zero_regardless_pil_shutdown_result",False)
 def test_aop_fail_early_return(self):self.reject("loader_aop_on_failure_returns_immediately",False)
 def test_fw_error_exit(self):self.reject("loader_request_firmware_failure_exits_through_out",False)
 def test_init_error_unvote(self):self.reject("loader_init_image_failure_has_err_boot_unvote",False)
 def test_mem_setup_deinit(self):self.reject("loader_mem_setup_failure_can_deinit_image",False)
 def test_auth_error_memory_reassign(self):self.reject("loader_auth_reset_failure_has_memory_reassignment_attempt",False)
 def test_proxy_unvote(self):self.reject("loader_error_path_attempts_proxy_unvote",False)
 def test_release_firmware(self):self.reject("loader_error_path_releases_firmware_when_acquired",False)
 def test_release_mmap(self):self.reject("loader_error_path_releases_mmap",False)
 def test_aop_off(self):self.reject("loader_error_path_sends_aop_off",False)
 def test_shutdown_fail_flag(self):self.reject("loader_shutdown_tracks_shutdown_fail",False)
 def test_no_rollback_guarantee(self):self.reject("loader_rollback_guaranteed_across_all_errors",True)
 def test_no_item134_order(self):self.reject("first_modem_start_after_item134_ready_verified",True)
 def test_no_recovery_proof(self):self.reject("loader_shutdown_cleanup_and_modem_success_verified",True)
 def test_unknown_ownership(self):
  d=copy.deepcopy(self.d);d["unknowns"].remove("memory_reassignment_and_SCM_failure_recovery");self.assertTrue(violations(d))
 def test_no_device_open(self):self.reject("device_open",True,"safety")
 def test_no_flash(self):self.reject("flash",True,"safety")

if __name__=="__main__":unittest.main()
