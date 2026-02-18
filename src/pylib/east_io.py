"""EAST 入出力の共通ユーティリティ。"""

from __future__ import annotations

from pylib.typing import Any

from pylib.east import EastBuildError, convert_path, convert_source_to_east_with_backend
from pylib import json
from pylib.pathlib import Path


def extract_module_leading_trivia(source: str) -> list[dict[str, Any]]:
    """モジュール先頭のコメント/空行を trivia 形式で抽出する。"""
    out: list[dict[str, Any]] = []
    blank_count = 0
    for raw in source.splitlines():
        s = raw.strip()
        if s == "":
            blank_count += 1
            continue
        if s.startswith("#"):
            if blank_count > 0:
                out.append({"kind": "blank", "count": blank_count})
                blank_count = 0
            text = s[1:]
            if text.startswith(" "):
                text = text[1:]
            out.append({"kind": "comment", "text": text})
            continue
        break
    if blank_count > 0:
        out.append({"kind": "blank", "count": blank_count})
    return out


def load_east_from_path(input_path: Path, *, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """入力ファイル（.py/.json）を読み取り EAST Module dict を返す。"""
    if input_path.suffix == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError("Invalid EAST JSON payload")
        if payload.get("ok") is False:
            raise RuntimeError(f"EAST error: {payload.get('error')}")
        if payload.get("ok") is True and isinstance(payload.get("east"), dict):
            return payload["east"]
        if payload.get("kind") == "Module":
            return payload
        raise RuntimeError("Invalid EAST JSON structure")

    try:
        source_text = input_path.read_text(encoding="utf-8")
        if parser_backend == "self_hosted":
            east = convert_path(input_path)
        else:
            east = convert_source_to_east_with_backend(source_text, str(input_path), parser_backend=parser_backend)
    except (SyntaxError, EastBuildError) as exc:
        details: list[str] = [f"EAST conversion failed: {type(exc).__name__}"]
        if isinstance(exc, EastBuildError):
            span = exc.source_span if isinstance(exc.source_span, dict) else {}
            ln = span.get("lineno")
            col = span.get("col")
            details.append(f"{exc.kind}: {exc.message}")
            if isinstance(ln, int):
                if isinstance(col, int):
                    details.append(f"at {input_path}:{ln}:{col + 1}")
                else:
                    details.append(f"at {input_path}:{ln}")
                src_lines = source_text.splitlines()
                if 1 <= ln <= len(src_lines):
                    details.append(f"source: {src_lines[ln - 1]}")
            if isinstance(exc.hint, str) and exc.hint != "":
                details.append(f"hint: {exc.hint}")
        else:
            ln = getattr(exc, "lineno", None)
            off = getattr(exc, "offset", None)
            txt = getattr(exc, "text", None)
            msg = getattr(exc, "msg", str(exc))
            details.append(str(msg))
            if isinstance(ln, int):
                if isinstance(off, int):
                    details.append(f"at {input_path}:{ln}:{off}")
                else:
                    details.append(f"at {input_path}:{ln}")
            if isinstance(txt, str) and txt.strip() != "":
                details.append(f"source: {txt.rstrip()}")
        raise RuntimeError("\n".join(details)) from exc

    if isinstance(east, dict):
        has_stmt_leading_trivia = False
        body = east.get("body")
        if isinstance(body, list) and len(body) > 0 and isinstance(body[0], dict):
            trivia = body[0].get("leading_trivia")
            has_stmt_leading_trivia = isinstance(trivia, list) and len(trivia) > 0
        if not has_stmt_leading_trivia:
            east["module_leading_trivia"] = extract_module_leading_trivia(source_text)
    return east
