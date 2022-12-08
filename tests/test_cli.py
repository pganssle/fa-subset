import contextlib
import os
from collections.abc import Iterable, MutableSequence, Sequence
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

import fa_subset
from fa_subset import __main__ as famain
from fa_subset import downloader


def _get_latest_version() -> str:
    return downloader.FA_VERSION_TEMPLATE.format(version=downloader.LATEST_FA_VERSION)


@pytest.fixture
def mocked_requests(fa_zip: Path):
    def load_data(url: str) -> mock.Mock:
        out = mock.Mock()
        file_contents = fa_zip.read_bytes()
        out.content = file_contents
        return out

    with mock.patch.object(downloader, "requests") as p:
        p.get.side_effect = load_data
        yield p


@contextlib.contextmanager
def in_cwd(new_cwd: Path) -> Iterable[None]:
    old_cwd = Path.cwd()
    try:
        os.chdir(new_cwd)
        yield
    finally:
        os.chdir(old_cwd)


@pytest.mark.parametrize(
    "flags",
    (
        (
            "--font-awesome",
            "--font-awesome-url",
        ),
        ("--font-awesome", "--font-awesome-version"),
        ("--font-awesome-url", "--font-awesome-version"),
        ("--font-awesome", "--font-awesome-url", "--font-awesome-version"),
    ),
)
def test_too_many_fa_flags(flags: Sequence[str], fa_zip: Path, tmp_path: Path) -> None:
    mapping = {
        "--font-awesome": os.fspath(fa_zip),
        "--font-awesome-url": downloader.FA_VERSION_TEMPLATE.format(version="6.2.0"),
        "--font-awesome-version": "6.1.9",
    }

    out_path = tmp_path / "glyphs.txt"
    out_path.write_text("user\nrss\ngithub")

    args: MutableSequence[str] = []
    for flag in flags:
        args.extend((flag, mapping[flag]))

    args.extend(("-i", os.fspath(out_path)))
    runner = CliRunner()
    result = runner.invoke(famain.main, args)
    assert result.exit_code != 0
    assert "--font-awesome" in result.output


@pytest.mark.parametrize(
    "flags",
    (
        ("--css-output",),
        ("--font-output",),
    ),
)
def test_only_one_output_flag(flags: Sequence[str], tmp_path: Path) -> None:
    font_output = tmp_path / "fonts"
    font_output.mkdir()
    css_output = tmp_path / "css"
    css_output.mkdir()

    mapping = {
        "--css-output": os.fspath(css_output),
        "--font-output": os.fspath(font_output),
    }

    glyph_path = tmp_path / "glyphs.txt"
    glyph_path.write_text("user\nrss\ngithub")

    args: MutableSequence[str] = []
    for flag in flags:
        args.extend((flag, mapping[flag]))

    args.extend(("-i", os.fspath(glyph_path)))
    runner = CliRunner()
    result = runner.invoke(famain.main, args)
    assert result.exit_code != 0
    assert "--css-output" in result.output
    assert "--font-output" in result.output


@pytest.mark.parametrize(
    "flags",
    (
        (
            "--output",
            "--css-output",
        ),
        (
            "--output",
            "--font-output",
        ),
        (
            "--output",
            "--css-output",
            "--font-output",
        ),
    ),
)
def test_too_many_output_flags(flags: Sequence[str], tmp_path: Path) -> None:
    font_output = tmp_path / "fonts"
    font_output.mkdir()
    css_output = tmp_path / "css"
    css_output.mkdir()
    output = tmp_path

    mapping = {
        "--css-output": os.fspath(css_output),
        "--font-output": os.fspath(font_output),
        "--output": os.fspath(output),
    }

    glyph_path = tmp_path / "glyphs.txt"
    glyph_path.write_text("user\nrss\ngithub")

    args: MutableSequence[str] = []
    for flag in flags:
        args.extend((flag, mapping[flag]))

    args.extend(("-i", os.fspath(glyph_path)))
    runner = CliRunner()
    result = runner.invoke(famain.main, args)
    assert result.exit_code != 0
    assert "--output" in result.output
    assert "--css-output" in result.output
    assert "--font-output" in result.output


@pytest.mark.parametrize(
    "flags",
    (
        (),
        ("--font-awesome-url", _get_latest_version()),
        ("--font-awesome-version", downloader.LATEST_FA_VERSION),
    ),
)
def test_cli_download(flags: Sequence[str], tmp_path: Path, mocked_requests) -> None:
    expected_output = tmp_path / "fontawesome-subset"
    expected_css_out = expected_output / "css" / "fontawesome-subset.css"
    expected_fonts = {
        expected_output / "fonts" / "fontawesome-subset.woff",
        expected_output / "fonts" / "fontawesome-subset.woff2",
    }

    glyph_path = tmp_path / "glyphs.txt"
    glyph_path.write_text("user\nrss\ngithub")

    with mock.patch.object(famain.tempfile, "gettempdir") as gettempdir_p:
        fake_temp_dir = tmp_path / "fake_temp_dir"
        gettempdir_p.return_value = os.fspath(fake_temp_dir)
        fake_temp_dir.mkdir()
        with in_cwd(tmp_path):
            runner = CliRunner()
            result = runner.invoke(famain.main, (*flags, "-i", os.fspath(glyph_path)))

    assert result.exit_code == 0
    mocked_requests.get.assert_called_once_with(_get_latest_version())

    for file in {expected_css_out} | expected_fonts:
        assert file.exists()
        assert os.path.getsize(file) > 0


def test_cli_stdin(mocked_requests, tmp_path: Path) -> None:
    expected_output = tmp_path / "fontawesome-subset"
    expected_output.mkdir()
    expected_css_out = expected_output / "css" / "fontawesome-subset.css"
    expected_fonts = {
        expected_output / "fonts" / "fontawesome-subset.woff",
        expected_output / "fonts" / "fontawesome-subset.woff2",
    }
    runner = CliRunner()
    result = runner.invoke(
        famain.main, ("--output", os.fspath(expected_output)), input="user\nrss\ngithub"
    )

    assert result.exit_code == 0
    for file in {expected_css_out} | expected_fonts:
        assert file.exists()
        assert os.path.getsize(file) > 0


def test_version():
    runner = CliRunner()
    result = runner.invoke(famain.main, ("--version",))

    assert result.exit_code == 0
    assert result.output == fa_subset.__version__ + "\n"
