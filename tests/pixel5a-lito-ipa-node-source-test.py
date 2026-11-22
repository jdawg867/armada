#!/usr/bin/env python3
"""Step 801: pinned Lito IPA source observations, never final DTB or modem boot."""
import json
import unittest
from pathlib import Path
FILE=Path(__file__).resolve().parents[1]/"validation/pixel5a-lito-ipa-node-source-audit.json"
GAPS={"complete_QCOM_and_Google_DT_source_graph","runtime_Barbet_IPA_DT_overrides_and_overlay_selection","loaded_IPA_PIL_subsystem_firmware_name","actual_modem_PIL_start_requester","vendor_SMEM_item134_published_before_MPSS","modem_crash_and_recovery_order","stock_Android12L_vendor_boot_contents","phone_calls_SMS_mobile_data"}
BLOBS={"lito_dtsi":"24b013a4b166456be0a1f8a4a278d9fb3dcfccd1","lito_v2":"97affc51181d437ee4d37797b261b41c5fe00e24","lito_v2_dts":"a3da016a653d65cb310deb32aa2895615fb8b7f1","barbet_common":"4aeed8583a96230c89b11ac85ec6b156abadc2db","redbull_common":"9eea9dc7431c5ef6cc68f100789402c025b558ce","barbet_mp":"277ae16bb06ebb5c945fe02a579298af45aba3ff"}
def errors(d):
    result=[]
    if (d.get("schema_version"),d.get("step"),d.get("scope"),d.get("kernel",{}).get("commit")) != (1,801,"pinned_Lito_IPA_DT_source_subset_only_not_flattened_runtime_dtb","929e7e2f3658867d51a1d423c7e000f5cf1d4043"):
        result.append("pin")
    if {k:v.get("blob") for k,v in d.get("sources",{}).items()}!=BLOBS:
        result.append("source blobs")
    ipa=d.get("ipa",{})
    if (ipa.get("node"),ipa.get("compatible"),ipa.get("hardware_version"),ipa.get("platform_type"),ipa.get("default_subsystem_gsi"),ipa.get("default_subsystem_uc"))!=("qcom,ipa@1e00000","qcom,ipa",18,1,"ipa_fws","ipa_uc"):
        result.append("node")
    if ipa.get("override_observed_in_reviewed_subset") is not False or ipa.get("runtime_override_values_verified") is not False:
        result.append("unverified override")
    fw=d.get("ipa_firmware_pil",{})
    if (fw.get("firmware_name"),fw.get("pas_id"),fw.get("name_is_modem"))!=("ipa_fws",15,False):
        result.append("firmware")
    chain=d.get("chain",{})
    for k in ("lito_v2_dts_includes_lito_v2","lito_v2_includes_lito","barbet_mp_includes_barbet","barbet_common_includes_redbull_common"):
        if chain.get(k) is not True: result.append("source chain")
    if chain.get("final_include_graph_complete") is not False or chain.get("compiled_dtb_verified") is not False:
        result.append("no DTB")
    if set(d.get("unverified",[]))!=GAPS: result.append("gaps")
    if any(v is not False for v in d.get("permissions",{}).values()) or d.get("hardware_tested") is not False:
        result.append("device modification")
    return result
class LitoIpaTests(unittest.TestCase):
    def setUp(self): self.d=json.loads(FILE.read_text())
    def test_baseline(self): self.assertEqual(errors(self.d),[])
    def test_pas_is_not_modem(self):
        self.d["ipa_firmware_pil"]["name_is_modem"]=True
        self.assertTrue(errors(self.d))
    def test_pas_id(self):
        self.d["ipa_firmware_pil"]["pas_id"]=4
        self.assertTrue(errors(self.d))
    def test_default_gsi(self):
        self.d["ipa"]["default_subsystem_gsi"]="modem"
        self.assertTrue(errors(self.d))
    def test_override_not_proven(self):
        self.d["ipa"]["runtime_override_values_verified"]=True
        self.assertTrue(errors(self.d))
    def test_final_dtb_not_verified(self):
        self.d["chain"]["compiled_dtb_verified"]=True
        self.assertTrue(errors(self.d))
    def test_full_graph_not_verified(self):
        self.d["chain"]["final_include_graph_complete"]=True
        self.assertTrue(errors(self.d))
    def test_modem_barrier_stays_unknown(self):
        self.d["unverified"].remove("vendor_SMEM_item134_published_before_MPSS")
        self.assertTrue(errors(self.d))
    def test_cannot_start_modem(self):
        self.d["permissions"]["modem_start"]=True
        self.assertTrue(errors(self.d))
    def test_no_hardware_claim(self):
        self.d["hardware_tested"]=True
        self.assertTrue(errors(self.d))
if __name__=="__main__":
    unittest.main()
