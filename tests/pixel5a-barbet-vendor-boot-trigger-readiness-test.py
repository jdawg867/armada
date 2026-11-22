#!/usr/bin/env python3
"""Step 827: preserve pinned Android init readiness claims, offline only."""
import copy,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-barbet-vendor-boot-trigger-readiness-audit.json"
SOURCES={"redbull_repo":"LineageOS/android_device_google_redbull","redbull_commit":"9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770","hardware_rc":"init.hardware.rc","hardware_rc_blob":"ec3c3edf7e72fb394bde8e9dc669e4a07ced854b","insmod_sh":"init.insmod.sh","insmod_sh_blob":"a222838cc855392838a69fbd9ea3951273078658","init_modem_sh":"init.modem.sh","init_modem_sh_blob":"75520c7055a56930ba4e7c1fab9fd7a2aefa1f5c","barbet_repo":"LineageOS/android_device_google_barbet","barbet_commit":"24101a383bb1951952adcd6f62668338dd048f03","barbet_insmod_cfg":"init.insmod.barbet.cfg","barbet_insmod_cfg_blob":"f2728df28091a374ff6bfa6e4e50f3695420e722"}
CI={"commit":"fd9848a94b20e837649e7eac944bfbc448974c83","android_validation":{"id":44972493641,"conclusion":"success"},"source_probe":{"id":44972493617,"conclusion":"success"},"arm64_compile":{"id":44972493620,"conclusion":"success"}}
YES={"early_init_starts_insmod_sh","insmod_service_disabled_oneshot","barbet_config_bulk_modprobe","barbet_config_ftm5_extra_modprobe","barbet_config_adsp_cdsp_sysfs_enable","insmod_shell_ready_properties_unconditionally_set","hardware_rc_waits_for_both_ready_properties","hardware_rc_on_boot_starts_init_modem_sh","init_modem_sh_only_publishes_cdt_imei_meid_properties","hardware_rc_per_mgr_trigger_on_esim_done","hardware_rc_per_mgr_trigger_on_esim_noneed","hardware_rc_per_mgr_trigger_on_boot_complete"}
NO={"insmod_shell_modprobe_status_checked","modem_start_directly_observed_in_init_modem_sh","ready_property_proves_module_probe_completion","ready_property_proves_item134_published","per_mgr_modem_start_runtime_order_verified","telephony_verified"}
UNKNOWN={"pinned_vendor_per_mgr_binary_behavior_and_first_modem_subsystem_get","effective_module_dependency_resolution_and_probe_completion","whether_vendor_init_scripts_publish_modemsmem_item134","first_PIL_modem_powerup_vs_item134_publish_and_ack","modem_restart_generation_republication_and_radio_recovery","real_call_SMS_mobile_data_and_SSR_functionality"}
SAFE={"adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}
def violations(d):
 err=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,827,"pinned_Barbet_Redbull_init_boot_trigger_readiness_source_only_not_runtime_modem_barrier"):err.append("scope")
 if d.get("sources")!=SOURCES:err.append("source")
 if d.get("ci_previous")!=CI:err.append("ci")
 observed=d.get("observed",{})
 if set(observed)!=YES|NO:err.append("schema")
 if any(observed.get(k) is not True for k in YES):err.append("positive")
 if any(observed.get(k) is not False for k in NO):err.append("runtime overclaim")
 if set(d.get("unknowns",[]))!=UNKNOWN:err.append("unknown")
 safe=d.get("safety",{})
 if set(safe)!=SAFE or any(v is not False for v in safe.values()) or d.get("hardware_tested") is not False:err.append("device")
 return err
class BootTriggers(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text(encoding="utf-8"))
 def reject(self,section,key,val):
  d=copy.deepcopy(self.d);d[section][key]=val;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_source_pin(self):self.reject("sources","hardware_rc_blob","main")
 def test_modem_shell_pin(self):self.reject("sources","init_modem_sh_blob","main")
 def test_barbet_pin(self):self.reject("sources","barbet_insmod_cfg_blob","main")
 def test_ci_pin(self):self.reject("ci_previous","commit","main")
 def test_early_insmod(self):self.reject("observed","early_init_starts_insmod_sh",False)
 def test_oneshot(self):self.reject("observed","insmod_service_disabled_oneshot",False)
 def test_bulk_modprobe(self):self.reject("observed","barbet_config_bulk_modprobe",False)
 def test_extra_ftm5(self):self.reject("observed","barbet_config_ftm5_extra_modprobe",False)
 def test_adsp_cdsp(self):self.reject("observed","barbet_config_adsp_cdsp_sysfs_enable",False)
 def test_modprobe_status(self):self.reject("observed","insmod_shell_modprobe_status_checked",True)
 def test_unconditional_properties(self):self.reject("observed","insmod_shell_ready_properties_unconditionally_set",False)
 def test_wait_props(self):self.reject("observed","hardware_rc_waits_for_both_ready_properties",False)
 def test_modem_script(self):self.reject("observed","hardware_rc_on_boot_starts_init_modem_sh",False)
 def test_modem_script_behavior(self):self.reject("observed","init_modem_sh_only_publishes_cdt_imei_meid_properties",False)
 def test_esim_done(self):self.reject("observed","hardware_rc_per_mgr_trigger_on_esim_done",False)
 def test_esim_noneed(self):self.reject("observed","hardware_rc_per_mgr_trigger_on_esim_noneed",False)
 def test_boot_complete(self):self.reject("observed","hardware_rc_per_mgr_trigger_on_boot_complete",False)
 def test_no_direct_modem_start(self):self.reject("observed","modem_start_directly_observed_in_init_modem_sh",True)
 def test_no_probe_proof(self):self.reject("observed","ready_property_proves_module_probe_completion",True)
 def test_no_item134_proof(self):self.reject("observed","ready_property_proves_item134_published",True)
 def test_no_per_mgr_runtime(self):self.reject("observed","per_mgr_modem_start_runtime_order_verified",True)
 def test_no_telephony(self):self.reject("observed","telephony_verified",True)
 def test_unknowns(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_modem_action(self):self.reject("safety","modem_start",True)
 def test_no_flash(self):self.reject("safety","flash",True)
if __name__=="__main__":unittest.main()
