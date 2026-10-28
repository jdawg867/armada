# Pixel 5a (barbet / SM7250) integration audit

> Status: **static source research only**. No bootable Armada OS phone image, verified hardware bring-up, or device enablement is claimed.

## Scope and workflow

- Target: Google Pixel 5a (`barbet`), Qualcomm SM7250/Lito.
- Target integration: Armada OS fork, feature branches into `development`.
- Research inputs: pinned mainline Linux and Qualcomm vendor kernel trees, now preserved as patch series and audit artifacts in the private `jdawg867/linux-sm7250-armada-integration` repository. Full kernel trees are **not** committed to Armada. Audit observations must be revalidated against those exact bases before code changes.
- Latest recorded local audit: Step 708, source and repository integrity **PASS**. This was a read-only inspection; CI on this repository does not rerun the local kernel audits.
- GitHub Actions: `.github/workflows/android-phone-validation.yml` executes Armada boot-image regeneration and build-channel baseline tests, not a device boot test.

## GitHub research handoff (October 2026)

Local kernel research checkouts were retired after the relevant modifications and audit artifacts were uploaded to the **private** repository `jdawg867/linux-sm7250-armada-integration`. The separate Ubuntu Touch vendor kernel checkout is **retained** because its local path is used by that project's adaptation workflow. GitHub backups preserve changes, not a complete standalone kernel source history.

| Backup branch in private research repository | Preserved materials |
| --- | --- |
| `feature/sm7250-source-snapshot` | Linux 7.2.6 SM7250 integration patch; base `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`, original snapshot `5867fa09dec9a1ac54a9cf8b07345c8d446b6548` |
| `feature/rpmh-research-backup` | Independent Linux 7.2.6 and mainline RPMh async-failure cleanup patches (research only; not approved for upstreaming) |
| `feature/pixel5a-vendor-backup` | Two Ubuntu Touch / Pixel 5a vendor kernel commits as patches |
| `feature/sm7250-audit-backup` | UFS PHY calibration tables/manifests, numbered audit patches, and prerequisite patches |
| `feature/kernel-build-config-backup` | Five saved build configurations |
| `feature/sm7250-validation-evidence` | Device-tree/TLMM validation files and previous configuration |

**Integrity gates completed locally before checkout retirement:** matching local/remote Git commit IDs for all six backup branches; SHA-256 verification of five build configurations and 22 validation evidence files; clean forward application of the SM7250 integration patch to its exact Linux 7.2.6 base with reconstructed tree hash `5fc4b475bef24d74b3469cc284415de283cad864`; and exact reconstruction of the mainline RPMh research patch with tree hash `b43a5f9456ce50375300e4f6daa3aa96907fed6b`. These are **source-provenance checks**, not runtime/hardware validation.

**Next GitHub-first checkpoint:** review the inactive SM7250 interconnect prototype and RPMh BCM ownership/lifecycle against the preserved patch and pinned base. Document provider-registration, node/index, QoS/BCM, and DTS binding gaps before proposing any enablement. Keep UFS PHY and modem/IPA/SMMU dependencies separate and deferred. Do not introduce a device-tree compatible or enable BCM voting based solely on a successful source reconstruction.

## Observed hardware and driver differences

| Subject | Lito vendor source observation | Mainline source observation | Confidence / next action |
| --- | --- | --- | --- |
| Applications SMMU | `msm-arm-smmu-lito.dtsi`: `apps_smmu` base `0x15000000`, size `0x100000`, downstream `qcom,qsmmu-v500`; auxiliary TCU `0x15182000` size `0x20` | `sm7250.dtsi` lacks `apps_smmu`; SM6350 provides related MMU-500 example | Static source observation; check mainline binding, TCU and driver semantics before any DT node |
| SMMU interrupts | 81 parent SPI entries; one global. Lito-only SPI values versus SM6350: `179`, `395`–`400` | SM6350 has 81 entries; SM6350-only values: `95`, `96`, `185`, `410`–`413` | Shared IDs preserve relative order, but arrays differ. **Never copy SM6350 IRQ list wholesale** |
| SMMU TBUs and streams | Eight TBU SID ranges cover `[0x0000,0x2000)` without overlap; IPA AP/WLAN/UC SIDs `0x520`, `0x521`, `0x522` map by range to `anoc_2_tbu` `[0x400,0x800)`, SPI 424 | Stream ownership and SM7250 SMMU driver compatibility not established | Static range membership is not evidence of runtime translation or TBU programming |
| IPCC | Register base `0x408000`, GIC SPI **229** | SM6350 reference base `0x408000` with SPI **228**; inspected SM7250 DTS has no provider | IRQ mismatch requires independent validation |
| Modem SMP2P | MPSS uses SMEM indices `435` and `428`; IPA inbound/outbound entries; IPCC mailbox | Inspected SM7250 DTS lacks MPSS SMP2P | Provider and modem lifecycle remain unimplemented |
| IPA IOMMU | Downstream has separate AP, WLAN, UC context-bank devices and respective domains | Mainline IPA uses `ipa->dev` for IMEM/SMEM IOMMU maps and `gsi->dev = &pdev->dev` for GSI DMA; IPA binding allows 1–2 IOMMU specifiers | **Do not automatically put all three vendor SIDs into mainline IPA `iommus`** |
| IPA versions and resources | Lito vendor IPA memory/IRQ/firmware descriptions need further reconciliation | SM6350 IPA example is **not** a validated drop-in; `qcom,sm7250-ipa` missing from inspected matching/binding | IPA enablement deferred |
| Interconnect | RPMh IPA clock exists in mainline `clk-rpmh.c` | Local SM7250 ICC source is a research prototype, intentionally without provider registration/DT match | No BCM/QoS voting, power-domain enabling or ICC activation |

## Integration checkpoints (not yet completed)

- [ ] Revalidate Step 702–708 discoveries against pinned mainline and vendor source commits, with explicit SHA manifests and immutable copied output.
- [ ] Determine ARM SMMU-500 feature/quirk compatibility, SID and mask semantics, TCU/TBU handling, `qcom,actlr` downstream differences, and correct binding.
- [ ] Resolve IPCC SPI 229 versus SM6350 SPI 228 from independent SM7250 evidence.
- [ ] Confirm SMP2P, SMEM, mailbox and modem remoteproc dependencies before any provider patches.
- [ ] Reconcile IPA 4.7 hardware version, endpoint data, GSI registers, IRQ trigger types, IOMMU domain ownership, firmware loader and IMEM/SMEM mapping semantics.
- [ ] Finish ICC/RPMh BCM lifecycle verification in an isolated feature branch. The research prototype must remain inactive.
- [ ] Add targeted source-only and DT/schema CI coverage **before** enabling each subsystem.
- [ ] Make minimal, separate, reviewable implementation PRs into `development`; do not merge on CI alone when hardware evidence is missing.
- [ ] Obtain explicit approval for boot-image creation, device flashing or on-device testing at a later stage.

## Deferred vendor-kernel research

Separate risk observations from local source audit (not runtime-proven and **not** patched here):

- Downstream IPA firmware initialization may not reliably signal completion on some error paths, with a potential unbounded waiter.
- A possible IPA SRAM PDN/canary offset overlap requires physical memory mapping verification.

Keep prospective generic kernel fixes isolated from primary Armada integration; consider upstream submissions only after primary integration and approved review.

## Safety rules

The present checklist and baseline GitHub Actions are **not** a hardware qualification gate. A green CI status can justify merging documentation or narrowly scoped tests; it does **not** authorize registration of unverified device-tree providers, SMMU stream programming, IPA/modem initialization, BCM/QoS votes, firmware writes, flashing or production image publication.
