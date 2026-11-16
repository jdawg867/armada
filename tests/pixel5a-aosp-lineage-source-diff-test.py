#!/usr/bin/env python3
"""Step 793: fully offline unified-diff input and missing-evidence tests."""
import importlib.util
import io
import json
import pathlib
import unittest
from unittest.mock import patch

SOURCE=pathlib.Path(__file__).resolve().parents[1]/"research/pixel5a-modemsmem/inspect_aosp_lineage_12l_diffs.py"
spec=importlib.util.spec_from_file_location("pixel5a_diff",SOURCE)
tool=importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

class SourceDiffTests(unittest.TestCase):
    def test_approved_paths(self):
        self.assertEqual(len(tool.DIFFERENT),3)
        self.assertEqual(set(tool.DIFFERENT),{
          ("barbet","barbet/init.barbet.rc"),
          ("redbull","BoardConfig-common.mk"),
          ("redbull","init.hardware.rc")})
    def test_reference_pinned(self):
        self.assertEqual(tool.TAG,"android-12.1.0_r7")
        self.assertIn("refs/tags/android-12.1.0_r7",tool.compare.target_urls(
           "redbull",tool.TAG,"BoardConfig-common.mk")[0])
    def test_reject_firmware(self):
        with self.assertRaises(ValueError):
            tool.make_diff("redbull","vendor_boot.img","x","y")
    def test_identical_lines(self):
        value=tool.make_diff("barbet","barbet/init.barbet.rc","hello\n","hello\n")
        self.assertEqual(value["changed_lines"],0)
        self.assertEqual(value["unified_diff"],"")
    def test_changed_lines(self):
        value=tool.make_diff("redbull","init.hardware.rc","start modem\n","stop modem\n")
        self.assertEqual(value["changed_lines"],2)
        self.assertIn("-start modem",value["unified_diff"])
        self.assertIn("+stop modem",value["unified_diff"])
    def test_keyword_detection(self):
        value=tool.make_diff("redbull","BoardConfig-common.mk",
                "CONFIG_MODEMSMEM=m\n","CONFIG_MODEMSMEM=y\n")
        self.assertEqual(len(value["keyword_changed_lines"]),2)
    def test_unrelated_change_not_proven_modem(self):
        value=tool.make_diff("redbull","BoardConfig-common.mk","A := 1\n","A := 2\n")
        self.assertEqual(value["keyword_changed_lines"],[])
    def test_mock_retrieval(self):
        def fetch(url,aosp=False): return "a\n" if aosp else "b\n"
        value=tool.one("barbet","barbet/init.barbet.rc",fetch=fetch)
        self.assertFalse(value["identical_bytes"])
        self.assertTrue(value["source_only"])
    def test_offline_default(self):
        with patch.object(tool.compare,"urlopen",side_effect=AssertionError("network access")):
            with patch("sys.stdout",new_callable=io.StringIO) as output:
                self.assertEqual(tool.main([]),0)
        self.assertIn("SOURCE_DIFFS_RETRIEVED 0",output.getvalue())
        self.assertIn("SOURCE_DIFFS_COMPLETE False",output.getvalue())
    def test_missing_network_source_not_claimed(self):
        with patch.object(tool,"one",side_effect=ValueError("missing")):
            with patch("sys.stdout",new_callable=io.StringIO) as output:
                tool.main(["--online"])
        self.assertIn("SOURCE_DIFFS_RETRIEVED 0",output.getvalue())
        self.assertIn("SOURCE_DIFFS_COMPLETE False",output.getvalue())

if __name__=="__main__":
    unittest.main()
