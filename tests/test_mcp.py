"""MCP connection to Claude: the stdio protocol, the in-app bridge, and
the document tools, driven against a real (offscreen) main window."""
import json
import os
import threading
import time

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from khervedoc import mcp_bridge, mcp_server  # noqa: E402
from khervedoc.mcp_bridge import tool_allowed  # noqa: E402
from khervedoc.mcp_server import BridgeClient, McpServer  # noqa: E402
from khervedoc.mcp_tools import TOOLS, ToolExecutor  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp, monkeypatch):
    from khervedoc.mainwindow import MainWindow
    monkeypatch.setattr(MainWindow, "_kick_compile", lambda self: None)
    w = MainWindow()
    w._auto_compile = False
    yield w
    if getattr(w, "_mcp_bridge", None) is not None:
        w._mcp_bridge.stop()
    w.close()


def _load(window, latex_body: str):
    from khervedoc.importers import import_tex
    window._editor.set_document(import_tex(
        "\\documentclass{article}\\begin{document}\n"
        + latex_body + "\n\\end{document}"))


# ── protocol ───────────────────────────────────────────────────────

class _FakeBridge:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def request(self, method, params=None):
        self.calls.append((method, params))
        if method == "get_status":
            return {"version": "9.9"}
        if method == "list_tools":
            return TOOLS[:2]
        return self.result


def test_initialize_reports_version_and_instructions():
    srv = McpServer(_FakeBridge())
    reply = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2025-03-26"}})
    res = reply["result"]
    assert res["protocolVersion"] == "2025-03-26"
    assert res["serverInfo"]["name"] == "khervetex"
    assert "KherveTeX" in res["instructions"]


def test_tools_use_mcp_schema_keys():
    srv = McpServer(_FakeBridge())
    tools = srv.handle({"id": 2, "method": "tools/list"})["result"]["tools"]
    assert all("inputSchema" in t for t in tools)


def test_rendered_page_is_returned_as_an_image_block():
    srv = McpServer(_FakeBridge({"page": 1, "image_png_base64": "AAAA"}))
    res = srv.handle({"id": 3, "method": "tools/call",
                      "params": {"name": "render_page",
                                 "arguments": {"page": 1}}})["result"]
    kinds = [c["type"] for c in res["content"]]
    assert kinds == ["text", "image"]
    assert "AAAA" not in res["content"][0]["text"]


def test_tool_error_is_flagged():
    srv = McpServer(_FakeBridge({"error": "nope"}))
    res = srv.handle({"id": 4, "method": "tools/call",
                      "params": {"name": "x"}})["result"]
    assert res["isError"] is True


def test_successful_compile_is_not_flagged():
    srv = McpServer(_FakeBridge({"ok": True, "error": None, "pages": 4,
                                 "log_tail": ""}))
    res = srv.handle({"id": 5, "method": "tools/call",
                      "params": {"name": "compile_document"}})["result"]
    assert res["isError"] is False


def test_missing_app_explains_how_to_fix(tmp_path):
    srv = McpServer(BridgeClient(str(tmp_path / "none.json")))
    reply = srv.handle({"id": 5, "method": "tools/list"})
    assert "Connect to Claude" in reply["error"]["message"]


def test_every_tool_has_an_implementation():
    for t in TOOLS:
        assert hasattr(ToolExecutor, f"_t_{t['name']}"), t["name"]


def test_access_levels():
    assert tool_allowed("get_outline", "read")
    assert not tool_allowed("insert_latex", "read")
    assert tool_allowed("insert_latex", "edit")
    assert not tool_allowed("open_document", "edit")
    assert tool_allowed("open_document", "full")


def test_host_entry_runs_this_package():
    from khervedoc.mcp_hosts import server_entry
    entry = server_entry()
    assert entry["args"][-1] == "khervedoc.mcp_server"
    assert "PYTHONPATH" in entry["env"]


# ── tools on a live window ─────────────────────────────────────────

def test_outline_read_and_insert(window):
    _load(window, "\\section{Intro}\\label{sec:i}\nHello world.\n"
                  "\\section{Methods}\nWe did things.")
    ex = ToolExecutor(window)
    outline = ex.execute("get_outline", {})["blocks"]
    assert [b["type"] for b in outline][:2] == ["Section", "Paragraph"]
    assert outline[0]["number"] == "1"
    r = ex.execute("insert_latex", {"latex": "New paragraph here.",
                                    "after": 1})
    assert r["inserted_blocks"] == 1
    got = ex.execute("read_blocks", {"start": 2})["blocks"][0]["latex"]
    assert "New paragraph here." in got


def test_replace_delete_and_search(window):
    _load(window, "\\section{A}\nOne.\n\n\\section{B}\nTwo.")
    ex = ToolExecutor(window)
    ex.execute("replace_blocks", {"start": 1, "end": 1,
                                  "latex": "Uno \\cite{k1}."})
    assert ex.execute("search_text", {"query": "uno"})["count"] == 1
    ex.execute("delete_blocks", {"start": 2, "end": 3})
    assert len(ex.execute("get_outline", {})["blocks"]) == 2
    bad = ex.execute("delete_blocks", {"start": 7, "end": 9})
    assert "outside" in bad["error"]


def test_replace_text_and_metadata(window):
    _load(window, "Colour and colour.")
    ex = ToolExecutor(window)
    assert ex.execute("replace_text", {"find": "colour",
                                       "replace": "color"})["replacements"] == 2
    ex.execute("set_metadata", {"title": "T", "add_packages": ["siunitx"]})
    info = ex.execute("get_document_info", {})
    assert info["title"] == "T" and "siunitx" in info["packages"]
    assert "\\usepackage{siunitx}" in ex.execute("get_latex", {})["latex"]


def test_unsaved_work_is_not_discarded(window):
    _load(window, "Keep me.")
    ex = ToolExecutor(window)
    ex.execute("insert_latex", {"latex": "More."})
    assert "unsaved" in ex.execute("new_document", {})["error"]
    assert ex.execute("new_document",
                      {"discard_unsaved_changes": True}) == {"ok": True}


def test_save_in_place_needs_a_file(window):
    _load(window, "x")
    r = ToolExecutor(window).execute("save_document", {})
    assert "never been saved" in r["error"]


# ── the bridge over a real socket ──────────────────────────────────

@pytest.fixture
def live(window, tmp_path, monkeypatch):
    ep = tmp_path / "ep.json"
    monkeypatch.setattr(mcp_bridge, "endpoint_path", lambda: str(ep))
    monkeypatch.setattr(mcp_bridge, "state_dir", lambda: str(tmp_path))
    bridge = window.mcp_bridge()
    assert bridge.start()
    yield window, bridge, str(ep)
    bridge.stop()


def _call(qapp, endpoint, method, params=None):
    """Run a blocking client request off-thread while Qt serves it."""
    out = {}

    def run():
        client = BridgeClient(endpoint)
        try:
            out["r"] = client.request(method, params)
        except Exception as exc:
            out["e"] = exc
        finally:
            client.close()

    t = threading.Thread(target=run)
    t.start()
    deadline = time.monotonic() + 10
    while t.is_alive() and time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.005)
    t.join(1)
    if "e" in out:
        raise out["e"]
    return out["r"]


def test_endpoint_file_is_private_and_removed_on_stop(live):
    window, bridge, ep = live
    info = json.load(open(ep))
    assert info["port"] == bridge.port() and info["token"]
    if os.name != "nt":
        assert oct(os.stat(ep).st_mode & 0o777) == "0o600"
    bridge.stop()
    assert not os.path.exists(ep)


def test_wrong_token_is_refused(live, qapp):
    window, bridge, ep = live
    info = json.load(open(ep))
    info["token"] = "wrong"
    bad = ep + ".bad"
    json.dump(info, open(bad, "w"))
    with pytest.raises(mcp_server.BridgeError, match="token"):
        _call(qapp, bad, "get_status")


def test_one_tool_call_is_one_undo_step(live, qapp):
    window, bridge, ep = live
    _load(window, "\\section{A}\nOriginal text.")
    before = window._editor.get_document()
    res = _call(qapp, ep, "call_tool", {
        "name": "replace_text",
        "input": {"find": "Original", "replace": "Changed"}})
    assert res["replacements"] == 1
    assert "Changed" in window._editor.text_edit.toPlainText()
    window._editor.text_edit.undo()
    assert window._editor.get_document() == before


def test_read_access_refuses_edits(live, qapp):
    window, bridge, ep = live
    bridge.set_access("read")
    res = _call(qapp, ep, "call_tool",
                {"name": "insert_latex", "input": {"latex": "x"}})
    assert res["error"].startswith("Refused")
    names = {t["name"] for t in _call(qapp, ep, "list_tools")}
    assert "insert_latex" not in names and "get_outline" in names


def test_edit_access_refuses_client_chosen_paths(live, qapp):
    window, bridge, ep = live
    bridge.set_access("edit")
    res = _call(qapp, ep, "call_tool",
                {"name": "save_document", "input": {"path": "/tmp/x.ktexz"}})
    assert "Full" in res["error"]
