# Pixel 5a Mainline Kernel Investigation

## Scope

Investigate upstream Linux 7.2.6 support for Google Pixel 5a
(barbet), Qualcomm SM7250/Lito.

This is a host-side research document, not a bootability claim.

## Source references

- Armada kernel version: Linux 7.2.6.
- Upstream stable source tag: v7.2.6.
- Upstream source commit:
  500df175a7f9e6bc1a9c328590ca5150f84f9ff0.
- Google-derived reference kernel: Linux 4.19.160.
- Stock Android kernel: Linux 4.19.202.
- Hardware revision reported by Android: MP1.0.

## Upstream platform support

- No dedicated SM7250 or Barbet device tree was found in the
  inspected Linux 7.2.6 Qualcomm DTS directory.
- No explicit SM7250 driver references were found in the inspected
  Qualcomm clock, pinctrl, GPU, UFS, PHY and SoC driver directories.
- SM6350 and SM7225 device-tree definitions are present.
- SM6350 provides a useful hardware-comparison reference.
- SM6350 compatibility with SM7250 is not established.

## UFS controller comparison

The vendor Lito and mainline SM6350 descriptions share:

- Controller base address: 0x01d84000.
- Controller register size: 0x3000.
- ICE register address: 0x01d90000.
- ICE register size: 0x8000.
- Controller interrupt: GIC SPI 265.
- UFS PHY base address: 0x01d87000.
- Two UFS lanes declared by the controller.

These matches establish similarities in hardware descriptions,
not proven driver compatibility.

## UFS PHY differences

- Vendor PHY register size: 0xE00.
- Mainline SM6350 PHY register size: 0x1000.
- Vendor PHY uses ref_clk_src, ref_clk and ref_aux_clk names.
- Mainline PHY uses ref, ref_aux and qref names.
- Vendor PHY references Qualcomm qphy.lvl RPMh resources.
- Mainline PHY uses power-domain and reset bindings.
- Actual SM7250 PHY revision and supported driver are unverified.

Vendor-specific device-tree bindings must not be copied directly
into mainline without reviewing upstream drivers and bindings.

## Known gaps

- Dedicated SM7250 SoC device-tree support is not established.
- Pixel 5a board device tree is absent from inspected upstream files.
- Clock, pinctrl, interconnect and regulator compatibility is unverified.
- UFS storage initialization is unverified.
- Display, touchscreen, GPU and power management are unverified.
- Fedora bootc/OSTree integration is not implemented.
- Android boot-image and initramfs integration is not implemented.

## Investigation priorities

1. Validate UFS controller and PHY compatibility.
2. Identify SM7250 clock and pinctrl requirements.
3. Review interconnect, regulators and power domains.
4. Establish a minimal mainline SoC and Barbet device-tree plan.
5. Investigate display, touchscreen and graphics.
6. Design a reproducible isolated kernel build.
7. Develop and validate an Android boot-image strategy.

## Safety

No device boot, flashing, partition writes or kernel build
is authorized by this investigation.

Armada's existing production kernel path remains unchanged.

## Clock and pin-controller investigation

### Google Lito vendor reference

The Google-derived Linux 4.19 source contains dedicated drivers:

- gcc-lito.c
- dispcc-lito.c
- gpucc-lito.c
- camcc-lito.c
- videocc-lito.c
- npucc-lito.c
- pinctrl-lito.c

Observed compatible strings include:

- qcom,gcc-lito
- qcom,lito-dispcc
- qcom,lito-gpucc
- qcom,lito-pinctrl

The vendor Lito pinctrl definition declares 146 GPIOs.

### Linux 7.2.6 reference

The inspected upstream source contains SM6350 implementations:

- gcc-sm6350.c
- dispcc-sm6350.c
- gpucc-sm6350.c
- camcc-sm6350.c
- videocc-sm6350.c
- pinctrl-sm6350.c

The SM6350 pinctrl definition declares 157 GPIOs.

Both inspected device trees place GCC at address 0x00100000.

### Compatibility assessment

- The matching GCC base address does not establish clock compatibility.
- Lito and SM6350 use distinct compatible strings.
- GPIO counts differ: Lito has 146 and SM6350 has 157.
- Clock tables, reset mappings and pin functions require comparison.
- Reusing the SM6350 pinctrl driver unchanged is not justified.
- A dedicated SM7250 driver or verified upstream extension may be needed.

No mainline SM7250 clock or pinctrl implementation is claimed.

### Proposed early implementation order

1. Compare GCC clock and reset maps.
2. Compare TLMM register layout and pin functions.
3. Identify required DT binding definitions.
4. Establish minimal interrupt and clock infrastructure.
5. Investigate UFS storage and required power dependencies.
6. Design the Barbet-specific device tree.

All implementation remains deferred pending further verification.

## GCC clock and reset mapping comparison

### Controller structure

The Google Lito GCC and upstream SM6350 GCC implementations
both use 32-bit registers with a four-byte register stride.

- Lito GCC base address: 0x00100000.
- SM6350 GCC base address: 0x00100000.
- Lito maximum register: 0x9C100.
- SM6350 maximum register: 0xBF030.
- The SM6350 descriptor includes GDSC definitions.
- The inspected Lito descriptor does not include GDSCs.

### Verified reset register differences

| Reset | Lito offset | SM6350 offset |
| --- | --- | --- |
| UFS PHY | 0x77000 | 0x3A000 |
| USB 3 primary | 0xF000 | 0x1A000 |
| USB 3 PHY primary | 0x50000 | 0x1C000 |
| USB 3 DP PHY | 0x50008 | 0x1C008 |
| QUSB2 primary PHY | 0x12000 | 0x1D000 |

These offsets come from the inspected driver reset maps.

### UFS clock definitions

Both implementations expose similarly named UFS clocks,
including AXI, AHB, ICE, PHY AUX and UniPro clocks.

One observed naming difference:

- Lito: GCC_UFS_1X_CLKREF_CLK.
- SM6350: GCC_UFS_MEM_CLKREF_CLK.

Individual clock register offsets, frequency tables and
parent relationships have not yet been verified.

### Engineering implications

The differing reset offsets prevent treating the SM6350 GCC
driver as a verified drop-in replacement for Lito.

A dedicated SM7250 implementation or carefully validated
adaptation must be evaluated against the vendor register maps,
modern upstream interfaces and device-tree bindings.

No kernel driver compatibility or successful hardware
initialization is established by these comparisons.

### UFS clock branch register comparison

The inspected clock drivers use different register offsets:

| Resource | Lito offset | SM6350 offset |
| --- | --- | --- |
| UFS PHY AHB clock | 0x77018 | 0x3A00C |
| UFS PHY AXI clock | 0x77010 | 0x3A034 |
| UFS PHY reset | 0x77000 | 0x3A000 |

Both implementations use Qualcomm clock-branch mechanisms, but
their hardware register offsets are not interchangeable.

The register comparison supports investigating a dedicated
SM7250 GCC implementation. It does not establish that copying
the Android vendor driver into Linux 7.2.6 would work.

## Linux 7.2.6 integration results

### Research baseline

- Kernel release: Linux 7.2.6.
- Baseline commit: `500df175a7f9e6bc1a9c328590ca5150f84f9ff0`.
- Integration performed in a separate Linux Git worktree.
- Armada's production kernel build was not modified.
- No phone partitions were modified.

### Upstream SM7250 patches

The Linux mailing-list SM7250 v9 series contains 12 patches.

Original archive SHA-256:

`d373f01d028a00583b37f435359ea946c1fbaaa75e90bb2b9dd96910841bda59`

The series introduces:

- SM7250 SoC identification.
- SM7250 GCC driver and clock definitions.
- RPMh clock and power-domain support.
- SM7250 device-tree definitions.
- Relevant device-tree bindings.

### Linux 7.2.6 adaptations

The integration required a GCC binding prerequisite and
an RPMh binding adaptation.

The GCC prerequisite was reconstructed from a public
mailing-list HTML archive whose displayed content contained
abbreviated email addresses and an abbreviated node name.

It is not a byte-for-byte copy of the accepted upstream commit.

Corrected GCC prerequisite SHA-256:

`d46d2032f3d85a5f2537a3055374c22461d6c42daa1a2d2eb24b026224373ffd`

RPMh binding adaptation SHA-256:

`1a43a5b9c371bcdae95cbb1dddda6e4ec800df4638def07c515e0eb1ec11d154`

Additional research-worktree changes:

- Explicit memory-timer address translation.
- Conditional SM7250 GCC clock-name and power-domain constraints.

These additional changes have not been submitted upstream
or integrated into Armada's production kernel patches.

### Host-side verification

The following checks succeeded:

- SM7250 patch application against Linux 7.2.6.
- SM7250 GCC driver compilation with the AArch64 cross-compiler.
- ARM64 ELF object verification.
- SM7250 device-tree preprocessing and DTB compilation.
- Device-tree schema generation using `dtschema` 2026.9.
- Synthetic SM7250 DTB schema validation: zero diagnostics.
- GCC binding-document and example validation.
- Git whitespace validation.

The synthetic DTB is not a deployable Pixel 5a board DTB.

Two `dtc` interrupt-provider warnings remain for the
GICv3 and Qualcomm PDC nodes. They were not resolved
by adding unverified hardware properties.

### Outstanding hardware support

The initial SM7250 device tree does not provide complete
Pixel 5a hardware support.

Priorities for subsequent development:

1. SM7250 TLMM/pinctrl support.
2. UFS storage-controller and PHY support.
3. Pixel 5a (`barbet`) board-specific device tree.
4. USB, GPU, display, regulators and other peripherals.
5. Comprehensive build and hardware validation.

No successful Pixel 5a mainline kernel boot has been
demonstrated.

### Production integration policy

Keep experimental SM7250 source changes isolated until
their dependencies, device-tree correctness, and relevant
hardware support have been validated.

Do not install, flash, or boot-test experimental kernel
artifacts without a separate, explicitly approved plan.
