#!/usr/bin/env python3
"""Compare exact AOSP 12L public text with pinned LineageOS text in GitHub CI.

Downloads allowlisted public source TEXT only. Never downloads firmware,
factory images, boot partitions or phone logs. No runtime-order claims.
"""
import argparse
import base64
import difflib
import hashlib
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TAGS=("android-12.1.0_r1","android-12.1.0_r5","android-12.1.0_r7")
SOURCE={
 "barbet":("LineageOS/android_device_google_barbet",
           "24101a383bb1951952adcd6f62668338dd048f03",
           ("init.insmod.barbet.cfg","barbet/init.barbet.rc")),
 "redbull":("LineageOS/android_device_google_redbull",
            "9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770",
            ("BoardConfig-common.mk","init.hardware.rc","init.insmod.sh")),
}
AOSP_BASE="https://android.googlesource.com/device/google"
GH_RAW="https://raw.githubusercontent.com"
MAX_TEXT=1_000_000

def target_urls(device,tag,path):
    if device not in SOURCE or tag not in TAGS or path not in SOURCE[device][2]:
        raise ValueError("unreviewed ref or path")
    owner,commit,_=SOURCE[device]
    return (
      f"{AOSP_BASE}/{device}/+/refs/tags/{tag}/{path}?format=TEXT",
      f"{GH_RAW}/{owner}/{commit}/{path}"
    )

def fetch_text(url,aosp=False,timeout=30):
    req=Request(url,headers={"User-Agent":"Armada-Pixel5a-public-source-audit/1.0"})
    with urlopen(req,timeout=timeout) as response:
        data=response.read(MAX_TEXT+1)
    if len(data)>MAX_TEXT:
        raise ValueError("file exceeds size limit")
    if aosp:
        data=base64.b64decode(data,validate=True)
    return data.decode("utf-8")

def comparison(aosp,lineage):
    aa=aosp.encode("utf-8")
    bb=lineage.encode("utf-8")
    al=aosp.splitlines()
    bl=lineage.splitlines()
    ops=difflib.SequenceMatcher(None,al,bl,autojunk=False).get_opcodes()
    return {
      "aosp_sha256":hashlib.sha256(aa).hexdigest(),
      "lineage_sha256":hashlib.sha256(bb).hexdigest(),
      "identical_bytes":aa==bb,
      "aosp_line_count":len(al),
      "lineage_line_count":len(bl),
      "hunks_changed":sum(n!="equal" for n,*_ in ops),
      "aosp_lines_changed":sum(j-i for n,i,j,k,l in ops if n!="equal"),
      "lineage_lines_changed":sum(l-k for n,i,j,k,l in ops if n!="equal"),
    }

def collect_one(device,tag,path,fetch=fetch_text):
    aosp_url,lineage_url=target_urls(device,tag,path)
    record={"device":device,"tag":tag,"path":path,
      "aosp_state":"unavailable","lineage_state":"unavailable",
      "compare_state":"not_compared","stock_vendor_boot_verified":False}
    try:
        aosp=fetch(aosp_url,aosp=True)
        record["aosp_state"]="retrieved"
    except (HTTPError,URLError,TimeoutError,UnicodeError,ValueError) as error:
        record["aosp_error_type"]=type(error).__name__
        if isinstance(error,HTTPError):
            record["aosp_http_status"]=error.code
        aosp=None
    try:
        lineage=fetch(lineage_url,aosp=False)
        record["lineage_state"]="retrieved"
    except (HTTPError,URLError,TimeoutError,UnicodeError,ValueError) as error:
        record["lineage_error_type"]=type(error).__name__
        if isinstance(error,HTTPError):
            record["lineage_http_status"]=error.code
        lineage=None
    if aosp is not None and lineage is not None:
        record.update(comparison(aosp,lineage))
        record["compare_state"]="compared"
    return record

def build_report(fetch=fetch_text):
    entries=[]
    for tag in TAGS:
        for device,(_,_,paths) in SOURCE.items():
            for path in paths:
                entries.append(collect_one(device,tag,path,fetch=fetch))
    return {
      "schema_version":1,
      "scope":"public_AOSP_vs_pinned_Lineage_source_text_only",
      "stock_vendor_boot_verified":False,
      "hardware_tested":False,
      "effective_modem_boot_order_verified":False,
      "entries":entries,
      "compared_count":sum(e["compare_state"]=="compared" for e in entries),
      "unavailable_count":sum(e["compare_state"]!="compared" for e in entries),
    }

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--online",action="store_true")
    parser.add_argument("--output",default="")
    args=parser.parse_args(argv)
    report=build_report() if args.online else {
      "schema_version":1,
      "scope":"public_AOSP_vs_pinned_Lineage_source_text_only",
      "stock_vendor_boot_verified":False,
      "hardware_tested":False,
      "effective_modem_boot_order_verified":False,
      "entries":[],"compared_count":0,"unavailable_count":0
    }
    data=json.dumps(report,sort_keys=True,indent=2)
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(data+"\n")
    print(data)
    return 0

if __name__=="__main__":
    sys.exit(main())
