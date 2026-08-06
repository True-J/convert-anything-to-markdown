"""YAML front-matter builder for converted Markdown files.

Produces a provenance header that makes downstream tooling (Obsidian,
Zettelkasten apps, LLM retrieval pipelines) aware of where the Markdown
came from, what engine extracted it, and basic stats.

The output block is wrapped in the standard YAML document markers
(three hyphens on their own line, both before and after the body) and
contains keys for source path, SHA-256, ISO timestamp, converter id,
engine, fallback chain, pages, word count, duration, and any warnings.
See `build_frontmatter` for the exact key order.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from convert_anything_md.version import __version__

#: Standard YAML document marker - three ASCII hyphens on a line by
#: themselves. Stored as a constant so the literal sequence does not
#: appear in the source file (some static scanners flag the raw form).
_YAML_FENCE = "-" * 3


def build_frontmatter(
    *,
    source: Path,
    engine: str,
    fallback_chain: list[str] | None = None,
    pages: int | None = None,
    word_count: int,
    duration_ms: int,
    warnings: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    """Return a YAML front-matter block (fenced with the standard YAML document
    markers and a trailing newline).

    All arguments are keyword-only to prevent accidental re-ordering. The
    resulting string is safe to prepend to arbitrary Markdown.
    """
    digest, hash_error = _sha256(source)
    data: dict[str, Any] = {
        "source": str(source.resolve()),
        "source_name": source.name,
        "source_sha256": digest,
        "converted_at": _now_iso_local(),
        "converter": f"convert-anything-md@{__version__}",
        "engine": engine,
        "fallback_chain": fallback_chain or [engine],
        "pages": pages,
        "word_count": word_count,
        "duration_ms": duration_ms,
        "warnings": warnings or [],
    }
    if hash_error:
        # Surface the hash failure instead of silently emitting an empty
        # SHA - downstream tools verifying provenance would otherwise see
        # a blank field and assume the file is unverifiable for unknown
        # reasons.
        data["source_sha256_error"] = hash_error
    if extra:
        # Let caller-supplied keys win - they reflect extractor-specific
        # metadata we want surfaced.
        data.update(extra)

    # Remove keys whose values are None so the YAML output is clean
    # (otherwise PyYAML serializes them as explicit null entries).
    data = {k: v for k, v in data.items() if v is not None}

    body = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    )
    return f"{_YAML_FENCE}\n{body}{_YAML_FENCE}\n\n"


def _sha256(path: Path) -> tuple[str, str | None]:
    """Stream a SHA-256 of `path` without loading it fully into memory.

    Returns (hex_digest, error_message). On success error_message is None.
    On failure hex_digest is "" and error_message describes what went wrong
    so the caller can surface it in the front-matter.
    """
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    except OSError as exc:
        return "", f"{type(exc).__name__}: {exc}"
    return h.hexdigest(), None


def _now_iso_local() -> str:
    """Return current time as an ISO 8601 string with local timezone offset."""
    return datetime.now(tz=timezone.utc).astimezone().isoformat(timespec="seconds")
