#!/usr/bin/env python3
"""Step 808: explicit Android init events do not prove modem SMEM readiness."""
import json
import unittest
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "validation/pixel5a-android-init-modem-start-event-graph.json"
EXPECTED_EDGES = {
    ("init_normal","module_loader","explicit_start_if_vendor_skip_init_zero"),
    ("module_loader","module_ready_properties","unconditional_setprop_at_script_end_not_probe_ack"),
    ("boot","init_modem_sh","explicit_start"),
    ("esim_done","per_mgr","explicit_start"),
    ("esim_noneed","per_mgr","explicit_start"),
    ("boot_completed","per_mgr","explicit_start"),
    ("per_mgr_running","per_proxy","explicit_start"),
}
UNKNOWN = {
    "proprietary_pm_service_kernel_start_interface",
    "init_runtime_event_order_and_actual_properties",
    "modemsmem_probe_completion_before_per_mgr",
    "actual_vendor_item134_payload_visibility",
    "MPSS_first_boot_request_and_consumer_acknowledgment",
    "safe_item134_ownership_and_reuse_on_restarts",
    "final_Barbet_vendor_boot_and_device_tree",
    "live_calls_SMS_mobile_data",
}
TRUE = {"per_mgr_comment_intended_modem_boot","per_mgr_ssr_device_read_allowed","per_mgr_ssr_sysfs_read_allowed","rild_can_find_per_mgr_service"}
FALSE = {"ready_props_prove_modemsmem_probe_complete","init_has_explicit_wait_for_modemsmem_before_per_mgr",
         "per_mgr_binary_call_graph_inspected","per_mgr_running_event_proves_modem_pil_start",
         "boot_completed_fallback_requires_esim_done","modemsmem_completion_to_first_start_edge_proven"}
PROVENANCE = {
    "init.hardware.rc":"ec3c3edf7e72fb394bde8e9dc669e4a07ced854b",
    "init.insmod.sh":"a222838cc855392838a69fbd9ea3951273078658",
    "sepolicy/vendor/qcom/common/peripheral_manager.te":"edafb01e6199964607b294d44287e9fcbfeae79f",
    "sepolicy/vendor/qcom/common/rild.te":"5bc8795a5172fa4d05556fb5a4368f141f24937f",
}
UNVERIFIED_NODES = {"modemsmem_probe_completed","item134_payload_published","modem_pil_first_start"}


def check(d):
    issues=[]
    a=d.get("android",{})
    if (d.get("schema_version"),d.get("step"),d.get("kind"),a.get("commit")) != (
        1,808,"pinned_android_init_event_dependency_graph_source_only",
        "9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770"):
        issues.append("identity")
    files=a.get("files",[])
    if {x.get("path"):x.get("blob") for x in files} != PROVENANCE or len(files)!=len(PROVENANCE):
        issues.append("blobs")
    nodes=d.get("events",[])
    node_ids={x.get("id") for x in nodes}
    if len(node_ids)!=len(nodes) or not UNVERIFIED_NODES.issubset(node_ids) or any(
        x.get("kind")!="unverified_external_event" for x in nodes if x.get("id") in UNVERIFIED_NODES):
        issues.append("unknown nodes")
    edges=d.get("edges",[])
    pairs={(x.get("from"),x.get("to"),x.get("type")) for x in edges}
    if pairs!=EXPECTED_EDGES or len(edges)!=len(EXPECTED_EDGES) or any(
        x.get("from") not in node_ids or x.get("to") not in node_ids for x in edges):
        issues.append("unsupported graph edge")
    o=d.get("observed",{})
    if (o.get("per_mgr_binary"),o.get("per_proxy_binary"))!=(
        "/vendor/bin/pm-service","/vendor/bin/pm-proxy"):
        issues.append("service identity")
    if set(o)!=(TRUE|FALSE|{"per_mgr_binary","per_proxy_binary"}) or any(
        o.get(k) is not True for k in TRUE) or any(o.get(k) is not False for k in FALSE):
        issues.append("runtime conclusions")
    if set(d.get("unverified",[]))!=UNKNOWN:
        issues.append("omitted unknowns")
    p=d.get("safety",{})
    if set(p)!={"device_access","smem_read","smem_write","modem_start","flash"} or any(
        v is not False for v in p.values()) or d.get("hardware_tested") is not False:
        issues.append("hardware claim")
    return issues


class EventGraphTest(unittest.TestCase):
    def setUp(self): self.d=json.loads(P.read_text())
    def test_baseline(self): self.assertEqual(check(self.d),[])
    def test_esim_done_trigger(self):
        self.d["edges"]=[e for e in self.d["edges"] if e["from"]!="esim_done"]
        self.assertTrue(check(self.d))
    def test_esim_noneed_trigger(self):
        self.d["edges"]=[e for e in self.d["edges"] if e["from"]!="esim_noneed"]
        self.assertTrue(check(self.d))
    def test_boot_fallback(self):
        self.d["edges"]=[e for e in self.d["edges"] if e["from"]!="boot_completed"]
        self.assertTrue(check(self.d))
    def test_no_direct_modem_start_from_manager(self):
        self.d["edges"].append({"from":"per_mgr","to":"modem_pil_first_start","type":"explicit_start"})
        self.assertTrue(check(self.d))
    def test_no_modemsmem_barrier_from_properties(self):
        self.d["edges"].append({"from":"module_ready_properties","to":"item134_payload_published","type":"explicit_start"})
        self.assertTrue(check(self.d))
    def test_unknown_modem_start_remains_unknown(self):
        next(n for n in self.d["events"] if n["id"]=="modem_pil_first_start")["kind"]="service"
        self.assertTrue(check(self.d))
    def test_unverified_probe_before_manager(self):
        self.d["observed"]["init_has_explicit_wait_for_modemsmem_before_per_mgr"]=True
        self.assertTrue(check(self.d))
    def test_boot_completed_not_esim_gate(self):
        self.d["observed"]["boot_completed_fallback_requires_esim_done"]=True
        self.assertTrue(check(self.d))
    def test_ready_properties_not_probe_complete(self):
        self.d["observed"]["ready_props_prove_modemsmem_probe_complete"]=True
        self.assertTrue(check(self.d))
    def test_proprietary_binary_unknown(self):
        self.d["observed"]["per_mgr_binary_call_graph_inspected"]=True
        self.assertTrue(check(self.d))
    def test_module_script_provenance(self):
        next(x for x in self.d["android"]["files"] if x["path"]=="init.insmod.sh")["blob"]="unverified"
        self.assertTrue(check(self.d))
    def test_recovery_ownership_unknown(self):
        self.d["unverified"].remove("safe_item134_ownership_and_reuse_on_restarts")
        self.assertTrue(check(self.d))
    def test_no_smem_write(self):
        self.d["safety"]["smem_write"]=True
        self.assertTrue(check(self.d))
    def test_no_hardware_claim(self):
        self.d["hardware_tested"]=True
        self.assertTrue(check(self.d))

if __name__=="__main__":
    unittest.main()
