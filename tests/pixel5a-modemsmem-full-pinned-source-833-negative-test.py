#!/usr/bin/env python3
"""Step 833 fail-closed negative tests for the complete pinned kernel file verifier."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tests/pixel5a-modemsmem-full-pinned-source-patch-833-test.py"
spec=importlib.util.spec_from_file_location("armada_full_file_833", SOURCE)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class FullSourceFailClosed(unittest.TestCase):
    def test_git_blob_identity(self):
        self.assertEqual(module.git_blob(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

    def test_wrong_content_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"modemsmem.c"
            path.write_text(module.ORIGINAL)
            with self.assertRaisesRegex(AssertionError, "blob mismatch"):
                module.check(path)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"target.c"
            target.write_text(module.ORIGINAL)
            link=Path(temp)/"linked.c"
            link.symlink_to(target)
            with self.assertRaisesRegex(AssertionError, "real file"):
                module.check(link)

    def test_patch_scope_writes_only_error_region(self):
        self.assertIn("if (size != sizeof(struct modem_smem_type))", module.REPLACEMENT)
        self.assertIn("if (ret && ret != -EEXIST)", module.REPLACEMENT)
        self.assertEqual(module.REPLACEMENT.count("return -ENOMEM;"), 3)
        self.assertNotIn("memset_io(", module.REPLACEMENT)
        self.assertNotIn("module_init(", module.REPLACEMENT)

    def test_full_source_pin_constant(self):
        self.assertEqual(module.EXPECTED_BLOB, "428143562894e6d8ca7b656174c72ee4b096f510")

if __name__=="__main__":
    unittest.main()
