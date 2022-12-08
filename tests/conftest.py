import shutil
from collections.abc import Iterable
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def fa_zip() -> Path:
    return DATA_DIR / "fontawesome-free-6.2.1-web.zip"


@pytest.fixture
def tmp_fa_zip(tmp_path: Path, fa_zip: Path) -> Iterable[Path]:
    out_file = tmp_path / fa_zip.name

    shutil.copyfile(fa_zip, out_file)
    yield out_file
