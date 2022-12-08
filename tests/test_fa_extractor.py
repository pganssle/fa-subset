import collections
import os
import shutil
from collections.abc import Iterable, Mapping, Sequence, Set
from pathlib import Path

import pytest
from fontTools import ttLib

from fa_subset import fa_extractor, zip_extractor


@pytest.fixture(scope="module")
def fa_dir(tmp_path_factory, fa_zip: Path) -> Iterable[Path]:
    tmp_path: Path = tmp_path_factory.mktemp("fa_dir")

    tmp_fa_zip = tmp_path / fa_zip.name
    shutil.copy(fa_zip, tmp_fa_zip)
    yield zip_extractor.unzip(tmp_fa_zip)


def test_find_input_fonts_ttf(fa_dir: Path) -> None:
    expected_font_names = {
        "fa-brands-400.ttf",
        "fa-regular-400.ttf",
        "fa-solid-900.ttf",
        "fa-v4compatibility.ttf",
    }

    input_fonts = fa_extractor.find_input_fonts(fa_dir, input_flavor="ttf")

    for font in input_fonts:
        assert font.exists()

    assert {x.name for x in input_fonts} == expected_font_names


def test_find_input_fonts_woff(fa_dir: Path) -> None:
    expected_font_names = {
        "fa-brands-400.woff2",
        "fa-regular-400.woff2",
        "fa-solid-900.woff2",
        "fa-v4compatibility.woff2",
    }

    input_fonts = fa_extractor.find_input_fonts(fa_dir, input_flavor="woff2")

    for font in input_fonts:
        assert font.exists()

    assert {x.name for x in input_fonts} == expected_font_names


@pytest.mark.parametrize(
    "included, expected_font_names",
    (
        (
            ("solid",),
            {"fa-solid-900.ttf"},
        ),
        (
            ("regular",),
            {"fa-regular-400.ttf"},
        ),
        (
            ("brands",),
            {"fa-brands-400.ttf"},
        ),
        (
            ("v4compat",),
            {"fa-v4compatibility.ttf"},
        ),
        (
            ("regular", "brands"),
            {"fa-regular-400.ttf", "fa-brands-400.ttf"},
        ),
    ),
)
def test_find_input_fonts_include(
    fa_dir: Path, included: Sequence[str], expected_font_names: Set[str]
) -> None:
    input_fonts = fa_extractor.find_input_fonts(
        fa_dir, include=included, input_flavor="ttf"
    )

    for font in input_fonts:
        assert font.exists()

    assert {x.name for x in input_fonts} == expected_font_names


def test_load_codepoints(fa_dir: Path) -> None:
    (css_file,) = fa_dir.glob("**/css/all.css")

    glyphs = [
        "user",
        "rss",
        "github",
    ]

    codepoints = fa_extractor.load_codepoints(css_file, glyphs)

    assert set(codepoints.keys()) == {"user", "rss-mod", "github"}


def test_load_codepoints_bad_glyph(fa_dir: Path) -> None:
    (css_file,) = fa_dir.glob("**/css/all.css")
    with pytest.raises(ValueError):
        fa_extractor.load_codepoints(css_file, ["oijaroeijoi"])


def assert_font_subset(
    subtests, font_path: Path, codepoints: Mapping[str, str]
) -> None:
    assert font_path.exists()
    assert os.path.getsize(font_path) > 0

    font = ttLib.TTFont(font_path)
    cmap = collections.ChainMap(*(table.cmap for table in font["cmap"].tables))
    assert len(cmap) == len(codepoints)
    for codepoint_name, codepoint in codepoints.items():
        with subtests.test(f"{font_path}-{codepoint_name}: {codepoint}"):
            assert int(codepoint, 16) in cmap


def test_generate_subset_font(fa_dir: Path, tmp_path: Path, subtests) -> None:
    glyphs = [
        "user",
        "rss",
        "github",
    ]
    (css_file,) = fa_dir.glob("**/css/all.css")

    out_path = tmp_path / "fontawesome-subset"
    expected_outputs = (
        out_path.with_suffix(".ttf"),
        out_path.with_suffix(".woff"),
        out_path.with_suffix(".woff2"),
    )

    input_fonts = fa_extractor.find_input_fonts(fa_dir)
    codepoints = fa_extractor.load_codepoints(css_file, glyphs)

    fa_extractor.generate_subset_font(
        input_fonts, codepoints, out_path, flavors=("ttf", "woff", "woff2")
    )

    assert codepoints
    for expected_output in expected_outputs:
        assert_font_subset(subtests, expected_output, codepoints)


def test_generate_font_subset(fa_dir: Path, tmp_path: Path, subtests) -> None:
    css_out = tmp_path / "fontawesome-subset.css"
    font_out = tmp_path / "fontawesome-subset"

    glyphs = [
        "user",
        "rss",
        "github",
    ]

    expected_outputs = (
        font_out.with_suffix(".ttf"),
        font_out.with_suffix(".woff"),
        font_out.with_suffix(".woff2"),
    )

    fa_extractor.generate_font_subset(
        fa_dir,
        css_out,
        font_out,
        glyphs,
        output_font_flavors=("ttf", "woff", "woff2"),
    )

    codepoints = fa_extractor.load_codepoints(css_out, ["user", "rss-mod", "github"])

    assert set(codepoints.keys()) == {"user", "rss-mod", "github"}
    for expected_output in expected_outputs:
        assert_font_subset(subtests, expected_output, codepoints)
