<a href="../../en/plans/p1-parser-stdlib-json.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-PARSER-STDLIB-JSON: pytra.std.json の parser 対応 + golden 再生成

最終更新: 2026-03-27
ステータス: 未着手

## 背景

`src/pytra/std/json.py` は stdlib の正本だが、current source が parser で parse 失敗する。そのため golden（EAST1/EAST2/EAST3/EAST3-opt/linked）が再生成できず、stale な stored EAST3 が使われ続けている。Go selfhost（P2-SELFHOST-S4）では、stale EAST3 に起因する型崩れ（`str` coercion 残り、optional narrowing 不足、cast 由来の壊れた型）が Go build ブロッカーになっている。

同じ問題は他の `pytra.std.*` でも起きうるため、parser の対応は selfhost だけでなくパイプライン全体の健全性に関わる。

## parse 失敗の原因

`src/pytra/std/json.py` で parser が処理できない構文:

1. **再帰的 type alias（PEP 695 形式）**:
   ```python
   type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]
   ```
   - `type X = ...` 構文（PEP 695）の parser 対応
   - 右辺の Union に自身（`JsonVal`）が再帰的に出現する forward reference の解決

2. **クラス定義前の前方参照**:
   ```python
   def get(self, key: str) -> JsonValue | None:  # JsonValue はこの後に定義
   ```

これらは P2-SELFHOST-S1 の備考で既に「parser 未対応構文」として挙がっている（ParseContext 再帰、Union forward ref）。

## 影響範囲

- `pytra.std.json` の golden が再生成可能になる
- Go selfhost の json lane ブロッカーが解消する
- 他の `pytra.std.*` で同種の構文を使っている場合も通るようになる

## サブタスク

1. [ID: P1-PARSER-JSON-S1] parser で `type X = ...`（PEP 695 type alias）構文を処理できるようにする
2. [ID: P1-PARSER-JSON-S2] Union 内の再帰的 forward reference（`list[JsonVal]` 内の `JsonVal` 自身）を解決できるようにする
3. [ID: P1-PARSER-JSON-S3] `pytra.std.json.py` が parse → resolve → compile → optimize → link を通過することを確認
4. [ID: P1-PARSER-JSON-S4] golden 再生成 + 既存 parity 維持確認

## 受け入れ基準

1. `pytra-cli2 -parse src/pytra/std/json.py` が成功すること
2. 全段（parse → resolve → compile → optimize → link）を通過すること
3. golden が current source から再生成されていること
4. 既存 fixture / sample の parity が維持されること

## 決定ログ

- 2026-03-27: Go selfhost の json lane ブロッカーの根本原因が「pytra.std.json.py が parse 不能 → golden stale → emitter が古い情報で生成」であることを特定。emitter で stale EAST3 を吸収するのではなく、parser を修正して golden を再生成する方針を決定。
