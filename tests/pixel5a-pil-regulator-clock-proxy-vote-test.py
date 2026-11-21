#!/usr/bin/env python3
"""Step 817 pinned PIL helper resource unwind claims; offline only."""
import copy,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-pil-regulator-clock-proxy-vote-audit.json"
SOURCE={"repository":"LineageOS/android_kernel_google_redbull","commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043","path":"drivers/soc/qcom/subsys-pil-tz.c","blob":"f17f9e57b0d1f671017032df9224ada0bbea15c2","reg_enable_lines":"455-515","reg_disable_lines":"517-533","clock_enable_lines":"535-555","clock_disable_lines":"557-563","proxy_vote_lines":"565-593","proxy_unvote_lines":"595-607"}
YES={"regulator_voltage_error_enters_unwind","regulator_load_error_enters_unwind","regulator_enable_error_enters_unwind","regulator_error_unwinds_prior_entries_reverse","regulator_disable_helper_returns_void","regulator_keep_proxy_regs_on_can_skip_enable_disable","clock_prepare_error_unwinds_previous_clocks_reverse","clock_disable_helper_returns_void","proxy_vote_acquires_bus_first","proxy_vote_regulator_failure_returns_without_explicit_bus_unvote","proxy_vote_clock_failure_disables_proxy_regulators","proxy_vote_success_path_has_bus_vote","proxy_unvote_helper_releases_bus_vote","bus_scaling_build_configuration_has_stub_path"}
NO={"regulator_cleanup_checks_reset_errors","proxy_vote_clock_failure_explicit_bus_unvote","bus_vote_leak_on_actual_pixel5a_verified","all_regulator_disable_operations_succeed_verified","modem_recovery_verified"}
UNKNOWN={"effective_compiled_MSM_bus_scaling_configuration","runtime_bus_client_and_vote_reference_model","regulator_clock_actual_acquisition_and_disable_results","whether_parent_loader_always_unvotes_after_proxy_vote_failure","PAS_shutdown_primary_resource_ownership_after_SCM_error","modemsmem_item134_ready_barrier_and_phone_telephony"}
SAFE={"adb","device_open","device_read","smem_read","smem_write","modem_start","flash"}
def violations(d):
 b=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,817,"pinned_PIL_regulator_clock_proxy_vote_helper_control_flow_source_only"):b.append("scope")
 if d.get("source")!=SOURCE:b.append("source")
 o=d.get("observed",{})
 if set(o)!=YES|NO:b.append("schema")
 if any(o.get(k) is not True for k in YES):b.append("source path")
 if any(o.get(k) is not False for k in NO):b.append("unsupported claim")
 if set(d.get("unknowns",[]))!=UNKNOWN:b.append("unknown")
 s=d.get("safety",{})
 if set(s)!=SAFE or any(v is not False for v in s.values()) or d.get("hardware_tested") is not False:b.append("device")
 return b
class Helpers(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text())
 def reject(self,k,v,section="observed"):
  d=copy.deepcopy(self.d);d[section][k]=v;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_pin(self):self.reject("blob","tip","source")
 def test_voltage_failure(self):self.reject("regulator_voltage_error_enters_unwind",False)
 def test_load_failure(self):self.reject("regulator_load_error_enters_unwind",False)
 def test_enable_failure(self):self.reject("regulator_enable_error_enters_unwind",False)
 def test_regulator_reverse(self):self.reject("regulator_error_unwinds_prior_entries_reverse",False)
 def test_no_regulator_reset_validation(self):self.reject("regulator_cleanup_checks_reset_errors",True)
 def test_disable_void(self):self.reject("regulator_disable_helper_returns_void",False)
 def test_keep_proxy(self):self.reject("regulator_keep_proxy_regs_on_can_skip_enable_disable",False)
 def test_clock_reverse(self):self.reject("clock_prepare_error_unwinds_previous_clocks_reverse",False)
 def test_clock_void(self):self.reject("clock_disable_helper_returns_void",False)
 def test_bus_first(self):self.reject("proxy_vote_acquires_bus_first",False)
 def test_regulator_no_bus_unvote(self):self.reject("proxy_vote_regulator_failure_returns_without_explicit_bus_unvote",False)
 def test_clock_error_reg_cleanup(self):self.reject("proxy_vote_clock_failure_disables_proxy_regulators",False)
 def test_clock_error_missing_bus_unvote(self):self.reject("proxy_vote_clock_failure_explicit_bus_unvote",True)
 def test_success_bus_vote(self):self.reject("proxy_vote_success_path_has_bus_vote",False)
 def test_unvote_function(self):self.reject("proxy_unvote_helper_releases_bus_vote",False)
 def test_stub(self):self.reject("bus_scaling_build_configuration_has_stub_path",False)
 def test_not_actual_leak(self):self.reject("bus_vote_leak_on_actual_pixel5a_verified",True)
 def test_not_hardware_recovery(self):self.reject("modem_recovery_verified",True)
 def test_no_disable_confirmation(self):self.reject("all_regulator_disable_operations_succeed_verified",True)
 def test_unknowns(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_modem(self):self.reject("modem_start",True,"safety")
 def test_no_flash(self):self.reject("flash",True,"safety")
if __name__=="__main__":unittest.main()
