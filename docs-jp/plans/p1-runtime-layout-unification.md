# TASK GROUP: TG-P1-RUNTIME-LAYOUT

最終更新: 2026-02-23

関連 TODO:
- `docs-jp/todo.md` の `ID: P0-RUNTIME-SEP-01`（`P0-RUNTIME-SEP-01-S1` 〜 `P0-RUNTIME-SEP-01-S5`）
- `docs-jp/todo.md` の `ID: P1-RUNTIME-01`（`P1-RUNTIME-01-S1` 〜 `P1-RUNTIME-01-S3`）
- `docs-jp/todo.md` の `ID: P1-RUNTIME-02`（`P1-RUNTIME-02-S1` 〜 `P1-RUNTIME-02-S2`）
- `docs-jp/todo.md` の `ID: P1-RUNTIME-03`（`P1-RUNTIME-03-S1` 〜 `P1-RUNTIME-03-S2`）
- `docs-jp/todo.md` の `ID: P1-RUNTIME-05`（`P1-RUNTIME-05-S1` 〜 `P1-RUNTIME-05-S3`）

背景:
- 言語ごとに runtime 配置規約が分断され、保守責務と探索規則が揺れている。
- C++ runtime では生成物と手書き実装が混在し、CI での責務検証が難しい。

目的:
- `src/runtime/<lang>/pytra/` へ配置規約を統一し、runtime 資産の責務境界を揃える。
- C++ runtime では生成層と手書き層を上位フォルダで分離し、将来の多言語展開で再利用可能な運用を確立する。

対象:
- C++: `src/runtime/cpp/pytra/` の「生成物 / 手書き / 入口フォワーダー」分離（`pytra-gen` / `pytra-core`）
- Rust: `src/rs_module/` から `src/runtime/rs/pytra/` への段階移行
- 他言語: `src/*_module/` 依存資産の `src/runtime/<lang>/pytra/` への移行計画
- `py2*` / hooks の解決パス統一

非対象:
- 各言語 runtime の機能追加そのもの

受け入れ基準:
- ランタイム参照先が `src/runtime/<lang>/pytra/` へ統一される。
- C++ runtime で `pytra-gen`（生成専用）と `pytra-core`（手書き専用）が CI で検証される。
- `src/*_module/` 直下への新規 runtime 追加が止まる。

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- 言語別 smoke tests（`test/unit/test_py2*_smoke.py`）

サブタスク実行順（todo 同期）:

1. `P0-RUNTIME-SEP-01`（C++ runtime 起源分離）
   - `P0-RUNTIME-SEP-01-S1`: `src/runtime/cpp/pytra/` の全ファイルを「生成物 / 手書き / 入口」に分類する（結果: `docs-jp/plans/p1-runtime-layout-unification-inventory.md`）。
   - `P0-RUNTIME-SEP-01-S2`: `src/runtime/cpp/pytra-gen/` と `src/runtime/cpp/pytra-core/` の最小構成を作る。
   - `P0-RUNTIME-SEP-01-S3`: 自動生成ファイルを `pytra-gen` へ段階移動する。
   - `P0-RUNTIME-SEP-01-S4`: 手書きファイル（`-impl` 含む）を `pytra-core` へ段階移動する。
   - `P0-RUNTIME-SEP-01-S5`: CI ガード（`AUTO-GENERATED` 必須/禁止）を導入する。
2. `P1-RUNTIME-01`（Rust 配置統一）
   - `P1-RUNTIME-01-S1`: `src/rs_module/` の責務マップを作る。
   - `P1-RUNTIME-01-S2`: `src/runtime/rs/pytra/` へ段階移動し、互換レイヤを維持する。
   - `P1-RUNTIME-01-S3`: 回帰確認後に `src/rs_module/` 依存を縮退する。
3. `P1-RUNTIME-02`（Rust 解決パス更新）
   - `P1-RUNTIME-02-S1`: `py2rs.py` / hooks の path 解決箇所と互換仕様を確定する。
   - `P1-RUNTIME-02-S2`: 新パスへ切り替え、旧パス fallback を撤去する。
4. `P1-RUNTIME-03`（`src/rs_module/` 廃止）
   - `P1-RUNTIME-03-S1`: 参照元を全件列挙し、廃止可否を確定する。
   - `P1-RUNTIME-03-S2`: 参照を置換し、`src/rs_module/` を削除する。
5. `P1-RUNTIME-05`（Rust 以外の解決パス統一）
   - `P1-RUNTIME-05-S1`: 言語ごとの現行 runtime 解決パス差分を棚卸しする。
   - `P1-RUNTIME-05-S2`: 各 `py2<lang>.py` / hooks の参照を新基準へ順次更新する。
   - `P1-RUNTIME-05-S3`: 多言語 smoke 実行後に旧パス互換レイヤを段階撤去する。

運用ルール:

1. 新規 runtime 実装（`py_runtime.*`, `pathlib.*`, `png/gif helper` など）は `src/runtime/<lang>/pytra/` 配下にのみ追加する。
2. `src/*_module/` 直下は互換レイヤ専用とし、新規実体ファイルは追加しない。
3. 互換レイヤは「移行完了後に削除する前提」の暫定資産として扱い、`todo` に撤去タスクを必ず紐付ける。
4. 例外追加が必要な場合は、同一ターンで `docs-jp/todo.md` に理由と撤去期限を記録する。

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-22: Rust 以外（C#/JS/TS/Go/Java/Swift/Kotlin）の `src/*_module/` -> `src/runtime/<lang>/pytra/` 移行計画（資産マップ + 段階手順）を追加。
- 2026-02-22: `src/*_module/` 直下に新規 runtime 実体を追加しない運用ルールを明文化。
- 2026-02-23: docs-jp/todo.md の親子 ID 分割（-S*）へ同期し、P0-RUNTIME-SEP-01 を含む実行順を明示した。
- 2026-02-23: `P0-RUNTIME-SEP-01-S1` を実施し、`src/runtime/cpp/pytra/` 全57ファイルの分類台帳を `docs-jp/plans/p1-runtime-layout-unification-inventory.md` として追加した（`generated=38`, `handwritten=19`, `entry_forwarder=0`）。
