#!/usr/bin/env python3
"""Source-only Step 793 bounded unified diff of AOSP r7 and pinned LineageOS.

Only allowlisted public text files. No binaries, partitions, kernel module
execution, boot trace, factory image or hardware access.
"""
import argparse
import difflib
import hashlib
import importlib.util
import json
import pathlib
import sys

HERE=pathlib.Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("compare_aosp_lineage_12l",HERE/"compare_aosp_lineage_12l.py")
compare=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare)
TAG="android-12.1.0_r7"
DIFFERENT=(
    ("barbet","barbet/init.barbet.rc"),
    ("redbull","BoardConfig-common.mk"),
    ("redbull","init.hardware.rc"),
)
MARKERS=("modem","smem","module","insmod","modprobe","pil","ssr","remoteproc",
         "init","ready","qcom","firmware","trigger","adsp","cdsp")

def make_diff(device,path,aosp,lineage):
    compare.target_urls(device,TAG,path)
    left=aosp.splitlines(keepends=True)
    right=lineage.splitlines(keepends=True)
    diff=list(difflib.unified_diff(left,right,fromfile=f"AOSP/{TAG}/{device}/{path}",
                  tofile=f"Lineage/pinned/{device}/{path}",n=3))
    changes=[x for x in diff if x.startswith(("+","-")) and not x.startswith(("+++","---"))]
    relevant=[x.rstrip("\n") for x in changes if any(m in x.lower() for m in MARKERS)]
    return {
      "device":device,"path":path,"aosp_sha256":hashlib.sha256(aosp.encode()).hexdigest(),
      "lineage_sha256":hashlib.sha256(lineage.encode()).hexdigest(),
      "identical_bytes":aosp==lineage,
      "changed_lines":len(changes),"keyword_changed_lines":relevant,
      "unified_diff":"".join(diff),
      "source_only":True,
    }

def one(device,path,fetch=compare.fetch_text):
    aosp_url,lineage_url=compare.target_urls(device,TAG,path)
    aosp=fetch(aosp_url,aosp=True)
    lineage=fetch(lineage_url,aosp=False)
    return make_diff(device,path,aosp,lineage)

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--online",action="store_true")
    parser.add_argument("--output",default="")
    args=parser.parse_args(argv)
    data={"schema_version":1,"tag":TAG,"scope":"public_AOSP_Lineage_diff_only",
          "stock_vendor_boot_verified":False,"modem_boot_order_verified":False,
          "source_content_semantically_reviewed":False,"files":[]}
    if args.online:
        for device,path in DIFFERENT:
            try:
                data["files"].append(one(device,path))
            except Exception as error:
                # Missing source never becomes a verified diff.
                data["files"].append({"device":device,"path":path,"state":"unavailable",
                    "error_type":type(error).__name__})
    data["retrieved_count"]=sum("unified_diff" in x for x in data["files"])
    data["all_diffs_available"]=data["retrieved_count"]==len(DIFFERENT)
    if args.output:
        pathlib.Path(args.output).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    print("SOURCE_DIFFS_RETRIEVED",data["retrieved_count"])
    print("SOURCE_DIFFS_COMPLETE",data["all_diffs_available"])
    for row in data["files"]:
        print("DIFF",row["device"],row["path"],row.get("changed_lines","unavailable"))
        if "unified_diff" in row:
            print(row["unified_diff"][:30000])
    print("STOCK_VENDOR_BOOT_VERIFIED=false")
    return 0

if __name__=="__main__":
    sys.exit(main())
