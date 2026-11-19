#!/usr/bin/env python3
"""Step 800 source provenance: DT property -> IPA resource -> context -> PIL name."""
import json
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"validation/pixel5a-ipa-firmware-name-property-provenance.json"
GAPS={
 "exact_final_barbet_ipa_node_properties","complete_qcom_base_overlay_mapping",
 "selected_runtime_barbet_variant","initial_MPSS_firmware_start_initiator",
 "all_modem_start_routes_including_userspace",
 "vendor_item134_publication_before_MPSS_start",
 "stock_vendor_boot_and_runtime_trace","telephony_and_modem_recovery"
}
PROPS={
 "gsi_property":"qcom,use-gsi-ipa-fw",
 "gsi_target_resource":"ipa_drv_res->gsi_fw_file_name",
 "gsi_context":"ipa3_ctx->gsi_fw_file_name",
 "gsi_default":"ipa_fws",
 "uc_property":"qcom,use-uc-ipa-fw",
 "uc_target_resource":"ipa_drv_res->uc_fw_file_name",
 "uc_context":"ipa3_ctx->uc_fw_file_name",
 "uc_default":"ipa_uc"
}
def defects(r):
    bad=[]
    source=r.get("source",{})
    if (r.get("schema_version"),r.get("step"),r.get("scope"),source.get("commit"),source.get("ipa_blob"))!=(
        1,800,"pinned_source_IPA_property_to_PIL_argument_not_runtime_dtb",
        "929e7e2f3658867d51a1d423c7e000f5cf1d4043",
        "f03dc32340af1e5b57ab0356b71c8700ff7e1bdb"):
        bad.append("provenance")
    a=r.get("assignments",{})
    if any(a.get(k)!=v for k,v in PROPS.items()):
        bad.append("property-to-context wiring")
    for field in ("uses_of_property_read_string","copies_resource_strings_into_context",
                  "conditional_firmware_selection_uses_override_or_default"):
        if a.get(field) is not True: bad.append("missing observed connection")
    for field in ("defaults_select_modem","lito_device_specific_override_observed_in_bounded_search",
                  "barbet_final_runtime_property_verified"):
        if a.get(field) is not False: bad.append("unverified modem override")
    if r.get("examples_other_soc")!=[
      {"path":"arch/arm64/boot/dts/vendor/qcom/scuba.dtsi","property":"qcom,use-gsi-ipa-fw","value":"scuba_ipa_fws"},
      {"path":"arch/arm64/boot/dts/vendor/qcom/lagoon.dtsi","property":"qcom,use-gsi-ipa-fw","value":"lagoon_ipa_fws"}]:
        bad.append("foreign SoC example")
    b=r.get("overlay_build_reference",{})
    if b.get("base")!="qcom-base/lito-v2.dtb" or b.get("qcom_base_mapping_fully_verified") is not False or b.get("compiled_dtbo_inspected") is not False:
        bad.append("unverified DTB")
    if set(r.get("still_unverified",[]))!=GAPS: bad.append("omitted blocker")
    p=r.get("safety",{})
    if set(p)!={"allow_smem_write","allow_modem_start","allow_driver_activation","allow_flash"} or any(x is not False for x in p.values()) or r.get("hardware_tested") is not False:
        bad.append("device action")
    return bad
class ProvenanceTests(unittest.TestCase):
    def setUp(self): self.d=json.loads(P.read_text())
    def test_baseline(self): self.assertEqual(defects(self.d),[])
    def test_gsi_override_property(self):
        self.d["assignments"]["gsi_property"]="qcom,proc-img-to-load"
        self.assertTrue(defects(self.d))
    def test_uc_override_property(self):
        self.d["assignments"]["uc_property"]="unknown"
        self.assertTrue(defects(self.d))
    def test_default_not_modem(self):
        self.d["assignments"]["defaults_select_modem"]=True
        self.assertTrue(defects(self.d))
    def test_absent_not_proven_absent_in_final_dtb(self):
        self.d["assignments"]["barbet_final_runtime_property_verified"]=True
        self.assertTrue(defects(self.d))
    def test_other_soc_example_not_barbet(self):
        self.d["examples_other_soc"][0]["value"]="modem"
        self.assertTrue(defects(self.d))
    def test_final_dtb_not_inspected(self):
        self.d["overlay_build_reference"]["compiled_dtbo_inspected"]=True
        self.assertTrue(defects(self.d))
    def test_item134_barrier_unverified(self):
        self.d["still_unverified"].remove("vendor_item134_publication_before_MPSS_start")
        self.assertTrue(defects(self.d))
    def test_no_modem_start(self):
        self.d["safety"]["allow_modem_start"]=True
        self.assertTrue(defects(self.d))
    def test_no_hardware_claim(self):
        self.d["hardware_tested"]=True
        self.assertTrue(defects(self.d))
if __name__=="__main__":
    unittest.main()
