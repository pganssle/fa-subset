import zipfile
from pathlib import Path


def unzip(source: Path) -> Path:
    fa_dir: Path = source.with_suffix("")
    if not fa_dir.exists():
        with zipfile.ZipFile(source, "r") as zf:
            fa_dir.mkdir()
            zf.extractall(fa_dir)
    return fa_dir
