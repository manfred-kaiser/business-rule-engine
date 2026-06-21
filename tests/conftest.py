from pathlib import Path

import pytest

from business_rule_engine import RuleParser


@pytest.fixture
def rules_dir() -> Path:
    """Return the path to the directory containing .rule fixture files."""
    return Path(__file__).parent / "rules"


@pytest.fixture(autouse=True)
def isolated_functions():
    """Restore CUSTOM_FUNCTIONS to its original state after each test."""
    snapshot = dict(RuleParser.CUSTOM_FUNCTIONS)
    yield
    RuleParser.CUSTOM_FUNCTIONS.clear()
    RuleParser.CUSTOM_FUNCTIONS.update(snapshot)
