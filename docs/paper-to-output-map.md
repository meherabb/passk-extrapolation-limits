# Paper to output map

Every figure and table of `paper/main.tex`, the file that holds its data, and the notebook section that produces it. Notebook sections are the numbers in the headings of `notebooks/passk-extrapolation-limits.ipynb` (see [notebook-guide.md](notebook-guide.md)); "E1" to "E10" are the experiment names used in the notebook and the paper's appendix.

Each figure exists in three forms in `results/01_figures/`: `pdf/<name>.pdf`, `png/<name>.png` and `data_json/<name>_data.json` (the series the figure is drawn from). The PDF files in `paper/figures/` are byte-identical copies of those in `results/01_figures/pdf/`; `make checksums` checks this. Each table exists in `results/02_tables/csv/<name>.csv` and `results/02_tables/latex/<name>.tex`.

## Figures

| Paper item | File in `results/01_figures/pdf/` | Notebook section | Shows |
|---|---|---|---|
| Figure 1 (`fig:horizon`) | `Fig01_population_horizon.pdf` | 7.1 (E1) | Theorem 1(A): 2E_n(x^k) against k/n^2; horizons |
| Figure 2 (`fig:certified`) | `Fig20_certified_horizon_vs_m.pdf` | 7.10 (E7) | certified horizon against benchmark size |
| Figure 3 (`fig:floor`) | `Fig27_error_floor_and_stability.pdf` | 7.14e (E10) | error floor against t; stability under resampling |
| Figure 4 (`fig:a1tests`) | `Fig17_assumption_A1_tests.pdf` | 7.0b | permutation tests of assumption (A1) |
| Figure 5 (`fig:a1violation`) | `Fig07b_A1_violation_block_drift.pdf` | 8.1 (Adv1) | (A1) violation by block drift |
| Figure 6 (`fig:bias`) | `Fig02_bound_vs_measured_bias.pdf` | 7.2 (E2) | Theorem 1(B) on data: bound against measured bias |
| Figure 7 (`fig:lemma6`) | `Fig08_theorem1C_lemma6.pdf` | 7.3 (E3) | Theorem 1(C): failure fractions on the Lemma 6 pair |
| Figure 8 (`fig:sandwich`) | `Fig03_sandwich.pdf` | 7.3b (E3) | LP certificate against the two lower bounds |
| Figure 9 (`fig:bracket`) | `Fig29_error_bracket_realistic_m.pdf` | 7.14g (E10) | error bracket at m = 1,319 |
| Figure 10 (`fig:needed`) | `Fig24_problems_needed_any_estimator.pdf` | 7.14b (E10) | problems needed by any estimator |
| Figure 11 (`fig:tightness`) | `Fig26_bound_tightness_and_stability.pdf` | 7.14c, 7.14d (E10) | tightness of the bound; resampling study |
| Figure 12 (`fig:lrsim`) | `Fig28_likelihood_ratio_simulation.pdf` | 7.14f (E10) | likelihood-ratio interval on drawn benchmarks |
| Figure 13 (`fig:bands`) | `Fig05_passk_bands_forecasts.pdf` | 7.4b (E4) | 95% bands and parametric forecasts on GSM8K |
| Figure 14 (`fig:e8`) | `Fig22_ground_truth_beyond_2n.pdf` | 7.12 (E8) | ground truth far beyond 2n, MATH-500 |
| Figure 15 (`fig:family`) | `Fig23_family_choice_ground_truth.pdf` | 7.13 (E9) | can the counts choose the family? (E8 and Monkey Business) |
| Figure 16 (`fig:relative`) | `Fig25_relative_failure_rate_errors.pdf` | 7.15 (C5e) | family comparison in relative failure-rate terms |
| Figure 17 (`fig:crossing`) | `Fig06_sign_identification.pdf` | 7.5 (E5) | crossing pair under both graders |
| Figure 18 (`fig:bandconstruction`) | `Fig21_band_construction.pdf` | 7.11 (Ab4) | band construction against the number of attempts |
| Figure 19 (`fig:ablations`) | `Fig11_ablations.pdf` | 7.6 (Ab1, Ab2) | LP design and kernel ablations |
| Figure 20 (`fig:adversarial`) | `Fig12_adversarial_pairs_and_selection.pdf` | 8.2 (Adv2, Adv3) | adversarial pairs and selection |

Figures produced by the notebook that are not in the paper: `Fig04_certified_horizons_nmin`, `Fig07a_A1_violation_copy_model`, `Fig09_baseline_comparison`, `Fig10_per_seed_errors`, `Fig13_data_breakdown`, `Fig14_efficiency`, `Fig15_mechanism_bias_by_rate`, `Fig16_piband_coverage`, `Fig18_bands_vs_forecasts_all_streams`, `Fig19_family_dependence`.

## Tables

| Paper item | File(s) in `results/02_tables/csv/` | Notebook section | Shows |
|---|---|---|---|
| Table 1 (`tab:floor`) | `Tab19_error_floor_realistic_m.csv`, `Tab22_error_bracket_realistic_m.csv` | 7.14e, 7.14g (E10) | error floor, LR half-width, ratio and coverage |
| Table 2 (`tab:truth`) | `Tab13b_ground_truth_family_choice.csv`, `Tab14a_monkey_business_data.csv`, `Tab14b_monkey_business_family_choice.csv` | 7.12b, 7.13 | ground truth far beyond 2n (the E8 row is computed from the raw per-block file) |
| Table 3 (`tab:map`) | none | - | reading map of claims and evidence; written by hand |
| Table 4 (`tab:profile`) | `results/04_checkpoints/profile_sampler.json` (not a CSV) | 6.1b | sampler profile |
| Table 5 (`tab:assumptions`) | `Tab01_assumption_tests.csv` | 7.0 | assumption checks, main pair |
| Table 6 (`tab:streams`) | `Tab12a_streams_checks.csv` | 7.9 (E6) | every stream with 256 attempts per problem |
| Table 7 (`tab:sandwich`) | `Tab05a_sandwich.csv` | 7.3b (E3) | LP certificate against the lower bounds (selected rows) |
| Table 8 (`tab:horizons`) | `Tab10_certified_horizons.csv`; the Theorem 1(C) columns and unrounded values: `results/03_logs/raw_results/e7_certified_horizons.csv` | 7.3b, 7.10 (E7) | certified horizons in t = k/n |
| Table 9 (`tab:inwindow`) | `Tab03_estimator_comparison.csv`, `Tab03b_estimator_tests.csv` | 7.4 (E4) | in-window accuracy of every estimator and the paired tests |
| Table 10 (`tab:needed`) | `Tab15_problems_needed_any_estimator.csv`, `Tab15d_problems_needed_pm01.csv`, `Tab15c_problems_needed_fixed_k.csv` | 7.14b, 7.14c (E10) | problems needed at +-0.05, +-0.1 and at fixed k |
| Table 11 (`tab:lrbound`) | `Tab17_upper_vs_lower_bound.csv` | 7.14c (E10) | likelihood-ratio and DKW bands against the bound, in problems |
| Table 12 (`tab:stability`) | `Tab20_floor_vs_problems_needed_stability.csv` | 7.14e (E10) | stability under 20 resamples of the benchmark |
| Table 13 (`tab:lrsim`) | `Tab21_likelihood_ratio_simulation.csv` | 7.14f (E10) | likelihood-ratio interval on 100 drawn benchmarks |
| Table 14 (`tab:bracket`) | `Tab22_error_bracket_realistic_m.csv` | 7.14g (E10) | error bracket at m = 1,319 for k = 4n and 8n |
| Table 15 (`tab:streamsextrap`) | `Tab12b_streams_extrapolation.csv` | 7.9 (E6) | extrapolation on every stream |
| Table 16 (`tab:e8`) | `Tab13_ground_truth_math500.csv` | 7.12 (E8) | E8: mean absolute error against the truth |
| Table 17 (`tab:mbdata`) | `Tab14a_monkey_business_data.csv` | 7.13 (E9) | the nine Monkey Business configurations |
| Table 18 (`tab:mbfamily`) | `Tab14b_monkey_business_family_choice.csv` | 7.13 (E9) | family choice on Monkey Business |
| Table 19 (`tab:relative`) | `Tab16_relative_failure_rate_errors.csv` | 7.15 (C5e) | fold error of the failure rate |
| Table 20 (`tab:crossing`) | `Tab11_crossing_pair.csv` | 7.5 (E5) | the crossing pair under G1 and G2 |
| Table 21 (`tab:stress`) | `Tab06_robustness_adversarial.csv`; the ranges: `results/01_figures/data_json/Fig07a_…`, `Fig07b_…` and `Fig12_…` | 8.1, 8.2 | stress tests on the main pair |
| Table 22 (`tab:ledger`) | `Tab08_claims.csv` | 9 | claims ledger |

`make paper-numbers` compares Tables 1, 2, 8, 21 and 22 with these files cell by cell.

Tables produced by the notebook that are not typeset in the paper: `Tab02_corollary_checks`, `Tab04_sota_comparison_rows`, `Tab05b_attempt_budget`, `Tab07_verifier_ablation_G1_vs_G2`, `Tab15b_dkw_band_vs_benchmark_size`, `Tab18_bound_under_resampling`. Several of them are quoted in the text (for example `Tab02_corollary_checks.csv` for the checks of the theory).

## Raw results behind the tables

`results/03_logs/raw_results/` holds the unaggregated rows (per block, per replicate, per problem). For example `e1_horizons.csv` has the 28 horizon rows of Theorem 1(A), `e3_lemma6_failure_fractions.csv` the failure fractions of the Lemma 6 pairs, `e4_per_block_results.csv` and `e8_ground_truth_per_block.csv` the errors of every estimator on every 32-attempt block, `e7_certified_horizons.csv` the certified horizons, and `raw_outcomes.npz` the outcome arrays of the ten streams. `tools/verify_paper_numbers.py` reads these files directly for the numbers that the CSV tables round.

## Numbers quoted in the text

`tools/verify_paper_numbers.py` lists, for each number quoted in the abstract, introduction, results, discussion and conclusion, the sentence fragment it comes from and the table or raw file it is recomputed from. Run `python tools/verify_paper_numbers.py` to see the list.
