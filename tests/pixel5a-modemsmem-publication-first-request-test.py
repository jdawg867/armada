#!/usr/bin/env python3
"""Step 803: fail closed on SMEM134 ownership, reset, and MPSS start claims."""
import json
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-modemsmem-publication-first-request-audit.json"
YES={"dt_declares_modemsmem_compatible","probe_calls_qcom_smem_alloc","probe_accepts_EEXIST","probe_calls_qcom_smem_get_and_validates_size","probe_unconditionally_memset_io_64_bytes","probe_writes_version_socid_modemflag_and_flags","sysfs_create_failure_still_returns_success","bam_dmux_has_explicit_subsystem_restart_modem","adsp_loader_has_conditional_literal_subsystem_get_modem"}
NO={"explicit_smem_publication_completion_signal","explicit_dependency_on_PIL_start","modemsmem_module_registration_equal_probe_completion","bam_dmux_restart_is_first_boot_request","adsp_loader_request_verified_live","first_modem_start_requester_identified","correct_item134_existing_owner_and_reinit_policy_known","MPSS_start_after_item134_population_proven"}
GAPS={"actual_SMEm_item134_existing_owner_and_consumers","whether_item134_is_preallocated_at_start","whether_zeroing_item134_during_restart_corrupts_modem_state","qcom_smem_alloc_and_get_runtime_return_status","ordering_between_modemsmem_probe_and_MPSS_firmware_start","required_memory_barrier_or_notification_protocol","all_real_first_boot_modem_start_requesters","stock_vendor_boot_and_final_DTB","hardware_telephony_and_restart_tests"}
def verify(d):
    issues=[]
    s=d.get("source",{})
    if (d.get("schema_version"),d.get("step"),d.get("scope"),s.get("commit"),s.get("modemsmem_blob"),s.get("modemsmem_header_blob"),s.get("bam_dmux_blob"))!=(1,803,"pinned_downstream_modemsmem_initialization_and_bounded_modem_requesters_source_only","929e7e2f3658867d51a1d423c7e000f5cf1d4043","428143562894e6d8ca7b656174c72ee4b096f510","a6b9d991fe7c023f44c21cc5c597746414c532a2","c6ec3156c17e0b50f1405434a46d92054715b1fd"):
        issues.append("unverified provenance")
    o=d.get("observed",{})
    if set(o)!=YES|NO or any(o.get(k) is not True for k in YES) or any(o.get(k) is not False for k in NO):
        issues.append("unsupported probe/start assertion")
    if (o.get("header_vendor_item_id"),o.get("structure_bytes"))!=(134,64):
        issues.append("wrong SMEM item or structure")
    if set(d.get("unknowns",[]))!=GAPS:issues.append("missing safety blocker")
    p=d.get("safety",{})
    if set(p)!={"flash","smem_write","driver_load","modem_start"} or any(v is not False for v in p.values()) or d.get("hardware_tested") is not False:
        issues.append("unapproved hardware claim")
    return issues
class AuditTests(unittest.TestCase):
    def setUp(self):self.d=json.loads(P.read_text())
    def test_baseline(self):self.assertEqual(verify(self.d),[])
    def test_existing_allocation_accepted(self):
        self.d["observed"]["probe_accepts_EEXIST"]=False
        self.assertTrue(verify(self.d))
    def test_full_reset_cannot_be_dismissed(self):
        self.d["observed"]["probe_unconditionally_memset_io_64_bytes"]=False
        self.assertTrue(verify(self.d))
    def test_no_publication_notification(self):
        self.d["observed"]["explicit_smem_publication_completion_signal"]=True
        self.assertTrue(verify(self.d))
    def test_no_start_order(self):
        self.d["observed"]["MPSS_start_after_item134_population_proven"]=True
        self.assertTrue(verify(self.d))
    def test_restart_not_first_boot(self):
        self.d["observed"]["bam_dmux_restart_is_first_boot_request"]=True
        self.assertTrue(verify(self.d))
    def test_no_safe_ownership_assumption(self):
        self.d["observed"]["correct_item134_existing_owner_and_reinit_policy_known"]=True
        self.assertTrue(verify(self.d))
    def test_unknown_restart_race_retained(self):
        self.d["unknowns"].remove("whether_zeroing_item134_during_restart_corrupts_modem_state")
        self.assertTrue(verify(self.d))
    def test_no_smem_write(self):
        self.d["safety"]["smem_write"]=True
        self.assertTrue(verify(self.d))
    def test_hardware_not_tested(self):
        self.d["hardware_tested"]=True
        self.assertTrue(verify(self.d))
if __name__=="__main__":
    unittest.main()
