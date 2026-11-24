#!/usr/bin/env python3
"""Step 833: check an RFC diff against the entire pinned, Git-blob-verified driver.

Input must be a previously downloaded public source text file.
No network, kernel build, module loading, or phone access occurs here.
"""
import argparse
import difflib
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "research/pixel5a-modemsmem/review-only/0001-modemsmem-preserve-smem-deferred-probe.patch"
REL = Path("drivers/soc/qcom/modemsmem/modemsmem.c")
EXPECTED_BLOB = "428143562894e6d8ca7b656174c72ee4b096f510"
ORIGINAL = (
    "\tif (ret && ret != -EEXIST) {\n"
    '\t\tdev_err(dev, "smem alloc fail\\n");\n'
    "\t\treturn -ENOMEM;\n"
    "\t}\n\n"
    "\tmodem_smem = qcom_smem_get(QCOM_SMEM_HOST_ANY, SMEM_ID_VENDOR0, &size);\n"
    "\tif (IS_ERR(modem_smem) || size != sizeof(struct modem_smem_type)) {\n"
    '\t\tdev_err(dev, "Get modem_smem pointer failed\\n");\n'
    "\t\treturn -ENOMEM;\n"
    "\t}\n"
)
REPLACEMENT = (
    "\tif (ret && ret != -EEXIST) {\n"
    '\t\tdev_err(dev, "smem alloc fail\\n");\n'
    "\t\tif (ret == -EPROBE_DEFER)\n"
    "\t\t\treturn ret;\n"
    "\t\treturn -ENOMEM;\n"
    "\t}\n\n"
    "\tmodem_smem = qcom_smem_get(QCOM_SMEM_HOST_ANY, SMEM_ID_VENDOR0, &size);\n"
    "\tif (IS_ERR(modem_smem)) {\n"
    '\t\tdev_err(dev, "Get modem_smem pointer failed\\n");\n'
    "\t\tif (PTR_ERR(modem_smem) == -EPROBE_DEFER)\n"
    "\t\t\treturn -EPROBE_DEFER;\n"
    "\t\treturn -ENOMEM;\n"
    "\t}\n"
    "\tif (size != sizeof(struct modem_smem_type)) {\n"
    '\t\tdev_err(dev, "Get modem_smem pointer failed\\n");\n'
    "\t\treturn -ENOMEM;\n"
    "\t}\n"
)

def git_blob(raw):
    prefix = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(prefix + raw).hexdigest()

def check(source):
    if source.is_symlink() or not source.is_file():
        raise AssertionError("source must be a real file")
    raw = source.read_bytes()
    if git_blob(raw) != EXPECTED_BLOB:
        raise AssertionError("pinned Git blob mismatch; refuse unverified source")
    original = raw.decode("utf-8")
    if original.count(ORIGINAL) != 1:
        raise AssertionError("pinned error path occurs other than exactly once")
    if not PATCH.is_file() or PATCH.is_symlink():
        raise AssertionError("patch path invalid")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        dest = root / REL
        dest.parent.mkdir(parents=True)
        dest.write_bytes(raw)
        for arguments in (["--check"], []):
            run = subprocess.run(["git", "apply", *arguments, str(PATCH)],
                                 cwd=root, capture_output=True, text=True)
            if run.returncode:
                raise AssertionError("git apply failed: " + run.stderr)
        result = dest.read_text(encoding="utf-8")
        expected = original.replace(ORIGINAL, REPLACEMENT)
        if result != expected:
            diff = "\n".join(difflib.unified_diff(expected.splitlines(), result.splitlines()))
            raise AssertionError("patch changes outside reviewed error paths:\n" + diff)
    return {
        "pinned_source_blob_verified": True,
        "full_pinned_file_patch_check": True,
        "full_pinned_file_patch_applied": True,
        "only_reviewed_error_paths_changed": True,
        "kernel_compilation_performed": False,
        "device_or_modem_access_performed": False,
    }

def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--source-file", type=Path, required=True)
    args = arg.parse_args()
    try:
        result = check(args.source_file)
    except (OSError, UnicodeError, AssertionError) as ex:
        print("FAIL_CLOSED: " + str(ex), file=sys.stderr)
        return 2
    for key, value in result.items():
        print("%s=%s" % (key.upper(), str(value).lower()))
    return 0

if __name__ == "__main__":
    sys.exit(main())
