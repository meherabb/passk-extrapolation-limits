# passk-extrapolation-limits

Code, data and results for an anonymous paper under double-blind review:

> **Extrapolating pass@k Beyond the Sampled Range: A Quadratic Horizon in Principle, an Error Floor in Practice**

Repeated-sampling evaluations often report or forecast pass@*k* for *k* far beyond the number *n* of attempts made on each problem. The paper asks how far beyond *n* the success counts can support such numbers. This repository holds the paper's LaTeX sources, the analysis notebook, every figure, table, log and cached result from the run behind the paper's numbers, and small tools that check the paper against those results.

## What the paper finds

- **In principle, a quadratic horizon.** With infinitely many problems, the per-problem success counts fix pass@*k* only up to 2*E*<sub>*n*</sub>(*x*<sup>*k*</sup>), twice the error of the best degree-*n* polynomial approximation of *x*<sup>*k*</sup> on [0, 1]. This is at most ε for every *k* up to ⌊*n*²/ln(4/ε)⌋, and at least 0.3396 once *k* ≥ 8*n*² (Theorem 1A).
- **In practice, much earlier.** At benchmark sizes in use (up to 1,319 problems), linear estimators with range-based certificates stop near *k* = 2*n*. On ten real count laws, a local two-point bound gives an error that every estimator exceeds with probability at least 1/4 under some nearby distribution. With 1,319 problems and *n* = 32, this floor at *k* = 16*n* is 0.084 to 0.205 for seven of the ten laws, and a profile likelihood-ratio interval comes within a factor of 1.02 to 1.22 of it.
- **Attempts beat problems.** At *k* = 512, the median number of problems below which no estimator reaches ±0.05 falls from 1.3 × 10<sup>5</sup> with *n* = 32 to 770 with *n* = 64.
- **Ground truth.** On 768,000 attempts sampled for this study and on the labels of the Monkey Business release, the nonparametric 95% bands contained the held-out truth in every block, while the accuracy of parametric forecasts depended on the assumed family. Some pre-registered predictions were not supported; the paper says which.

`make verify` checks every number in this list: the first bullet by an independent linear-programming computation, the others against the files in `results/`.

## Repository layout

```
paper/        LaTeX sources of the paper (ACL style, anonymous), figures, bibliography
notebooks/    the analysis notebook, clean (passk-extrapolation-limits.ipynb)
              and as executed for the paper, with outputs (executed/)
results/      everything the final run produced: figures, tables, raw results,
              cached intermediate results, sampled outcomes, environment record
tools/        checks and helpers (standard library, plus numpy/scipy for the theory check)
docs/         documentation (start with docs/paper-to-output-map.md)
```

`results/` is a byte-for-byte copy of the master archive written by the final run, so its `SHA256SUMS.txt` still applies. See [docs/results-layout.md](docs/results-layout.md) for the folder structure.

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
make verify                                         # about 10 seconds
```

The tools were tested with Python 3.13. Without `make`, run the commands listed in the `Makefile`; each check is a single Python call.

`make verify` runs seven checks and needs no GPU, network access or notebook run:

| Check | What it confirms |
|---|---|
| `checksums` | every file in `results/` has the SHA-256 recorded by the run, and each figure in `paper/figures/` equals the figure in `results/` |
| `notebooks` | the clean and the executed notebook contain exactly the same code |
| `pickles` | the 132 cached `.pkl` files import nothing except numpy, pandas and builtin types (they are read without being unpickled) |
| `paper-sources` | the figures, citations and cross-references of `paper/main.tex` resolve; the author line is anonymous |
| `paper-numbers` | five tables of the paper (error floor, ground truth, certified horizons, stress tests, claims ledger) agree cell by cell with the result files, and so do 66 claims quoted in the text, from the abstract to the appendix |
| `theory` | the constants of the proofs, and 2*E*<sub>*n*</sub>(*x*<sup>*k*</sup>) for the values quoted in the text, are recomputed independently by linear programming; `make theory-full` also checks all 28 rows of the horizon table |
| `anonymity` | no e-mail addresses, user paths, account-bearing URLs, tokens or identifying file metadata anywhere in the tree |

## Headline results

| Quantity | Value | Source |
|---|---|---|
| Largest *t* = *k*/*n* certified by LP-cert at accuracy 0.1, *m* = 164 / 300 / 1,319 / 10,000 | none / 1.25 / 2.5 / 4 | `Tab10_certified_horizons.csv` |
| Error floor at *m* = 1,319, *k* = 16*n*, seven of ten count laws | 0.084 to 0.205 | `Tab19_error_floor_realistic_m.csv` |
| Likelihood-ratio half-width over the floor, *k* = 16*n* | 1.02 to 1.22 | `Tab22_error_bracket_realistic_m.csv` |
| Median problems needed for ±0.05 at *k* = 512, *n* = 16 / 32 / 64 | 6.1 × 10<sup>9</sup> / 1.3 × 10<sup>5</sup> / 770 | `Tab15c_problems_needed_fixed_k.csv` |
| 95% band contains the truth, MATH-500 (*k* ≤ 992) and nine Monkey Business configurations (*k* ≤ 8,192) | 8/8 blocks in every case | `Tab13_…`, `Tab14a_…` |

Tables and figures of the paper are mapped to files in [docs/paper-to-output-map.md](docs/paper-to-output-map.md); each claim and its verdict is listed in [docs/claims-and-evidence.md](docs/claims-and-evidence.md).

## Re-running the analysis

The samples (768,000 attempts, plus the Monkey Business labels) are in `results/04_checkpoints/`, so the analysis can be re-run on a CPU in analysis-only mode. `tools/run_notebook.py` executes the notebook headlessly in a fresh folder under `runs/`; it never modifies `results/`. `tools/compare_runs.py` compares the new archive with the shipped one.

```bash
pip install -r requirements-dev.txt
make reproduce          # reuse cached stages, regenerate all figures, tables and the archive
make reproduce-stages   # additionally recompute the 31 stages of the final run (E10 floor, bootstrap, LR simulation)
```

| Level | What is recomputed | Time measured |
|---|---|---|
| `make verify` | nothing (checks only) | about 10 seconds |
| `make reproduce` | all tables, figures and raw results from cached stages | 1.3 minutes (notebook run) |
| `make reproduce-stages` | also the 31 stages of the final run | 23 minutes (35 on the Kaggle CPU of the final run) |
| `tools/run_notebook.py --drop-all-caches` | every analysis stage, from the sampled outcomes | not run by us |
| sampling | the 768,000 attempts themselves (GPU) | about 21 GPU-hours on one T4; not needed, the outcomes are included |

In both runs the tables, the raw results and the verdicts came out identical to the shipped ones. The figure data agree to a relative 1e-9 after `make reproduce`. After `make reproduce-stages`, 72 of the 752 numbers in the data of `Fig27` to `Fig29` (error floor, likelihood-ratio simulation, error bracket) differ by up to 0.5%, because the recomputed stages end an iterative solver at a tolerance. Details, the environment record and the exact comparison are in [docs/reproducing.md](docs/reproducing.md).

## Data and models

Ten streams of 256 attempts for each of 300 problems come from four Qwen2.5-family models on seeded subsets of GSM8K and MATH-500 (three of the streams repeat the Qwen2.5-0.5B MATH-500 stream with new seeds and give, with the original, 1,024 attempts per problem as ground truth). Nine configurations of the Monkey Business release (Llama-3, Gemma-7B, Pythia-12B on GSM8K, MATH and CodeContests) provide 10,000 labelled attempts per problem; only the correctness labels are used and only they are included. See [docs/data-card.md](docs/data-card.md).

The sample files hold, per problem, the outcome of every attempt under both graders, its length in tokens, whether it hit the token cap, the extracted final answer (at most 80 characters) and the last 32 characters of the generation. They do not hold the generated text.

## Notes for reviewers

- The notebook and the archive names carry an earlier working title ("DoublingBarrier-QuadraticHorizon"). The paper's title is the one above. See [docs/known-issues.md](docs/known-issues.md) for this and a few other discrepancies we know of.
- The abstract of `paper/main.tex` links to an anonymous mirror of this repository. The link is a placeholder until the mirror exists.
- `tools/scan_anonymity.py` looks for e-mail addresses, absolute user paths, account-bearing URLs, access tokens and identifying metadata (PDF, PNG, notebook and archive members), and for any strings you supply. It is included so that the check can be repeated.

## Licence and third-party material

Our code, text and results are released under the MIT licence ([LICENSE](LICENSE)). The ACL style files in `paper/`, the datasets and the models keep their own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Citation

Please cite the paper once the review is over; [CITATION.cff](CITATION.cff) will be completed then.
