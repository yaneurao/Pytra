"""EAST 入出力の共通ユーティリティ。"""

from __future__ import annotations

from pylib.std.dataclasses import dataclass
from pylib.std.typing import Any

from pylib.tra.east import EastBuildError, convert_path, convert_source_to_east_with_backend
from pylib.std import json
from pylib.std.pathlib import Path


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
                summary="EAST JSON の形式が不正です。",
                details=["期待形式: dict ルートの JSON"],
            )
        if payload.get("ok") is False:
            raise UserFacingError(
                category="east_error",
                summary="EAST JSON にエラー情報が含まれています。",
                details=[f"error: {payload.get('error')}"],
            )
        if payload.get("ok") is True and isinstance(payload.get("east"), dict):
            return payload["east"]
        if payload.get("kind") == "Module":
            return payload
        raise UserFacingError(
            category="input_invalid",
            summary="EAST JSON の構造が不正です。",
            details=["期待形式: {'ok': true, 'east': {...}} または {'kind': 'Module', ...}"],
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
                    summary="Python の文法エラーです。",
                    details=details,
                ) from exc
            if _is_unsupported_by_design(exc):
                raise UserFacingError(
                    category="unsupported_by_design",
                    summary="この構文は言語仕様上サポート対象外です。",
                    details=details,
                ) from exc
            raise UserFacingError(
                category="not_implemented",
                summary="この構文はまだ実装されていません。",
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
                summary="Python の文法エラーです。",
                details=details,
            ) from exc

    if isinstance(east, dict):
        has_stmt_leading_trivia = False
        body = east.get("body")
        if isinstance(body, list) and len(body) > 0 and isinstance(body[0], dict):
            trivia = body[0].get("leading_trivia")
            has_stmt_leading_trivia = isinstance(trivia, list) and len(trivia) > 0
        if not has_stmt_leading_trivia:
            east["module_leading_trivia"] = extract_module_leading_trivia(source_text)
    return east
