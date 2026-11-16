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
