#!/usr/bin/env python3
"""Step 805: source-only provider/consumer error and proposed publication gates."""
import json
import unittest
from pathlib import Path
F=Path(__file__).resolve().parents[1]/"validation/pixel5a-smem-provider-probe-publication-contract.json"
TRUE={"provider_arch_initcall_registration","provider_requires_SBL_initialized_header","provider_requires_hwspinlock","provider_handles_unsupported_version_as_EINVAL","provider_sets_global_pointer_at_success_end","allocator_returns_EPROBE_DEFER_before_provider_ready","get_returns_ERR_PTR_EPROBE_DEFER_before_provider_ready","consumer_accepts_alloc_EEXIST","consumer_converts_other_alloc_errors_to_ENOMEM","consumer_converts_get_pointer_or_size_errors_to_ENOMEM","consumer_resets_existing_64_byte_item","consumer_sysfs_create_error_nonfatal"}
FALSE={"consumer_preserves_allocator_EPROBE_DEFER","consumer_communicates_payload_ready_to_PIL","consumer_guards_existing_item_before_reset","provider_arch_initcall_proves_consumer_probe_finished","first_MPSS_boot_after_consumer_probe_proven"}
REQUIRED={"start_disabled_by_default","require_item134_sole_writer_policy","require_existing_item_preservation_or_explicit_owner_clearance","require_exact_size_and_valid_pointer","require_distinct_deferred_provider_status","require_payload_write_visibility_contract","require_successful_publication_ack_before_MPSS_start","require_crash_restart_safe_republication_policy","require_explicit_manual_hardware_authorization"}
UNKNOWN={"item134_owner_and_existing_contents","physical_provider_probe_and_module_load_order","driver_retry_behavior_if_minus_ENOMEM","remote_processor_acknowledgement_or_fence","SMEM_memory_region_cache_and_visibility_requirements","userspace_or_kernel_first_MPSS_start_requester","modem_restart_ownership_and_republication","final_vendor_boot_DTB_and_hardware_telephony"}
def check(d):
    errors=[]
    s=d.get("source",{})
    if (d.get("step"),d.get("scope"),s.get("commit"),s.get("provider_blob"),s.get("consumer_blob"))!=(805,"pinned_downstream_probe_deferral_and_proposed_fail_closed_gate_not_kernel_implementation","929e7e2f3658867d51a1d423c7e000f5cf1d4043","de4d8aba7e366d5a3594731674dcfa310b3a8713","428143562894e6d8ca7b656174c72ee4b096f510"):
        errors.append("pin")
    o=d.get("observed",{})
    if set(o)!=(TRUE|FALSE) or any(o.get(k) is not True for k in TRUE) or any(o.get(k) is not False for k in FALSE):
        errors.append("source facts")
    p=d.get("proposal",{})
    if p.get("status")!="requirements_only_not_implemented" or any(p.get(k) is not True for k in REQUIRED):
        errors.append("proposed gate")
    if set(d.get("unverified",[]))!=UNKNOWN: errors.append("unknowns")
    safety=d.get("safety",{})
    if set(safety)!={"smem_write","modem_start","driver_load","flash"} or any(v is not False for v in safety.values()) or d.get("hardware_tested") is not False:
        errors.append("device action")
    return errors
class PublicationContractTest(unittest.TestCase):
    def setUp(self): self.d=json.loads(F.read_text())
    def test_baseline(self): self.assertEqual(check(self.d),[])
    def test_deferred_provider_error_not_preserved(self):
        self.d["observed"]["consumer_preserves_allocator_EPROBE_DEFER"]=True
        self.assertTrue(check(self.d))
    def test_provider_arch_initcall_not_probe_completion(self):
        self.d["observed"]["provider_arch_initcall_proves_consumer_probe_finished"]=True
        self.assertTrue(check(self.d))
    def test_start_not_proven_ordered(self):
        self.d["observed"]["first_MPSS_boot_after_consumer_probe_proven"]=True
        self.assertTrue(check(self.d))
    def test_existing_reset_unprotected(self):
        self.d["observed"]["consumer_guards_existing_item_before_reset"]=True
        self.assertTrue(check(self.d))
    def test_contract_not_implemented(self):
        self.d["proposal"]["status"]="enabled"
        self.assertTrue(check(self.d))
    def test_start_gate_required(self):
        self.d["proposal"]["require_successful_publication_ack_before_MPSS_start"]=False
        self.assertTrue(check(self.d))
    def test_restart_policy_required(self):
        self.d["proposal"]["require_crash_restart_safe_republication_policy"]=False
        self.assertTrue(check(self.d))
    def test_smem_owner_unknown(self):
        self.d["unverified"].remove("item134_owner_and_existing_contents")
        self.assertTrue(check(self.d))
    def test_no_hardware_action(self):
        self.d["safety"]["modem_start"]=True
        self.assertTrue(check(self.d))
if __name__=="__main__":
    unittest.main()
