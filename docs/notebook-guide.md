# Notebook guide

There are two notebooks with identical code (`make notebooks` checks that every cell source, type and id agrees):

| File | Content |
|---|---|
| `notebooks/passk-extrapolation-limits.ipynb` | clean: no outputs, no execution counts, only the kernel specification as metadata |
| `notebooks/executed/passk-extrapolation-limits.executed.ipynb` | as it was run for the paper, with outputs: Kaggle CPU session, analysis-only mode, 35.4 minutes |

The notebook has 89 cells (53 code, 36 markdown). Its first cell still carries the working title of the study (see [known-issues.md](known-issues.md)).

## Modes and switches

The notebook is controlled by environment variables, read in section 1.1. All are optional.

| Variable | Meaning |
|---|---|
| `PASSK_MODE` | `auto` (default): sample until the session budget is used, then analyse once every stream is complete; without a GPU it switches to `analyze`. `sample`: sample only. `analyze`: skip sampling and analyse what is on disk |
| `PASSK_RESUME_FROM` | a results folder or zip from an earlier session; its samples and cached stages are restored. `tools/run_notebook.py` sets this to a copy of `results/04_checkpoints/` |
| `PASSK_MB` | `0` skips the Monkey Business analysis (default `1`) |
| `PASSK_MB_DIR` | a folder that already holds the Monkey Business files, instead of downloading them. The labels in `results/04_checkpoints/monkey_business/` are restored by `PASSK_RESUME_FROM`, so nothing is downloaded in the reproduction runs |
| `PASSK_SESSION_MIN` | cap on sampling minutes (default: the whole session) |
| `PASSK_USE_DRIVE` | Colab only: `0` keeps outputs on the machine instead of Google Drive |
| `PASSK_DRY_RUN`, `PASSK_SMOKE` | `1` simulates attempts instead of sampling, or shrinks the replicate counts, for a fast test; both are stamped into every output file |

Outputs are written to `./outputs` (Kaggle: `/kaggle/working/outputs`; Colab with Drive: a folder on Drive). The notebook ends by writing the master archive that `results/` is a copy of.

## Sections

Cell numbers count from 0 over all cells. Section numbers are the numbers in the notebook's headings.

| Section | Cells | Content |
|---|---|---|
| 1 Setup | 3 to 6 | dependencies and switches (1.1); environment, paths, seeds (1.2); figure style, statistics and checkpoint helpers, configuration (1.3); resume check (1.4) |
| 2 Problem definition | 8, 9 | objects of Theorem 1 (2.1); assumption checks A1 to A3 (2.2) |
| 3 Method | 11 to 15 | doubling estimator and Chen et al.'s estimator (3.1); LP-optimised estimator and its certificate (3.2); brackets for 2*E*<sub>*n*</sub>, the horizon, the extremal pair (3.3); optimised two-point lower bound and the Lemma 6 pair (3.4); partial-identification band (3.5) |
| 4 Baselines | 17, 18 | power law, Beta-binomial, NPMLE and moment matching; a reproducibility self-check that runs part of the pipeline twice (4.2) |
| 5 Datasets | 20, 21 | GSM8K and MATH-500 (5.1); prompts, stop rules, graders G1 and G2 (5.2) |
| 6 Inference | 23 to 26 | model loading and batched sampler (6.1); sampler profile (6.1b); sampling driver with per-problem checkpoints (6.2) |
| 7 Evaluation | 28 to 76 | assumption checks and Figure 17 (7.0); E1 Theorem 1(A) numerics (7.1); E2 Theorem 1(B) on data (7.2); E3 Theorem 1(C) and the sandwich (7.3, 7.3b); E4 extrapolation on real data (7.4, 7.4b); E5 crossing pair (7.5); ablations (7.6); data breakdown and efficiency (7.7); corollary verdicts (7.8); E6 every stream (7.9); E7 certified horizon at realistic *m* (7.10); Ab4 band construction (7.11); E8 ground truth, MATH-500 (7.12, 7.12b); E9 Monkey Business (7.13); E10 the error floor and the likelihood-ratio interval (7.14 to 7.14g); C5e relative errors (7.15) |
| 8 Robustness | 78 to 81 | (A1) violations (8.1); extremal pairs inside real data, adversarial selection (8.2); grader ablation (8.3) |
| 9 Claims | 83 | comparison rows, claims ledger (`Tab08`), draft abstract |
| 10 Packaging | 85 | run manifest, key-results summary |
| 11 Final | 87, 88 | summary and the master archive (figures, tables, logs, checkpoints, environment, `SHA256SUMS.txt`) |

Cells marked `[analysis]` in their first line run in analysis-only mode.

## How stages are cached

A stage is computed inside `cached(name, fn)`. If `outputs/checkpoints/<name>.pkl` exists, it is loaded and the log line says `loaded from checkpoint`; otherwise the stage runs and is saved. Names contain hashes of the data and the settings, so a changed input gives a new name. The run manifest records, for every stage, whether it was resumed or computed and how long it took. To recompute a stage, remove its `.pkl` from the folder named by `PASSK_RESUME_FROM`, or let `tools/run_notebook.py --drop-stage <prefix>` leave it out.

## Running it

- **Headless, on a CPU, from the shipped samples:** `python tools/run_notebook.py` (see [reproducing.md](reproducing.md)).
- **Interactively:** install `requirements.txt` and, before starting the kernel, set `PASSK_MODE=analyze` and `PASSK_RESUME_FROM` to a folder that contains `04_checkpoints/` (`tools/run_notebook.py` builds one from `results/04_checkpoints/`; running it that way is the only route we tested). Outputs go to `./outputs`.
- **Sampling again:** needs a single T4-class GPU, `PASSK_MODE=sample`, the model weights from the Hugging Face Hub and about 21 GPU-hours for all streams. The sampler is checkpointed per problem and resumes across sessions. This path is not needed to reproduce anything in the paper.
