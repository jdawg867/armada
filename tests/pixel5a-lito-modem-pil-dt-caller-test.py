#!/usr/bin/env python3
"""Step 796 source contract for Lito modem PIL node and conditional caller."""
import json
import unittest
from pathlib import Path
PATH=Path(__file__).resolve().parents[1]/"validation/pixel5a-lito-modem-pil-dt-caller-audit.json"
GAPS={
"final_barbet_flattened_dtb_modem_properties","actual_adsp_loader_device_node_proc_img_value",
"whether_any_other_modem_start_callers_exist","whether_subsystem_get_modem_executes_before_modemsmem_probe",
"whether_existing_vendor_smem_item134_is_published_before_pil_boot",
"whether_optional_pon_depends_on_is_added_in_overlays",
"exact_stock_android12l_vendor_boot_or_runtime_logs",
"crash_recovery_write_ownership_and_visibility","calls_sms_mobile_data_hardware_functionality"}
def audit(d):
    issues=[]
    s=d.get("source",{})
    if (d.get("step"),d.get("scope"),s.get("commit"),s.get("lito_blob"),
        s.get("adsp_loader_blob"))!=(796,
        "pinned_downstream_lito_pil_dt_and_adsp_caller_source_only",
        "929e7e2f3658867d51a1d423c7e000f5cf1d4043",
        "24b013a4b166456be0a1f8a4a278d9fb3dcfccd1",
        "a32acfd359092d4a8cdbcb2da804d0ec8601da0b"):
        issues.append("incorrect source pin")
    node=d.get("modem_node",{})
    if (node.get("compatible"),node.get("firmware_name"),node.get("pas_id"),
        node.get("smem_id"),node.get("smem_id_usage"))!=(
        "qcom,pil-tz-generic","modem",4,421,"crash_reason_not_item134"):
        issues.append("incorrect modem node interpretation")
    for key in ("pon_depends_on_present_in_inspected_node",
                "modemsmem_provisioning_dependency_present_in_inspected_node"):
        if node.get(key) is not False: issues.append("unproven DT dependency")
    caller=d.get("caller",{})
    if (caller.get("call"),caller.get("image_property"),caller.get("required_state"))!=(
            'subsystem_get("modem")',"qcom,proc-img-to-load","APR_SUBSYS_DOWN"):
        issues.append("caller route misrepresented")
    if caller.get("call_unconditionally_executed_on_barbet") is not False:
        issues.append("unverified conditional execution")
    if d.get("inheritance",{}).get("final_flattened_dt_verified") is not False:
        issues.append("unsupported final DT evidence")
    if set(d.get("not_established",[]))!=GAPS:
        issues.append("missing start-order limitation")
    if d.get("hardware_tested") is not False or any(v is not False for v in d.get("safety",{}).values()):
        issues.append("device action or testing incorrectly authorized")
    return issues
class PinTests(unittest.TestCase):
    def setUp(self): self.d=json.loads(PATH.read_text())
    def test_baseline(self): self.assertEqual(audit(self.d),[])
    def test_wrong_smem_id(self):
        self.d["modem_node"]["smem_id"]=134
        self.assertTrue(audit(self.d))
    def test_wrong_pil_firmware(self):
        self.d["modem_node"]["firmware_name"]="adsp"
        self.assertTrue(audit(self.d))
    def test_unproven_dependency(self):
        self.d["modem_node"]["pon_depends_on_present_in_inspected_node"]=True
        self.assertTrue(audit(self.d))
    def test_caller_not_unconditional(self):
        self.d["caller"]["call_unconditionally_executed_on_barbet"]=True
        self.assertTrue(audit(self.d))
    def test_dtb_not_verified(self):
        self.d["inheritance"]["final_flattened_dt_verified"]=True
        self.assertTrue(audit(self.d))
    def test_no_runtime_start_order(self):
        self.d["not_established"].remove("whether_subsystem_get_modem_executes_before_modemsmem_probe")
        self.assertTrue(audit(self.d))
    def test_no_firmware_boot(self):
        self.d["safety"]["allow_pil_boot"]=True
        self.assertTrue(audit(self.d))
if __name__=="__main__":
    unittest.main()
