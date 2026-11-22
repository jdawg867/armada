#!/usr/bin/env python3
"""Step 793: source-only diff classification does not grant modem permission."""
import json
import unittest
from pathlib import Path
PATH=Path(__file__).resolve().parents[1]/"validation/pixel5a-aosp-lineage-12l-diff-interpretation.json"
EXPECTED={
"barbet/init.barbet.rc":(1,"service_user_declaration_changed"),
"redbull/BoardConfig-common.mk":(24,"kernel_module_packaging_and_build_configuration_differs"),
"redbull/init.hardware.rc":(13,"init_property_and_service_related_differences_not_new_publication_barrier")}
UNVERIFIED={
"effective_resolved_modules_load_for_stock_android12l",
"exact_factory_vendor_boot_contents",
"module_loader_exit_status_and_driver_probe_completion",
"qualcomm_modemsmem_item134_memory_visibility_before_mpss_start",
"modem_recovery_dependency_on_item134",
"full_phone_telephony_calls_sms_mobile_data"}
FALSE=("hardware_tested","firmware_read","smem_write_authorized")
def problems(d):
    issues=[]
    if (d.get("schema_version"),d.get("kind"),d.get("aosp_tag"))!=(1,"source_only_aosp_vs_lineage_android12l_diff_interpretation","android-12.1.0_r7"):
        issues.append("source provenance changed")
    rows=d.get("files",[])
    actual={r.get("path"):(r.get("source_diff_hunks"),r.get("init_effect")) for r in rows}
    if len(rows)!=3 or actual!=EXPECTED:
        issues.append("diff interpretation changed")
    if any(r.get("direct_modemsmem_publication_dependency") is not False for r in rows):
        issues.append("unsupported SMEM publication barrier")
    claims=d.get("key_findings",{})
    required_true=("public_aosp_lineage_init_insmod_script_identical","public_aosp_lineage_barbet_insmod_cfg_identical","module_packaging_logic_differs_between_trees","direct_publication_completion_notification_observed_in_changed_lines")
    if any(claims.get(k) is not (False if k=="direct_publication_completion_notification_observed_in_changed_lines" else True) for k in required_true):
        issues.append("inaccurate source observation")
    for k in ("source_diff_establishes_modemsmem_probe_completion_before_mpss","source_diff_establishes_stock_vendor_boot_module_contents"):
        if claims.get(k) is not False:
            issues.append("unsupported startup claim")
    if set(d.get("remaining_unverified",[]))!=UNVERIFIED:
        issues.append("unresolved device blocker omitted")
    if d.get("source_diff_content_reviewed") is not True or any(d.get(k) is not False for k in FALSE):
        issues.append("unsafe validation/activation claim")
    return issues
class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.d=json.loads(PATH.read_text())
    def test_baseline(self): self.assertEqual(problems(self.d),[])
    def test_wrong_hunk(self):
        self.d["files"][1]["source_diff_hunks"]=0
        self.assertTrue(problems(self.d))
    def test_fake_barrier(self):
        self.d["files"][0]["direct_modemsmem_publication_dependency"]=True
        self.assertTrue(problems(self.d))
    def test_unverified_stock(self):
        self.d["key_findings"]["source_diff_establishes_stock_vendor_boot_module_contents"]=True
        self.assertTrue(problems(self.d))
    def test_fake_hardware(self):
        self.d["hardware_tested"]=True
        self.assertTrue(problems(self.d))
    def test_missing_blocker(self):
        self.d["remaining_unverified"].pop()
        self.assertTrue(problems(self.d))
    def test_wrong_source(self):
        self.d["aosp_tag"]="main"
        self.assertTrue(problems(self.d))
    def test_no_firmware(self):
        self.d["firmware_read"]=True
        self.assertTrue(problems(self.d))
if __name__=="__main__":
    unittest.main()
