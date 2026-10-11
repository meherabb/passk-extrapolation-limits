# Paper sources

`main.tex` is the paper as submitted for double-blind review: ACL style with the `review` option and an anonymous author line.

| File | Content |
|---|---|
| `main.tex` | text, tables and appendices |
| `custom.bib` | bibliography (53 entries) |
| `acl.sty`, `acl_natbib.bst` | ACL style files, unmodified; they keep their own terms (see [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)) |
| `figures/` | the 20 figures the paper includes, as vector PDFs; each one is identical to the file of the same name in `../results/01_figures/pdf/` (`make checksums` compares them) |

## Building

pdfLaTeX and BibTeX, with a TeX installation that includes the `inconsolata` package (the ACL style loads it):

```bash
cd paper
latexmk -pdf main.tex        # from the repository root: make paper
```

Our test build gave 27 pages, with no undefined references or citations. It used an empty stand-in for `inconsolata`, which was not installed on the machine, so line breaks around monospaced text may differ slightly from a build with the real font.

`make paper-sources` (`tools/check_paper_sources.py`) checks, without compiling, that every figure file, citation key and cross-reference used in `main.tex` exists and that the author line is anonymous.

## The link in the abstract

The abstract links to an anonymous mirror of this repository. The address ends in `XXXX`, a placeholder for the suffix that the mirror service assigns. Replace it in `main.tex` once the mirror exists.

## How the numbers get into the paper

The paper's tables and figures come from `../results/` (tables from `02_tables/`, figures from `01_figures/pdf/`). `make paper-numbers` re-derives five of the tables and the numbers quoted in the text from the result files; [../docs/paper-to-output-map.md](../docs/paper-to-output-map.md) lists, for every table and figure of the paper, the file it comes from.
