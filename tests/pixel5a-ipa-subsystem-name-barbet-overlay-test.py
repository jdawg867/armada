#!/usr/bin/env python3
"""Step 799: preserve pinned IPA default subsystem names vs runtime overrides."""
import json
import unittest
from pathlib import Path
PATH=Path(__file__).resolve().parents[1]/"validation/pixel5a-ipa-subsystem-name-barbet-overlay-audit.json"
GAPS={
"ipa_gsi_fw_file_name_assignment_provenance","ipa_uc_fw_file_name_assignment_provenance",
"runtime_IPA_sub_sys_argument_on_pixel5a","complete_barbet_dt_overlay_preprocessor_expansion",
"qcom_base_lito_audio_include_mapping_in_final_dtb",
"actual_barbet_overlay_variant_in_boot_chain","all_nonliteral_modem_start_callers",
"MPSS_initial_boot_request_and_smem134_publication_order",
"stock_android12l_image_and_cellular_runtime"}
def audit(d):
    errors=[]
    k=d.get("kernel",{})
    if (d.get("schema_version"),d.get("step"),d.get("classification"),k.get("commit")) != (
        1,799,"pinned_source_IPA_argument_and_barbet_overlay_build_mapping_only",
        "929e7e2f3658867d51a1d423c7e000f5cf1d4043"):
        errors.append("incorrect provenance")
    ipa=d.get("ipa",{})
    required={
        "blob":"f03dc32340af1e5b57ab0356b71c8700ff7e1bdb",
        "default_gsi_name":"ipa_fws","default_uc_name":"ipa_uc",
        "override_gsi_field":"ipa3_ctx->gsi_fw_file_name",
        "override_uc_field":"ipa3_ctx->uc_fw_file_name",
        "dynamic_argument_call":"subsystem_get(sub_sys)"
    }
    if any(ipa.get(k)!=v for k,v in required.items()): errors.append("misreported IPA names")
    for key in ("resolved_default_values_are_modem","possible_overrides_resolved","actual_barbet_runtime_argument_verified"):
        if ipa.get(key) is not False: errors.append("unsupported IPA runtime claim")
    b=d.get("barbet_overlay",{})
    if (b.get("makefile_blob"),b.get("name"),b.get("base"),b.get("entry_blob"),
        b.get("board_include_blob"),b.get("board_includes"))!=(
        "852a844e147eba2dc9f2a2cf7b2483ff3e91894e",
        "lito-v2-barbet-mp-overlay.dtbo","qcom-base/lito-v2.dtb",
        "12c699a75dd1e8d3815e98b0e0ba59e454f14c08",
        "277ae16bb06ebb5c945fe02a579298af45aba3ff","lito-barbet.dtsi"):
        errors.append("wrong overlay build chain")
    if b.get("mp_build_mapping_found") is not True or any(b.get(x) is not False for x in (
       "full_preprocessed_dtb_verified","actual_device_overlay_variant_verified")):
        errors.append("unverified boot image equivalence")
    if set(d.get("unverified",[]))!=GAPS: errors.append("unknowns omitted")
    p=d.get("safety",{})
    if set(p)!={"smem_write","modem_start","driver_activation","flash"} or any(x is not False for x in p.values()) or d.get("hardware_tested") is not False:
        errors.append("unsupported device action")
    return errors

class SourceOnlyTests(unittest.TestCase):
    def setUp(self): self.d=json.loads(PATH.read_text())
    def test_baseline(self): self.assertEqual(audit(self.d),[])
    def test_default_gsi_not_modem(self):
        self.d["ipa"]["default_gsi_name"]="modem"
        self.assertTrue(audit(self.d))
    def test_default_uc_not_modem(self):
        self.d["ipa"]["default_uc_name"]="modem"
        self.assertTrue(audit(self.d))
    def test_dynamic_argument_not_runtime_verified(self):
        self.d["ipa"]["actual_barbet_runtime_argument_verified"]=True
        self.assertTrue(audit(self.d))
    def test_override_unresolved(self):
        self.d["ipa"]["possible_overrides_resolved"]=True
        self.assertTrue(audit(self.d))
    def test_overlay_is_build_mapping_not_dtb(self):
        self.d["barbet_overlay"]["full_preprocessed_dtb_verified"]=True
        self.assertTrue(audit(self.d))
    def test_overlay_variant_unverified(self):
        self.d["barbet_overlay"]["actual_device_overlay_variant_verified"]=True
        self.assertTrue(audit(self.d))
    def test_honors_nested_include(self):
        self.d["barbet_overlay"]["board_includes"]="lito-redfin.dtsi"
        self.assertTrue(audit(self.d))
    def test_no_modem_start_authorization(self):
        self.d["safety"]["modem_start"]=True
        self.assertTrue(audit(self.d))
    def test_no_unsupported_modem_order_claim(self):
        self.d["unverified"].remove("MPSS_initial_boot_request_and_smem134_publication_order")
        self.assertTrue(audit(self.d))
if __name__=="__main__":
    unittest.main()
