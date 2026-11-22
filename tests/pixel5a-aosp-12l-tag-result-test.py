#!/usr/bin/env python3
"""Regression gate for Step 791's actual online AOSP tag fetch result."""
import json
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/"validation/pixel5a-aosp-12l-tag-probe-result.json"
KNOWN={
"device/google/barbet/init.insmod.barbet.cfg":"a081d17fbfe8995aaf64ee8dfd4e528a13756d1deb3f660f22da55f044fe8383",
"device/google/barbet/barbet/init.barbet.rc":"78a14c15c8c71b5d40c712009711636bbd8505e85419cfec92ec4e15e9bbef4e",
"device/google/redbull/BoardConfig-common.mk":"27a623d774cb7818a892d340c9a36aee732f69f4d482b0a73fdf30757fbf5ff3",
"device/google/redbull/init.hardware.rc":"5cf98b4bab2359a81f5ddf3b10db397f9ff0361ad850733226cc7ed30f21f294",
"device/google/redbull/init.insmod.sh":"d6ca82cf42232a1b1e934827e055c024f39f5fdc1def5905b6f131bbb62f0855"}
TAGS=["android-12.1.0_r1","android-12.1.0_r5","android-12.1.0_r7"]
FALSE=("all_files_retrieved","source_compared_to_lineage_bytes",
       "stock_vendor_boot_image_inspected","stock_runtime_module_load_verified",
       "modemsmem_before_mpss_start_verified","device_hardware_tested")
def errors(x):
    out=[]
    if x.get("schema_version")!=1 or x.get("kind")!="official_aosp_tag_text_probe_result":
        out.append("invalid provenance scope")
    if x.get("github_workflow_run")!=43916059845 or x.get("commit")!="c209f41d665c52c2c7a374610f6a0b246e20fab8":
        out.append("wrong verified workflow identity")
    if x.get("source")!="https://android.googlesource.com/device/google" or x.get("tags")!=TAGS:
        out.append("source tags changed")
    if (x.get("retrieved_count"),x.get("unavailable_count"),x.get("total_attempted"))!=(15,3,18):
        out.append("retrieval result changed")
    if x.get("sha256_by_path")!=KNOWN or x.get("all_retrieved_file_hashes_identical_across_sampled_tags") is not True:
        out.append("published source hashes changed")
    if x.get("unavailable_paths")!=[{"path":"device/google/redbull/modules.load","tags":TAGS,"http_status":404}]:
        out.append("missing source file incorrectly represented")
    for field in FALSE:
        if x.get(field) is not False:
            out.append("unsupported verification claim "+field)
    return out

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads(PATH.read_text())
    def test_record(self):
        self.assertEqual(errors(self.record),[])
    def test_wrong_run(self):
        self.record["github_workflow_run"]=1
        self.assertTrue(errors(self.record))
    def test_missing_files_not_success(self):
        self.record["all_files_retrieved"]=True
        self.assertTrue(errors(self.record))
    def test_no_stock_image_claim(self):
        self.record["stock_vendor_boot_image_inspected"]=True
        self.assertTrue(errors(self.record))
    def test_no_boot_order_claim(self):
        self.record["modemsmem_before_mpss_start_verified"]=True
        self.assertTrue(errors(self.record))
    def test_no_lineage_byte_comparison_claim(self):
        self.record["source_compared_to_lineage_bytes"]=True
        self.assertTrue(errors(self.record))
    def test_refuse_invented_modules_load(self):
        self.record["unavailable_paths"]=[]
        self.assertTrue(errors(self.record))
    def test_refuse_hash_mismatch(self):
        self.record["sha256_by_path"]["device/google/redbull/init.insmod.sh"]="unverified"
        self.assertTrue(errors(self.record))
    def test_no_hardware_claim(self):
        self.record["device_hardware_tested"]=True
        self.assertTrue(errors(self.record))
if __name__=="__main__":
    unittest.main()
