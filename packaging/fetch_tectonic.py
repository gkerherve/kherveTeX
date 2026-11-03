"""Fetch the tectonic engine that ships inside KherveTeX, and warm its cache.

    python packaging/fetch_tectonic.py            # binary -> packaging/bin/
    python packaging/fetch_tectonic.py --warm     # + khervedoc/tectonic_cache/

The binary is the official release build for this machine (Windows x86_64
msvc, macOS arm64 / x86_64); PyInstaller cannot cross-compile, so neither
can this. ``--warm`` compiles tectonic's kitchen-sink documents
(``compiler.download_tectonic_bundle``) and every starter example, then
copies the resulting bundle cache to ``khervedoc/tectonic_cache``, which the
spec bundles and ``__main__._seed_tectonic_cache`` copies to the user's
cache on first launch, so the templates compile offline.

The warm-up runs on an empty cache of its own, so the bundle holds exactly
what the examples need, whatever the build machine compiled before; then it
compiles every example again with ``--only-cached`` from a fresh copy, as a
new PC would, and stops if one fails. A stamp records which examples it was
made for: the spec warms again when they change.
"""

import argparse
import hashlib
import io
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

TECTONIC_VERSION = "0.17.0"
_ROOT = Path(__file__).resolve().parent.parent
_BIN = _ROOT / "packaging" / "bin"
_CACHE = _ROOT / "khervedoc" / "tectonic_cache"
_STAMP = _ROOT / "khervedoc" / "tectonic_cache.stamp"


def _target() -> tuple[str, str]:
    machine = platform.machine().lower()
    if sys.platform == "win32":
        return "x86_64-pc-windows-msvc", "zip"
    if sys.platform == "darwin":
        arch = "aarch64" if machine in ("arm64", "aarch64") else "x86_64"
        return f"{arch}-apple-darwin", "tar.gz"
    return "x86_64-unknown-linux-musl", "tar.gz"


def fetch() -> Path:
    triple, ext = _target()
    name = f"tectonic-{TECTONIC_VERSION}-{triple}.{ext}"
    url = ("https://github.com/tectonic-typesetting/tectonic/releases/download/"
           f"tectonic%40{TECTONIC_VERSION}/{name}")
    exe_name = "tectonic.exe" if sys.platform == "win32" else "tectonic"
    have = _BIN / exe_name
    if have.is_file():
        try:
            v = subprocess.run([str(have), "--version"], capture_output=True,
                               text=True, timeout=30).stdout
        except OSError:
            v = ""
        if TECTONIC_VERSION in v:
            return have
    print(f"Downloading {url}", flush=True)
    data = urllib.request.urlopen(url, timeout=120).read()
    _BIN.mkdir(parents=True, exist_ok=True)
    out = _BIN / exe_name
    if ext == "zip":
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            member = next(n for n in zf.namelist() if n.endswith(exe_name))
            out.write_bytes(zf.read(member))
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
            member = next(m for m in tf.getmembers()
                          if m.isfile() and m.name.endswith(exe_name))
            out.write_bytes(tf.extractfile(member).read())
    out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"tectonic {TECTONIC_VERSION} -> {out} "
          f"({out.stat().st_size / 1e6:.1f} MB)", flush=True)
    return out


def _examples():
    sys.path.insert(0, str(_ROOT))
    from khervedoc import examples
    from khervedoc.serializer import serialize_document
    return [(label, serialize_document(factory()))
            for label, factory in examples.EXAMPLES
            if factory is not examples.blank]


def fingerprint() -> str:
    """What the cache must cover: the tectonic version, the kitchen-sink
    documents and every example's preamble (with dates and numbers taken
    out, so a planner's date does not count as a change)."""
    import inspect
    from khervedoc import compiler
    h = hashlib.sha256(TECTONIC_VERSION.encode())
    h.update(inspect.getsource(compiler.download_tectonic_bundle).encode())
    for label, tex in _examples():
        preamble = tex.split("\\begin{document}")[0]
        h.update(label.encode() + re.sub(r"\d", "", preamble).encode())
    return h.hexdigest()


def is_current() -> bool:
    """The bundled cache exists and was warmed for today's examples."""
    return (_CACHE.is_dir() and any(_CACHE.rglob("*.otf"))
            and _STAMP.is_file()
            and _STAMP.read_text().strip() == fingerprint())


def verify_offline(tectonic: Path) -> list[str]:
    """Every example compiled with --only-cached from a fresh copy of the
    bundled cache, as on a new PC: the labels that fail."""
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "cache"
        shutil.copytree(_CACHE, cache)
        env = dict(os.environ, TECTONIC_CACHE_DIR=str(cache),
                   TEXINPUTS=str(_ROOT / "khervedoc" / "styles") + os.pathsep)
        for n, (label, tex) in enumerate(_examples()):
            work = Path(tmp) / f"ex{n}"
            work.mkdir()
            (work / "d.tex").write_text(tex, encoding="utf-8")
            proc = subprocess.run(
                [str(tectonic), "--only-cached", "-Z", "continue-on-errors",
                 "d.tex"], cwd=work, env=env, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=300)
            ok = proc.returncode == 0 and (work / "d.pdf").is_file()
            print(f"  offline {label!r}: {'ok' if ok else 'FAILED'}", flush=True)
            if not ok:
                failed.append(label)
    return failed


def warm(tectonic: Path) -> None:
    os.environ["PATH"] = str(tectonic.parent) + os.pathsep + os.environ["PATH"]
    sys.path.insert(0, str(_ROOT))
    from khervedoc import compiler
    found = compiler._find_tectonic()
    assert found and os.path.normcase(found) == os.path.normcase(str(tectonic)), found

    with tempfile.TemporaryDirectory() as tmp:
        # An empty cache of its own: the bundle is what the examples need,
        # not whatever this machine's cache happens to hold.
        cache = Path(tmp) / "cache"
        os.environ["TECTONIC_CACHE_DIR"] = str(cache)
        ok, _log = compiler.download_tectonic_bundle(
            on_output=lambda line: print("  " + line, flush=True))
        print(f"kitchen-sink bundle: {'ok' if ok else 'FAILED'}", flush=True)
        failed = [] if ok else ["kitchen-sink bundle"]
        for label, tex in _examples():
            res = compiler.compile_tex(tex, Path(tmp) / "ex",
                                       source_dir=_ROOT / "khervedoc" / "styles")
            print(f"  example {label!r}: {'ok' if res.ok else 'FAILED'}", flush=True)
            if not res.ok:
                failed.append(label)
        del os.environ["TECTONIC_CACHE_DIR"]
        if failed:
            raise SystemExit(f"these did not compile while warming: {failed}")
        shutil.rmtree(_CACHE, ignore_errors=True)
        shutil.copytree(cache, _CACHE)
    size = sum(p.stat().st_size for p in _CACHE.rglob("*") if p.is_file())
    print(f"cache -> {_CACHE} ({size / 1e6:.0f} MB)", flush=True)
    failed = verify_offline(tectonic)
    if failed:
        raise SystemExit(f"these do not compile offline from the cache: {failed}")
    _STAMP.write_text(fingerprint())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--warm", action="store_true",
                    help="also build khervedoc/tectonic_cache")
    args = ap.parse_args()
    exe = fetch()
    if args.warm:
        warm(exe)


if __name__ == "__main__":
    main()
