"""EAST 入出力の共通ユーティリティ。"""

from __future__ import annotations

from pytra.std.dataclasses import dataclass
from pytra.std.typing import Any

from pytra.compiler.east import EastBuildError, convert_path, convert_source_to_east_with_backend
from pytra.std import json
from pytra.std.pathlib import Path


def _normalize_dispatch_mode(value: Any) -> str:
    if isinstance(value, str):
        mode = value.strip()
        if mode == "native" or mode == "type_id":
            return mode
    return "native"


def _normalize_east_root(east: dict[str, Any]) -> dict[str, Any]:
    """EAST ルート契約（stage/schema/meta.dispatch_mode）を補完する。"""
    if east.get("kind") != "Module":
        return east

    stage_value = east.get("east_stage")
    stage = 2
    if isinstance(stage_value, int):
        if stage_value == 1 or stage_value == 2 or stage_value == 3:
            stage = stage_value
    east["east_stage"] = stage

    schema_value = east.get("schema_version")
    schema_version = 1
    if isinstance(schema_value, int) and schema_value > 0:
        schema_version = schema_value
    east["schema_version"] = schema_version

    meta_value = east.get("meta")
    meta: dict[str, Any] = {}
    if isinstance(meta_value, dict):
        meta = meta_value
    east["meta"] = meta
    meta["dispatch_mode"] = _normalize_dispatch_mode(meta.get("dispatch_mode"))
    return east


@dataclass
class UserFacingError(Exception):
    """ユーザーにそのまま提示するための分類済み例外。"""

    category: str
    summary: str
    details: list[str]

    def __str__(self) -> str:
        lines = [f"[{self.category}] {self.summary}"]
        lines.extend(self.details)
        return "\n".join(lines)


def _is_unsupported_by_design(err: EastBuildError) -> bool:
    msg = str(err.message)
    hint = str(err.hint)
    return ("forbidden by language constraints" in msg) or ("language constraints" in hint)


def _is_user_syntax_error(err: EastBuildError) -> bool:
    msg = str(err.message)
    return ("cannot parse" in msg) or ("unexpected token" in msg) or ("invalid syntax" in msg)


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
            raise UserFacingError(
                category="input_invalid",
                summary="Invalid EAST JSON format.",
                details=["expected: dict-root JSON"],
            )
        if payload.get("ok") is False:
            raise UserFacingError(
                category="east_error",
                summary="EAST JSON contains an error payload.",
                details=[f"error: {payload.get('error')}"],
            )
        if payload.get("ok") is True and isinstance(payload.get("east"), dict):
            return _normalize_east_root(payload["east"])
        if payload.get("kind") == "Module":
            return _normalize_east_root(payload)
        raise UserFacingError(
            category="input_invalid",
            summary="Invalid EAST JSON structure.",
            details=["expected: {'ok': true, 'east': {...}} or {'kind': 'Module', ...}"],
        )

    try:
        source_text = input_path.read_text(encoding="utf-8")
        if parser_backend == "self_hosted":
            east = convert_path(input_path)
        else:
            east = convert_source_to_east_with_backend(source_text, str(input_path), parser_backend=parser_backend)
    except (SyntaxError, EastBuildError) as exc:
        details: list[str] = []
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
            if _is_user_syntax_error(exc):
                raise UserFacingError(
                    category="user_syntax_error",
                    summary="Python syntax error.",
                    details=details,
                ) from exc
            if _is_unsupported_by_design(exc):
                raise UserFacingError(
                    category="unsupported_by_design",
                    summary="This syntax is unsupported by language design.",
                    details=details,
                ) from exc
            raise UserFacingError(
                category="not_implemented",
                summary="This syntax is not implemented yet.",
                details=details,
            ) from exc
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
            raise UserFacingError(
                category="user_syntax_error",
                summary="Python syntax error.",
                details=details,
            ) from exc

    if isinstance(east, dict):
        east = _normalize_east_root(east)
        has_stmt_leading_trivia = False
        body = east.get("body")
        if isinstance(body, list) and len(body) > 0 and isinstance(body[0], dict):
            trivia = body[0].get("leading_trivia")
            has_stmt_leading_trivia = isinstance(trivia, list) and len(trivia) > 0
        if not has_stmt_leading_trivia:
            east["module_leading_trivia"] = extract_module_leading_trivia(source_text)
    return east
