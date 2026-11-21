#!/usr/bin/env python3
"""Pin downstream modemsmem write hazards; never infer safe ownership."""
import copy
import json
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "validation/pixel5a-downstream-modemsmem-write-audit.json"
UNSAFE = {
 "unconditional_zeroing_after_existing_allocation",
 "no_proven_owner_for_vendor_item",
 "no_remove_sysfs_cleanup",
 "sysfs_create_failure_does_not_fail_probe",
 "allocation_or_get_errors_collapsed_to_enomem",
 "boot_mode_and_flag_properties_need_exact_vendor_contract",
 "no_demonstrated_mpSS_start_order_dependency",
}
SOURCE = {
 "repository":"LineageOS/android_kernel_google_redbull",
 "commit":"929e7e2f3658867d51a1d423c7e000f5cf1d4043",
 "path":"drivers/soc/qcom/modemsmem/modemsmem.c",
 "blob":"428143562894e6d8ca7b656174c72ee4b096f510",
 "header_path":"drivers/soc/qcom/modemsmem/modemsmem.h",
 "header_blob":"a6b9d991fe7c023f44c21cc5c597746414c532a2",
}
def check(d):
    issues = []
    if (d.get("schema_version"),d.get("device"),d.get("scope")) != (
        1,"Pixel 5a barbet","pinned_lineage_redbull_source_only_not_safe_to_port"):
        issues.append("source research incorrectly elevated")
    if d.get("source") != SOURCE:
        issues.append("downstream source identity changed")
    v = d.get("vendor_smem",{})
    if any(v.get(k)!=n for k,n in {
      "item":134,"bytes":64,"alloc_api":"qcom_smem_alloc",
      "existing_item_errno":"-EEXIST","get_api":"qcom_smem_get",
      "probe_overwrites_existing":True,"clears_all_64_bytes":True,
      "clearing_call":"memset_io","write_api":"writel_relaxed",
      "existing_data_preserved":False,"ownership_documented":False
    }.items()):
        issues.append("destructive vendor SMEM source semantics changed")
    l = d.get("lifecycle",{})
    if any(l.get(k)!=n for k,n in {
      "platform_driver_register":True,"module_init":True,
      "remove_callback":False,"sysfs_create_group":True,
      "sysfs_failure_fatal":False,"sysfs_remove_group":False,
      "allocation_failure_mapped_to_enomem":True
    }.items()):
        issues.append("downstream lifecycle risks changed")
    props=d.get("inputs",{})
    if (props.get("modem_flag_path")!="/chosen/cdt/cdb2" or
       props.get("factory_bootmodes")!=["factory","ffbm-00","ffbm-01"] or
       props.get("factory_tunable_sysfs") is not True or
       props.get("dsds_property")!="dsds" or
       any(props.get(k)!=value for k,value in {
        "platform_version":"socinfo_get_g_platform_version",
        "platform_type":"socinfo_get_g_platform_type",
        "platform_subtype":"socinfo_get_g_platform_subtype"
       }.items())):
        issues.append("vendor boot inputs incorrectly described")
    if set(d.get("unsafe_to_copy",[]))!=UNSAFE:
        issues.append("unresolved vendor hazards omitted")
    policy=d.get("research_port",{})
    if set(policy)!={"allow_allocation","allow_existing_item_overwrite",
                      "allow_publication","allow_driver_activation",
                      "allow_modem_start","allow_factory_sysfs"} or (
                      any(x is not False for x in policy.values())):
        issues.append("unsafe port permission enabled")
    if d.get("hardware_verified") is not False:
        issues.append("unsupported hardware verification")
    return issues

class VendorSourceAudit(unittest.TestCase):
    def setUp(self):
        self.d=json.loads(PATH.read_text())
    def test_baseline(self):
        self.assertEqual(check(self.d),[])
    def test_source_tamper(self):
        self.d["source"]["blob"]="unreviewed"
        self.assertIn("downstream source identity changed",check(self.d))
    def test_no_overwrite_promotion(self):
        self.d["research_port"]["allow_existing_item_overwrite"]=True
        self.assertIn("unsafe port permission enabled",check(self.d))
    def test_no_allocation_promotion(self):
        self.d["research_port"]["allow_allocation"]=True
        self.assertIn("unsafe port permission enabled",check(self.d))
    def test_no_factory_sysfs(self):
        self.d["research_port"]["allow_factory_sysfs"]=True
        self.assertIn("unsafe port permission enabled",check(self.d))
    def test_no_false_preservation(self):
        self.d["vendor_smem"]["existing_data_preserved"]=True
        self.assertIn("destructive vendor SMEM source semantics changed",check(self.d))
    def test_no_false_cleanup(self):
        self.d["lifecycle"]["remove_callback"]=True
        self.assertIn("downstream lifecycle risks changed",check(self.d))
    def test_no_hidden_hazards(self):
        self.d["unsafe_to_copy"].pop()
        self.assertIn("unresolved vendor hazards omitted",check(self.d))
    def test_no_hardware_claim(self):
        self.d["hardware_verified"]=True
        self.assertIn("unsupported hardware verification",check(self.d))
    def test_no_boot_flag_invention(self):
        self.d["inputs"]["modem_flag_path"]="/chosen/unverified"
        self.assertIn("vendor boot inputs incorrectly described",check(self.d))

if __name__=="__main__":
    unittest.main()
