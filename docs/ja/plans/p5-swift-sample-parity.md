# P5: Swift sample parity

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-SWIFT-PARITY-*`

## 背景

pytra-cli の compile → link → emit パイプライン統一後、Swift backend の sample parity check を実施したところ 1/18 PASS（17番のみ）。

runtime コピー（`py_runtime.swift`）を `swift.py` に追加し、`pytra-cli.py` に `swiftc` 全 `.swift` 一括コンパイルの build/run を追加済み。`sample/swift/image_runtime.swift` は `py_runtime.swift` と関数が重複するためコピー対象から除外。

残り 17 件は全て transpile failed — emitter の未実装構文が原因。

## 対象

- `src/toolchain/emit/swift/emitter/` — emitter バグ修正
- `src/toolchain/emit/swift.py` — runtime コピー
- `src/pytra-cli.py` — Swift build/run

## 非対象

- Swift emitter の新規構文サポート追加（既存 sample で使われる範囲のみ）

## 受け入れ基準

- [ ] `runtime_parity_check.py --targets swift` で sample/py の全 18 ケースが PASS する。

## 決定ログ

- 2026-03-21: parity check 実施、1/18 PASS で起票。`image_runtime.swift` の重複関数問題を回避済み（コピー除外）。
- 2026-03-21: VarDecl 対応、`_resolved_runtime_symbol` の dotted call 修正、png/gif module rewrite 追加。4/18 PASS に改善。
- 2026-03-22: `build_import_alias_map` による stdlib 解決を実装。`@main struct Main` 除去。`_native` suffix 命名規約統一。**4/18 PASS**。残り: emitter 固有バグ多数。
