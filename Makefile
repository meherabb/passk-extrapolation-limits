# Convenience targets. Each one is a plain Python command, so on a system without make you can run the
# command shown in the recipe directly.  `make help` lists the targets.

PYTHON     ?= python3
ANON_TERMS ?= .anonymity-terms
# Folder for the output of a notebook run; it must not exist yet (or be empty). Override with  make reproduce RUN=runs/other
reproduce:        RUN ?= runs/reproduce
reproduce-stages: RUN ?= runs/reproduce-stages

.DEFAULT_GOAL := help
.PHONY: help verify checksums notebooks pickles paper-sources paper-numbers theory theory-full anonymity \
        reproduce reproduce-stages paper clean

help:
	@echo "Checks that need no notebook run:"
	@echo "  make verify            everything below except theory-full (about 10 seconds)"
	@echo "  make checksums         SHA-256 of every file in results/, and paper figures == result figures"
	@echo "  make notebooks         the clean and the executed notebook hold identical code"
	@echo "  make pickles           what the cached .pkl files would import (nothing is unpickled)"
	@echo "  make paper-sources     figures, citations and cross-references of paper/main.tex"
	@echo "  make paper-numbers     numbers in the paper against results/02_tables and results/03_logs"
	@echo "  make theory            constants of Theorem 1 and 2E_n(x^k) recomputed by linear programming"
	@echo "  make theory-full       ... and all 28 horizon rows (about a minute)"
	@echo "  make anonymity         scan for names, e-mail addresses, paths, tokens and file metadata"
	@echo "Re-running the analysis (needs requirements-dev.txt; output goes to a new folder under runs/, never to results/):"
	@echo "  make reproduce         reuse the cached stages and compare with results/ (about 2 minutes)"
	@echo "  make reproduce-stages  recompute the 31 stages of the final run and compare (about 25 minutes)"
	@echo "Other:"
	@echo "  make paper             build paper/main.pdf (needs a TeX Live installation with the inconsolata package)"
	@echo "  make clean             remove LaTeX build files and Python caches"

verify: checksums notebooks pickles paper-sources paper-numbers theory anonymity
	@echo "All checks passed."

checksums:
	$(PYTHON) tools/verify_checksums.py

notebooks:
	$(PYTHON) tools/check_notebooks.py

pickles:
	$(PYTHON) tools/audit_pickles.py results/04_checkpoints

paper-sources:
	$(PYTHON) tools/check_paper_sources.py

paper-numbers:
	$(PYTHON) tools/verify_paper_numbers.py

theory:
	$(PYTHON) tools/verify_theory_numbers.py

theory-full:
	$(PYTHON) tools/verify_theory_numbers.py --full

anonymity:
	$(PYTHON) tools/scan_anonymity.py $(if $(wildcard $(ANON_TERMS)),--terms-file $(ANON_TERMS),)

reproduce:
	$(PYTHON) tools/run_notebook.py --workdir $(RUN)
	$(PYTHON) tools/compare_runs.py results $(RUN)/*_results_*.zip

reproduce-stages:
	$(PYTHON) tools/run_notebook.py --workdir $(RUN) \
	    --drop-stage e10f_ --drop-stage e10fb_ --drop-stage e10ls_ --drop-stage e10bk_
	$(PYTHON) tools/compare_runs.py results $(RUN)/*_results_*.zip --fig-rtol 0.01 --fig-atol 1e-4

paper:
	cd paper && latexmk -pdf -interaction=nonstopmode main.tex

clean:
	cd paper && latexmk -C > /dev/null 2>&1 || true
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
