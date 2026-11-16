# Step 774 — Pixel 5a telephony prerequisites (pinned-source evidence)

> **Source-only.** This is not a modem boot test, a telephony stack, or permission to flash/activate firmware. The Pixel 5a must remain a daily-driver phone. Calls, SMS/MMS, cellular data and recovery are mandatory release criteria in `validation/pixel5a-phone-capabilities.json`.

## Exact source checked

Private preserved integration patch: `jdawg867/linux-sm7250-armada-integration`, branch `feature/sm7250-source-snapshot`, path `patches/sm7250-linux-7.2.6-integration.patch`, Git blob `8c32955827e9bd17873b5660db4cfa0037e9585c`. This is a patch based on Linux 7.2.6 `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`, **not** a complete compiled kernel tree.

The preserved patch contains reserved-memory entries:

| Label | Start | Size | End (exclusive) | Observation |
| --- | --- | --- | --- | --- |
| `smem_mem` | `0x80900000` | `0x00200000` | `0x80b00000` | `compatible = "qcom,smem"`; `hwlocks = <&tcsr_mutex 3>`; `no-map` |
| `ipa_fw_mem` | `0x8bc00000` | `0x00010000` | `0x8bc10000` | IPA firmware carveout, `no-map` |
| `ipa_gsi_mem` | `0x8bc10000` | `0x00005400` | `0x8bc15400` | GSI carveout, `no-map` |
| `modem_wlan_mem` | `0x8c000000` | `0x0f800000` | `0x9b800000` | Shared named modem/WLAN carveout, `no-map` |

The rows above are transcribed from patch added lines near 916–977 and recorded in `validation/pixel5a-modem-reserved-memory.json` for source-only arithmetic checks. A region label does **not** establish actual firmware loading, modem access, correct mapping, or modem/WLAN ownership.

## Separate telephony dependency gates — still unresolved

1. **Modem boot/lifetime:** reconcile actual Pixel 5a vendor modem remoteproc/PAS/firmware and the Linux base's supported matching, clocks, interrupts, resets, memory and secure-world dependencies; no invented DT compatible.
2. **Cross-processor transport:** validate IPCC IRQ and mailbox/client signals, SMEM/SMP2P directions and IDs, GLINK/QRTR handoff; previous downstream review reported MPSS SMEM indices `435` and `428`, and IPCC SPI `229` versus a different SM6350 reference value. These observations have **not** been revalidated in this step from the vendor source.
3. **Mobile data:** reconcile IPA 4.7 / GSI, IOMMU domains, AP/WLAN/UC SIDs `0x520`, `0x521`, `0x522` from earlier source audit; SMMU/ICC dependencies remain inactive/unverified.
4. **Userspace phone functions:** identify verified Linux userspace modem-control protocol, carrier IMS/VoLTE capability, voice audio routing, SIM/eSIM provisioning and SMS/MMS/data interfaces. Hardware resource definitions do not establish that these interfaces work.
5. **Preservation:** no repartitioning, vendor/modem firmware overwrite, experimental flashing, or modifications to a known-working Android installation. Before user-approved on-device work, validate a restoration procedure and read-only device inventory.

## Acceptance and next proof

- Source gate: nonoverlap and bounded 64-bit arithmetic for *these four recorded carveouts*, with negative tests. This is only a transcription-consistency check.
- Pending evidence: exact pinned vendor file/commit containing modem DT nodes and IPC endpoints; compatible/binding review; remoteproc and IPA compile and controlled runtime logs.
- Device gate (not authorized here): outgoing/incoming calls including VoLTE as required by carrier, SMS/MMS, LTE data, suspend/recover, and return-to-Android validation. Never place an actual emergency call as an automated test.

Keep generic RPMh fixes on the isolated research branch; do not merge them into the Armada phone port.

## Step 775 — Google Pixel modemsmem prerequisite (external RFC, not integrated)

A public Linux mailing-list **RFC**, dated September 6, 2026 (message ID `20260906-modemsmem-v1-2-a3634b553841@ixit.cz`), proposes a `google,modemsmem` driver: https://lists.openwall.net/linux-kernel/2026/09/06/26 . The authors say that Google Pixel 3 through Pixel 5a devices require extra SoC platform information in a vendor-defined SMEM item before modem startup. The proposed implementation calls `qcom_smem_alloc` and `qcom_smem_get`, reads platform data from `SMEM_HW_SW_BUILD_ID`, and uses `CONFIG_QCOM_MODEMSMEM` with dependencies on `OF` and `QCOM_SMEM`.

**This is an external proposed patch, not the pinned Linux 7.2.6 kernel and not direct Pixel 5a runtime evidence.** The RFC itself notes that `modem_flag` initialization remains unresolved. Its eventual upstream acceptance, compile compatibility with the pinned base, and exact Pixel 5a vendor-DT `qcom,smem-id` binding require separate confirmation. Do not copy or enable this driver without evaluating its SMEM semantics and boot ordering, and do not infer that the modem works because generic SMEM nodes exist.

The machine-readable `validation/pixel5a-modem-dependencies.json` and test `tests/pixel5a-modem-dependencies-test.py` keep `modemsmem` explicitly `rfc_only` and treat every dependency as blocking. They also prevent an unsubstantiated `modem_ready` claim while this stage is source research. The test exercises metadata, **not** live transport or modem behavior.

**Next concrete evidence target:** obtain the exact Google Pixel 5a downstream `modemsmem` DT overlay and implementation, plus MPSS remoteproc and GLINK/QRTR nodes with immutable source IDs; compare them individually to the pinned Linux APIs. Preserve the original Android install and phone function.

## Step 776 — pinned Qualcomm Lito reference inspection (not Pixel 5a overlay)

Inspected the Android kernel/msm-extra/devicetree `qcom/lito.dtsi` at tag `android-11.0.0_r0.56`, blob `ab7d52cf0c446049d39f01c7d494f4b1a8b33a1a`: https://android.googlesource.com/kernel/msm-extra/devicetree/+/refs/tags/android-11.0.0_r0.56/qcom/lito.dtsi . These are **Lito platform reference facts, not a verified Pixel 5a merged device tree**.

- IPCC `ipcc_mproc`: base `0x408000`, size `0x1000`, interrupt `GIC_SPI 229 IRQ_TYPE_LEVEL_HIGH`; 3 interrupt and 2 mailbox cells.
- MPSS node `pil_modem`/`qcom,mss@4080000`: downstream `qcom,pil-tz-generic` compatible; firmware name `modem`; memory region `modem_wlan_mem`; PAS ID **4**; SMEM ID **421**; watchdog SPI **266**; shutdown signal via `mpss_smp2p_out`, input events through `mpss_smp2p_in`, AOP mailbox `qmp_aop`.
- MPSS interrupt names, in source order: `qcom,wdog`, `qcom,err-fatal`, `qcom,err-ready`, `qcom,proxy-unvote`, `qcom,stop-ack`, `qcom,shutdown-ack`.
- `qcom,rmtfs_sharedmem@0`: client ID `0x00000001`, declared size `0x280000`. This is not evidence that a userspace rmtfs service exists on Armada.

`validation/pixel5a-lito-modem-source.json` and its eight negative/baseline checks preserve these source observations and explicitly disallow changing the scope to a proven Pixel 5a overlay. The checks **do not** parse a live downstream kernel checkout or probe any device.

A separate older Qualcomm Lito `lito-smp2p.dtsi` diff includes MPSS SMEM indices **435** and **428**; we must retrieve the exact matching file at the chosen Pixel 5a branch and verify direction, interrupt and mailbox wiring before using them. Similarly, `modemsmem.ko` occurs in the Android redbull kernel prebuilts, but that binary's presence is not proof of modem startup or that the Pixel 5a overlay instantiates its driver.

**Next source gate:** identify the exact Pixel 5a `android-msm-barbet-4.19-android12L` device-tree include graph (and/or another explicit, pinned vendor branch) and complete the MPSS, IPCC, SMP2P, modemsmem, GLINK and rmtfs comparison; then separately map Linux 7.2.6 APIs/bindings. Until then, no new DT nodes, kernel activation or phone flashing.

## Step 777 — pinned Pixel 5a downstream source chain, modemsmem and MPSS SMP2P

**Source provenance:** GitHub mirror `LineageOS/android_kernel_google_redbull`, immutable commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`. This is inspected LineageOS downstream source, **not** an assertion of bit-identical Google stock Android 12L device tree, build, module load or boot. The actual Android Gitiles branch `kernel/msm-extra/devicetree` `android-msm-barbet-4.19-android12L` exists at commit `bac014853ace9398eb34866209e1eb183c7fdfbe`, but its exact DT files have **not** yet been fully read or compared to the mirror.

**Directly fetched and verified source chain** (Git blob IDs from GitHub connector):

1. `arch/arm64/boot/dts/google/lito-v2-barbet-mp.dtsi` (blob `277ae16bb06ebb5c945fe02a579298af45aba3ff`) includes `lito-barbet.dtsi`.
2. `google/lito-barbet.dtsi` (`cbfbedb711ae7bdba17e0513a8f924ce1fdaeeb1`) includes `lito-barbet-common.dtsi`.
3. `google/lito-barbet-common.dtsi` (`4aeed8583a96230c89b11ac85ec6b156abadc2db`) includes `lito-redbull-common.dtsi`.
4. `google/lito-redbull-common.dtsi` (`9eea9dc7431c5ef6cc68f100789402c025b558ce`) declares `modemsmem { compatible = "modemsmem"; };` (lines 136–138).

**Actual downstream implementation is available**, not merely the 2026 upstream RFC: `drivers/soc/qcom/modemsmem/modemsmem.c` (blob `428143562894e6d8ca7b656174c72ee4b096f510`) matches `modemsmem`, allocates and fetches SMEM using `qcom_smem_alloc` and `qcom_smem_get`, and sets SoC information from `socinfo_get_g_platform_type`. Header `drivers/soc/qcom/modemsmem/modemsmem.h` (`a6b9d991fe7c023f44c21cc5c597746414c532a2`) defines `SMEM_ID_VENDOR0 = 134`. `redbull_defconfig` (blob `55e2088384d7189da77f5cd31ccf11dd75e58e4d`) sets `CONFIG_MODEMSMEM=m`. This **does not** mean its module is loaded, its shared memory correct in Linux 7.2.6, or its initialization ordered before MPSS in Armada.

The pinned `arch/arm64/boot/dts/vendor/qcom/lito-smp2p.dtsi` (blob `9a7ba151bed5dbec01bf8013e4de3f9fafc52f11`) directly provides:

- `qcom,smp2p-mpss` with `qcom,smem = <435>, <428>` in this **source order** (not reversed), local PID 0 and remote PID 1.
- Incoming MPSS SMP2P edge IRQ and outgoing mailbox use `&ipcc_mproc`, `IPCC_CLIENT_MPSS`, `IPCC_MPROC_SIGNAL_SMP2P`; incoming IRQ is edge-rising.
- Named `mpss_smp2p_out` and `mpss_smp2p_in` endpoints plus IPA and WLAN inbound children.

The pinned `arch/arm64/boot/dts/vendor/qcom/lito.dtsi` (blob `24b013a4b166456be0a1f8a4a278d9fb3dcfccd1`) agrees with Step 776's basic Lito findings: IPCC SPI **229**, modem PAS ID **4**, modem `qcom,smem-id = <421>`, watchdog SPI **266**, firmware `modem`, region `modem_wlan_mem`. Its downstream compatible `qcom,pil-tz-generic` must **not** be copied blindly to Linux 7.2.6 remoteproc.

**Important distinction:** SMEM item **134** is the Pixel modemsmem vendor-data item, **421** is the MPSS subsystem SMEM ID, and **435/428** are SMP2P edge IDs. These are separate contracts; do not substitute one for another.

`validation/pixel5a-barbet-modem-reference.json` and `tests/pixel5a-barbet-modem-reference-test.py` preserve the exact source-blob identities, path chain and constants, reject missing or reversed wiring and unsupported readiness/activation claims. This is *metadata consistency*, not DT compilation or hardware testing.

**Next engineering gate:** obtain the exact Google `android-msm-barbet-4.19-android12L` tree's matching `qcom/lito*.dtsi` and stock overlays; compare content and include graph; map downstream subsystem and SMEM APIs to pinned mainline. Keep modem and interconnect disabled and do not touch firmware.

## Step 778 — pinned Linux 7.2.6 modemsmem interface compatibility and isolated C harness

**Compared exact source:** downstream Redbull `drivers/soc/qcom/modemsmem/modemsmem.c` blob `428143562894e6d8ca7b656174c72ee4b096f510`, downstream `modemsmem.h` blob `a6b9d991fe7c023f44c21cc5c597746414c532a2` (commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`); pinned mainline Linux 7.2.6 commit `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`, `include/linux/soc/qcom/smem.h` blob `f946e3beca215548ac56dbf779138d05479712f5`, `include/linux/soc/qcom/socinfo.h` blob `ba823a0013c583620a9071bc9d9425da51158df5`, and `drivers/soc/qcom/socinfo.c` blob `af418adad7aaf3855ca12c797f0ec2abd07b0474`.

**API compatibility:**
- Pinned mainline declares `qcom_smem_alloc(unsigned host, unsigned item, size_t size)` and `qcom_smem_get(unsigned host, unsigned item, size_t *size)`, as well as `QCOM_SMEM_HOST_ANY`. These support the shape of the downstream SMEM allocation and retrieval calls, **not** proof of data layout or early-init ordering.
- Downstream includes `<soc/qcom/socinfo.h>` and uses `socinfo_get_g_platform_version()`, `socinfo_get_g_platform_type()`, `socinfo_get_g_platform_subtype()`. Pinned mainline has `<linux/soc/qcom/socinfo.h>` describing `struct socinfo` including `plat_ver`, `hw_plat`, `hw_plat_subtype`, but does **not** declare those downstream getters. An independent adapter must validate SMEM item `SMEM_HW_SW_BUILD_ID = 137`, field format version and size before reading them, and establish which version/plat fields correspond to downstream expectations.
- The downstream vendor payload is **16 32-bit words / 64 bytes**; `SMEM_ID_VENDOR0 = 134`. The downstream major ID computation masks bits 16–23 (`(version >> 16) & 0xff`), minor ID uses bits 0–7 (`version & 0xff`). A port must not silently widen these values based on mainline SOCINFO_MAJOR/SOCINFO_MINOR macros.
- Downstream `modemsmem.c` accepts `qcom_smem_alloc` return `-EEXIST`, then fetches the item; it returns `-ENOMEM` for several unrelated failures, unconditionally `memset_io`s the item, tolerates sysfs group registration failure, and has no driver `remove` function for its sysfs group. These lifecycle/error characteristics must be addressed before loading a kernel port.
- Existing `modem_flag`, factory and dual-SIM behavior references a vendor `/chosen/cdt/cdb2` property; validate the exact intended flag semantics and never enable factory test behavior implicitly.

**New executable research implementation:** `research/pixel5a-modemsmem/modemsmem_payload.h` defines the fixed-size vendor data contract and a C11 `armada_modemsmem_build()` implementation with explicit caller-supplied platform values, zeroed reserved words and opt-in factory/DSDS flags. `test_modemsmem_payload.c` exercises this exact helper in compiled C with five cases: ABI size/offsets, normal version and flag mapping, explicit factory/DSDS, repeated initialization clearing stale flags, and NULL argument rejection. CI compiles with strict C11 warnings and UBSan.

**Scope limitation:** this helper is a standalone host-compilable payload transformation. It **does not** connect to Linux Kconfig/Makefile, use `qcom_smem_*`, read SoCinfo from hardware, implement a platform driver, or load a modem. Passing five tests proves only the specified helper's tested behavior. It must not be called a compiled kernel module or a complete modem-support port.

**Next engineering work:** design and compile an isolated kernel-facing adapter with pinned Linux 7.2.6 headers/stubs, source-backed SoCinfo format/size checks, SMEM allocation ownership/error handling, and ordering relative to MPSS remoteproc; no real memory publication or activation until an approved and validated stage.

## Step 779 — bounded Socinfo decoder and simulated SMEM staging (no publication)

Using pinned Linux 7.2.6 `include/linux/soc/qcom/socinfo.h` blob `ba823a0013c583620a9071bc9d9425da51158df5` and `include/linux/soc/qcom/smem.h` blob `f946e3beca215548ac56dbf779138d05479712f5`, an **isolated host-compilable C11 adapter** was added in `research/pixel5a-modemsmem/modemsmem_adapter.h`.

- The decoder recognizes **SMEM_HW_SW_BUILD_ID / item 137**. Using the reviewed prefix of mainline's `struct socinfo` layout, it reads 32-bit little-endian `fmt` at offset 0, `hw_plat` at 52, `plat_ver` at 56, and `hw_plat_subtype` at 64. It first verifies at least 4 bytes to read `fmt`, accepts only reviewed format 0.6 through 0.23, and requires 68 bytes before reading the later fields. Other formats fail closed until individually reviewed.
- The resulting `armada_modemsmem_inputs` preserve the Step 778 vendor payload mapping, with no automatic `modem_flag`, factory or DSDS enablement. The adapter **does not** verify a real firmware's layout or match downstream `socinfo_get_g_platform_*()` getters on a Pixel 5a, so such equivalence remains a hypothesis.
- A mocked callback interface mirrors the pinned `qcom_smem_alloc` and `qcom_smem_get` host/item/size contract, but **intentionally normalizes get-errors** to integer return codes for host testing rather than pretending Linux `ERR_PTR` is safely a C pointer. A future kernel wrapper must implement `IS_ERR/PTR_ERR` correctly. It accepts already-existing item 134 (`-EEXIST`), checks that vendor item size is 64 bytes and never copies bytes into that item.
- **Nine compiled C fault-path cases** exercise normal staging, already-existing SMEM, source read error, truncated source data, unsupported format, allocation failure, wrong vendor item size, vendor read failure and invalid callback arguments. Every failure leaves the output untouched, and the mock vendor bytes remain unchanged. GitHub Actions compiles with strict warnings and UBSan.

This is **not** a real Linux kernel header compilation, module build, SMEM initialization, modem registration, remoteproc sequencing, or on-device test. It intentionally lacks write/publish and teardown. In particular, the real lifetime/locking and whether kernel Socinfo format and platform fields match the Pixel 5a modem firmware remain unverified. Do not activate the driver or create a platform device from this experiment.

**Step 780 direction:** add source-backed kernel wrapper design and validate the negative paths of `IS_ERR/PTR_ERR`, format fallback and modem-init ordering against the exact pinned Linux driver. Keep hardware disabled and generic RPMh fixes isolated.

## Step 780 — SMEM ERR_PTR semantics and MPSS ordering block

**Pinned source examined:** Linux 7.2.6 base `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`, `drivers/soc/qcom/smem.c` blob `afb21a778fe7bb22a6093145c900e132b1ff7747`, `include/linux/err.h` blob `d3e38d5b3a985b016d25dc000d29bb9034c87cf5`, `drivers/remoteproc/qcom_q6v5_pas.c` blob `cb3e51d6f7cecbe5c2f5b72059001efab047f089`.

- `__smem` begins as `INIT_ERR_PTR(-EPROBE_DEFER)` (SMEM driver around line 358). `qcom_smem_alloc()` checks `IS_ERR(__smem)` and returns its `PTR_ERR` as a **negative int**. `qcom_smem_get()` instead returns an **error pointer** if SMEM is unavailable; its documented contract explicitly says `ERR_PTR()` on failure. `qcom_smem_is_available()` is only a boolean and does not distinguish deferred, absent or other failures. A wrapper must call `IS_ERR`/`PTR_ERR` before any dereference, preserving `-EPROBE_DEFER`, `-ENODEV`, `-ENOENT`, etc., rather than mapping everything to `-ENOMEM`.
- `qcom_smem_alloc()` and `qcom_smem_get()` operate with item number and host; vendor item `134` remains a separate contract from mainline SoC-info item `137`. Neither guarantees that creating the vendor item is safe if another consumer already owns or expects its contents.
- Pinned `qcom_q6v5_pas.c` drives the modem remoteproc through `rproc_add()` and `qcom_pas_start()`. Direct inspection did **not** identify a device-link or explicit ordering dependency requiring our research `modemsmem` stage to publish its data before MPSS start. **This is an unresolved boot-order hazard**, not proof that the modem currently starts too early. No MPSS startup can be authorized until a suitable dependency strategy and its real-kernel lifecycle are validated.

**Added research-only facade:** `research/pixel5a-modemsmem/kernel_smem_facade.h` includes Linux-facing headers `linux/err.h` and `linux/soc/qcom/smem.h`, and provides tiny `armada_modemsmem_kernel_get()`/`armada_modemsmem_kernel_alloc()` wrappers. The get wrapper checks `IS_ERR` and returns `PTR_ERR`, detects unexpected NULL and leaves its output arguments unchanged on errors. `test_kernel_smem_facade.c` compiles the facade under **deliberately mocked** Linux include files and runs seven error-path tests including defer, absent item, uninitialized SMEM, NULL and allocation `-EEXIST` handling.

These seven tests exercise a **host simulation** of Linux error-pointer encoding, *not* the actual Linux headers or kernel build. They do not establish concurrent lifetime, SMEM ownership, memory writes, clock/power requirements or that a modem can start. No code in this step publishes SMEM, adds a Kconfig entry or activates hardware.

**Next gate:** test the facade against the exact Linux 7.2.6 kernel header environment (not just mocks), establish whether the Google vendor item requires overwrite vs. preserve-on-reprobe and verify how a real MPSS remoteproc startup would be deferred until vendor SMEM publication. No assumptions about boot order or flash permissions.

## Step 781 — non-enabling MPSS start-order model (host C11 only)

Introduced `research/pixel5a-modemsmem/modem_boot_gate.h` plus `test_modem_boot_gate.c`. This is **a model of intended ordering, not a kernel integration**. It holds the states `WAIT_SMEM`, `STAGED`, `READY_SIMULATED` and `FAILED`. A simulated start request returns `-EAGAIN` until both successful input staging and an **explicit mock acknowledgement** of publication. No SMEM write is provided: callers can simulate acknowledgement, but cannot use this header to publish vendor data or actually start the MPSS remoteproc.

The host test suite has nine checks: initial denial, simulated defer, retry after defer, rejection of premature acknowledgement, explicit mock success, permanent staging failure, failed acknowledgement, reset revocation and NULL input errors. The suite is compiled as C11 with strict warnings and UBSan. `-EAGAIN` represents pending work **only in this host model**; a real kernel probe would use `-EPROBE_DEFER` as appropriate.

**Critical limitation:** The actual Linux 7.2.6 `qcom_q6v5_pas.c` remoteproc startup path is not wired to this model. The model is not concurrency-safe or a kernel security gate. It does not demonstrate that MPSS firmware reads SMEM item 134, that acknowledgement can be trusted, or that system init ordering is solved. Never interpret a host PASS as a modem-boot authorization or hardware qualification.

**Step 782 prerequisite:** establish a real, source-backed kernel mechanism that prevents remoteproc startup before required vendor SMEM data publication, including concurrency, probe defer, reprobe and teardown. Verify it in an isolated kernel build before considering device enablement. The existing Android installation, modem firmware and working phone functionality remain protected.

## Step 782 — remoteproc autostart, recovery and generation-lifetime review

**Pinned Linux 7.2.6 source** `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`:
- `drivers/remoteproc/qcom_q6v5_pas.c`, blob `cb3e51d6f7cecbe5c2f5b72059001efab047f089`, `qcom_pas_probe()` lines 803–808 defers if secure monitor is not ready. Around lines 827–835 it allocates an rproc and assigns `rproc->auto_boot = desc->auto_boot`; around 917–920 it handles early-boot state and registers with `rproc_add()`. No dependency on our unpublished vendor SMEM item 134 was found in this path.
- `drivers/remoteproc/remoteproc_core.c`, blob `527996e8ecdaaa840738b74b911a1192d769045c`: `rproc_add()` lines 2296–2326 calls `rproc_trigger_auto_boot()` when `auto_boot` is true. That mechanism may schedule attach work or asynchronous firmware loading; callback calls `rproc_boot()` (lines 1662–1697). A probe-only check or changing a single booleans does **not** establish a universal startup barrier for manual or recovery paths.
- `qcom_pas_start()` in PAS source lines 270–341 performs Q6 preparation, powers dependencies, loads/authenticates firmware and waits for start. `qcom_pas_remove()` (around lines 944 onward) calls `rproc_del()`. A readiness guard would require clear ownership and synchronization with remoteproc lifecycle and error cleanup; inserting a bare condition is not sufficient.
- The downstream Redbull driver, the pinned Linux 7.2.6 remoteproc framework and a Pixel 5a-specific userspace/firmware requirement must be reconciled before any production design.

**Added host-only generation model:** `research/pixel5a-modemsmem/modem_start_epoch.h` and `test_modem_start_epoch.c`. The model has separate automatic, explicit and recovery start origins. Each remains blocked until the *current* simulated generation has been staged and acknowledged. A restart increments a generation token and revokes readiness. Acknowledgements or staging from an earlier generation fail closed. The twelve compiled C cases exercise initial and staged denial, defer/retry, premature acknowledgement, reset, stale acknowledgement, current-generation requirements, terminal staging/publication failure, repeated staging, invalid origin and generation-wrap rejection. CI runs the executable with strict C11 warnings and UBSan.

**Unresolved:** This model does not intercept the real remoteproc's asynchronous auto-boot callback, manual rproc boots, crash recovery or teardown. It has no locking and uses a caller-controlled simulated acknowledgement—not a verified hardware publication guarantee. It does not publish SMEM or implement a real kernel callback. Host success provides **no** device-safety authorization.

**Step 783 target:** inspect exact `rproc_boot` and crash-recovery locking/restart paths, check whether an isolated, non-active module could enforce readiness at the shared start path with sound ownership and teardown, then use kernel-header compilation checks before writing an actual integration patch. Maintain the original Android installation and all modem firmware unchanged.

## Step 783 — remoteproc core lock and recovery bypass audit

The Step 782 source-only workflow run #54 (`43795236652`) completed successfully. Inspected pinned Linux 7.2.6 commit `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`, `drivers/remoteproc/remoteproc_core.c` Git blob `527996e8ecdaaa840738b74b911a1192d769045c`, with these distinct entry paths:

- **Normal boot (lines 1912–1969):** `rproc_boot()` obtains `mutex_lock_interruptible(&rproc->lock)`, rejects `deleting`, and increments `rproc->power`. Additional boot callers return success when power was already above 1; otherwise firmware loading/boot happens inside the lock. Guarding only the low-level PAS start path would not address boot reference increments or attach semantics.
- **Crash/recovery (lines 1825–1853 and 1862–1895):** crash handler marks `RPROC_CRASHED` under `rproc->lock`; `rproc_trigger_recovery()` again locks and calls **`rproc_boot_recovery()` or `rproc_attach_recovery()`**, rather than routing directly through `rproc_boot()`. A gate patched only into `rproc_boot()` would miss this path.
- **Deletion (lines 2589–2619):** `rproc_del()` sets `deleting` under `crash_handler_lock`, cancels crash work, calls shutdown, and unregisters the device. Any external publication-state gate needs lock-order analysis and teardown lifetime guarantees; a standalone boolean cannot safely coordinate with all these operations.
- **Crashes (lines 2715–2738):** `rproc_report_crash()` can be called from atomic context and queues recovery work. No sleeping publication operation can safely be inserted directly in the atomic crash notification path.

**Host-only experiment:** added `research/pixel5a-modemsmem/modem_lifecycle_audit.h` and `test_modem_lifecycle_audit.c`; nine compiled tests model crash generation invalidation, stale asynchronous acknowledgements, fresh recovery acknowledgement, terminal removal, delayed acknowledgement after removal, duplicate crash, failed recovery, overflow and NULL handles. The model is deliberately single-threaded, has no kernel locking, cannot observe real SMEM publication, and makes no real remoteproc calls. GitHub Actions tests only this simulated behavior.

**Open design blockers before a true kernel-compilable module:** establish a real publication protocol with memory ordering and lifetime ownership, whether SMEM item 134 can be rewritten on modem restart, kernel probe/remoteproc start dependency wiring, handling of early attached firmware, crash workqueue lock order, and compatibility of the exact Linux 7.2.6 headers. Do not change the PAS driver or activate MPSS until these are source-backed, compiled and independently reviewed. A passing host test is not evidence that the phone can boot Armada or place calls.

**Next checkpoint:** Step 784 can build an isolated kernel-header compile probe (no driver registration) against the pinned kernel using GitHub Actions and include an explicit source audit of `rproc_boot_recovery()`, `rproc_attach_recovery()` and their lock requirements.

## Step 784 — compile-only Linux 7.2.6 ARM64 kernel API probe

**Source identity and separation:** pinned `torvalds/linux` commit `500df175a7f9e6bc1a9c328590ca5150f84f9ff0` (top-level Makefile VERSION 7 / PATCHLEVEL 2 / SUBLEVEL 6). The actual pinned SMEM header is `include/linux/soc/qcom/smem.h` (Git blob `f946e3beca215548ac56dbf779138d05479712f5`); Socinfo header is `include/linux/soc/qcom/socinfo.h` (blob `ba823a0013c583620a9071bc9d9425da51158df5`). A newly isolated compilation probe lives in `research/pixel5a-modemsmem/modemsmem_kernel_header_probe.c`. It includes those **real Linux kernel headers**, rather than the Step 780 host mocks, alongside the existing error-pointer facade, and checks the `struct socinfo` offsets for fmt/hw_plat/plat_ver/hw_plat_subtype and the presence of `SMEM_HW_SW_BUILD_ID=137`.

**Dedicated CI workflow:** `.github/workflows/pixel5a-kernel-api-compile.yml` downloads that exact pinned commit to the GitHub runner's temporary directory; installs the ARM64 cross-compiler and Kbuild dependencies; runs an ARM64 `defconfig` and `modules_prepare`; then compiles the isolated external Kbuild probe. It checks that `modemsmem_kernel_header_probe.o` is produced and does not upload or run any resulting module artifact. The source includes no `module_init`, `platform_driver_register`, firmware request, modem start or SMEM publication.

**Scope:** A successful external-module object compile checks types, field offsets and header compatibility under the selected generic ARM64 configuration. It is **not** a complete Android kernel build, link/symbol compatibility guarantee, functional module implementation, DT or firmware verification, or phone test. The workflow uses `KBUILD_MODPOST_WARN=1` because `modules_prepare` does not provide a built-kernel `Module.symvers`; linking warnings cannot be represented as success evidence. No `CONFIG_MODEMSMEM` driver has been added to Linux.

**Still unresolved:** `rproc_trigger_recovery()` holds `rproc->lock` and calls a separate `rproc_boot_recovery`/`rproc_attach_recovery` path; any actual publication gate needs fully verified ownership, correct lock order, the early-attached-remoteproc case, synchronization with asynchronous firmware callbacks, and real phone-specific firmware semantics. Do not activate modem drivers or flash the phone. Next checkpoint is to inspect the *completed* compile workflow, fix genuine build issues, and only then consider an isolated kernel-facing adapter and lifecycle design.

## Step 785 — read-only kernel-facing SMEM preflight (first kernel-native research helper)

**Baseline:** Step 784 GitHub Actions kernel API compile run #2 (`43795990681`) and phone validation run #61 (`43795990690`) both passed for commit `a7786390a163478e93e539c48066e3231433f631`.

**Added** `research/pixel5a-modemsmem/kernel_readonly_preflight.h` and compiled it through the existing `modemsmem_kernel_header_probe.c` using Linux 7.2.6 kernel headers (pinned mainline commit `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`).

The helper is deliberately **read-only and disconnected**:
- Fetches item `SMEM_HW_SW_BUILD_ID` (**137**) using the existing Linux-facing `IS_ERR/PTR_ERR` facade and preserves the exact errors, including deferred probe and missing items.
- Requires at least 68 bytes before copying the reviewed `struct socinfo` prefix; accepts only source-reviewed format versions **0.6 through 0.23**, then reads little-endian `hw_plat` at offset 52, `plat_ver` at 56 and `hw_plat_subtype` at 64. Extracts downstream 8-bit vendor major/minor fields into a **host-endian candidate**, never a published payload.
- Looks up already-present vendor SMEM item **134** read-only, requires an exact 64-byte size, and returns the candidate **only if both item lookups and all bounds/format checks succeed**.
- Does **not allocate item 134**, write any SMEM contents, claim ownership or validate existing vendor values. A successful preflight is not a publication acknowledgement and must not authorize modem startup. Missing item 134 remains a blocker until a safe allocation/ownership strategy is established.
- No Kconfig, device-tree entry, platform driver registration, module init hook, or real remoteproc call. There is no activation path for this helper.

Added `tests/pixel5a-kernel-readonly-preflight-test.py` with seven static source/negative tests: baseline guard presence, allocation rejection, write rejection, remoteproc-start rejection, vendor-size guard retention, kernel-probe wiring, and unknown-format rejection. The separate GitHub kernel workflow checks compilation against actual pinned ARM64 headers. Static tests do not exercise real SMEM and kernel compilation does not establish runtime safety.

**Critical unresolved ownership and ordering:** A vendor item may already contain firmware-managed information; size alone does not imply it is safe to overwrite, zero or free it. Remoteproc automatic boot and recovery paths are not integrated with any publication barrier. The next safe checkpoint is an isolated **real-kernel-compiled** ownership/deferral design and negative tests for absent vendor allocation, arbitrary error-pointer returns, and teardown/callback races—without ever enabling the driver.

## Step 786 — vendor SMEM allocation ownership audit without allocation

**Pinned kernel evidence**: Linux 7.2.6 `drivers/soc/qcom/smem.c` at `500df175a7f9e6bc1a9c328590ca5150f84f9ff0` was directly inspected. In both private and global allocation paths, an already allocated item produces `-EEXIST` (private around line 425; global around 471–472). `qcom_smem_alloc()` (around 506–544) uses a hardware spinlock and returns integer errors, whereas `qcom_smem_get()` (around 686–709) returns an `ERR_PTR()` on failure. The global lookup reports an unallocated slot as `ERR_PTR(-ENXIO)`; private-path failure may report `-ENOENT`. An unprobed `__smem` starts as `-EPROBE_DEFER`. There is no generic free operation in the public SMEM interface examined. **Neither -EEXIST nor a size-matching lookup tells us who owns item 134.**

The new `research/pixel5a-modemsmem/kernel_vendor_ownership_audit.h`, compiled into the same inactive ARM64 Kbuild probe as Step 785, observes item **134** without allocating or writing to it. It reports `PRESENT_UNOWNED` (64-byte size observed but not ownership proof), `ABSENT_UNOWNED` (`-ENXIO`/`-ENOENT`), `UNAVAILABLE` (`-EPROBE_DEFER`), `INVALID_SIZE`, or `OTHER_ERROR`. The deferred/error paths retain underlying negative errors. The distinction between a successful observation and an authorization to publish is intentional: **no state grants write permission or modem-start readiness**.

`tests/pixel5a-vendor-ownership-audit-test.py` provides eight baseline/negative source-contract tests. Both `.github/workflows/android-phone-validation.yml` and `.github/workflows/pixel5a-kernel-api-compile.yml` enforce them. The dedicated kernel workflow also compiles the header through `modemsmem_kernel_header_probe.c` against the actual pinned Linux 7.2.6 ARM64 headers. These source checks do not demonstrate runtime concurrency, memory ordering, error recovery, or successful modem initialization.

**Cleanup design remains blocked:** There is no approved owner for a newly created item 134, no confirmed authority to wipe/reuse an existing item, and no proof that a modem restart requires rewriting the item. We therefore implement no allocation, zeroing, overwriting, freeing or firmware/remoteproc activation. Any later active path must first identify authoritative Pixel 5a firmware/vendor expectations, secure an explicit device-init lifecycle and synchronization strategy, and validate a complete isolated build before device testing.

## Step 787 — authoritative downstream modemsmem write and teardown behavior

Direct inspection of `LineageOS/android_kernel_google_redbull` at pinned commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`:
- `drivers/soc/qcom/modemsmem/modemsmem.c`, Git blob `428143562894e6d8ca7b656174c72ee4b096f510`
- `drivers/soc/qcom/modemsmem/modemsmem.h`, Git blob `a6b9d991fe7c023f44c21cc5c597746414c532a2`
- `drivers/soc/qcom/modemsmem/Makefile`, Git blob `b7c435d9f9e09a203818b3e491e8696ff212d34`, conditional `CONFIG_MODEMSMEM`

**Important correction to ownership planning:** The original Google/Redbull downstream probe calls `qcom_smem_alloc(..., SMEM_ID_VENDOR0, sizeof(struct modem_smem_type))`, accepts `-EEXIST`, gets the item, and then **unconditionally zeros all 64 bytes with `memset_io()`**. It rewrites version, platform, subtype and firmware-specific flags with `writel_relaxed()` via `modem_smem_set_u32()`. Thus the original driver **does overwrite an existing allocation**, but its behavior is not evidence that a new, unrelated Linux 7.2.6 port has the authority or correct boot timing to do likewise.

The original implementation also uses downstream-only `socinfo_get_g_platform_*()` getters, `/chosen/cdt/cdb2` fields (modem_flag, factory bootmode, dsds), and exposes a factory-mode-writeable `modemsmem` sysfs attribute. It maps several allocation/get failures to `-ENOMEM`, tolerates sysfs group creation failure while still returning probe success, and has **no explicit platform `.remove` callback or `sysfs_remove_group()`**. This is a source-level lifecycle concern, not proof of a runtime leak in a specific boot environment.

**Step 787 deliverables:** `validation/pixel5a-downstream-modemsmem-write-audit.json` pins the exact downstream source identity and records destructive writes, boot flags and incomplete lifecycle handling. `tests/pixel5a-downstream-modemsmem-write-audit-test.py` provides 10 source/baseline-negative tests that reject unreviewed changes to provenance, enablement, overwrite claims, factory sysfs, and hidden limitations. Both GitHub workflows enforce these tests.

**No new active kernel writes:** The Step 785–786 read-only preflight and ownership classifier remain intentionally disconnected; this step adds no allocation, overwrite, sysfs, platform driver, firmware access, modem startup, or kernel image. A safe active implementation still requires explicit Pixel 5a-specific publication timing/owner evidence, rigorous restart lifecycle and actual kernel/phone validation. Keep PR #18 draft and protect the existing Android installation.

## Step 788 — downstream publication versus PAS startup ordering contract

**Previous CI:** Step 787 Android phone validation #69 (`43799652749`) and actual pinned Linux 7.2.6 ARM64 kernel API compile #10 (`43799652842`) both completed successfully. This proves only the existing source/host contracts and isolated compilation; it does not prove modem initialization.

**Source anchors, directly inspected:** immutable `LineageOS/android_kernel_google_redbull` commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`:
- `drivers/soc/qcom/modemsmem/modemsmem.c`, blob `428143562894e6d8ca7b656174c72ee4b096f510`: probe allocates vendor SMEM 134 (accepts `-EEXIST`) around line 174, fetches the 64-byte item around 181, unconditionally zeros it via `memset_io` at 188, then sets vendor fields and optionally creates a factory-writeable sysfs group around 243; module init registers a platform driver around 272. No completion notification to the MPSS start path appears in this inspected implementation.
- `arch/arm64/boot/dts/google/lito-redbull-common.dtsi`, blob `9eea9dc7431c5ef6cc68f100789402c025b558ce`, declares `modemsmem { compatible = "modemsmem"; }` around lines 136–138.
- `arch/arm64/configs/redbull_defconfig`, blob `55e2088384d7189da77f5cd31ccf11dd75e58e4d`, configures `CONFIG_MODEMSMEM=m` (line 627), i.e. a module in this downstream kernel configuration, **not** an init ordering dependency.

**Distinct mainline PAS pathway:** Linux 7.2.6 commit `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`, `drivers/remoteproc/qcom_q6v5_pas.c`, blob `cb3e51d6f7cecbe5c2f5b72059001efab047f089`: PAS probe checks only SCM availability at lines 807–808, assigns `rproc->auto_boot = desc->auto_boot` around 835 and registers through `rproc_add()` around 920. In `drivers/remoteproc/remoteproc_core.c`, blob `527996e8ecdaaa840738b74b911a1192d769045c`, `rproc_add()` may initiate async autostart. The inspected sources **do not establish** that module-driven modemsmem initialization necessarily precedes MPSS startup. Nor do these observations prove it happens in the opposite order: actual stock Android 12L boot orchestration, userspace module load order, firmware interactions and device-link topology have not been verified.

**Cleanup contract is still incomplete:** The inspected downstream modemsmem driver has no explicit `.remove`/sysfs-group cleanup callback. A future port would need explicit and verified probe/remove handling, ownership of any previously allocated vendor data, correct preservation/republication semantics on crash/reprobe, and synchronization with remoteproc auto/manual/recovery startup. A source-only audit must never retrofit `memset_io` into the isolated read-only helper.

**Step 788 artifacts:** `validation/pixel5a-modem-publication-order-audit.json` records pinned source blobs, observed downstream probe sequence and mainline PAS registration, uncertainties and explicit no-activation requirements. `tests/pixel5a-modem-publication-order-test.py` adds 10 baseline/negative tests, incorporated into both GitHub workflows. These lock the **unknown** status rather than inventing a guaranteed ordering or granting permission to write SMEM.

**Next investigation:** trace the Pixel 5a-specific stock Android 12L `init*.rc`, module load rules and effective boot/firmware dependencies from an exact pinned source; compare to downstream modemsmem registration and PAS startup. Even if source evidence establishes load order, real restart paths, shared memory ownership and userspace telephony remain separately blocked. No phone access or kernel activation is authorized.

## Step 789 — pinned Barbet Android init and early module-loading evidence

**Baseline verification:** Step 788 Android phone validation run #73 (`43805638006`) and Linux 7.2.6 ARM64 kernel header compile run #14 (`43805637967`) both completed successfully for commit `a8eb62d4035c4bb2ae630ffa436032b30ef0efca`.

**Pinned device source inspected directly, not exact stock Android 12L binaries:**
- `LineageOS/android_device_google_barbet` commit `24101a383bb1951952adcd6f62668338dd048f03`: `init.insmod.barbet.cfg` blob `f2728df28091a374ff6bfa6e4e50f3695420e722`, `barbet/init.barbet.rc` blob `e90914410f21493621e2f6ac6c3e00e117ed9c9c`, `device-barbet.mk` blob `750a8be1c808ec4e861e2627059d7022d0507560`.
- `LineageOS/android_device_google_redbull` commit `9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770`: `modules.load` blob `b116d1f234682a1f7e7275f36e6c7a2feb79ddb5`; `BoardConfig-common.mk` blob `a70253537c0da383ac0c96c9f02f526faba89ef4`; `BoardConfigLineage.mk` blob `73921b90f308b6adbf6ba6b0d31c563eedede37e`; `init.hardware.rc` blob `ec3c3edf7e72fb394bde8e9dc669e4a07ced854b`; `init.insmod.sh` blob `a222838cc855392838a69fbd9ea3951273078658`.

**Established from these sources:**
1. `modules.load` explicitly lists `smem.ko`, `subsys-pil-tz.ko`, and `modemsmem.ko` (the latter path `kernel/drivers/soc/qcom/modemsmem/modemsmem.ko`). `BoardConfig-common.mk` includes those names in `BOOT_KERNEL_MODULES`, with a comment assigning those modules to first-stage `vendor_boot.img`; `BoardConfigLineage.mk` filters module output into vendor-ramdisk and vendor module lists. Therefore, for this source tree, `modemsmem` is **listed as an early-boot module**, not merely a later unreferenced vendor module.
2. Barbet `init.insmod.barbet.cfg` starts with `modprobe|-b *`, then `modprobe|ftm5.ko`, sets `vendor.all.modules.ready`, enables ADSP/CDSP and sets `vendor.all.devices.ready`. The common `init.hardware.rc` starts `insmod_sh` at `on init` and later waits for those properties; `init.insmod.sh` invokes `modprobe -a -d /vendor/lib/modules` using `modules.load` where present.
3. **Important limitation:** the shell script does not check whether `modprobe` succeeded and unconditionally sets readiness properties even if the configuration file is missing. It is therefore unsafe to interpret `vendor.all.modules.ready=1` as proof that `modemsmem` probed, initialized SMEM item 134 or published all 64 bytes before MPSS startup.
4. A module list order alone is not a verified driver probe-completion order; first-stage `vendor_boot.img` inclusion and the additional modprobe phase need to be reconciled against the actual kernel/device dependency graph. The **downstream Qualcomm `subsys-pil-tz` loader must not be silently equated** with the separate mainline Linux 7.2.6 `qcom_q6v5_pas` remoteproc path examined earlier.
5. These are pinned LineageOS-derived device source files. They are **not a byte-for-byte demonstration of Pixel 5a stock Android 12L vendor_boot, init rc, modules.load, boot logs, or firmware load order**.

**Step 789 deliverables:** `validation/pixel5a-barbet-module-load-evidence.json` pins the six important common/Barbet source files and additional product/boot composition evidence. `tests/pixel5a-barbet-module-load-evidence-test.py` adds ten baseline/negative tests to **both** CI workflows. These enforce the source identity, early-module evidence, readiness property limitation, no false ordering claim, downstream-vs-mainline difference and no active modem permission.

**Next:** investigate the exact stock Android 12L Pixel 5a vendor_boot image/module list, init services and boot logs (without flashing or modifying the phone) to distinguish listed load order from actually completed modemsmem probe and MPSS initialization. Any firmware image handling and future ADB reads require explicit safe methodology and permission. Do not modify active SMEM, modem firmware or the working Android installation.

## Step 790 — official Pixel 5a Android 12L release identity versus stock vendor_boot inspection

**Baseline:** Step 789 Android phone CI #77 (`43910932347`) and actual pinned Linux 7.2.6 ARM64 compile CI #18 (`43910933790`) completed successfully on commit `1675e949ff2c9461079ab8bfe05f8303155a8af4`.

**Official stock release identity is now sourced directly from Google's Android Building release announcement:** https://groups.google.com/g/android-building/c/GoMawyG2l94/m/gF67Adc6EQAJ (March 7, May 2, and June 6, 2022 entries) and official Google factory/OTA indexes https://developers.google.com/android/images and https://developers.google.com/android/ota . These are relevant to Pixel 5a / barbet Android **12.1.0 (12L)** and identify:
- March `SP2A.220305.012` with AOSP tag `android-12.1.0_r1`, kernel `device/google/barbet-kernel` tag `android-12.1.0_r0.5` / branch `android-msm-barbet-4.19-android12L`.
- May `SP2A.220505.002` with AOSP tag `android-12.1.0_r5`, barbet kernel tag `android-12.1.0_r0.21` / `android-msm-barbet-4.19-android12L`.
- June `SQ3A.220605.009.A1` with AOSP tag `android-12.1.0_r7`, barbet kernel tag `android-12.1.0_r0.27` / `android-msm-barbet-4.19-android12-qpr3`.

**Scope and licensing:** Google's official factory image index provides restore images and licensing terms. No stock Pixel 5a `vendor_boot.img` or factory archive was downloaded, checksum-verified, decompressed, disassembled, or installed during this step. The user has not selected a particular stock build/variant to match their phone. Therefore **no stock module list, early init script bytes, effective module probe order, modemsmem publication timing or MPSS startup ordering is verified from stock images.** AOSP release tags and LineageOS source lists may inform subsequent read-only comparison, but neither proves the actual proprietary vendor_boot layout or modem runtime behavior.

**Step 790 artifacts:** `validation/pixel5a-stock-android12l-image-evidence.json` records the official build-tag-kernel mappings, stock image evidence gaps, no-modification policy and future prerequisites. `tests/pixel5a-stock-android12l-image-evidence-test.py` has twelve baseline/negative checks against incorrect release mappings, false binary extraction/probe claims and unsafe firmware actions. Both existing GitHub CI workflows run those tests; the Linux kernel build remains an isolated unchanged read-only compile probe.

**Next research gate:** For a *specific authorized stock build*, verify image provenance/checksum and its documented use restrictions, then perform only permitted offline analysis of vendor_boot metadata/module lists; compare AOSP tagged device sources and explain any divergence. If legal/source access prevents binary inspection, keep the blocked item explicit and continue with published source code. Do not flash, boot, alter active partitions, install drivers, or treat an AOSP tag as proof of exact stock-image content.

## Step 791 — exact-tag public AOSP 12L source comparison probe (no factory image)

**Baseline:** Step 790 Android phone validation #81 (`43912441623`) and Linux 7.2.6 ARM64 compile-only probe #22 (`43912441565`) succeeded on commit `5eaf895f4bc55f6b3730d6755370fe1b380f1df1`.

Official `device/google/barbet` and `device/google/redbull` AOSP repositories are accessible as project references (see https://android.googlesource.com/device/google/barbet/ and https://android.googlesource.com/device/google/redbull/+refs). Exact `android-12.1.0_r1`, `r5`, `r7` individual text-file pages were **not accessible via the research browsing interface** at this checkpoint. No exact-tag contents, hashes, or differences from LineageOS are asserted from that failure. Master branch files are not substitutes for these immutable tagged files.

**Step 791 code artifacts:** `research/pixel5a-modemsmem/probe_aosp_12l_sources.py` is a read-only, allowlisted public-text fetcher for six device-tree paths across each of the three Android 12L release tags (18 source/tag records), using official googlesource `?format=TEXT`, base64 decoding, SHA-256 and limited marker-presence observations. Every unavailable source is labeled as such; no claimed checksum or missing evidence is fabricated. All records carry `stock_vendor_boot_verified=false`; even successful tagged source retrieval would only verify *AOSP text*, not the exact vendor_boot binary on a factory phone. `tests/pixel5a-aosp-12l-source-probe-test.py` contains 10 offline mock/negative tests to reject arbitrary tags/paths, fabricated hashes and ungrounded hardware claims. Both existing CI workflows run those tests.

A **third isolated GitHub Actions workflow** `.github/workflows/pixel5a-aosp-12l-source-probe.yml` attempts these public-text downloads on a GitHub runner, reports retrieved/unavailable counts and per-file hashes, and uploads metadata only (not full source, firmware, OTA, factory archive or boot image). A run can complete even with unavailable sources, but its `all_files_retrieved` field remains `false`; such a green CI status must **never** be interpreted as a complete source comparison. CI cannot validate vendor firmware probe timing or actual Android 12L binary compatibility.

**Next gate:** examine the resulting metadata and, only for successfully retrieved tagged files, compare exact source bytes/hashes to the pinned LineageOS files. Treat unavailable tags/files as unverified. If available evidence is insufficient for stock effective module order, continue with published source or separately authorized read-only offline factory image checks. No device, SMEM, remoteproc, firmware, or partition modifications are authorized.
