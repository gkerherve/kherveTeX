"""Smoke-test a frozen KherveTeX: start it, drive it over MCP, compile.

    python packaging/smoke_test.py dist/KherveTeX/KherveTeX.exe
    python packaging/smoke_test.py dist/KherveTeX.app/Contents/MacOS/KherveTeX

A freeze fails quietly: a module PyInstaller missed only shows up when the
code that imports it runs. So this:

* runs the bundled tectonic binary (``--version``);
* turns the in-app MCP bridge on in the app's QSettings (needs PySide6 in
  the interpreter running this script — the build environment has it);
* starts the real executable on Qt's offscreen platform and waits for the
  bridge's endpoint file;
* speaks MCP to it through ``<exe> --mcp-server`` (the path Claude takes):
  ``get_document_info``, then ``compile_document`` on the starter
  document, which must succeed with at least one page — i.e. the bundled
  tectonic, the serializer and PyMuPDF all work inside the freeze;
* runs the app on an EMPTY tectonic cache (a brand-new PC) and checks it
  seeds the bundled packages, then compiles every example and a 12 pt
  two-column document with \\url using ``--only-cached`` — no network —
  so a package or font missing from the bundle fails the build instead
  of failing on a user's machine.

Meant for CI runners: it changes the app's settings (MCP on, Full access).
Exits non-zero on the first failure.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from khervedoc.mcp_server import endpoint_path  # noqa: E402  (no Qt import)


_CHILDREN = []


def _fail(message: str):
    print(f"SMOKE TEST FAILED: {message}", flush=True)
    for proc in _CHILDREN:
        try:
            proc.kill()
        except Exception:
            pass
    os._exit(1)


class Mcp:
    def __init__(self, exe: str, env: dict):
        self.proc = subprocess.Popen([exe, "--mcp-server"], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     env=env)
        _CHILDREN.append(self.proc)
        self._id = 0

    def _send(self, msg: dict):
        self.proc.stdin.write((json.dumps(msg) + "\n").encode())
        self.proc.stdin.flush()

    def notify(self, method: str):
        self._send({"jsonrpc": "2.0", "method": method})

    def request(self, method: str, params: dict = None) -> dict:
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": method,
                    "params": params or {}})
        while True:
            line = self.proc.stdout.readline()
            if not line:
                _fail(f"the MCP server closed while waiting for {method}")
            reply = json.loads(line)
            if reply.get("id") == self._id:
                if "error" in reply:
                    _fail(f"{method}: {reply['error']}")
                return reply["result"]

    def call(self, tool: str, /, _strict=True, **arguments) -> dict:
        # mcp_server flags isError whenever the result has an "error" key,
        # and compile_document always has one (None on success).
        result = self.request("tools/call", {"name": tool, "arguments": arguments})
        text = next((b["text"] for b in result["content"] if b["type"] == "text"), "{}")
        data = json.loads(text)
        if _strict and result.get("isError"):
            _fail(f"{tool}: {data}")
        return data

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def find_tectonic(exe: Path) -> Path:
    base = exe.parent.parent if exe.parent.name == "MacOS" else exe.parent
    name = "tectonic.exe" if sys.platform == "win32" else "tectonic"
    hits = [p for p in base.rglob(name) if p.is_file()]
    if not hits:
        _fail(f"no bundled {name} under {base}")
    return hits[0]


def offline_compiles(tec: Path, cache: Path, work: Path, env: dict):
    files = [p for p in cache.rglob("*") if p.is_file()] if cache.is_dir() else []
    if len(files) < 50:
        _fail(f"the app did not seed the empty tectonic cache ({len(files)} files)")
    print(f"seeded the empty cache with {len(files)} files", flush=True)
    from khervedoc import examples
    from khervedoc.serializer import serialize_document
    docs = {f"example{i}": serialize_document(f())
            for i, (_label, f) in enumerate(examples.EXAMPLES)}
    docs["fonts12"] = (
        r"\documentclass[12pt,twocolumn]{article}"
        r"\usepackage[a4paper]{geometry}\usepackage{amsmath,amssymb,graphicx,"
        r"multicol,float,setspace,xurl}\begin{document}\section{A}Text "
        r"\textbf{b} \emph{i} \texttt{t} \textsf{s} \url{https://x.org} "
        r"$x^2$\footnote{n}\end{document}")
    styles = _ROOT / "khervedoc" / "styles"
    oenv = dict(env, TEXINPUTS=str(styles) + os.pathsep)
    for name, source in docs.items():
        d = work / name
        d.mkdir()
        (d / "d.tex").write_text(source, encoding="utf-8")
        t0 = time.monotonic()
        try:
            out = subprocess.run([str(tec), "--only-cached", "-Z", "continue-on-errors",
                                  "--keep-logs", "d.tex"], cwd=d, env=oenv,
                                 capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired as exc:
            _fail(f"{name}: tectonic --only-cached hung for 180 s:\n"
                  + str(exc.stdout or "")[-1500:])
        log = out.stdout + out.stderr
        print(f"  offline {name}: {time.monotonic() - t0:.0f} s", flush=True)
        if not (d / "d.pdf").is_file() or "not found" in log or "not loadable" in log:
            _fail(f"{name} does not compile offline from the seeded cache:\n"
                  + log[-2000:])
    print(f"{len(docs)} documents compile offline from the seeded cache", flush=True)


def enable_bridge():
    from PySide6.QtCore import QSettings
    s = QSettings("kherveDOC", "kherveDOC")
    s.setValue("mcp/enabled", True)
    s.setValue("mcp/access", "full")
    s.sync()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--timeout", type=float, default=2400)
    args = ap.parse_args()
    exe = Path(args.exe).resolve()
    if not exe.is_file():
        _fail(f"{exe} does not exist")
    threading.Timer(args.timeout, lambda: _fail(f"timed out after {args.timeout}s")).start()

    tec = find_tectonic(exe)
    out = subprocess.run([str(tec), "--version"], capture_output=True, text=True)
    if out.returncode != 0:
        _fail(f"bundled tectonic did not run: {out.stderr}")
    print(f"bundled {tec.name}: {out.stdout.strip()}", flush=True)

    enable_bridge()
    endpoint = Path(endpoint_path())
    endpoint.unlink(missing_ok=True)
    import tempfile
    work = Path(tempfile.mkdtemp(prefix="ktex_smoke_"))
    cache = work / "tectonic-cache"          # empty: a brand-new machine
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen",
               TECTONIC_CACHE_DIR=str(cache))
    log = open(Path(os.environ.get("RUNNER_TEMP", ".")) / "khervetex-smoke.log", "wb")
    app = subprocess.Popen([str(exe)], env=env, stdout=log, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL)
    _CHILDREN.append(app)
    try:
        t0 = time.monotonic()
        while not endpoint.is_file():
            if app.poll() is not None:
                _fail(f"the app exited with code {app.returncode} during startup")
            if time.monotonic() - t0 > 180:
                _fail("the app did not start its MCP bridge within 180 s")
            time.sleep(1)
        print(f"app started in {time.monotonic() - t0:.0f} s", flush=True)
        time.sleep(3)

        print("connecting over MCP", flush=True)
        mcp = Mcp(str(exe), env)
        init = mcp.request("initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "smoke-test", "version": "1"}})
        mcp.notify("notifications/initialized")
        print("server:", init.get("serverInfo"), flush=True)
        tools = mcp.request("tools/list")["tools"]
        print(f"{len(tools)} tools", flush=True)
        print("get_document_info", flush=True)
        info = mcp.call("get_document_info")
        print("document:", json.dumps(info)[:300], flush=True)
        print("compile_document", flush=True)
        res = mcp.call("compile_document", _strict=False)
        print("compile:", {k: res.get(k) for k in ("ok", "error", "pages")}, flush=True)
        if not res.get("ok") or not res.get("pages"):
            print(res.get("log_tail", ""), flush=True)
            _fail("compile_document did not produce a PDF")
        mcp.close()
        offline_compiles(tec, cache, work, env)
    finally:
        app.terminate()
        try:
            app.wait(timeout=20)
        except subprocess.TimeoutExpired:
            app.kill()
    print("SMOKE TEST PASSED", flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
