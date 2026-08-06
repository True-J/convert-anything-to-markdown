"""convert-anything-md: hybrid document-to-Markdown converter.

Public API:
    from convert_anything_md import convert_file, convert_batch, ExtractionResult

The library routes each input file to the best available extractor and emits
a Markdown file (optionally with YAML front-matter) to a user-chosen
directory (default: the OS desktop). See cli.py for the command-line entry
point installed as `convert-anything-md` (alias: `cam`).
"""

from convert_anything_md.extractors.base import ExtractionResult
from convert_anything_md.router import convert_batch, convert_file
from convert_anything_md.version import __version__

__all__ = ["ExtractionResult", "convert_batch", "convert_file", "__version__"]

