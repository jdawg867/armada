# Pixel 5a / SM7250 interconnect and RPMh review gates

> **Research checklist, not device enablement.** This file does not assert that the SM7250 ICC provider is operational, compiled, schema-validated, boot-tested, or suitable to register. Do not add a compatible string, enable a provider, or issue BCM/QoS votes until the evidence gates below are met.

## Provenance and scope

- Armada hardware audit: [pixel-5a-sm7250-audit.md](pixel-5a-sm7250-audit.md).
- Pinned mainline Linux 7.2.6 base: `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`.
- Prior SM7250 integration snapshot (patch-backed, not a full source clone): `5867fa09dec9a1ac54a9cf8b07345c8d446b6548`.
- Preserved private GitHub research backup: `jdawg867/linux-sm7250-armada-integration`, branch `feature/sm7250-source-snapshot`. The interconnect prototype is present in the backed-up changes.
- Additional private audit materials: branch `feature/sm7250-audit-backup`.
- Previous local review inspected `drivers/interconnect/qcom/sm7250.c`, `drivers/interconnect/qcom/icc-rpmh.[ch]`, `include/dt-bindings/interconnect/qcom,sm7250-rpmh.h`, and downstream `lito-bus.dtsi`. Those findings require revalidation using the pinned sources before coding.
- **Current state:** the SM7250 ICC Kconfig option was disabled in the preserved `sm7250.config`; the saved build config kept this driver disabled, **but** the backed-up C prototype includes OF matches and a platform-driver registration. Earlier statements that the source lacked registration were incorrect; this is not a compile or runtime result.

## Direct inspection of preserved patch (October 28, 2026)

Read `patches/sm7250-linux-7.2.6-integration.patch` from private backup branch `feature/sm7250-source-snapshot`. The file changes `drivers/interconnect/qcom/sm7250.c` (new, 2,019 lines), `include/dt-bindings/interconnect/qcom,sm7250-rpmh.h` (new, 371 lines), `drivers/interconnect/qcom/Kconfig`, `drivers/interconnect/qcom/Makefile`, and `Documentation/devicetree/bindings/interconnect/qcom,rpmh.yaml`.

Concrete findings from the **added lines in the patch**, not from a compiled kernel:

- The C file has **14** `qcom,sm7250-*` entries in `qnoc_of_match`, and ends with `module_platform_driver(qnoc_driver)`. Its `probe` and `remove` members reference `qcom_icc_rpmh_probe` and `qcom_icc_rpmh_remove`. This **contradicts prior documentation** saying registration/DT matching were absent. The source-file header still says registration and matching are incomplete; that comment is stale relative to the file's tail.
- The added C file contains **17** `qcom_icc_desc` declarations and **17** node-pointer arrays, compared with **14** matched compatibles. This count alone does not establish an error: some descriptors might intentionally be unused or referenced elsewhere. Reconcile each descriptor and each binding compatible independently.
- The added binding header defines **258** `SM7250_*` integer macros. A narrow scan identified **139** designated array entries using `[SM7250_*] = &node`; all 139 referenced names were found among the binding defines, and none of those names appeared twice as designated entries. **This does not verify provider-local numeric collisions, array completeness, node routing, BCM membership, or compilation.**
- `Kconfig` declares `INTERCONNECT_QCOM_SM7250` and `Makefile` associates it with `sm7250.o`, while the preserved build configuration has `# CONFIG_INTERCONNECT_QCOM_SM7250 is not set`. The compiled/active status is **not verified**.
- The DT binding patch adds 14 SM7250 compatible strings. Binding presence is not evidence of correct hardware topology or authorization to activate providers.

**Required reconciliation:** update review assumptions to reflect the *actual source* while retaining the disabled configuration and no hardware-activation rule. Existing synthetic-only CI is not a substitute for checking these 17 descriptors, 14 matches, provider-local IDs, BCM references, and downstream fabric evidence.

## Descriptor, OF-match and BCM reconciliation (source snapshot follow-up)

This comparison inspects the **added C source lines** in `patches/sm7250-linux-7.2.6-integration.patch` on private backup branch `feature/sm7250-source-snapshot`. It does not parse a reconstructed compiled tree or verify downstream hardware.

- All **14** `qcom,sm7250-*` OF-match entries reference names among the **17** declared `qcom_icc_desc` structures. The three descriptors with no OF match are `sm7250_mc_virt_display_desc`, `sm7250_gem_noc_display_desc`, and `sm7250_mmss_noc_display_desc`. Their absence from the match table may be deliberate deferral; determine intent before adding compatibles.
- The file declares **32** `qcom_icc_bcm` objects and **12** arrays of BCM pointers. All references in those 12 arrays resolve to declared BCM objects. For each of the 32 BCM objects, its literal `.num_nodes` agrees with the number of listed node-address references, based on a narrow regular-expression scan.
- Six display-specific BCM declarations are **not referenced by those arrays**: `sm7250_bcm_acv_display`, `sm7250_bcm_mc0_display`, `sm7250_bcm_sh0_display`, `sm7250_bcm_mm0_display`, `sm7250_bcm_mm1_display`, and `sm7250_bcm_mm2_display`. This correlates with the three unmatched display descriptors; it does **not** prove that array/descriptor wiring is otherwise complete.
- **Open source questions:** whether these three display providers are intentionally inactive; whether 17 node arrays have correct provider-local binding indices and topology; whether BCM shared ownership and `keepalive`/vote semantics are safe; whether QoS, probe, remove and firmware requirements are satisfied. The saved Kconfig remains disabled, and no hardware enablement is authorized.

## Provider-local index and shared BCM audit (source-only)

The following scan uses the added lines of `drivers/interconnect/qcom/sm7250.c` and `include/dt-bindings/interconnect/qcom,sm7250-rpmh.h` in the preserved `feature/sm7250-source-snapshot` patch. The index scope is **within each node-pointer array**, not across all provider arrays: binding IDs are provider-local.

- Parsed **17 node-pointer arrays** with **139** explicitly indexed `[SM7250_*] = &node` entries. For these entries every symbol resolves to one of the **258** literal binding macros. No duplicate resolved numeric ID was seen *within an individual array*. This is a partial static scan, not confirmation of array capacity, graph links or DT consumer arguments.
- Found **one BCM object shared between two referenced BCM-pointer arrays**: `sm7250_bcm_cn1` is listed in both `sm7250_a1noc_bcms` and `sm7250_cnoc_bcms`. Shared BCM ownership requires checking the RPMh probe/remove, BCM initialization and aggregation/voting lifecycle before enabling either provider.
- Found **six repeated firmware BCM names across distinct C objects**, each in display and non-display variants: `ACV`, `MC0`, `SH0`, `MM0`, `MM1`, and `MM2`. Their display variants are not referenced by the 12 identified BCM-pointer arrays (see previous section). Equal firmware names are not necessarily a defect; aliasing, shared membership and separate display paths must be checked against the downstream design.
- **No hardware-readiness conclusion:** matching literal indices does not establish contiguous IDs, complete endpoint graphs, safe BCM voting or working provider registration. Keep `CONFIG_INTERCONNECT_QCOM_SM7250` disabled in the preserved configuration, and do not add DT consumers or activate providers.

## RPMh lifecycle wiring review (preserved SM7250 patch)

The backed-up `drivers/interconnect/qcom/sm7250.c` registers a `platform_driver` with `.probe = qcom_icc_rpmh_probe`, `.remove = qcom_icc_rpmh_remove`, `.sync_state = icc_sync_state`, and `module_platform_driver(qnoc_driver)`. These are *references to generic RPMh core functions*, not evidence that probe, error unwind, shared BCM ownership, or removal is safe. The preserved integration patch does **not** change `drivers/interconnect/qcom/icc-rpmh.c`; the generic helper implementation must be reviewed independently at the pinned Linux base.

The 17 declared `qcom_icc_desc` structures divide as follows:

- **12** set `.bcms` and reference BCM pointer arrays.
- **5** omit `.bcms`: the three display-only descriptors `sm7250_mc_virt_display_desc`, `sm7250_gem_noc_display_desc`, `sm7250_mmss_noc_display_desc`, plus the matched `sm7250_npu_noc_desc` and `sm7250_dc_noc_desc`. For the two matched descriptors, empty BCM membership may be intentional but must be checked against required RPMh vote semantics.
- The shared `sm7250_bcm_cn1` object is referenced by A1NOC and CNOC arrays. Review whether generic probe initializes it repeatedly, how its `voter_idx` and ownership are managed, and whether remove/unwind can invalidate a BCM still referenced by another provider.

**Remaining gating evidence**: inspect the exact pinned `icc-rpmh.c` / `icc-rpmh.h` definitions of `qcom_icc_rpmh_probe`, `qcom_icc_rpmh_remove`, `qcom_icc_bcm_init`, and `icc_sync_state`; trace failures, teardown, shared-BCM initialization, and votes with concrete code citations before proposing changes. Neither a passing source scan nor the presence of function pointers constitutes runtime verification. Do not enable this driver or add consumer DT nodes.

## Verification checklist

| Gate | Required evidence before enablement | Status |
| --- | --- | --- |
| Source reproduction | Read the private GitHub integration patch and pin exact file evidence; full independent checkout/build validation remains outstanding | Patch inspected; build unverified |
| Binding / index contract | Check each SM7250 RPMh interconnect binding ID, node-array index, duplicate or missing ID, and endpoints against downstream reference; distinguish vendor-only indexes | Pending |
| Provider lifecycle | Verify `qcom_icc_desc` construction, `qcom_icc_rpmh_probe` and remove/unwind, node creation/destruction and any shared-BCM ownership | Registration syntax present; lifecycle semantics pending |
| BCM arrays | Verify every BCM name, node membership, keepalive status and the `qcom_icc_bcm_init` lifecycle; check for duplicate or dangling nodes | Pending |
| QoS programming | Verify offsets, ports, masks, and init sequencing before permitting `qcom_icc_rpmh_configure_qos` calls | Pending |
| Aggregate/set semantics | Verify `qcom_icc_pre_aggregate`, aggregate, `qcom_icc_set`, and `qcom_icc_set_qos` interactions; check failure and teardown behavior | Pending |
| Clock/power dependencies | Reconcile RPMh clocks, power domains and sleep/wake voting dependency order | Pending |
| DT integration | Verify SM7250-specific providers, consumers, compatibles and upstream binding requirements; do **not** infer from SM6350 | Pending |
| Static checks | Add source-only tests that fail on index/descriptor inconsistencies while the hardware driver remains disabled | Pending |
| Hardware readiness | Independently validate firmware/board resources, boot and runtime traces on approved test hardware before activation | Deferred; requires explicit approval |

## Immediate GitHub-only action

1. Review the preserved source snapshot and node/binding index mapping; record **file paths, source commit, and concrete evidence** for each finding. If private research files are inaccessible from the GitHub integration, mark evidence unavailable rather than substituting a generic Qualcomm design.
2. Split findings into: (a) source-only correctness issues, (b) unresolved hardware/firmware assumptions, and (c) explicitly deferred enablement steps.
3. Propose narrowly scoped data validation in a separate feature PR; keep `CONFIG_INTERCONNECT_QCOM_SM7250` disabled and do not add a DT match.
4. Review any proposed generic RPMh error cleanup independently of the Pixel 5a port, with no automatic upstream submission.

## Non-goals

No local kernel build, boot-image generation, phone flash, ICC registration, BCM writes, SMMU/IPA/modem activation, or claims of successful device bring-up are part of this document.
