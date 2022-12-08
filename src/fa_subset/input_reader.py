import functools
import io
from collections.abc import Iterable, Sequence
from pathlib import Path


def _read_txt(glyph_file: Iterable[str]) -> Sequence[str]:
    return tuple(filter(None, (line.split("#", 1)[0].strip() for line in glyph_file)))


@functools.singledispatch
def read_txt(glyph_file) -> Sequence[str]:
    """Reads a text file of glyph names.

    :param glyph_file:
        A Path object or file-like object pointing to a text file containing
        newline-delimited glyph names. Comments can be included using `#`.
        Empty lines will be ignored.

    :return:
        Returns a sequence of glyph names.
    """
    exc = None
    if isinstance(glyph_file, Iterable):
        try:
            return _read_txt(glyph_file)
        except AttributeError as e:
            exc = e
    raise TypeError(
        f"Cannot read type from parameter of type: {type(glyph_file)}"
    ) from exc


@read_txt.register
def _(glyph_file: str) -> Sequence[str]:
    return read_txt(io.StringIO(glyph_file))


@read_txt.register
def _(glyph_file: io.TextIOBase) -> Sequence[str]:
    return _read_txt(iter(glyph_file))


@read_txt.register
def _(glyph_file: Path) -> Sequence[str]:
    with open(glyph_file) as f:
        return read_txt(f)
