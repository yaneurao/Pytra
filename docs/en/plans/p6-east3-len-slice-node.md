<a href="../../ja/plans/p6-east3-len-slice-node.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p6-east3-len-slice-node.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p6-east3-len-slice-node.md`

# P6: py_len / py_slice を EAST3 IR ノード化し py_runtime.h から除去

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-EAST3-LEN-SLICE-NODE-01`

## 背景

`py_len` / `py_slice` は `py_runtime.h` に実装され、C++ emitter が文字列リテラルとして直接 emit している。

- `py_len(v)` — リスト・文字列等の長さを返す。各言語に同等機能がある（Go: `len(v)`, JS: `v.length`, Rust: `v.len()` 等）。
- `py_slice(v, lo, up)` — スライス抽出。各言語で構文・API が大きく異なる（Python: `v[lo:up]`, Go: `v[lo:up]`, JS: `v.slice(lo, up)`, Rust: `&v[lo..up]` 等）。

EAST3 IR には現時点でこれら専用のノードが存在せず、emitter が `py_len(...)` / `py_slice(...)` を文字列で直接挿入している。

問題：
- 非 C++ バックエンドが `len()` / スライスを生成する際に `py_runtime.h` と等価なヘルパを独自に持つか、別の慣習で実装する必要がある。
- EAST3 IR レベルに意味論が記録されていないため、最適化パスや静的解析が介入できない。

## 目的

- EAST3 IR に `Len` / `Slice` ノード（または既存 `CallBuiltIn` 相当）を追加する。
- C++ emitter はそれらのノードからインライン式または最小限の C++ コードを生成し、`py_len()` / `py_slice()` の直接呼び出しを排除する。
- `py_len` / `py_slice` を `py_runtime.h` から削除する（または generated 層に移動する）。

## 対象

- `src/toolchain/emit/cpp/emitter/`（`py_len` / `py_slice` emit 箇所）
- EAST3 IR 定義（ノード追加 or 既存 CallBuiltIn の活用）
- `src/runtime/cpp/native/core/py_runtime.h`（除去対象関数）
- `test/unit/toolchain/emit/cpp/`（回帰テスト）

## 非対象

- 非 C++ バックエンドへの `Len` / `Slice` ノード実装（基盤整備のみ）
- `py_list_slice_copy` の細かい境界クランプ挙動の再設計（既存挙動を維持）
- `str` に対するスライスの文字コード対応（現状維持）

## 受け入れ基準

- 生成 C++ に `py_len(...)` / `py_slice(...)` の直接呼び出しが残らない（生成コード内）。
- 上記関数が `py_runtime.h` から削除されている（または generated 層に限定移動）。
- スライスの境界クランプ（`lo < 0`/`up > n` 等のクリッピング）が維持されている。
- fixture 3/3・sample 18/18 pass、selfhost diff mismatches=0。

## 子タスク（案）

- [ ] [ID: P6-EAST3-LEN-SLICE-NODE-01-S1-01] `py_len` / `py_slice` の emit 経路を棚卸しし、EAST3 IR ノード化の設計方針（新規ノード追加 vs 既存 CallBuiltIn 活用）を決定する。
- [ ] [ID: P6-EAST3-LEN-SLICE-NODE-01-S2-01] `py_len` の IR ノード化と C++ emitter 側の対応を実装する。
- [ ] [ID: P6-EAST3-LEN-SLICE-NODE-01-S2-02] `py_slice` の IR ノード化と C++ emitter 側の対応を実装する。
- [ ] [ID: P6-EAST3-LEN-SLICE-NODE-01-S2-03] `py_runtime.h` から `py_len` / `py_slice` / `py_list_slice_copy` を削除し、コンパイルが通ることを確認する。
- [ ] [ID: P6-EAST3-LEN-SLICE-NODE-01-S3-01] fixture / sample / selfhost で非退行を確認する。

## 決定ログ

- 2026-03-18: py_runtime.h 縮小・多言語対応容易化の調査において `py_len` / `py_slice` が EAST3 IR ノードを持たず文字列 emit されていることを確認し起票。P6-CPP-LIST-MUT-IR-BYPASS-FIX-01 の後に着手予定。
- 2026-03-18: 実装完了。py_div アプローチを踏襲し object 境界は fallback 維持。py_len は base_ops.h へ移動（py_runtime.h は include 経由で再公開）。py_slice の list 版は emitter が py_list_slice_copy を直接 emit するため py_runtime.h から除去。str 版は py_str_slice にリネームし base_ops.h へ移動。truthy_len_expr を CppEmitter でオーバーライドし `!X.empty()` 生成。str/bytes の py_len → .size() 変換は _render_container_size_expr 経由。生成済み C++ ファイル（string_ops.cpp / json.cpp / re.cpp / gif.cpp / argparse.cpp）を手動更新。selfhost mismatches=0 確認済み。cpp 0.581.3。
