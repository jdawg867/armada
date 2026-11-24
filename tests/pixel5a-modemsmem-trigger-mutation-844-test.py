#!/usr/bin/env python3
"""Step 844: prove the Step 843 synthetic retry-queue guard rejects scheduling bugs.

Compile the exact reviewed error block unchanged and vary only the temporary
driver-core model. No module, device, phone, or runtime driver-core access.
"""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests/pixel5a-modemsmem-triggered-retry-843-c-test.py"
spec = importlib.util.spec_from_file_location("step843_trigger_model", HARNESS)
step843 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step843)

MUTATIONS = {
    "trigger_retries_every_device": (
        "    if (queued) run_probe();",
        "    run_probe();",
    ),
    "trigger_ignores_pending_device": (
        "    if (queued) run_probe();",
        "    if (queued && 0) run_probe();",
    ),
    "lose_deferred_queue_entry": (
        "        queued = 1;\n        complete = 0;",
        "        queued = 0;\n        complete = 0;",
    ),
    "keep_queue_after_non_deferred_result": (
        "        queued = 0;\n        complete = (rc == 0);",
        "        queued = 1;\n        complete = (rc == 0);",
    ),
}

class TriggerMutationControls(unittest.TestCase):
    @staticmethod
    def compile_and_execute(footer, location, name):
        c = location / (name + ".c")
        binary = location / name
        c.write_text(step843.step840.HEADER +
                     step843.step840.verifier.REPLACEMENT + footer,
                     encoding="utf-8")
        build = subprocess.run(
            ["cc", "-std=c11", "-O1", "-Wall", "-Wextra", "-Werror",
             "-pedantic", "-fsanitize=undefined", "-fno-omit-frame-pointer",
             str(c), "-o", str(binary)],
            capture_output=True, text=True, timeout=30)
        if build.returncode:
            return "compile_failure", build.stderr
        executed = subprocess.run([str(binary)], capture_output=True,
                                  text=True, timeout=30)
        return ("pass" if executed.returncode == 0 else "assertion_failure",
                executed.stdout + executed.stderr)

    def test_original_and_four_scheduling_mutations(self):
        original = step843.FOOTER
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status, details = self.compile_and_execute(original, root, "original")
            self.assertEqual(status, "pass", details)
            self.assertIn("PASS Step 843 synthetic deferred queue", details)
            for name, (old, new) in MUTATIONS.items():
                with self.subTest(mutation=name):
                    self.assertEqual(original.count(old), 1, name)
                    mutated = original.replace(old, new, 1)
                    self.assertNotEqual(mutated, original)
                    status, details = self.compile_and_execute(mutated, root, name)
                    self.assertEqual(
                        status, "assertion_failure",
                        "Expected compile success followed by detected scheduling "
                        "regression for " + name + "\n" + details)
                    self.assertIn("FAIL ", details)

if __name__ == "__main__":
    unittest.main()
