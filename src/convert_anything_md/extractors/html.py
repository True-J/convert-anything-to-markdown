"""HTML → Markdown.

Primary: Trafilatura (best-in-class boilerplate removal, F1 0.958 on
news-style pages). Fallback: BeautifulSoup with a simple tag-to-Markdown
walk, which still works when Trafilatura has trouble with exotic pages.
"""

from __future__ import annotations

import time
from pathlib import Path

from convert_anything_md.extractors.base import (
    ExtractionResult,
    ExtractorError,
    ExtractorUnavailable,
    word_count,
)


class TrafilaturaExtractor:
    """Content-aware HTML → Markdown using Trafilatura."""

    name = "trafilatura"

    def extract(self, path: Path) -> ExtractionResult:
        try:
            import trafilatura
        except ImportError as exc:
            raise ExtractorUnavailable("trafilatura is not installed") from exc

        start = time.perf_counter()
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ExtractorError(f"cannot read {path.name}: {exc}") from exc

        try:
            markdown = trafilatura.extract(
                raw,
                output_format="markdown",
                include_comments=False,
                include_tables=True,
                include_images=False,
                favor_precision=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise ExtractorError(
                f"trafilatura failed on {path.name}: {exc}"
            ) from exc

        if not markdown:
            raise ExtractorError(
                f"trafilatura extracted no content from {path.name} — "
                "the page may be mostly boilerplate."
            )

        duration_ms = int((time.perf_counter() - start) * 1000)
        return ExtractionResult(
            markdown=markdown.strip() + "\n",
            engine=self.name,
            word_count=word_count(markdown),
            duration_ms=duration_ms,
            fallback_chain=[self.name],
        )


class BeautifulSoupHtmlExtractor:
    """Lightweight HTML → Markdown fallback for when Trafilatura misses."""

    name = "beautifulsoup"

    # Tag → Markdown prefix. Everything else becomes plain text.
    _HEADING_MAP = {
        "h1": "# ", "h2": "## ", "h3": "### ",
        "h4": "#### ", "h5": "##### ", "h6": "###### ",
    }

    def extract(self, path: Path) -> ExtractionResult:
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise ExtractorUnavailable("beautifulsoup4 is not installed") from exc

        start = time.perf_counter()
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ExtractorError(f"cannot read {path.name}: {exc}") from exc

        soup = BeautifulSoup(raw, "lxml")
        # Strip boilerplate elements.
        for tag_name in ("script", "style", "noscript", "nav", "footer", "header", "aside"):
            for tag in soup(tag_name):
                tag.decompose()

        parts: list[str] = []
        title = soup.find("title")
        if title and title.text.strip():
            parts.append(f"# {title.text.strip()}")

        body = soup.body or soup
        for element in body.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre"]
        ):
            text = element.get_text(" ", strip=True)
            if not text:
                continue
            prefix = self._HEADING_MAP.get(element.name)
            if prefix:
                parts.append(f"{prefix}{text}")
            elif element.name == "li":
                parts.append(f"- {text}")
            elif element.name == "blockquote":
                parts.append(f"> {text}")
            elif element.name == "pre":
                parts.append(f"```\n{text}\n```")
            else:
                parts.append(text)

        if not parts:
            raise ExtractorError(
                f"no extractable content in {path.name}"
            )

        markdown = "\n\n".join(parts).strip() + "\n"
        duration_ms = int((time.perf_counter() - start) * 1000)
        return ExtractionResult(
            markdown=markdown,
            engine=self.name,
            word_count=word_count(markdown),
            duration_ms=duration_ms,
            fallback_chain=[self.name],
        )

