# Claims and evidence

The paper separates three kinds of statement.

- **Pre-registered.** The decision criterion was written into the analysis code before the data that test it were analysed. No public registry was used, so "pre-registered" here means "fixed in the code first". The revision in the notebook's ledger (`rev. 2` to `rev. 7`) tells when each claim entered the analysis.
- **Exploratory.** Found on one dataset and tested on another, or defined after related results had been seen.
- **Descriptive.** A bound or a measurement; there is no test.

Where each claim is recorded:

| Place | Content |
|---|---|
| paper, Table 22 (Appendix, Claims Ledger) | the claims of the paper with status, criterion, measured value and verdict |
| `results/02_tables/csv/Tab08_claims.csv` | the full ledger the notebook wrote (28 rows, including the descriptive E10 rows) |
| `results/verdicts.json` | the verdict of every check and claim |
| notebook section 9 | the code that evaluates the criteria |
| paper, Table 3 (reading map) | where each claim is made and which appendix section holds its evidence |

## Summary of the verdicts

| Claim | Status | Criterion | Measured | Verdict |
|---|---|---|---|---|
| C1: certified extrapolation by linear estimators with range-based certificates stops near *k* = 2*n* at realistic *m* | pre-registered | *t*\*<sub>LP</sub>(0.1) ≤ 2.5 for every *n* at *m* ≤ 1,319 | 1.25 to 2.5 (4 at *m* = 10,000) | supported |
| C1 scope: where the two-point bound reaches 0.1 | descriptive | none | *t* = 11.2 to 34 | open for other estimators |
| C1 data: deviation at *k* = 1.5*n* inside the certificate | pre-registered | every stream | 6/6 Qwen streams; 9 Monkey Business configurations | supported |
| C1 accuracy: LP-cert against the best forecaster at *k* = 48 | pre-registered | BH *q* < 0.05 | 0.0364 against 0.0107 (base), 0.0174 against 0.0087 (instruct) | LP-cert worse |
| C2: beyond 2*n* the counts give only wide bands at realistic *m* | pre-registered | width ≥ max(0.1, 10 · 2*E*<sub>*n*</sub>) in every stream | minimum 0.102, median 0.232 | supported |
| C3: forecasts are set by the family, not the counts | pre-registered | median family index ≥ 3 | median 1.0 (1.8 without moment matching) | not supported; retired |
| C4: a reversal beyond 2*n* is not identified from *n* attempts | pre-registered, restated | significant reversal, not identified from any such *n* | *k*\* = 29.1 (G1), 46.4 (G2); not identified from *n* = 8, 16, 32 | supported (both graders) |
| C5a (E8): the family changes accuracy far beyond 2*n* | pre-registered | error gap ≥ 0.05 and family index ≥ 3 | gap 0.192 (0.062 among the three standard families); index 3.7 (1.7 without moment matching) at *k* = 992 | supported as run; see the moment-matching note in the paper |
| C5b (E8 and Monkey Business): the band holds the truth | pre-registered | all blocks but at most one | 8/8 blocks at every *k*; 9/9 configurations | supported |
| C5c, C5d (E8): in-window validation fails; the best family flips | exploratory | found on E8 | fails (0.0330 against 0.0075); flips (power law at *k* = 128, Beta-binomial at *k* = 992) | tested on Monkey Business |
| C5c (Monkey Business): in-window validation fails | pre-registered | at least half of the informative configurations | 2/6 | not supported |
| C5d (Monkey Business): the best family flips | pre-registered | at least half of the informative configurations | 0/6 | not supported |
| C5e: the family comparison in relative failure-rate terms | exploratory, defined after C5c and C5d were seen | none | 21 resolved cells with absolute error below 0.01 and fold error of 2 or more | no test |
| E10: error floor, bracket, problems needed, stability | descriptive | none | paper, Section 5.2 | no test |

The numbers in this table are those of `Tab08_claims.csv`. `make paper-numbers` compares the paper's ledger (Table 22) with that file row by row, and recomputes the numbers quoted in the paper's text.
