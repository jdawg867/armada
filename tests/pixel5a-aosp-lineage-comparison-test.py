#!/usr/bin/env python3
"""Offline tests for Step 792 exact pinned public-text comparison."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from unittest import TestCase,main
from unittest.mock import patch
from urllib.error import HTTPError

PATH=Path(__file__).resolve().parents[1]/"research/pixel5a-modemsmem/compare_aosp_lineage_12l.py"
spec=importlib.util.spec_from_file_location("compare_aosp_lineage_12l",PATH)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ComparisonTests(TestCase):
    def test_expected_ref(self):
        a,b=mod.target_urls("barbet","android-12.1.0_r1","init.insmod.barbet.cfg")
        self.assertIn("/refs/tags/android-12.1.0_r1/",a)
        self.assertIn("24101a383bb1951952adcd6f62668338dd048f03",b)
    def test_reject_unsupported_tag(self):
        with self.assertRaises(ValueError):
            mod.target_urls("barbet","main","init.insmod.barbet.cfg")
    def test_reject_path_traversal(self):
        with self.assertRaises(ValueError):
            mod.target_urls("redbull",mod.TAGS[0],"../../vendor_boot.img")
    def test_equal_text(self):
        r=mod.comparison("a\nb\n","a\nb\n")
        self.assertTrue(r["identical_bytes"])
        self.assertEqual(r["hunks_changed"],0)
    def test_modified_text(self):
        r=mod.comparison("a\nb\n","a\nc\n")
        self.assertFalse(r["identical_bytes"])
        self.assertEqual(r["hunks_changed"],1)
        self.assertEqual(r["aosp_lines_changed"],1)
    def test_exact_sha(self):
        r=mod.comparison("abc","abc")
        self.assertEqual(r["aosp_sha256"],hashlib.sha256(b"abc").hexdigest())
    def test_mock_pair(self):
        def fetch(url,aosp=False):
            return "line one\n" if aosp else "line two\n"
        r=mod.collect_one("redbull",mod.TAGS[1],"init.insmod.sh",fetch=fetch)
        self.assertEqual(r["compare_state"],"compared")
        self.assertFalse(r["identical_bytes"])
        self.assertFalse(r["stock_vendor_boot_verified"])
    def test_one_missing(self):
        def fetch(url,aosp=False):
            if aosp:
                raise HTTPError(url,404,"missing",{},None)
            return "lineage present"
        r=mod.collect_one("barbet",mod.TAGS[0],"barbet/init.barbet.rc",fetch=fetch)
        self.assertEqual(r["compare_state"],"not_compared")
        self.assertNotIn("aosp_sha256",r)
        self.assertEqual(r["aosp_http_status"],404)
    def test_all_results_are_source_only(self):
        def fetch(url,aosp=False):
            return "x"
        r=mod.build_report(fetch=fetch)
        self.assertEqual(len(r["entries"]),15)
        self.assertEqual(r["compared_count"],15)
        self.assertFalse(r["stock_vendor_boot_verified"])
        self.assertFalse(r["effective_modem_boot_order_verified"])
    def test_offline_default(self):
        with patch.object(mod,"urlopen",side_effect=AssertionError("network attempted")):
            with patch("sys.stdout",new_callable=io.StringIO) as out:
                self.assertEqual(mod.main([]),0)
        r=json.loads(out.getvalue())
        self.assertEqual(r["entries"],[])
        self.assertFalse(r["hardware_tested"])
if __name__=="__main__":
    main()
