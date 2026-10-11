# Reproducing the results

There are five levels, from checking the shipped files to sampling again. The times below were measured on a 2-core Intel Xeon at 2.1 GHz with 7 GB of memory, Python 3.13 and the library versions in `requirements.txt`. No level up to 3 needs a GPU.

| Level | Command | What is recomputed | Time |
|---|---|---|---|
| 0 | `make verify` | nothing; the shipped files are checked against each other and against the paper | about 10 seconds |
| 1 | `make reproduce` | every table, figure and raw result, from the cached analysis stages | 1.3 minutes for the notebook run |
| 2 | `make reproduce-stages` | level 1, and the 31 stages the final run computed | 23 minutes for the notebook run |
| 3 | `python tools/run_notebook.py --drop-all-caches` | every analysis stage (115 in the final run), from the sampled outcomes | not run by us |
| 4 | sampling (`PASSK_MODE=sample`) | the 768,000 attempts | about 21 GPU-hours on one T4; not needed |

Levels 1 to 3 also need `requirements-dev.txt` (it adds `nbclient`, `nbformat` and `ipykernel`). Every run writes to its own folder under `runs/` (or the folder given by `--workdir`) and never touches `results/`.

## Level 0: checks

```bash
make verify
```

runs the seven checks listed in the [README](../README.md). `make theory-full` additionally recomputes all 28 rows of the horizon table (about a minute).

## Levels 1 and 2: re-running the notebook

```bash
make reproduce          # level 1
make reproduce-stages   # level 2
```

Both call `tools/run_notebook.py`, which

1. copies `results/04_checkpoints/` into a fresh folder (leaving out the stages that are to be recomputed),
2. executes `notebooks/passk-extrapolation-limits.ipynb` cell by cell with `PASSK_MODE=analyze`, `PASSK_RESUME_FROM` pointing at that copy, `MPLBACKEND=Agg` and `PYTHONHASHSEED=20261005`,
3. writes the executed notebook, a log and the new master archive into the run folder,

and then call `tools/compare_runs.py`, which compares the new archive with `results/`. Level 2 withholds the cache files with the prefixes `e10f_`, `e10fb_`, `e10ls_` and `e10bk_`: the error floor, its bootstrap, the likelihood-ratio simulation and the error bracket. These are the 31 stages that the final run computed; the other 86 were reused from earlier sessions (see [results-layout.md](results-layout.md)).

The first notebook cell installs a package with `pip` if numpy, scipy, pandas, matplotlib or mpmath is missing or older than the minimum it lists (numpy 1.23, scipy 1.10, pandas 1.5, matplotlib 3.7, mpmath 1.3). With `requirements.txt` installed it installs nothing. In analysis-only mode the notebook needs no network access: the Monkey Business labels come from `results/04_checkpoints/monkey_business/`. We checked this by repeating level 1 in a Linux network namespace that has only a loopback interface; the run completed and compared exactly as the first one (below).

## What "reproduces" means

We ran level 1 twice (once with the network disabled) and level 2 once, and compared the archives written by those runs with `results/`. Both level-1 runs gave the same comparison:

| Compared | Level 1 | Level 2 |
|---|---|---|
| Tables, CSV (29 files) and LaTeX (29 files) | identical | identical |
| Raw results, CSV (28 files) and NPZ (1 file) | identical | identical |
| `verdicts.json` | identical | identical |
| Figure data, JSON (30 files) | 26 identical, 4 equal within a relative 1e-9 (largest absolute difference 3 × 10⁻⁸, on values of order 10) | 23 identical, 4 equal within a relative 1e-9, 3 files with differences (below) |
| Stages computed / reused | 0 / 117 | 31 / 86, the same 31 as the final run |
| Run time | 1.3 minutes | 23.3 minutes (the final run took 35.4 minutes on a Kaggle CPU) |

The PDF figures are not compared byte for byte, because matplotlib writes a creation date into them; the series each figure is drawn from are compared instead. The sampled outcomes were not regenerated: sampling needs the GPU, and the outcomes are the input to everything above.

### The three figure-data files that differ at level 2

The files are `Fig27_error_floor_and_stability_data.json`, `Fig28_likelihood_ratio_simulation_data.json` and `Fig29_error_bracket_realistic_m_data.json`. Of their 752 numbers, 72 differ by more than a relative 1e-9:

| File | Numbers that differ | Largest relative difference | Largest absolute difference |
|---|---|---|---|
| `Fig27_…` (error floor, stability) | 28 of 313 | 0.51% | 1.2 × 10⁻⁴ |
| `Fig28_…` (likelihood-ratio simulation) | 27 of 162 | 1.8 × 10⁻⁶ | 1.4 × 10⁻⁷ |
| `Fig29_…` (error bracket) | 17 of 277 | 0.17% | 4.0 × 10⁻⁶ |

No table entry, raw result or verdict changed. The cause is the solver, not the data. The error floor is the largest separation of two success-rate distributions that a squared-Hellinger budget allows. It is found by a cutting-plane loop of linear programs (SciPy's HiGHS interface, `hel_solve` in notebook section 7.14b) that stops when the Hellinger distance of its candidate is within 2% of the budget; the candidate is then shrunk until the budget holds exactly. The value reported is that of a feasible point, hence a valid lower bound on the separation whichever machine computed it, but where the loop stops depends on which optimal vertex the LP solver returns, and that can differ between processors. The two runs solved slightly different numbers of LPs (floor stage: 2,398 in the final run, 2,384 here; error bracket: 23,785 and 23,802). The notebook's own solver check reports, for the final run and the re-run alike, that the certified separation lies within 1.1% of the LP upper bound in all 833 floor solves, so differences of the order we saw are what the stopping rule allows. The bootstrap and the likelihood-ratio simulation use the same solver.

Because the tables round to three digits, a value within about 10⁻⁴ of a rounding boundary could change its last digit on another processor; none did on ours. `make reproduce-stages` therefore compares figure data with `--fig-rtol 0.01 --fig-atol 1e-4`; tables, raw results and verdicts are always compared at a relative 1e-9.

## Level 3: all analysis stages

`python tools/run_notebook.py --drop-all-caches` withholds every analysis cache (`*.pkl`) and keeps the two problem lists, the sampled outcomes and the Monkey Business labels. The final run recorded 117 stages, two of which are the problem lists, so 115 stages are recomputed. The notebook is written to recompute every stage in this case, but we have not run it, so we give no time and cannot say whether the tables would come out unchanged, as they did for the 31 stages of level 2. Stages that use the LP solver may show differences of the kind described above.

## Level 4: sampling again

Sampling uses one T4-class GPU, the Hugging Face weights of the four models and `PASSK_MODE=sample`. The 256 attempts at problem `i` of stream `s` are drawn in one batch from a generator seeded with `20261005 + 100003·s + i`. We have not repeated the sampling, and GPU arithmetic can differ between devices and library versions, so a repeat need not draw the same attempts. The sampler is checkpointed per problem and resumes across sessions. The full sampling run took about 21 GPU-hours. The paper's results do not depend on repeating it, since the outcomes are included.

## Environment record

| | Final run (shipped results) | Re-runs for this repository |
|---|---|---|
| Machine | Kaggle CPU session | 2-core Intel Xeon at 2.1 GHz, 7 GB |
| Platform | Linux 6.18.48, x86-64, glibc 2.39 | Linux 6.18.44, x86-64, glibc 2.39 |
| Python | 3.13.15 | 3.13.16 |
| numpy / scipy / pandas | 2.1.3 / 1.16.3 / 2.3.3 | 2.1.3 / 1.16.3 / 2.3.3 |
| matplotlib / mpmath | 3.10.0 / 1.3.0 | 3.10.0 / 1.3.0 |
| Notebook mode | analysis only (`PASSK_MODE=analyze`) | analysis only |

The full record of the final run is `results/05_environment/environment_and_config.json`; `results/05_environment/pip_freeze.txt` lists all 858 packages of the Kaggle image (it includes packages the notebook does not use, such as PyTorch).

The repository's checks (`make verify`) were run on Python 3.13 only. They use numpy and SciPy for the theory check and the standard library elsewhere, so other recent Python versions will probably work, but we have not tried them.
