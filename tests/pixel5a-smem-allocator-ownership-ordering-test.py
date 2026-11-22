#!/usr/bin/env python3
"""Step 804: enforce source-only SMEM allocator metadata vs payload distinction."""
import json
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-smem-allocator-ownership-ordering-audit.json"
YES={"private_existing_item_returns_EEXIST","global_existing_item_returns_EEXIST","alloc_rejects_uninitialized_smem_with_EPROBE_DEFER","alloc_hardware_spinlock_acquired","alloc_hardware_spinlock_released","alloc_uses_global_or_private_partition","private_wmb_orders_header_before_free_offset","global_wmb_orders_entry_header_before_allocated_flag","get_hardware_spinlock_acquired","get_hardware_spinlock_released","get_resolves_existing_pointer_and_size","modemsmem_accepts_EEXIST_and_gets_item","modemsmem_unconditionally_zeros_item_after_get"}
NO={"allocation_metadata_wmb_proves_modem_payload_written","hardware_spinlock_guarantees_MPSS_payload_consumption","existing_allocation_identifies_original_item_owner","get_pointer_size_is_publication_ack","modemsmem_explicit_completion_notification","firmware_start_after_payload_stores_proven"}
GAPS={"original_item134_owner_on_actual_phone","item134_preallocation_and_existing_content","SMEM_partitions_used_at_runtime","reinitialization_and_restart_corruption_risk","payload_memory_ordering_and_modem_read_protocol","initial_MPSS_start_requester_and_start_barrier","actual_first_stage_driver_probe_order","compiled_vendor_boot_and_effective_Barbet_DTB","cellular_and_modem_hardware_behavior"}
def verify(d):
    errors=[]
    s=d.get("source",{})
    if (d.get("schema_version"),d.get("step"),d.get("scope"),s.get("commit"),s.get("smem_blob"),s.get("modemsmem_blob"))!=(1,804,"pinned_downstream_smem_allocator_metadata_ordering_only","929e7e2f3658867d51a1d423c7e000f5cf1d4043","de4d8aba7e366d5a3594731674dcfa310b3a8713","428143562894e6d8ca7b656174c72ee4b096f510"):
        errors.append("source identity")
    o=d.get("observed",{})
    if set(o)!=(YES|NO) or any(o.get(k) is not True for k in YES) or any(o.get(k) is not False for k in NO):
        errors.append("unsupported allocator or payload claim")
    if (d.get("numbers",{}).get("smem_vendor_item_id"),d.get("numbers",{}).get("modemsmem_struct_size_bytes"))!=(134,64):
        errors.append("item structure")
    if set(d.get("unverified",[]))!=GAPS:
        errors.append("unresolved ownership omitted")
    safety=d.get("safety",{})
    if set(safety)!={"flash","smem_write","load_modem","enable_driver"} or any(x is not False for x in safety.values()) or d.get("hardware_tested") is not False:
        errors.append("hardware action")
    return errors
class SmemAudit(unittest.TestCase):
    def setUp(self):self.d=json.loads(P.read_text())
    def test_baseline(self):self.assertEqual(verify(self.d),[])
    def test_existing_item_does_not_prove_owner(self):
        self.d["observed"]["existing_allocation_identifies_original_item_owner"]=True
        self.assertTrue(verify(self.d))
    def test_allocation_barrier_not_payload_barrier(self):
        self.d["observed"]["allocation_metadata_wmb_proves_modem_payload_written"]=True
        self.assertTrue(verify(self.d))
    def test_spinlock_not_modem_ack(self):
        self.d["observed"]["hardware_spinlock_guarantees_MPSS_payload_consumption"]=True
        self.assertTrue(verify(self.d))
    def test_get_not_publication_ack(self):
        self.d["observed"]["get_pointer_size_is_publication_ack"]=True
        self.assertTrue(verify(self.d))
    def test_private_EEXIST(self):
        self.d["observed"]["private_existing_item_returns_EEXIST"]=False
        self.assertTrue(verify(self.d))
    def test_global_EEXIST(self):
        self.d["observed"]["global_existing_item_returns_EEXIST"]=False
        self.assertTrue(verify(self.d))
    def test_64_bytes(self):
        self.d["numbers"]["modemsmem_struct_size_bytes"]=128
        self.assertTrue(verify(self.d))
    def test_no_start_after_payload_claim(self):
        self.d["observed"]["firmware_start_after_payload_stores_proven"]=True
        self.assertTrue(verify(self.d))
    def test_no_smem_write(self):
        self.d["safety"]["smem_write"]=True
        self.assertTrue(verify(self.d))
if __name__=="__main__":
    unittest.main()
