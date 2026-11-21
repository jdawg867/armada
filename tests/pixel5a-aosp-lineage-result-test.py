#!/usr/bin/env python3
"""Fail-closed regression tests for hosted Step 792 source-only comparison."""
import json
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-aosp-lineage-12l-comparison-result.json"
EXPECTED={"barbet/init.insmod.barbet.cfg":(True,0),"barbet/barbet/init.barbet.rc":(False,1),"redbull/BoardConfig-common.mk":(False,24),"redbull/init.hardware.rc":(False,13),"redbull/init.insmod.sh":(True,0)}
def issues(d):
    out=[]
    if (d.get("kind"),d.get("source_workflow_run_id"))!=("verified_public_aosp_lineage_android12l_text_comparison",43920100174):
        out.append("provenance")
    if (d.get("pairs_attempted"),d.get("pairs_compared"),d.get("pairs_unavailable"))!=(15,15,0):
        out.append("counts")
    rows=d.get("unique_paths",[])
    found={r["device"]+"/"+r["path"]:(r["identical_bytes"],r["hunks_changed"]) for r in rows}
    if len(rows)!=5 or found!=EXPECTED or any(r["identical_bytes"]!=(r["aosp_sha256"]==r["lineage_sha256"]) for r in rows):
        out.append("file comparisons")
    if d.get("missing_uncompared_aosp_module_list")!="device/google/redbull/modules.load":
        out.append("missing path")
    for field in ("exact_stock_vendor_boot_verified","stock_module_loading_verified","modemsmem_probe_before_mpss_start_verified","hardware_tested","source_diff_content_reviewed"):
        if d.get(field) is not False: out.append("unsupported "+field)
    return out
class ResultTests(unittest.TestCase):
    def setUp(self): self.d=json.loads(P.read_text())
    def test_baseline(self): self.assertEqual(issues(self.d),[])
    def test_counts(self):
        self.d["pairs_compared"]=14
        self.assertTrue(issues(self.d))
    def test_diff(self):
        self.d["unique_paths"][2]["hunks_changed"]=1
        self.assertTrue(issues(self.d))
    def test_identity(self):
        self.d["unique_paths"][0]["identical_bytes"]=False
        self.assertTrue(issues(self.d))
    def test_missing_file(self):
        self.d["missing_uncompared_aosp_module_list"]="invented"
        self.assertTrue(issues(self.d))
    def test_no_hardware_claim(self):
        self.d["hardware_tested"]=True
        self.assertTrue(issues(self.d))
    def test_no_boot_order_claim(self):
        self.d["modemsmem_probe_before_mpss_start_verified"]=True
        self.assertTrue(issues(self.d))
    def test_no_diff_content_claim(self):
        self.d["source_diff_content_reviewed"]=True
        self.assertTrue(issues(self.d))
if __name__=="__main__":
    unittest.main()
