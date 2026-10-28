#!/usr/bin/env python3
"""Source-only SM7250 ICC index audit; does not build or enable any kernel driver.

Usage: python3 tests/sm7250-icc-index-check.py HEADER SOURCE
Run --self-test for synthetic fixture tests used by CI.

Checks only explicitly indexed entries of the form [MASTER_FOO] = &node.
The source parser is deliberately narrow: it is NOT a C parser or hardware proof.
"""
import argparse
from pathlib import Path
import re
import sys
import unittest

DEFINE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s+(0[xX][\da-fA-F]+|\d+)\b", re.M)
INDEX = re.compile(r"\[\s*([A-Za-z_]\w*)\s*\]\s*=\s*&\s*[A-Za-z_]\w*")
PREFIXES = ("MASTER_", "SLAVE_")
# Lightweight comment stripping for source-only index evidence. This is
# intentionally not a full C lexer; string-literal false positives remain
# outside the validator's supported subset.
COMMENT = re.compile(r"/\\*[\\s\\S]*?\\*/|//[^\\n]*")


def without_comments(text: str) -> str:
    return COMMENT.sub(lambda m: re.sub(r"[^\\n]", " ", m.group()), text)


def audit(header: str, source: str) -> list[str]:
    problems = []
    definitions = {}
    ids = {}
    for symbol, raw in DEFINE.findall(without_comments(header)):
        if not symbol.startswith(PREFIXES):
            continue
        value = int(raw, 0)
        if symbol in definitions:
            problems.append(f"duplicate definition: {symbol}")
        if value in ids and ids[value] != symbol:
            problems.append(f"duplicate numeric ID {value}: {ids[value]} and {symbol}")
        definitions[symbol] = value
        ids[value] = symbol

    if not definitions:
        problems.append("no literal MASTER_/SLAVE_ binding IDs found")

    seen = set()
    slots = {}
    found = 0
    for symbol in INDEX.findall(without_comments(source)):
        if not symbol.startswith(PREFIXES):
            continue
        found += 1
        if symbol in seen:
            problems.append(f"duplicate indexed node: {symbol}")
        seen.add(symbol)
        if symbol not in definitions:
            problems.append(f"undefined node index: {symbol}")
            continue
        value = definitions[symbol]
        if value in slots and slots[value] != symbol:
            problems.append(f"index collision {value}: {slots[value]} and {symbol}")
        slots[value] = symbol

    if not found:
        problems.append("no explicit MASTER_/SLAVE_ indexed node entries found")
    return problems


class SyntheticTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(audit("#define MASTER_A 0\n#define SLAVE_B 1\n",
                               "[MASTER_A] = &a, [SLAVE_B] = &b,"), [])

    def test_undefined(self):
        self.assertTrue(any("undefined" in p for p in
                            audit("#define MASTER_A 0", "[MASTER_X] = &x")))

    def test_numeric_collision(self):
        self.assertTrue(any("duplicate numeric" in p for p in
                            audit("#define MASTER_A 0\n#define SLAVE_B 0",
                                  "[MASTER_A] = &a, [SLAVE_B] = &b")))

    def test_duplicate_slot(self):
        self.assertTrue(any("duplicate indexed" in p for p in
                            audit("#define MASTER_A 0",
                                  "[MASTER_A] = &a, [MASTER_A] = &b")))

    def test_commented_entries_not_counted(self):
        header = "#define MASTER_A 0\\n#define SLAVE_B 1"
        source = "/* [MASTER_A] = &fake, */ [SLAVE_B] = &real, // [SLAVE_B] = &fake"
        self.assertEqual(audit(header, source), [])

    def test_commented_definitions_not_counted(self):
        header = "/* #define MASTER_A 0 */\\n#define SLAVE_B 1"
        self.assertTrue(any("undefined" in p for p in
                            audit(header, "[MASTER_A] = &a, [SLAVE_B] = &b")))

    def test_missing_data_fails_closed(self):
        self.assertTrue(audit("", ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("header", type=Path, nargs="?")
    parser.add_argument("source", type=Path, nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        if args.header or args.source:
            parser.error("--self-test takes no paths")
        result = unittest.main(argv=[sys.argv[0]], exit=False)
        return 0 if result.result.wasSuccessful() else 1
    if not args.header or not args.source:
        parser.error("provide both binding header and C source")
    for path in (args.header, args.source):
        if not path.is_file() or path.is_symlink():
            parser.error(f"not a regular source file: {path}")
    problems = audit(args.header.read_text(encoding="utf-8"),
                     args.source.read_text(encoding="utf-8"))
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print("PASS: literal ICC binding/index consistency (limited static check)")
    print("NOT VERIFIED: array selection, endpoint graph, BCM/QoS, DT, build, or hardware")
    return 0


if __name__ == "__main__":
    sys.exit(main())
