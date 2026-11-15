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
