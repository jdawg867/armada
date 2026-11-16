#!/usr/bin/env python3
"""Step 790: official stock Android 12L release identity, NOT binary boot inspection."""
import json
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/"validation/pixel5a-stock-android12l-image-evidence.json"
RELEASES=[
 ("SP2A.220305.012","android-12.1.0_r1","2022-03","android-12.1.0_r0.5","android-msm-barbet-4.19-android12L"),
 ("SP2A.220505.002","android-12.1.0_r5","2022-05","android-12.1.0_r0.21","android-msm-barbet-4.19-android12L"),
 ("SQ3A.220605.009.A1","android-12.1.0_r7","2022-06","android-12.1.0_r0.27","android-msm-barbet-4.19-android12-qpr3"),
]
FALSE_FIELDS=(
 "binary_vendor_boot_image_downloaded","binary_vendor_boot_hash_verified",
 "binary_vendor_boot_extracted","actual_stock_modules_load_verified",
 "actual_stock_modemsmem_module_probed","actual_stock_mpss_start_order_verified",
 "device_boot_logs_examined","android12l_aosp_tag_files_compared_to_stock_image",
 "stock_image_can_be_used_without_google_license_review",
 "modem_functional_verified","device_modified"
)
BLOCKERS={
 "obtain_licensed_exact_build_vendor_boot_for_offline_inspection",
 "verify_exact_build_and_digest_before_parsing",
 "identify_module_load_order_from_image_not_assumption",
 "distinguish_module_load_completion_from_driver_probe_completion",
 "verify_modemsmem_to_mpss_dependency_and_crash_recovery",
 "verify_device_variant_and_vendor_firmware_release"
}
def audit(d):
    issues=[]
    if (d.get("schema_version"),d.get("device"),d.get("codename"),d.get("scope")) != (
      1,"Google Pixel 5a (5G)","barbet",
      "official_android12l_release_identity_only_stock_vendor_boot_not_extracted"):
        issues.append("unverified stock scope promoted")
    if (d.get("official_release_source") !=
        "https://groups.google.com/g/android-building/c/GoMawyG2l94/m/gF67Adc6EQAJ"
        or d.get("official_factory_index") != "https://developers.google.com/android/images"
        or d.get("official_ota_index") != "https://developers.google.com/android/ota"):
        issues.append("official release provenance changed")
    releases=d.get("releases",[])
    actual=[(r.get("build"),r.get("tag"),r.get("month"),
             r.get("kernel_tag"),r.get("kernel_branch")) for r in releases]
    if actual!=RELEASES or any(r.get("android_version")!="12.1.0" or
      r.get("kernel_project")!="device/google/barbet-kernel" for r in releases):
        issues.append("official build/tag mapping changed")
    for name in FALSE_FIELDS:
        if d.get(name) is not False:
            issues.append("unsupported stock image or device verification: "+name)
    if d.get("verified_from_official_release_announcement") is not True:
        issues.append("release announcement not grounded")
    if d.get("allowed_workflow")!="source_only_no_flashing_no_redistribution":
        issues.append("unsafe boot image workflow")
    if set(d.get("blockers",[]))!=BLOCKERS:
        issues.append("stock verification blockers omitted")
    if set(d.get("source_tree_paths_for_readonly_followup",[]))!={
      "device/google/barbet/init.insmod.barbet.cfg",
      "device/google/redbull/BoardConfig-common.mk",
      "device/google/redbull/modules.load",
      "device/google/redbull/init.hardware.rc",
      "device/google/redbull/init.insmod.sh"}:
        issues.append("source follow-up missing")
    return issues

class StockReleaseTest(unittest.TestCase):
    def setUp(self):
        self.d=json.loads(PATH.read_text())
    def test_baseline(self):
        self.assertEqual(audit(self.d),[])
    def test_wrong_build(self):
        self.d["releases"][1]["build"]="unverified"
        self.assertIn("official build/tag mapping changed",audit(self.d))
    def test_wrong_release_tag(self):
        self.d["releases"][2]["tag"]="android-12.1.0_r8"
        self.assertIn("official build/tag mapping changed",audit(self.d))
    def test_wrong_kernel_branch(self):
        self.d["releases"][2]["kernel_branch"]="unknown"
        self.assertIn("official build/tag mapping changed",audit(self.d))
    def test_fake_download(self):
        self.d["binary_vendor_boot_image_downloaded"]=True
        self.assertTrue(audit(self.d))
    def test_fake_hash(self):
        self.d["binary_vendor_boot_hash_verified"]=True
        self.assertTrue(audit(self.d))
    def test_fake_module_order(self):
        self.d["actual_stock_modules_load_verified"]=True
        self.assertTrue(audit(self.d))
    def test_fake_probe_success(self):
        self.d["actual_stock_modemsmem_module_probed"]=True
        self.assertTrue(audit(self.d))
    def test_fake_mpss_order(self):
        self.d["actual_stock_mpss_start_order_verified"]=True
        self.assertTrue(audit(self.d))
    def test_allow_firmware(self):
        self.d["allowed_workflow"]="flash_firmware"
        self.assertIn("unsafe boot image workflow",audit(self.d))
    def test_missing_license_gate(self):
        self.d["blockers"].remove("obtain_licensed_exact_build_vendor_boot_for_offline_inspection")
        self.assertIn("stock verification blockers omitted",audit(self.d))
    def test_hardware_not_ready(self):
        self.d["modem_functional_verified"]=True
        self.assertTrue(audit(self.d))
if __name__=="__main__":
    unittest.main()
