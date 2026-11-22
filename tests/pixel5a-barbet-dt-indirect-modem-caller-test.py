#!/usr/bin/env python3
"""Step 798: prevent source include/callsite evidence from becoming modem boot claims."""
import json
import unittest
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"validation/pixel5a-barbet-dt-indirect-modem-caller-audit.json"
CHAIN=[
("arch/arm64/boot/dts/google/lito-barbet.dtsi","lito-barbet-common.dtsi"),
("arch/arm64/boot/dts/google/lito-barbet-common.dtsi","lito-redbull-common.dtsi"),
("arch/arm64/boot/dts/google/lito-redbull-common.dtsi","lito-redbull-audio.dtsi"),
("arch/arm64/boot/dts/google/lito-redbull-audio.dtsi","qcom-base/lito-audio-overlay.dtsi")]
CALLERS={
"techpack/audio/dsp/adsp-loader.c":("subsystem_get(\"modem\")","literal_modem_only_conditional"),
"drivers/platform/msm/ipa/ipa_v3/ipa.c":("subsystem_get(sub_sys)","dynamic_argument_unresolved"),
"drivers/net/wireless/cnss2/main.c":("subsystem_get(subsys_info->subsys_desc.name)","source_sets_name_wlan"),
"drivers/gpu/msm/adreno_a6xx.c":("subsystem_get(a6xx_core->zap_name)","dynamic_gpu_firmware_name_not_classified_modem")}
UNKNOWN={
"final_barbet_dtb_and_overlay_resolution","qcom_base_audio_overlay_include_mapping",
"runtime_adsp_loader_proc_img_to_load_property","IPA_dynamic_sub_sys_argument_values_on_barbet",
"other_nonliteral_and_userspace_modem_start_routes","which_modem_PIL_driver_binds_on_barbet",
"stock_android12l_vendor_boot_and_init_execution",
"vendor_item134_publication_before_mpss_firmware_start",
"modem_restart_republication_and_telephony_validation"}
def check(d):
    failures=[]
    if (d.get("step"),d.get("classification"),d.get("kernel",{}).get("commit"))!=(
        798,"bounded_pinned_source_graph_and_callsite_audit_not_flattened_DTB",
        "929e7e2f3658867d51a1d423c7e000f5cf1d4043"):
        failures.append("source identity")
    chain=d.get("include_chain",[])
    if [(x.get("from"),x.get("to")) for x in chain]!=CHAIN or any(len(x.get("blob",""))!=40 for x in chain):
        failures.append("include graph")
    audio=d.get("audio_source",{})
    for name in ("inspected_files_contain_modem_image_selection","final_preprocessed_dtb_verified",
                 "qcom_base_overlay_path_mapping_verified"):
        if audio.get(name) is not False: failures.append("source promoted to DTB")
    if audio.get("base_adsp_loader_enabled") is not True or audio.get("overlay_sets_adsp_variant") is not True:
        failures.append("audio source observation")
    callers=d.get("callers",[])
    actual={x.get("file"):(x.get("expression"),x.get("classification")) for x in callers}
    if len(callers)!=4 or actual!=CALLERS or any(x.get("runtime_executed") is not False for x in callers):
        failures.append("unverified caller")
    other=d.get("other_modem_framework",{})
    if other.get("declares_subsystem_modem") is not True or other.get("registered_on_barbet") is not False:
        failures.append("alternate modem framework")
    if set(d.get("unresolved",[]))!=UNKNOWN: failures.append("missing boot uncertainty")
    if d.get("hardware_tested") is not False or any(x is not False for x in d.get("activation",{}).values()):
        failures.append("unapproved device action")
    return failures
class EvidenceTests(unittest.TestCase):
    def setUp(self): self.d=json.loads(P.read_text())
    def test_baseline(self): self.assertEqual(check(self.d),[])
    def test_no_final_dtb(self):
        self.d["audio_source"]["final_preprocessed_dtb_verified"]=True
        self.assertTrue(check(self.d))
    def test_modem_loader_not_selected(self):
        self.d["audio_source"]["inspected_files_contain_modem_image_selection"]=True
        self.assertTrue(check(self.d))
    def test_ipa_variable_not_literal_modem(self):
        self.d["callers"][1]["classification"]="literal_modem"
        self.assertTrue(check(self.d))
    def test_cnss_wlan_not_modem(self):
        self.d["callers"][2]["classification"]="literal_modem"
        self.assertTrue(check(self.d))
    def test_alternate_driver_not_active(self):
        self.d["other_modem_framework"]["registered_on_barbet"]=True
        self.assertTrue(check(self.d))
    def test_runtime_call_not_confirmed(self):
        self.d["callers"][0]["runtime_executed"]=True
        self.assertTrue(check(self.d))
    def test_smem_barrier_not_verified(self):
        self.d["unresolved"].remove("vendor_item134_publication_before_mpss_firmware_start")
        self.assertTrue(check(self.d))
    def test_no_flash(self):
        self.d["activation"]["allow_phone_flash"]=True
        self.assertTrue(check(self.d))
    def test_source_identity(self):
        self.d["kernel"]["commit"]="main"
        self.assertTrue(check(self.d))
if __name__=="__main__":
    unittest.main()
