# Results archive: A Quadratic Horizon and a Doubling Barrier: Distribution-Free Limits on Extrapolating pass@k from Repeated Samples

- Archive: `DoublingBarrier-QuadraticHorizon_passk-extrapolation_results_kaggle_20261009-212836.zip`
- Run mode: **ANALYSIS-ONLY RUN (attempts sampled on a T4 GPU in earlier sessions)**
- Environment: kaggle; run started 2026-10-09T20:53:10; archived 2026-10-09T21:28:38; wall-clock 0.59 h
- Models: base = `Qwen/Qwen2.5-0.5B`, instruct = `Qwen/Qwen2.5-0.5B-Instruct`, base15 = `Qwen/Qwen2.5-1.5B`, rl15 = `hkust-nlp/Qwen-2.5-1.5B-SimpleRL-Zoo`
- Data (problems per stream): gsm8k:base m = 300, gsm8k:instruct m = 300, gsm8k:base15 m = 300, gsm8k:rl15 m = 300, math500:base m = 300, math500:instruct m = 300, math500:base_x2 m = 300, math500:base_x3 m = 300, math500:base_x4 m = 300, math500:instruct1k m = 300; N = 256 attempts per problem and stream (8 blocks of 32); seed 20261005
- Graders: G1 lenient equivalence (primary; numeric for GSM8K, normalised LaTeX for MATH-500); G2 strict string match (verifier ablation Ab3)

## Verdicts

- Claims (Section 9): E10 floor: REPORTED; E10 floor, resampled problems: REPORTED; E10 bracket: REPORTED; E10: REPORTED; E10, fixed k: REPORTED; E10a: REPORTED; E10 at +-0.1: REPORTED; E10b: REPORTED; E10b on drawn benchmarks: REPORTED; E10, resampled problems: REPORTED; C1: SUPPORTED; C1 scope: OPEN (barrier holds for the class, not for all estimators); C1 data: SUPPORTED; C1 accuracy, Base: LP WORSE; C1 accuracy, Instruct: LP WORSE; C2: SUPPORTED; C2 decomposition: REPORTED; C3: NOT SUPPORTED (retired); C4, G1: SUPPORTED; C4, G2: SUPPORTED; C5a, E8: SUPPORTED (as run; see moment-matching note); C5b, E8: SUPPORTED; C5c, E8: EXPLORATORY; C5d, E8: EXPLORATORY; C5b, Monkey Business: SUPPORTED; C5c, Monkey Business: NOT SUPPORTED; C5d, Monkey Business: NOT SUPPORTED; C5e: EXPLORATORY
- A1 (Base): PASS
- A2 (Base): PASS
- A3 (Base): PASS
- A1 (Instruct): PASS
- A2 (Instruct): PASS
- A3 (Instruct): FAIL (p_i read as verifier-acceptance probability)
- Theorem 1(A) horizon bracket: PASS
- Corollary 3 (numerical): PASS
- Corollary 1 (Base): PASS
- Corollary 2 (Base): PASS
- Overdispersion (Base): PASS
- Corollary 1 (Instruct): PASS
- Corollary 2 (Instruct): PASS
- Overdispersion (Instruct): PASS
- Corollary 3 (data-facing, Lemma 6): PASS
- PI-band coverage (semi-synthetic): PASS
- C4 reversal beyond 2n not identified (G1): PASS: not identified from n = [8, 16, 32]
- C4 reversal beyond 2n not identified (G2): PASS: not identified from n = [8, 16, 32]
- Ab1: lambda=0 certificate exceeds lambda*: YES
- Ab1: certificate settles across G: YES
- Ab2: contrast inside envelope (all kernels): PASS
- C2 wide bands beyond 2n (claim streams): PASS
- C3 family-driven forecasts: FAIL
- C1 certified horizon near 2n at realistic m: PASS
- C1 scope: two-point bound binds at t (eps=0.1, realistic m): 11.2 to 34 (LP certifies up to 2.5)
- Ab4: the band used does not widen with more attempts: PASS
- C5a family choice changes accuracy (E8): PASS
- C5b band covers ground truth (E8): PASS
- C5c backtest (E8, exploratory): FAILS (picked far error 0.0330 vs best 0.0075)
- C5d family flip (E8, exploratory): FLIP (best at k=128: Power law; at k=992: Beta-bin.)
- C5a without moment matching (E8, descriptive): family index 1.7 at k=992 (pre-registered rule needs 3); error gap among the three standard families 0.062
- C5c backtest fails to find the far-k family (Monkey Business, pre-registered): NOT SUPPORTED (2/6 informative streams)
- C5d best family flips between 4n and the far k (Monkey Business, pre-registered): NOT SUPPORTED (0/6 informative streams)
- C5b band covers ground truth (Monkey Business, pre-registered): PASS (9/9 configurations)
- C1 data: doubling deviation inside Theorem 1(B) (Monkey Business): PASS (9 configurations)
- E10a DKW band: problems for width 0.1 (descriptive): k=4n: 2.2e+02-1.1e+06; k=16n: >2e+12 in 2/10
- E10 problems needed for +-0.05, any estimator (descriptive): k=2n: 20 to 66, not binding in 2/10; k=4n: 59 to 840, not binding in 2/10; k=8n: 170 to 3.0e5, not binding in 2/10; k=16n: 260 to 2.9e10, not binding in 2/10; k=32n: 260 to 5.0e11, >1e12 in 2/10, not binding in 2/10; k=64n: 300, >1e12 in 7/10, not binding in 2/10
- E10 problems needed for +-0.1, any estimator (descriptive): k=2n: 10 to 16, not binding in 7/10; k=4n: 17 to 100, not binding in 3/10; k=8n: 58 to 4,200, not binding in 3/10; k=16n: 11 to 4.1e6, not binding in 2/10; k=32n: 12 to 7.5e11, not binding in 2/10; k=64n: 13 to 3.6e11, >1e12 in 2/10, not binding in 2/10
- E10b likelihood-ratio band against the bound (descriptive): LR band at level 3/4 needs 3.3-5.4x the bound's problems (t = 4, 8, 16n; 24 pairs); at 95% 10-16x; DKW band 490-28,000x
- E10 bound under resampling of problems (descriptive): MATH L3-8B-I k=4n: 170 to 320 (full data 260; more than 1,319 in 0/20); MATH L3-8B-I k=16n: 57,000 to 6.6e7 (full data 5.7e6; more than 1,319 in 20/20); CC L3-70B-I k=4n: 98 to 160 (full data 120; more than 1,319 in 0/20); CC L3-70B-I k=16n: 59,000 to 3.6e6 (full data 6.2e5; more than 1,319 in 20/20); MATH L3-70B-I k=4n: 29 to 88 (full data 63; more than 1,319 in 0/20); MATH L3-70B-I k=16n: 48 to 9,400 (full data 260; more than 1,319 in 5/20)
- E10 error floor at realistic m, any estimator (descriptive): m = 1,319: k=2n 0.001-0.011 (above 0.05 for 0/10), k=4n 0.002-0.044 (above 0.05 for 0/10), k=8n 0.002-0.122 (above 0.05 for 5/10), k=16n 0.003-0.205 (above 0.05 for 7/10), k=32n 0.004-0.242 (above 0.05 for 7/10), k=64n 0.005-0.310 (above 0.05 for 7/10); at k=16n the floor exceeds 0.05 for 7/10 count laws (0.084 to 0.205)
- E10 error floor under resampling of problems (descriptive): MATH L3-8B-I k=4n: floor 0.028-0.033 (full data 0.032; spread 1.19; problems needed spread 1.92); MATH L3-8B-I k=16n: floor 0.065-0.103 (full data 0.087; spread 1.59; problems needed spread 1,200); CC L3-70B-I k=4n: floor 0.017-0.023 (full data 0.020; spread 1.31; problems needed spread 1.67); CC L3-70B-I k=16n: floor 0.097-0.129 (full data 0.116; spread 1.33; problems needed spread 62); MATH L3-70B-I k=4n: floor 0.018-0.024 (full data 0.022; spread 1.34; problems needed spread 3.02); MATH L3-70B-I k=16n: floor 0.026-0.058 (full data 0.043; spread 2.24; problems needed spread 200)
- E10b likelihood-ratio interval on drawn benchmarks (descriptive): 22 (count law, t) pairs, 100 draws each at the best-case m: median width 0.082-0.097 (best case 0.1); coverage at nominal 0.75: k=4n 0.83 (8 pairs), k=8n 0.95 (8 pairs), k=16n 0.99 (6 pairs); midpoint within +-0.05 in 81% or more of the draws of every pair
- E10 error bracket at realistic m (descriptive): m = 1,319: likelihood-ratio half-width over the floor (median of 100 drawn benchmarks; count laws with floor above 0.01) k=4n 1.31-1.56, k=8n 1.12-1.29, k=16n 1.02-1.22; coverage at nominal 0.75: k=4n 0.85, k=8n 0.92, k=16n 0.97; at k=16n, for the 7 count laws whose floor exceeds 0.05: floor 0.084-0.205, half-width 0.089-0.222
- C5e relative failure-rate errors (exploratory): 21 resolved cells with |error| < 0.01 but fold error >= 2; backtest >= 2x best fold in 2/10; relative flips 1
- Ab3: G1/G2 statuses agree: 12/12

## Contents

| Folder | Contents | Files |
|---|---|---|
| `01_figures/pdf/` | camera-ready vector figures (Fig01-Fig22) | 30 |
| `01_figures/png/` | 300-dpi previews of the same figures | 30 |
| `01_figures/data_json/` | exact plotted data, figure size and palette for every figure | 30 |
| `02_tables/latex/` | booktabs LaTeX tables (Tab01-Tab13) | 29 |
| `02_tables/csv/` | the same tables as CSV | 29 |
| `03_logs/raw_results/` | per-seed (per-block) results, raw 0/1 outcome matrices, per-problem counts | 29 |
| `03_logs/audit_samples/` | 2% verbatim generations with both grades (A3 audit) | 0 |
| `04_checkpoints/` | resume state: sampled attempts per stream, sampler profile, RL template, analysis caches | 153 |
| `05_environment/` | pip freeze, nvidia-smi, environment and full configuration | 3 |
| `06_notebook/` | the executed notebook (not captured automatically; add the .ipynb you ran by hand) | 0 |
| (root) | run_manifest.json, key_results_summary.txt, verdicts.json, file_inventory.csv, SHA256SUMS.txt, README.md | 8 |

## How to reproduce

1. Check integrity: from inside this folder run `sha256sum -c SHA256SUMS.txt`.
2. Re-run without re-sampling: copy `04_checkpoints/` to `outputs/checkpoints/` next to the notebook (Kaggle: `/kaggle/working/outputs/checkpoints/`) and Run all; sampling and finished analyses resume from it.
3. Full re-run from scratch: Run all on one T4 GPU over several sessions; attach the latest results or resume zip each time (Section 1 merges its checkpoints) and the analysis runs once every stream reaches its target.
4. Regenerate or restyle a figure without models or data: load `01_figures/data_json/<FigNN_name>_data.json`; it holds every plotted series, the figure size and the palette.
5. Raw attempt outcomes: `03_logs/raw_results/raw_outcomes.npz`, keys `<model>_G1`/`<model>_G2` (main pair) and `<task>__<model>_G1`/`_G2` (every stream), 0/1 arrays of shape m x 256.

## Naming

Notebook names F1-F22 and T1-T13 are archived as Fig01-Fig22 and Tab01-Tab13 (zero-padded). Checkpoint names are unchanged so the notebook can resume from them. `file_inventory.csv` maps every archived file to its source path, size and SHA-256.
