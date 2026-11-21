#!/usr/bin/env python3
"""Source-only regression snapshot for Step 794 pinned Lineage ordering."""
import json
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"validation/pixel5a-lineage-first-stage-module-projection.json"
EXPECTED=[("smem.ko",34,30),("subsys-pil-tz.ko",53,47),("modemsmem.ko",83,74)]
FALSE=("smem_publication_before_mpss_proven","stock_vendor_boot_verified",
       "driver_probe_completion_verified","actual_firmware_start_time_verified",
       "hardware_tested","source_loader_checks_modprobe_exit_status")
def validate(r):
    issues=[]
    if (r.get("schema_version"),r.get("kind"),r.get("scope")) != (1,
      "pinned_lineage_first_stage_source_projection",
      "source_only_not_generated_vendor_boot_or_runtime"):
        issues.append("incorrect provenance")
    if r.get("commit")!="9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770" or (
        r.get("module_list_blob")!="b116d1f234682a1f7e7275f36e6c7a2feb79ddb5"):
        issues.append("unverified source")
    if tuple(r.get(k) for k in ("list_total","common_boot_eligibility_count",
       "lineage_boot_extra_count","projected_boot_count","projected_vendor_count"))!=(
         329,219,2,220,109):
        issues.append("incorrect source counts")
    watch=[(x.get("name"),x.get("list_index_zero_based"),
            x.get("projected_boot_index_zero_based")) for x in r.get("watch",[])]
    if watch!=EXPECTED or r.get("pil_before_modemsmem_in_source_list") is not True:
        issues.append("incorrect module order")
    if any(r.get(field) is not False for field in FALSE):
        issues.append("unsupported runtime or probe claim")
    return issues
class ProjectionEvidenceTests(unittest.TestCase):
    def setUp(self): self.d=json.loads(P.read_text())
    def test_valid(self): self.assertEqual(validate(self.d),[])
    def test_not_stock(self):
        self.d["stock_vendor_boot_verified"]=True
        self.assertTrue(validate(self.d))
    def test_no_pil_start_claim(self):
        self.d["smem_publication_before_mpss_proven"]=True
        self.assertTrue(validate(self.d))
    def test_order(self):
        self.d["watch"][1]["projected_boot_index_zero_based"]=74
        self.assertTrue(validate(self.d))
    def test_count(self):
        self.d["projected_boot_count"]=219
        self.assertTrue(validate(self.d))
    def test_source(self):
        self.d["module_list_blob"]="not-pinned"
        self.assertTrue(validate(self.d))
    def test_probe_not_done(self):
        self.d["driver_probe_completion_verified"]=True
        self.assertTrue(validate(self.d))
    def test_loader_status_not_checked(self):
        self.d["source_loader_checks_modprobe_exit_status"]=True
        self.assertTrue(validate(self.d))
if __name__=="__main__":
    unittest.main()
