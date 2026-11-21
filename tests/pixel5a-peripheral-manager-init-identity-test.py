#!/usr/bin/env python3
"""Step 811 pinned init user/group -> DAC and SELinux eligibility, offline only."""
import copy
import json
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "validation/pixel5a-peripheral-manager-init-identity-audit.json"
PINS = {
    "repository": "LineageOS/android_device_google_redbull",
    "commit": "9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770",
    "init_path": "init.hardware.rc",
    "init_blob": "ec3c3edf7e72fb394bde8e9dc669e4a07ced854b",
    "ueventd_path": "ueventd.rc",
    "ueventd_blob": "ee94e699cdacc2fb9e061d66e5281bde81a798a1",
    "file_contexts_path": "sepolicy/vendor/qcom/common/file_contexts",
    "file_contexts_blob": "f53709a48e090c7faa3af51da725688876747955",
    "policy_path": "sepolicy/vendor/qcom/common/peripheral_manager.te",
    "policy_blob": "edafb01e6199964607b294d44287e9fcbfeae79f",
}
FIELDS = {
    "per_mgr_service": "vendor.per_mgr",
    "per_mgr_binary": "/vendor/bin/pm-service",
    "per_mgr_declared_user": "system",
    "per_mgr_declared_group": "system",
    "per_mgr_declared_ioprio": "rt 4",
    "per_proxy_service": "per_proxy",
    "per_proxy_binary": "/vendor/bin/pm-proxy",
    "per_proxy_declared_user": "system",
    "per_proxy_declared_group": "system",
    "per_proxy_starts_on": "init.svc.vendor.per_mgr=running",
    "modem_node": "/dev/subsys_modem",
    "modem_node_mode": "0640",
    "modem_node_owner": "system",
    "modem_node_group": "system",
    "per_mgr_source_domain": "vendor_per_mgr",
    "modem_node_source_type": "modem_ssr_device",
    "per_mgr_selinux_read_rule": "allow vendor_per_mgr modem_ssr_device:chr_file r_file_perms;",
}
YES = {
    "per_proxy_is_disabled",
    "per_mgr_declared_identity_satisfies_source_DAC_read",
    "per_mgr_source_domain_has_read_permission",
    "per_mgr_can_be_inferred_to_have_source_level_open_eligibility",
}
NO = {
    "per_mgr_proprietary_binary_open_proven",
    "per_mgr_runtime_credentials_verified",
    "per_mgr_runtime_selinux_verified",
    "compiled_policy_verified",
    "modem_initial_boot_verified",
    "modemsmem_item134_acknowledgment_verified",
}
UNKNOWN = {
    "effective_installed_init_and_ueventd_configs",
    "effective_runtime_UID_GID_and_supplementary_groups",
    "effective_runtime_SELinux_domain_and_compiled_policy",
    "actual_subsys_modem_node_presence_and_label",
    "proprietary_pm_service_device_open_behavior",
    "first_modem_requester_and_timing",
    "modemsmem_item134_visibility_ack_and_reuse_policy",
    "stock_telephony_and_SSR_recovery",
}
SAFE = {"adb", "device_open", "device_read", "smem_read", "smem_write", "modem_start", "flash"}


def violations(d):
    bad = []
    if (d.get("schema_version"), d.get("step"), d.get("scope")) != (
        1, 811, "pinned_peripheral_manager_init_identity_source_eligibility_not_live_open"
    ):
        bad.append("scope")
    if d.get("sources", {}).get("android") != PINS:
        bad.append("source")
    o = d.get("observed", {})
    if set(o) != set(FIELDS) | YES | NO:
        bad.append("schema")
    if any(o.get(k) != v for k, v in FIELDS.items()):
        bad.append("field")
    if any(o.get(k) is not True for k in YES):
        bad.append("source eligibility")
    if any(o.get(k) is not False for k in NO):
        bad.append("unsupported runtime proof")
    if set(d.get("unknowns", [])) != UNKNOWN:
        bad.append("unknown")
    if set(d.get("safety", {})) != SAFE or any(v is not False for v in d.get("safety", {}).values()):
        bad.append("unsafe")
    if d.get("hardware_tested") is not False:
        bad.append("hardware")
    return bad


class PinnedIdentityTests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads(FILE.read_text())

    def reject(self, key, val, section="observed"):
        d = copy.deepcopy(self.d)
        d[section][key] = val
        self.assertTrue(violations(d))

    def test_baseline(self):
        self.assertEqual(violations(self.d), [])

    def test_service(self):
        self.reject("per_mgr_service", "other")

    def test_binary(self):
        self.reject("per_mgr_binary", "/vendor/bin/unknown")

    def test_declared_uid(self):
        self.reject("per_mgr_declared_user", "radio")

    def test_declared_gid(self):
        self.reject("per_mgr_declared_group", "radio")

    def test_node_mode(self):
        self.reject("modem_node_mode", "0600")

    def test_node_owner(self):
        self.reject("modem_node_owner", "root")

    def test_node_group(self):
        self.reject("modem_node_group", "radio")

    def test_selinux_policy(self):
        self.reject("per_mgr_selinux_read_rule", "allow other other:chr_file read;")

    def test_dac_eligibility(self):
        self.reject("per_mgr_declared_identity_satisfies_source_DAC_read", False)

    def test_selinux_eligibility(self):
        self.reject("per_mgr_source_domain_has_read_permission", False)

    def test_proxy_dependency(self):
        self.reject("per_proxy_starts_on", "init.svc.vendor.per_mgr=stopped")

    def test_proxy_disabled(self):
        self.reject("per_proxy_is_disabled", False)

    def test_no_proprietary_open(self):
        self.reject("per_mgr_proprietary_binary_open_proven", True)

    def test_no_runtime_credentials(self):
        self.reject("per_mgr_runtime_credentials_verified", True)

    def test_no_compiled_policy(self):
        self.reject("compiled_policy_verified", True)

    def test_no_boot_proof(self):
        self.reject("modem_initial_boot_verified", True)

    def test_no_item_ack(self):
        self.reject("modemsmem_item134_acknowledgment_verified", True)

    def test_pinned_blob(self):
        self.reject("android", {"commit": "main"}, "sources")

    def test_unknowns(self):
        d = copy.deepcopy(self.d)
        d["unknowns"].remove("proprietary_pm_service_device_open_behavior")
        self.assertTrue(violations(d))

    def test_no_device_open(self):
        self.reject("device_open", True, "safety")


if __name__ == "__main__":
    unittest.main()
