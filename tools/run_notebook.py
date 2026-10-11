#!/usr/bin/env python3
"""Run the analysis notebook headlessly, without a GPU and without network access.

The notebook is executed in analysis-only mode: nothing is sampled, and every analysis stage whose cache file is
present in the shipped checkpoints is loaded instead of recomputed. All output goes to a fresh working directory, so
the repository itself is never modified.

Examples
--------
    # fast path: reuse every cached stage (regenerates all figures, tables and the master archive)
    python tools/run_notebook.py

    # recompute the last 31 stages of the final run (E10 floor, bootstrap and likelihood-ratio simulation)
    python tools/run_notebook.py --drop-stage e10f_ --drop-stage e10fb_ --drop-stage e10ls_ --drop-stage e10bk_

    # recompute everything that is not raw data (very long; not timed by the authors)
    python tools/run_notebook.py --drop-all-caches

Afterwards compare the new archive with the shipped results:

    python tools/compare_runs.py results runs/<workdir>/DoublingBarrier-QuadraticHorizon_passk-extrapolation_results_local_*.zip

Requirements: numpy, scipy, pandas, matplotlib, mpmath (versions in requirements.txt) and, for this script,
nbclient, nbformat and ipykernel (requirements-dev.txt).
"""
import argparse
import datetime
import os
import shutil
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_NB = os.path.join(REPO, "notebooks", "passk-extrapolation-limits.ipynb")
DEFAULT_RESULTS = os.path.join(REPO, "results")


def build_resume_source(results_dir, dst, drop_prefixes, drop_all):
    """Copy 04_checkpoints into dst/04_checkpoints, leaving out the stages that must be recomputed."""
    src = os.path.join(results_dir, "04_checkpoints")
    if not os.path.isdir(src):
        raise SystemExit(f"{src} not found: pass --results pointing at the results folder")
    out = os.path.join(dst, "04_checkpoints")
    kept = dropped = 0
    for root, _dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        for fn in files:
            top = rel_root.split(os.sep)[0]
            is_cache = fn.endswith(".pkl")
            drop = is_cache and (drop_all or any(fn.startswith(p) for p in drop_prefixes))
            # the problem lists (gsm8k_subset, math500_order) are inputs, not analysis stages
            if drop and fn.startswith(("gsm8k_subset", "math500_order")):
                drop = False
            if drop:
                dropped += 1
                continue
            target = os.path.join(out, "" if rel_root == "." else rel_root)
            os.makedirs(target, exist_ok=True)
            shutil.copy2(os.path.join(root, fn), os.path.join(target, fn))
            kept += 1
    return kept, dropped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--notebook", default=DEFAULT_NB)
    ap.add_argument("--results", default=DEFAULT_RESULTS, help="folder holding 04_checkpoints/ (default: results/)")
    ap.add_argument("--workdir", help="new, empty folder for the run (default: runs/analysis-<timestamp>)")
    ap.add_argument("--drop-stage", action="append", default=[], metavar="PREFIX",
                    help="do not restore cache files whose name starts with PREFIX, so the stage is recomputed (repeatable)")
    ap.add_argument("--drop-all-caches", action="store_true", help="do not restore any analysis cache (*.pkl)")
    ap.add_argument("--timeout", type=int, default=-1, help="per-cell timeout in seconds (default: none)")
    ap.add_argument("--no-mb", action="store_true", help="skip the Monkey Business analysis (PASSK_MB=0)")
    args = ap.parse_args(argv)

    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError:
        raise SystemExit("this script needs nbclient, nbformat and ipykernel: pip install -r requirements-dev.txt")

    nb_path = os.path.abspath(args.notebook)
    results = os.path.abspath(args.results)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    work = os.path.abspath(args.workdir or os.path.join(REPO, "runs", f"analysis-{stamp}"))
    if os.path.exists(work) and os.listdir(work):
        raise SystemExit(f"{work} exists and is not empty")
    os.makedirs(work, exist_ok=True)

    resume = os.path.join(work, "_resume_source")
    kept, dropped = build_resume_source(results, resume, args.drop_stage, args.drop_all_caches)
    print(f"[run] resume source: {kept} checkpoint files kept, {dropped} analysis caches withheld")

    env = {
        "PASSK_MODE": "analyze",
        "PASSK_RESUME_FROM": resume,
        "PASSK_MB": "0" if args.no_mb else "1",
        "MPLBACKEND": "Agg",
        "PYTHONHASHSEED": "20261005",
        "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS", ""),
    }
    env = {k: v for k, v in env.items() if v != ""}
    os.environ.update(env)
    # make sure the kernel is started with the interpreter that runs this script
    os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")

    nb = nbformat.read(nb_path, as_version=4)
    t0 = time.time()
    state = {"last": t0}
    log = open(os.path.join(work, "run_log.txt"), "w", buffering=1)

    def say(msg):
        line = f"[{time.time() - t0:7.1f}s] {msg}"
        print(line, flush=True)
        log.write(line + "\n")

    def on_start(cell, cell_index, **_):
        state["last"] = time.time()
        if cell.cell_type == "code":
            first = (cell.source.strip().splitlines() or [""])[0][:90]
            say(f"cell {cell_index:2d} start: {first}")

    def on_done(cell, cell_index, execute_reply=None, **_):
        if cell.cell_type == "code":
            say(f"cell {cell_index:2d} done in {time.time() - state['last']:.1f}s")

    client = NotebookClient(nb, timeout=None if args.timeout < 0 else args.timeout, kernel_name="python3",
                            resources={"metadata": {"path": work}}, allow_errors=False, interrupt_on_timeout=False)
    client.on_cell_start = on_start
    client.on_cell_executed = on_done
    say(f"executing {os.path.relpath(nb_path, REPO)} in {work}")
    try:
        client.execute()
    finally:
        out_nb = os.path.join(work, "executed.ipynb")
        nbformat.write(nb, out_nb)
        say(f"executed notebook written to {out_nb}")
    zips = sorted(f for f in os.listdir(work) if f.endswith(".zip") and "_results_" in f)
    say("finished in %.1f min; master archive: %s" % ((time.time() - t0) / 60, zips[-1] if zips else "NOT FOUND"))
    return 0 if zips else 1


if __name__ == "__main__":
    sys.exit(main())
