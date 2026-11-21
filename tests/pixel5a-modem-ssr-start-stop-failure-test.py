#!/usr/bin/env python3
"""Step 814 pinned SSR startup/shutdown failure control flow; offline only."""
import copy
import json
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"validation/pixel5a-modem-ssr-start-stop-failure-audit.json"
PIN={"repository":"LineageOS/android_kernel_google_redbull","commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043","path":"drivers/soc/qcom/subsystem_restart.c","blob":"e304cb58b65037237b2a231a52dadb3bccd618c7","start_lines":"899-937","stop_lines":"939-963","get_lines":"1031-1085"}
STRINGS={"start_before_powerup_notification":"SUBSYS_BEFORE_POWERUP","powerup_error_notification":"SUBSYS_POWERUP_FAILURE","err_ready_failure_notification":"SUBSYS_POWERUP_FAILURE","err_ready_success_notification":"SUBSYS_AFTER_POWERUP","stop_before_shutdown_notification":"SUBSYS_BEFORE_SHUTDOWN","stop_checks_force_shutdown_property":"qcom,pil-force-shutdown","stop_after_shutdown_notification":"SUBSYS_AFTER_SHUTDOWN"}
YES={"start_reinitializes_error_ready_completion","start_calls_descriptor_powerup","powerup_callback_failure_returns_error","powerup_success_enables_all_irqs","not_loadable_branch_marks_online_without_err_ready_wait","loadable_branch_waits_for_err_ready","err_ready_failure_calls_descriptor_shutdown","err_ready_failure_disables_all_irqs","err_ready_failure_returns_error","err_ready_success_marks_online","stop_reinitializes_shutdown_ack_completion","stop_nonforced_path_marks_offlining","stop_nonforced_path_attempts_sysmon_shutdown","stop_calls_descriptor_shutdown","stop_marks_offline","stop_disables_all_irqs","get_first_reference_calls_start"}
NO={"powerup_callback_failure_directly_calls_descriptor_shutdown","powerup_callback_failure_directly_disables_irqs","not_loadable_branch_emits_after_powerup_notification","stop_force_path_attempts_sysmon_shutdown","get_failed_start_increments_refcount","start_proves_modemsmem_item134_ready","stop_proves_telephony_recovery","hardware_verified"}
UNKNOWN={"descriptor_powerup_callback_failure_rollback_semantics","Barbet_loadable_branch_and_runtime_DT_force_shutdown_property","modem_first_start_vs_item134_publication","subsystem_recovery_generation_and_external_refholders","actual_Pixel5a_telephony_end_to_end"}
SAFETY={"adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}

def violations(d):
 bad=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,814,"pinned_SSR_subsys_start_stop_source_control_flow_not_live_modem_recovery"):bad.append("scope")
 if d.get("source")!=PIN:bad.append("pin")
 o=d.get("observed",{})
 if set(o)!=set(STRINGS)|YES|NO:bad.append("schema")
 if any(o.get(k)!=v for k,v in STRINGS.items()):bad.append("names")
 if any(o.get(k) is not True for k in YES):bad.append("source flow")
 if any(o.get(k) is not False for k in NO):bad.append("unsupported inference")
 if len(d.get("limitations",[]))!=6 or not all(isinstance(x,str) and x for x in d["limitations"]):bad.append("limitations")
 if set(d.get("unknowns",[]))!=UNKNOWN:bad.append("unknowns")
 s=d.get("safety",{})
 if set(s)!=SAFETY or any(x is not False for x in s.values()) or d.get("hardware_tested") is not False:bad.append("device")
 return bad

class PinnedStartStopTests(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def reject(self,key,value,section="observed"):
  d=copy.deepcopy(self.d);d[section][key]=value;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_before_powerup(self):self.reject("start_before_powerup_notification","AFTER")
 def test_powerup_callback(self):self.reject("start_calls_descriptor_powerup",False)
 def test_powerup_error(self):self.reject("powerup_callback_failure_returns_error",False)
 def test_powerup_error_no_forced_shutdown(self):self.reject("powerup_callback_failure_directly_calls_descriptor_shutdown",True)
 def test_powerup_error_no_direct_irq_disable(self):self.reject("powerup_callback_failure_directly_disables_irqs",True)
 def test_irq_enable(self):self.reject("powerup_success_enables_all_irqs",False)
 def test_not_loadable_skip_wait(self):self.reject("not_loadable_branch_marks_online_without_err_ready_wait",False)
 def test_not_loadable_notification(self):self.reject("not_loadable_branch_emits_after_powerup_notification",True)
 def test_loadable_wait(self):self.reject("loadable_branch_waits_for_err_ready",False)
 def test_wait_failure_shutdown(self):self.reject("err_ready_failure_calls_descriptor_shutdown",False)
 def test_wait_failure_irq(self):self.reject("err_ready_failure_disables_all_irqs",False)
 def test_wait_error(self):self.reject("err_ready_failure_returns_error",False)
 def test_online(self):self.reject("err_ready_success_marks_online",False)
 def test_after_powerup(self):self.reject("err_ready_success_notification","NONE")
 def test_shutdown_ack(self):self.reject("stop_reinitializes_shutdown_ack_completion",False)
 def test_force_property(self):self.reject("stop_checks_force_shutdown_property","force")
 def test_graceful(self):self.reject("stop_nonforced_path_attempts_sysmon_shutdown",False)
 def test_forced_no_sysmon(self):self.reject("stop_force_path_attempts_sysmon_shutdown",True)
 def test_shutdown_callback(self):self.reject("stop_calls_descriptor_shutdown",False)
 def test_offline(self):self.reject("stop_marks_offline",False)
 def test_stop_irqs(self):self.reject("stop_disables_all_irqs",False)
 def test_after_shutdown(self):self.reject("stop_after_shutdown_notification","NONE")
 def test_count_failure(self):self.reject("get_failed_start_increments_refcount",True)
 def test_item134_not_proven(self):self.reject("start_proves_modemsmem_item134_ready",True)
 def test_recovery_not_proven(self):self.reject("stop_proves_telephony_recovery",True)
 def test_source_pin(self):self.reject("blob","unversioned","source")
 def test_missing_unknown(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_device_open(self):self.reject("device_open",True,"safety")
 def test_no_flash(self):self.reject("flash",True,"safety")

if __name__=="__main__":unittest.main()
