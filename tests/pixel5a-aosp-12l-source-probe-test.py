#!/usr/bin/env python3
"""No-network unit tests for the public AOSP tag source probe."""
import base64
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

SCRIPT=pathlib.Path(__file__).resolve().parents[1]/"research/pixel5a-modemsmem/probe_aosp_12l_sources.py"
spec=importlib.util.spec_from_file_location("probe_aosp_12l_sources",SCRIPT)
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class FakeResponse:
    def __init__(self, content):
        self.content=content
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self.content

class AospSourceTests(unittest.TestCase):
    def test_exact_tag_only(self):
        self.assertEqual(probe.safe_ref("android-12.1.0_r7"),"android-12.1.0_r7")
    def test_reject_unpinned_tag(self):
        with self.assertRaises(ValueError):
            probe.safe_ref("refs/heads/main")
    def test_reject_unreviewed_file(self):
        with self.assertRaises(ValueError):
            probe.source_url("redbull","android-12.1.0_r7","../../boot.img")
    def test_explicit_tag_path(self):
        self.assertEqual(probe.source_url("barbet","android-12.1.0_r7","init.insmod.barbet.cfg"),
            "https://android.googlesource.com/device/google/barbet/+/refs/tags/android-12.1.0_r7/init.insmod.barbet.cfg?format=TEXT")
    def test_base64_text(self):
        self.assertEqual(probe.decode_blob(base64.b64encode(b"modemsmem.ko\n")),
                         "modemsmem.ko\n")
    def test_marker_is_presence_only(self):
        hits=probe.inspect("modemsmem.ko\n")
        self.assertTrue(hits["modemsmem.ko"])
        self.assertFalse(hits["subsys-pil-tz.ko"])
    def test_mock_retrieval_hash(self):
        sample=b"BOOT_KERNEL_MODULES := modemsmem.ko\n"
        with patch.object(probe,"urlopen",return_value=FakeResponse(base64.b64encode(sample))):
            result=probe.fetch_one("redbull","android-12.1.0_r1","BoardConfig-common.mk")
        self.assertEqual(result["state"],"retrieved")
        self.assertEqual(result["lines"],1)
        self.assertTrue(result["markers"]["modemsmem.ko"])
        self.assertFalse(result["stock_vendor_boot_verified"])
    def test_missing_file_not_fabricated(self):
        with patch.object(probe,"urlopen",side_effect=HTTPError("https://example.com",404,"not found",{},None)):
            result=probe.fetch_one("barbet","android-12.1.0_r5","init.insmod.barbet.cfg")
        self.assertEqual(result["state"],"unavailable")
        self.assertEqual(result["http_status"],404)
        self.assertNotIn("sha256",result)
    def test_no_network_default(self):
        with patch.object(probe,"urlopen",side_effect=AssertionError("unexpected network")):
            with patch("sys.stdout",new_callable=io.StringIO) as output:
                self.assertEqual(probe.main([]),0)
        self.assertFalse(json.loads(output.getvalue().split("\nAOSP_TAG_SOURCE_PROBE=")[0])["all_files_retrieved"])
    def test_output_has_no_hardware_claim(self):
        with tempfile.TemporaryDirectory() as td:
            path=pathlib.Path(td)/"probe.json"
            with patch("sys.stdout",new_callable=io.StringIO):
                probe.main(["--output",str(path)])
            result=json.loads(path.read_text())
        self.assertFalse(result["stock_vendor_boot_verified"])
        self.assertFalse(result["hardware_tested"])

if __name__=="__main__":
    unittest.main()
