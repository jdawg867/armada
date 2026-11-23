# Step 840 — review-only deferred-probe retry sequence

## Source and compile evidence

The isolated RFC patch is `research/pixel5a-modemsmem/review-only/0001-modemsmem-preserve-smem-deferred-probe.patch`. The exact replacement C block is imported from `tests/pixel5a-modemsmem-full-pinned-source-patch-833-test.py`, which verifies the full original `modemsmem.c` at Git blob `428143562894e6d8ca7b656174c72ee4b096f510` from `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`.

Step 839 baseline: GitHub Actions run [45279631503](https://github.com/jdawg867/armada/actions/runs/45279631503) passed original/modified ARM64 object Kbuild checks with different output hashes and matching defined symbol names. Android source-only CI [45279631519](https://github.com/jdawg867/armada/actions/runs/45279631519) also passed.

## New guard (Step 840)

`tests/pixel5a-modemsmem-probe-retry-840-c-test.py` compiles the **exact Step 833 reviewed C replacement** using a small synthetic host-side SMEM provider and tracks a model driver-core queue. It requires:

- Allocation `-EPROBE_DEFER` to return defer *without* calling `qcom_smem_get`.
- A later, successful allocation/get attempt to return success.
- SMEM pointer acquisition `ERR_PTR(-EPROBE_DEFER)` to return defer, followed by a successful repeat.
- Ordinary allocation/get errors and size mismatch to preserve `-ENOMEM`; existing item `-EEXIST` to remain accepted.
- The stand-in payload's sentinel value to remain unchanged.
- Exactly nine synthetic probe attempts, two deferrals, and no unexpected defer enqueues.

The source-only Android phone validation workflow now executes this compiled host test. Any new CI outcome must be checked before claiming that Step 840 passes.

## Important boundaries

This is a **model** of driver-core retry behavior and fault inputs, not a test of the actual live Linux driver-core queue, SMEM provider timing, Android init, subsystem restart, or phone hardware. Even with the compiled kernel object, source-only evidence cannot establish calls, SMS, mobile-data, first-modem-start readiness, or firmware compatibility.

The historical RFC patch header's line saying "not compiled" described its original Step 832 status; as of Step 839 the isolated ARM64 object **has been compiled successfully in CI**. The patch remains an unmerged review candidate and must not be interpreted as approved for installation, upstream submission, or phone modification.
