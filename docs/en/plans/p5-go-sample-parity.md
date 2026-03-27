<a href="../../ja/plans/p5-go-sample-parity.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p5-go-sample-parity.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p5-go-sample-parity.md`

# P5: Go sample parity

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-GO-PARITY-*`

## 背景

pytra-cli の compile → link → emit パイプライン統一後、Go backend の sample parity check を実施したところ 4/18 PASS（05, 08, 09, 17）に留まった。

`go_native_emitter.py` に `UnboundLocalError`（`_go_type` の `tn: str = tn`、`_infer_go_type` の `attr_name` スコープ不正）があり修正済み。runtime コピー（`py_runtime.go`）と `pytra-cli.py` の `go build` 全 `.go` 一括コンパイルも追加済み。

残り 14 件は emitter の transpile failed（5件）と run failed（9件）。

## 対象

- `src/toolchain/emit/go/emitter/go_native_emitter.py` — emitter バグ修正
- `src/toolchain/emit/go.py` — runtime コピー
- `src/pytra-cli.py` — Go build/run

## 非対象

- Go emitter の新規構文サポート追加（既存 sample で使われる範囲のみ）

## 受け入れ基準

- [ ] `runtime_parity_check.py --targets go` で sample/py の全 18 ケースが PASS する。

## 決定ログ

- 2026-03-21: parity check 実施、4/18 PASS で起票。`_go_type` / `_infer_go_type` の UnboundLocalError 2件を修正済み。
- 2026-03-21: VarDecl 対応、`_tuple_element_types` の UnboundLocalError 修正、`_resolved_runtime_symbol` の dotted call 修正、png/gif module rewrite 追加。8/18 PASS に改善。
- 2026-03-22: `build_import_alias_map` による stdlib 解決を実装。`math.sqrt→math.Sqrt`、`math.pi→math.Pi` を import alias map 経由で変換。Go stdlib `import "math"` の自動追加。`.east` runtime の `func main()` 除去。value の `resolved_type` fallback 追加。Go unused var `_ = name` 抑制。**13/18 PASS**。残り: 型推論不足(10,14,15,16)、パーサーバグ(18)。
