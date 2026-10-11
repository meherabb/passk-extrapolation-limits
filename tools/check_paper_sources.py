#!/usr/bin/env python3
"""Lint the LaTeX sources of the paper (standard library only).

    python tools/check_paper_sources.py [--paper paper]

Checks: the ACL style is loaded with the `review` option and the author line is anonymous; every included figure
exists and every figure file is used; every citation key is in the bibliography (and vice versa); every \\ref has a
\\label; the abstract is free of e-mail addresses. It also prints the abstract length and notes whether the link to the
anonymous code mirror still has its placeholder.
"""
import argparse
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strip_comments(tex):
    return re.sub(r"(?<!\\)%.*", "", tex)


def abstract_words(tex):
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if not m:
        return None, ""
    body = m.group(1)
    body = re.sub(r"\\url\{[^}]*\}", " URL ", body)
    body = re.sub(r"\$[^$]*\$", "M", body)   # a formula counts as one word; "pass@$k$" stays one word
    body = re.sub(r"\\[A-Za-z]+\*?(\[[^\]]*\])?", " ", body)
    body = re.sub(r"[{}~\\]", " ", body)
    words = [w for w in body.split() if re.search(r"[A-Za-z0-9]", w)]
    return len(words), m.group(1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--paper", default=os.path.join(REPO, "paper"))
    args = ap.parse_args(argv)
    tex_path = os.path.join(args.paper, "main.tex")
    bib_path = os.path.join(args.paper, "custom.bib")
    tex_raw = open(tex_path, encoding="utf-8").read()
    tex = strip_comments(tex_raw)
    bib = open(bib_path, encoding="utf-8").read()
    problems, notes = [], []

    if not re.search(r"\\usepackage\[review\]\{acl\}", tex):
        problems.append("the ACL style is not loaded with the `review` option")
    if not re.search(r"\\author\{\s*Anonymous", tex):
        problems.append("the author line is not anonymous")
    for f in ("acl.sty", "acl_natbib.bst"):
        if not os.path.isfile(os.path.join(args.paper, f)):
            problems.append(f"{f} is missing from the paper folder")

    inc = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex)
    missing = [p for p in inc if not os.path.isfile(os.path.join(args.paper, p))]
    figdir = os.path.join(args.paper, "figures")
    on_disk = {f"figures/{f}" for f in os.listdir(figdir)} if os.path.isdir(figdir) else set()
    unused = sorted(on_disk - set(inc))
    dups = sorted({p for p in inc if inc.count(p) > 1})
    problems += [f"included figure not found: {p}" for p in missing]
    problems += [f"figure file not used by main.tex: {p}" for p in unused]
    problems += [f"figure included twice: {p}" for p in dups]
    print(f"figures: {len(inc)} included, {len(missing)} missing, {len(unused)} unused")

    cited = set()
    for m in re.finditer(r"\\cite[a-z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}", tex):
        cited.update(k.strip() for k in m.group(1).split(","))
    keys = re.findall(r"@\w+\{([^,\s]+),", bib)
    problems += [f"cited key not in custom.bib: {k}" for k in sorted(cited - set(keys))]
    problems += [f"duplicate bib key: {k}" for k in sorted({k for k in keys if keys.count(k) > 1})]
    uncited = sorted(set(keys) - cited)
    if uncited:
        notes.append(f"{len(uncited)} bib entries are not cited (BibTeX leaves them out): {', '.join(uncited)}")
    print(f"citations: {len(cited)} keys cited, {len(keys)} bib entries")

    labels = re.findall(r"\\label\{([^}]*)\}", tex)
    refs = set()
    for m in re.finditer(r"\\(?:ref|eqref|autoref|cref|Cref|pageref)\{([^}]*)\}", tex):
        refs.update(k.strip() for k in m.group(1).split(","))
    problems += [f"\\ref without \\label: {k}" for k in sorted(refs - set(labels))]
    problems += [f"duplicate \\label: {k}" for k in sorted({k for k in labels if labels.count(k) > 1})]
    unref = sorted(set(labels) - refs)
    if unref:
        notes.append(f"labels never referenced: {', '.join(unref)}")
    print(f"cross-references: {len(labels)} labels, {len(refs)} distinct targets referenced")

    n, abstract = abstract_words(tex_raw)
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", abstract):
        problems.append("the abstract contains an e-mail address")
    print(f"abstract: about {n} words (counting the URL as one word and each formula as one)")
    if re.search(r"anonymous\.4open\.science/r/[^}]*XXXX", tex_raw):
        notes.append("the abstract still has the placeholder XXXX in the link to the anonymous mirror; "
                     "replace it with the four characters the mirror service assigns")

    for t in notes:
        print("NOTE:", t)
    for p in problems:
        print("PROBLEM:", p)
    print("OK" if not problems else f"FAILED ({len(problems)} problem(s))")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
