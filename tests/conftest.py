from pathlib import Path

import pytest


@pytest.fixture
def rules_dir() -> Path:
    """Return the path to the directory containing .rule fixture files."""
    return Path(__file__).parent / "rules"
