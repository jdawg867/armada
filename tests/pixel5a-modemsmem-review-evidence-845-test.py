#!/usr/bin/env python3
"""Step 845: keep RFC review status accurate without claiming phone readiness."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "research/pixel5a-modemsmem/review-only/0001-modemsmem-preserve-smem-deferred-probe.patch"

def violations(text):
    if "\n--- a/drivers/soc/qcom/modemsmem/modemsmem.c\n" not in text:
        return ["unrecognized patch target"]
    header, diff = text.split("\n--- a/drivers/soc/qcom/modemsmem/modemsmem.c\n", 1)
    issues = []
    if "Review-only candidate." not in header:
        issues.append("must remain review-only")
    if "compiled against the pinned Redbull 4.19 source" not in header:
        issues.append("actual compile evidence missing")
    if "45324044445" not in header:
        issues.append("verified compile run reference missing")
    if "compile-only evidence" not in header:
        issues.append("compile scope boundary missing")
    for statement in ("not a boot or modem test", "Not deployed on the Pixel 5a",
                      "merged, or sent upstream"):
        if statement not in header:
            issues.append("missing safety boundary: " + statement)
    if "Not compiled against the pinned redbull tree" in header:
        issues.append("stale claim about source compilation")
    if "calls/SMS/data verified" in header or "runtime verified" in header:
        issues.append("unverified hardware claim")
    required = (
        "+\t\tif (ret == -EPROBE_DEFER)",
        "+\t\tif (PTR_ERR(modem_smem) == -EPROBE_DEFER)",
        " \tif (ret && ret != -EEXIST) {",
        "+\tif (size != sizeof(struct modem_smem_type)) {",
    )
    if any(line not in diff for line in required):
        issues.append("reviewed patch hunk drift")
    return issues

class PatchReviewMetadata(unittest.TestCase):
    def test_pinned_compilation_and_safety_claims(self):
        text = PATCH.read_text(encoding="utf-8")
        self.assertEqual(violations(text), [])
    def test_reject_stale_compile_status(self):
        text = PATCH.read_text(encoding="utf-8").replace(
            "compiled against the pinned Redbull 4.19 source",
            "Not compiled against the pinned redbull tree")
        self.assertTrue(violations(text))
    def test_reject_unverified_hardware_claim(self):
        text = PATCH.read_text(encoding="utf-8").replace(
            "not a boot or modem test", "runtime verified")
        self.assertTrue(violations(text))
    def test_reject_missing_isolation(self):
        text = PATCH.read_text(encoding="utf-8").replace("Review-only candidate.", "Approved kernel patch.")
        self.assertTrue(violations(text))
    def test_reject_missing_source_hunk(self):
        text = PATCH.read_text(encoding="utf-8").replace(
            "+\t\tif (ret == -EPROBE_DEFER)", "+\t\tif (ret == -ENOMEM)")
        self.assertTrue(violations(text))

if __name__ == "__main__":
    unittest.main()
