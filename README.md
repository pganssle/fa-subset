# `fa-subset`: A utility for extracting glyphs from Font Awesome

[Font Awesome](https://fontawesome.com/) is an icon font framework that is very useful for designing web sites and web applications, but because it's got extensive coverage of various icons, it can be a quite heavyweight solution when you only use a few of the glyphs. With `fa-subset`, you can extract only the glyphs you want to use, along with the CSS you need to use it.

For example, if you only want to use the `user`, `rss`, `arrow-right` and `arrow-left` glyphs, you'd need to serve `fa-regular-400.{ttf,woff2}`, which are currently 61k and 25k, respectively. With  `fa-subset`, those files are 1.8k and 0.8k, respectively.

## Usage
```
Usage: fa-subset [OPTIONS] INPUT

  A CLI for creating subsets of the font awesome icon framework.

  "INPUT" should be a newline-delimited text file containing a list of glyphs
  to include in the output.

  If none of the `--font-awesome*` flags are specified, this tries to download
  the latest version. Otherwise, you may specify exactly one of those options
  to pick which version of font-awesome to use.

Options:
  --output DIRECTORY           A directory (which may exist already, but will
                               be made if it does not exist) where the outputs
                               should go. If you would like to specify the CSS
                               and font output locations separately, use
                               `--css-output` and `--font-output`. If those
                               are used, you must not specify `--output`.
  --css-output DIRECTORY       A directory into which to put the CSS files. If
                               specified, you must NOT specify `--output`, and
                               you MUST specify `--font-output`.
  --font-output DIRECTORY      A directory into which to put the font files.
                               If specified, you must NOT specify `--output`,
                               and you MUST specify `--css-output`.
  --font-awesome PATH          If you already have a copy of font-awesome
                               (either as a zip or a directory, use this
                               option to point the subsetter at it.
  --font-awesome-url TEXT      If you have a specific URL to download font
                               awesome from, use this option to pass it to the
                               subsetter.
  --font-awesome-version TEXT  If you know what version of font awesome you
                               want to download, pass it to this option.
  -f, --flavor TEXT            Flavors of font to output. Currently supported
                               options are: woff2, woff and ttf
  --help                       Show this message and exit.
```

`fa_subset` can also be used as a library, for your font subsetting needs that are more complicated than something you can easily express in terms of the command line flags.

## Installation

`fa_subset` is available [on PyPI](https://pypi.org/project/fa-subset/). We recommend installing it with [`pipx`](https://pypa.github.io/pipx/) or in a virtual environment.

## License

All images and documentation contained herein are licensed under [CC-0](https://creativecommons.org/publicdomain/zero/1.0/>).

The code is released under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) license.

These licenses do not cover Font Awesome. As of 2022, the free versions of Font Awesome use [SIL OFL 1.1, CC-BY 4.0 and MIT Licenses](https://fontawesome.com/license/free).
