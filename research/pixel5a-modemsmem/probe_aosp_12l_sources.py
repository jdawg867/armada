#!/usr/bin/env python3
"""Read-only probe for exact AOSP Barbet/Redbull Android 12L source tags.

Only fetches PUBLIC TEXT source files; never factory images or firmware.
No result from this script proves a vendor_boot binary or runtime probe order.
"""
import argparse
import base64
import hashlib
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TAGS = ("android-12.1.0_r1", "android-12.1.0_r5", "android-12.1.0_r7")
FILES = {
    "barbet": ("init.insmod.barbet.cfg", "barbet/init.barbet.rc"),
    "redbull": ("BoardConfig-common.mk", "modules.load", "init.hardware.rc", "init.insmod.sh"),
}
MARKERS = ("modemsmem.ko", "smem.ko", "subsys-pil-tz.ko",
           "vendor.all.modules.ready", "modprobe|-b *", "BOOT_KERNEL_MODULES")
BASE = "https://android.googlesource.com/device/google"

def safe_ref(ref):
    if not re.fullmatch(r"android-12\.1\.0_r(?:1|5|7)", ref):
        raise ValueError("unexpected AOSP tag")
    return ref

def source_url(device, tag, path):
    if device not in FILES or path not in FILES[device]:
        raise ValueError("unexpected source path")
    return f"{BASE}/{device}/+/refs/tags/{safe_ref(tag)}/{path}?format=TEXT"

def inspect(text):
    """Report only marker presence, not a claim about actual stock binaries."""
    return {key: key in text for key in MARKERS}

def decode_blob(encoded):
    raw=base64.b64decode(encoded, validate=True)
    return raw.decode("utf-8")

def fetch_one(device, tag, path, timeout=20):
    address=source_url(device, tag, path)
    result={"repository": f"device/google/{device}", "tag": tag,
            "path": path, "state": "unavailable",
            "stock_vendor_boot_verified": False}
    try:
        req=Request(address, headers={"User-Agent":"Armada-source-only-review/1.0"})
        with urlopen(req, timeout=timeout) as stream:
            data=decode_blob(stream.read())
        result.update(state="retrieved", sha256=hashlib.sha256(data.encode()).hexdigest(),
                      lines=len(data.splitlines()), markers=inspect(data))
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error, HTTPError):
            result["http_status"]=error.code
    return result

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--online", action="store_true",
                    help="fetch published AOSP text files with no firmware access")
    ap.add_argument("--output", default="",
                    help="write a bounded JSON manifest to a runner temp file")
    args=ap.parse_args(argv)
    result={"schema_version":1, "scope":"official_AOSP_tag_source_only",
            "stock_vendor_boot_verified":False,"hardware_tested":False,
            "entries":[]}
    if args.online:
        for tag in TAGS:
            for repo, paths in FILES.items():
                for path in paths:
                    result["entries"].append(fetch_one(repo, tag, path))
    result["retrieved_count"]=sum(x["state"]=="retrieved" for x in result["entries"])
    result["unavailable_count"]=sum(x["state"]=="unavailable" for x in result["entries"])
    result["all_files_retrieved"]=(len(result["entries"])==len(TAGS)*sum(map(len,FILES.values()))
                                   and result["unavailable_count"]==0)
    serialized=json.dumps(result,indent=2,sort_keys=True)
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(serialized+"\n")
    print(serialized)
    print("AOSP_TAG_SOURCE_PROBE=complete; STOCK_VENDOR_BOOT_VERIFIED=false")
    return 0

if __name__=="__main__":
    sys.exit(main())
