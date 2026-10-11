# Data card

The repository contains no prompts, no problem text and no generated text beyond what is listed below. Problems are identified by index into the public benchmarks.

## Sampled streams (this study)

Each stream has 300 problems and 256 attempts per problem, drawn on one NVIDIA T4 GPU. That gives 10 streams and 768,000 attempts in total. Decoding is pure sampling at temperature 0.7, with no top-*p*, top-*k* or repetition penalty, so attempts are independent given the prompt.

| Code | Task | Model | Prompt | New-token cap | Stream index |
|---|---|---|---|---|---|
| G-B0.5 | GSM8K | `Qwen/Qwen2.5-0.5B` | two-shot | 256 | 1 |
| G-I0.5 | GSM8K | `Qwen/Qwen2.5-0.5B-Instruct` | chat template | 512 | 2 |
| G-B1.5 | GSM8K | `Qwen/Qwen2.5-1.5B` | SimpleRL-Zoo prompt | 512 | 3 |
| G-RL1.5 | GSM8K | `hkust-nlp/Qwen-2.5-1.5B-SimpleRL-Zoo` | SimpleRL-Zoo prompt | 512 | 4 |
| M-B0.5 | MATH-500 | `Qwen/Qwen2.5-0.5B` | two-shot | 512 | 5 |
| M-I0.5 | MATH-500 | `Qwen/Qwen2.5-0.5B-Instruct` | chat template | 512 | 6 |
| M-B0.5x2, x3, x4 | MATH-500 | `Qwen/Qwen2.5-0.5B` | two-shot | 512 | 7, 8, 9 |
| M-I0.5L | MATH-500 | `Qwen/Qwen2.5-0.5B-Instruct` | chat template | 1,024 | 10 |

- **M-I0.5** truncated 48.5% of its attempts at the 512-token cap. It was superseded by **M-I0.5L** (1,024 tokens). Its samples are kept, and the paper marks it as superseded.
- **M-B0.5x2, x3, x4** repeat M-B0.5 with new seeds. Together with M-B0.5 they give 1,024 attempts per problem as ground truth for experiment E8.
- The six *claim streams* of the paper are G-B0.5, G-I0.5, G-B1.5, G-RL1.5, M-B0.5 and M-I0.5L.
- **Problems.** GSM8K: a seeded 500-problem subset of the 1,319-problem test split, in a fixed order; the first 300 are used. MATH-500: a seeded permutation; the first 300 are used. The index lists are in `results/04_checkpoints/gsm8k_subset.pkl` and `math500_order.pkl`.
- **SimpleRL-Zoo prompt.** The model card does not state the training prompt. Both formats of that release were scored on 16 GSM8K training problems (disjoint from the evaluation set) with 16 attempts each, and the better one was kept (accuracy 0.83 against 0.52). The decision is recorded in `results/04_checkpoints/rl_template.json`.
- **Seeds.** Attempts of problem *i* in stream *s* are drawn in one batch from a generator seeded with `20261005 + 100003·s + i`, by Gumbel-max sampling.
- **Graders.** G1 compares the numeric value of the final answer (GSM8K) or the answer after a Hendrycks-style normalisation (MATH-500). G2 compares normalised strings (GSM8K) or requires an exact match up to spaces (MATH-500). All streams are regraded at analysis time from the stored final answers.
- **Compute.** About 21 GPU-hours on one T4 (estimated from the per-problem time recorded by the final sampler; earlier, slower runs are not counted). The sampler profile is in `results/04_checkpoints/profile_sampler.json` and in Table 4 of the paper.

### Files

`results/04_checkpoints/samples/<task>__<model>.jsonl` has one JSON record per problem (300 lines each, 10 files):

| Field | Content |
|---|---|
| `i` | index of the problem within the stream (0 to 299) |
| `g1`, `g2` | 256 outcomes (0 or 1) under grader G1 and grader G2 |
| `lens`, `cap` | length of each attempt in tokens; 1 if it reached the token cap |
| `final` | the extracted final answer of each attempt (at most 80 characters) |
| `last` | the last 32 characters of each generation |
| `steps`, `sec`, `tokens`, `batch`, `compactions` | sampler statistics for the problem |
| `sv`, `fp`, `env` | sampler version, stream fingerprint, software and hardware of the sampling session |

The generated text itself is not stored.

## Public count laws: Monkey Business

The Monkey Business release provides about 10,000 labelled attempts per problem. Nine configurations were fixed before their labels were analysed: Llama-3-8B-Instruct and Llama-3-70B-Instruct on GSM8K, MATH and CodeContests; Gemma-7B on MATH and CodeContests; Pythia-12B on MATH. They have 127 (GSM8K), 128 (MATH) and 140 (CodeContests) problems.

`results/04_checkpoints/monkey_business/<config>.npz` holds, for each configuration, `Y` (problems × 10,000 correctness labels, `uint8`), `lengths` (attempts per problem) and `meta` (a JSON string with the source repository, the size and SHA-256 of the downloaded file, and the time it was fetched). Only these labels were used; the generations are not included.

## Count laws used for the error floor (E10)

Ten laws: the nine Monkey Business configurations and the 1,024-attempt Qwen2.5-0.5B MATH-500 stream. For each, the empirical distribution of per-problem success rates over all attempts is the reference distribution, and the floor is computed for *n* = 32.

## Sources and licences

| Material | Source | Licence as listed upstream |
|---|---|---|
| GSM8K test split | `openai/grade-school-math` | MIT |
| MATH, MATH-500 | Hendrycks et al. (MATH); Lightman et al. (the 500-problem split); `HuggingFaceH4/MATH-500` | MIT (MATH, PRM800K); the MATH-500 dataset card states none |
| Monkey Business | `ScalingIntelligence/monkey_business` | MIT |
| Qwen2.5-0.5B, -0.5B-Instruct, -1.5B | Qwen team | Apache-2.0 |
| Qwen-2.5-1.5B-SimpleRL-Zoo | `hkust-nlp` | Apache-2.0 |

Licences were looked up in October 2026 and should be checked at the source before any redistribution. See [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for what this repository redistributes.
