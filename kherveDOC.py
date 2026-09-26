"""Launcher — run this file to start kherveDOC.

Equivalent to `python -m khervedoc` but lets you double-click the file or
hand it to an IDE's run button.
"""
import sys
from pathlib import Path

# Make the package importable when this file is run directly.
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__" and "--mcp-server" in sys.argv[1:]:
    # Claude launches the frozen app with this flag as its MCP server;
    # answer on stdio without importing Qt or opening a window.
    from khervedoc.mcp_server import main as mcp_main
    sys.exit(mcp_main([a for a in sys.argv[1:] if a != "--mcp-server"]))

from khervedoc.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
