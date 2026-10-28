# Pixel 5a / SM7250 interconnect and RPMh review gates

> **Research checklist, not device enablement.** This file does not assert that the SM7250 ICC provider is operational, compiled, schema-validated, boot-tested, or suitable to register. Do not add a compatible string, enable a provider, or issue BCM/QoS votes until the evidence gates below are met.

## Provenance and scope

- Armada hardware audit: [pixel-5a-sm7250-audit.md](pixel-5a-sm7250-audit.md).
- Pinned mainline Linux 7.2.6 base: `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`.
- Prior SM7250 integration snapshot (patch-backed, not a full source clone): `5867fa09dec9a1ac54a9cf8b07345c8d446b6548`.
- Preserved private GitHub research backup: `jdawg867/linux-sm7250-armada-integration`, branch `feature/sm7250-source-snapshot`. The interconnect prototype is present in the backed-up changes.
- Additional private audit materials: branch `feature/sm7250-audit-backup`.
- Previous local review inspected `drivers/interconnect/qcom/sm7250.c`, `drivers/interconnect/qcom/icc-rpmh.[ch]`, `include/dt-bindings/interconnect/qcom,sm7250-rpmh.h`, and downstream `lito-bus.dtsi`. Those findings require revalidation using the pinned sources before coding.
- **Current state:** the SM7250 ICC Kconfig option was disabled in the preserved `sm7250.config`; the prototype intentionally lacked provider registration / DT matching. This status is not a compile result.

## Verification checklist

| Gate | Required evidence before enablement | Status |
| --- | --- | --- |
| Source reproduction | Retrieve the exact backed-up patch; verify checksum and apply against pinned base; inspect the resulting ICC files | Pending independent GitHub-side review |
| Binding / index contract | Check each SM7250 RPMh interconnect binding ID, node-array index, duplicate or missing ID, and endpoints against downstream reference; distinguish vendor-only indexes | Pending |
| Provider lifecycle | Verify `qcom_icc_desc` construction, `qcom_icc_rpmh_probe` and remove/unwind, node creation/destruction and any shared-BCM ownership | Pending |
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
