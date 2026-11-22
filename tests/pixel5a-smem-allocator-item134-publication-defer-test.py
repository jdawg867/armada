#!/usr/bin/env python3
"""Step 830: offline guard for pinned SMEM allocation versus item134 publication."""
import copy,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-smem-allocator-item134-publication-defer-audit.json"
CI={"previous_commit":"a4eaa70ae167123a1c7cb7ef371f92c6020c8aea","android_run":44985869730,"android_conclusion":"success","source_run":44985869759,"source_conclusion":"success","compile_run":44985869813,"compile_conclusion":"success"}
SRC={"kernel_repo":"LineageOS/android_kernel_google_redbull","commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043","smem_c":"drivers/soc/qcom/smem.c","smem_c_blob":"de4d8aba7e366d5a3594731674dcfa310b3a8713","modemsmem_c":"drivers/soc/qcom/modemsmem/modemsmem.c","modemsmem_blob":"428143562894e6d8ca7b656174c72ee4b096f510"}
YES={"allocator_private_existing_item_returns_EEXIST","allocator_global_existing_item_returns_EEXIST","allocator_uses_hwspinlock_for_alloc","allocator_uses_hwspinlock_for_get","allocator_unlocks_after_allocation","allocator_unlocks_after_get","allocator_metadata_wmb_before_private_free_offset","allocator_metadata_wmb_before_global_allocated_flag","modemsmem_retrieves_existing_item_after_EEXIST","modemsmem_unconditionally_zeroes_contents_outside_allocator_get_lock","modemsmem_populates_fields_after_zeroing","allocator_get_can_return_EPROBE_DEFER","allocator_alloc_can_return_EPROBE_DEFER","modemsmem_alloc_other_failure_maps_to_ENOMEM","modemsmem_get_ERROR_maps_to_ENOMEM"}
NO={"allocator_EEXIST_signals_content_fully_initialized","allocator_wmb_is_item134_content_publication_ack","modemsmem_propagates_EPROBE_DEFER_to_platform_probe","modemsmem_explicit_remote_consumer_ack","actual_race_or_incorrect_phone_behavior_proven","live_device_tested"}
UNKNOWN={"whether_driver_probe_is_invoked_before_QCOM_SMEM_is_ready_on_stock_barbet","actual_platform_driver_probe_deferral_and_retry_behavior","content_publication_memory_ordering_required_by_modem_firmware_ABI","remote_modem_consumption_and_first_start_sequence","whether_EEXIST_happens_only_before_first_MPSS_start","SSR_reprobe_item134_republication_and_telephony_recovery"}
SAFE={"adb","device_open","device_read","modem_start","smem_read","smem_write","flash"}
def violations(d):
 errors=[]
 if (d.get("schema_version"),d.get("step"),d.get("scope"))!=(1,830,"pinned_SMEM_allocator_vs_modemsmem_item134_content_write_ownership_and_probe_error_boundary"):errors.append("scope")
 if d.get("ci")!=CI:errors.append("CI")
 if d.get("source")!=SRC:errors.append("source")
 f=d.get("findings",{})
 if set(f)!=YES|NO:errors.append("fields")
 if any(f.get(k) is not True for k in YES):errors.append("verified")
 if any(f.get(k) is not False for k in NO):errors.append("overclaim")
 if set(d.get("unknowns",[]))!=UNKNOWN:errors.append("unknowns")
 s=d.get("safety",{})
 if set(s)!=SAFE or any(v is not False for v in s.values()) or d.get("hardware_tested") is not False:errors.append("hardware")
 return errors
class Step830(unittest.TestCase):
 def setUp(self):self.d=json.loads(P.read_text(encoding="utf-8"))
 def reject(self,section,key,value):
  d=copy.deepcopy(self.d);d[section][key]=value;self.assertTrue(violations(d))
 def test_baseline(self):self.assertEqual(violations(self.d),[])
 def test_kernel_commit(self):self.reject("source","commit","tip")
 def test_allocator_blob(self):self.reject("source","smem_c_blob","tip")
 def test_driver_blob(self):self.reject("source","modemsmem_blob","tip")
 def test_ci_pin(self):self.reject("ci","previous_commit","tip")
 def test_private_eexist(self):self.reject("findings","allocator_private_existing_item_returns_EEXIST",False)
 def test_global_eexist(self):self.reject("findings","allocator_global_existing_item_returns_EEXIST",False)
 def test_eexist_not_ready(self):self.reject("findings","allocator_EEXIST_signals_content_fully_initialized",True)
 def test_lock_alloc(self):self.reject("findings","allocator_uses_hwspinlock_for_alloc",False)
 def test_lock_get(self):self.reject("findings","allocator_uses_hwspinlock_for_get",False)
 def test_unlock_alloc(self):self.reject("findings","allocator_unlocks_after_allocation",False)
 def test_unlock_get(self):self.reject("findings","allocator_unlocks_after_get",False)
 def test_metadata_barrier_private(self):self.reject("findings","allocator_metadata_wmb_before_private_free_offset",False)
 def test_metadata_barrier_global(self):self.reject("findings","allocator_metadata_wmb_before_global_allocated_flag",False)
 def test_metadata_not_ack(self):self.reject("findings","allocator_wmb_is_item134_content_publication_ack",True)
 def test_modem_existing_get(self):self.reject("findings","modemsmem_retrieves_existing_item_after_EEXIST",False)
 def test_zero_outside_get_lock(self):self.reject("findings","modemsmem_unconditionally_zeroes_contents_outside_allocator_get_lock",False)
 def test_fields_after_zero(self):self.reject("findings","modemsmem_populates_fields_after_zeroing",False)
 def test_get_defer(self):self.reject("findings","allocator_get_can_return_EPROBE_DEFER",False)
 def test_alloc_defer(self):self.reject("findings","allocator_alloc_can_return_EPROBE_DEFER",False)
 def test_alloc_error_mapping(self):self.reject("findings","modemsmem_alloc_other_failure_maps_to_ENOMEM",False)
 def test_get_error_mapping(self):self.reject("findings","modemsmem_get_ERROR_maps_to_ENOMEM",False)
 def test_no_defer_propagation(self):self.reject("findings","modemsmem_propagates_EPROBE_DEFER_to_platform_probe",True)
 def test_no_ack(self):self.reject("findings","modemsmem_explicit_remote_consumer_ack",True)
 def test_no_race_claim(self):self.reject("findings","actual_race_or_incorrect_phone_behavior_proven",True)
 def test_no_hardware_claim(self):self.reject("findings","live_device_tested",True)
 def test_unknowns(self):
  d=copy.deepcopy(self.d);d["unknowns"].pop();self.assertTrue(violations(d))
 def test_no_device(self):self.reject("safety","device_open",True)
 def test_no_smem_write(self):self.reject("safety","smem_write",True)
 def test_no_flash(self):self.reject("safety","flash",True)
if __name__=="__main__":unittest.main()
