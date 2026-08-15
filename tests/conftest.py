"""Test-support path hook: make tests/ itself importable so host-qualification
guards can be shared by test modules in different subdirectories."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
