#!/usr/bin/env python3
"""Check that the two notebooks in this repository hold exactly the same code (standard library only).

    notebooks/passk-extrapolation-limits.ipynb                      stripped: no outputs, no execution counts
    notebooks/executed/passk-extrapolation-limits.executed.ipynb    the notebook as it was run for the paper, with outputs

The check compares the source of every cell, in order, and the cell types and ids. It also confirms that the
stripped notebook carries no outputs and that the executed one carries outputs.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(REPO, "notebooks", "passk-extrapolation-limits.ipynb")
B = os.path.join(REPO, "notebooks", "executed", "passk-extrapolation-limits.executed.ipynb")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    a, b = load(A)["cells"], load(B)["cells"]
    problems = []
    if len(a) != len(b):
        problems.append(f"cell counts differ: {len(a)} vs {len(b)}")
    for i, (x, y) in enumerate(zip(a, b)):
        if x["cell_type"] != y["cell_type"]:
            problems.append(f"cell {i}: type {x['cell_type']} vs {y['cell_type']}")
        elif "".join(x["source"]) != "".join(y["source"]):
            problems.append(f"cell {i}: source differs")
        if x.get("id") != y.get("id"):
            problems.append(f"cell {i}: id differs")
    out_a = sum(len(c.get("outputs", [])) for c in a if c["cell_type"] == "code")
    out_b = sum(len(c.get("outputs", [])) for c in b if c["cell_type"] == "code")
    if out_a != 0:
        problems.append(f"stripped notebook still has {out_a} outputs")
    if out_b == 0:
        problems.append("executed notebook has no outputs")
    code = sum(1 for c in a if c["cell_type"] == "code")
    print(f"{len(a)} cells ({code} code), stripped outputs: {out_a}, executed outputs: {out_b}")
    for p in problems:
        print("PROBLEM:", p)
    print("OK: identical cell sources" if not problems else "FAILED")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
