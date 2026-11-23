#!/usr/bin/env python3
"""Step 840: host-only retry lifecycle of the exact reviewed modemsmem probe block.

A synthetic driver core retries only when the actual patched C block returns
-EPROBE_DEFER. This is NOT a hardware or full Android modem lifecycle test.
"""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/pixel5a-modemsmem-full-pinned-source-patch-833-test.py"
spec = importlib.util.spec_from_file_location("step833_pinned_source", SOURCE)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

HEADER = r"""
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#define EPROBE_DEFER 517
#define EEXIST 17
#define ENOMEM 12
#define EINVAL 22
#define QCOM_SMEM_HOST_ANY (~0U)
#define SMEM_ID_VENDOR0 134
struct modem_smem_type { unsigned version; };
static struct modem_smem_type payload = { 0x12345678U };
static int get_error;
static int bad_size;
static int get_calls;
static int log_calls;
static void *dev;
static void dev_err(void *device, const char *message) {
    (void)device; (void)message; ++log_calls;
}
static struct modem_smem_type *qcom_smem_get(unsigned host,
                                            unsigned item, size_t *size) {
    (void)host; (void)item;
    ++get_calls;
    *size = sizeof(payload) + (bad_size ? 4U : 0U);
    if (get_error) return (struct modem_smem_type *)(intptr_t)get_error;
    return &payload;
}
#define IS_ERR(p) ((uintptr_t)(void *)(p) >= (uintptr_t)-4095)
#define PTR_ERR(p) ((long)(intptr_t)(p))
static int probe_once(int allocation_result, int smem_get_error, int wrong_size) {
    int ret = allocation_result;
    size_t size = 0;
    struct modem_smem_type *modem_smem;
    get_error = smem_get_error;
    bad_size = wrong_size;
"""
FOOTER = r"""
    (void)modem_smem;
    return 0;
}
static int errors;
static void expect(const char *label, int actual, int expected) {
    if (actual != expected) {
        fprintf(stderr, "FAIL %s expected %d got %d\n", label, expected, actual);
        ++errors;
    }
}
static int attempts;
static int queued;
static int driver_attempt(int alloc, int get, int size) {
    int result = probe_once(alloc, get, size);
    ++attempts;
    if (result == -EPROBE_DEFER) ++queued;
    return result;
}
int main(void) {
    /* Allocation defers: do not access the pointer; next attempt succeeds. */
    expect("alloc defer", driver_attempt(-EPROBE_DEFER, 0, 0), -EPROBE_DEFER);
    expect("no get after alloc defer", get_calls, 0);
    expect("alloc defer queued", queued, 1);
    expect("alloc retry", driver_attempt(0, 0, 0), 0);
    expect("one get on retry", get_calls, 1);
    expect("alloc retry no new queue", queued, 1);

    /* Pointer acquisition defers and then succeeds on provider readiness. */
    expect("get defer", driver_attempt(0, -EPROBE_DEFER, 0), -EPROBE_DEFER);
    expect("get defer queued", queued, 2);
    expect("get retry", driver_attempt(0, 0, 0), 0);
    expect("get retry not queued", queued, 2);

    /* Other errors and a bad ABI size must never be treated as deferral. */
    expect("alloc invalid", driver_attempt(-EINVAL, 0, 0), -ENOMEM);
    expect("alloc no get", get_calls, 3);
    expect("get invalid", driver_attempt(0, -EINVAL, 0), -ENOMEM);
    expect("get no-memory", driver_attempt(0, -ENOMEM, 0), -ENOMEM);
    expect("wrong ABI size", driver_attempt(0, 0, 1), -ENOMEM);
    expect("existing item valid", driver_attempt(-EEXIST, 0, 0), 0);
    expect("still only 2 deferred", queued, 2);
    expect("nine attempts", attempts, 9);
    expect("payload unchanged", payload.version, 0x12345678U);
    expect("failure log count", log_calls, 6);
    if (errors) return 1;
    puts("PASS Step 840 nine synthetic probe attempts, two deferrals, two retries, no payload write");
    return 0;
}
"""

class PinnedProbeRetry(unittest.TestCase):
    def test_compiled_reviewed_branch_retries_without_phone_access(self):
        block = verifier.REPLACEMENT
        self.assertIn("if (ret == -EPROBE_DEFER)", block)
        self.assertIn("if (PTR_ERR(modem_smem) == -EPROBE_DEFER)", block)
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "retry.c"
            binary = Path(temp) / "retry"
            source.write_text(HEADER + block + FOOTER, encoding="utf-8")
            command = ["cc", "-std=c11", "-O1", "-Wall", "-Wextra", "-Werror",
                       "-pedantic", "-fsanitize=undefined",
                       "-fno-omit-frame-pointer", str(source), "-o", str(binary)]
            compiled = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            executed = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(executed.returncode, 0, executed.stderr)
            self.assertIn("PASS Step 840 nine synthetic probe attempts", executed.stdout)

if __name__ == "__main__":
    unittest.main()
