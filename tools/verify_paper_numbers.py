#!/usr/bin/env python3
"""Check the numbers quoted in the paper against the shipped result tables.

    python tools/verify_paper_numbers.py [--paper paper] [--results results]

Four kinds of check, all against files in results/ (no notebook code is run):

  1. Main-text Table 1 (error floor, tab:floor) and Table 2 (ground truth far beyond 2n, tab:truth): every cell of the
     LaTeX table in paper/main.tex is compared with 02_tables/csv (Tab19, Tab22; Tab13b, Tab14a, Tab14b and the raw
     MATH-500 block results), including which cells are shaded or bold or carry a star.
  2. Three appendix tables, cell by cell: the certified horizons (tab:horizons, against the raw file
     e7_certified_horizons.csv), the stress tests (tab:stress, against Tab06 and the data of the A1-violation and
     adversarial figures) and the claims ledger (tab:ledger, against Tab08: status, verdict word and colour of every
     row, and the measured values), with the sentences of the appendix that quote them.
  3. Numbers quoted in the running text (abstract, introduction, results, discussion, conclusion): each claim names the
     sentence fragment it comes from, the script confirms that the fragment is still in main.tex, and recomputes the
     number from the tables.
  4. A few arithmetic identities used in the text (for example 768,000 = 10 x 300 x 256).

The other appendix tables are not checked by this script.

Rounding: a printed value p with d decimals matches a table value v if |p - v| < 0.5 * 10**-d (plus a tiny float
slack), because the tables are rounded once more than the text. Standard library only.  Exit status 0 if every
check passes, 1 otherwise.
"""
import argparse
import csv
import glob
import json
import math
import os
import re
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------------------------------------------------------------------------------------------
NUM = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?(?:e[-+]?\d+)?|\.\d+", re.I)


def first_num(s):
    m = NUM.search(s)
    return float(m.group(0).replace(",", "")) if m else None


def all_nums(s):
    return [float(m.group(0).replace(",", "")) for m in NUM.finditer(s)]


def span(s):
    """'88-90/100' -> (88.0, 90.0); '85/100' -> (85.0, 85.0); '4.7-5.1' -> (4.7, 5.1); '1,300' -> (1300, 1300); '--' -> None"""
    s = s.strip().split("/")[0]
    if not s or s.startswith("--"):
        return None
    parts = re.split(r"(?<=[\d\)])\s*-\s*(?=[\d.])", s)
    vals = [first_num(p) for p in parts if first_num(p) is not None]
    if not vals:
        return None
    return (vals[0], vals[-1])


def decimals(txt):
    """number of decimals in a printed number such as '0.0364', '.0307', '1.3', '770', '6.1' (before an exponent)"""
    m = re.match(r"[-+]?\d*\.?(\d*)", txt.strip())
    return len(m.group(1)) if m else 0


def same(printed, value, d=None):
    """does the table value `value` round to the printed text `printed`?"""
    if d is None:
        d = decimals(printed)
    return abs(float(printed.replace(",", "")) - value) < 0.5 * 10 ** (-d) + 1e-9


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class Ctx:
    def __init__(self, paper_dir, results_dir):
        self.tex_raw = open(os.path.join(paper_dir, "main.tex"), encoding="utf-8").read()
        self.tex = re.sub(r"(?<!\\)%.*", "", self.tex_raw)
        self.tex_norm = re.sub(r"\s+", " ", self.tex)
        self.tab = os.path.join(results_dir, "02_tables", "csv")
        self.raw = os.path.join(results_dir, "03_logs", "raw_results")
        self.results_dir = results_dir
        self.ok = 0
        self.bad = []
        self.cells = 0

    def table(self, prefix):
        hits = sorted(glob.glob(os.path.join(self.tab, prefix + "*.csv")))
        if not hits:
            raise SystemExit(f"no table {prefix}*.csv in {self.tab}")
        return read_csv(hits[0])

    def rawcsv(self, name):
        return read_csv(os.path.join(self.raw, name))

    def claim(self, where, snippet, ok, detail=""):
        """`snippet` must occur in main.tex (so the script and the paper cannot drift apart); `ok` is the data check."""
        sn = re.sub(r"\s+", " ", snippet)
        present = sn in self.tex_norm
        good = bool(ok) and present
        if good:
            self.ok += 1
        else:
            self.bad.append(f"{where}: {snippet}")
        why = "" if present else "   [text not found in main.tex]"
        print(f"  [{'ok' if good else 'FAIL'}] {where:<22} {snippet[:70]:<70}  {detail}{why}")


# ----------------------------------------------------------------------------------------------------------------
# LaTeX table parsing
def tex_table(ctx, label):
    i = ctx.tex.index("\\label{%s}" % label)
    j = ctx.tex.rfind("\\begin{tabular}", 0, i)
    k = ctx.tex.index("\\end{tabular}", j)
    body = ctx.tex[j:k]
    body = body.split("\\midrule", 1)[1].split("\\bottomrule")[0]
    rows = []
    for r in body.split("\\\\"):
        r = r.strip()
        if r:
            rows.append([c.strip() for c in r.split("&")])
    return rows


def clean(cell):
    shaded = "\\cellcolor" in cell
    bold = "\\textbf" in cell
    star = "\\ast" in cell
    t = re.sub(r"\\cellcolor\{[^}]*\}", "", cell)
    t = re.sub(r"\\textbf\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\$\^\\(?:ast|dagger)\$", "", t)
    t = t.replace("\\%", "").strip()
    return t, shaded, bold, star


# ----------------------------------------------------------------------------------------------------------------
def check_table_floor(ctx):
    print("Table 1 (tab:floor): error floor at m = 1,319, n = 32")
    t19 = {r["Distribution"]: r for r in ctx.table("Tab19")}
    t22 = {(r["Distribution"], r["t"]): r for r in ctx.table("Tab22")}
    rows = tex_table(ctx, "tab:floor")
    problems = 0
    if len(rows) != len(t19):
        print(f"  [FAIL] the paper table has {len(rows)} rows, Tab19 has {len(t19)}")
        problems += 1
    for cells in rows:
        name = clean(cells[0])[0]
        if name not in t19:
            print(f"  [FAIL] unknown count law {name!r}")
            problems += 1
            continue
        a, b = t19[name], t22[(name, "16")]
        cl = [clean(c) for c in cells]
        expect = [
            ("pass@16n", a["pass@16n"], False),
            ("4n", a["t=4"], True), ("8n", a["t=8"], True), ("16n", a["t=16"], True), ("64n", a["t=64"], True),
            ("m=500, 16n", a["t=16, m=500"], True),
            ("LR half-width", "%.3f" % first_num(b["LR drawn"]), False),
            ("LR ratio", b["ratio"], False),
        ]
        for idx, (col, want, shade) in enumerate(expect, start=1):
            got, shaded, _, _ = cl[idx]
            ok = same(got, float(want), 3 if col != "LR ratio" else 2) and (not shade or shaded == (float(want) > 0.05))
            ctx.cells += 1
            if not ok:
                problems += 1
                print(f"  [FAIL] {name} / {col}: paper {got!r}{' (shaded)' if shaded else ''}, table {want}")
        # coverage: "97" or "81--82"
        lo, hi = span(b["coverage"])
        got = cl[9][0]
        want = f"{int(lo)}" if lo == hi else f"{int(lo)}--{int(hi)}"
        ctx.cells += 1
        if got != want:
            problems += 1
            print(f"  [FAIL] {name} / coverage: paper {got!r}, table {want!r}")
    if problems == 0:
        ctx.ok += 1
        print(f"  [ok] all {len(rows)} rows x 9 columns agree with Tab19/Tab22, and the shading marks exactly the floors above 0.05")
    else:
        ctx.bad.append("tab:floor")


def check_table_truth(ctx):
    print("Table 2 (tab:truth): ground truth far beyond 2n (k = 8,192; E8: k = 992)")
    t14a = {r["Config"]: r for r in ctx.table("Tab14a")}
    t14b = {r["Config"]: r for r in ctx.table("Tab14b")}
    t13b = ctx.table("Tab13b")[0]  # n = 32
    e8 = [r for r in ctx.rawcsv("e8_ground_truth_per_block.csv") if r["n"] == "32" and r["k"] == "992"]
    width = statistics.mean(float(r["band_F_hi"]) - float(r["band_F_lo"]) for r in e8 if r["estimator"] == "Power law")
    rows = tex_table(ctx, "tab:truth")
    problems = 0
    if len(rows) != 10:
        print(f"  [FAIL] expected 10 rows, found {len(rows)}")
        problems += 1
    for cells in rows:
        name = clean(cells[0])[0]
        if "E8" in name:
            want = [width, float(t13b["PL far"]), float(t13b["BB far"]), float(t13b["NP far"]), float(t13b["picked far err"])]
            fails = None
        else:
            a, b = t14a[name], t14b[name]
            want = [float(a["band k=8192"]), float(b["PL"]), float(b["BB"]), float(b["NP"]), float(b["picked err"])]
            fails = b["fails/flip"].split("/")[0] == "Y"
        cl = [clean(c) for c in cells]
        for idx, w in enumerate(want, start=1):
            ctx.cells += 1
            got = cl[idx][0]
            if not same(got, w, 3 if idx == 1 else 4):
                problems += 1
                print(f"  [FAIL] {name} / column {idx}: paper {got!r}, table {w:.4f}")
        # bold marks the lowest of PL, BB, NP; the star marks a pre-registered failure of the in-window choice
        errs = want[1:4]
        best = min(errs)
        bold_cells = [i for i in range(3) if cl[2 + i][2]]
        want_bold = [i for i, e in enumerate(errs) if round(e, 4) == round(best, 4)]
        ctx.cells += 1
        if bold_cells != want_bold:
            problems += 1
            print(f"  [FAIL] {name}: bold cells {bold_cells}, lowest of the three forecasts at {want_bold}")
        picked = want[4]
        rule = picked >= max(2 * best, best + 0.01)
        ctx.cells += 1
        if cl[5][3] != rule or (fails is not None and fails != rule):
            problems += 1
            print(f"  [FAIL] {name}: star {cl[5][3]}, margin rule {rule}, table flag {fails}")
    if problems == 0:
        ctx.ok += 1
        print(f"  [ok] all {len(rows)} rows x 5 columns agree (Tab13b, Tab14a, Tab14b, raw E8 blocks); bold = lowest forecast; "
              f"star = pre-registered failure margin")
    else:
        ctx.bad.append("tab:truth")


# ----------------------------------------------------------------------------------------------------------------
def sig_digits(txt):
    """significant digits of a printed number such as '4.88' (3), '40.0' (3), '104.4' (4)"""
    return len(txt.replace(".", "").replace("-", "").lstrip("0"))


def figure_data(ctx, name):
    with open(os.path.join(ctx.results_dir, "01_figures", "data_json", name), encoding="utf-8") as fh:
        return json.load(fh)["data"]


def check_table_horizons(ctx):
    print("Certified horizons (tab:horizons, appendix)")
    raw = {(int(r["n"]), int(r["m"]), r["eps"]): r for r in ctx.rawcsv("e7_certified_horizons.csv")}
    rows = tex_table(ctx, "tab:horizons")
    problems = 0
    if len(rows) * 2 != len(raw):
        print(f"  [FAIL] the paper table has {len(rows)} rows, e7_certified_horizons.csv has {len(raw) // 2} pairs (n, m)")
        problems += 1
    for cells in rows:
        shaded = "\\rowcolor" in cells[0]
        n = int(re.sub(r"\\rowcolor\{[^}]*\}", "", cells[0]).strip())
        m = int(cells[1].replace(",", ""))
        cl = [clean(c) for c in cells[2:]]
        ctx.cells += 1
        if shaded != (m <= 1319):
            problems += 1
            print(f"  [FAIL] n={n}, m={m:,}: row shading {shaded}, but shaded rows are those with m <= 1,319")
        for j, eps in enumerate(("0.05", "0.1")):
            r = raw[(n, m, eps)]
            lp, two, thm = cl[j], cl[2 + j], cl[4 + j]
            # LP-cert: the largest certified t on the grid, or '--'; bold at m = 1,319 (the largest benchmark in use)
            want = r["t*_LP"]
            ok_lp = (lp[0] == "--") if want == "" else (lp[0] != "--" and float(lp[0]) == float(want))
            # two-point bound: three significant digits; Theorem 1(C): one decimal
            ok_two = same(two[0], float(r["t_bind_M5"])) and sig_digits(two[0]) == 3 and not two[2]
            ok_thm = same(thm[0], float(r["t_bind_Thm1C"]), 1) and decimals(thm[0]) == 1 and not thm[2]
            ctx.cells += 3
            for what, ok, got, w in (("LP-cert", ok_lp and lp[2] == (m == 1319 and want != ""), lp[0], want or "--"),
                                     ("two-point", ok_two, two[0], r["t_bind_M5"]),
                                     ("Theorem 1(C)", ok_thm, thm[0], r["t_bind_Thm1C"])):
                if not ok:
                    problems += 1
                    print(f"  [FAIL] n={n}, m={m:,}, eps={eps}, {what}: paper {got!r}, file {w}")
    if problems == 0:
        ctx.ok += 1
        print(f"  [ok] all {len(rows)} rows x 6 columns agree with e7_certified_horizons.csv; shading = the benchmark sizes "
              f"m <= 1,319; bold = the LP-cert horizon at m = 1,319")
    else:
        ctx.bad.append("tab:horizons")
    ratio = float(raw[(16, 10000, "0.05")]["t_bind_Thm1C"]) / float(raw[(16, 1319, "0.05")]["t_bind_Thm1C"])
    ctx.claim("appendix, horizons", "from 37.9 at $m=1{,}319$ to 104.4 at $m=10{,}000$ for $\\varepsilon=0.05$",
              same("37.9", float(raw[(16, 1319, "0.05")]["t_bind_Thm1C"])) and same("104.4", float(raw[(16, 10000, "0.05")]["t_bind_Thm1C"]))
              and abs(ratio - math.sqrt(10000 / 1319)) < 0.01,
              f"ratio {ratio:.3f} against sqrt(10000/1319) = {math.sqrt(10000 / 1319):.3f}")
    lp_vals = [float(r["t*_LP"]) for r in raw.values() if r["t*_LP"] != ""]
    ctx.claim("appendix, horizons", "LP-cert never certifies beyond $t=4$, even at $m=10{,}000$, and at $m=164$ it certifies nothing at either accuracy",
              max(lp_vals) == 4.0 and all(r["t*_LP"] == "" for k, r in raw.items() if k[1] == 164)
              and all(float(r["t*_LP"]) == 4.0 for k, r in raw.items() if k[1:] == (10000, "0.1")),
              f"largest certified t = {max(lp_vals):g}; empty for every n and both accuracies at m = 164")


def bias_bound(n, t):
    """B_n(t) of Theorem 1(B), with eta = 2 - t"""
    return 4 * n * (t - 1) / (math.e ** 2 * t * (n - 1) ** 2) + 2.0 ** (-n) + math.exp(-(2 - t) * n)


def first_crossing(grid, bias, bound):
    """the grid interval that contains the first point where the bias exceeds `bound`"""
    for i, b in enumerate(bias):
        if b > bound:
            return (grid[i - 1], grid[i]) if i else (None, grid[0])
    return None


def check_table_stress(ctx):
    print("Stress tests (tab:stress, appendix)")
    copy = figure_data(ctx, "Fig07a_A1_violation_copy_model_data.json")
    drift = figure_data(ctx, "Fig07b_A1_violation_block_drift_data.json")
    adv = figure_data(ctx, "Fig12_adversarial_pairs_and_selection_data.json")
    bound = bias_bound(32, 1.5)
    rows = tex_table(ctx, "tab:stress")
    labels = ["Copy model", "bias exceeds", "tests reach", "Block drift", "bias exceeds", "tests reach",
              "Same-count-law", "band contains", "Selected subset", "bias contrast", "exact"]
    problems = 0
    if len(rows) != len(labels) or any(lab not in row[0] for lab, row in zip(labels, rows)):
        print(f"  [FAIL] the rows of the paper table are not the expected {len(labels)} (found {len(rows)})")
        ctx.bad.append("tab:stress")
        return

    def interval(txt):
        a, b = (float(x) for x in txt.split("--"))
        return a, b

    crosses = {}
    for col, model in ((1, "base"), (2, "instruct")):
        got = [clean(row[col])[0].replace("$", "") for row in rows]
        c_copy = first_crossing(copy[model]["rho_fine"], copy[model]["bias_copy"], bound)
        c_drift = first_crossing(drift[model]["tau_fine"], drift[model]["bias_drift"], bound)
        crosses[model] = (c_copy, c_drift)
        ok = [
            same(got[0], copy[model]["rho_break"], 3),
            c_copy is not None and all(abs(x - y) < 1e-9 for x, y in zip(interval(got[1]), c_copy)),
            same(got[2], copy[model]["rho_detect"], 3),
            same(got[3], drift[model]["tau_break"], 3),
            c_drift is not None and all(abs(x - y) < 1e-9 for x, y in zip(interval(got[4]), c_drift)),
            same(got[5], drift[model]["tau_detect"], 3),
            same(got[6], adv["adv2"][model]["sep"], 3),
            float(got[7]) == round(100 * adv["adv2"][model]["band_both"]),
            int(got[8]) == adv["adv3"][model]["n_sel"],
            same(got[9], adv["adv3"][model]["mean"], 4),
            same(got[10], adv["adv3"]["beta_star"], 4),
        ]
        ctx.cells += len(ok)
        for i, good in enumerate(ok):
            if not good:
                problems += 1
                print(f"  [FAIL] {model}, row {i} ({labels[i]}): paper {got[i]!r}")
    if problems == 0:
        ctx.ok += 1
        print(f"  [ok] all 11 rows x 2 columns agree with Fig07a, Fig07b and Fig12 data (B_32(1.5) = {bound:.6f}; the ranges are the "
              f"grid intervals in which the bias first exceeds it)")
    else:
        ctx.bad.append("tab:stress")

    env = copy["envelope"]
    ctx.claim("appendix, A1", "$[-0.0060,\\,2.3\\times10^{-10}]$, whose lower end is $-B_{32}(1.5)$",
              same("0.0060", -env[0], 4) and same("2.3", env[1] * 1e10, 1) and abs(-env[0] - bound) < 1e-6,
              f"envelope [{env[0]:.5f}, {env[1]:.2e}], B_32(1.5) = {bound:.5f}")
    ctx.claim("appendix, A1", "only beyond $\\rho=0.05$ (base) and $0.07$ (instruct)",
              crosses["base"][0][0] == 0.05 and crosses["instruct"][0][0] == 0.07, f"{crosses['base'][0]} and {crosses['instruct'][0]}")
    ctx.claim("appendix, A1", "the bias exceeds $B_{32}(1.5)$ by $\\tau=0.010$, while the tests reach 80\\% power only at $\\tau=0.017$",
              crosses["base"][1][1] == 0.01 and crosses["instruct"][1][1] == 0.01
              and same("0.017", drift["base"]["tau_detect"], 3) and same("0.017", drift["instruct"]["tau_detect"], 3),
              f"{crosses['base'][1]} and {crosses['instruct'][1]}")
    worst = [max(v) for mod in ("base", "instruct") for v in adv["adv2"][mod]["miss"].values()]
    ctx.claim("appendix, adversarial", "misses one member by half of that in 60\\% to 100\\% of replicates",
              round(100 * min(worst)) == 60 and round(100 * max(worst)) == 100, f"worst-member miss {min(worst):.3f} to {max(worst):.3f}")
    t07 = ctx.table("Tab07")
    ctx.claim("appendix, adversarial", "All headline checks agree between graders G1 and G2 (12 of 12)",
              len(t07) == 12 and all(r["Agree"] == "yes" for r in t07), f"{sum(r['Agree'] == 'yes' for r in t07)} of {len(t07)} (Tab07)")


def check_ledger(ctx):
    print("Claims ledger (tab:ledger, appendix)")
    t08 = ctx.table("Tab08")
    rows = tex_table(ctx, "tab:ledger")
    # (start of the paper's claim, start of the matching Tab08 claims, Tab08 verdict starts with, paper status, paper verdict, colour)
    spec = [
        ("C1: certified", ["C1 ["], "SUPPORTED", "pre-registered", "supported", "blue"),
        ("C1 scope", ["C1 scope"], "OPEN", "descriptive", "open for other estimators", None),
        ("C1 accuracy", ["C1 accuracy, Base", "C1 accuracy, Instruct"], "LP WORSE", "pre-registered", "LP-cert worse", None),
        ("C2:", ["C2 ["], "SUPPORTED", "pre-registered", "supported", "blue"),
        ("C3:", ["C3 ["], "NOT SUPPORTED", "pre-registered", "not supported; retired", "red"),
        ("C4:", ["C4, G1", "C4, G2"], "SUPPORTED", "pre-registered, restated", "supported", "blue"),
        ("C5a", ["C5a"], "SUPPORTED", "pre-registered", "supported as run", "blue"),
        ("C5b", ["C5b, E8", "C5b, Monkey Business"], "SUPPORTED", "pre-registered", "supported", "blue"),
        ("C5c, C5d (E8)", ["C5c, E8", "C5d, E8"], "EXPLORATORY", "exploratory", "tested below", None),
        ("C5c (Monkey Business)", ["C5c, Monkey Business"], "NOT SUPPORTED", "pre-registered", "not supported", "red"),
        ("C5d (Monkey Business)", ["C5d, Monkey Business"], "NOT SUPPORTED", "pre-registered", "not supported", "red"),
        ("C5e", ["C5e"], "EXPLORATORY", "exploratory", "no test", None),
        ("E10", ["E10"], "REPORTED", "descriptive", "no test", None),
    ]
    problems = 0
    if len(rows) != len(spec):
        print(f"  [FAIL] the paper's ledger has {len(rows)} rows, expected {len(spec)}")
        problems += 1
    for (start, prefixes, verdict, status, word, colour), cells in zip(spec, rows):
        claim_txt = clean(cells[0])[0]
        mine = [r for pre in prefixes for r in t08 if r["Claim"].startswith(pre)]
        tags = " ".join(re.findall(r"\[([^\]]*)\]", " ".join(r["Claim"] for r in mine)))
        got_status, got_word = clean(cells[1])[0], re.sub(r"\\cellcolor\{[^}]*\}", "", cells[4]).strip()
        got_colour = "blue" if "blue!10" in cells[4] else ("red" if "red!10" in cells[4] else None)
        ctx.cells += 4
        checks = [
            (claim_txt.startswith(start), f"row {start!r}: claim text {claim_txt[:40]!r}"),
            (len(mine) >= len(prefixes) and all(r["Verdict"].startswith(verdict) for r in mine),
             f"{start}: Tab08 verdicts {[r['Verdict'][:20] for r in mine]}, expected {verdict}"),
            (got_status == status and (start in ("C4:", "C1 accuracy") or status.split(",")[0] in tags),
             f"{start}: status {got_status!r}, Tab08 tags {tags!r}"),
            (got_word == word and got_colour == colour, f"{start}: verdict {got_word!r} ({got_colour}), expected {word!r} ({colour})"),
        ]
        for ok, msg in checks:
            if not ok:
                problems += 1
                print("  [FAIL]", msg)
    if problems == 0:
        ctx.ok += 1
        print(f"  [ok] all {len(rows)} rows: claim, status, verdict word and colour agree with Tab08 (C1 accuracy and C4 carry no status "
              f"tag there; the notebook's text fixes C1-C4 in revision 2)")
    else:
        ctx.bad.append("tab:ledger")

    def measured(prefix):
        return " ".join(r["Measured (this run)"] for r in t08 if r["Claim"].startswith(prefix))
    ctx.claim("appendix, ledger", "& 1.25 to 2.5 &", "from 1.25 to 2.50" in measured("C1 ["), measured("C1 [")[:60])
    c2 = measured("C2 [")
    ctx.claim("appendix, ledger", "median 0.232, minimum 0.102", "min 0.102, median 0.232" in c2, c2[:60])
    k992 = {}
    for r in ctx.rawcsv("e8_ground_truth_per_block.csv"):
        if r["n"] == "32" and r["k"] == "992" and r["abs_error"]:
            k992.setdefault(r["estimator"], []).append(float(r["abs_error"]))
    me = {e: statistics.mean(v) for e, v in k992.items() if e in ("Power law", "Beta-binomial", "NPMLE", "Moment matching")}
    c5a = measured("C5a")
    ctx.claim("appendix, ledger", "gap 0.192; index 3.7 (1.7 without MM)",
              len(me) == 4 and same("0.192", max(me.values()) - min(me.values())) and "family index 3.7" in c5a and "family index 1.7" in c5a,
              f"gap over the four families {max(me.values()) - min(me.values()):.4f} (E8, k = 992); {c5a[50:100]}")
    ctx.claim("appendix, ledger", "8/8; 9/9 configurations", "8/8" in measured("C5b, E8") and "9/9" in measured("C5b, Monkey Business"),
              "Tab08")
    ctx.claim("appendix, ledger", "at least half of informative configurations & 2/6", "2/6" in measured("C5c, Monkey Business"), "Tab08")
    ctx.claim("appendix, ledger", "at least half of informative configurations & 0/6", "0/6" in measured("C5d, Monkey Business"), "Tab08")
    fold = [first_num(v) for r in ctx.table("Tab16") for k, v in r.items() if k.startswith(("PL", "BB", "NP", "BT")) and k != "far k"]
    ctx.claim("appendix, ledger", "21 cells with fold error 2 to 142", "21 resolved cells" in measured("C5e") and max(fold) == 142,
              f"{measured('C5e')[:40]}; largest fold error in Tab16 {max(fold):g}")


# ----------------------------------------------------------------------------------------------------------------
def check_text(ctx):
    t19 = {r["Distribution"]: r for r in ctx.table("Tab19")}
    t22 = ctx.table("Tab22")
    t10 = ctx.table("Tab10")
    t15 = {r["Distribution"]: r for r in ctx.table("Tab15_")}
    t15c = ctx.table("Tab15c")
    t17 = ctx.table("Tab17")
    t20 = ctx.table("Tab20")
    t21 = ctx.table("Tab21")
    t14a = ctx.table("Tab14a")
    t14b = ctx.table("Tab14b")
    t11 = {r["Quantity"]: r for r in ctx.table("Tab11")}
    t12a = ctx.table("Tab12a")
    t12b = {r["Stream"]: r for r in ctx.table("Tab12b")}
    t02 = ctx.table("Tab02")

    fl = lambda col: {k: float(v[col]) for k, v in t19.items()}   # noqa: E731
    f4, f8, f16, f64, f500 = fl("t=4"), fl("t=8"), fl("t=16"), fl("t=64"), fl("t=16, m=500")
    over16 = sorted(k for k, v in f16.items() if v > 0.05)
    lo16, hi16 = min(f16[k] for k in over16), max(f16[k] for k in over16)

    print("Abstract, introduction, conclusion")
    ctx.claim("abstract", "errs by at least 0.084 to 0.205 with probability",
              len(over16) == 7 and same("0.084", lo16) and same("0.205", hi16),
              f"{len(over16)} laws above 0.05 at 16n, range {lo16:.3f}-{hi16:.3f} (Tab19)")
    ctx.claim("intro, bullet 2", "this floor at $k=16n$ is 0.084 to 0.205 for seven of the ten laws", True,
              "same numbers")
    ctx.claim("conclusion", "by at least 0.08 to 0.2 with probability", same("0.08", lo16, 2) and same("0.2", hi16, 1),
              f"{lo16:.3f} -> 0.08, {hi16:.3f} -> 0.2")
    rat = {}
    for r in t22:
        if float(t19[r["Distribution"]]["t=%s" % r["t"]]) > 0.01:
            rat.setdefault(int(r["t"]), []).append(float(r["ratio"]))
    rng = {t: (min(v), max(v)) for t, v in rat.items()}
    ctx.claim("abstract", "within a factor of 1.22 of this floor", same("1.22", rng[16][1]), f"max ratio at 16n = {rng[16][1]}")
    ctx.claim("intro, bullet 2", "within a factor of 1.02 to 1.22 of it", same("1.02", rng[16][0]) and same("1.22", rng[16][1]),
              f"ratios at 16n: {rng[16][0]}-{rng[16][1]} (laws with floor above 0.01)")

    # certification
    lp = {}
    m5 = []
    for r in t10:
        m = int(r["m"].replace(",", ""))
        lp.setdefault(m, set()).add(r["t*LP 0.1"])
        if m in (164, 300, 1319):
            m5.append(float(r["M5 binds 0.1"]))
    ctx.claim("intro, bullet 1", "certifies an error of 0.1 beyond $k=2.5n$",
              lp[1319] == {"2.5"} and lp[164] == {"--"} and lp[300] == {"1.25"},
              f"t* at eps=0.1 for n=16,32,64: m=164 {sorted(lp[164])}, m=300 {sorted(lp[300])}, m=1,319 {sorted(lp[1319])}")
    ctx.claim("sec. 5.1", "reaches $t=1.25$ at $m=300$ and $t=2.5$ at $m=1{,}319$, and needs $m=10{,}000$ to reach $t=4$",
              lp[10000] == {"4"}, f"m=10,000: {sorted(lp[10000])}")
    ctx.claim("sec. 5.1", "reaches 0.1 only at $t=11.2$ to $34$", same("11.2", min(m5)) and same("34", max(m5), 0),
              f"two-point bound reaches 0.1 at t = {min(m5)} to {max(m5)} (m = 164, 300, 1,319)")

    # 5.2 floor paragraph
    ctx.claim("sec. 5.2", "At $k=4n$ the floor is at most 0.044 for every count law", same("0.044", max(f4.values())),
              f"max {max(f4.values()):.3f}")
    n8 = sum(v > 0.05 for v in f8.values())
    ctx.claim("sec. 5.2", "At $k=8n$ it exceeds 0.05 for five of the ten laws, and at $k=16n$ for seven, ranging from 0.084 to 0.205",
              n8 == 5, f"{n8} laws at 8n, {len(over16)} at 16n")
    ctx.claim("sec. 5.2", "At $k=64n$ it reaches 0.31", same("0.31", max(f64.values())), f"max {max(f64.values()):.3f}")
    lo5, hi5 = min(f500[k] for k in over16), max(f500[k] for k in over16)
    ctx.claim("sec. 5.2", "floors of 0.095 to 0.225 at $16n$", same("0.095", lo5) and same("0.225", hi5),
              f"m=500, same seven laws: {lo5:.3f}-{hi5:.3f}")
    gs = [float(v) for k, r in t19.items() if k.startswith("GSM8K") for c, v in r.items() if c.startswith("t=") and "m=500" not in c]
    ctx.claim("sec. 5.2", "floors of at most 0.005", max(gs) <= 0.005 + 1e-9, f"max over t = 2..64 and both GSM8K laws: {max(gs):.3f}")

    # LR paragraph
    ctx.claim("sec. 5.2", "1.31 to 1.56 times the floor at $k=4n$, 1.12 to 1.29 times at $8n$, and 1.02 to 1.22 times at $16n$",
              same("1.31", rng[4][0]) and same("1.56", rng[4][1]) and same("1.12", rng[8][0]) and same("1.29", rng[8][1])
              and same("1.02", rng[16][0]) and same("1.22", rng[16][1]),
              f"4n {rng[4]}, 8n {rng[8]}, 16n {rng[16]}")
    cov = {4: [], 8: [], 16: []}
    for r in t22:
        lo, hi = span(r["coverage"])
        cov[int(r["t"])].append((lo, hi))
    avg = {t: (statistics.mean(a for a, _ in v) / 100, statistics.mean(b for _, b in v) / 100) for t, v in cov.items()}
    ok = all(avg[t][0] - 0.005 <= p <= avg[t][1] + 0.005 for t, p in ((4, 0.85), (8, 0.92), (16, 0.97)))
    ctx.claim("sec. 5.2", "averages 0.85, 0.92 and 0.97", ok, "mean coverage " + ", ".join(f"{avg[t][0]:.3f}-{avg[t][1]:.3f}" for t in (4, 8, 16)))
    mincov = min(lo for v in cov.values() for lo, _ in v)
    ctx.claim("sec. 5.2", "the lowest coverage in any combination is 75 of 100", mincov == 75, f"min {mincov:.0f}/100")

    # needed / stability
    big = [float(first_num(r["t=16"])) for r in t15.values() if not r["t=16"].startswith("<")]
    over = sorted(v for v in big if v > 60000)
    ctx.claim("sec. 5.2", "it exceeds 60,000 for seven count laws, with values from $6.5\\times10^4$ to $2.9\\times10^{10}$",
              len(over) == 7 and over[0] == 65000 and over[-1] == 2.9e10, f"{len(over)} laws, {over[0]:.3g} to {over[-1]:.3g} (Tab15)")
    needed_spread = max(float(r["needed spread"].replace(",", "")) for r in t20)
    floor_spread = {(r["Distribution"], r["t"]): float(r["floor spread"]) for r in t20}
    ctx.claim("sec. 5.2", "they move by factors up to 1,200 (10th to 90th percentile)", needed_spread == 1200, f"max spread {needed_spread:g}")
    ctx.claim("sec. 5.2", "at most 2.24, and by 1.33 and 1.59 for the two laws whose floor exceeds 0.05",
              max(floor_spread.values()) == 2.24 and floor_spread[("CC L3-70B-I", "16")] == 1.33 and floor_spread[("MATH L3-8B-I", "16")] == 1.59,
              "Tab20")
    rngs = {(r["Distribution"], r["t"]): r["floor 10%-90%"] for r in t20}
    ctx.claim("sec. 5.2", "at 0.065--0.103 and 0.097--0.129",
              rngs[("MATH L3-8B-I", "16")] == "0.065-0.103" and rngs[("CC L3-70B-I", "16")] == "0.097-0.129", "Tab20")

    # attempts beat problems
    c15 = {r["k"].replace(",", ""): r for r in t15c}
    vals = {(k, n): first_num(c15[k]["n=%d" % n]) for k in ("128", "512") for n in (16, 32, 64)}
    ctx.claim("intro, bullet 3", "falls from $1.3\\times10^5$ with $n=32$ to 770 with $n=64$",
              vals[("512", 32)] == 1.3e5 and vals[("512", 64)] == 770, f"k=512: n=32 {vals[('512', 32)]:g}, n=64 {vals[('512', 64)]:g} (Tab15c)")
    ctx.claim("sec. 5.2", "is $6.1\\times10^9$ with $n=16$, $1.3\\times10^5$ with $n=32$ and 770 with $n=64$; at $k=128$ it is 1,600, 71 and 24",
              vals[("512", 16)] == 6.1e9 and (vals[("128", 16)], vals[("128", 32)], vals[("128", 64)]) == (1600, 71, 24),
              f"k=128: {vals[('128', 16)]:g}, {vals[('128', 32)]:g}, {vals[('128', 64)]:g}")
    tot32, tot64 = vals[("512", 32)] * 32, vals[("512", 64)] * 64
    ctx.claim("sec. 5.2", "about $4.2\\times10^6$ ($1.3\\times10^5\\times32$) to about $4.9\\times10^4$ ($770\\times64$), almost two orders of magnitude",
              same("4.2", tot32 / 1e6, 1) and same("4.9", tot64 / 1e4, 1) and 50 < tot32 / tot64 < 100,
              f"{tot32:.3g} and {tot64:.3g}, ratio {tot32 / tot64:.1f}")

    # bands in units of problems
    lrb = [span(r["LR/bound"]) for r in t17 if span(r["LR/bound"])]
    dkw = [span(r["DKW/bound"]) for r in t17 if span(r["DKW/bound"])]
    ctx.claim("sec. 5.2", "3.3 to 5.4 times the problems", min(a for a, _ in lrb) == 3.3 and max(b for _, b in lrb) == 5.4,
              f"LR/bound {min(a for a, _ in lrb)}-{max(b for _, b in lrb)} (Tab17)")
    ctx.claim("sec. 5.2", "490 to 28,000 times as many", min(a for a, _ in dkw) == 490 and max(b for _, b in dkw) == 28000,
              f"DKW/bound {min(a for a, _ in dkw):g}-{max(b for _, b in dkw):g} (Tab17)")
    widths = [first_num(r["width"]) for r in t21]
    covs = [span(r["coverage"]) for r in t21]
    ctx.claim("sec. 5.2", "median width of 0.082 to 0.097 and covered the truth in 73 to 100 of 100 draws",
              min(widths) == 0.082 and max(widths) == 0.097 and min(a for a, _ in covs) == 73 and max(b for _, b in covs) == 100,
              f"widths {min(widths)}-{max(widths)}, coverage {min(a for a, _ in covs):.0f}-{max(b for _, b in covs):.0f}/100 (Tab21)")

    # ground truth
    print("Ground truth")
    mb = {r["Config"]: r for r in t14a}
    w = lambda *names: [float(mb[n]["band k=8192"]) for n in names]    # noqa: E731
    gsm, mth = w("GSM8K L3-8B-I", "GSM8K L3-70B-I"), w("MATH L3-8B-I", "MATH L3-70B-I", "MATH G-7B")
    cc, py = w("CC L3-8B-I", "CC L3-70B-I", "CC G-7B"), w("MATH P-12B")
    ctx.claim("sec. 5.3", "0.08 to 0.09 on GSM8K, 0.26 to 0.39 on MATH, 0.80 for Pythia-12B and 0.92 to 0.99 on CodeContests",
              same("0.08", min(gsm), 2) and same("0.09", max(gsm), 2) and same("0.26", min(mth), 2) and same("0.39", max(mth), 2)
              and same("0.80", py[0], 2) and same("0.92", min(cc), 2) and same("0.99", max(cc), 2),
              f"GSM8K {min(gsm)}-{max(gsm)}, MATH {min(mth)}-{max(mth)}, Pythia {py[0]}, CC {min(cc)}-{max(cc)} (Tab14a)")
    ctx.claim("sec. 5.3", "in all nine Monkey Business configurations", all(r["cover"] == "8/8" for r in t14a) and len(t14a) == 9,
              "cover = 8/8 in 9 of 9 rows (Tab14a)")
    ctx.claim("sec. 4", "These have 127, 128 and 140 problems per task", sorted({int(r["m"]) for r in t14a}) == [127, 128, 140],
              f"m = {sorted({int(r['m']) for r in t14a})}")
    t13 = ctx.table("Tab13")
    bandrow = [r for r in t13 if r["Estimator"].startswith("PI band")][0]
    ctx.claim("sec. 5.3", "with width 0.43 at $k=992$", all("8/8" in v for k, v in bandrow.items() if k.startswith("k=")) and "w 0.43" in bandrow["k=992"],
              f"Tab13: {bandrow['k=992']}")
    e8 = [r for r in ctx.rawcsv("e8_ground_truth_per_block.csv") if r["n"] == "32" and r["estimator"] in ("Power law", "Beta-binomial", "NPMLE")]
    bykey = {}
    for r in e8:
        bykey.setdefault((int(r["k"]), r["estimator"]), []).append(float(r["abs_error"]))
    ks = sorted({k for k, _ in bykey})
    best = {k: min(("Power law", "Beta-binomial", "NPMLE"), key=lambda e: statistics.mean(bykey[(k, e)])) for k in ks}
    ok = all(best[k] == "Power law" for k in ks if k <= 128) and all(best[k] == "Beta-binomial" for k in ks if k >= 192)
    ctx.claim("sec. 5.3", "the power law was most accurate up to $k=128$ and the Beta-binomial from $k=192$ on", ok,
              "most accurate of the three families at k = " + ", ".join(f"{k}:{'PL' if best[k] == 'Power law' else 'BB'}" for k in ks))
    t13b = ctx.table("Tab13b")[0]
    ctx.claim("sec. 5.3", "At $k=992$ their errors were 0.031 and 0.0075",
              same("0.031", float(t13b["PL far"])) and same("0.0075", float(t13b["BB far"])), f"PL {t13b['PL far']}, BB {t13b['BB far']}")
    ctx.claim("sec. 5.3", "gave 0.033", same("0.033", float(t13b["picked far err"])), f"{t13b['picked far err']}")
    inf = [r for r in t14b if r["inform."] == "yes"]
    fails = sum(r["fails/flip"].split("/")[0] == "Y" for r in inf)
    flips = sum(r["fails/flip"].split("/")[1] == "Y" for r in t14b)
    ctx.claim("sec. 5.3", "The in-window choice failed in two of six informative configurations",
              len(inf) == 6 and fails == 2 and flips == 0, f"{len(inf)} informative, {fails} failures, {flips} flips (Tab14b)")
    pl = [float(r["PL"]) for r in inf]
    ctx.claim("sec. 5.3", "the power law's far-$k$ error ranged from 0.005 to 0.057",
              same("0.005", min(pl), 3) and abs(max(pl) - 0.057) <= 0.0006, f"{min(pl)} to {max(pl)} over the six")
    npc = [float(r["NP"]) for r in t14b if r["Config"].startswith("CC")]
    ctx.claim("sec. 5.3", "erred by 0.21 to 0.40 on CodeContests", same("0.21", min(npc), 2) and same("0.40", max(npc), 2),
              f"{min(npc)} to {max(npc)}")

    # claim streams
    claim_streams = ["G-B0.5", "G-I0.5", "G-B1.5", "G-RL1.5", "M-B0.5", "M-I0.5L"]
    b4 = [float(t12b[s]["band k=4n"]) for s in claim_streams]
    ex = [float(t12b[s]["extra"]) for s in claim_streams]
    ctx.claim("sec. 5.3", "median width 0.23 (minimum 0.10)", same("0.23", statistics.median(b4), 2) and same("0.10", min(b4), 2),
              f"median {statistics.median(b4):.4f}, min {min(b4)} (Tab12b)")
    ctx.claim("sec. 5.3", "adds a median of 0.081", abs(statistics.median(ex) - 0.081) <= 0.001,
              f"median of the six rounded entries {statistics.median(ex):.4f} (entries are rounded to 3 decimals)")
    a3 = sorted(float(r["A3"].rstrip("%")) for r in t12a if r["Stream"] in claim_streams and float(r["A3"].rstrip("%")) > 2)
    ctx.claim("limitations", "whose graders disagreed on 2.2\\% to 14.8\\% of attempts", len(a3) == 4 and a3[0] == 2.18 and a3[-1] == 14.83,
              f"four streams above 2%: {a3}")

    # theory checks and in-window accuracy
    print("Theory checks and in-window accuracy")
    cor3 = [r for r in t02 if r["Check"].startswith("Cor. 3 numerical")][0]
    ctx.claim("sec. 5", "pass@2048 values 0.669 apart", "sep 0.6688" in cor3["Value"], cor3["Value"])
    ctx.claim("sec. 5", "$2.3\\times10^{-61}$", "2.3e-61" in cor3["Value"], cor3["Value"])
    lem6 = ctx.rawcsv("e3_lemma6_failure_fractions.csv")
    minfrac = min(float(r["frac"]) for r in lem6)
    ctx.claim("sec. 5", "at least 65.9\\% of replicates", abs(minfrac * 100 - 65.9) <= 0.05 + 1e-9 and all(r["pass"] == "True" for r in lem6),
              f"minimum failure fraction {minfrac * 100:.2f}% over {len(lem6)} (t, estimator) cells")
    blk = ctx.rawcsv("e4_per_block_results.csv")
    mae = {}
    for r in blk:
        if r["k"] == "48" and r["abs_error"]:
            mae.setdefault((r["estimator"], r["model"]), []).append(float(r["abs_error"]))
    m = lambda e, mod: statistics.mean(mae[(e, mod)])    # noqa: E731
    ctx.claim("sec. 5.1", "at $k=48$ its mean absolute error is 0.0364 (base) and 0.0174 (instruct), against 0.0107 and 0.0087 for the power law",
              same("0.0364", m("LP-cert (ours)", "base")) and same("0.0174", m("LP-cert (ours)", "instruct"))
              and same("0.0107", m("Power law", "base")) and same("0.0087", m("Power law", "instruct")),
              f"LP-cert {m('LP-cert (ours)', 'base'):.4f}/{m('LP-cert (ours)', 'instruct'):.4f}, power law {m('Power law', 'base'):.4f}/{m('Power law', 'instruct'):.4f}")
    ctx.claim("sec. 5.1", "erred by 0.0110 and 0.0119",
              same("0.0110", m("Doubling (ours)", "base")) and same("0.0119", m("Doubling (ours)", "instruct")),
              f"{m('Doubling (ours)', 'base'):.4f}, {m('Doubling (ours)', 'instruct'):.4f}")
    mani = json.load(open(os.path.join(ctx.results_dir, "run_manifest.json"), encoding="utf-8"))
    mmv = mani["mm_check"]["max_abs_diff_vs_chen_k<=16"]
    ctx.claim("sec. 4", "to within $4.4\\times10^{-4}$", same("4.4", mmv * 1e4, 1), f"max |difference| {mmv:.3e}")

    # discussion
    print("Discussion")
    ctx.claim("sec. 6", "moves pass@$16n$ by 0.17 to 0.41 for seven of our ten count laws",
              same("0.17", 2 * lo16, 2) and same("0.41", 2 * hi16, 2), f"twice the floors: {2 * lo16:.3f} to {2 * hi16:.3f}")
    ctx.claim("sec. 6", "while the floor at $m=1{,}319$ reaches 0.044 and 0.205", same("0.044", max(f4.values())) and same("0.205", hi16), "")
    q1 = float(t11["Crossing k* (256 attempts, 95%)"]["G1 (lenient)"].split()[0])
    q2 = float(t11["Crossing k* (256 attempts, 95%)"]["G2 (strict)"].split()[0])
    ctx.claim("sec. 6", "cross at $k^*=29$ under G1 and $k^*=46$ under G2", round(q1) == 29 and round(q2) == 46, f"k* = {q1:.3f} and {q2:.3f}")
    ctx.claim("sec. 6", "the base model leads significantly from $k=98$ and $k=126$ respectively",
              t11["Base significantly ahead from k"]["G1 (lenient)"] == "98" and t11["Base significantly ahead from k"]["G2 (strict)"] == "126", "Tab11")
    g1 = [first_num(r["G1 (lenient)"]) for q, r in t11.items() if q.startswith("Forecast") and first_num(r["G1 (lenient)"]) is not None]
    g2 = [first_num(r["G2 (strict)"]) for q, r in t11.items() if q.startswith("Forecast") and first_num(r["G2 (strict)"]) is not None]
    npml = t11["Forecast k* from n = 32, NPMLE"]["G1 (lenient)"]
    ctx.claim("sec. 6", "range from 27.7 to 61.3 (G1, where the NPMLE forecasts none) and 33.0 to 106.1 (G2)",
              same("27.7", min(g1)) and same("61.3", max(g1)) and same("33.0", min(g2)) and same("106.1", max(g2)) and npml == "--" and len(g1) == 3 and len(g2) == 4,
              f"G1 {min(g1)}-{max(g1)}, G2 {min(g2)}-{max(g2)}")
    ctx.claim("sec. 6", "The grader alone moves $k^*$ by more than half", q2 / q1 - 1 > 0.5, f"{q2:.1f} / {q1:.1f} = {q2 / q1:.2f}")

    print("Arithmetic")
    ctx.claim("sec. 4", "768,000 attempts in all", 10 * 300 * 256 == 768000, "10 x 300 x 256")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--paper", default=os.path.join(REPO, "paper"))
    ap.add_argument("--results", default=os.path.join(REPO, "results"))
    args = ap.parse_args(argv)
    ctx = Ctx(args.paper, args.results)
    check_table_floor(ctx)
    check_table_truth(ctx)
    check_table_horizons(ctx)
    check_table_stress(ctx)
    check_ledger(ctx)
    check_text(ctx)
    print(f"\n{ctx.ok} checks passed, {len(ctx.bad)} failed; {ctx.cells} table entries compared (values, shading, bold and star marks)")
    for b in ctx.bad:
        print("  FAILED:", b)
    print("OK: the paper's numbers agree with the shipped results" if not ctx.bad else "FAILED")
    return 1 if ctx.bad else 0


if __name__ == "__main__":
    sys.exit(main())
