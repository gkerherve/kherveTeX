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
"""

import argparse
import io
import os
import platform
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


def warm(tectonic: Path) -> None:
    os.environ["PATH"] = str(tectonic.parent) + os.pathsep + os.environ["PATH"]
    sys.path.insert(0, str(_ROOT))
    from khervedoc import compiler, examples
    from khervedoc.serializer import serialize_document
    found = compiler._find_tectonic()
    assert found and os.path.normcase(found) == os.path.normcase(str(tectonic)), found

    ok, _log = compiler.download_tectonic_bundle(
        on_output=lambda line: print("  " + line, flush=True))
    print(f"kitchen-sink bundle: {'ok' if ok else 'FAILED'}", flush=True)
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        for label, factory in examples.EXAMPLES:
            res = compiler.compile_tex(serialize_document(factory()),
                                       Path(tmp) / "ex",
                                       source_dir=_ROOT / "khervedoc" / "styles")
            print(f"  example {label!r}: {'ok' if res.ok else 'FAILED'}", flush=True)
            if not res.ok:
                failed.append(label)
    cache = compiler.query_tectonic_cache_dir(str(tectonic))
    if cache is None or not cache.is_dir():
        raise SystemExit(f"tectonic reported no cache directory ({cache})")
    shutil.rmtree(_CACHE, ignore_errors=True)
    shutil.copytree(cache, _CACHE)
    size = sum(p.stat().st_size for p in _CACHE.rglob("*") if p.is_file())
    print(f"cache {cache} -> {_CACHE} ({size / 1e6:.0f} MB)", flush=True)
    if failed:
        print(f"WARNING: examples that did not compile: {failed}", flush=True)


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
