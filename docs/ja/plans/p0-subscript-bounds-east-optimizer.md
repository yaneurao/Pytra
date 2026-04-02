# P0-SUBSCRIPT-BOUNDS: negative-index-mode / bounds-check-mode を EAST optimizer に移管する

最終更新: 2026-04-02

## 背景

旧 toolchain の emitter に `--negative-index-mode`（`always` / `const_only` / `off`）と `--bounds-check-mode`（`always` / `debug` / `off`）があった。旧デフォルトは `const_only` + `off`。

toolchain2 ではこのオプションが移行されておらず、C++ runtime の `py_list_at_ref` が全 `Subscript` アクセスで常に負数正規化 + bounds check を行っている。1600x1200 PNG 書き出しで数百万回の hot loop indexing が遅い直接原因。

### 設計上の問題

旧 toolchain ではこのオプションが **emitter のオプション** だった。これは設計として正しくない:
- emitter はオプションの存在を知るべきではない
- 最適化判断は EAST optimizer の責務
- emitter は EAST3 のメタデータを写像するだけ

## 方針

1. `--negative-index-mode` / `--bounds-check-mode` を EAST optimizer のオプションとして復活させる
2. optimizer が `Subscript` ノードにメタデータを付与する:
   - `meta.subscript_access_v1.negative_index: "normalize" | "skip"` — 負数正規化の要否
   - `meta.subscript_access_v1.bounds_check: "full" | "off"` — 範囲チェックの要否
3. optimizer の判定ロジック:
   - `ForRange` ループ変数による添字 → `negative_index: "skip"`, `bounds_check: "off"`
   - 定数リテラル非負 → `negative_index: "skip"`
   - 負数リテラル（`a[-1]`）→ `negative_index: "normalize"`
   - それ以外 → オプション設定に従う
4. emitter はメタデータを見て runtime API を選ぶだけ:
   - `bounds_check: "full"` → `py_list_at_ref`（既存、full check）
   - `bounds_check: "off"` → 直接 `operator[]` / 言語のネイティブ添字アクセス
5. emitter は `--negative-index-mode` / `--bounds-check-mode` のオプション自体を知らない

## 対象

- `src/toolchain2/optimize/` — optimizer にオプションとメタデータ付与ロジックを追加
- `docs/ja/spec/spec-east.md` — `meta.subscript_access_v1` スキーマ定義
- `docs/ja/spec/spec-east3-optimizer.md` — optimizer パス仕様に追記
- `src/toolchain2/emit/cpp/emitter.py` — メタデータに基づく API 選択（emitter はオプションを知らない）
- 全 emitter — 同上

## 非対象

- emitter にオプションを生やすこと（禁止）
- `src/pytra/utils/png.py` の正本改善（別タスク、ただし相乗効果あり）

## 既存ドキュメントの状況

- `docs/en/spec/spec-options.md` に旧 emitter オプションとして `--negative-index-mode` / `--bounds-check-mode` / `-O0`~`-O3` が記載されている
- `docs/ja/spec/archive/20260328-spec-options.md` に日本語版（archive 済み）
- いずれも「emitter のオプション」として書かれており、EAST optimizer のオプションとしての記述はない
- `docs/ja/tutorial/transpiler-cli.md` にも `--bounds-check-mode` が emitter CLI オプションとして記載
- `docs/ja/tutorial/advanced-usage.md` に `-O3` が記載
- toolchain2 にはこれらが一切移行されていない
- spec-east.md / spec-east3-optimizer.md にも該当記述なし

## 受け入れ基準

- [ ] EAST optimizer に `--negative-index-mode` / `--bounds-check-mode` オプションがある
- [ ] `Subscript` ノードに `meta.subscript_access_v1` が付与される
- [ ] emitter はメタデータのみを参照し、オプション自体を知らない
- [ ] C++ sample 01 (mandelbrot) の実行時間が Rust/Go と同等レベルに改善される
- [ ] fixture + sample parity に回帰がない
- [ ] spec-options.md を更新し、EAST optimizer のオプションとして再定義する（emitter オプションの記述を削除）
- [ ] spec-east3-optimizer.md に `subscript_access_v1` パスを追記する
- [ ] `docs/ja/tutorial/transpiler-cli.md` のオプション欄を更新する（emitter オプションではなく EAST optimizer オプションとして記述）
- [ ] `docs/ja/tutorial/advanced-usage.md` の `-O3` 記述を更新する

## サブタスク

1. [ ] [ID: P0-SUB-BOUNDS-S1] `meta.subscript_access_v1` スキーマを spec-east.md に定義する
2. [ ] [ID: P0-SUB-BOUNDS-S2] EAST optimizer に `--negative-index-mode` / `--bounds-check-mode` を追加し、`Subscript` ノードにメタデータを付与するパスを実装する
3. [ ] [ID: P0-SUB-BOUNDS-S3] C++ emitter でメタデータに基づく direct index / py_list_at_ref の分岐を実装する
4. [ ] [ID: P0-SUB-BOUNDS-S4] sample 01 (mandelbrot) の C++ 実行時間が改善されることを確認する
5. [ ] [ID: P0-SUB-BOUNDS-S5] fixture + sample + stdlib parity に回帰がないことを確認する

## 決定ログ

- 2026-04-02: C++ sample 01 が Python と同等（12.8s vs 34.9s、Rust 1.9s）と遅い原因を調査。PNG runtime の `py_list_at_ref` が毎回 bounds check + 負数正規化していることが根本原因。旧 toolchain では `bounds_check_mode=off` がデフォルトだったが toolchain2 に未移行。emitter のオプションではなく EAST optimizer の責務として再設計する方針で起票。
