"""Shared EAST parser entrypoints and error helpers."""

from __future__ import annotations

from typing import Any

from pytra.std.pathlib import Path


class EastBuildError(Exception):
    kind: str
    message: str
    source_span: dict[str, Any]
    hint: str

    def __init__(
        self,
        kind: str,
        message: str,
        source_span: dict[str, Any],
        hint: str,
    ) -> None:
        self.kind = kind
        self.message = message
        self.source_span = dict(source_span)
        self.hint = hint

    def to_payload(self) -> dict[str, Any]:
        """例外情報を EAST エラー応答用 dict に整形する。"""
        out: dict[str, Any] = {}
        out["kind"] = self.kind
        out["message"] = self.message
        out["source_span"] = self.source_span
        out["hint"] = self.hint
        return out


_IMPORT_BUILD_ERROR_TAG = "__PYTRA_IMPORT_BUILD_ERROR__|"


def _make_east_build_error(kind: str, message: str, source_span: dict[str, Any], hint: str) -> RuntimeError:
    """self-hosted 生成で投げる例外を std::exception 互換（RuntimeError）に統一する。"""
    src_line = int(source_span.get("lineno", 0))
    src_col = int(source_span.get("col", 0))
    return RuntimeError(f"{kind}: {message} at {src_line}:{src_col} hint={hint}")


def _make_import_build_error(
    code: str,
    message: str,
    source_span: dict[str, Any],
    hint: str,
    *,
    local_name: str = "",
    import_label: str = "",
) -> RuntimeError:
    """import 系 parser 診断を frontend 向けの structured envelope へ包む。"""
    payload = _IMPORT_BUILD_ERROR_TAG + code + "|" + message
    if local_name != "":
        payload += "\nlocal_name=" + local_name
    if import_label != "":
        payload += "\nimport_label=" + import_label
    src_line = int(source_span.get("lineno", 0))
    src_col = int(source_span.get("col", 0))
    if src_line > 0:
        payload += "\nlineno=" + str(src_line)
    if src_col > 0:
        payload += "\ncol=" + str(src_col)
    if hint != "":
        payload += "\nhint=" + hint
    return RuntimeError(payload)


def parse_import_build_error(err_text: str) -> tuple[str, str, dict[str, str]] | None:
    """structured import build error envelope を復元する。"""
    if not err_text.startswith(_IMPORT_BUILD_ERROR_TAG):
        return None
    lines = err_text.splitlines()
    head = lines[0]
    parts = head.split("|", 2)
    if len(parts) != 3:
        return None
    code = parts[1]
    message = parts[2]
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key != "":
            fields[key] = value
    return code, message, fields


def convert_source_to_east(source: str, filename: str) -> dict[str, Any]:
    """後方互換用の入口。self-hosted パーサで EAST を生成する。"""
    return convert_source_to_east_self_hosted(source, filename)


def convert_source_to_east_with_backend(source: str, filename: str, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """指定バックエンドでソースを EAST へ変換する統一入口。"""
    if parser_backend != "self_hosted":
        raise _make_east_build_error(
            kind="unsupported_syntax",
            message=f"unknown parser backend: {parser_backend}",
            source_span={},
            hint="Use parser_backend=self_hosted.",
        )
    return convert_source_to_east_self_hosted(source, filename)


def convert_path(input_path: Path, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """Python ファイルを読み込み、EAST ドキュメントへ変換する。"""
    source = input_path.read_text(encoding="utf-8")
    return convert_source_to_east_with_backend(source, str(input_path), parser_backend=parser_backend)


def convert_source_to_east_self_hosted(source: str, filename: str) -> dict[str, Any]:
    """Lazy import wrapper to avoid cycles while the module parser owns the implementation."""
    from toolchain.compile.core_module_parser import convert_source_to_east_self_hosted_impl

    return convert_source_to_east_self_hosted_impl(source, filename)
