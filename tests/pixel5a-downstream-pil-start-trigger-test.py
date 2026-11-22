#!/usr/bin/env python3
"""Source-only regression against unsupported PIL/modem publication claims."""
import json
import unittest
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/"validation/pixel5a-downstream-pil-start-trigger-audit.json"
TRUE={
 "pil_probe_sets_powerup_to_subsys_powerup",
 "pil_probe_registers_subsys",
 "pil_subsys_powerup_calls_pil_boot",
 "ssr_subsys_register_registers_device_and_list",
 "subsystem_get_invokes_subsys_start_on_zero_refcount",
 "subsys_start_calls_descriptor_powerup",
 "subsystem_get_resolves_pon_depends_on",
 "pon_depends_on_derived_from_device_tree_property",
 "pil_probe_reads_qcom_smem_id_for_crash_reason"
}
FALSE={
 "smem_id_equivalent_to_vendor_item_134",
 "subsys_register_immediately_calls_pil_boot",
 "source_only_module_list_position_proves_runtime_start"
}
GAPS={
 "actual_barbet_modem_node_and_pon_depends_on_properties_not_yet_traced",
 "all_callers_of_subsystem_get_modem_not_yet_traced",
 "exact_stock_android12l_vendor_boot_and_module_load_order_unverified",
 "module_registration_does_not_prove_probe_completion_or_modem_boot",
 "no_vendor_item134_publication_completion_dependency_proven",
 "crash_recovery_republication_and_lock_order_unverified",
 "actual_voice_sms_data_and_device_validation_not_performed"
}
def validate(x):
    errors=[]
    s=x.get("source",{})
    if (x.get("step"),x.get("scope"),s.get("commit"),s.get("pil_blob"),
        s.get("ssr_blob"),s.get("peripheral_blob"))!=(795,
        "pinned_downstream_PIL_subsystem_software_paths_only",
        "929e7e2f3658867d51a1d423c7e000f5cf1d4043",
        "f17f9e57b0d1f671017032df9224ada0bbea15c2",
        "e304cb58b65037237b2a231a52dadb3bccd618c7",
        "c7920af7ab0c010c24078c72809a5d83667ce765"):
        errors.append("unreviewed kernel provenance")
    o=x.get("observed",{})
    if set(o)!=TRUE|FALSE or any(o.get(k) is not True for k in TRUE) or any(o.get(k) is not False for k in FALSE):
        errors.append("unsupported start trigger observation")
    if set(x.get("gaps",[]))!=GAPS:
        errors.append("missing device-specific dependency caveat")
    p=x.get("permissions",{})
    if set(p)!={"allow_smem_publish","allow_driver_registration","allow_firmware_boot","allow_flash","allow_upstream_generic_kernel_patch"} or any(v is not False for v in p.values()):
        errors.append("unsafe action authorized")
    if x.get("hardware_tested") is not False:
        errors.append("unsupported hardware verification")
    return errors
class TriggerAudit(unittest.TestCase):
    def setUp(self):
        self.x=json.loads(PATH.read_text())
    def test_baseline(self): self.assertEqual(validate(self.x),[])
    def test_registration_not_immediate_boot(self):
        self.x["observed"]["subsys_register_immediately_calls_pil_boot"]=True
        self.assertTrue(validate(self.x))
    def test_subsystem_get_trigger_stays(self):
        self.x["observed"]["subsystem_get_invokes_subsys_start_on_zero_refcount"]=False
        self.assertTrue(validate(self.x))
    def test_pon_dependency_not_claimed_complete(self):
        self.x["gaps"].remove("actual_barbet_modem_node_and_pon_depends_on_properties_not_yet_traced")
        self.assertTrue(validate(self.x))
    def test_no_vendor_smem_equivalence(self):
        self.x["observed"]["smem_id_equivalent_to_vendor_item_134"]=True
        self.assertTrue(validate(self.x))
    def test_no_first_stage_runtime_claim(self):
        self.x["observed"]["source_only_module_list_position_proves_runtime_start"]=True
        self.assertTrue(validate(self.x))
    def test_no_firmware_activation(self):
        self.x["permissions"]["allow_firmware_boot"]=True
        self.assertTrue(validate(self.x))
    def test_no_hardware_claim(self):
        self.x["hardware_tested"]=True
        self.assertTrue(validate(self.x))
if __name__=="__main__":
    unittest.main()
