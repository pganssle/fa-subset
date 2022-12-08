import dataclasses
import functools
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

import fontTools.merge  # type: ignore
import fontTools.subset  # type: ignore

FONT_NAMES: Final[Mapping[str, str]] = {
    "brands": "fa-brands-400",
    "regular": "fa-regular-400",
    "solid": "fa-solid-900",
    "v4compat": "fa-v4compatibility",
}

FONT_FAMILY: Final[str] = "FontAwesomeSubset"

FONT_DEFINITION: Final[
    str
] = f"""@font-face {{{{
  font-family: '{FONT_FAMILY}';
  src:
{{flavors}};
}}}}
"""

CSS_START: Final[
    str
] = """.fa,
.fas,
.far,
.fal,
.fab {
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  display: inline-block;
  font-style: normal;
  font-variant: normal;
  text-rendering: auto;
  line-height: 1;
  font-family: 'FontAwesomeSubset'; }
"""

CSS_BASE: Final[
    str
] = """.fa-{icon}:before {{
    content: "\\{codepoint}"; }}
"""


@dataclasses.dataclass
class _FAPaths:
    fa_dir: Path

    @functools.cached_property
    def fa_css_dir(self):
        # Right now the structure contains exactly one /css directory, hopefully
        # this doesn't change.
        (fa_css_dir,) = self.fa_dir.glob("**/css")
        return fa_css_dir

    @functools.cached_property
    def fa_css_file(self):
        return self.fa_css_dir / "all.css"

    @functools.cached_property
    def fa_base_dir(self):
        return self.fa_css_dir.parent

    @functools.cached_property
    def fa_font_dir(self):
        return self.fa_base_dir / "webfonts"


@functools.lru_cache
def _fa_paths(fa_dir: Path) -> _FAPaths:
    return _FAPaths(fa_dir)


def _make_kwargs(**kwargs) -> Mapping[str, Any]:
    return {key: value for key, value in kwargs.items() if value is not None}


def _extract_font_awesome(icon: str, css: str) -> str:
    name = f".fa-{icon}"

    m = re.search(
        name + ":+before {\s+content: " "['\"]+(?P<codepoint>[^'\"]+)",
        css,
        re.MULTILINE,
    )

    if m is None:
        raise ValueError(f"Unknown icon: {icon}")

    codepoint = m.group("codepoint")
    if codepoint.startswith("\\"):
        codepoint = codepoint[1:]

    return codepoint


def load_codepoints(css_file: Path, glyphs: Sequence[str]) -> Mapping[str, str]:
    with open(css_file, "r") as f:
        css = f.read()
        codepoints = {icon: _extract_font_awesome(icon, css) for icon in glyphs}

    if "rss" in codepoints:
        # Apparently uBlock is blocking .fa-rss (at least for me)
        codepoints["rss-mod"] = codepoints["rss"]
        del codepoints["rss"]

    return codepoints


def find_input_fonts(
    fa_dir: Path,
    *,
    input_flavor: str = "ttf",
    include=("brands", "solid", "regular", "v4compat"),
) -> Sequence[Path]:
    font_names = [f"{FONT_NAMES[name]}.{input_flavor}" for name in include]
    fa_paths = _fa_paths(fa_dir)
    return [fa_paths.fa_font_dir / font_fname for font_fname in font_names]


def generate_subset_font(
    input_fonts: Sequence[Path],
    codepoints: Mapping[str, str],
    output_loc: Path,
    flavors: Sequence[str] = ("woff2", "woff"),
) -> Sequence[tuple[str, str]]:
    codepoints_str = ",".join(("U+" + cp) for cp in codepoints.values())

    with tempfile.TemporaryDirectory() as tdir_s:
        tdir = Path(tdir_s)
        # Create subsets of all the input fonts
        font_outputs = []
        for font_in in input_fonts:
            font_path = os.fspath(font_in)
            out_name = font_in.stem + ".sub" + font_in.suffix
            font_out = tdir / out_name

            fontTools.subset.main(
                args=(
                    font_path,
                    f"--output-file={font_out}",
                    f"--unicodes={codepoints_str}",
                )
            )

            font_outputs.append(font_out)

        # Merge them into a single font output
        merger = fontTools.merge.Merger()
        font = merger.merge(font_outputs)
        flavors_out = []
        for flavor in flavors:
            if flavor in {"woff", "woff2"}:
                font.flavor = flavor
            out_path = output_loc.with_suffix(f".{flavor}")
            flavors_out.append((out_path.name, flavor))
            font.save(out_path)

        return flavors_out


def generate_css(
    codepoints: Mapping[str, str],
    font_flavors: Sequence[tuple[str, str]],
    font_locs: Path = Path("../fonts/"),
) -> str:
    font_flavors_in = [
        (font_locs / output_name, flavor) for output_name, flavor in font_flavors
    ]

    font_inputs = ",\n".join(
        [
            f"    url('{font_loc}') format('{flavor}')"
            for font_loc, flavor in font_flavors_in
        ]
    )

    css = [FONT_DEFINITION.format(flavors=font_inputs), CSS_START]

    css += [
        CSS_BASE.format(icon=icon, codepoint=codepoint)
        for icon, codepoint in codepoints.items()
    ]

    return "\n".join(css)


def generate_font_subset(
    fa_dir: Path,
    css_out: Path,
    font_out: Path,
    glyphs: Sequence[str],
    *,
    output_font_flavors: Sequence[str] | None = None,
    input_flavor: str | None = None,
    include_fonts: Sequence[str] | None = None,
) -> None:

    fa_paths = _fa_paths(fa_dir)
    input_fonts = find_input_fonts(
        fa_dir, **_make_kwargs(input_flavor=input_flavor, include=include_fonts)
    )

    codepoints = load_codepoints(fa_paths.fa_css_file, glyphs)
    font_flavors = generate_subset_font(
        input_fonts, codepoints, font_out, **_make_kwargs(flavors=output_font_flavors)
    )

    css = generate_css(codepoints, font_flavors)
    css_out.write_text(css)
