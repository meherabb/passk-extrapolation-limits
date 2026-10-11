#!/usr/bin/env python3
"""Verify the integrity of the shipped results and the paper assets (standard library only).

Checks
  1. every file listed in results/SHA256SUMS.txt exists and has the recorded SHA-256;
  2. nothing in results/ is missing from that list, except the three files the notebook writes last
     (SHA256SUMS.txt itself, README.md and file_inventory.csv);
  3. every PDF in paper/figures/ is byte-identical to the PDF of the same name in results/01_figures/pdf/.

    python tools/verify_checksums.py [--results results] [--paper paper]

Exit status 0 if everything matches, 1 otherwise.
"""
import argparse
import hashlib
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNLISTED_OK = {"SHA256SUMS.txt", "README.md", "file_inventory.csv"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--results", default=os.path.join(REPO, "results"))
    ap.add_argument("--paper", default=os.path.join(REPO, "paper"))
    args = ap.parse_args(argv)
    problems = 0

    sums_path = os.path.join(args.results, "SHA256SUMS.txt")
    if not os.path.isfile(sums_path):
        print(f"missing {sums_path}")
        return 1
    listed = {}
    with open(sums_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            digest, _, rel = line.partition("  ")
            listed[rel.strip()] = digest.strip()
    bad = missing = 0
    for rel, digest in sorted(listed.items()):
        path = os.path.join(args.results, *rel.split("/"))
        if not os.path.isfile(path):
            print(f"MISSING  {rel}")
            missing += 1
        elif sha256(path) != digest:
            print(f"CHANGED  {rel}")
            bad += 1
    print(f"results/SHA256SUMS.txt: {len(listed)} files listed, {len(listed) - bad - missing} match, "
          f"{bad} changed, {missing} missing")
    problems += bad + missing

    present = set()
    for root, _dirs, files in os.walk(args.results):
        for fn in files:
            present.add(os.path.relpath(os.path.join(root, fn), args.results).replace(os.sep, "/"))
    extra = sorted(p for p in present - set(listed) if p not in UNLISTED_OK)
    for p in extra:
        print(f"NOT LISTED  {p}")
    print(f"files in results/ that are not in SHA256SUMS.txt (besides {', '.join(sorted(UNLISTED_OK))}): {len(extra)}")
    problems += len(extra)

    figs = os.path.join(args.paper, "figures")
    mism = 0
    n = 0
    if os.path.isdir(figs):
        for fn in sorted(os.listdir(figs)):
            if not fn.endswith(".pdf"):
                continue
            n += 1
            src = os.path.join(args.results, "01_figures", "pdf", fn)
            if not os.path.isfile(src):
                print(f"NO SOURCE  paper/figures/{fn} has no counterpart in results/01_figures/pdf/")
                mism += 1
            elif sha256(src) != sha256(os.path.join(figs, fn)):
                print(f"DIFFERS    paper/figures/{fn} is not identical to results/01_figures/pdf/{fn}")
                mism += 1
    print(f"paper/figures: {n} PDFs, {n - mism} identical to the results archive, {mism} not")
    problems += mism

    print("OK" if problems == 0 else f"FAILED ({problems} problem(s))")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
