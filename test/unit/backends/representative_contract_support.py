from __future__ import annotations

from unittest import TestCase


_REPRESENTATIVE_ESCAPE_MARKERS = (
    "unsupported",
    "preview_only",
    "preview only",
    "preview-only",
    "[not_implemented]",
    "not_implemented",
    "not implemented yet",
)


def assert_no_representative_escape(
    testcase: TestCase,
    text: str,
    *,
    backend: str,
    fixture: str,
) -> None:
    testcase.assertTrue(
        text.strip(),
        f"{backend} representative fixture {fixture} emitted empty output",
    )
    lowered = text.lower()
    for marker in _REPRESENTATIVE_ESCAPE_MARKERS:
        testcase.assertNotIn(
            marker,
            lowered,
            f"{backend} representative fixture {fixture} escaped via {marker!r}",
        )
