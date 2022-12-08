__all__ = ("downloader", "fa_extractor", "input_reader", "zip_extractor")


def __getattr__(name):
    import importlib

    if name == "__version__":
        try:
            from ._version import __version__
        except ImportError:
            return importlib.metadata.version("fa_subset")
        return __version__

    if name in __all__:
        return importlib.import_module("." + name, __name__)

    raise AttributeError(f"module {__name__!r} has not attribute {name!r}")


def __dir__():
    # __dir__ should include all the lazy-importable modules as well.
    return sorted(
        {x for x in globals() if x not in sys.modules} | set(__all__) | {"__version__"}
    )
