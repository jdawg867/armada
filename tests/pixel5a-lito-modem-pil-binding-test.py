#!/usr/bin/env python3
"""Step 802: PIL source binding must not become a device boot assertion."""
import json
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-lito-modem-pil-binding-dependency-audit.json"
TRUE={"pil_driver_matches_compatible","pil_probe_reads_firmware_name","pil_probe_copies_firmware_name_to_subsystem_name","pil_probe_installs_subsys_powerup_callback","pil_probe_calls_subsys_register","subsys_get_finds_subsystem_by_name","subsys_get_invokes_optional_pon_depends_on","subsys_get_starts_on_initial_zero_refcount","pil_powerup_calls_pil_boot"}
FALSE={"subsys_registration_immediately_boots_modem","alternative_pil_q6v5_mss_matches_inspected_lito_node","smem_421_is_vendor_payload_134"}
GAPS={"actual_final_flattened_barbet_modem_node","other_dt_overrides_or_pon_depends_on_additions","which_downstream_modem_driver_is_bound_at_runtime","actual_first_subsystem_get_modem_requester","whether_modemsmem_item134_has_completed_before_PIL_start","probe_completion_and_memory_visibility_order","firmware_start_and_restart_republication_timing","stock_vendor_boot_and_physical_telephony_behavior"}
def errors(d):
    e=[]
    s=d.get("sources",{})
    if (d.get("step"),d.get("kind"),s.get("commit"),s.get("lito_blob"),s.get("pil_blob"),s.get("restart_blob"),s.get("alternative_blob"))!=(802,"source_only_lito_modem_PIL_binding_and_dependency_audit","929e7e2f3658867d51a1d423c7e000f5cf1d4043","24b013a4b166456be0a1f8a4a278d9fb3dcfccd1","f17f9e57b0d1f671017032df9224ada0bbea15c2","e304cb58b65037237b2a231a52dadb3bccd618c7","db48b1a2117162dbd0c893c9c9a49c74838805c8"):
        e.append("provenance")
    n=d.get("modem_node",{})
    if (n.get("compatible"),n.get("firmware_name"),n.get("pas_id"),n.get("crash_reason_smem_id"),n.get("vendor_payload_smem_item_id"))!=("qcom,pil-tz-generic","modem",4,421,134):
        e.append("node identity")
    for k in ("has_pon_depends_on_in_inspected_node","has_item134_completion_gate_in_inspected_node"):
        if n.get(k) is not False:e.append("unproven barrier")
    o=d.get("observed",{})
    if set(o)!=TRUE|FALSE or any(o.get(k) is not True for k in TRUE) or any(o.get(k) is not False for k in FALSE):
        e.append("registration/boot confusion")
    if set(d.get("unknowns",[]))!=GAPS:e.append("unknowns")
    p=d.get("permissions",{})
    if set(p)!={"allow_modem_boot","allow_smem_write","allow_driver_load","allow_flash"} or any(v is not False for v in p.values()) or d.get("hardware_tested") is not False:e.append("unsafe claim")
    return e
class SourceAudit(unittest.TestCase):
    def setUp(self):self.d=json.loads(P.read_text())
    def test_baseline(self):self.assertEqual(errors(self.d),[])
    def test_compatible(self):
        self.d["modem_node"]["compatible"]="qcom,pil-q6v5-mss"
        self.assertTrue(errors(self.d))
    def test_pil_pas_id(self):
        self.d["modem_node"]["pas_id"]=15
        self.assertTrue(errors(self.d))
    def test_smem_reason_not_payload(self):
        self.d["observed"]["smem_421_is_vendor_payload_134"]=True
        self.assertTrue(errors(self.d))
    def test_registration_does_not_boot(self):
        self.d["observed"]["subsys_registration_immediately_boots_modem"]=True
        self.assertTrue(errors(self.d))
    def test_no_dependency_claim(self):
        self.d["modem_node"]["has_pon_depends_on_in_inspected_node"]=True
        self.assertTrue(errors(self.d))
    def test_no_completed_publication(self):
        self.d["unknowns"].remove("whether_modemsmem_item134_has_completed_before_PIL_start")
        self.assertTrue(errors(self.d))
    def test_no_runtime_binding(self):
        self.d["unknowns"].remove("which_downstream_modem_driver_is_bound_at_runtime")
        self.assertTrue(errors(self.d))
    def test_no_firmware_boot(self):
        self.d["permissions"]["allow_modem_boot"]=True
        self.assertTrue(errors(self.d))
    def test_no_hardware(self):
        self.d["hardware_tested"]=True
        self.assertTrue(errors(self.d))
if __name__=="__main__":
    unittest.main()
