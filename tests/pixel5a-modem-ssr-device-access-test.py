#!/usr/bin/env python3
"""Step 810: pinned ueventd DAC / SELinux source evidence; no device access."""
import copy
import json
import unittest
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "validation/pixel5a-modem-ssr-device-access-audit.json"

TRUE = {
    "ueventd_entry_covers_modem_node",
    "selinux_policy_grants_device_read_permission",
    "mode_and_selinux_both_must_allow_an_open",
}
FALSE = {
    "ueventd_grants_world_access",
    "proprietary_pm_service_effective_uid_gid_verified",
    "compiled_runtime_sepolicy_verified",
    "actual_device_node_mode_verified",
    "pm_service_open_observed",
    "first_modem_start_observed",
    "modemsmem_item134_readiness_verified",
}
UNKNOWN = {
    "effective_pm_service_UID_GID_and_supplemental_groups",
    "loaded_SELinux_policy_and_domain_at_runtime",
    "actual_subsys_modem_device_node_and_label",
    "which_userspace_process_first_opens_subsys_modem",
    "other_source_or_proprietary_modem_first_start_requesters",
    "modemsmem_probe_and_item134_publication_vs_first_start",
    "first_boot_modem_recovery_and_phone_telephony",
}
FIELDS = {
    "ueventd_pattern": "/dev/subsys_*",
    "ueventd_mode": "0640",
    "ueventd_owner": "system",
    "ueventd_group": "system",
    "ueventd_vendor_copy_destination": "$(TARGET_COPY_OUT_VENDOR)/etc/ueventd.rc",
    "modem_node": "/dev/subsys_modem",
    "modem_selinux_type": "modem_ssr_device",
    "peripheral_manager_domain": "vendor_per_mgr",
    "selinux_permission": "allow vendor_per_mgr modem_ssr_device:chr_file r_file_perms;",
}
PINS = {
    "repository": "LineageOS/android_device_google_redbull",
    "commit": "9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770",
    "ueventd_path": "ueventd.rc",
    "ueventd_blob": "ee94e699cdacc2fb9e061d66e5281bde81a798a1",
    "device_common_path": "device-common.mk",
    "device_common_blob": "200ab69ad13b09aef47b1350fb40b1ee7c9dd2d8",
    "file_contexts_path": "sepolicy/vendor/qcom/common/file_contexts",
    "file_contexts_blob": "f53709a48e090c7faa3af51da725688876747955",
    "peripheral_manager_policy_path": "sepolicy/vendor/qcom/common/peripheral_manager.te",
    "peripheral_manager_policy_blob": "edafb01e6199964607b294d44287e9fcbfeae79f",
}
SAFETY = {"device_open", "device_read", "modem_start", "smem_read", "smem_write", "adb", "flash"}


def violations(d):
    bad = []
    if (d.get("schema_version"), d.get("step"), d.get("scope")) != (
        1, 810, "pinned_redbull_ueventd_DAC_and_SELinux_source_access_not_runtime_open"
    ):
        bad.append("scope")
    if d.get("sources", {}).get("android") != PINS:
        bad.append("source pin")
    o = d.get("observed", {})
    if set(o) != set(FIELDS) | TRUE | FALSE:
        bad.append("observed schema")
    if any(o.get(k) != v for k, v in FIELDS.items()):
        bad.append("DAC or SELinux field")
    if any(o.get(k) is not True for k in TRUE):
        bad.append("missing established boundary")
    if any(o.get(k) is not False for k in FALSE):
        bad.append("unsupported access/runtime promotion")
    if set(d.get("unknowns", [])) != UNKNOWN:
        bad.append("unknowns")
    safety = d.get("safety", {})
    if set(safety) != SAFETY or any(v is not False for v in safety.values()):
        bad.append("active device operation")
    if d.get("hardware_tested") is not False:
        bad.append("hardware claim")
    return bad


class Step810Tests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads(P.read_text(encoding="utf-8"))

    def reject(self, section, key, value):
        d = copy.deepcopy(self.d)
        d[section][key] = value
        self.assertTrue(violations(d))

    def test_baseline(self):
        self.assertEqual(violations(self.d), [])

    def test_ueventd_mode(self):
        self.reject("observed", "ueventd_mode", "0666")

    def test_ueventd_pattern(self):
        self.reject("observed", "ueventd_pattern", "/dev/subsys_other")

    def test_owner(self):
        self.reject("observed", "ueventd_owner", "radio")

    def test_group(self):
        self.reject("observed", "ueventd_group", "radio")

    def test_no_world_access(self):
        self.reject("observed", "ueventd_grants_world_access", True)

    def test_vendor_copy_path(self):
        self.reject("observed", "ueventd_vendor_copy_destination", "/system/etc/ueventd.rc")

    def test_selinux_type(self):
        self.reject("observed", "modem_selinux_type", "other_device")

    def test_selinux_policy(self):
        self.reject("observed", "selinux_permission", "allow vendor_per_mgr modem_ssr_device:chr_file write;")

    def test_dac_and_mac_both_required(self):
        self.reject("observed", "mode_and_selinux_both_must_allow_an_open", False)

    def test_no_proprietary_service_identity(self):
        self.reject("observed", "proprietary_pm_service_effective_uid_gid_verified", True)

    def test_no_live_node_verification(self):
        self.reject("observed", "actual_device_node_mode_verified", True)

    def test_no_service_open(self):
        self.reject("observed", "pm_service_open_observed", True)

    def test_no_firmware_start(self):
        self.reject("observed", "first_modem_start_observed", True)

    def test_no_item134_acknowledgment(self):
        self.reject("observed", "modemsmem_item134_readiness_verified", True)

    def test_pin_immutable(self):
        self.reject("sources", "android", {"commit": "main"})

    def test_unknowns_preserved(self):
        d = copy.deepcopy(self.d)
        d["unknowns"].remove("effective_pm_service_UID_GID_and_supplemental_groups")
        self.assertTrue(violations(d))

    def test_no_unsafe_open(self):
        self.reject("safety", "device_open", True)


if __name__ == "__main__":
    unittest.main()
