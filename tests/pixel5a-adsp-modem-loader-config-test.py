#!/usr/bin/env python3
"""Step 797: refuse to promote a conditional ADSP code path into Pixel 5a boot evidence."""
import json
import unittest
from pathlib import Path

FILE=Path(__file__).resolve().parents[1]/"validation/pixel5a-adsp-modem-loader-config-audit.json"
PINS={
"arch/arm64/boot/dts/vendor/qcom/msm-audio-lpass.dtsi":"a9496d85ef337acf1802bccd1cbeb73e47acae7e",
"arch/arm64/boot/dts/vendor/qcom/lito-audio.dtsi":"b0c71b6bef60277d3bd694ab21b3b52616ea9529",
"arch/arm64/boot/dts/vendor/qcom/lito-audio-overlay.dtsi":"d40caafaa79af5726f4cdae22a4992d36a84c5d4",
"arch/arm64/boot/dts/google/lito-redbull-audio.dtsi":"6fc430fff036faed2c92217aace7e3be2455985e",
"arch/arm64/boot/dts/google/lito-barbet-audio.dtsi":"b8b9b41e3de01936a851ed33d1c592684f7374e2",
"techpack/audio/dsp/adsp-loader.c":"a32acfd359092d4a8cdbcb2da804d0ec8601da0b"}
YES={"msm_audio_lpass_declares_adsp_loader","adsp_loader_enabled_in_lpass_source",
"adsp_state_zero_in_lpass_source","lito_audio_includes_msm_audio_lpass",
"redbull_audio_includes_lito_audio_overlay","overlay_adds_adsp_variant_nvmem",
"overlay_adds_adsp2_variant_firmware_name",
"adsp_loader_code_defaults_to_adsp_when_image_property_absent",
"adsp_loader_contains_conditional_subsystem_get_modem"}
NO={"inspected_lpass_node_selects_modem_image","inspected_lito_audio_overlay_selects_modem_image",
"conditional_modem_call_proven_executed_on_pixel5a","entire_final_dtb_and_all_overrides_resolved"}
GAPS={"all_final_barbet_audio_dtb_overrides","complete_dt_include_graph_and_preprocessor_expansion",
"whether_runtime_proc_img_property_is_modem","all_possible_nonliteral_modem_subsystem_get_callers",
"initial_modem_firmware_boot_source_and_timing","smem_134_publication_barrier_before_firmware_start",
"stock_android12l_boot_trace_and_vendor_boot_binary","voice_sms_mobile_data_actual_operation"}
def validate(d):
    issues=[]
    if (d.get("step"),d.get("scope"),d.get("kernel_commit"))!=(797,
        "pinned_source_only_adsp_loader_configuration_not_final_dtb",
        "929e7e2f3658867d51a1d423c7e000f5cf1d4043"):
        issues.append("invalid scope")
    if d.get("paths")!=PINS: issues.append("incorrect provenance")
    o=d.get("observed",{})
    if set(o)!=YES|NO or any(o.get(x) is not True for x in YES) or any(o.get(x) is not False for x in NO):
        issues.append("source observation promoted")
    if set(d.get("unverified",[]))!=GAPS: issues.append("missing uncertainty")
    s=d.get("safety",{})
    if set(s)!={"firmware_boot","smem_write","driver_activation","device_flash"} or any(x is not False for x in s.values()):
        issues.append("unsafe authorization")
    if d.get("hardware_tested") is not False: issues.append("hardware not tested")
    return issues
class ConfigTests(unittest.TestCase):
    def setUp(self): self.d=json.loads(FILE.read_text())
    def test_baseline(self): self.assertEqual(validate(self.d),[])
    def test_pin(self):
        self.d["paths"]["techpack/audio/dsp/adsp-loader.c"]="wrong"
        self.assertTrue(validate(self.d))
    def test_modem_not_selected(self):
        self.d["observed"]["inspected_lpass_node_selects_modem_image"]=True
        self.assertTrue(validate(self.d))
    def test_overlay_modem_not_selected(self):
        self.d["observed"]["inspected_lito_audio_overlay_selects_modem_image"]=True
        self.assertTrue(validate(self.d))
    def test_default_adsp(self):
        self.d["observed"]["adsp_loader_code_defaults_to_adsp_when_image_property_absent"]=False
        self.assertTrue(validate(self.d))
    def test_final_dtb_not_claimed(self):
        self.d["observed"]["entire_final_dtb_and_all_overrides_resolved"]=True
        self.assertTrue(validate(self.d))
    def test_source_does_not_prove_boot(self):
        self.d["observed"]["conditional_modem_call_proven_executed_on_pixel5a"]=True
        self.assertTrue(validate(self.d))
    def test_no_modem_publication_claim(self):
        self.d["unverified"].remove("smem_134_publication_barrier_before_firmware_start")
        self.assertTrue(validate(self.d))
    def test_no_activation(self):
        self.d["safety"]["firmware_boot"]=True
        self.assertTrue(validate(self.d))
    def test_no_hardware_claim(self):
        self.d["hardware_tested"]=True
        self.assertTrue(validate(self.d))
if __name__=="__main__":
    unittest.main()
