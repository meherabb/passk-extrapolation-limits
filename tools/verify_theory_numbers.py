#!/usr/bin/env python3
"""Recompute the constants and the polynomial-approximation numbers of Theorem 1 independently of the notebook.

    python tools/verify_theory_numbers.py            # constants and the values quoted in the text (about a minute)
    python tools/verify_theory_numbers.py --full     # also the 28 (n, eps) pairs of the horizon table (a few minutes)

What is checked
  * closed-form constants of the proofs: (3-4/e)/9, the total-variation bound 0.334, the constants 0.158 and 0.0479 of
    Theorem 1(C), gamma_m of Proposition 1, B_32(1.5) = 0.00601 and the certificate 0.1236 at m = 300;
  * 2*E_n(x^k), twice the error of the best degree-n uniform approximation of x^k on [0, 1], for the values the text
    quotes: 2E_32(x^128) = 5.7e-5 and 2E_32(x^512) = 0.047, the extremal pair at (n, k) = (16, 2048), and the horizon
    K_0.01(32) = 307 with its bracket [170, 8192);
  * with --full, K_eps(n) = min{k : 2E_n(x^k) > eps} - 1 for every row of results/03_logs/raw_results/e1_horizons.csv.

Method: E_n(f) is computed as a linear program (scipy/HiGHS, Chebyshev basis, Chebyshev-Lobatto grid with
N + 1 points).  Restricting the sup-norm to the grid gives a lower bound; the error of the returned polynomial on a
much denser grid gives an upper bound.  Both are printed, so the reader sees how tight the bracket is.  Nothing here
is imported from, or reads, the notebook's own implementation; only the table of K values is read for comparison.

Needs numpy and scipy.  Exit status 0 if every check passes.
"""
import argparse
import csv
import math
import os
import sys
import time

import numpy as np
from numpy.polynomial import chebyshev as C
from scipy.optimize import linprog

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(ok, label, detail=""):
    print(f"  [{'ok' if ok else 'FAIL'}] {label}" + (f"   {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)


# ----------------------------------------------------------------------------------------------------------------
# E_n(x^k) by linear programming
def _lobatto(N):
    j = np.arange(N + 1)
    return 0.5 * (1.0 - np.cos(np.pi * j / N))


def best_approx_error(n, k, N=8000, N_dense=800000):
    """Return (lower, upper, a) with lower <= E_n(x^k) <= upper, using the polynomial with Chebyshev coefficients a."""
    x = _lobatto(N)
    V = C.chebvander(2.0 * x - 1.0, n)
    f = x ** k
    ones = np.ones((N + 1, 1))
    A = np.vstack([np.hstack([V, -ones]), np.hstack([-V, -ones])])
    b = np.concatenate([f, -f])
    c = np.zeros(n + 2)
    c[-1] = 1.0
    res = linprog(c, A_ub=A, b_ub=b, bounds=[(None, None)] * (n + 1) + [(0, None)], method="highs",
                  options={"primal_feasibility_tolerance": 1e-10, "dual_feasibility_tolerance": 1e-10})
    if res.status != 0:
        raise RuntimeError(f"LP failed for n={n}, k={k}: {res.message}")
    a = res.x[:n + 1]
    lower = float(res.x[-1])
    xd = _lobatto(N_dense)
    upper = float(np.max(np.abs(C.chebval(2.0 * xd - 1.0, a) - xd ** k)))
    return lower, upper, a


def two_E(n, k, **kw):
    lo, hi, _ = best_approx_error(n, k, **kw)
    return 2.0 * lo, 2.0 * hi


# ----------------------------------------------------------------------------------------------------------------
def closed_forms():
    print("Closed-form constants")
    e = math.e
    lb = (3 - 4 / e) / 9
    check(lb > 0.1698 and 2 * lb >= 0.3396, "Lemma 4: E_n(x^k) >= (3-4/e)/9 > 0.1698, so 2E >= 0.3396",
          f"(3-4/e)/9 = {lb:.6f}, twice = {2 * lb:.6f}")
    tv = 0.5 * math.sqrt(math.exp(1 / e) - 1)
    check(tv < 0.334 and (1 - tv) / 2 > 0.25, "Lemma 5: TV <= 0.5*sqrt(exp(1/e)-1) < 0.334, and (1-TV)/2 > 1/4",
          f"TV bound = {tv:.5f}, (1-TV)/2 = {(1 - tv) / 2:.4f}")
    c1 = (1 - 1 / e) / 4
    c2 = (1 - 1 / e) / (8 * math.sqrt(e))
    check(c1 >= 0.158 and 0.158 > 0.99 * c1, "Theorem 1(C): w=1/2 gives (1-1/e)/4 >= 0.158", f"{c1:.6f}")
    check(c2 >= 0.0479 and 0.0479 > 0.99 * c2, "Theorem 1(C): w=t/(4 sqrt(em)) gives (1-1/e)/(8 sqrt(e)) t/sqrt(m) >= 0.0479 t/sqrt(m)",
          f"{c2:.6f}")
    for m in (164, 300, 500, 1319, 10000):
        g = 2 * (1 - 0.75 ** (1 / (2 * m)))
        ok = abs(g * m - 0.29) < 0.005 and abs((1 - g / 2) ** m - math.sqrt(0.75)) < 1e-9
        check(ok, f"Proposition 1: gamma_m ~ 0.29/m and (1-gamma_m/2)^m = (3/4)^(1/2) at m = {m}",
              f"gamma_m * m = {g * m:.5f}")
    check(abs(math.sqrt(1 - 0.75) - 0.5) < 1e-12, "Proposition 1: Le Cam, TV <= sqrt(1 - (3/4)) = 1/2")
    n, t, eta = 32, 1.5, 0.5
    B = 4 * n * (t - 1) / (math.e ** 2 * t * (n - 1) ** 2) + 2.0 ** (-n) + math.exp(-eta * n)
    check(abs(B - 0.00601) < 5e-6, "B_32(1.5) = 0.00601", f"{B:.6f}")
    m, delta = 300, 0.05
    cert = t * math.sqrt(math.log(2 / delta) / (2 * m)) + B
    check(abs(cert - 0.1236) < 5e-5, "certificate at n=32, k=48, m=300, delta=0.05 is 0.1236", f"{cert:.5f}")
    check(abs(math.sqrt(math.log(2 / delta) / (2 * m)) - 0.0784) < 5e-5, "Hoeffding term sqrt(ln(2/delta)/(2m)) = 0.0784",
          f"{math.sqrt(math.log(2 / delta) / (2 * m)):.5f}")
    k_lo = math.floor(32 ** 2 / math.log(4 / 0.01))
    check(k_lo == 170 and 8 * 32 ** 2 == 8192, "horizon bracket for (n, eps) = (32, 0.01) is [170, 8192)",
          f"floor(n^2/ln(4/eps)) = {k_lo}, 8n^2 = {8 * 32 ** 2}")
    check(768000 == 10 * 300 * 256, "768,000 attempts = 10 streams x 300 problems x 256 attempts")


def quoted_values():
    print("Best polynomial approximation (linear program, bracket from a denser grid)")
    t0 = time.time()
    for (n, k, claim, test) in [
        (32, 128, "5.7e-5 (width of the identified set for pass@128, n = 32)", lambda v: 5.65e-5 <= v < 5.75e-5),
        (32, 512, "0.047 (n = 32, k = 16n)", lambda v: 0.0465 <= v < 0.0475),
        (16, 2048, "0.669 (extremal pair at (16, 2048); 0.6688 in the check table)", lambda v: 0.6685 <= v < 0.6695),
    ]:
        lo, hi = two_E(n, k)
        mid = 0.5 * (lo + hi)
        check(test(mid), f"2E_{n}(x^{k}) = {claim}", f"LP lower {lo:.6e}, upper {hi:.6e}, relative gap {(hi - lo) / hi:.1e}")
        ub = 4 * math.exp(-n * n / k)
        check(hi <= ub, f"   and 2E_{n}(x^{k}) <= 4 exp(-n^2/k)", f"{hi:.4e} <= {ub:.4e}")
    for n in (4, 16, 32):
        lo, hi = two_E(n, 8 * n * n)
        check(lo >= 0.3396, f"2E_{n}(x^(8 n^2)) >= 0.3396", f"{lo:.4f}")
    lo307, hi307 = two_E(32, 307)
    lo308, hi308 = two_E(32, 308)
    check(hi307 <= 0.01 < lo308, "K_0.01(32) = 307: 2E_32(x^307) <= 0.01 < 2E_32(x^308)",
          f"2E at 307 in [{lo307:.6f}, {hi307:.6f}], at 308 in [{lo308:.6f}, {hi308:.6f}]")
    print(f"  ({time.time() - t0:.0f} s)")


def full_horizons(path):
    print("Horizon table (every row of e1_horizons.csv)")
    if not os.path.isfile(path):
        check(False, f"{path} not found")
        return
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    t0 = time.time()
    worst = 0.0
    for r in rows:
        n, eps, K = int(r["n"]), float(r["eps"]), int(r["K_eps(n)"])
        lo_k, hi_k = int(r["floor(n^2/ln(4/eps))"]), int(r["8n^2"])
        a_lo, a_hi = two_E(n, K)
        b_lo, b_hi = two_E(n, K + 1)
        ok = a_hi <= eps < b_lo and lo_k <= K < hi_k and lo_k == math.floor(n * n / math.log(4 / eps)) and hi_k == 8 * n * n
        # monotone on a coarse grid below K, so that "min{k: 2E > eps} - 1" is what was computed
        ks = sorted({max(1, int(K * f)) for f in (0.25, 0.5, 0.75, 0.9)})
        mono = all(two_E(n, kk)[1] <= eps for kk in ks)
        stored_a, stored_b = float(r["2E at K"]), float(r["2E at K+1"])
        agree = abs(0.5 * (a_lo + a_hi) - stored_a) <= 2e-4 * max(stored_a, 1e-12) + 1e-9 and \
            abs(0.5 * (b_lo + b_hi) - stored_b) <= 2e-4 * max(stored_b, 1e-12) + 1e-9
        worst = max(worst, abs(0.5 * (a_lo + a_hi) - stored_a) / max(stored_a, 1e-12))
        check(ok and mono and agree, f"n = {n:3d}, eps = {eps:<5}: K = {K:6d}  2E(K) = {0.5 * (a_lo + a_hi):.6f} <= eps < 2E(K+1) = {0.5 * (b_lo + b_hi):.6f}"
              f"  bracket [{lo_k}, {hi_k})")
    print(f"  {len(rows)} rows, largest relative difference to the stored 2E at K: {worst:.1e}  ({time.time() - t0:.0f} s)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--full", action="store_true", help="also verify all rows of the horizon table")
    ap.add_argument("--horizons", default=os.path.join(REPO, "results", "03_logs", "raw_results", "e1_horizons.csv"))
    args = ap.parse_args(argv)
    closed_forms()
    quoted_values()
    if args.full:
        full_horizons(args.horizons)
    print("OK: every check passed" if not FAILS else f"FAILED: {len(FAILS)} check(s)")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
