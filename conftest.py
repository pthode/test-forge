"""Pytest bootstrap: make the src/ layout importable.

The project uses a src/ layout (src/tokenlab/) with no installed package
metadata, so the package is not on sys.path by default. Adding src/ here lets
`from tokenlab.duration import parse_duration` resolve during test collection
without requiring an editable install. This is test-harness wiring only and
introduces no runtime dependency for the library itself.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
