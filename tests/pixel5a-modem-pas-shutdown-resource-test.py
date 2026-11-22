#!/usr/bin/env python3
"""Step 816: pinned PAS/SCM shutdown source assertions, offline only."""
import json
import copy
import unittest
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "validation/pixel5a-modem-pas-shutdown-resource-audit.json"
PINS = {
 "repository":"LineageOS/android_kernel_google_redbull",
 "commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043",
 "trusted_path":"drivers/soc/qcom/subsys-pil-tz.c",
 "trusted_blob":"f17f9e57b0d1f671017032df9224ada0bbea15c2",
 "loader_path":"drivers/soc/qcom/peripheral-loader.c",
 "loader_blob":"c7920af7ab0c010c24078c72809a5d83667ce765",
 "trusted_shutdown_lines":"722-769",
 "subsys_shutdown_lines":"833-853",
 "loader_shutdown_lines":"1419-1440",
}
FIELDS = {"scm_shutdown_command":"PAS_SHUTDOWN_CMD","scm_transport_result_field":"rc","scm_secure_return_field":"desc.ret[0]"}
YES = {
 "no_auth_returns_zero","shutdown_bus_scaling_vote_before_proxy_resources",
 "bus_vote_failure_returns_directly","proxy_regulator_enable_failure_unvotes_bus",
 "proxy_clock_enable_failure_unwinds_proxy_regulators_and_bus",
 "post_scm_disables_proxy_clocks","post_scm_disables_proxy_regulators","post_scm_releases_bus_vote",
 "scm_transport_failure_returns_rc_without_disabling_primary_clocks_regulators",
 "scm_secure_nonzero_result_still_disables_primary_clocks_regulators",
 "successful_transport_disables_primary_clocks_regulators",
 "shutdown_error_returns_scm_result_when_transport_successful",
 "loader_records_shutdown_failure_flag","loader_sends_AOP_off_after_shutdown_attempt",
 "wrapper_discards_lower_shutdown_result",
}
NO = {"successful_rollback_proven","SCM_transport_failure_resource_state_verified","SCM_secure_error_resource_state_verified","modemsmem_134_barrier_verified","hardware_tested"}
UNKNOWN = {
 "PAS_transport_error_vs_secure_status_actual_hardware_effect",
 "primary_regulator_clock_ownership_after_transport_error",
 "proxy_resource_cleanup_and_bus_vote_error_propagation",
 "PIL_shutdown_fail_flag_impact_on_future_start",
 "forced_shutdown_ack_and_SSR_generation",
 "modemsmem_item134_ownership_ack_and_telephony_recovery",
}
SAFETY={"adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}

def violations(d):
 b=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope")) != (1,816,"pinned_PAS_SCM_trusted_shutdown_error_and_resource_cleanup_source_not_runtime_rollback"):b.append("scope")
 if d.get("sources")!=PINS:b.append("pins")
 o=d.get("observed",{})
 if set(o)!=set(FIELDS)|YES|NO:b.append("schema")
 if any(o.get(k)!=v for k,v in FIELDS.items()):b.append("return path")
 if any(o.get(k) is not True for k in YES):b.append("source")
 if any(o.get(k) is not False for k in NO):b.append("runtime")
 if set(d.get("unknowns",[]))!=UNKNOWN:b.append("unknown")
 s=d.get("safety",{})
 if set(s)!=SAFETY or any(v is not False for v in s.values()):b.append("active")
 return b

class ShutdownTests(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def reject(self,key,value,section="observed"):
  d=copy.deepcopy(self.d);d[section][key]=value;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_source_pin(self):
  d=copy.deepcopy(self.d);d["sources"]["trusted_blob"]="main";self.assertTrue(violations(d))
 def test_loader_pin(self):
  d=copy.deepcopy(self.d);d["sources"]["loader_blob"]="main";self.assertTrue(violations(d))
 def test_no_auth(self):self.reject("no_auth_returns_zero",False)
 def test_bus_vote(self):self.reject("shutdown_bus_scaling_vote_before_proxy_resources",False)
 def test_early_bus_failure(self):self.reject("bus_vote_failure_returns_directly",False)
 def test_proxy_reg_failure(self):self.reject("proxy_regulator_enable_failure_unvotes_bus",False)
 def test_proxy_clk_failure(self):self.reject("proxy_clock_enable_failure_unwinds_proxy_regulators_and_bus",False)
 def test_scm_command(self):self.reject("scm_shutdown_command","PAS_AUTH_AND_RESET_CMD")
 def test_transport_field(self):self.reject("scm_transport_result_field","desc.ret[0]")
 def test_secure_field(self):self.reject("scm_secure_return_field","rc")
 def test_proxy_clocks(self):self.reject("post_scm_disables_proxy_clocks",False)
 def test_proxy_regs(self):self.reject("post_scm_disables_proxy_regulators",False)
 def test_bus_unvote(self):self.reject("post_scm_releases_bus_vote",False)
 def test_transport_error_primary_resources(self):self.reject("scm_transport_failure_returns_rc_without_disabling_primary_clocks_regulators",False)
 def test_secure_error_primary_resources(self):self.reject("scm_secure_nonzero_result_still_disables_primary_clocks_regulators",False)
 def test_transport_success_primary_resources(self):self.reject("successful_transport_disables_primary_clocks_regulators",False)
 def test_secure_return(self):self.reject("shutdown_error_returns_scm_result_when_transport_successful",False)
 def test_shutdown_fail_record(self):self.reject("loader_records_shutdown_failure_flag",False)
 def test_aop_off(self):self.reject("loader_sends_AOP_off_after_shutdown_attempt",False)
 def test_wrapper_mask(self):self.reject("wrapper_discards_lower_shutdown_result",False)
 def test_no_rollback_proof(self):self.reject("successful_rollback_proven",True)
 def test_no_transport_hardware_proof(self):self.reject("SCM_transport_failure_resource_state_verified",True)
 def test_no_secure_hardware_proof(self):self.reject("SCM_secure_error_resource_state_verified",True)
 def test_no_item134(self):self.reject("modemsmem_134_barrier_verified",True)
 def test_unknowns(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_device_open(self):self.reject("device_open",True,"safety")
 def test_no_flash(self):self.reject("flash",True,"safety")

if __name__=="__main__":unittest.main()
