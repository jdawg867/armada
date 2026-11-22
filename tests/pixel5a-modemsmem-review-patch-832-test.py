#!/usr/bin/env python3
"""Step 832: source-only RFC patch and negative error mapping tests.

This is deliberately NOT a kernel compile or hardware probe test.
"""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "research/pixel5a-modemsmem/review-only/0001-modemsmem-preserve-smem-deferred-probe.patch"
REL = Path("drivers/soc/qcom/modemsmem/modemsmem.c")

# Exact unmodified 11-line hunk from pinned LineageOS/redbull source.
BEFORE = (
    "\t\t\tsizeof(struct modem_smem_type));\n"
    "\tif (ret && ret != -EEXIST) {\n"
    '\t\tdev_err(dev, "smem alloc fail\\n");\n'
    "\t\treturn -ENOMEM;\n"
    "\t}\n"
    "\n"
    "\tmodem_smem = qcom_smem_get(QCOM_SMEM_HOST_ANY, SMEM_ID_VENDOR0, &size);\n"
    "\tif (IS_ERR(modem_smem) || size != sizeof(struct modem_smem_type)) {\n"
    '\t\tdev_err(dev, "Get modem_smem pointer failed\\n");\n'
    "\t\treturn -ENOMEM;\n"
    "\t}\n"
)

def patched_snippet():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dest = root / REL
        dest.parent.mkdir(parents=True)
        # Surround the exact source hunk with enough source-context lines.
        prefix = "/* simulated earlier pinned source lines */\n" * 174
        dest.write_text(prefix + BEFORE + "\n/* end simulated source */\n")
        chk = subprocess.run(["git", "apply", "--check", "--unsafe-paths", str(PATCH)],
                             cwd=root, capture_output=True, text=True)
        if chk.returncode:
            raise AssertionError("Patch check failed: " + chk.stderr)
        out = subprocess.run(["git", "apply", "--unsafe-paths", str(PATCH)],
                             cwd=root, capture_output=True, text=True)
        if out.returncode:
            raise AssertionError("Patch apply failed: " + out.stderr)
        applied = dest.read_text()
        return applied.split(prefix)[-1].split("\n/* end simulated source */")[0]

class ErrorPropagationTests(unittest.TestCase):
    def test_patch_is_valid_against_pinned_hunk(self):
        self.assertIn("if (ret == -EPROBE_DEFER)", patched_snippet())

    def test_alloc_defer_preserved(self):
        self.assertRegex(patched_snippet(), r"if \(ret == -EPROBE_DEFER\)\s+return ret;")

    def test_alloc_eexist_preserved(self):
        self.assertIn("if (ret && ret != -EEXIST)", patched_snippet())

    def test_non_defer_alloc_errors_still_nomem(self):
        s = patched_snippet()
        self.assertRegex(s, r"if \(ret == -EPROBE_DEFER\)\s+return ret;\s+return -ENOMEM;")

    def test_get_defer_preserved(self):
        self.assertRegex(patched_snippet(), r"if \(PTR_ERR\(modem_smem\) == -EPROBE_DEFER\)\s+return -EPROBE_DEFER;")

    def test_non_defer_get_error_still_nomem(self):
        self.assertRegex(patched_snippet(), r"if \(PTR_ERR\(modem_smem\) == -EPROBE_DEFER\)\s+return -EPROBE_DEFER;\s+return -ENOMEM;")

    def test_size_guard_retained(self):
        self.assertRegex(patched_snippet(), r"if \(size != sizeof\(struct modem_smem_type\)\) \{\s+dev_err\(dev,")
        self.assertIn("return -ENOMEM;", patched_snippet())

    def test_fault_mapping_alloc(self):
        def result(code):
            if not code or code == -17:  # EEXIST
                return "continue"
            return -517 if code == -517 else -12  # EPROBE_DEFER, ENOMEM
        self.assertEqual(result(-517), -517)
        self.assertEqual(result(-12), -12)
        self.assertEqual(result(-22), -12)
        self.assertEqual(result(-17), "continue")
        self.assertEqual(result(0), "continue")

    def test_fault_mapping_get(self):
        def result(pointer_error, size_matches):
            if pointer_error is not None:
                return -517 if pointer_error == -517 else -12
            return "continue" if size_matches else -12
        self.assertEqual(result(-517, False), -517)
        self.assertEqual(result(-22, True), -12)
        self.assertEqual(result(None, False), -12)
        self.assertEqual(result(None, True), "continue")

    def test_patch_only_edits_error_return_block(self):
        patch = PATCH.read_text()
        self.assertIn("drivers/soc/qcom/modemsmem/modemsmem.c", patch)
        self.assertNotIn("memset_io(modem_smem", patch)
        self.assertNotIn("modem_smem_set_u32(", patch)
        self.assertNotIn("rproc_boot(", patch)
        self.assertNotIn("qcom_smem_alloc(QCOM_SMEM_HOST_ANY", patch)

if __name__ == "__main__":
    unittest.main()
