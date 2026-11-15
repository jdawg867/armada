#!/usr/bin/env python3
"""Fail-closed dependency audit; metadata evidence, not modem/device testing."""
import json
from pathlib import Path
import unittest

MANIFEST = Path(__file__).resolve().parents[1] / "validation/pixel5a-modem-dependencies.json"
REQUIRED = {
    "reserved_memory", "modemsmem", "remoteproc", "smp2p_ipcc",
    "glink_qrtr", "ipa_gsi_iommu", "telephony_userspace", "android_recovery"
}
STATUS = {"unverified", "rfc_only", "partial_source_evidence", "source_verified", "hardware_verified"}

def validate(record):
    problems = []
    if record.get("schema_version") != 1 or record.get("source_phase_only") is not True:
        problems.append("invalid source-only phase")
    if record.get("target") != "Google Pixel 5a (barbet / SM7250)":
        problems.append("target mismatch")
    sources = record.get("sources")
    if not isinstance(sources, list):
        return problems + ["invalid sources"]
    indexed = {}
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("id"), str):
            problems.append("invalid source entry")
            continue
        sid = source["id"]
        if sid in indexed:
            problems.append("duplicate source " + sid)
        indexed[sid] = source
        if source.get("kind") == "private_patch":
            if source.get("git_blob") != "8c32955827e9bd17873b5660db4cfa0037e9585c":
                problems.append("private patch blob mismatch")
        elif source.get("kind") == "public_rfc":
            if source.get("url") != "https://lists.openwall.net/linux-kernel/2026/09/06/26" or (
                source.get("message_id") != "20260906-modemsmem-v1-2-a3634b553841@ixit.cz"
            ):
                problems.append("RFC provenance mismatch")
        else:
            problems.append("unknown source category")
    if set(indexed) != {"preserved_linux_patch", "modemsmem_rfc_2026"}:
        problems.append("missing or extra source")
    dependencies = record.get("dependencies")
    if not isinstance(dependencies, list):
        return problems + ["invalid dependencies"]
    by_id = {}
    for entry in dependencies:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            problems.append("invalid dependency")
            continue
        ident = entry["id"]
        if ident in by_id:
            problems.append("duplicate dependency " + ident)
        by_id[ident] = entry
        if entry.get("status") not in STATUS:
            problems.append("unknown dependency status " + ident)
        if entry.get("blocking") is not True:
            problems.append("missing blocking gate " + ident)
        evidence = entry.get("evidence")
        if not isinstance(evidence, list) or any(s not in indexed for s in evidence):
            problems.append("invalid evidence refs " + ident)
        if entry.get("status") in {"source_verified", "hardware_verified"}:
            problems.append("unverified claim in source-only phase " + ident)
        if not isinstance(entry.get("details"), str) or not entry["details"].strip():
            problems.append("missing dependency description " + ident)
    if set(by_id) != REQUIRED:
        problems.append("dependency set mismatch")
    if by_id.get("modemsmem", {}).get("status") != "rfc_only" or (
        by_id.get("modemsmem", {}).get("evidence") != ["modemsmem_rfc_2026"]
    ):
        problems.append("Pixel modemsmem must remain explicitly RFC-only")
    if record.get("modem_ready") is not False:
        problems.append("unsupported modem-ready claim")
    return problems

class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.base = json.loads(MANIFEST.read_text(encoding="utf-8"))
    def test_baseline(self):
        self.assertEqual(validate(self.base), [])
    def test_ready_rejected(self):
        self.base["modem_ready"] = True
        self.assertIn("unsupported modem-ready claim", validate(self.base))
    def test_rfc_is_not_verified(self):
        next(x for x in self.base["dependencies"] if x["id"] == "modemsmem")["status"] = "source_verified"
        self.assertTrue(any("RFC-only" in e for e in validate(self.base)))
    def test_missing_dependency(self):
        self.base["dependencies"].pop()
        self.assertIn("dependency set mismatch", validate(self.base))
    def test_duplicate_dependency(self):
        self.base["dependencies"].append(dict(self.base["dependencies"][0]))
        self.assertTrue(any("duplicate dependency" in e for e in validate(self.base)))
    def test_source_tamper(self):
        self.base["sources"][0]["git_blob"] = "unverified"
        self.assertIn("private patch blob mismatch", validate(self.base))
    def test_missing_evidence_reference(self):
        self.base["dependencies"][0]["evidence"] = ["no-such-source"]
        self.assertTrue(any("invalid evidence refs" in e for e in validate(self.base)))
    def test_hardware_claim_rejected(self):
        self.base["dependencies"][0]["status"] = "hardware_verified"
        self.assertTrue(any("unverified claim" in e for e in validate(self.base)))

if __name__ == "__main__":
    unittest.main()
