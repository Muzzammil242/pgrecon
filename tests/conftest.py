from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def dump_basic() -> Path:
    return FIXTURES / "dump_basic"
