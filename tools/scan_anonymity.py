#!/usr/bin/env python3
"""Scan a directory tree (or single files) for anything that could identify the authors.

Purpose
-------
Double-blind review requires that nothing in the released material reveals who wrote it. This script looks for the
usual leaks in a repository: personal strings you supply, e-mail addresses, absolute user paths, hosting URLs that
carry an account name, access tokens, and document metadata (PDF, PNG, Jupyter, zip/npz members).

It reads every file as bytes, so it also finds strings inside pickles. Archives (.zip, .npz, .gz) are opened.

Usage
-----
    python tools/scan_anonymity.py                       # scan the repository, generic checks only
    python tools/scan_anonymity.py --terms-file .anonymity-terms
    python tools/scan_anonymity.py --term "first last" --term myusername path/to/dir

`--terms-file` holds one string per line (names, user names, e-mail, institution, project nicknames). Lines starting
with # are ignored. Keep that file out of the repository (it is listed in .gitignore).

Exit status: 0 if nothing was found, 1 if at least one finding, 2 on a usage error.
Standard library only; if `pypdf` is installed, the text of PDF pages is searched as well.
"""
import argparse
import gzip
import io
import os
import re
import struct
import sys
import zipfile
import zlib
from collections import Counter, defaultdict

SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints", "node_modules", ".venv", "venv", "runs"}
MAX_MEMBER_BYTES = 200 * 1024 * 1024
CONTEXT = 70

# ----------------------------------------------------------------------------------------------------------------
# Generic patterns (bytes).  category -> compiled regex
GENERIC = {
    "email": re.compile(rb"(?<![A-Za-z0-9._%+-])(?!pass@)(?!Pass@)[A-Za-z0-9._%+-]{2,}@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,24}(?![A-Za-z0-9])"),
    "user path": re.compile(rb"(?:/home/[A-Za-z0-9._-]+|/Users/[A-Za-z0-9._ -]+|/root/\.[A-Za-z]+|C:\\\\?Users\\\\?[A-Za-z0-9._ -]+)"),
    # (written in pieces, so that this file does not match its own rules)
    "kaggle/colab/drive path": re.compile(rb"(?:/kag" rb"gle/input/[^\s\"'\\)]*|/con" rb"tent/drive[^\s\"'\\)]*|My" rb"Drive[^\s\"'\\)]*)"),
    "account-bearing URL": re.compile(
        rb"https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org|kaggle\.com|huggingface\.co|gist\.github\.com|"
        rb"colab\.research\.google\.com/drive|drive\.google\.com|docs\.google\.com|overleaf\.com/(?:project|read)|"
        rb"wandb\.ai|osf\.io|zenodo\.org/records?|figshare\.com)/[^\s\"'<>\\)]+"),
    "access token": re.compile(
        rb"(?:hf_[A-Za-z0-9]{30,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|gho_[A-Za-z0-9]{30,}|"
        rb"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{32,}|xox[abp]-[A-Za-z0-9-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
        rb"\"key\"\s*:\s*\"[0-9a-f]{32}\")"),
    "kaggle credentials": re.compile(rb"\"username\"\s*:\s*\"[^\"]+\"\s*,\s*\"key\""),
}

# Public third-party URLs that occur in the repository and are not leaks (matched case-insensitively against the
# URL without scheme and without "www.").  Everything else that points at an account, repository, drive or project
# is reported.
URL_ALLOW = (
    "github.com/acl-org/",                          # ACL style files: header of paper/acl.sty, paper/README.md
    "github.com/tdurieux/anonymous_github",         # Anonymous GitHub, mentioned in the documentation
    "github.com/explosion/spacy-models/",           # the next four are pins inside results/05_environment/pip_freeze.txt
    "github.com/googlecolab/",
    "github.com/kaggle/learntools",
    "github.com/facebookresearch/segment-anything",
    "huggingface.co/datasets/huggingfaceh4/math-500",   # MATH-500 test split downloaded by the notebook
    "huggingface.co/datasets/{",                        # f-string in the notebook: the Monkey Business repository id is a variable
    "huggingface.co/datasets/scalingintelligence/monkey_business",
)

# Defaults written into the notebook (optional Google Drive mount, Kaggle input glob); they name no person.
BENIGN_PATH = re.compile(rb"^(?:/con" rb"tent/drive(?:/My" rb"Drive/passk_extrapolation(?:/outputs)?)?|/kag" rb"gle/input/\*)")


def _decode(b):
    return b.decode("utf-8", "replace")


class Scanner:
    def __init__(self, terms, allow_urls=(), allow_regex=None, verbose=False):
        self.terms = []
        for t in terms:
            t = t.strip()
            if not t or t.startswith("#"):
                continue
            self.terms.append(t)
        self.term_res = []
        for t in self.terms:
            tl = t.lower()
            variants = {tl}
            squeezed = re.sub(r"[^a-z0-9]+", "", tl)
            if len(squeezed) >= 6:
                variants.add(squeezed)
                # allow separators (space, dot, underscore, dash) between the letters of a long term
            pats = [re.escape(v.encode()) for v in variants]
            if len(squeezed) >= 6 and squeezed != tl:
                pats.append(rb"[\s._-]*".join(re.escape(ch.encode()) for ch in squeezed))
            self.term_res.append((t, re.compile(b"|".join(pats), re.IGNORECASE)))
        self.allow_urls = tuple(u.lower() for u in URL_ALLOW + tuple(allow_urls))
        self.allow_regex = re.compile(allow_regex.encode()) if allow_regex else None
        self.findings = []        # (category, location, detail)
        self.files_scanned = 0
        self.members_scanned = 0
        self.verbose = verbose

    # ------------------------------------------------------------------ helpers
    def add(self, cat, loc, detail):
        self.findings.append((cat, loc, detail))

    def _ctx(self, data, m):
        s = max(0, m.start() - CONTEXT)
        e = min(len(data), m.end() + CONTEXT)
        return _decode(data[s:e]).replace("\n", " ").replace("\r", " ")

    def scan_text_bytes(self, data, loc):
        """Run the user terms and the generic patterns over a byte string."""
        for term, rx in self.term_res:
            for m in rx.finditer(data):
                self.add("personal term", loc, f"{term!r}: ...{self._ctx(data, m)}...")
                break  # one example per term per location is enough
        for cat, rx in GENERIC.items():
            seen = set()
            for m in rx.finditer(data):
                hit = m.group(0)
                if self.allow_regex and self.allow_regex.search(hit):
                    continue
                if cat == "kaggle/colab/drive path" and BENIGN_PATH.match(hit):
                    continue
                if cat == "account-bearing URL":
                    low = _decode(hit).lower().rstrip(".,;:)")
                    low_noscheme = low.split("://", 1)[1]
                    low_noscheme = low_noscheme[4:] if low_noscheme.startswith("www.") else low_noscheme
                    if low_noscheme.startswith(self.allow_urls):
                        continue
                if hit in seen:
                    continue
                seen.add(hit)
                self.add(cat, loc, _decode(hit)[:200])
                if len(seen) >= 5:
                    break

    # ------------------------------------------------------------------ container formats
    def scan_png(self, data, loc):
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return
        pos = 8
        while pos + 8 <= len(data):
            ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
            body = data[pos + 8:pos + 8 + ln]
            pos += 12 + ln
            if typ == b"tEXt":
                self.scan_text_bytes(body, f"{loc} [PNG tEXt]")
            elif typ == b"zTXt":
                try:
                    k, rest = body.split(b"\x00", 1)
                    self.scan_text_bytes(k + b"=" + zlib.decompress(rest[1:]), f"{loc} [PNG zTXt]")
                except Exception:
                    pass
            elif typ == b"iTXt":
                self.scan_text_bytes(body, f"{loc} [PNG iTXt]")
            elif typ in (b"eXIf", b"tIME"):
                self.add("image metadata", loc, f"PNG chunk {typ.decode()} present")
            if typ == b"IEND":
                break

    def scan_pdf(self, data, loc):
        if not data.startswith(b"%PDF"):
            return
        # Information dictionary entries and XMP are stored uncompressed in matplotlib / LaTeX output
        for key in (b"Author", b"Creator", b"Producer", b"Title", b"Subject", b"Keywords", b"Company"):
            for m in re.finditer(rb"/" + key + rb"\s*(\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>)", data):
                val = m.group(1)
                if key == b"Author" and val not in (b"()", b"<>"):
                    self.add("pdf metadata", loc, f"/Author {_decode(val)[:120]}")
                elif self.verbose:
                    print(f"    [info] {loc} /{key.decode()} {_decode(val)[:100]}")
                self.scan_text_bytes(val, f"{loc} [PDF /{key.decode()}]")
        for m in re.finditer(rb"<x:xmpmeta.*?</x:xmpmeta>", data, re.S):
            self.scan_text_bytes(m.group(0), f"{loc} [PDF XMP]")
        try:  # optional: text drawn on the pages (figure titles, axis labels, stamps)
            import pypdf  # type: ignore
            reader = pypdf.PdfReader(io.BytesIO(data))
            meta = reader.metadata or {}
            for k, v in dict(meta).items():
                self.scan_text_bytes(f"{k}={v}".encode("utf-8", "replace"), f"{loc} [PDF metadata]")
            for i, page in enumerate(reader.pages):
                self.scan_text_bytes(page.extract_text().encode("utf-8", "replace"), f"{loc} [PDF text p.{i + 1}]")
        except ImportError:
            pass
        except Exception as exc:  # corrupt or exotic PDF
            self.add("scan error", loc, f"pypdf could not read the PDF: {type(exc).__name__}")

    def scan_zip_like(self, data, loc, depth=0):
        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            return False
        for info in zf.infolist():
            name = f"{loc}::{info.filename}"
            self.scan_text_bytes(info.filename.encode("utf-8", "replace"), f"{name} [member name]")
            if info.is_dir():
                continue
            if info.file_size > MAX_MEMBER_BYTES:
                self.add("scan error", name, "member too large to scan")
                continue
            self.members_scanned += 1
            self.scan_blob(zf.read(info), name, depth + 1)
        return True

    def scan_blob(self, data, loc, depth=0):
        low = loc.lower()
        if depth < 3 and (data[:4] == b"PK\x03\x04") and self.scan_zip_like(data, loc, depth):
            return
        if data[:2] == b"\x1f\x8b" and depth < 3:
            try:
                self.scan_blob(gzip.decompress(data), loc + "[gunzip]", depth + 1)
                return
            except Exception:
                pass
        if data.startswith(b"\x89PNG"):
            self.scan_png(data, loc)
        elif data.startswith(b"%PDF"):
            self.scan_pdf(data, loc)
        self.scan_text_bytes(data, loc)

    # ------------------------------------------------------------------ walking
    def scan_path(self, root):
        root = os.path.abspath(root)
        if os.path.isfile(root):
            self._scan_file(root, os.path.basename(root))
            return
        for dp, dns, fns in os.walk(root):
            dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
            for d in dns:
                self.scan_text_bytes(d.encode("utf-8", "replace"), os.path.relpath(os.path.join(dp, d), root) + "/ [dir name]")
            for fn in sorted(fns):
                full = os.path.join(dp, fn)
                self._scan_file(full, os.path.relpath(full, root))

    def _scan_file(self, full, rel):
        if os.path.islink(full):
            self.add("symlink", rel, os.readlink(full))
            return
        self.scan_text_bytes(os.path.basename(rel).encode("utf-8", "replace"), f"{rel} [file name]")
        try:
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            self.add("scan error", rel, f"unreadable: {exc}")
            return
        self.files_scanned += 1
        self.scan_blob(data, rel)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="*", help="directories or files to scan (default: the repository root)")
    ap.add_argument("--term", action="append", default=[], help="a string that must not occur (repeatable)")
    ap.add_argument("--terms-file", help="file with one forbidden string per line")
    ap.add_argument("--allow-url-prefix", action="append", default=[],
                    help="host/owner prefix of a public third-party URL to accept, e.g. github.com/some-org/")
    ap.add_argument("--allow-regex", help="ignore generic hits matching this regular expression")
    ap.add_argument("--max-print", type=int, default=60, help="maximum findings to print (default 60)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    terms = list(args.term)
    if args.terms_file:
        try:
            with open(args.terms_file, encoding="utf-8") as fh:
                terms += [ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
        except OSError as exc:
            print(f"cannot read --terms-file: {exc}", file=sys.stderr)
            return 2
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = args.paths or [default_root]

    sc = Scanner(terms, allow_urls=args.allow_url_prefix, allow_regex=args.allow_regex, verbose=args.verbose)
    for p in paths:
        if not os.path.exists(p):
            print(f"no such path: {p}", file=sys.stderr)
            return 2
        sc.scan_path(p)

    print(f"scanned {sc.files_scanned} files and {sc.members_scanned} archive members; "
          f"{len(terms)} personal term(s) supplied" + ("" if terms else " (none: only the generic checks ran)"))
    if not sc.findings:
        print("OK: no findings.")
        return 0
    by_cat = Counter(c for c, _, _ in sc.findings)
    print("FINDINGS:", ", ".join(f"{k}: {v}" for k, v in sorted(by_cat.items())))
    for cat, loc, detail in sc.findings[:args.max_print]:
        print(f"  [{cat}] {loc}\n      {detail}")
    if len(sc.findings) > args.max_print:
        print(f"  ... {len(sc.findings) - args.max_print} more (use --max-print)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
