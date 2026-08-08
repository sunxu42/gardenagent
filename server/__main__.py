"""Allow ``python -m server`` to start the unified Garden server."""

import os

# macOS + Anaconda: mem0ai[nlp]/spacy may load a second OpenMP runtime.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from server.server import main

if __name__ == "__main__":
    main()
