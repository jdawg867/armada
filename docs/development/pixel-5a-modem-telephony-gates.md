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

### Step 791 verified GitHub-runner result (follow-up to source probe)

The new **official AOSP public-text-only workflow** run #2, ID `43916059845`, completed SUCCESS for commit `c209f41d665c52c2c7a374610f6a0b246e20fab8`. Its logs and metadata artifact establish **15 successfully retrieved tagged source-file records out of 18 attempts**; **three HTTP 404** responses occurred for `device/google/redbull/modules.load`, at each of `android-12.1.0_r1`, `r5`, `r7`. No SHA checksum has been invented for the missing file. A missing repository path at these tags does **not** mean a stock vendor_boot binary has no `modules.load` or that modem support modules are absent.

All five successfully retrieved *paths* have identical SHA-256 content hashes across these three sampled tags:
- `device/google/barbet/init.insmod.barbet.cfg`: `a081d17fbfe8995aaf64ee8dfd4e528a13756d1deb3f660f22da55f044fe8383`
- `device/google/barbet/barbet/init.barbet.rc`: `78a14c15c8c71b5d40c712009711636bbd8505e85419cfec92ec4e15e9bbef4e`
- `device/google/redbull/BoardConfig-common.mk`: `27a623d774cb7818a892d340c9a36aee732f69f4d482b0a73fdf30757fbf5ff3`
- `device/google/redbull/init.hardware.rc`: `5cf98b4bab2359a81f5ddf3b10db397f9ff0361ad850733226cc7ed30f21f294`
- `device/google/redbull/init.insmod.sh`: `d6ca82cf42232a1b1e934827e055c024f39f5fdc1def5905b6f131bbb62f0855`

`validation/pixel5a-aosp-12l-tag-probe-result.json` preserves the exact result snapshot and `tests/pixel5a-aosp-12l-tag-result-test.py` adds nine baseline/negative tests enforced in both existing workflows. **No exact byte comparison to the LineageOS source files, stock image inspection, effective module-probe timing, SMP2P/MPSS startup order or phone functionality has yet been verified.** Next investigation should fetch the pinned LineageOS source bytes in a similarly bounded source-only job and compare hashes/differences only for matching AOSP paths; keep the absent AOSP `modules.load` status explicit. No physical handset access is necessary for source comparison.

## Step 792 — pinned AOSP Android 12L vs LineageOS source-byte comparison

**Baseline:** Step 791 Android phone validation #90 (`43916536699`), Linux 7.2.6 ARM64 header compile #31 (`43916536755`), and public AOSP text-source probe #6 (`43916536620`) all passed at commit `958bb0d5889569b7bab4ef7ddb8183ee4c574ee6`.

**Exact matching public source inputs:** For Google AOSP `device/google/barbet` and `device/google/redbull`, the GitHub-runner comparison requests only five confirmed retrievable paths at each `android-12.1.0_r1`, `r5` and `r7`. The LineageOS counterpart is pinned to immutable `LineageOS/android_device_google_barbet` commit `24101a383bb1951952adcd6f62668338dd048f03` and `LineageOS/android_device_google_redbull` commit `9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770`. The five paths are `init.insmod.barbet.cfg`, `barbet/init.barbet.rc`, `BoardConfig-common.mk`, `init.hardware.rc` and `init.insmod.sh`.

The research script `research/pixel5a-modemsmem/compare_aosp_lineage_12l.py` downloads bounded public **text source only** from official Googlesource and immutable GitHub raw paths, calculates SHA-256 for both sides, compares exact UTF-8 bytes, and reports count-only line-diff metadata. It records retrieval failure without fabricating hashes or equivalence. The dedicated `.github/workflows/pixel5a-aosp-12l-source-probe.yml` runs this and uploads metadata only; neither binary firmware nor proprietary stock `vendor_boot.img` is downloaded or redistributed. `tests/pixel5a-aosp-lineage-comparison-test.py` adds ten mocked/offline checks for exact refs, missing-file handling, byte equality/differences, SHA calculation, and no hardware claims, included in all existing validation workflows.

The earlier AOSP `device/google/redbull/modules.load` returns HTTP 404 at all three tags, while the pinned LineageOS tree contains `modules.load`. **No byte-by-byte compare of that missing AOSP file is possible;** the fact it is missing from the tagged public source path says nothing definitive about the factory image. The comparison workflow's success status is not itself proof all five source pairs were accessible or identical: inspect `compared_count`, `compare_state` and each per-path `identical_bytes` before drawing a conclusion.

**Unresolved:** AOSP and Lineage source matches (if any) do not establish the actual stock factory image contents, downstream `modemsmem` probe completion or MPSS firmware start order. This step does not modify the Pixel 5a, enable remoteproc or publish SMEM. Following the CI run, record verified hashes and changed-line counts and narrow any future source audit to demonstrated differences. Do not call an offline text comparison a kernel/firmware runtime qualification.

### Step 792 verified byte-comparison results

GitHub public-source workflow **#11** (run `43920100174`) completed SUCCESS and compared **all 15** allowlisted AOSP Android 12L vs pinned LineageOS source pairs (five files times three tags; zero unavailable pairs). The AOSP versions are byte-identical across sampled tags `android-12.1.0_r1`, `r5` and `r7`, but only **two of five files match pinned LineageOS exactly**:
- **Identical:** Barbet `init.insmod.barbet.cfg` (SHA-256 `a081d17fbfe8995aaf64ee8dfd4e528a13756d1deb3f660f22da55f044fe8383`) and Redbull `init.insmod.sh` (SHA-256 `d6ca82cf42232a1b1e934827e055c024f39f5fdc1def5905b6f131bbb62f0855`).
- **Different:** Barbet `barbet/init.barbet.rc` (AOSP SHA `78a14c15c8c71b5d40c712009711636bbd8505e85419cfec92ec4e15e9bbef4e`; Lineage SHA `080e04c5474e2663cfe056062f08935dcb644f077a8680e867f4164772b66000`; one changed line-opcode hunk).
- **Different:** Redbull `BoardConfig-common.mk` (AOSP SHA `27a623d774cb7818a892d340c9a36aee732f69f4d482b0a73fdf30757fbf5ff3`; Lineage SHA `028dd8dcff8f6f306ab2a09e41617c48ba2c2539c0cbb197861204af3090e581`; 24 changed line-opcode hunks).
- **Different:** Redbull `init.hardware.rc` (AOSP SHA `5cf98b4bab2359a81f5ddf3b10db397f9ff0361ad850733226cc7ed30f21f294`; Lineage SHA `aa992f1b8481afed9ab20de181b76999b03da8910ae394f9795b34b44d81c8bf`; 13 changed line-opcode hunks).

The hunk counts are unreviewed textual differences, **not** findings that a particular modem init instruction changed. `validation/pixel5a-aosp-lineage-12l-comparison-result.json` preserves the GitHub-run result and exact hashes; `tests/pixel5a-aosp-lineage-result-test.py` adds eight negative/baseline checks in both workflows. **The AOSP `modules.load` path remains missing (HTTP 404) in all three public tags and was not one of the five compared paths.** No complete stock vendor_boot image, Pixel 5a boot trace, SMEM publication ordering, or working cellular modem has been verified.

**Step 793 next:** Retrieve and examine the *actual diff hunks* for the three differing public-source paths, determine whether any involve modemsmem, first-stage module policy, property readiness, or peripheral loader sequencing. Preserve all differences as source-only until exact stock image/runtime proof exists; no device operations.

## Step 793 — pinned AOSP/Lineage source-diff hunk review

**Baseline:** Step 792 GitHub phone CI #99 (`43920682296`), real Linux 7.2.6 ARM64 kernel-header compile #40 (`43920682114`) and public source comparison #15 (`43920682183`) passed at commit `faaba01187f71243d6f32c9dd3836d111220d38b`.

**Goal:** Determine what actually changed in the three text files verified as different: `barbet/init.barbet.rc`, `redbull/BoardConfig-common.mk` and `redbull/init.hardware.rc`. Do not infer the semantics of these changes from Step 792's line-hunk counts.

**Method:** `research/pixel5a-modemsmem/inspect_aosp_lineage_12l_diffs.py` limits AOSP to the immutable Android 12L `android-12.1.0_r7` tag, and LineageOS to pinned commits `24101a383bb1951952adcd6f62668338dd048f03` (Barbet) and `9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770` (Redbull). Source-only downloads use the established allowlisted public-text fetcher. Output includes unified line diffs and hashes with `stock_vendor_boot_verified=false`. An unavailable file remains unavailable, never a hypothetical diff. GitHub's source-only workflow independently checks the hashes against Step 792 before accepting the result. The new `tests/pixel5a-aosp-lineage-source-diff-test.py` provides ten offline positive/negative tests in all three GitHub workflows.

**Interpretation pending actual diff logs:** Only source lines retrieved and verified by the CI diff job may support a conclusion about modem module list contents, module-init readiness, boot-device enabling or peripheral loader behavior. Even confirmed AOSP-vs-Lineage source differences do **not** establish stock `vendor_boot.img`, kernel driver probe completion, item134 SMEM publication or MPSS startup timing. AOSP `device/google/redbull/modules.load` was HTTP 404 in all three sampled tags and remains unverified. No firmware, phone partitions or hardware are accessed.

### Step 793 actual source-diff results and CI correction

Source diff workflow run #20 (`43983484332`) **retrieved and printed all three verified public-source unified diffs**, but its final pinned-hash verification step failed because the expected lookup key omitted Barbet's nested `barbet/` directory. That is a CI bookkeeping error, **not evidence of a mismatching source hash**. Fixed the expected key in a subsequent commit; final-head workflow outcomes must be checked separately.

**Review of directly retrieved AOSP `android-12.1.0_r7` versus pinned LineageOS diff text:**
- `barbet/init.barbet.rc`, one changed hunk: LineageOS explicitly adds `user root` to the `vendor.mdm_helper` service; the inspected context retains its command path, `class core`, and groups. This is a service user declaration difference, **not a newly verified item134 publication barrier**.
- `redbull/BoardConfig-common.mk`, 24 changed line-opcode hunks: AOSP has a substantial block calculating `KERNEL_MODULES_LOAD`, `BOARD_VENDOR_RAMDISK_KERNEL_MODULES_LOAD`, `BOARD_VENDOR_KERNEL_MODULES_LOAD` and `BOOT_KERNEL_MODULES_FILTER` from module artifacts/ordered load lists. The corresponding pinned LineageOS *common* file does not have this block; its separate `BoardConfigLineage.mk` uses another load-list filter scheme, so **module packaging behavior can differ**. The diff also shows AVB signing/key wiring and asynchronous-probe kernel-command-line changes. The source comparison does not evaluate the expanded Make variables for an exact stock build, so cannot prove actual module load order or early probe completion.
- `redbull/init.hardware.rc`, 13 changed line-opcode hunks: the differences include charger service declaration, battery/charging and NFC permissions/properties, `vendor.ss_ramdump` folder setup, scheduling/task-profile and storage tuning. Both inspected versions retain `wait_for_prop vendor.all.modules.ready 1` and `wait_for_prop vendor.all.devices.ready 1`. No newly verified `modemsmem`-probe-completion acknowledgment is added in these observed changes.

These are **source differences and reviewer interpretations**, not modem startup runtime proof. No stock factory `vendor_boot.img` or actual kernel boot trace was inspected; the missing public AOSP `redbull/modules.load` path remains a blocker. `validation/pixel5a-aosp-lineage-12l-diff-interpretation.json` records the reviewed distinctions and remaining unknowns; `tests/pixel5a-aosp-lineage-diff-interpretation-test.py` adds eight baseline/negative checks in both phone and ARM64 workflows. Future work must resolve effective generated module lists and compare the relevant downstream MPSS loader sequence without flashing or activating the modem.

## Step 794 — pinned Lineage first-stage module projection and downstream PIL source

**Verified baseline:** Step 793 at `7e7f2f321b0f9d05b8c0b33f5ff41c519b7d3286` passed Android phone validation #109 (`43983808840`), Linux 7.2.6 ARM64 compile-only probe #50 (`43983808824`), and public AOSP/Lineage source diff #25 (`43983808822`). No kernel modem startup was attempted.

**Exact pinned source files:** `LineageOS/android_device_google_redbull` commit `9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770`:
- `BoardConfig-common.mk` (blob `a70253537c0da383ac0c96c9f02f526faba89ef4`) lines 148–156 explicitly says `BOOT_KERNEL_MODULES` defines eligible first-stage `vendor_boot.img` modules and that the supplied kernel's `modules.load` filters and orders those entries; missing modules can be silently dropped. It includes `smem.ko` around line 160, `subsys-pil-tz.ko` around 229, `modemsmem.ko` around 253.
- `BoardConfigLineage.mk` (blob `73921b90f308b6adbf6ba6b0d31c563eedede37e`) adds two boot modules and uses `$(notdir ...)` on `device/google/redbull/modules.load` to create `KERNEL_MODULES_LOAD`. Its `BOARD_VENDOR_RAMDISK_KERNEL_MODULES_LOAD := $(filter $(BOOT_KERNEL_MODULES), $(KERNEL_MODULES_LOAD))` preserves the **input ordered list** for eligible items; `BOARD_VENDOR_KERNEL_MODULES_LOAD := $(filter-out ...)` projects the remaining vendor set. The `BOOT_KERNEL_MODULES` declaration itself **is not the effective load order**.
- `modules.load` (blob `b116d1f234682a1f7e7275f36e6c7a2feb79ddb5`) lists `smem.ko` before `subsys-pil-tz.ko`, which in turn occurs before `modemsmem.ko`. This is a **source-list ordering** only, not evidence of how/when kernel platform drivers complete probing or when firmware starts.
- `init.insmod.sh` (blob `a222838cc855392838a69fbd9ea3951273078658`) invokes `modprobe -a -d /vendor/lib/modules` but does not examine its exit status, and sets `vendor.all.modules.ready=1` and `vendor.all.devices.ready=1` even without the config file. Barbet `init.insmod.barbet.cfg` (commit `24101a383bb1951952adcd6f62668338dd048f03`, blob `f2728df28091a374ff6bfa6e4e50f3695420e722`) requests `modprobe|-b *` and later writes those properties.

**Pinned downstream loader:** `LineageOS/android_kernel_google_redbull` commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `drivers/soc/qcom/subsys-pil-tz.c`, blob `f17f9e57b0d1f671017032df9224ada0bbea15c2`. `subsys_powerup()` (around lines 856–867) calls `pil_boot(&d->desc)`; the platform probe around line 1271 calls `subsys_register`, and the platform driver registers around line 1321. These are a distinct **downstream Qualcomm PIL/SSR** framework, not automatically the mainline Linux 7.2.6 PAS remoteproc path. Neither the observed module list nor the inspected loader has verified a dependency on modemsmem item134 publication completion.

**CI reproducibility:** Added `research/pixel5a-modemsmem/project_lineage_module_load.py` to fetch six allowlisted pinned public *text* files, compute the specific Lineage Make `filter`/`filter-out` first-stage projection from actual `BOOT_KERNEL_MODULES` and `modules.load` data, report the three watched items' source-list positions, and check for the reviewed PIL method references. Its structured output explicitly marks stock `vendor_boot`, probe completion, and modem-start order unverified. `tests/pixel5a-lineage-module-projection-test.py` provides ten offline synthetic and negative tests (including reversed ordering, missing items, duplicate basenames, and loader readiness not being a probe acknowledgement); added to all three workflows. The public AOSP source workflow also runs the live pinned-source projection and uploads metadata only.

**Limits:** This models specific pinned Lineage Make expressions; it is not a complete GNU Make/Soong invocation, compiled module dependency resolution, real init-module insertion, first-stage ramdisk extraction, Qualcomm PIL runtime trace, or proof of vendor SMEM write visibility. The **AOSP Android 12L `redbull/modules.load` tagged path remains missing (404)**; the Lineage first-stage projection must not be relabeled stock. No firmware files, device partitions, active module images, or Pixel 5a hardware were accessed.

**Next:** Use the actual computed module projection numbers from CI; then inspect `subsys_register` / PIL boot triggers and their device-tree/early userspace integration to identify any real driver-order barriers rather than relying on module list position.

### Step 794 source projection result (exact pinned Lineage text)

A direct independent evaluation of the pinned `BoardConfig-common.mk`, `BoardConfigLineage.mk` and `modules.load` texts yielded **329** ordered module basenames, **219** declared common first-stage eligible names, and two additional Lineage entries. Projecting the ordered module list through the union of first-stage eligible basenames yielded **220 first-stage entries** and **109 vendor entries** (not a complete Soong/Make build result).

The three watched module positions in the **ordered source list**, zero-based, are `smem.ko=34`, `subsys-pil-tz.ko=53`, `modemsmem.ko=83`; in the **projected first-stage list** they are `30`, `47`, `74` (human positions #31, #48, #75). Thus source list sequence is `smem` → `subsys-pil-tz` → `modemsmem`. No inference is permitted about firmware start order, driver probe completion or visibility of the vendor SMEM item134 payload.

These figures are pinned in `validation/pixel5a-lineage-first-stage-module-projection.json` and protected by `tests/pixel5a-lineage-first-stage-evidence-test.py`, integrated with all three CI workflows. The GitHub source-only workflow is additionally configured to recalculate them from immutable pinned public source references; its live outcome must be independently checked. **Absent actual factory-image module lists, exact build-dependent module artifacts and kernel probe logs, these are NOT stock Pixel 5a boot facts.**

## Step 795 — downstream PIL registration versus actual power-up trigger

**Baseline:** At Step 794 commit `c2930266972547e44c2a05fbf85224897867388c`, the project source-only module projection was documented (329 listed modules, 220 modeled first-stage, 109 vendor); GitHub commit-run lookup did not return any new Step 794 workflow runs at the time, so it was not presented as CI-validated. Step 793 runs were last confirmed successful. Step 795 should not claim Step 794 CI succeeded without separately observing a matching workflow run.

**Pinned source**: `LineageOS/android_kernel_google_redbull` commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`:
- `drivers/soc/qcom/subsys-pil-tz.c` Git blob `f17f9e57b0d1f671017032df9224ada0bbea15c2`: probe assigns `d->subsys_desc.powerup = subsys_powerup` around line 1158 and invokes `subsys_register(&d->subsys_desc)` around 1271. The powerup callback itself calls `pil_boot(&d->desc)` around 865. **The reviewed probe registration path is not itself a direct `pil_boot()` call.**
- `drivers/soc/qcom/subsystem_restart.c` Git blob `e304cb58b65037237b2a231a52dadb3bccd618c7`: `subsys_register()` (around 1896–2014) publishes the subsystem device and its registration/notification and IRQ machinery; `__subsystem_get()` (around 1031–1077) recursively handles `subsys->desc->pon_depends_on`, then invokes `subsys_start()` when its reference count is initially zero; `subsys_start()` (around 899–920) calls `subsys->desc->powerup()`. A separate recovery path also invokes the callback. The optional dependency name is read from DT property `qcom,pon-depends-on` in `subsys_parse_devicetree()` (around 1759–1761).
- `drivers/soc/qcom/peripheral-loader.c` Git blob `c7920af7ab0c010c24078c72809a5d83667ce765` owns `pil_boot()` around 1220. The PIL loader is a separate downstream architecture from the previously audited Linux 7.2.6 `qcom_q6v5_pas` remoteproc.
- `qcom,smem-id` consumed by `subsys-pil-tz.c` (around 1099–1110) is used in the inspected source for crash-reason lookup. There is **no basis to identify it with vendor SMEM item134 or to infer that it is a publication fence**.

**Caveat:** This review establishes how subsystem registration and `subsystem_get()` can trigger downstream powerup. It has **not** traced all users of `subsystem_get("modem")`, the Pixel 5a's final DT node/property values, which particular subsystem boots first under Android 12L, firmware start timings, or memory-visibility guarantees for vendor item134. A `qcom,pon-depends-on` property can create a dependency between named subsystems, but its existence in the framework does not prove a dependency on the modemsmem platform driver. The source-derived module list order is not driver probe order.

**Artifacts:** `validation/pixel5a-downstream-pil-start-trigger-audit.json` pins the exact three downstream blobs, source-backed start-trigger facts, unresolved barriers and no-activation permissions. `tests/pixel5a-downstream-pil-start-trigger-test.py` provides eight baseline/negative tests, wired into the three GitHub workflows. No firmware, device tree, kernel module or modem is deployed or started; all phone capability statuses remain untested.

**Step 796:** inspect specific Pixel 5a / Lito modem PIL DT nodes and consumers of `subsystem_get("modem")` in the pinned downstream tree, and distinguish registration, demand-triggered boot, and crash recovery without altering the running handset.

## Step 796 — Lito modem PIL DT node and conditional modem startup requester

**Baseline:** Step 795 head `df6488298061d76479c527f9fc7acbae00cbb8fd` was verified with Android validation #114 (`44228519107`), Linux 7.2.6 isolated ARM64 compile #55 (`44228519131`) and pinned AOSP/Lineage public-source workflow #30 (`44228518930`), all successful.

**Pinned DT evidence:** `LineageOS/android_kernel_google_redbull`, commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `arch/arm64/boot/dts/vendor/qcom/lito.dtsi`, blob `24b013a4b166456be0a1f8a4a278d9fb3dcfccd1`, lines ~2753–2807 declares `pil_modem: qcom,mss@4080000`, `compatible = "qcom,pil-tz-generic"`, `qcom,firmware-name = "modem"`, `qcom,pas-id = <4>` and `qcom,smem-id = <421>`. The **421 item is for subsystem crash-reason lookup** in the inspected `subsys-pil-tz.c` path, not vendor item 134 created by `modemsmem`. The inspected node does **not** declare `qcom,pon-depends-on` or a modemsmem-publication dependency. That is a statement about this source node, not a proof that no included DT overlay adds one. The Google `lito-barbet-common.dtsi` includes `lito-redbull-common.dtsi` (blob `4aeed8583a96230c89b11ac85ec6b156abadc2db`) but the **final flattened Barbet DTB is not verified** and the complete include graph has not been evaluated.

**Concrete source-level modem boot requester:** `techpack/audio/dsp/adsp-loader.c`, blob `a32acfd359092d4a8cdbcb2da804d0ec8601da0b`, `adsp_load_fw()` around lines 78–115 reads `qcom,proc-img-to-load`; if `"modem"` and `apr_get_modem_state() == APR_SUBSYS_DOWN`, it calls `subsystem_get("modem")` then marks APR modem state loaded on success. The routine is scheduled via a workqueue. This is a **real conditional call site**, not evidence the branch runs for the final Pixel 5a DT, nor proof that this is the only caller of modem start. Downstream `subsystem_restart.c` then takes the previously audited `subsys_start` → `powerup` → `pil_boot` path on an initial request, subject to its framework conditions and failure handling.

**Implications:** Module-list ordering and a named PIL subsystem cannot guarantee vendor SMEM item134 was initialized, flushed or accepted before a caller requests firmware start. The actual Barbet `qcom,proc-img-to-load` property value, full DT overlay graph, possible other callers, driver probe status, stock `vendor_boot.img` and MPSS hardware behavior remain unresolved.

**Deliverables:** `validation/pixel5a-lito-modem-pil-dt-caller-audit.json` pins immutable DT/loader source hashes, observed conditional call path and unresolved assumptions; `tests/pixel5a-lito-modem-pil-dt-caller-test.py` contains eight baseline/negative tests, now called by all three GitHub workflows. No actual modem start, firmware access, image extraction, phone operation, write to SMEM or driver registration is performed.

**Step 797 suggested focus:** Resolve exact Barbet audio/ADSP loader DT properties and overlays and search downstream modem start callers, with pinned source-only evidence. The mainline Linux 7.2.6 PAS remoteproc port must remain separately reviewed before any integration or device action.

## Step 797 — Barbet/Lito ADSP loader configuration and conditional modem branch

**Baseline:** Step 796 GitHub Android phone validation #119 (`44229560313`), source inspection #35 (`44229560417`) and Linux 7.2.6 ARM64 compile #60 (`44229560308`) all completed SUCCESS on `555eda35de05527bb6af09d1bb86fd30886e0ffb`. No active modem testing occurred.

**Pinned kernel source** `LineageOS/android_kernel_google_redbull` at `929e7e2f3658867d51a1d423c7e000f5cf1d4043`:
- `arch/arm64/boot/dts/vendor/qcom/msm-audio-lpass.dtsi`, blob `a9496d85ef337acf1802bccd1cbeb73e47acae7e`, lines 531–535: `adsp_loader: qcom,msm-adsp-loader` is `status = "ok"`, `compatible = "qcom,adsp-loader"`, with `qcom,adsp-state = <0>`. The inspected node **does not** set `qcom,proc-img-to-load = "modem"`.
- `arch/arm64/boot/dts/vendor/qcom/lito-audio.dtsi`, blob `b0c71b6bef60277d3bd694ab21b3b52616ea9529`, includes `msm-audio-lpass.dtsi`.
- `arch/arm64/boot/dts/google/lito-redbull-audio.dtsi`, blob `6fc430fff036faed2c92217aace7e3be2455985e`, includes `qcom-base/lito-audio-overlay.dtsi`; its pinned vendor source is `arch/arm64/boot/dts/vendor/qcom/lito-audio-overlay.dtsi`, blob `d40caafaa79af5726f4cdae22a4992d36a84c5d4`. Its `&adsp_loader` override at 487–491 adds `nvmem-cells` for `adsp_variant`, `adsp-fw-names = "adsp2"`, and bit values. The inspected override **does not** set the loader image property to `"modem"`.
- `arch/arm64/boot/dts/google/lito-barbet-audio.dtsi`, blob `b8b9b41e3de01936a851ed33d1c592684f7374e2`, was inspected; no direct `qcom,proc-img-to-load = "modem"` assignment was found there.
- In `techpack/audio/dsp/adsp-loader.c`, blob `a32acfd359092d4a8cdbcb2da804d0ec8601da0b`, `adsp_load_fw()` reads `qcom,proc-img-to-load`; if absent, it follows the `load_adsp` branch, not the `subsystem_get("modem")` branch. The latter exists but requires an explicit `"modem"` property and an APR state of `APR_SUBSYS_DOWN`. This is a **conditional code branch, not proof of Pixel 5a modem activation**.

**Important remaining uncertainty:** The inspected DT source subset does not constitute a final preprocessed/flattened Pixel 5a DTB or verify that no other include, overlay or runtime property enables `qcom,proc-img-to-load = "modem"`. The exact boot firmware start, userspace trigger, possible nonliteral `subsystem_get` callers, vendor SMEM item 134 publication barrier and recovery remain unknown. Even if these specific DT nodes default to ADSP loading, a different component may request MPSS startup.

**Artifacts:** `validation/pixel5a-adsp-modem-loader-config-audit.json` pins six source blobs and records precisely scoped source observations. `tests/pixel5a-adsp-modem-loader-config-test.py` adds ten negative/baseline tests in all three GitHub workflows. No flashing, SMEM allocation/write, module load, modem boot, device access or firmware download is performed.

**Next:** Resolve the complete Barbet flattened DT source include graph and inspect nonliteral subsystem-get callers and early userspace modem-load policy. Do not enable an active driver before establishing a safe modemsmem publication/start barrier.

## Step 798 — Barbet audio include chain and nonliteral modem-start call sites

**CI baseline:** Step 797 at `89f5153942ee120db0b2386e3cfd586b1eb4c9a2`: Android validation #124 (`44423649119`), Linux 7.2.6 ARM64 compile #65 (`44423649905`), and pinned source workflow #40 (`44423649369`) all passed.

**Directly inspected pinned Linux downstream tree:** `LineageOS/android_kernel_google_redbull`, `929e7e2f3658867d51a1d423c7e000f5cf1d4043`.

The **source include chain** passes from `lito-barbet.dtsi` to `lito-barbet-common.dtsi`, then `lito-redbull-common.dtsi`, and then `lito-redbull-audio.dtsi`, whose source includes `qcom-base/lito-audio-overlay.dtsi`. Separate pinned vendor text `msm-audio-lpass.dtsi` declares an enabled `adsp_loader` and `lito-audio-overlay.dtsi` adds NVMEM-backed `adsp2` firmware selection. Neither inspected node nor overlay explicitly selects `qcom,proc-img-to-load = "modem"`. This is **not a full flattened DTB**: the exact `qcom-base` include mapping and all preprocessor or later overlay overrides have not yet been verified.

**Bounded callsite search of the pinned downstream kernel:**
- `techpack/audio/dsp/adsp-loader.c`, blob `a32acfd359092d4a8cdbcb2da804d0ec8601da0b`, has the literal conditional `subsystem_get("modem")`. Its code also provides a sysfs boot command which schedules a worker, but the command is not evidence that a phone actually uses the modem branch. The loader probe initializes the workqueue; it does not directly call `subsystem_get("modem")`.
- `drivers/platform/msm/ipa/ipa_v3/ipa.c`, blob `f03dc32340af1e5b57ab0356b71c8700ff7e1bdb`, calls `subsystem_get(sub_sys)` with a variable argument. **Its effective value on Barbet was not traced in this step**; it cannot be declared a modem start merely because a variable is passed.
- `drivers/net/wireless/cnss2/main.c`, blob `1d38cdf05733fd9e1ca044c3aa087202737f6dad`, uses `subsystem_get(subsys_info->subsys_desc.name)`; the inspected initialization sets that descriptor name to `"wlan"`, so this evidence concerns WLAN, not a demonstrated modem trigger.
- `drivers/gpu/msm/adreno_a6xx.c` uses `subsystem_get(a6xx_core->zap_name)` for GPU firmware, another dynamic-name call that should **not** be classified as a modem call without tracing its value.
- A second potential modem implementation is present in `drivers/soc/qcom/pil-q6v5-mss.c`, blob `db48b1a2117162dbd0c893c9c9a49c74838805c8`, whose descriptor name is `"modem"`. Its existence **does not establish that it binds in the Barbet configuration**. The pinned Lito source node examined previously uses `qcom,pil-tz-generic`.

These findings are pinned in `validation/pixel5a-barbet-dt-indirect-modem-caller-audit.json`; ten fail-closed regression cases in `tests/pixel5a-barbet-dt-indirect-modem-caller-test.py` run in all three GitHub workflows. This is a **bounded code-search and inspected-source audit**, not a complete call graph, evaluated final DT, stock Android 12L boot image, active kernel or hardware boot trace.

**Step 799:** Trace how the IPA `sub_sys` argument is assigned and whether its code path can request `"modem"` on this device; inspect the final DT include preprocessing/overlay mapping independently. Preserve separate investigations of vendor SMEM item134 ownership/publication, PIL registration and crash recovery. Do not enable any modem or module on the working Pixel 5a.

## Step 799 — IPA dynamic PIL argument defaults and Barbet MP overlay Make mapping

**Baseline** at Step 798 head `c1677dde400711cd401a868be6e87f3405a451df`: Android phone validation #129 (`44426247711`), Linux 7.2.6 ARM64 compile-only #70 (`44426247697`) and AOSP/Lineage source inspection #45 (`44426247708`) all completed SUCCESS.

**Pinned kernel source:** `LineageOS/android_kernel_google_redbull` commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`.

**IPA dynamic name resolution in the inspected source:** `drivers/platform/msm/ipa/ipa_v3/ipa.c`, blob `f03dc32340af1e5b57ab0356b71c8700ff7e1bdb`. `ipa3_pil_load_ipa_fws(const char *sub_sys)` calls `subsystem_get(sub_sys)` around line 6314. The two default callsite arguments are defined in this source at lines 53–54: `IPA_SUBSYSTEM_NAME = "ipa_fws"`, `IPA_UC_SUBSYSTEM_NAME = "ipa_uc"`. In `ipa3_load_ipa_fw()` around lines 6339–6352, the primary firmware path chooses `ipa3_ctx->gsi_fw_file_name` when populated and the default `ipa_fws` otherwise, with a separate manual firmware-load path for the other mode. Around lines 6371–6388, the IPA uC branch is conditional on APQ platform/mode and chooses `ipa3_ctx->uc_fw_file_name` when populated or default `ipa_uc` otherwise. **Neither default literal is "modem".** However, the originating assignments and effective values of those two optional firmware-name fields on Barbet have not been proven, so a runtime use of the dynamic name must not be assumed or excluded.

**Barbet MP overlay build path:** `arch/arm64/boot/dts/google/Makefile`, blob `852a844e147eba2dc9f2a2cf7b2483ff3e91894e`, line 90 maps `lito-v2-barbet-mp-overlay.dtbo` to `qcom-base/lito-v2.dtb`. `arch/arm64/boot/dts/google/lito-v2-barbet-mp-overlay.dts`, blob `12c699a75dd1e8d3815e98b0e0ba59e454f14c08`, includes `lito-v2-barbet-mp.dtsi`, which in turn includes `lito-barbet.dtsi` (blob `277ae16bb06ebb5c945fe02a579298af45aba3ff`). This resolves a specific **source/build include chain**, not the choice of installed device variant, final compiled flattened DTB, overlay application, audio `qcom-base` include mapping or runtime `qcom,proc-img-to-load`.

**Artifacts:** `validation/pixel5a-ipa-subsystem-name-barbet-overlay-audit.json` records the pinned exact source IDs, defaults, override gaps and the observed overlay build mapping. `tests/pixel5a-ipa-subsystem-name-barbet-overlay-test.py` includes ten baseline/negative checks in all three GitHub Actions workflows. In particular, the tests reject relabeling IPA's default `ipa_fws`/`ipa_uc` calls as `modem`, promoting source files into a verified runtime DTB, erasing untraced override assignments or authorizing firmware startup.

**Step 800 next:** Locate the code that populates `gsi_fw_file_name` and `uc_fw_file_name` and their exact Lito/Barbet DT property inputs, then inspect the chosen `qcom-base` audio mapping with a source-only include/Make audit. Keep modemsmem vendor item 134 publication and MPSS firmware start order unverified. No phone changes.

## Step 800 — pinned IPA firmware override property-to-PIL argument provenance

**Baseline:** Step 799 at commit `d4325a73ea2876da3273c12c35cc2d3945721144` had phone CI #134 (`44430329887`) and public source CI #50 (`44430329906`) SUCCESS. The separate Linux 7.2.6 ARM64 probe #75 (`44430329893`) was still in progress at the time of this audit; its result must not be assumed green without a separate completed GitHub run.

**Pinned code** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043` `drivers/platform/msm/ipa/ipa_v3/ipa.c` (Git blob `f03dc32340af1e5b57ab0356b71c8700ff7e1bdb`):
- Around lines 7565–7576, `of_property_read_string` reads `qcom,use-gsi-ipa-fw` into `ipa_drv_res->gsi_fw_file_name` and `qcom,use-uc-ipa-fw` into `ipa_drv_res->uc_fw_file_name`. When missing it reports use of default firmware, rather than assigning a literal modem subsystem.
- Around lines 6743–6769, `ipa3_ctx` copies these optional strings from the resource fields to `ipa3_ctx->gsi_fw_file_name` and `ipa3_ctx->uc_fw_file_name`.
- In `ipa3_load_ipa_fw` around lines 6346–6350 and 6380–6384, optional context strings reach `ipa3_pil_load_ipa_fws()` instead of the fallbacks `IPA_SUBSYSTEM_NAME="ipa_fws"` or `IPA_UC_SUBSYSTEM_NAME="ipa_uc"`. `ipa3_pil_load_ipa_fws(const char *sub_sys)` passes the selected name to `subsystem_get(sub_sys)`. **Neither default is "modem"**.
- A bounded pinned-repository source search shows `qcom,use-gsi-ipa-fw` assignments for other SoCs (`scuba.dtsi` uses `"scuba_ipa_fws"`; `lagoon.dtsi` uses `"lagoon_ipa_fws"`) and the IPA source/bindings, **but no direct assignment in returned Lito/Barbet source paths**. Absence from this source search is **not proof** that a final preprocessed Barbet DTB or a runtime override lacks those properties.

**Build mapping:** The pinned Google DT Makefile maps `lito-v2-barbet-mp-overlay.dtbo` onto `qcom-base/lito-v2.dtb`. Complete `qcom-base` include mapping, chosen device overlay variant, compiled DTBO, installed DTB and effective IPA node properties are **not** established.

**Artifacts:** `validation/pixel5a-ipa-firmware-name-property-provenance.json` records exact source provenance, the full source property → resource → context → PIL argument chain, other-SoC examples, absent runtime proof and safety locks. `tests/pixel5a-ipa-firmware-name-property-provenance-test.py` adds ten baseline/negative checks to all three GitHub Actions workflows. The new tests must not be mistaken for a running modem experiment.

**Step 801:** Verify the Lito/Barbet IPA DT node and any variant overrides directly from pinned source and (if possible) the build include mapping. Separately identify whether any actual modem start caller has a dependency on `modemsmem` item134 publication. No Android device/firmware modifications.

## Step 801 — Lito IPA hardware and IPA firmware PIL nodes (source-only)

**Baseline**: Step 800 public source workflow #55 (`44432284863`) and phone validation #139 (`44432284823`) both succeeded at `76721c45d82efb084837956acf8f43c931e01a76`. The Linux 7.2.6 ARM64 compile #80 (`44432284810`) was still marked in progress in the GitHub commit-run lookup at the start of Step 801. Its status is a separate verification gate, not assumed successful.

**Pinned source**: `LineageOS/android_kernel_google_redbull` commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `arch/arm64/boot/dts/vendor/qcom/lito.dtsi` (Git blob `24b013a4b166456be0a1f8a4a278d9fb3dcfccd1`), lines ~3546–3578:
- The `qcom,ipa_fws` node declares `compatible = "qcom,pil-tz-generic"`, `qcom,pas-id = <0xf>` (15), and `qcom,firmware-name = "ipa_fws"`. This is an IPA firmware subsystem, **not a modem-named PIL node**.
- The separate `ipa_hw: qcom,ipa@1e00000` node has `compatible = "qcom,ipa"`, `qcom,ipa-hw-ver = <18>` (IPAv4.7) and `qcom,platform-type = <1>` (MSM). In the directly inspected `lito.dtsi` source node no `qcom,use-gsi-ipa-fw` nor `qcom,use-uc-ipa-fw` assignment appears.
- `arch/arm64/boot/dts/vendor/qcom/lito-v2.dtsi` (blob `97affc51181d437ee4d37797b261b41c5fe00e24`) includes `lito.dtsi`; `lito-v2.dts` (blob `a3da016a653d65cb310deb32aa2895615fb8b7f1`) includes `lito-v2.dtsi`. Direct inspection of those and the pinned Google `lito-redbull-common.dtsi`, `lito-barbet-common.dtsi` and `lito-v2-barbet-mp.dtsi` did not reveal these optional IPA firmware-name property overrides.

**Interpretation:** The inspected Lito source is consistent with using `ipa_fws` / `ipa_uc` default names from the Step 800 code audit, rather than an IPA-initiated `subsystem_get("modem")`. This does **not** prove complete DT preprocessing, actual Barbet overlay choice, built DTB contents, effective runtime property values, eventual IPA firmware load, or that no other component requests modem startup. The separate Lito modem PIL node, as audited in Step 796, remains distinct from the IPA firmware PIL node; no driver/module list or source-level IPA finding is proof of MPSS startup after modemsmem vendor item 134 publication.

**Artifacts:** `validation/pixel5a-lito-ipa-node-source-audit.json` pins the six inspected blobs, IPL/IPA hardware node properties, no direct overrides in reviewed source files, and unresolved runtime constraints. `tests/pixel5a-lito-ipa-node-source-test.py` has ten baseline/negative cases, incorporated into all three GitHub workflows. No stock boot archive, phone partition, firmware, active driver or hardware is accessed.

**Step 802:** Continue a pinned, read-only review of Lito modem PIL driver selection, the device-tree subsystem dependency graph and any first-boot requesters. Require an evidence-backed item134 initialization/visibility fence before considering kernel integration; do not perform live modem tests without separate approval.

## Step 802 — pinned Lito modem PIL binding and unproven publication dependency

**Baseline:** Step 801 at `c2e077c66c17ee2797707ac9c97c1da97361287f`: Android validation #143 (`44433989595`), Linux 7.2.6 isolated ARM64 compile probe #84 (`44433989561`) and official source workflow #59 (`44433989587`) all passed. These results test host/source/compile-only behavior, not the phone.

**Pinned Qualcomm downstream source**: `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`.
- `arch/arm64/boot/dts/vendor/qcom/lito.dtsi` blob `24b013a4b166456be0a1f8a4a278d9fb3dcfccd1`: `pil_modem: qcom,mss@4080000` at lines 2753–2807 declares `compatible = "qcom,pil-tz-generic"`, `qcom,firmware-name = "modem"`, `qcom,pas-id = <4>`, `qcom,smem-id = <421>`; the latter identifies a crash-reason SMEM lookup in the inspected driver, **not** vendor item134. The directly inspected node does not declare `qcom,pon-depends-on` or a dependency indicating completion of item134 publication.
- `drivers/soc/qcom/subsys-pil-tz.c` blob `f17f9e57b0d1f671017032df9224ada0bbea15c2` registers a platform driver with OF match `qcom,pil-tz-generic` (lines ~1304–1323), matching the Lito modem node. Its probe reads `qcom,firmware-name`, copies that name into `subsys_desc.name`, installs `subsys_powerup` and calls `subsys_register`. Thus the source makes the named `modem` subsystem available; **registration itself does not call `pil_boot`**.
- `drivers/soc/qcom/subsystem_restart.c` blob `e304cb58b65037237b2a231a52dadb3bccd618c7`: `__subsystem_get("modem", ...)` finds a named registered subsystem, attempts the optional `pon_depends_on` subsystem reference, and starts its powerup on the initial zero reference count; the PIL powerup callback invokes `pil_boot`. This framework behavior does **not** prove any specific component actually invoked the first `subsystem_get("modem")` in the Pixel 5a boot sequence.
- `drivers/soc/qcom/pil-q6v5-mss.c` blob `db48b1a2117162dbd0c893c9c9a49c74838805c8` includes a distinct modem subsystem implementation, but its OF compatible values (`qcom,pil-q6v5-mss`, `qcom,pil-q6v55-mss`, `qcom,pil-q6v56-mss`) do not match the inspected Lito `qcom,pil-tz-generic` node. Do not conflate alternate downstream Qualcomm modem paths or the new mainline 7.2.6 remoteproc PAS path.

**Most important unresolved barrier:** The examined Lito modem node provides no explicit item134 publication completion fence. Even when the `subsys-pil-tz` driver binds and registers the modem name, module insertion, platform-probe completion, firmware start, and ownership/visibility of item134 remain separate states. No concrete MPSS startup requester, final flattened Barbet DT overlay or successful runtime sequencing has been proven. A future device bring-up must obtain an actual ordering/visibility guarantee before enabling the modem.

**Deliverables:** `validation/pixel5a-lito-modem-pil-binding-dependency-audit.json` pins four source blobs, exact modem node identity, binding and start callbacks, and remaining blockers. `tests/pixel5a-lito-modem-pil-binding-test.py` adds ten baseline/negative checks in all three GitHub workflows. No stock image, firmware or Pixel 5a hardware was accessed.

**Step 803:** Examine the pinned downstream modem startup callers outside the literal ADSP branch and any userspace-triggered initial subsystem request. Trace the actual `modemsmem` probe completion/publication contract as a separate safety requirement. Preserve all hardware gates and keep PR #18 draft.

## Step 803 — downstream modemsmem item 134 reset, ownership and first-start uncertainty

**Baseline:** At Step 802 head `a6aadc310ba4215d77be85db25caff40af73f99d`, official AOSP/Lineage source workflow #65 (`44435508936`) succeeded and Android phone validation #149 (`44435508940`) succeeded. Linux 7.2.6 ARM64 probe #90 (`44435508838`) was still running when checked at the beginning of Step 803; its latest result must be checked separately.

**Pinned downstream Google/Qualcomm tree**: `LineageOS/android_kernel_google_redbull` commit `929e7e2f3658867d51a1d423c7e000f5cf1d4043`.
- `arch/arm64/boot/dts/google/lito-redbull-common.dtsi` blob `9eea9dc7431c5ef6cc68f100789402c025b558ce` includes a `modemsmem { compatible = "modemsmem"; }` node, distinct from the Lito PIL modem node.
- `drivers/soc/qcom/modemsmem/modemsmem.h` blob `a6b9d991fe7c023f44c21cc5c597746414c532a2` defines `SMEM_ID_VENDOR0 = 134` and `struct modem_smem_type` as 16 32-bit words (64 bytes), with fields for version, SOC IDs, flags, factory test mode and DSDS mode.
- `drivers/soc/qcom/modemsmem/modemsmem.c` blob `428143562894e6d8ca7b656174c72ee4b096f510`, `modem_smem_probe()` lines ~173–188: `qcom_smem_alloc(QCOM_SMEM_HOST_ANY, SMEM_ID_VENDOR0, sizeof(...))` treats `-EEXIST` as acceptable; `qcom_smem_get(...)` checks pointer and exact size; then it **unconditionally executes `memset_io(modem_smem, 0, sizeof(*modem_smem))`**, even after the accepted `-EEXIST` case. Lines ~190–240 write version, SOC platform IDs, optional bootmode / modem flag and DSDS fields. This is a source-level **whole-item reset on successful probe**, not evidence that it is safe for all possible MPSS firmware states, ownership or restart sequences.
- Lines ~242–248 attempt the sysfs attribute group but return 0 even if that creation fails. No explicit `modemsmem publication complete` callback, event or dependency on `subsys-pil-tz` powerup appears in this probe. Module registration is not equivalent to successful probe completion.
- Bounded modem-start search found the previously documented conditional literal `subsystem_get("modem")` in `techpack/audio/dsp/adsp-loader.c` (blob `a32acfd359092d4a8cdbcb2da804d0ec8601da0b`). `drivers/soc/qcom/bam_dmux.c` (blob `c6ec3156c17e0b50f1405434a46d92054715b1fd`) contains an explicit `subsystem_restart("modem")` during fatal interaction handling. A *restart* call is not proof of the initial boot requester or proof that item134 is republished after a crash. No concrete first-boot caller has been verified.

**Safety significance:** The existing-item reset behavior introduces an **ownership and reinitialization hazard** to investigate before any upstream/mainline port. Copying this probe into Linux 7.2.6 or enabling a new SMEM writer without knowing existing owners, write visibility, modem firmware expectations and restart timing is not authorized. Neither the ordered Lineage module list nor `vendor.all.modules.ready` guarantees that the 64-byte payload is fully written before MPSS starts. Even a successful driver probe would not by itself prove firmware consumed the expected data, so an appropriate dependency/handshake must be demonstrated before considering hardware bring-up.

**Deliverables:** `validation/pixel5a-modemsmem-publication-first-request-audit.json` pins the exact source, bounded startup/restart findings, and unresolved item134 ownership and memory ordering. `tests/pixel5a-modemsmem-publication-first-request-test.py` adds ten baseline/negative tests in all three GitHub workflows. No SMEM write, modem start, module insertion, device access, firmware download or phone flash was performed.

**Step 804 suggested next:** Audit the exact pinned `qcom_smem_alloc`/`qcom_smem_get` existing-item semantics and any driver-side memory ordering, and trace first modem requests beyond literal `subsystem_get("modem")`. Preserve no-device-action gates until a publication and ownership contract is established.

## Step 804 — Qualcomm SMEM allocator metadata barriers are not modem item134 readiness

**Verified Step 803 baseline:** commit `d59f94bac39270b4c557cb61a149524a56c8e614`, Android validation #154 (`44437233906`), public source #70 (`44437233895`), and Linux 7.2.6 ARM64 inactive compile #95 (`44437233805`) all SUCCESS.

**Exact source:** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043` `drivers/soc/qcom/smem.c` blob `de4d8aba7e366d5a3594731674dcfa310b3a8713`.
- `qcom_smem_alloc_private()` around lines 368–435 scans partition entries and returns `-EEXIST` when an item ID is already present, without establishing the original allocator's identity. The `wmb()` at ~426 orders a **new entry header** before advancing `offset_free_uncached`, explicitly to let unlocked readers see consistent partition metadata.
- `qcom_smem_alloc_global()` around 437–468 similarly returns `-EEXIST` for a previously allocated entry. Its `wmb()` at ~461 orders global table header fields before marking `allocated=1`. Neither allocator barrier orders the later modem payload writes relative to MPSS boot.
- `qcom_smem_alloc()` ~479–516 returns `-EPROBE_DEFER` if SMEM infrastructure is not initialized, rejects fixed/static entry allocation, uses the hardware spinlock, and selects an available private/global partition. The lock protects **allocation metadata** for participating processors; it is not a proof of later 64-byte payload initialization or that the modem has consumed it.
- `qcom_smem_get()` ~683–717 likewise uses the hardware spinlock to resolve a pointer and item size, returning errors for failed lookups. Global lookup verifies the allocated marker; private lookup validates range/canary/size. Neither returns a firmware-side readiness acknowledgement, original owner identity, publication generation, or payload status.

**Connection to item134:** The inspected `modemsmem.c` blob `428143562894e6d8ca7b656174c72ee4b096f510` accepts `-EEXIST`, resolves the same 64-byte item134, then unconditionally clears it with `memset_io` and rewrites fields. This is **not guarded by any allocator-provided payload publication-complete callback, explicit modem consumer handshake, or verified firmware start dependency**. Existing-item handling is not ownership arbitration; a concurrent or restart-time writer/reader requires separate investigation. Avoid copying that reset pattern into mainline 7.2.6 without a documented ownership and restart protocol.

**Deliverables:** `validation/pixel5a-smem-allocator-ownership-ordering-audit.json` pins the source and limits; `tests/pixel5a-smem-allocator-ownership-ordering-test.py` adds ten negative/baseline tests to each of the three GitHub workflows. These tests are source-evidence consistency tests; they do not execute SMEM APIs or access a running phone.

**Step 805:** Inspect the precise `modemsmem` platform probe deferral/error handling and the source-level ordering of the SMEM provider and PIL consumers. Consider a fail-closed, independently checkable publication contract before proposing any kernel change, but do not enable the modem or publish SMEM on the actual Pixel 5a.

## Step 805 — SMEM provider readiness, error translation and proposed fail-closed publication contract

**CI baseline:** Step 804 head `3817b183127d31a6785bdccf61c8bf2380a162b3` had Android phone validation #159 (`44439580807`), AOSP/Lineage public-source #75 (`44439580773`), and Linux 7.2.6 ARM64 inactive kernel API compile #100 (`44439580791`) all SUCCESS.

**Pinned source:** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`; `drivers/soc/qcom/smem.c` blob `de4d8aba7e366d5a3594731674dcfa310b3a8713`, `drivers/soc/qcom/modemsmem/modemsmem.c` blob `428143562894e6d8ca7b656174c72ee4b096f510`, and `drivers/soc/qcom/subsys-pil-tz.c` blob `f17f9e57b0d1f671017032df9224ada0bbea15c2`.

- The SMEM platform driver uses `arch_initcall(qcom_smem_init)` around line 1242 and registers an OF-compatible `qcom,smem` driver. This *does not prove its platform probe finished* before separate loadable modem or PIL modules bind.
- The SMEM provider's probe around lines 1140–1211 maps the shared-memory table, confirms bootloader/SBL initialization, obtains a hardware spinlock, checks the SMEM version and partition setup, then assigns `__smem = smem` near the successful exit. Missing/uninitialized provider state causes `qcom_smem_alloc()` to return `-EPROBE_DEFER`, and `qcom_smem_get()` returns `ERR_PTR(-EPROBE_DEFER)`.
- Downstream `modem_smem_probe()` calls the allocator and accepts `-EEXIST` for item 134, but **maps every other allocator error to `-ENOMEM`**. It likewise maps `IS_ERR(pointer)` or mismatched size from `qcom_smem_get()` to `-ENOMEM`. The original `-EPROBE_DEFER` is **not preserved**, so an early probe cannot rely on the driver core's normal deferred-probe semantics based on the original error. The actual device retry outcome is untested.
- A successful SMEM pointer/size lookup is **not a payload-ready guarantee**. The modemsmem probe then resets an existing or new 64-byte item without verifying its original owner and rewrites fields; even `sysfs_create_group()` failure is logged but not propagated. No explicit publication-complete event shared with PIL is present in the inspected probe, nor a verified first MPSS start barrier.

**Proposed integration requirements (NOT implemented):** keep any Armada modem boot disabled by default; establish sole-writer/ownership policy and define permitted reuse of pre-existing item 134; preserve allocator error provenance including `-EPROBE_DEFER`; check exact 64-byte layout and initialization failures; define payload write visibility and a real completion/acknowledgement contract before allowing first MPSS startup; define crash-restart reinitialization behavior; obtain explicit manual authorization before any hardware activation. Merely adding a generic `wmb()` or moving module list entries is not proof of consumption.

**Artifacts:** `validation/pixel5a-smem-provider-probe-publication-contract.json` records pinned source facts and clearly marks the gate as `requirements_only_not_implemented`. `tests/pixel5a-smem-provider-publication-contract-test.py` contains ten source-only baseline/negative tests, incorporated in all three existing GitHub workflows. No kernel publication implementation, SMEM write, modem start or device flashing occurred.

**Step 806:** Review provider/consumer device-tree dependencies and the nearest testable host-only model for probe deferral and safe existing-item behavior. Never enable active modem startup without verifying item 134 ownership, payload visibility, first-start order and restart safety.

## Step 806 — device-tree provider/consumer gap and offline modem publication state model

**Verified Step 805 baseline:** `6ea42a4ba118eab70868462bd648dc328a777aae` — Android phone validation #164 (`44441731062`), pinned AOSP/Lineage source #80 (`44441731055`) and Linux 7.2.6 ARM64 compile-only #105 (`44441731066`) all completed SUCCESS.

**Pinned DT evidence:** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`. `arch/arm64/boot/dts/vendor/qcom/lito.dtsi`, blob `24b013a4b166456be0a1f8a4a278d9fb3dcfccd1`, lines 2510–2513 declares `smem: qcom,smem` with compatible `qcom,smem`, `memory-region=<&smem_mem>`, and hardware lock `hwlocks=<&tcsr_mutex 3>`. The same Lito source around 2753–2807 declares `pil_modem: qcom,mss@4080000`, compatible `qcom,pil-tz-generic`. Separately, `arch/arm64/boot/dts/google/lito-redbull-common.dtsi`, blob `9eea9dc7431c5ef6cc68f100789402c025b558ce`, lines 136–138 declares `modemsmem { compatible = "modemsmem"; }`.

**Dependency interpretation:** The inspected provider node's memory region and hwlock are resources for its provider implementation, **not an explicit dependency on the successful 64-byte vendor item134 payload publication**. The inspected `modemsmem` node has no phandle to the provider, and the inspected PIL modem node has no phandle or `qcom,pon-depends-on` pointing at `modemsmem`. The consumer calls SMEM APIs at probe time, so it functionally depends on a working provider, but the existing consumer translates `-EPROBE_DEFER` into `-ENOMEM` (Step 805). DT declaration order, driver registration, module load and even successful provider probe **do not guarantee** modemsmem payload completion or first MPSS start ordering. No compiled or installed Barbet DTB was inspected, so later overrides are unresolved.

**New host-only policy model:** `research/pixel5a-modemsmem/modem_publication_gate.py` is a pure Python immutable state machine. It has **no** driver, SMEM, firmware, networking, ADB, file mutation or hardware operation. Its simulated `may_start` decision is false unless all independent evidence states are asserted: provider ready, item discovered, owner clearance, existing-item preservation policy, valid payload, payload visibility, explicit acknowledgement, and manual authorization. A provider-loss or crash event immediately revokes authorization, and a recovery review deliberately clears *all* prior evidence, including provider readiness. The model never automatically writes or clears a pre-existing item. **A true simulated decision is not an authorization to boot a real modem.** No actual firmware-side acknowledgement protocol has been identified.

**Artifacts:** `validation/pixel5a-modem-publication-offline-state-model.json` pins the source files and identified DT gaps and explicitly marks this as simulation-only. `tests/pixel5a-modem-publication-state-model-test.py` contains 14 cases including simulated provider deferral, ownership, ordered payload visibility/acknowledgement, manual permission, crash/provider loss, replay prevention and negative cases. All three GitHub workflows run the tests.

**Step 807:** Investigate whether the original Android vendor integration contains any source-visible mechanism for first MPSS startup and whether the downstream `modemsmem` existing-item reset can be replaced by a non-destructive ownership protocol. Continue source-only analysis; no modem bring-up on the Pixel 5a.

## Step 807 — pinned Android Peripheral Manager modem-start policy, not a proven firmware call

**Verified baseline:** Step 806 head `530de065af9ac5b83abeb9aace7dce3669dd974d` passed Android validation #172 (`44443792561`), AOSP/Lineage source #88 (`44443792549`) and inactive Linux 7.2.6 ARM64 compile #113 (`44443792555`). No phone hardware was tested.

**Exact Android source:** `LineageOS/android_device_google_redbull@9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770`.
- `init.hardware.rc`, blob `ec3c3edf7e72fb394bde8e9dc669e4a07ced854b`, lines ~561–584: service `vendor.per_mgr /vendor/bin/pm-service` is declared; when `persist.vendor.modem.esim.reset` equals `done` or `noneed`, Android init starts `vendor.per_mgr`; `sys.boot_completed=1` is a fallback start trigger. The source comment explicitly describes starting Peripheral Manager **to boot the modem** after eSIM reset. `init.svc.vendor.per_mgr=running` also starts `per_proxy` (`/vendor/bin/pm-proxy`).
- The `on boot` action at line ~448 starts `init-modem-sh`; service definition ~464–468 points to `/vendor/bin/init.modem.sh`. The pinned shell script `init.modem.sh`, blob `75520c7055a56930ba4e7c1fab9fd7a2aefa1f5c`, only publishes CDT-derived modem identifiers as properties. **It does not directly call a modem loader or write item134.** This source inspection requires no handling or disclosure of real IMEI or MEID values.
- `init.insmod.sh`, blob `a222838cc855392838a69fbd9ea3951273078658`, sets `vendor.all.modules.ready=1` and `vendor.all.devices.ready=1` after handling the config, even if it is missing. This is **not** evidence of completed `modemsmem` probe, 64-byte payload publication or actual modem startup.
- `sepolicy/vendor/qcom/common/peripheral_manager.te`, blob `edafb01e6199964607b294d44287e9fcbfeae79f`, grants Peripheral Manager read permissions for modem SSR device and SSR sysfs paths and Binder/QIPCRTR capabilities. These permissions do **not** reveal how the proprietary `pm-service` implementation requests firmware boot.
- `init.hardware.mpssrfs.rc.user`, blob `f75a413c1a1865a758060ab9e5c1c3c5c05dbae4`, prepares modem remote filesystem directories during post-fs-data. Directory creation is not proof of the initial modem firmware request.
- The bounded downstream kernel code search still finds a **conditional** literal `subsystem_get("modem")` in `techpack/audio/dsp/adsp-loader.c`, but the inspected Barbet/Lito source configuration did not establish that code path's selection; other indirect or userspace-triggered mechanisms may exist.

**Interpretation:** `vendor.per_mgr` is now a well-supported **Android init-side modem boot trigger/service lead**, not a traced call from the proprietary binary to `subsystem_get("modem")` or a proven timing dependency. The order of `vendor.per_mgr`, modemsmem probe completion, first MPSS start and firmware consumption of item134 is not established by these sources.

**Existing item134 policy:** The pinned downstream `modemsmem.c` (Git blob `428143562894e6d8ca7b656174c72ee4b096f510`) accepts `-EEXIST` for the 64-byte vendor item and *unconditionally clears it*, even if it already exists. A non-destructive scheme is **not implemented or validated**. Proposed preconditions: do not write to an existing item until an authoritative ownership agreement exists; do not mistake stale existing content for a valid modem-ready payload; require exact size, an independently verified write/visibility and consumer acknowledgement protocol, safe first-start and restart ordering, and explicit device-operation approval. Merely preserving bytes does not prove they are safe to reuse.

**Deliverables:** `validation/pixel5a-android-peripheral-manager-first-start-audit.json` pins all Android source blobs and modem-related uncertainties. `tests/pixel5a-android-peripheral-manager-first-start-test.py` adds 13 offline positive/negative tests to all three GitHub workflows. No vendor binary was executed or accessed from a working handset, no modem was started, no identifier value was obtained, and no SMEM data was read/written.

**Step 808:** Examine additional public source-visible Peripheral Manager startup interfaces and Pixel 5a init/sepolicy edges; consider whether a read-only, offline init-event graph can establish start ordering without vendor binaries. Keep PR #18 draft, and obtain separate approval before any real device bring-up.

## Step 808 — bounded Android init event graph, Peripheral Manager and item134 readiness

**Step 807 verified CI:** latest previous head `67e2b204940baff1e5471444fb810787afa6e236` passed Android validation #177 (`44779082584`), public AOSP/Lineage source #93 (`44779082754`) and inactive Linux 7.2.6 ARM64 compile #118 (`44779082611`).

**Pinned source:** `LineageOS/android_device_google_redbull@9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770`, `init.hardware.rc` blob `ec3c3edf7e72fb394bde8e9dc669e4a07ced854b`, `init.insmod.sh` blob `a222838cc855392838a69fbd9ea3951273078658`, `sepolicy/vendor/qcom/common/peripheral_manager.te` blob `edafb01e6199964607b294d44287e9fcbfeae79f` and `sepolicy/vendor/qcom/common/rild.te` blob `5bc8795a5172fa4d05556fb5a4368f141f24937f`.

**Seven explicit init/source edges, not a flattened runtime timeline:**
1. The conditional `on init && property:vendor.skip.init=0` action (beginning at `init.hardware.rc:53`) starts `insmod_sh` (lines 97–98). Its shell script sets `vendor.all.modules.ready` and `vendor.all.devices.ready` unconditionally at the end (around `init.insmod.sh:52-53`), so these are **not** proven module probe completion or item134 publication acknowledgements.
2. The `on boot` action (around `init.hardware.rc:436-450`) starts `init-modem-sh`, whose separately inspected script publishes CDT identifier *properties*, not a firmware-start request. No identifiers were collected.
3. Three **separate** triggers start `vendor.per_mgr` (`/vendor/bin/pm-service`): `persist.vendor.modem.esim.reset=done`, `persist.vendor.modem.esim.reset=noneed`, and fallback `sys.boot_completed=1` (lines 575–584). The boot-completed fallback does not have a source-level conjunction requiring eSIM state `done`; this does **not** establish a safely ordered modem startup relative to eSIM or SMEM.
4. The property `init.svc.vendor.per_mgr=running` starts `per_proxy` (`/vendor/bin/pm-proxy`) (lines 566–573). This proves an init service edge, **not** that modem firmware booted.

**Permissions are not action evidence.** `peripheral_manager.te` grants read access to `modem_ssr_device` and SSR sysfs, and Binder/QIPCRTR capabilities; `rild.te` allows RIL to find the Peripheral Manager service. Neither policy file exposes the proprietary daemon's implementation or demonstrates an actual `subsystem_get("modem")` call. No complete Android init runtime event log or installed device state was audited.

**Safety-critical absent edges:** The inspected Android init files do not contain an explicit `modemsmem probe success → item134 payload visible → firmware consumer acknowledgement → first modem PIL start` dependency. This absence is confined to these reviewed source files, not a claim about every vendor binary, proprietary mechanism or final boot image. The downstream kernel `modemsmem` implementation still zeroes an existing 64-byte item134 and the host-only Step 806 model does not fix this in a running kernel.

**Artifacts:** `validation/pixel5a-android-init-modem-start-event-graph.json` pins the seven explicit source edges and separates unverified external events. `tests/pixel5a-android-init-modem-start-event-graph-test.py` has fifteen baseline/negative tests in all three GitHub workflows; the tests reject invented direct `per_mgr → pil_boot` edges, promotion of ready properties into probe ACKs and removal of item134 ownership/recovery uncertainties. No physical phone, firmware, identifiers, SMEM reads/writes or modem start were involved.

**Step 809:** Inspect Android `vendor.per_mgr` SELinux device-node labels and any public source-visible `modem_ssr_device` interfaces and kernel subsystem character-device handlers, then assess whether a *possible* userspace first-start path can be narrowed further. Keep differences between permission, existence, open/read and actual firmware boot explicit.

## Step 809 — source-visible /dev/subsys_modem startup-on-open interface

**Verified Step 808 baseline:** commit `60f16b54bb5f76dfb16efb5728af29eb53d1623f` — Android phone validation #185 (`44788172085`), AOSP/Lineage source #101 (`44788172064`), Linux 7.2.6 ARM64 compile-only #126 (`44788172068`) all succeeded.

**Pinned downstream kernel:** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `drivers/soc/qcom/subsystem_restart.c`, blob `e304cb58b65037237b2a231a52dadb3bccd618c7`.
- Lines ~1457–1476: `subsys_device_open()` looks up the registered `subsys_device` by character-device minor number and directly calls `subsystem_get_with_fwname(subsys_dev->desc->name, subsys_dev->desc->fw_name)`. The initial zero-reference-count request can trigger the subsystem's `subsys_start` and powerup callback, not merely a passive read.
- Lines ~1479–1500: the device `release` callback invokes `subsystem_put()`, and the file-operations table contains `.open` and `.release` but no `.read` or `.write` entry in the inspected table. Thus an ordinary **open** can itself cause a request; a process need not write a special command.
- Lines ~1525–1558: `subsys_char_device_add()` uses `device_create(..., "subsys_%s", subsys_dev->desc->name)`; lines ~1946–1953 add the character device as part of subsystem registration. With the pinned Lito `modem` descriptor (Step 802), the name is `subsys_modem`. Registration/device creation does **not** itself prove the subsystem was opened or booted.

**Pinned Android source:** `LineageOS/android_device_google_redbull@9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770`, `sepolicy/vendor/qcom/common/file_contexts`, blob `f53709a48e090c7faa3af51da725688876747955`, maps `/dev/subsys_modem` to `modem_ssr_device` (around line 234). `sepolicy/vendor/qcom/common/peripheral_manager.te`, blob `edafb01e6199964607b294d44287e9fcbfeae79f`, grants `vendor_per_mgr` `r_file_perms` on that character-device type (line 16). Android `init.hardware.rc`, blob `ec3c3edf7e72fb394bde8e9dc669e4a07ced854b`, starts `vendor.per_mgr` (binary `/vendor/bin/pm-service`) on eSIM reset completion/noneed or boot-completed fallback, and a source comment describes Peripheral Manager as intended to boot modem.

**Evidence boundary:** This yields a concrete possible chain `vendor.per_mgr` → **authorized userspace open of /dev/subsys_modem** → `subsys_device_open` → `subsystem_get_with_fwname("modem", ...)` → potential initial PIL powerup. It is **not established** that proprietary `pm-service` actually opens the character device; no stock binary was inspected or executed and no running first-boot trace was collected. Permission does not prove usage. Actual device-node mode/ownership, SELinux policy at runtime, available kernel interfaces, first-start requester and MPSS firmware result still need independent evidence. This source chain does not add a dependency on the `modemsmem` item134 probe or guarantee payload visibility, ownership or crash-restart safety.

**Deliverables:** `validation/pixel5a-modem-subsys-char-device-first-start-audit.json` pins the kernel and Android source blobs, device name/label, startup-on-open semantics and all unresolved gaps. `tests/pixel5a-modem-subsys-char-device-first-start-test.py` includes 13 fail-closed baseline/negative tests across all three GitHub workflows. No opening of `/dev/subsys_modem`, firmware startup, SMEM access or phone interaction was performed.

**Step 810:** Examine the checked-in Android `ueventd` device permissions and any other users of `/dev/subsys_modem`, and separately investigate userspace read-only evidence available from public sources. Continue to treat opening the character device as potentially *active*, not a harmless diagnostic.

## Step 810 — pinned ueventd DAC and SELinux gates for /dev/subsys_modem

**Source-only finding.** At `LineageOS/android_device_google_redbull@9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770`, `ueventd.rc` (blob `ee94e699cdacc2fb9e061d66e5281bde81a798a1`) contains `/dev/subsys_* 0640 system system`. The `device-common.mk` source (blob `200ab69ad13b09aef47b1350fb40b1ee7c9dd2d8`) copies this file into the vendor ueventd configuration. Thus `/dev/subsys_modem` matches a source-defined mode/ownership rule, but the installed image and actual running device node have not been checked.

The pinned `sepolicy/vendor/qcom/common/file_contexts` labels `/dev/subsys_modem` `modem_ssr_device`, while `peripheral_manager.te` authorizes `vendor_per_mgr` with `allow vendor_per_mgr modem_ssr_device:chr_file r_file_perms;`. **DAC and SELinux are independent checks:** these policy entries alone do not establish the proprietary `pm-service` process UID/GIDs, effective runtime domain, compiled policy, successful `open()`, or firmware boot. In particular, `0640 system:system` is not a world-readable permission; a process outside the owner/group and without other relevant credential effects would lack DAC read access. No claim is made about the actual service credentials.

As established in Step 809, opening the subsystem character device is potentially **active**: the kernel `subsys_device_open()` calls `subsystem_get_with_fwname()`, which can trigger power-up. Do not treat an attempted open as a harmless read-only inspection. We did not run ADB, open/read the node, start MPSS, touch SMEM item134, use phone identifiers, flash or activate any kernel changes.

**Artifacts:** `validation/pixel5a-modem-ssr-device-access-audit.json` pins the checked source provenance and unknowns. `tests/pixel5a-modem-ssr-device-access-test.py` contains eighteen offline baseline/negative tests and is added to all three existing GitHub Actions workflows. These checks are source-claim invariants, not live Android instrumentation. CI result for this commit must be separately checked.

**Next (Step 811):** Investigate the source-visible `vendor.per_mgr` init service user/group declarations and related service definitions, and whether any public service implementation corroborates which process opens `/dev/subsys_modem`. Continue separating source-level DAC/SELinux eligibility from observed runtime actions, and preserve all phone-function gates.

## Step 811 — pinned Peripheral Manager init UID/GID and modem SSR source access eligibility

**Step 810 CI:** exact commit `53c11319cda50c9b2fc049bd2311871d53aebdf8` passed the three PR workflows: Android phone validation `44863209424`, official Android AOSP source probe `44863209478`, and isolated kernel API compile `44863209446`.

**Pinned source:** `LineageOS/android_device_google_redbull@9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770`, `init.hardware.rc` blob `ec3c3edf7e72fb394bde8e9dc669e4a07ced854b`, lines 561–564, declares `service vendor.per_mgr /vendor/bin/pm-service` with `user system` and `group system` (plus `ioprio rt 4`). The associated `per_proxy` service, lines 566–573, also has user/group system/system, is disabled by default, and starts when `init.svc.vendor.per_mgr=running`. This proxy trigger is an init service edge, *not* a verified modem boot event.

The pinned `ueventd.rc` blob `ee94e699cdacc2fb9e061d66e5281bde81a798a1` assigns `/dev/subsys_*` mode `0640 system system`; the specific modem node matches this pattern. Under the **source declarations**, the Peripheral Manager's declared `system` UID would satisfy owner-read DAC checks. Pinned `file_contexts` labels `/dev/subsys_modem` as `modem_ssr_device`, and `peripheral_manager.te` (blob `edafb01e6199964607b294d44287e9fcbfeae79f`) contains `allow vendor_per_mgr modem_ssr_device:chr_file r_file_perms;`. Thus init identity, ueventd DAC, and SELinux source rules are mutually compatible with a read-capable open; this narrows the previous uncertainty.

**Not established:** actual installed init/ueventd policy, live effective credentials/SELinux, actual node state, proprietary `pm-service` implementation or successful `open()`, which requester starts MPSS first, or SMEM item134 availability/acknowledgment before modem firmware consumption. An `open()` on the subsystem character device can initiate firmware power-up; it must not be treated as a passive diagnostic.

**Artifacts:** `validation/pixel5a-peripheral-manager-init-identity-audit.json` and `tests/pixel5a-peripheral-manager-init-identity-test.py` (21 offline baseline/negative tests), wired into all three existing GitHub workflows. No ADB, binary/device access, modem boot, SMEM operation or flash was performed. Step 811 CI has to be checked against the final branch head.

**Step 812:** Investigate *public* Peripheral Manager implementations or service interface documentation and other users of the SSR device, bounded to pinned source analysis. Do not infer proprietary runtime behavior from a SELinux grant or service declaration. Keep PR #18 draft until real phone-function validation is authorized and demonstrated.

## Step 812 — bounded public Peripheral Manager implementation and SSR interface evidence

**Step 811 exact-head GitHub Actions:** `602a3fd8c6a8698325e77e48581dd6d935594250` passed Android phone validation `44913728086`, official Android source probe `44913728052` and isolated Linux kernel API compile `44913728048`.

**Bounded search:** GitHub code searches for `subsys_modem` in the Redbull device repository, `subsys_modem peripheral_manager`, and `pm-service subsystem_get` were combined with exact pinned Redbull init/SELinux and kernel subsystem-restart source inspection. Search results include unrelated projects and historical device-family policy; **no corresponding public implementation of Redbull's proprietary `/vendor/bin/pm-service` was verified**. A bounded code search cannot prove no implementation exists anywhere. Do not attribute third-party live observations about other hardware to the Pixel 5a.

**Primary pinned evidence:** `LineageOS/android_device_google_redbull@9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770`, `init.hardware.rc` blob `ec3c3edf7e72fb394bde8e9dc669e4a07ced854b`, declares `vendor.per_mgr` and its `/vendor/bin/pm-service` executable; `peripheral_manager.te` blob `edafb01e6199964607b294d44287e9fcbfeae79f` grants `vendor_per_mgr` read-file privileges on `modem_ssr_device`; `file_contexts` blob `f53709a48e090c7faa3af51da725688876747955` maps `/dev/subsys_modem`. The kernel at `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `drivers/soc/qcom/subsystem_restart.c` blob `e304cb58b65037237b2a231a52dadb3bccd618c7`, defines `subsys_device_open()` calling `subsystem_get_with_fwname()`. These connect a *possible* active-open interface to an intended service, not an observed daemon call graph.

**Cross-device comparison, not a porting assumption:** the historical `LineageOS/android_device_lge_bullhead@5cef16f959fe119986fe3d295d420e5f53f08d63` `sepolicy/peripheral_manager.te` blob `343899d329b260e1f335a54ec441a16d5e9e9786` permits `per_mgr` access to an SSR character-device type. It reinforces that this class of policy is used in older Qualcomm Android trees but **does not prove** the Pixel 5a Peripheral Manager binary's code or startup ordering.

**Remaining unproven:** actual device open, first requester, modem boot and recovery, modemsmem item134 publication/readiness/ownership, runtime installed policy, and usable calls/SMS/data. An actual `open("/dev/subsys_modem")` can request modem boot and is not a read-only diagnostic. No physical device, binary disassembly, ADB, SMEM access or flashing performed.

**Deliverables:** `validation/pixel5a-peripheral-manager-public-interface-audit.json` and `tests/pixel5a-peripheral-manager-public-interface-test.py` (20 offline baseline/negative tests) integrated into all three existing GitHub Actions workflows. Source assertions are not a replacement for runtime telephony validation; CI for this step must be independently checked.

**Step 813:** Audit the public SSR character device's error and release semantics with respect to reference counts and initial modem startup, including failure unwind and implications for any eventual userspace modem request, without opening the character device or touching the phone.

## Step 813 — pinned SSR character open/close and get/put lifecycle

**Step 812 CI verified:** commit `d949a5d34cbbf91999abb8139a7d82378268f77c` passed Android phone validation `44916541942`, public AOSP/Lineage probe `44916541900` and isolated Linux ARM64 compile `44916541909`.

**Pinned kernel source:** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `drivers/soc/qcom/subsystem_restart.c`, blob `e304cb58b65037237b2a231a52dadb3bccd618c7`, inspected `__subsystem_get()` (~1028–1081), `subsystem_get_with_fwname()` (~1108–1112), `subsystem_put()` (~1114–1155), and character-device `subsys_device_open()`, `subsys_device_close()` and fops (~1457–1500).

- Character `.open` looks up subsystem by device minor, returns `-EINVAL` if no matching registration, calls `subsystem_get_with_fwname(desc->name, desc->fw_name)`, and propagates `PTR_ERR` on `IS_ERR`. Merely opening a present device **can actively start firmware**.
- `__subsystem_get` returns `ERR_PTR(-ENODEV)` for absent subsystems and for module pin failure; acquires an optional dependency using `subsystem_get(pon_depends_on)`; while holding tracking lock, only when `count==0` calls `subsys_start()`. A successful request increments `count`. The error path for `subsys_start` bypasses the increment, unlocks and drops dependency/module/device references.
- Character `.release` looks up the subsystem again by minor, returns `-EINVAL` if missing, then calls `subsystem_put(subsys_dev)`. It does **not** retrieve a per-file saved reference handle in the inspected code; this is not evidence that runtime concurrent unregister or recovery is safe. The standard file release callback must not be assumed to execute after an unsuccessful open.
- `subsystem_put` no-ops on an error/null handle, checks and warns on an unexpected zero reference count; for a valid counted reference decrements `count`, invoking `subsys_stop()` and memory release only when count reaches zero. A close **does not guarantee** power-down if another reference holder remains. This inspection does not validate all cross-dependency or SSR crash paths.
- Registered subsystem descriptors should have a name; although `__subsystem_get` contains a special null-name return, we do not assign semantics to null-name runtime `/dev/subsys_modem` behavior absent evidence.

**Evidence limit:** Reference counts are not telephony service readiness. We have not established the proprietary Peripheral Manager's open/close lifetime, other owners, module presence on stock Pixel 5a, SMEM item134 visibility or ownership, safe SSR recovery or working calls/SMS/data.

**Artifacts:** `validation/pixel5a-modem-ssr-get-put-lifecycle-audit.json`, `tests/pixel5a-modem-ssr-get-put-lifecycle-test.py` (26 offline baseline/negative cases), integrated into the three existing GitHub workflows. No ADB, open, device read, modem start, SMEM operation, kernel activation or flashing was performed. This step's CI must be verified on final branch head.

**Step 814:** Inspect pinned `subsys_start()`/ `subsys_stop()` and dependency unwind in greater detail, especially a failed first boot versus a deliberate close, without claiming operational modem recovery or touching the Pixel 5a.

## Step 814 — pinned SSR startup error versus last-reference shutdown

**Step 813 verified CI:** exact head `ac1eae4926a1ca2896d059ae4beb838267b4e407` passed Android phone validation `44916853885`, public AOSP/Lineage source probe `44916853858`, and ARM64 inactive compile `44916853871`.

**Pinned source:** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `drivers/soc/qcom/subsystem_restart.c` blob `e304cb58b65037237b2a231a52dadb3bccd618c7`, `subsys_start()` lines 899–937, `subsys_stop()` lines 939–963, `__subsystem_get()` lines 1031 onward.

**First-start / failure branches:**
1. `subsys_start()` emits `SUBSYS_BEFORE_POWERUP`, resets `err_ready` completion and invokes the registered `desc->powerup` callback.
2. **Callback error:** emits `SUBSYS_POWERUP_FAILURE` and directly returns. This branch does not explicitly invoke `desc->shutdown` or `disable_all_irqs` itself. Whether the callback safely unwinds partial powerup is an **unverified dependency**. In the caller, the failed start skips reference-count increment and follows dependency/module/device unwind.
3. **Callback success:** enables subsystem interrupts. If `is_not_loadable`, sets ONLINE and returns without the error-ready wait or subsequent AFTER_POWERUP notification. This special branch must not be conflated with the loadable modem flow.
4. **Loadable ready wait failure:** sends `SUBSYS_POWERUP_FAILURE`, calls `desc->shutdown(desc,false)`, disables interrupts and returns an error; this is **different cleanup** from immediate callback failure.
5. **Loadable ready success:** sets state ONLINE and emits `SUBSYS_AFTER_POWERUP`.

**Stop path:** `subsys_stop()` emits `SUBSYS_BEFORE_SHUTDOWN` and resets `shutdown_ack`. Unless the DT property `qcom,pil-force-shutdown` is present, it marks OFFLINING and attempts SysMon graceful shutdown under its timeout helper, logging a nonzero SysMon result. It then calls `desc->shutdown(desc,false)`, sets OFFLINE, disables interrupts, and emits `SUBSYS_AFTER_SHUTDOWN`. The forced path skips SysMon graceful signaling; this is not proof of healthy modem recovery. Only the final counted `subsystem_put` invokes `subsys_stop`, as audited in Step 813.

**Open questions and safety:** Descendant `powerup` callback cleanup on partial failure, exact Barbet `is_not_loadable` and DT force-shutdown properties, SMEM item134 ownership/publication/acknowledgment ordering, modem reinitialization after crash, and functioning calls/SMS/data are all unverified. Neither notifications nor state flags establish telephony readiness. No hardware, ADB, character-device open, modem boot, SMEM read/write, flash or release action was performed.

**Artifacts:** `validation/pixel5a-modem-ssr-start-stop-failure-audit.json` and `tests/pixel5a-modem-ssr-start-stop-failure-test.py` (30 offline baseline/negative tests) in all three existing GitHub Actions workflows. Source assertions, not live device validation. Verify this Step 814 commit's CI separately.

**Step 815:** Inspect the registered Lito modem descriptor's `powerup` and `shutdown` callback implementation and any rollback on partial failure, especially whether its cleanup matches SSR caller expectations. Continue source-only and keep PR #18 draft.

## Step 815 — pinned Lito PIL powerup callbacks and conditional loader rollback

**Step 814 CI:** commit `747617394e9c81dbc85c90401442045cc96976fc` passed Android phone validation `44918068460`, public AOSP/Lineage source probe `44918068483` and isolated Linux ARM64 compile `44918068475`.

**Pinned kernel source:** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `drivers/soc/qcom/subsys-pil-tz.c` blob `f17f9e57b0d1f671017032df9224ada0bbea15c2`, `drivers/soc/qcom/peripheral-loader.c` blob `c7920af7ab0c010c24078c72809a5d83667ce765`, and `drivers/soc/qcom/subsystem_restart.c` blob `e304cb58b65037237b2a231a52dadb3bccd618c7`.

**Registered Lito-compatible callbacks:** the PIL TZ driver's probe assigns `subsys_desc.powerup = subsys_powerup` and `subsys_desc.shutdown = subsys_shutdown`. The power-up callback reinitializes stop acknowledgment when the corresponding IRQ is present, sets the firmware name, then **returns the result of `pil_boot()`**. The shutdown callback conditionally uses the force-stop SMEM state and stop acknowledgment before invoking `pil_shutdown()`; critically, it returns `0` independently of underlying PIL shutdown errors. This source-level behavior must not be interpreted as proof that the modem shut down successfully.

**Loader failure behavior:** `pil_boot()` first sends AOP ON, returning early if it fails. After firmware request and image checks it has stage-dependent error branches: resource voting; init-image, memory setup, segment loading, memory assignment, and auth-and-reset stages; conditional `deinit_image`, `pil_proxy_unvote`, firmware release, memory region clear/free and `pil_release_mmap`, followed by AOP OFF on error. There are conditional ownership transitions, and cleanup operation return values are not all checked. The source therefore establishes **attempted stage-specific cleanup**, not an atomic rollback guarantee for every hardware/resource failure.

**Shutdown behavior:** `pil_shutdown()` invokes the PIL shutdown operation and sets or clears `desc->shutdown_fail`, handles proxy unvote, issues AOP OFF and sets `desc->modem_ssr = true`. It returns `void`, and the surrounding `subsys_shutdown` returns success even when the lower-level shutdown operation failed. No actual SSR reliability, modem reset generation, or telephony functionality was tested.

**Remaining gates:** effective Barbet DT and driver binding; clock/regulator/SCM failure cleanup effectiveness; memory ownership and assignment; SMEM item134 original ownership, publication and consumer acknowledgment; first modem request timing; calls, SMS, cellular data and crash recovery. No source callback is an item134 readiness fence, and no physical Pixel 5a, ADB, modem start, character open, SMEM read/write or flash operation was involved.

**Artifacts:** `validation/pixel5a-modem-pil-callback-rollback-audit.json` and `tests/pixel5a-modem-pil-callback-rollback-test.py` (23 offline baseline/negative tests), added to the three existing GitHub Actions workflows. Final commit CI must be independently checked.

**Step 816:** Examine pinned `pil_shutdown_trusted()` and PAS/SCM error propagation, resource and memory ownership on failed shutdown; continue source-only and keep PR #18 draft.

## Step 816 — trusted PAS shutdown, SCM transport status and regulator/clock cleanup

**Step 815 CI check:** exact head `60a648513b32d6d7a9b1838bf51bcdd422fcfe30` had Android phone validation `44919394800` and public source probe `44919394804` **success**, while isolated ARM64 compile `44919394809` was **in_progress** at inspection. Do not promote that checkpoint to all-three-passed without rechecking.

**Pinned source:** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `drivers/soc/qcom/subsys-pil-tz.c` blob `f17f9e57b0d1f671017032df9224ada0bbea15c2`, `pil_shutdown_trusted()` lines 722–769 and `subsys_shutdown()` lines 833–853; `drivers/soc/qcom/peripheral-loader.c` blob `c7920af7ab0c010c24078c72809a5d83667ce765`, `pil_shutdown()` lines 1419–1440.

**Shutdown ordering and failures:**
- The trusted shutdown callback returns immediately when `no_auth` is set. Otherwise it acquires a bus-scale vote, proxy regulators, and proxy clocks before invoking `scm_call2(PAS_SHUTDOWN_CMD)`.
- Bus-vote failure returns directly; proxy-regulator or proxy-clock enable failure branches undo the bus vote and, for the clock branch, proxy regulators. These are *code paths*, not confirmed hardware resource states.
- After the SCM call, proxy clocks and regulators are disabled and the bus request is released. If the **SCM transport `rc`** is nonzero, the function returns it **without reaching the subsequent primary clock/regulator disable calls**. If transport succeeds but the **secure return `desc.ret[0]`** is nonzero, the primary resources are nevertheless disabled and the secure result returned. This distinction makes shutdown failure handling and resource ownership important.
- The higher-level `pil_shutdown()` sets `shutdown_fail` according to the trusted callback result, performs proxy-unvote handling, sends AOP OFF and marks `modem_ssr=true`, but has `void` return. The `subsys_shutdown()` wrapper invokes it then returns `0`. Therefore a visible successful SSR callback result cannot be interpreted as secure-PAS shutdown success.
- No release or reinitialization path shown here proves that failing primary clock/regulator cleanup is harmless; a later retry may encounter state left by the prior attempt. No hardware condition is asserted.

**Unresolved gates:** actual PAS transport/secure outcomes, clock/regulator/proxy resource ownership, error propagation into recovery policy, forced stop acknowledgment, SMEM item134 publication and reuse protocol, modem restart generation, and live phone calls/SMS/data. No physical device, ADB, modem start, character-device open, SMEM reads/writes, flashing or patch activation occurred.

**Artifacts:** `validation/pixel5a-modem-pas-shutdown-resource-audit.json` and `tests/pixel5a-modem-pas-shutdown-resource-test.py` (28 offline baseline/negative tests), included in all three GitHub workflows. These tests protect pinned source claims; they do not execute trusted firmware, modem power transitions or recovery.

**Step 817:** Inspect pinned regulator and clock enable/disable helper cleanup behavior, particularly partial-acquisition failure and whether early SCM errors can preserve resources unexpectedly. Keep PR #18 draft and continue offline.

## Step 817 — pinned regulator/clock helper rollback and proxy bus vote paths

**Step 816 CI:** `bfd0237da495e39e6afa32786e1d65f4ca89859c` passed Android validation `44919599053`, public Android source probe `44919599078`, and isolated Linux ARM64 compile `44919599013`.

**Source:** `LineageOS/android_kernel_google_redbull@929e7e2f3658867d51a1d423c7e000f5cf1d4043`, `drivers/soc/qcom/subsys-pil-tz.c` blob `f17f9e57b0d1f671017032df9224ada0bbea15c2`: `enable_regulators()` lines 455–515, `disable_regulators()` 517–533, `prepare_enable_clocks()` 535–555, `disable_unprepare_clocks()` 557–563, `pil_make_proxy_vote()` 565–593, `pil_remove_proxy_vote()` 595–607, `do_bus_scaling_request()` 378–404.

**Helper behavior:** `enable_regulators` attempts per-entry voltage/load/enable, and its error labels reset the current entry where applicable and unwind earlier entries in reverse order. Cleanup calls to `regulator_set_voltage`, `regulator_set_load`, and `regulator_disable` have unchecked return values, so attempting rollback is not proof of restored hardware state. With `keep_proxy_regs_on && reg_no_enable`, the helper can skip regulator enabling, and corresponding disable helper can skip disabling. `disable_regulators` returns void. The clock helper reverses previously enabled clocks if `clk_prepare_enable` fails, and its teardown helper also returns void.

**Critical follow-up:** `pil_make_proxy_vote` acquires a bus-scaling vote before proxy regulators and clocks. If `enable_regulators` fails, this helper **returns directly without an explicit matching bus unvote**; if clock acquisition fails, it disables proxy regulators then returns, again without a matching local bus unvote. Its successful counterpart `pil_remove_proxy_vote` does release the bus vote, but that is a distinct function; the enclosing `pil_boot` error path and build-time bus-scaling configuration must be audited before claiming an effective leak. This source has a no-op bus-scaling configuration branch, so the missing unvote must not be presented as a verified Pixel 5a hardware leak. Do not patch this general kernel behavior inline with Armada's phone-specific work; isolate and defer upstream submission until the user approves batch review.

**Unresolved:** exact configured bus client, whether the parent loader later unvotes on all failure cases, actual regulator/clock outcomes, implications of PAS transport errors from Step 816, SMEM item134 publication/acknowledgment, and live modem/phone recovery. No ADB, character-device open, modem power request, SMEM operation or flashing.

**Artifacts:** `validation/pixel5a-pil-regulator-clock-proxy-vote-audit.json` and `tests/pixel5a-pil-regulator-clock-proxy-vote-test.py` (24 offline baseline/negative tests), added to three existing GitHub Actions workflows. Verify final Step 817 CI independently.

**Step 818:** Trace `pil_boot()` handling of a failed `pil_proxy_vote()` and the exact `pil_proxy_unvote()` behavior to establish whether the missing local bus unvote is compensated by its caller. Continue source-only and keep draft PR #18 unmerged.
