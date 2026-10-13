#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

CHECKER="$ROOT/scripts/check-pixel5a-kernel.py"

cat > "$WORK/valid.config" <<'CONFIG'
CONFIG_MODULES=y
CONFIG_BLK_DEV_INITRD=y
CONFIG_RD_LZ4=y
CONFIG_DEVTMPFS=y
CONFIG_EXT4_FS=y
CONFIG_BLK_DEV_DM=y
CONFIG_DM_VERITY=y
CONFIG_SCSI_UFS_QCOM=m
CONFIG_QCOM_SCM=m
CONFIG_DRM_MSM=m
CONFIG_USB_DWC3=m
CONFIG_OVERLAY_FS=y
CONFIG
python3 "$CHECKER" "$WORK/valid.config" > "$WORK/result"

grep -q 'PASS CONFIG_EXT4_FS y' "$WORK/result"
grep -q 'FOUND CONFIG_SCSI_UFS_QCOM m' "$WORK/result"

sed 's/CONFIG_EXT4_FS=y/# CONFIG_EXT4_FS is not set/' "$WORK/valid.config" > "$WORK/invalid.config"

if python3 "$CHECKER" "$WORK/invalid.config" > "$WORK/invalid-result"; then
    echo "FAIL: Missing EXT4 was accepted" >&2
    exit 1
fi

grep -q 'FAIL CONFIG_EXT4_FS n' "$WORK/invalid-result"


# Missing Qualcomm UFS must fail.
sed 's/CONFIG_SCSI_UFS_QCOM=m/# CONFIG_SCSI_UFS_QCOM is not set/' "$WORK/valid.config" > "$WORK/no-ufs.config"

if python3 "$CHECKER" "$WORK/no-ufs.config" > "$WORK/no-ufs-result"; then
    echo "FAIL: Missing UFS driver was accepted" >&2
    exit 1
fi
grep -q 'MISSING CONFIG_SCSI_UFS_QCOM n' "$WORK/no-ufs-result"

# Missing Qualcomm DRM must fail.
sed 's/CONFIG_DRM_MSM=m/# CONFIG_DRM_MSM is not set/' "$WORK/valid.config" > "$WORK/no-drm.config"

if python3 "$CHECKER" "$WORK/no-drm.config" > "$WORK/no-drm-result"; then
    echo "FAIL: Missing DRM driver was accepted" >&2
    exit 1
fi
grep -q 'MISSING CONFIG_DRM_MSM n' "$WORK/no-drm-result"

# Required EXT4 support must be built in.
sed 's/CONFIG_EXT4_FS=y/CONFIG_EXT4_FS=m/' "$WORK/valid.config" > "$WORK/modular-ext4.config"

if python3 "$CHECKER" "$WORK/modular-ext4.config" > "$WORK/modular-ext4-result"; then
    echo "FAIL: Modular EXT4 was accepted" >&2
    exit 1
fi
grep -q 'FAIL CONFIG_EXT4_FS m' "$WORK/modular-ext4-result"

echo "Pixel 5a kernel compatibility tests passed"
