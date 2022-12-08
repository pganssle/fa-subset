import pathlib
from unittest import mock

import pytest

from fa_subset import downloader


@pytest.fixture
def mocked_requests():
    with mock.patch.object(downloader, "requests") as p:
        p.get.return_value.content = b"Fake content!"
        yield p


def test_download_latest(mocked_requests, tmp_path: pathlib.Path) -> None:

    out_path = downloader.download_latest(tmp_path)

    mocked_requests.get.assert_called_once()
    assert downloader.LATEST_FA_VERSION in mocked_requests.get.call_args[0][0]

    assert out_path.exists()
    assert out_path.read_bytes() == b"Fake content!"


def test_download_version(mocked_requests, tmp_path: pathlib.Path) -> None:
    out_path = downloader.download_version("6.2.0", tmp_path)
    expected_url = (
        "https://use.fontawesome.com/releases/v6.2.0/fontawesome-free-6.2.0-web.zip"
    )
    mocked_requests.get.assert_called_once_with(expected_url)

    assert out_path.exists()
    assert out_path.read_bytes() == b"Fake content!"


def test_download_url(mocked_requests, tmp_path: pathlib.Path) -> None:
    expected_url = (
        "https://use.fontawesome.com/releases/v6.0.0/fontawesome-free-6.0.0-web.zip"
    )

    out_path = downloader.download_url(expected_url, tmp_path)
    mocked_requests.get.assert_called_once_with(expected_url)

    assert out_path.exists()
    assert out_path.read_bytes() == b"Fake content!"


def test_download_url_exists(mocked_requests, tmp_path: pathlib.Path) -> None:
    expected_out_path = tmp_path / "fa_subset_fa/fontawesome-free-6.2.1-web.zip"

    expected_out_path.parent.mkdir()
    expected_out_path.write_bytes(b"Different content")

    out_path = downloader.download_url(
        "https://use.fontawesome.com/releases/v6.2.1/fontawesome-free-6.2.1-web.zip",
        tmp_path,
    )

    assert out_path == expected_out_path
    mocked_requests.get.assert_not_called()

    assert out_path.read_bytes() == b"Different content"
