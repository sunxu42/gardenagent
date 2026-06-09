"""Deprecated: prompt editor API is now served by the unified server."""
from __future__ import annotations

import sys


def main() -> None:
    print(
        "src/prompt-editor-server.py is deprecated.\n"
        "Start the unified server instead:\n"
        "  python src/server.py\n"
        "Prompt editor API is available at /api/prompt-editor/ on the same port as WebSocket.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
