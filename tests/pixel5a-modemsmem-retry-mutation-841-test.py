#!/usr/bin/env python3
"""Step 841: negative mutation controls for the exact Step 840 C retry harness.

Host-only: no Android, kernel module, modem, or device access. Mutants are
created in temporary files and MUST fail the real Step 840 assertions.
"""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests/pixel5a-modemsmem-probe-retry-840-c-test.py"
spec = importlib.util.spec_from_file_location("step840_probe_retry", HARNESS)
step840 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step840)

MUTATIONS = {
    "drop_allocation_defer": (
        "if (ret == -EPROBE_DEFER)",
        "if (ret == -EPROBE_DEFER && 0)",
    ),
    "drop_get_defer": (
        "if (PTR_ERR(modem_smem) == -EPROBE_DEFER)",
        "if (PTR_ERR(modem_smem) == -EPROBE_DEFER && 0)",
    ),
    "reject_existing_item": (
        "if (ret && ret != -EEXIST)",
        "if (ret)",
    ),
    "accept_wrong_size": (
        "if (size != sizeof(struct modem_smem_type))",
        "if (size != sizeof(struct modem_smem_type) && 0)",
    ),
    "get_called_during_allocation_defer": (
        "\t\t\treturn ret;",
        "\t\t\t(void)qcom_smem_get(QCOM_SMEM_HOST_ANY, SMEM_ID_VENDOR0, &size);\n\t\t\treturn ret;",
    ),
    "suppress_get_memory_error": (
        "if (IS_ERR(modem_smem)) {",
        "if (IS_ERR(modem_smem) && PTR_ERR(modem_smem) == -EPROBE_DEFER) {",
    ),
}

class DeferredProbeMutationControls(unittest.TestCase):
    @staticmethod
    def compile_and_execute(block, directory, stem):
        src = directory / (stem + ".c")
        exe = directory / stem
        src.write_text(step840.HEADER + block + step840.FOOTER, encoding="utf-8")
        cc = subprocess.run(
            ["cc", "-std=c11", "-O1", "-Wall", "-Wextra", "-Werror",
             "-pedantic", "-fsanitize=undefined", "-fno-omit-frame-pointer",
             str(src), "-o", str(exe)],
            capture_output=True, text=True, timeout=30,
        )
        if cc.returncode:
            return "compile_failure", cc.stderr
        run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
        return ("pass" if run.returncode == 0 else "assertion_failure",
                run.stdout + run.stderr)

    def test_reference_passes_and_every_mutant_is_detected(self):
        reviewed = step840.verifier.REPLACEMENT
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result, output = self.compile_and_execute(reviewed, root, "reference")
            self.assertEqual(result, "pass", output)
            self.assertIn("PASS Step 840 nine synthetic probe attempts", output)
            for label, (old, new) in MUTATIONS.items():
                with self.subTest(mutant=label):
                    self.assertEqual(reviewed.count(old), 1, "ambiguous mutation anchor")
                    mutated = reviewed.replace(old, new, 1)
                    self.assertNotEqual(mutated, reviewed)
                    status, output = self.compile_and_execute(mutated, root, label)
                    self.assertEqual(
                        status, "assertion_failure",
                        "Mutant must compile but be rejected by the real Step 840 "
                        "runtime assertions: " + label + "\n" + output,
                    )
                    self.assertIn("FAIL ", output)

if __name__ == "__main__":
    unittest.main()
