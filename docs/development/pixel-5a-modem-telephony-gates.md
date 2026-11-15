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
