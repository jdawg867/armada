#!/usr/bin/env python3
"""Step 824 regression tests: synthetic, offline modules.dep only."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/pixel5a-modemsmem/analyze_modules_dep_offline.py"
spec = importlib.util.spec_from_file_location("armada_dep824", SCRIPT)
dep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dep)

BASE = """kernel/smem.ko:
kernel/msm_bus.ko: kernel/smem.ko
kernel/subsys-pil-tz.ko: kernel/msm_bus.ko kernel/smem.ko
kernel/modemsmem.ko: kernel/smem.ko
"""

class DependencyGraphTests(unittest.TestCase):
    def test_baseline_graph(self):
        graph = dep.parse_dep(BASE)
        self.assertEqual(len(graph), 4)
        self.assertEqual(dep.resolve(graph, ["kernel/subsys-pil-tz.ko"]),
                         ["kernel/smem.ko", "kernel/msm_bus.ko", "kernel/subsys-pil-tz.ko"])

    def test_disjoint_targets(self):
        order = dep.resolve(dep.parse_dep(BASE),
                            ["kernel/modemsmem.ko", "kernel/subsys-pil-tz.ko"])
        self.assertEqual(order, ["kernel/smem.ko", "kernel/modemsmem.ko",
                                 "kernel/msm_bus.ko", "kernel/subsys-pil-tz.ko"])

    def test_report_is_not_runtime_proof(self):
        r = dep.report(BASE, ["kernel/subsys-pil-tz.ko"])
        self.assertEqual(r["scope"], "offline_explicit_modules_dep_dependency_topology_only")
        self.assertFalse(r["dependency_order_is_runtime_load_order"])
        self.assertFalse(r["module_insertion_performed"])
        self.assertFalse(r["probe_completion_verified"])
        self.assertFalse(r["modem_boot_order_verified"])
        self.assertFalse(r["modemsmem_item134_ready_verified"])
        self.assertFalse(r["telephony_verified"])

    def test_empty(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("")

    def test_missing_colon(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("a.ko")

    def test_duplicate_module(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("a.ko:\na.ko:\n")

    def test_duplicate_basename_with_exact_paths(self):
        graph = dep.parse_dep("x/a.ko:\ny/a.ko: x/a.ko\n")
        self.assertEqual(dep.resolve(graph, ["y/a.ko"]), ["x/a.ko", "y/a.ko"])

    def test_duplicate_dependency(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("a.ko: b.ko b.ko\nb.ko:\n")

    def test_missing_dependency(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("a.ko: absent.ko\n")

    def test_self_dependency(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("a.ko: a.ko\n")

    def test_cycle(self):
        graph = dep.parse_dep("a.ko: b.ko\nb.ko: a.ko\n")
        with self.assertRaises(dep.DependencyError): dep.resolve(graph, ["a.ko"])

    def test_missing_target(self):
        with self.assertRaises(dep.DependencyError): dep.resolve(dep.parse_dep(BASE), ["missing.ko"])

    def test_empty_target_list(self):
        with self.assertRaises(dep.DependencyError): dep.resolve(dep.parse_dep(BASE), [])

    def test_duplicate_target(self):
        with self.assertRaises(dep.DependencyError):
            dep.resolve(dep.parse_dep(BASE), ["kernel/smem.ko", "kernel/smem.ko"])

    def test_path_traversal(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("../a.ko:\n")

    def test_absolute_path(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("/lib/a.ko:\n")

    def test_dot_path(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("./a.ko:\n")

    def test_bad_colon(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("a.ko: b: c\n")

    def test_nonmodule(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("a.txt:\n")

    def test_xz_module(self):
        self.assertEqual(dep.resolve(dep.parse_dep("a.ko.xz:\n"), ["a.ko.xz"]), ["a.ko.xz"])

    def test_utf8_size_limit(self):
        with self.assertRaises(dep.DependencyError): dep.parse_dep("x" * (dep.MAX_BYTES + 1))

    def test_no_network_or_kernel_mutation(self):
        code=SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("urllib", "requests", "subprocess", "modprobe ", "insmod ", "/dev/subsys_modem", "rproc_boot("):
            self.assertNotIn(forbidden, code)

    def test_cli_input_required(self):
        result=subprocess.run([sys.executable,str(SCRIPT)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_cli_explicit_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"modules.dep"
            p.write_text(BASE,encoding="utf-8")
            result=subprocess.run([sys.executable,str(SCRIPT),"--modules-dep",str(p),
                                   "--target","kernel/subsys-pil-tz.ko"],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            self.assertEqual(report["module_entries"],4)
            self.assertFalse(report["probe_completion_verified"])

    def test_cli_symlink_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"modules.dep"
            p.write_text(BASE,encoding="utf-8")
            link=Path(tmp)/"link"
            link.symlink_to(p)
            r=subprocess.run([sys.executable,str(SCRIPT),"--modules-dep",str(link),
                              "--target","kernel/smem.ko"],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)


    def test_compressed_gzip_zstd_modules(self):
        graph=dep.parse_dep("kernel/a.ko.zst: kernel/b.ko.gz\\nkernel/b.ko.gz:\\n")
        self.assertEqual(dep.resolve(graph, ["kernel/a.ko.zst"]),
                         ["kernel/b.ko.gz", "kernel/a.ko.zst"])

    def test_deep_acyclic_chain_not_python_recursion(self):
        lines=["x/m0.ko:"]
        lines.extend("x/m%d.ko: x/m%d.ko" % (i, i-1) for i in range(1, 1700))
        graph=dep.parse_dep("\\n".join(lines)+"\\n")
        order=dep.resolve(graph,["x/m1699.ko"])
        self.assertEqual(len(order),1700)
        self.assertEqual(order[0],"x/m0.ko")
        self.assertEqual(order[-1],"x/m1699.ko")

    def test_target_never_ambiguous_basename(self):
        graph=dep.parse_dep("x/a.ko:\\ny/a.ko:\\n")
        with self.assertRaises(dep.DependencyError):dep.resolve(graph,["a.ko"])

    def test_duplicate_basename_exact_paths_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"modules.dep"
            p.write_text("x/a.ko:\\ny/a.ko: x/a.ko\\n")
            r=subprocess.run([sys.executable,str(SCRIPT),"--modules-dep",str(p),
                              "--target","y/a.ko"],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(r.stdout)["dependency_first_candidate_order"],["x/a.ko","y/a.ko"])

if __name__ == "__main__":
    unittest.main()
