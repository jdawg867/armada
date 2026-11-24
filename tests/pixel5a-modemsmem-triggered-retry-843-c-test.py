#!/usr/bin/env python3
"""Step 843: synthetic driver-core trigger gate using exact reviewed C source.

A deferred result is retained as pending; only an explicit simulated trigger
re-invokes it. This host model is not the actual Linux deferred-probe subsystem.
"""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests/pixel5a-modemsmem-probe-retry-840-c-test.py"
spec = importlib.util.spec_from_file_location("step840", HARNESS)
step840 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step840)

FOOTER = r"""
    (void)modem_smem;
    return 0;
}
static int errors;
static int calls;
static int queued;
static int complete;
static int last_error;
static int alloc_rc;
static int get_rc;
static int invalid_size;
static void expect(const char *name, int actual, int expected) {
    if (actual != expected) {
        fprintf(stderr, "FAIL %s got=%d want=%d\n", name, actual, expected);
        ++errors;
    }
}
static void reset(void) {
    calls = queued = complete = last_error = 0;
    get_calls = log_calls = 0;
    alloc_rc = get_rc = invalid_size = 0;
}
static void run_probe(void) {
    int rc = probe_once(alloc_rc, get_rc, invalid_size);
    ++calls;
    last_error = rc;
    if (rc == -EPROBE_DEFER) {
        queued = 1;
        complete = 0;
    } else {
        queued = 0;
        complete = (rc == 0);
    }
}
static void provider_trigger(void) {
    if (queued) run_probe();
}
int main(void) {
    reset();
    alloc_rc = -EPROBE_DEFER;
    run_probe();
    expect("alloc initial defer", last_error, -EPROBE_DEFER);
    expect("alloc initial queued", queued, 1);
    expect("alloc initial calls", calls, 1);
    expect("alloc initial no get", get_calls, 0);
    /* Provider becomes ready without notification: NO retry yet. */
    alloc_rc = 0;
    expect("no implicit retry", calls, 1);
    provider_trigger();
    expect("alloc retry success", complete, 1);
    expect("alloc retry count", calls, 2);
    provider_trigger();
    expect("successful probe never retried", calls, 2);

    reset();
    get_rc = -EPROBE_DEFER;
    run_probe();
    expect("get initial defer", last_error, -EPROBE_DEFER);
    expect("get initially queued", queued, 1);
    get_rc = 0;
    provider_trigger();
    expect("get retry success", complete, 1);
    expect("get retry count", calls, 2);

    reset();
    alloc_rc = -ENOMEM;
    run_probe();
    expect("ENOMEM not queued", queued, 0);
    provider_trigger();
    expect("ENOMEM not retried", calls, 1);

    reset();
    get_rc = -EINVAL;
    run_probe();
    expect("get EINVAL still ENOMEM", last_error, -ENOMEM);
    provider_trigger();
    expect("get EINVAL not retried", calls, 1);

    reset();
    invalid_size = 1;
    run_probe();
    expect("size remains ENOMEM", last_error, -ENOMEM);
    provider_trigger();
    expect("size mismatch not retried", calls, 1);

    reset();
    alloc_rc = -EEXIST;
    run_probe();
    expect("existing item accepted", complete, 1);
    provider_trigger();
    expect("existing item not retried", calls, 1);

    expect("no payload writes", payload.version, 0x12345678U);
    if (errors) return 1;
    puts("PASS Step 843 synthetic deferred queue explicit trigger and non-deferred fail-closed cases");
    return 0;
}
"""

class TriggeredRetryModel(unittest.TestCase):
    def test_compiled_reviewed_source_requires_trigger(self):
        block = step840.verifier.REPLACEMENT
        self.assertIn("PTR_ERR(modem_smem) == -EPROBE_DEFER", block)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "trigger.c"
            exe = Path(tmp) / "trigger"
            src.write_text(step840.HEADER + block + FOOTER, encoding="utf-8")
            cmd = ["cc", "-std=c11", "-O1", "-Wall", "-Wextra", "-Werror",
                   "-pedantic", "-fsanitize=undefined", "-fno-omit-frame-pointer",
                   str(src), "-o", str(exe)]
            build = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            self.assertEqual(build.returncode, 0, build.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("PASS Step 843 synthetic deferred queue", run.stdout)

if __name__ == "__main__":
    unittest.main()
