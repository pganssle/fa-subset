import functools
import operator
import shutil
import sys
import tempfile
from collections.abc import Iterable, MutableSequence, Sequence
from pathlib import Path
from typing import NoReturn

import click

from . import fa_extractor, input_reader

ExistingDir = click.Path(dir_okay=True, file_okay=False, exists=True, path_type=Path)
ExistingFileOrDir = click.Path(
    dir_okay=True, file_okay=True, exists=True, path_type=Path
)
ExistingFile = click.Path(dir_okay=False, file_okay=True, exists=True, path_type=Path)


def _get_default_output_loc() -> Path:
    return Path.cwd() / "fontawesome-subset"


def _bad_options(message: str) -> NoReturn:
    print(message)
    sys.exit(1)


@click.command()
@click.option(
    "--input",
    "-i",
    type=ExistingFile,
    default=None,
    help="A newline-delimited text file containing a list of glyphs to include "
    "in the output",
)
@click.option(
    "--output",
    "-o",
    type=ExistingDir,
    default=None,
    help="A directory (which may exist already, but will be made if "
    "it does not exist) where the outputs should go. If you "
    "would like to specify the CSS and font output locations "
    "separately, use `--css-output` and `--font-output`. If "
    "those are used, you must not specify `--output`.",
    show_default=_get_default_output_loc(),
)
@click.option(
    "--css-output",
    type=ExistingDir,
    default=None,
    help="A directory into which to put the CSS files. If specified, "
    "you must NOT specify `--output`, and you MUST specify "
    "`--font-output`.",
)
@click.option(
    "--font-output",
    type=ExistingDir,
    default=None,
    help="A directory into which to put the font files. If specified, "
    "you must NOT specify `--output`, and you MUST specify "
    "`--css-output`.",
)
@click.option(
    "--font-awesome",
    type=ExistingFileOrDir,
    default=None,
    help="If you already have a copy of font-awesome (either as a zip "
    "or a directory, use this option to point the subsetter at it.",
)
@click.option(
    "--font-awesome-url",
    type=str,
    default=None,
    help="If you have a specific URL to download font awesome from, "
    "use this option to pass it to the subsetter.",
)
@click.option(
    "--font-awesome-version",
    type=str,
    default=None,
    help="If you know what version of font awesome you want to "
    "download, pass it to this option.",
)
@click.option(
    "--flavor",
    "-f",
    type=str,
    multiple=True,
    default=("woff", "woff2"),
    help="Flavors of font to output. Currently supported options are:\n"
    "    woff2, woff and ttf",
)
@click.option(
    "--version", is_flag=True, default=False, help="Print the current version and exit"
)
def main(
    input: Path | None,
    output: Path | None,
    css_output: Path | None,
    font_output: Path | None,
    font_awesome: Path | None,
    font_awesome_url: str | None,
    font_awesome_version: str | None,
    flavor: Sequence[str],
    version: bool = False,
) -> None:
    """A CLI for creating subsets of the font awesome icon framework.

    If none of the `--font-awesome*` flags are specified, this tries to
    download the latest version. Otherwise, you may specify exactly one of
    those options to pick which version of font-awesome to use.
    """
    if version:
        from . import __version__

        print(__version__)
        sys.exit(0)

    # Handle mutually exclusive options
    if (output is not None) and ((css_output is not None) or (font_output is not None)):
        _bad_options(
            "May specify either --output OR --css-output and --font-output, but not both"
        )
    elif (css_output is not None) != (font_output is not None):
        _bad_options(
            "Both or neither of --css-output and --font-output must be specified, not just one"
        )

    temp_path = Path(tempfile.gettempdir())

    if (
        sum(
            map(
                functools.partial(operator.is_not, None),
                (font_awesome, font_awesome_url, font_awesome_version),
            )
        )
    ) > 1:
        _bad_options(
            f"May specify either 0 or 1 of --font-awesome, --font-awesome-url, "
            "--font-awesome-version, but specified {num_fa_specified}"
        )

    if font_awesome is None:
        from . import downloader

        if font_awesome_version is not None:
            font_awesome = downloader.download_version(font_awesome_version, temp_path)
        elif font_awesome_url is not None:
            font_awesome = downloader.download_url(font_awesome_url, temp_path)
        else:
            font_awesome = downloader.download_latest(temp_path)
    assert font_awesome is not None

    if font_awesome.suffix == ".zip":
        from . import zip_extractor

        fa_dir = zip_extractor.unzip(font_awesome)
    else:
        fa_dir = font_awesome

    if css_output is not None:
        assert font_output is not None
        css_loc: Path = css_output
        fonts_loc: Path = font_output
    else:
        if output is None:
            output = _get_default_output_loc()
        css_loc = output / "css"
        fonts_loc = output / "fonts"

    css_out = css_loc / "fontawesome-subset.css"
    font_out = fonts_loc / "fontawesome-subset"

    if input is None:
        # If input is not specified, read from stdin
        input_: Path | Iterable[str] = sys.stdin
    else:
        input_ = input

    glyphs = input_reader.read_txt(input_)

    directories_made: MutableSequence[Path] = []
    assert output is not None
    try:
        if not output.exists():
            directories_made.append(output)
            output.mkdir()

        if not css_out.parent.exists():
            for parent in css_out.absolute().parents:
                if not parent.exists():
                    directories_made.append(parent)
                else:
                    break
            css_out.parent.mkdir(parents=True)

        if not font_out.parent.exists():
            for parent in font_out.absolute().parents:
                if not parent.exists():
                    directories_made.append(parent)
                else:
                    break
            font_out.parent.mkdir(parents=True)

        fa_extractor.generate_font_subset(
            fa_dir=fa_dir,
            css_out=css_out,
            font_out=font_out,
            glyphs=glyphs,
            output_font_flavors=flavor,
        )
    except:
        for directory in directories_made:
            try:
                shutil.rmtree(directory)
            except Exception:
                pass
        raise


if __name__ == "__main__":  # pragma: nocover
    main()
