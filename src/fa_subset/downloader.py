import urllib.parse
from pathlib import Path
from typing import Final

import requests

FA_VERSION_TEMPLATE: Final[
    str
] = "https://use.fontawesome.com/releases/v{version}/fontawesome-free-{version}-web.zip"
LATEST_FA_VERSION: Final[str] = "6.2.1"


def download_latest(out_dir: Path) -> Path:
    return download_version(LATEST_FA_VERSION, out_dir)


def download_version(version: str, out_dir: Path) -> Path:
    font_awesome_url = FA_VERSION_TEMPLATE.format(version=version)
    return download_url(font_awesome_url, out_dir)


def download_url(url: str, out_path: Path) -> Path:
    filename = Path(urllib.parse.urlparse(url).path).name

    font_awesome = out_path / f"fa_subset_fa/{filename}"

    font_awesome.parent.mkdir(exist_ok=True)

    if not font_awesome.exists():
        r = requests.get(url)
        r.raise_for_status()
        font_awesome.write_bytes(r.content)

    return font_awesome
