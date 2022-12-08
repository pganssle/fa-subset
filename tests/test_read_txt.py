import textwrap
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Literal, TextIO, TypeVar, Union

import pytest

from fa_subset import input_reader

T = TypeVar("T")
U = TypeVar("U")

GlyphInputs = Sequence[str] | str | Path | TextIO
GlyphTypeName = Union[
    Literal["sequence"], Literal["str"], Literal["path"], Literal["file"]
]


@pytest.fixture
def glyph_input(request, tmp_path: Path) -> Iterable[GlyphInputs]:
    components: Sequence[str] | str
    input_type: GlyphTypeName
    components, input_type = request.param
    if input_type == "sequence":
        if isinstance(components, str):
            yield components.split("\n")
            return
        else:
            yield components
            return
    else:
        if isinstance(components, str):
            str_components = components
        else:
            str_components = "\n".join(components)

        if input_type == "str":
            yield str_components
            return
        elif input_type in ("path", "file"):
            glyph_path = tmp_path / "glyphs.txt"
            glyph_path.write_text(str_components)
            if input_type == "path":
                yield glyph_path
                return
            else:
                with open(glyph_path, "rt") as f:
                    yield f
                return
    raise ValueError(f"Invalid input type: {input_type}")  # pragma: nocover


def _collect(f: Callable[..., Iterable[T]]) -> Callable[..., Sequence[T]]:
    def _collector(*args, **kwargs) -> Sequence[T]:
        return tuple(f(*args, **kwargs))

    return _collector


@_collect
def _make_fixture_param_args(
    glyphs: Sequence[tuple[Sequence[str], Sequence[str]]],
    input_methods: Sequence[GlyphTypeName] = ("sequence", "str", "path", "file"),
) -> Iterable[tuple[tuple[Sequence[str], str], Sequence[str]]]:
    for glyph_seq, expected_glyphs in glyphs:
        for input_method in input_methods:
            yield (glyph_seq, input_method), expected_glyphs


@pytest.mark.parametrize(
    "glyph_input, expected",
    _make_fixture_param_args(
        [
            (
                ("angle-left", "bars", "user", "gear", "qrcode"),
                ("angle-left", "bars", "user", "gear", "qrcode"),
            ),
            (
                "github\ntwitter\nuser",
                ("github", "twitter", "user"),
            ),
        ]
    )
    + _make_fixture_param_args(
        [
            (  # With blank lines
                textwrap.dedent(
                    """

                angle-left
                bars
                user
                """
                ),
                ("angle-left", "bars", "user"),
            ),
            (
                textwrap.dedent(
                    """\
                # Comment on the top line
                angle-left
                bars
                user
                filter
                """
                ),
                ("angle-left", "bars", "user", "filter"),
            ),
            (
                textwrap.dedent(
                    """\
                angle-left
                bars # inline comment
                user
                filter
                """
                ),
                ("angle-left", "bars", "user", "filter"),
            ),
            (
                textwrap.dedent(
                    """\
                # Top line
                angle-left # And a comment
                bars       # On
                user       # every
                filter     # line
                """
                ),
                ("angle-left", "bars", "user", "filter"),
            ),
            (
                textwrap.dedent(
                    """\
                angle-left
                bars
                user
                filter
                """,
                ),
                ("angle-left", "bars", "user", "filter"),
            ),
        ],
        input_methods=("str", "path", "file"),
    ),
    indirect=["glyph_input"],
)
def test_glyphs(
    glyph_input: GlyphInputs,
    expected: Sequence[str],
) -> None:
    actual = input_reader.read_txt(glyph_input)

    assert tuple(actual) == expected


@pytest.mark.parametrize("bad_input", (b"user\nrss\n", 32, [b"user", b"rss"]))
def test_invalid_type(bad_input) -> None:
    with pytest.raises(TypeError):
        input_reader.read_txt(bad_input)
