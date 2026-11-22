# Step 833 — Full pinned Redbull modemsmem patch verification

**Status:** isolated internal draft review only; not merged, submitted upstream, or deployed.

- Armada integration: `feature/pixel5a-phone-function-gates`, draft PR #18 (unchanged by review-only commits).
- Candidate: `review/kernel-modemsmem-probe-defer-832`, draft PR #19.
- Pinned source: `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `drivers/soc/qcom/modemsmem/modemsmem.c` Git blob `428143562894e6d8ca7b656174c72ee4b096f510`.
- Step 832 CI check at audit commit `05696d283526a4a418e310e2f32992bf2e322502`: no pull-request-triggered runs returned. This does **not** prove a failed test. Root cause identified in branch workflow: `pull_request.branches: [development]` did not include PR #19's `feature/pixel5a-phone-function-gates` base.
- The review branch's Android phone validation workflow now also listens for `push` exclusively to `review/kernel-modemsmem-probe-defer-832`. This avoids changing the integration branch's CI trigger policy. The workflow status lookup available in this integration filters for PR-triggered runs and may not list push runs. **Do not claim CI passed without inspecting a completed run.**

## Verification design

`tests/pixel5a-modemsmem-full-pinned-source-patch-833-test.py` accepts an already-downloaded source file via `--source-file`. It checks the exact Git blob SHA-1 (Git blob header plus file bytes); rejects symlinks, incomplete and changed source; requires the original error-handling hunk exactly once; uses `git apply --check` and `git apply` on a temporary directory; and compares the entire resulting file with the original file plus the expected reviewed error-path replacement. A patch that changes any unrelated line fails. CI retrieves the immutable public source text over HTTPS and passes the file to this host-only verifier.

`tests/pixel5a-modemsmem-full-pinned-source-833-negative-test.py` checks the input pin, malformed-source and symlink failure, the review-only patch scope, and blob-hash implementation. `tests/pixel5a-modemsmem-review-patch-832-test.py` retains synthetic fault-case checks for `-EPROBE_DEFER`, `-EEXIST`, other allocation/get errors and structure-size mismatch.

**Security and lifecycle boundary:** This verification never touches a phone, loads a kernel module, performs SMEM reads/writes, boots a modem, flashes a device, or provides live telephony proof. Source match + clean patch application is **not** compilation against the full Redbull build and cannot verify kernel ABI or normal Pixel 5a calls/SMS/mobile data.

**Step 834:** inspect completed review-branch CI (including push events); fix any failures; then, if appropriate, add an isolated pinned-kernel compile/test without modifying the daily-use Pixel 5a. Upstream submission and merges remain prohibited until the primary Armada OS phone integration is complete and user expressly approves batch review.
