#!/usr/bin/env python3
"""Compare the results of a notebook run with the shipped results.

    python tools/compare_runs.py results runs/<workdir>/DoublingBarrier-..._results_local_<stamp>.zip

Each argument is either a results folder (the one that contains 02_tables/) or a master archive (.zip). The tool
compares, file by file,
  * the tables         02_tables/csv/*.csv      cell by cell, numbers within a relative/absolute tolerance
  * the LaTeX tables   02_tables/latex/*.tex    text
  * the raw results    03_logs/raw_results/*.csv, *.npz
  * the figure data    01_figures/data_json/*.json   (the series every figure is drawn from)
  * verdicts.json
and prints one line per category plus, for every file that differs, how many numbers differ and by how much. Figures
(PDF/PNG) are not compared byte for byte, because matplotlib embeds a creation date; their data files are compared
instead.

Tolerances. Tables, raw results and verdicts are compared with --rtol/--atol (default 1e-9 / 1e-12). The figure data
has its own --fig-rtol/--fig-atol (default: the same). Stages that end an iterative optimisation at a tolerance
(the cutting-plane linear programs behind the error floor, the likelihood-ratio simulation) can stop at a slightly
different point on another machine; `make reproduce-stages` therefore compares figure data with --fig-rtol 0.01 and
--fig-atol 1e-4 (see docs/reproducing.md).

Exit status 0 if every compared file is identical or equal within the tolerance, 1 otherwise.
Standard library only; numpy is used for .npz files if it is installed.
"""
import argparse
import csv
import io
import json
import math
import os
import re
import sys
import zipfile


class Source:
    """A results folder or a master archive, addressed by archive-relative paths such as 02_tables/csv/Tab19_....csv"""

    def __init__(self, path):
        self.path = path
        self.files = {}
        if os.path.isdir(path):
            base = path
            if not os.path.isdir(os.path.join(base, "02_tables")):
                subs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d, "02_tables"))]
                if len(subs) == 1:
                    base = os.path.join(path, subs[0])
            for root, _d, fns in os.walk(base):
                for fn in fns:
                    full = os.path.join(root, fn)
                    self.files[os.path.relpath(full, base).replace(os.sep, "/")] = ("fs", full)
        elif zipfile.is_zipfile(path):
            zf = zipfile.ZipFile(path)
            names = [n for n in zf.namelist() if not n.endswith("/")]
            tops = {n.split("/", 1)[0] for n in names}
            strip = len(tops) == 1 and any(n.startswith(next(iter(tops)) + "/02_tables/") for n in names)
            for n in names:
                rel = n.split("/", 1)[1] if strip else n
                self.files[rel] = ("zip", zf, n)
        else:
            raise SystemExit(f"{path}: not a folder or a zip archive")

    def read(self, rel):
        ent = self.files[rel]
        if ent[0] == "fs":
            with open(ent[1], "rb") as fh:
                return fh.read()
        return ent[1].read(ent[2])


def num(s):
    s = s.strip()
    try:
        return float(s)
    except ValueError:
        return None


def close(a, b, rtol, atol):
    if a == b:
        return True
    if math.isnan(a) and math.isnan(b):
        return True
    return abs(a - b) <= atol + rtol * max(abs(a), abs(b))


def cmp_csv(a, b, rtol, atol):
    ra = list(csv.reader(io.StringIO(a.decode("utf-8"))))
    rb = list(csv.reader(io.StringIO(b.decode("utf-8"))))
    if len(ra) != len(rb):
        return f"row counts differ ({len(ra)} vs {len(rb)})", 0.0
    worst = 0.0
    for i, (x, y) in enumerate(zip(ra, rb)):
        if len(x) != len(y):
            return f"row {i}: column counts differ", worst
        for j, (u, v) in enumerate(zip(x, y)):
            if u == v:
                continue
            fu, fv = num(u), num(v)
            if fu is not None and fv is not None:
                if close(fu, fv, rtol, atol):
                    worst = max(worst, abs(fu - fv))
                    continue
                return f"row {i}, column {j}: {u!r} vs {v!r}", worst
            return f"row {i}, column {j}: {u!r} vs {v!r}", worst
    return None, worst


def leaves(x, path="$"):
    """Yield (path, value) for every leaf of a parsed JSON value; an empty list or object counts as a leaf."""
    if isinstance(x, dict) and x:
        for k in x:
            yield from leaves(x[k], f"{path}.{k}")
    elif isinstance(x, list) and x:
        for i, v in enumerate(x):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, x


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def json_diff(x, y, rtol, atol):
    """Compare two parsed JSON values leaf by leaf.

    Returns (message, within, n) where `message` is None if every leaf agrees within the tolerance, otherwise a text
    that says what differs (and, for numbers, how many differ and the largest relative and absolute difference);
    `within` is the largest absolute difference among numbers that differ but stay within the tolerance; `n` is the
    number of numbers compared.
    """
    lx, ly = dict(leaves(x)), dict(leaves(y))
    if lx.keys() != ly.keys():
        extra = sorted(set(lx) ^ set(ly))
        return f"structure differs ({len(extra)} paths, e.g. {extra[0]})", 0.0, 0
    bad, within, n, other = [], 0.0, 0, None
    for path, a in lx.items():
        b = ly[path]
        if is_number(a) and is_number(b):
            n += 1
            a, b = float(a), float(b)
            if close(a, b, rtol, atol):
                if a != b:
                    within = max(within, abs(a - b))
            else:
                bad.append((abs(a - b) / max(abs(a), abs(b)), abs(a - b), path, a, b))
        elif a != b and other is None:
            other = f"{path}: {str(a)[:60]!r} vs {str(b)[:60]!r}"
    if other:
        return other, within, n
    if bad:
        rel, ab, path, a, b = max(bad)
        worst_abs = max(t[1] for t in bad)
        return (f"{len(bad)} of {n} numbers differ beyond the tolerance; largest relative difference {rel:.2g}, "
                f"largest absolute difference {worst_abs:.2g}; first: {bad[0][2]}: {bad[0][3]!r} vs {bad[0][4]!r}"), within, n
    return None, within, n


def cmp_npz(a, b):
    try:
        import numpy as np
    except ImportError:
        return "numpy not installed: skipped", None
    za, zb = np.load(io.BytesIO(a), allow_pickle=False), np.load(io.BytesIO(b), allow_pickle=False)
    if sorted(za.files) != sorted(zb.files):
        return "array names differ", None
    for k in za.files:
        if not np.array_equal(za[k], zb[k]):
            return f"array {k} differs", None
    return None, 0.0


CATEGORIES = [
    ("tables (csv)", re.compile(r"^02_tables/csv/.*\.csv$"), "csv"),
    ("tables (latex)", re.compile(r"^02_tables/latex/.*\.tex$"), "text"),
    ("raw results (csv)", re.compile(r"^03_logs/raw_results/.*\.csv$"), "csv"),
    ("raw results (npz)", re.compile(r"^03_logs/raw_results/.*\.npz$"), "npz"),
    ("figure data (json)", re.compile(r"^01_figures/data_json/.*\.json$"), "json"),
    ("verdicts", re.compile(r"^verdicts\.json$"), "json"),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reference", help="shipped results folder or archive")
    ap.add_argument("new", help="folder or archive produced by a new run")
    ap.add_argument("--rtol", type=float, default=1e-9)
    ap.add_argument("--atol", type=float, default=1e-12)
    ap.add_argument("--fig-rtol", type=float, help="relative tolerance for the figure data (default: --rtol)")
    ap.add_argument("--fig-atol", type=float, help="absolute tolerance for the figure data (default: --atol)")
    ap.add_argument("--only", help="regular expression: compare only archive paths that match")
    args = ap.parse_args(argv)

    ref, new = Source(args.reference), Source(args.new)
    bad_total = 0
    for label, rx, kind in CATEGORIES:
        names = sorted(n for n in ref.files if rx.match(n) and (not args.only or re.search(args.only, n)))
        ident = tol = 0
        diffs, skipped, worst = [], [], 0.0
        for n in names:
            if n not in new.files:
                diffs.append((n, "missing in the new run"))
                continue
            a, b = ref.read(n), new.read(n)
            if a == b:
                ident += 1
                continue
            if kind == "csv":
                msg, w = cmp_csv(a, b, args.rtol, args.atol)
            elif kind == "json":
                fig = label.startswith("figure")
                rt = args.fig_rtol if fig and args.fig_rtol is not None else args.rtol
                at = args.fig_atol if fig and args.fig_atol is not None else args.atol
                msg, w, _n = json_diff(json.loads(a), json.loads(b), rt, at)
            elif kind == "npz":
                msg, w = cmp_npz(a, b)
                if w is None and msg and "skipped" in msg:
                    skipped.append(n)
                    continue
            else:
                msg = None if a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n") else "text differs"
                w = 0.0
            if msg:
                diffs.append((n, msg))
            else:
                tol += 1
                worst = max(worst, w or 0.0)
        extra = sorted(n for n in new.files if rx.match(n) and n not in ref.files and (not args.only or re.search(args.only, n)))
        print(f"{label:<20} {len(names):3d} files: {ident:3d} identical, {tol:3d} equal within tolerance"
              f"{(' (largest absolute difference %.3g)' % worst) if tol else ''}, {len(diffs)} different"
              f"{', %d skipped' % len(skipped) if skipped else ''}"
              f"{', %d only in the new run' % len(extra) if extra else ''}")
        for n, msg in diffs[:25]:
            print(f"    DIFFERENT {n}: {msg}")
        bad_total += len(diffs)
    print("OK: the new run reproduces the shipped results" if bad_total == 0 else f"FAILED: {bad_total} file(s) differ")
    return 0 if bad_total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
