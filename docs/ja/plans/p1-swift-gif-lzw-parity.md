<a href="../../en/plans/p1-swift-gif-lzw-parity.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: Swift sample parity（EAST3 生成 utils 有効化）

## 背景

Swift backend の sample/py 05-16（GIF 出力）が parity FAIL。

## 調査結果

### EAST3 生成版が動作しない根本原因: §10 コンテナ参照セマンティクス未実装

EAST3 生成の `utils/png.swift` / `utils/gif.swift` は `_png_append_list(dst, src)` のような関数内コンテナ変更パターンを多用する。しかし Swift の `[Any]` は値型であるため、関数内での `.append()` は呼び出し元に反映されない。

```swift
// EAST3 生成コード（動作しない）
func _png_append_list(_ dst: Any, _ src: Any) {
    var dst: [Any] = __pytra_as_list(dst)  // ← ローカルコピー
    dst.append(...)  // ← コピーにのみ反映、呼び出し元は変わらない
}
```

これは spec-emitter-guide.md §10 が禁止する「値型コンテナのラッパーなし直接使用」に該当。

### 対処の選択肢

1. **§10 準拠: 参照型ラッパー `class PyList` 導入** — 全 `[Any]` を `PyList` に置換。emitter 全体のリスト処理を変更。根本解決だが大規模。
2. **暫定: hand-written `utils/png.swift` / `utils/gif.swift` を `src/runtime/swift/` に配置** — EAST3 生成をスキップし、Swift ネイティブの `Data` 型で画像バイナリを構築。spec §6 からの逸脱だが §10 解決まで現実的。

## 完了済みの改善

- extern_var_v1 対応（pi, e の __native 委譲）
- int32 / uint* / byte 型マッピング追加
- PyFile クラス追加（ファイル I/O）
- open() → __pytra_open() マッピング
- let パラメータのコンテナ型 var 化
- pytra.utils.* スキップ解除（コンパイルは通るが §10 問題で実行時不正）

## 現状

- PNG 01-04: py_runtime スタブ利用で 4/4 PASS だったが、スタブ除去後は §10 問題で FAIL
- GIF 05-16: 0/12 FAIL
- テキスト 17-18: union type 非サポート（既存制限）

## ブロッカー

**§10 コンテナ参照セマンティクス（`class PyList` 導入）** が前提タスク。これなしでは EAST3 生成の画像コードは Swift で動作しない。

## 決定ログ

- 2026-03-23: 計画書作成。
- 2026-03-23: 方針修正。手書き GIF → EAST3 生成版有効化に変更。
- 2026-03-23: §10 コンテナ参照セマンティクス未実装がブロッカーであることを確認。EAST3 生成の utils/png.swift は値型コンテナ問題でバイナリ出力が空になる。pytra.utils.* スキップを一旦戻し、py_runtime スタブの PNG を維持。GIF parity は §10 解決待ち。
