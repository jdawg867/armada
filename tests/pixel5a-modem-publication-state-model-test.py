#!/usr/bin/env python3
"""Host-only Step 806 proof that proposed publication gate defaults to deny."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "pixel5a-modemsmem"))
from modem_publication_gate import Gate, transition

PATH = ROOT / "validation/pixel5a-modem-publication-offline-state-model.json"
GAPS = {
    "compiled_Barbet_DTB_and_overrides", "actual_DT_probe_links_and_runtime_order",
    "item134_original_ownership_and_contents",
    "payload_visibility_ack_protocol_or_modem_capability",
    "who_requests_first_MPSS_start", "modem_crash_and_recovery_ownership",
    "stock_vendor_boot_and_Android_runtime", "actual_hardware_telephony"
}
PROPOSAL = {
    "default_modem_disabled", "requires_provider_ready",
    "requires_exclusive_owner_clearance", "requires_existing_item_preservation",
    "requires_valid_exact_64_byte_payload", "requires_payload_visibility_confirmed",
    "requires_explicit_acknowledgement", "requires_manual_authorization",
    "revokes_on_crash_or_provider_loss", "never_auto_republishes_existing_item",
}
def full(existing=True):
    s = Gate()
    for e in ("provider_ready", "existing_item" if existing else "new_item",
              "owner_cleared", "preservation_verified", "payload_validated",
              "visibility_confirmed", "acknowledged", "manual_authorized"):
        s = transition(s, e)
    return s

class GateTests(unittest.TestCase):
    def test_manifest_source_pins_and_limits(self):
        d=json.loads(PATH.read_text())
        s=d["source"]
        self.assertEqual(d["step"],806)
        self.assertEqual(s["commit"],"929e7e2f3658867d51a1d423c7e000f5cf1d4043")
        self.assertEqual(s["lito_blob"],"24b013a4b166456be0a1f8a4a278d9fb3dcfccd1")
        self.assertEqual(s["google_common_blob"],"9eea9dc7431c5ef6cc68f100789402c025b558ce")
        self.assertFalse(d["observed"]["modem_explicit_dt_dependency_on_consumer_present"])
        self.assertFalse(d["observed"]["consumer_explicit_dt_phandle_to_provider_present"])
        self.assertEqual(set(d["unverified"]),GAPS)
        self.assertEqual(d["offline_policy"]["mode"],"simulation_only_not_kernel_integration")
        self.assertTrue(all(d["offline_policy"][k] for k in PROPOSAL))
        self.assertTrue(all(v is False for v in d["safety"].values()))
        self.assertIs(d["hardware_tested"],False)

    def test_initial_gate_denied(self):
        self.assertFalse(Gate().may_start)
    def test_provider_deferred(self):
        with self.assertRaisesRegex(ValueError, "EPROBE_DEFER"):
            transition(Gate(),"existing_item")
    def test_no_ownership_reuse(self):
        s=transition(transition(Gate(),"provider_ready"),"existing_item")
        self.assertFalse(s.may_start)
        with self.assertRaisesRegex(ValueError,"owner clearance"):
            transition(s,"payload_validated")
    def test_no_unspecified_existing_reset(self):
        s=transition(transition(transition(Gate(),"provider_ready"),"existing_item"),"owner_cleared")
        with self.assertRaisesRegex(ValueError,"policy not verified"):
            transition(s,"payload_validated")
    def test_no_premature_visibility(self):
        s=Gate()
        for e in ("provider_ready","existing_item","owner_cleared","preservation_verified"):
            s=transition(s,e)
        with self.assertRaisesRegex(ValueError,"invalid or incomplete"):
            transition(s,"visibility_confirmed")
    def test_no_ack_before_visibility(self):
        s=Gate()
        for e in ("provider_ready","existing_item","owner_cleared","preservation_verified","payload_validated"):
            s=transition(s,e)
        with self.assertRaisesRegex(ValueError,"visibility"):
            transition(s,"acknowledged")
    def test_no_manual_authorization_before_ack(self):
        s=Gate()
        for e in ("provider_ready","existing_item","owner_cleared","preservation_verified","payload_validated","visibility_confirmed"):
            s=transition(s,e)
        with self.assertRaisesRegex(ValueError,"acknowledgement"):
            transition(s,"manual_authorized")
    def test_requires_each_final_gate(self):
        s=full()
        self.assertTrue(s.may_start) # simulated decision only
        from dataclasses import replace
        for key in ("provider_ready","owner_cleared","existing_item_preserved",
                    "payload_valid","visible","acknowledged","manual_authorized"):
            self.assertFalse(replace(s, **{key:False}).may_start,key)
    def test_new_item_requires_same_policy(self):
        self.assertTrue(full(False).may_start)
    def test_crash_revokes_and_revalidation(self):
        s=transition(full(),"crash")
        self.assertFalse(s.may_start)
        with self.assertRaisesRegex(ValueError,"recovery is blocked"):
            transition(s,"manual_authorized")
        s=transition(s,"recovery_reviewed")
        self.assertEqual(s,Gate())
        self.assertFalse(s.may_start)
    def test_provider_loss_revokes_and_needs_provider_retry(self):
        s=transition(full(),"provider_lost")
        self.assertFalse(s.may_start)
        s=transition(s,"recovery_reviewed")
        with self.assertRaisesRegex(ValueError,"EPROBE_DEFER"):
            transition(s,"existing_item")
    def test_unknown_events_fail_closed(self):
        with self.assertRaises(ValueError):
            transition(full(),"start_modem")
    def test_repeat_item_discovery_rejected(self):
        with self.assertRaisesRegex(ValueError,"already performed"):
            transition(full(),"existing_item")

if __name__=="__main__":
    unittest.main()
