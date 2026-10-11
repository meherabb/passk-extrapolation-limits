#!/usr/bin/env python3
"""Strip outputs, execution counts and run-specific cell metadata from a Jupyter notebook (standard library only).

    python tools/strip_notebook.py notebooks/executed/passk-extrapolation-limits.executed.ipynb \
           notebooks/passk-extrapolation-limits.ipynb

The source of every cell is copied unchanged. Only these things are removed:
  * outputs and execution_count of code cells,
  * per-cell metadata (execution timestamps, trust flags),
  * notebook metadata other than the kernel specification and the language name.
`tools/check_notebooks.py` verifies that the two notebooks in this repository have identical cell sources.
"""
import json
import sys


def strip(nb):
    out = {"cells": [], "metadata": {}, "nbformat": nb["nbformat"], "nbformat_minor": nb["nbformat_minor"]}
    ks = nb.get("metadata", {}).get("kernelspec")
    if ks:
        out["metadata"]["kernelspec"] = {k: ks[k] for k in ("display_name", "language", "name") if k in ks}
    li = nb.get("metadata", {}).get("language_info")
    if li and "name" in li:
        out["metadata"]["language_info"] = {"name": li["name"]}
    for cell in nb["cells"]:
        c = {"cell_type": cell["cell_type"], "id": cell.get("id"), "metadata": {}, "source": cell["source"]}
        if c["id"] is None:
            del c["id"]
        if cell["cell_type"] == "code":
            c["execution_count"] = None
            c["outputs"] = []
        out["cells"].append(c)
    return out


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        nb = json.load(fh)
    text = json.dumps(strip(nb), sort_keys=True, indent=1, separators=(",", ": "), ensure_ascii=False) + "\n"
    with open(argv[2], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"wrote {argv[2]} ({len(text) / 1024:.0f} KiB, {len(nb['cells'])} cells)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
