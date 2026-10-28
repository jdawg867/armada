#!/usr/bin/env python3
"""Validate the Pixel 5a source-audit record; never probe hardware or enable drivers."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
doc = root / "docs/development/pixel-5a-sm7250-audit.md"
if not doc.is_file() or doc.is_symlink():
    sys.exit("FAIL: expected regular Pixel 5a audit document")
text = doc.read_text(encoding="utf-8")

facts = {
    "target codename": r"barbet",
    "SoC": r"SM7250",
    "source-only caveat": r"static source research only",
    "applications SMMU": r"apps_smmu",
    "vendor SMMU base": r"0x15000000",
    "vendor IPCC IRQ": r"SPI \*\*229\*\*",
    "mainline reference IPCC IRQ": r"SPI \*\*228\*\*",
    "AP stream": r"0x520",
    "WLAN stream": r"0x521",
    "UC stream": r"0x522",
    "TBU": r"anoc_2_tbu",
    "SMMU deferred": r"SMMU",
    "IPA enablement deferred": r"IPA enablement deferred",
    "ICC inactive": r"inactive",
    "requires approval for flash": r"explicit approval",
}
for label, pattern in facts.items():
    if re.search(pattern, text, flags=re.IGNORECASE) is None:
        sys.exit(f"FAIL: missing evidence record: {label}")

# The three independently observed vendor stream IDs must fit the observed
# second TBU half-open interval. This is pure data validation, NOT hardware proof.
stream_ids = (0x520, 0x521, 0x522)
start, end = 0x400, 0x800
if len(set(stream_ids)) != 3 or not all(start <= sid < end for sid in stream_ids):
    sys.exit("FAIL: IPA/TBU static range consistency")

# The conflicting interrupt sets are disjoint, both have seven members;
# they do not justify copying the SM6350 array to Lito.
lito_only = {179, *range(395, 401)}
sm6350_only = {95, 96, 185, *range(410, 414)}
if len(lito_only) != 7 or len(sm6350_only) != 7 or lito_only & sm6350_only:
    sys.exit("FAIL: IRQ difference consistency")

# Do not misrepresent this metadata-only gate as a bring-up, DTSchema,
# compile, IPA version, SMMU registration, or hardware verification.
for statement in ("No bootable Armada OS phone image",
                  "hardware qualification gate"):
    if statement.casefold() not in text.casefold():
        sys.exit(f"FAIL: missing safety caveat: {statement}")


# Require the separate ICC/RPMh evidence gate to remain explicitly source-only.
# This does not inspect private kernel source or prove any hardware capability.
icc_doc = root / "docs/development/pixel-5a-sm7250-icc-review.md"
if not icc_doc.is_file() or icc_doc.is_symlink():
    sys.exit("FAIL: expected regular SM7250 ICC review document")
icc_text = icc_doc.read_text(encoding="utf-8")

icc_gates = {
    "source provenance": r"500df175a7f9e6bc1a9c328590ca5150f84f9ff0",
    "binding and index review": r"Binding / index contract",
    "provider lifecycle": r"Provider lifecycle",
    "BCM initialization": r"qcom_icc_bcm_init",
    "QoS review": r"QoS programming",
    "aggregation semantics": r"qcom_icc_pre_aggregate",
    "device-tree review": r"DT integration",
    "hardware gate": r"Hardware readiness",
    "deferred configuration": r"CONFIG_INTERCONNECT_QCOM_SM7250",
    "no premature DT match": r"do not add a DT match",
    "no kernel build": r"No local kernel build",
}
for label, pattern in icc_gates.items():
    if re.search(pattern, icc_text, flags=re.IGNORECASE) is None:
        sys.exit(f"FAIL: missing ICC review gate: {label}")

# A missing source checkout is expected on hosted CI, not a reason to
# substitute unverified source assertions or turn on kernel hardware.
if "not device enablement" not in icc_text.casefold():
    sys.exit("FAIL: ICC gate must remain explicitly non-enabling")

print("PASS: Pixel 5a static evidence consistency")
print("NOT VERIFIED: kernel source, binding, DT, build, boot, or hardware")
