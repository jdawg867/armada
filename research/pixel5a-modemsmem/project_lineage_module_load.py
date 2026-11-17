#!/usr/bin/env python3
"""Step 794: read-only LineageOS Barbet module-list projection and PIL audit.

Models only the specific pinned BoardConfigLineage.mk filter expressions:
  BOOT_KERNEL_MODULES += ...
  KERNEL_MODULES_LOAD = $(foreach ..., $(notdir ...))
  BOARD_VENDOR_RAMDISK_KERNEL_MODULES_LOAD = $(filter BOOT, LOAD)
  BOARD_VENDOR_KERNEL_MODULES_LOAD = $(filter-out BOOT, LOAD)

Does NOT execute GNU make, build vendor_boot, run modules, prove kernel probe
completion, assert a stock Android 12L binary, or permit any modem action.
"""
import argparse
import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT="https://raw.githubusercontent.com/LineageOS"
REFS={
 "redbull":"9fdf5ccfc9dd1ca22ca4ea657e414cb35e95b770",
 "barbet":"24101a383bb1951952adcd6f62668338dd048f03",
 "kernel":"929e7e2f3658867d51a1d423c7e000f5cf1d4043",
}
FILES={
 "board":("android_device_google_redbull","redbull","BoardConfig-common.mk"),
 "lineage":("android_device_google_redbull","redbull","BoardConfigLineage.mk"),
 "load":("android_device_google_redbull","redbull","modules.load"),
 "init":("android_device_google_redbull","redbull","init.insmod.sh"),
 "cfg":("android_device_google_barbet","barbet","init.insmod.barbet.cfg"),
 "pil":("android_kernel_google_redbull","kernel","drivers/soc/qcom/subsys-pil-tz.c"),
}
WATCH=("smem.ko","subsys-pil-tz.ko","modemsmem.ko")
MAX_BYTES=120000
def url(key):
    project,refname,path=FILES[key]
    return f"{ROOT}/{project}/{REFS[refname]}/{path}"

def fetch(key):
    req=Request(url(key),headers={"User-Agent":"Armada-Barbet-public-module-audit/1.0"})
    with urlopen(req,timeout=25) as f:
        data=f.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:
        raise ValueError("source exceeds bounded limit")
    return data.decode("utf-8")

def assignment(text,key):
    lines=text.splitlines()
    begin=re.compile(r"^\s*"+re.escape(key)+r"\s*(?::|\+|\?)?=\s*(.*)$")
    for i,line in enumerate(lines):
        m=begin.match(line)
        if not m: continue
        payload=[]
        j=i
        part=m.group(1)
        while True:
            cont=part.rstrip().endswith("\\")
            part=part.rstrip().removesuffix("\\")
            payload.extend(part.split())
            if not cont: break
            j+=1
            if j>=len(lines): raise ValueError("unterminated make assignment")
            part=lines[j]
        return payload
    raise ValueError("missing "+key)

def evaluate(sources):
    board=assignment(sources["board"],"BOOT_KERNEL_MODULES")
    additions=assignment(sources["lineage"],"BOOT_KERNEL_MODULES")
    ordered=[line.strip().rsplit("/",1)[-1] for line in sources["load"].splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if len(ordered)!=len(set(ordered)):
        raise ValueError("duplicate module basename")
    allowed=set(board+additions)
    boot=[module for module in ordered if module in allowed]
    vendor=[module for module in ordered if module not in allowed]
    ranks={module:ordered.index(module) for module in WATCH if module in ordered}
    missing=[module for module in WATCH if module not in ranks]
    seen={name: { "in_common_boot_set":name in board,
                  "in_effective_boot_projection":name in boot,
                  "ordered_index_zero_based":ranks.get(name)} for name in WATCH}
    script=sources["init"]
    pil=sources["pil"]
    return {
      "schema_version":1,
      "scope":"pinned_LineageOS_source_projection_not_a_real_make_build",
      "source_refs":REFS,
      "source_urls":{key:url(key) for key in FILES},
      "ordered_modules_count":len(ordered),
      "boot_projection_count":len(boot),
      "vendor_projection_count":len(vendor),
      "common_boot_entries_count":len(board),
      "added_boot_entries_count":len(additions),
      "watched":seen,
      "missing_watched":missing,
      "pil_appears_before_modemsmem_in_list":ranks.get("subsys-pil-tz.ko",-1) < ranks.get("modemsmem.ko",-1)
           if not missing else False,
      "module_loader_checks_modprobe_status":False if (
        "modprobe -a -d /vendor/lib/modules $arg" in script
        and "setprop vendor.all.modules.ready 1" in script) else None,
      "pil_powerup_calls_pil_boot":"ret = pil_boot(&d->desc);" in pil,
      "pil_probe_registers_subsystem":"subsys_register(&d->subsys_desc)" in pil,
      "pil_probe_requires_modemsmem_publication":False,
      "actual_stock_vendor_boot_verified":False,
      "module_probe_completion_verified":False,
      "actual_modem_start_order_verified":False,
      "hardware_tested":False,
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--online",action="store_true")
    parser.add_argument("--output",default="")
    args=parser.parse_args()
    if not args.online:
        print("SOURCE_ONLY_NO_NETWORK=PASS")
        return
    sources={key:fetch(key) for key in FILES}
    report=evaluate(sources)
    if report["missing_watched"]: raise SystemExit("required listed modules missing")
    if report["module_loader_checks_modprobe_status"] is None:
        raise SystemExit("loader source contract changed; review manually")
    if not report["pil_powerup_calls_pil_boot"] or not report["pil_probe_registers_subsystem"]:
        raise SystemExit("pinned PIL source contract changed")
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    print("SOURCE_ONLY_STOCK_VENDOR_BOOT_VERIFIED=false")

if __name__=="__main__":
    main()
