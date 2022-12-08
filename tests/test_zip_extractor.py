from pathlib import Path

from fa_subset import zip_extractor


def test_zip_extraction(tmp_fa_zip: Path) -> None:
    expected_path = tmp_fa_zip.parent / "fontawesome-free-6.2.1-web"
    actual_path = zip_extractor.unzip(tmp_fa_zip)

    assert actual_path == expected_path
    assert actual_path.exists()
    assert actual_path.is_dir()
