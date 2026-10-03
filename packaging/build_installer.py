"""One-shot Windows build: PyInstaller, portable zip, Inno Setup installer.

    python packaging/fetch_tectonic.py --warm     # tectonic + offline cache
    python packaging/build_installer.py           # this script
    python packaging/build_installer.py --skip-freeze

Produces, in ``dist/``:

* ``Setup_KherveTeX_<ver>.exe`` — the installer (``<ver>`` = ``__version__``)
* ``KherveTeX-Setup.exe``       — stable-name copy the website links to
* ``KherveTeX_<ver>.zip``       — portable build; its root is ``KherveTeX/``
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_DIST = _ROOT / "dist"
_APP = "KherveTeX"


def _find_iscc() -> Path:
    if os.environ.get("KHERVETEX_ISCC"):
        return Path(os.environ["KHERVETEX_ISCC"])
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Inno Setup 6" / "ISCC.exe",
    ]
    found = next((c for c in candidates if c.is_file()), None)
    if found is None and shutil.which("iscc"):
        found = Path(shutil.which("iscc"))
    return found or candidates[0]


def _run(cmd, **kwargs):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kwargs)


def app_version() -> str:
    sys.path.insert(0, str(_ROOT))
    from khervedoc import __version__
    return __version__


def build_zip(version: str) -> Path:
    out = _DIST / f"{_APP}_{version}.zip"
    out.unlink(missing_ok=True)
    root = _DIST / _APP
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, Path(_APP) / path.relative_to(root))
    return out


def build_installer(version: str) -> Path:
    iscc = _find_iscc()
    if not iscc.is_file():
        raise SystemExit(f"Inno Setup not found at {iscc} (or set KHERVETEX_ISCC)")
    _run([iscc, f"/DMyAppVersion={version}", _ROOT / "KherveTeX_setup.iss"], cwd=_ROOT)
    out = _DIST / f"Setup_{_APP}_{version}.exe"
    if not out.is_file():
        raise SystemExit(f"installer not produced: {out}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-freeze", action="store_true")
    args = parser.parse_args()
    if sys.platform != "win32":
        raise SystemExit("build_installer.py only runs on Windows (macOS: build_macos.py)")
    version = app_version()
    print(f"{_APP} {version}", flush=True)
    if not args.skip_freeze:
        _run([sys.executable, "-m", "PyInstaller", "KherveTeX.spec", "--noconfirm"], cwd=_ROOT)
    if not (_DIST / _APP / f"{_APP}.exe").is_file():
        raise SystemExit("dist/KherveTeX/KherveTeX.exe not found")
    zip_path = build_zip(version)
    exe_path = build_installer(version)
    stable = _DIST / f"{_APP}-Setup.exe"
    shutil.copy2(exe_path, stable)
    print()
    for path in (exe_path, zip_path, stable):
        print(f"{path.name:<36} {path.stat().st_size / 1e6:>7.1f} MB")


if __name__ == "__main__":
    main()
