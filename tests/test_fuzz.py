"""The schema fuzzer's laws hold on a few fixed seeds.

The nightly job runs a fresh window of seeds against live PostgreSQL;
this keeps the generator and the two laws exercised on every commit.
"""

import importlib.util
import logging
from pathlib import Path
from types import ModuleType

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"


def _tool(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_fuzz_seed_obeys_the_laws(seed: int, tmp_path: Path) -> None:
    logging.getLogger("sqlglot").setLevel(logging.ERROR)
    runner = _tool("fuzz_run")
    result = runner.check_seed(seed, tmp_path, pg=None)
    assert result.failures == []
    assert result.objects > 40
    assert result.ddl_bytes > 5000


def test_fuzz_dump_is_deterministic(tmp_path: Path) -> None:
    gen = _tool("fuzz_dump")
    gen.generate(7, tmp_path / "a")
    gen.generate(7, tmp_path / "b")
    for path in sorted((tmp_path / "a").iterdir()):
        assert path.read_bytes() == (tmp_path / "b" / path.name).read_bytes()
