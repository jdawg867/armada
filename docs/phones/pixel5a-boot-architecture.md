# Pixel 5a Boot Architecture

## Device

- Manufacturer: Google
- Model: Pixel 5a
- Codename: barbet
- SoC: Qualcomm SM7250
- Hardware revision: MP1.0
- Bootloader: unlocked
- Active Android slot during audit: B

## Stock firmware reference

- Android: 12
- Build: SQ1A.220205.002
- Build ID: 8010174
- Kernel: Linux 4.19.202
- Factory image SHA-256: a18455ecd4cf8220cfdb99b165766ddaab7856cc278d82d636595d9c144f9c5a

## Boot images

- boot.img: Android header version 3
- vendor_boot.img: vendor header version 3
- dtbo.img: 11 entries
- Kernel compression: LZ4
- Generic ramdisk compression: LZ4
- Vendor ramdisk compression: LZ4
- Base DTB compatible: qcom,lito

## Hardware revision

Android reports MP1.0.

DTBO entry 00 identifies:
- Model: Google Inc. MSM sm7250 v2 Barbet MP
- Compatible: google,barbet-sm7250; qcom,sm7250
- Board ID: 0x102805

Entry 00 is a candidate, not a verified bootloader selection.

## Armada requirements

- Preserve Fedora bootc and OSTree.
- Support Android boot and vendor_boot header v3.
- Respect device-tree and DTBO selection requirements.
- Investigate Pixel 5a kernel configuration and drivers.
- Develop a compatible initramfs strategy.
- Maintain a verified Android recovery reference.

## Safety

No flashing, partition writes, or boot experiments
were performed during this architecture audit.

This document does not establish Armada bootability.

## Experimental vendor-kernel compatibility assessment

### Existing development reference

- Source: Ubuntu Touch Barbet kernel workspace (external to Armada).
- Source version: Linux 4.19.160.
- Source commit: 8a77a608b84ddf2673d4ba34ef977e378ba49925.
- Compiled kernel release: 4.19.160-ge469934bead0.
- Compiled artifacts: ARM64 Image, Image.lz4 and kernel modules.
- Installed stock Android kernel: Linux 4.19.202.

The existing source is not an exact match for the installed stock kernel.

### Hardware and early-boot findings

- EXT4, initramfs, LZ4 decompression and Device Mapper are enabled.
- DM-Verity, OverlayFS and kernel module loading are enabled.
- Qualcomm UFS, SCM, DRM and USB DWC3 are configured as modules.
- The inspected modules report matching kernel-release metadata.
- All five direct dependencies reported for ufs_qcom.ko were found.
- The staged module tree contains modules.dep and modules.alias.
- A host-side modprobe dry run resolved UFS module dependencies.
- No modules were loaded during that dry run.

### Known limitations

- EROFS and SquashFS are disabled in the inspected configuration.
- CONFIG_CGROUP_PIDS is disabled.
- CONFIG_CGROUP2_FS was not present in the inspected configuration.
- Fedora/systemd compatibility has not been established.
- Kernel-module packaging for an Armada initramfs is not implemented.
- Graphics, touchscreen, power and networking are not validated.
- The installed stock kernel is newer than the development reference.

### Initial compatibility checker

The script scripts/check-pixel5a-kernel.py checks selected kernel
configuration options. Required options must be built in, while selected
hardware drivers may be built in or modular.

The checker is an initial project policy, not a universal Fedora
requirement or proof of bootability. In particular, modular filesystem
support can be viable with an appropriately configured initramfs.

Synthetic positive and negative tests are provided by
tests/pixel5a-kernel-compat-test.sh.

The checker does not verify module dependency closure, boot image
correctness, a running Fedora userspace or hardware functionality.

### Development strategy

- Preserve Armada's existing mainline kernel build.
- Investigate upstream Qualcomm SM7250 and Barbet support.
- Keep the Linux 4.19 vendor kernel as an experimental reference.
- Do not transplant vendor device trees into mainline without reviewing
  compatible drivers and device-tree bindings.
- Implement and test Android boot image integration separately.
- Require explicit review before any device boot or flashing experiment.

No bootability claim or production kernel selection is made here.
