#!/usr/bin/env python3
"""Step 824: offline, fail-closed parser for an explicitly supplied modules.dep.

No network, device, module insertion, modprobe, execution or firmware operations.
Produces only a dependency-ordered *candidate* list: not actual load/probe order.
"""
import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

MAX_BYTES = 2_000_000
MAX_MODULES = 20_000
MODULE = re.compile(r"^[A-Za-z0-9_+./-]+\.ko(?:\.(?:xz|gz|zst))?$")

class DependencyError(ValueError):
    pass

def canonical(token):
    if not token or not MODULE.fullmatch(token) or "\\" in token:
        raise DependencyError("invalid module token")
    p = PurePosixPath(token)
    if p.is_absolute() or ".." in p.parts or "." in p.parts or str(p) != token:
        raise DependencyError("unsafe or noncanonical module path")
    return token

def parse_dep(data):
    if not isinstance(data, str):
        raise DependencyError("expected UTF-8 text")
    if len(data.encode("utf-8")) > MAX_BYTES:
        raise DependencyError("modules.dep too large")
    # Full relative paths are authoritative. Equal basenames in different directories
    # are valid; only exact path targets are accepted, never basename resolution.
    graph = {}
    for num, raw in enumerate(data.splitlines(), 1):
        if not raw.strip():
            continue
        if ":" not in raw or raw.count(":") != 1:
            raise DependencyError("missing or ambiguous colon at line %d" % num)
        head, rest = raw.split(":", 1)
        name = canonical(head.strip())
        if name in graph:
            raise DependencyError("duplicate module entry: " + name)
        deps = tuple(canonical(item) for item in rest.split())
        if len(deps) != len(set(deps)):
            raise DependencyError("duplicate dependencies: " + name)
        graph[name] = deps
        if len(graph) > MAX_MODULES:
            raise DependencyError("too many modules")
    if not graph:
        raise DependencyError("empty modules.dep")
    for name, deps in graph.items():
        for dep in deps:
            if dep not in graph:
                raise DependencyError("missing dependency entry for " + dep)
            if dep == name:
                raise DependencyError("self dependency " + name)
    return graph

def resolve(graph, targets):
    if not targets:
        raise DependencyError("no requested module targets")
    # Target names must be exact paths, never ambiguous basename lookups.
    wanted = [canonical(x) for x in targets]
    if len(wanted) != len(set(wanted)):
        raise DependencyError("duplicate targets")
    for target in wanted:
        if target not in graph:
            raise DependencyError("target not in graph: " + target)
    state = {}
    order = []
    for target in wanted:
        if state.get(target) == 2:
            continue
        state[target] = 1
        stack = [(target, iter(graph[target]))]
        while stack:
            node, deps = stack[-1]
            try:
                child = next(deps)
            except StopIteration:
                state[node] = 2
                order.append(node)
                stack.pop()
                continue
            if state.get(child) == 1:
                raise DependencyError("dependency cycle at " + child)
            if state.get(child) == 2:
                continue
            state[child] = 1
            stack.append((child, iter(graph[child])))
    return order

def report(data, targets):
    graph = parse_dep(data)
    order = resolve(graph, targets)
    return {
        "schema_version": 1,
        "scope": "offline_explicit_modules_dep_dependency_topology_only",
        "module_entries": len(graph),
        "requested_targets": list(targets),
        "dependency_first_candidate_order": order,
        "dependency_order_is_runtime_load_order": False,
        "modprobe_alias_softdep_blacklist_evaluated": False,
        "module_insertion_performed": False,
        "probe_completion_verified": False,
        "modem_boot_order_verified": False,
        "modemsmem_item134_ready_verified": False,
        "telephony_verified": False,
    }

def read_metadata(path, label):
    if path is None:
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise DependencyError(label + " must be a bounded, regular, non-symlink file")
    return path.read_text(encoding="utf-8")

def classify_sidecar(text, name):
    if text is None:
        return "not_supplied"
    lines = [line.strip() for line in text.splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if name == "softdep" and lines:
        # modules.softdep may change insertion ordering, including pre/post
        # dependencies not visible in modules.dep; never silently ignore it.
        raise DependencyError("nonempty modules.softdep is unsupported: cannot infer runtime ordering")
    if name == "alias" and lines:
        # Alias patterns do not affect exact-path dependency topology directly,
        # but caller can never conclude actual alias resolution here.
        return "present_not_interpreted"
    return "empty"

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--modules-dep", type=Path, required=True,
                   help="existing local modules.dep; never fetches or loads modules")
    p.add_argument("--target", action="append", required=True,
                   help="exact relative module path present in modules.dep")
    p.add_argument("--modules-softdep", type=Path, default=None,
                   help="optional existing modules.softdep; fail closed if it defines rules")
    p.add_argument("--modules-alias", type=Path, default=None,
                   help="optional modules.alias; recorded but never resolved")
    args = p.parse_args(argv)
    try:
        if args.modules_dep.is_symlink() or not args.modules_dep.is_file():
            raise DependencyError("modules.dep must be a regular non-symlink file")
        if args.modules_dep.stat().st_size > MAX_BYTES:
            raise DependencyError("modules.dep too large")
        softdep_status = classify_sidecar(read_metadata(args.modules_softdep, "modules.softdep"), "softdep")
        alias_status = classify_sidecar(read_metadata(args.modules_alias, "modules.alias"), "alias")
        result = report(args.modules_dep.read_text(encoding="utf-8"), args.target)
        result["modules_softdep_status"] = softdep_status
        result["modules_alias_status"] = alias_status
        result["softdep_alias_metadata_complete"] = (softdep_status != "not_supplied" and alias_status != "not_supplied")
        result["modprobe_alias_softdep_blacklist_evaluated"] = False
    except (DependencyError, UnicodeError, OSError) as e:
        print("FAIL_CLOSED: " + str(e), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    sys.exit(main())
