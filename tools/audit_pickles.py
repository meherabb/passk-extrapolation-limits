#!/usr/bin/env python3
"""Audit pickle files without loading their contents.

For every .pkl file this script lists the classes and functions the file would import when unpickled (module.name).
It uses an Unpickler whose find_class() never imports anything: it records the request and returns an inert stub, so
no code from the file is executed. Anything outside the allow-list below is reported and the exit status is 1.

    python tools/audit_pickles.py results/04_checkpoints
"""
import os
import pickle
import sys
from collections import Counter

ALLOWED_EXACT = {
    "builtins.slice", "builtins.set", "builtins.frozenset", "builtins.complex", "builtins.range", "builtins.bytearray",
    "builtins.object", "builtins.int", "builtins.float", "builtins.str", "builtins.bool", "builtins.tuple",
    "builtins.list", "builtins.dict", "builtins.bytes",
    "collections.OrderedDict", "collections.defaultdict", "collections.deque", "collections.Counter",
    "copyreg._reconstructor", "copyreg.__newobj__", "_codecs.encode", "datetime.datetime", "datetime.date",
    "datetime.timedelta", "fractions.Fraction", "decimal.Decimal",
}
ALLOWED_PREFIX = ("numpy.", "pandas.", "scipy.", "mpmath.")
FORBIDDEN_FRAGMENTS = ("eval", "exec", "compile", "system", "popen", "subprocess", "__import__", "open", "getattr",
                       "setattr", "pty", "socket", "shutil", "importlib")


class _Stub:
    def __init__(self, *a, **k):
        pass

    def __call__(self, *a, **k):
        return _Stub()

    def __setstate__(self, state):
        pass

    def __reduce__(self):
        return (_Stub, ())


class _Recorder(pickle.Unpickler):
    def __init__(self, fh):
        super().__init__(fh)
        self.requested = Counter()

    def find_class(self, module, name):
        self.requested[f"{module}.{name}"] += 1
        return type(name, (_Stub,), {})

    def persistent_load(self, pid):
        raise pickle.UnpicklingError("persistent id present")


def audit(path):
    with open(path, "rb") as fh:
        rec = _Recorder(fh)
        try:
            rec.load()
        except Exception as exc:  # the stubs cannot rebuild real arrays; only the requested names matter
            if not rec.requested:
                return rec.requested, f"{type(exc).__name__}: {exc}"
    return rec.requested, None


def classify(name):
    low = name.lower()
    if any(f in low.split(".")[-1] for f in FORBIDDEN_FRAGMENTS) or low.startswith(("os.", "posix.", "nt.", "subprocess.", "sys.")):
        return False
    return name in ALLOWED_EXACT or name.startswith(ALLOWED_PREFIX)


def main(root):
    total, problems, seen = 0, [], Counter()
    for dp, _d, fns in os.walk(root):
        for fn in sorted(fns):
            if not fn.endswith((".pkl", ".pickle")):
                continue
            p = os.path.join(dp, fn)
            total += 1
            names, err = audit(p)
            if err:
                problems.append((os.path.relpath(p, root), "unreadable: " + err))
            for n, c in names.items():
                seen[n] += c
                if not classify(n):
                    problems.append((os.path.relpath(p, root), f"not on the allow-list: {n}"))
    print(f"{total} pickle files audited; globals requested (module.name: count over all files):")
    for n, c in sorted(seen.items()):
        print(f"  {c:6d}  {n}")
    if problems:
        print("PROBLEMS:")
        for rel, why in problems[:50]:
            print(f"  {rel}: {why}")
        return 1
    print("OK: every pickle asks only for numpy / pandas / scipy / mpmath / builtin container types.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
