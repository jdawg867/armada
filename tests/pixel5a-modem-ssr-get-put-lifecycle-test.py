#!/usr/bin/env python3
"""Step 813 SSR get/put audit: pinned source claims only, no device access."""
import copy
import json
import unittest
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "validation/pixel5a-modem-ssr-get-put-lifecycle-audit.json"
PIN = {
    "repository": "LineageOS/android_kernel_google_redbull",
    "commit": "929e7e2f3658867d51a1d423c7e000f5cf1d4043",
    "path": "drivers/soc/qcom/subsystem_restart.c",
    "blob": "e304cb58b65037237b2a231a52dadb3bccd618c7",
    "get_lines": "1028-1081",
    "put_lines": "1114-1155",
    "char_fops_lines": "1457-1500",
}
FIELDS = {
    "char_open_handler": "subsys_device_open",
    "char_release_handler": "subsys_device_close",
    "char_open_calls": "subsystem_get_with_fwname",
    "char_close_calls": "subsystem_put",
}
YES = {
    "char_open_looks_up_minor", "char_release_looks_up_minor",
    "char_open_returns_negative_invalid_minor", "char_close_returns_negative_invalid_minor",
    "char_open_propagates_ERR_PTR_error", "char_open_has_no_file_private_data_handle_storage",
    "char_close_has_no_file_private_data_handle_retrieval",
    "get_missing_subsystem_returns_ENODEV", "get_module_pin_failure_returns_ENODEV",
    "get_first_reference_calls_subsys_start", "get_success_increments_subsystem_count",
    "get_start_failure_bypasses_count_increment",
    "get_start_failure_unwinds_dependency_and_module_device_refs",
    "put_zero_reference_warnings_and_skips_decrement",
    "put_final_reference_calls_subsys_stop",
    "put_final_reference_frees_subsystem_memory",
}
NO = {
    "put_nonfinal_reference_stops_modem", "release_always_stops_modem",
    "failed_open_proven_to_receive_release", "char_open_guarantees_item134_readiness",
    "PM_service_runtime_open_observed", "modem_recovery_runtime_verified",
}
CAVEATS = {
    "Character open returns zero on non-ERR_PTR result; pinned __subsystem_get returns NULL for a null name, but registered name is expected to be non-null; do not infer NULL-return behavior from an actual device without evidence",
    "Character release performs fresh minor lookup, not an observed per-file saved handle; no concurrency safety proof is claimed",
    "The inspected dependency handling is source-specific and does not establish hardware recovery safety",
    "Callers other than character device can hold subsystem references, so close need not shut down modem",
    "Neither success of open nor refcount changes establish modemsmem item134 publication or firmware acknowledgment",
}
UNKNOWN = {
    "proprietary_pm_service_open_and_close_lifetime",
    "multiple_user_or_kernel_reference_holders",
    "restart_generation_recovery_and_telephony_liveness",
    "actual_runtime_dependencies_and_modemsmem_item134_barrier",
    "installed_kernel_vendor_policy_compatibility",
}
SAFE = {"adb", "device_open", "device_read", "smem_read", "smem_write", "modem_start", "flash"}

def violations(d):
    bad = []
    if (d.get("schema_version"), d.get("step"), d.get("scope")) != (
        1, 813, "pinned_downstream_SSR_character_open_close_and_get_put_control_flow_source_only"
    ):
        bad.append("scope")
    if d.get("source") != PIN:
        bad.append("pin")
    observed = d.get("observed", {})
    if set(observed) != set(FIELDS) | YES | NO:
        bad.append("fields")
    if any(observed.get(k) != v for k, v in FIELDS.items()):
        bad.append("handlers")
    if any(observed.get(k) is not True for k in YES):
        bad.append("lifecycle semantics")
    if any(observed.get(k) is not False for k in NO):
        bad.append("unsupported proof")
    if set(d.get("caveats", [])) != CAVEATS:
        bad.append("caveats")
    if set(d.get("unknowns", [])) != UNKNOWN:
        bad.append("unknowns")
    safety = d.get("safety", {})
    if set(safety) != SAFE or any(v is not False for v in safety.values()):
        bad.append("device access")
    if d.get("hardware_tested") is not False:
        bad.append("hardware proof")
    return bad

class OfflineLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads(P.read_text(encoding="utf-8"))

    def reject(self, key, val, section="observed"):
        altered = copy.deepcopy(self.d)
        altered[section][key] = val
        self.assertTrue(violations(altered))

    def test_baseline(self):
        self.assertEqual(violations(self.d), [])

    def test_open_handler(self):
        self.reject("char_open_handler", "read")

    def test_release_handler(self):
        self.reject("char_release_handler", "write")

    def test_get_call(self):
        self.reject("char_open_calls", "subsystem_put")

    def test_put_call(self):
        self.reject("char_close_calls", "subsystem_get")

    def test_missing_minor(self):
        self.reject("char_open_returns_negative_invalid_minor", False)

    def test_close_missing_minor(self):
        self.reject("char_close_returns_negative_invalid_minor", False)

    def test_open_error(self):
        self.reject("char_open_propagates_ERR_PTR_error", False)

    def test_first_count(self):
        self.reject("get_first_reference_calls_subsys_start", False)

    def test_increment(self):
        self.reject("get_success_increments_subsystem_count", False)

    def test_failure_count(self):
        self.reject("get_start_failure_bypasses_count_increment", False)

    def test_failure_unwind(self):
        self.reject("get_start_failure_unwinds_dependency_and_module_device_refs", False)

    def test_final_stop(self):
        self.reject("put_final_reference_calls_subsys_stop", False)

    def test_nonfinal_stop(self):
        self.reject("put_nonfinal_reference_stops_modem", True)

    def test_release_not_guaranteed_stop(self):
        self.reject("release_always_stops_modem", True)

    def test_no_paired_handle_storage(self):
        self.reject("char_open_has_no_file_private_data_handle_storage", False)

    def test_no_paired_handle_load(self):
        self.reject("char_close_has_no_file_private_data_handle_retrieval", False)

    def test_failed_open_release_unproven(self):
        self.reject("failed_open_proven_to_receive_release", True)

    def test_no_item134_order(self):
        self.reject("char_open_guarantees_item134_readiness", True)

    def test_no_runtime_daemon(self):
        self.reject("PM_service_runtime_open_observed", True)

    def test_no_runtime_recovery(self):
        self.reject("modem_recovery_runtime_verified", True)

    def test_source_pin(self):
        self.reject("blob", "branch-tip", "source")

    def test_missing_caveat(self):
        altered = copy.deepcopy(self.d)
        altered["caveats"].pop()
        self.assertTrue(violations(altered))

    def test_missing_unknown(self):
        altered = copy.deepcopy(self.d)
        altered["unknowns"].pop()
        self.assertTrue(violations(altered))

    def test_no_open(self):
        self.reject("device_open", True, "safety")

    def test_no_flash(self):
        self.reject("flash", True, "safety")

if __name__ == "__main__":
    unittest.main()
