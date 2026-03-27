<a href="../../en/plans/p1-emit-go-parity.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-EMIT-GO-PARITY: Go emitter の compile + run parity 修正

最終更新: 2026-03-26
ステータス: 着手中

## 背景

Go emitter は fixture 132 + sample 18 の emit に成功しているが、生成された Go コードが `go run` で正しく動作するか（Python と stdout 一致するか）は未検証だった。parity テストの完了条件は「emit + compile + run + stdout 一致」（emitter guide §13）。

現状の問題:
- list/dict comprehension がプレースホルダー（`nil /* list comprehension */`）のまま
- `pytra/utils/png.py` / `gif.py` のパイプライン自動変換が未完（with 文、bytearray 対応等）
- resolve が一部の型情報を欠落しており emitter がワークアラウンドしていた（P1-SPEC-CONFORM で修正中）

## 対象

### Go emitter 修正

- `toolchain2/emit/go/emitter.py`
- `src/runtime/go/mapping.json`

### EAST 修正（resolve/compile）

emitter から型推論・cast 追加を除去するために、前段で必要な情報を確定させる:
- integer promotion cast の挿入（spec-east2.md §2.5、resolve 実装済み）
- `write_text` 等のメソッド呼び出しを BuiltinCall に lowering（resolve）
- with 文のパーサー対応（parser）
- bytearray の型伝播改善（resolve）

### runtime 配置

- `src/runtime/go/built_in/py_runtime.go` — built-in 関数
- `src/runtime/go/std/` — stdlib ヘルパー
- `src/runtime/go/mapping.json` — runtime_call 写像
- `src/runtime/go/utils/` は手書き禁止（emitter guide）。`pytra/utils/{png,gif}.py` はパイプラインが自動変換する

## 必読

- [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md) — §1.1 禁止事項、§12.4 cast 判定、§13 parity 完了条件
- [docs/ja/spec/spec-runtime-mapping.md](../spec/spec-runtime-mapping.md) — mapping.json フォーマット
- [docs/ja/plans/plan-pipeline-redesign.md](plan-pipeline-redesign.md) — §3.3 runtime 配置ルール、§3.4 命名ルール

## 禁止事項（emitter guide §1.1）

- emitter で cast を追加しない。EAST に cast がないなら resolve のバグ
- emitter で変数の型を変更しない
- emitter で for-range のループ変数の型を変更しない
- emitter で mapping にない名前変換をハードコードしない
- `runtime/go/utils/` に手書きファイルを置かない（パイプライン自動変換のみ）

EAST の情報が不足している場合は emitter にワークアラウンドを書くのではなく、resolve/compile を修正すること。

## 受け入れ基準

1. fixture 132 件で `go run` + stdout 一致
2. sample 18 件で `go run` + stdout 一致（PNG/GIF artifact の CRC32 一致を含む）
3. emitter に型推論・cast 追加・ハードコードモジュール判定がない
4. `runtime/go/utils/` に手書きファイルがない
