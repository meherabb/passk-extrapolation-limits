# Layout of `results/`

`results/` is the master archive written by the notebook at the end of the final run, unpacked and left byte-for-byte as it was. The notebook names the archive `DoublingBarrier-QuadraticHorizon_passk-extrapolation_results_kaggle_20261009-212836.zip` (its working title, see [known-issues.md](known-issues.md)); the 338 files listed in `SHA256SUMS.txt` are checked by `make checksums`.

```
results/
├── 01_figures/
│   ├── pdf/         Fig01 … Fig29      vector figures (30 files; the paper uses 20 of them)
│   ├── png/         the same figures as bitmaps
│   └── data_json/   the series each figure is drawn from, one JSON file per figure
├── 02_tables/
│   ├── csv/         Tab01 … Tab22      29 tables
│   └── latex/       the same tables as LaTeX fragments
├── 03_logs/
│   └── raw_results/ unaggregated rows: per block, per replicate, per problem (28 CSV files and raw_outcomes.npz)
├── 04_checkpoints/
│   ├── *.pkl                           132 cache files (see below)
│   ├── samples/                        10 JSONL files, one per sampled stream
│   ├── monkey_business/                9 NPZ files with the Monkey Business correctness labels
│   ├── profile_sampler.json            sampler profile of one problem (paper, Table 4)
│   └── rl_template.json                the choice of prompt for the SimpleRL-Zoo pair
├── 05_environment/
│   ├── environment_and_config.json     software versions, every setting of the run, seeds
│   ├── pip_freeze.txt                  packages of the Kaggle image the final run used
│   └── nvidia_smi.txt                  "unavailable": the final run was analysis-only, on a CPU
├── README.md                           written by the notebook (see the note below)
├── SHA256SUMS.txt                      SHA-256 of every file above
├── file_inventory.csv                  path, size, category and SHA-256 of every file
├── run_manifest.json                   what the run did: stages computed or resumed, checks, seeds, Monkey Business sources
├── verdicts.json                       the verdict of every check and claim
├── key_results_summary.txt             plain-text summary written by the run
├── abstract_draft.txt                  draft abstract generated from this run's numbers (not the paper's abstract)
└── paper_outline.md                    outline generated with it
```

## Cached analysis stages

Each analysis stage is wrapped in `cached(name, fn)` in the notebook: if `04_checkpoints/<name>.pkl` exists, the stage is loaded; otherwise it is computed and saved. Most names contain a SHA-1 hash of the stage's input data or settings and a version number, so a stage computed on different data or with other settings has a different name and is recomputed. The stages are

| Prefix (files) | Content |
|---|---|
| `a1_` (1), `ab1_` to `ab4_` (5), `adv1_` to `adv3_` (4) | assumption checks, ablations, adversarial tests |
| `e1_` (1), `e2_` (1), `e3_` (4), `e4_` (6), `e5_`, `e5v3_` (3), `e6_`, `e6v3_` (13), `e7_` (2) | experiments E1 to E7 |
| `e8_`, `e8x_` (2), `e9_` (9) | ground truth far beyond 2*n*: MATH-500 and Monkey Business |
| `e10_` (1), `e10h_` (30), `e10lr_` (10), `e10bs_` (3) | E10: identification against tolerance, local two-point bound, profile likelihood-ratio interval, resampling of the benchmark |
| `e10f_` (10), `e10fb_` (3), `e10ls_` (8), `e10bk_` (10) | E10 at a fixed benchmark size: error floor, its resampling study, likelihood-ratio simulation, error bracket. These 31 stages are the ones the final run computed; the other 86 were reused from earlier runs |
| `c5e_` (1) | relative failure-rate errors (exploratory) |
| `e1_cache`, `lp_cache`, `m5_cache` | auxiliary caches of the horizon, LP and two-point computations |
| `gsm8k_subset.pkl`, `math500_order.pkl` | the problem lists; these are inputs, not analysis results |

`results/04_checkpoints/` holds 132 cache files. The final run recorded 117 stages in `run_manifest.json` (86 reused, 31 computed; two of the 117 are the problem lists). The other 15 files are not recorded as stages of that run: `e1_cache`, `lp_cache` and `m5_cache` are auxiliary caches, and the remaining 12 have names that match no stage of the final run, so they are probably left over from earlier revisions of the notebook. They are kept so that the checksums stay valid.

The caches are Python pickles. `make pickles` runs `tools/audit_pickles.py`, which lists everything each file would import when loaded without importing or executing anything; all 132 files request only numpy, pandas and builtin container types. Do not unpickle files from an untrusted copy of this repository: compare `SHA256SUMS.txt` first.

## Notes on files written by the notebook

- `results/README.md` is generated text that was written before several figures and tables were added. It lists Fig01 to Fig22 and Tab01 to Tab13 and says that two folders are empty. The archive in fact holds Fig01 to Fig29 and Tab01 to Tab22, as the table above shows. The file is kept as is so that the checksums stay valid.
- `abstract_draft.txt` and `paper_outline.md` are generated drafts. The paper's abstract and outline are in `paper/main.tex`.
- The tables in `02_tables/csv/` carry rounded values. The unrounded rows are in `03_logs/raw_results/`.
