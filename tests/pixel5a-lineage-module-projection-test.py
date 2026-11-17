#!/usr/bin/env python3
"""Step 794: synthetic, offline tests for pinned Lineage module-list projection."""
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

SRC=pathlib.Path(__file__).resolve().parents[1]/"research/pixel5a-modemsmem/project_lineage_module_load.py"
spec=importlib.util.spec_from_file_location("project_lineage_module_load",SRC)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def fixture():
    return {
        "board": "BOOT_KERNEL_MODULES := \\\n smem.ko \\\n subsys-pil-tz.ko \\\n modemsmem.ko\\n",
        "lineage": "BOOT_KERNEL_MODULES += \\\n touch_offload.ko\\n",
        "load": "kernel/drivers/soc/qcom/smem.ko\\n"
                "kernel/drivers/soc/qcom/subsys-pil-tz.ko\\n"
                "kernel/drivers/soc/qcom/other.ko\\n"
                "kernel/drivers/soc/qcom/modemsmem/modemsmem.ko\\n"
                "kernel/drivers/input/touch_offload.ko\\n",
        "init": "modprobe -a -d /vendor/lib/modules $arg\\n"
                "setprop vendor.all.modules.ready 1\\n",
        "cfg": "modprobe|-b *\\n",
        "pil": "subsys_register(&d->subsys_desc);\\n"
               "ret = pil_boot(&d->desc);\\n",
    }

class ProjectionTests(unittest.TestCase):
    def test_append_assignment(self):
        self.assertEqual(mod.assignment("BOOT_KERNEL_MODULES += a.ko b.ko\\n",
                                       "BOOT_KERNEL_MODULES"),["a.ko","b.ko"])
    def test_multiline_assignment(self):
        self.assertEqual(mod.assignment(fixture()["board"],"BOOT_KERNEL_MODULES"),
                         list(mod.WATCH))
    def test_source_refs(self):
        self.assertIn(mod.REFS["kernel"],mod.url("pil"))
        self.assertIn(mod.REFS["redbull"],mod.url("load"))
    def test_boot_projection_keeps_load_order(self):
        r=mod.evaluate(fixture())
        self.assertEqual(r["ordered_modules_count"],5)
        self.assertEqual(r["boot_projection_count"],4)
        self.assertEqual(r["vendor_projection_count"],1)
        self.assertTrue(r["pil_appears_before_modemsmem_in_list"])
        self.assertFalse(r["actual_modem_start_order_verified"])
    def test_missing_pil_no_start_order_claim(self):
        a=fixture()
        a["load"]=a["load"].replace(
          "kernel/drivers/soc/qcom/subsys-pil-tz.ko\\n","")
        r=mod.evaluate(a)
        self.assertIn("subsys-pil-tz.ko",r["missing_watched"])
        self.assertFalse(r["pil_appears_before_modemsmem_in_list"])
    def test_opposite_list_order_rejected_as_positive(self):
        a=fixture()
        a["load"]=a["load"].replace(
          "kernel/drivers/soc/qcom/subsys-pil-tz.ko\\n",
          "kernel/drivers/soc/qcom/__tmp__.ko\\n").replace(
          "kernel/drivers/soc/qcom/modemsmem/modemsmem.ko\\n",
          "kernel/drivers/soc/qcom/subsys-pil-tz.ko\\n").replace(
          "kernel/drivers/soc/qcom/__tmp__.ko\\n",
          "kernel/drivers/soc/qcom/modemsmem/modemsmem.ko\\n")
        self.assertFalse(mod.evaluate(a)["pil_appears_before_modemsmem_in_list"])
    def test_duplicate_module_basenames_rejected(self):
        a=fixture()
        a["load"]+="another/directory/smem.ko\\n"
        with self.assertRaises(ValueError):
            mod.evaluate(a)
    def test_loader_ready_not_probe_ack(self):
        r=mod.evaluate(fixture())
        self.assertIs(r["module_loader_checks_modprobe_status"],False)
        self.assertFalse(r["module_probe_completion_verified"])
        self.assertFalse(r["actual_stock_vendor_boot_verified"])
    def test_pil_source_evidence_not_remoteproc(self):
        r=mod.evaluate(fixture())
        self.assertTrue(r["pil_powerup_calls_pil_boot"])
        self.assertTrue(r["pil_probe_registers_subsystem"])
        self.assertFalse(r["pil_probe_requires_modemsmem_publication"])
    def test_no_network_in_offline_evaluation(self):
        with patch.object(mod,"urlopen",side_effect=AssertionError("network")):
            self.assertTrue(mod.evaluate(fixture())["pil_appears_before_modemsmem_in_list"])

if __name__=="__main__":
    unittest.main()
