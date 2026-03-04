# P2: 多言語 runtime の C++ 同等化（再設計版: SoT厳守 + 生成優先）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-RUNTIME-PARITY-CPP-02`

背景:
- 旧P2（`P2-RUNTIME-PARITY-CPP-01`）は「同等化」を急ぐあまり、runtime 実装責務と生成責務の境界が曖昧になり、実装方針に誤りが混入した。
- 具体的には、pure Python 正本からの機械生成を優先すべき箇所で、言語別に手書き実装・特別命名・monolithic 埋め込みが発生しやすい状態だった。
- また、emitter がライブラリ関数名を文字列比較で直接分岐する経路が残り、IR 解決責務の逸脱が再発した。

目的:
- C++ runtime との API 契約同等化を維持しつつ、実装方法を「SoT厳守」「生成優先」「責務分離」に再定義する。
- runtime 同等化を、設計ルール + 静的ガード + parity 回帰で再発不能な形へ固定する。

対象:
- `src/runtime/<lang>/{pytra-core,pytra-gen}/`
- `src/pytra/{std,utils}/`（正本モジュール）
- `src/backends/*/emitter/*.py`（runtime 呼び出し経路）
- `tools/`（監査・生成・parity・CI導線）

非対象:
- C++ runtime 自体の大規模再設計
- EAST 仕様全面刷新
- 一括全言語移行（段階導入）

## 注意事項（必読）

以下は「推奨」ではなく必須ルール:

1. `src/pytra/std/*` / `src/pytra/utils/*` の pure Python 実装は正本（SoT）とし、対応機能を他言語で手書き再実装しない。
2. SoT 由来コードは必ず `src/runtime/<lang>/pytra-gen/` に配置し、`pytra-core` へ混在させない。
3. SoT 由来ファイル名は機械的素通し命名（例: `png.py -> png.<ext>`, `gif.py -> gif.<ext>`）を原則とし、helper 名の特別命名を禁止する。
4. `pytra-core` には言語依存の基盤処理のみを置く。SoT で表現可能な API は `pytra-gen` へ寄せる。
5. emitter で `callee_name == "..."` / `attr_name == "..."` による `pytra.std.*` / `pytra.utils.*` 関数名の直書き分岐を禁止する。
6. runtime/stdlib 呼び出しの解決責務は lower/IR 側に置く。emitter は解決済みノード（`runtime_call` 系）を描画するだけに限定する。
7. compiler/backends で Python 標準 `ast` モジュールに依存しない（selfhost 制約）。
8. `pytra-gen` の生成物には `source:` と `generated-by:` marker を必須化し、監査で fail-fast する。
9. parity 実行前に artifact を必ず掃除し、stdout だけでなく artifact サイズ/CRC32 も検証する。

## 受け入れ基準

- 旧P2（`P2-RUNTIME-PARITY-CPP-01`）は TODO 未完了一覧から除去され、新IDへ置換されている。
- 新P2の実施に必要な禁止事項が文書化され、検査可能な形（スクリプト/CI）で管理される。
- `pytra-gen` の命名・配置・marker に関する監査が全対象言語で通る。
- 非C++ emitter の runtime 呼び出し経路で、ライブラリ関数名直書き分岐が段階撤去される。
- parity 回帰（artifact サイズ/CRC32 含む）で runtime 差由来 fail が追跡可能になる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/audit_image_runtime_sot.py --fail-on-core-mix --fail-on-gen-markers --fail-on-non-compliant`
- `python3 tools/check_emitter_runtimecall_guardrails.py`
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --ignore-unstable-stdout`

## 分解

- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-01] 旧P2（`P2-RUNTIME-PARITY-CPP-01`）を TODO 未完了一覧から削除し、新P2へ置換する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-02] SoT/pytra-core/pytra-gen の責務境界を `docs/ja/spec` に追記し、禁止事項を固定する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S1-03] 対象モジュール（`std/utils`）の「生成必須 / core許可」分類表を作成する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-01] `pytra-gen` 命名規約（素通し命名）違反を検知する静的チェックを追加する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-02] SoT marker（`source/generated-by`）と配置違反（core混在）チェックを強化し、CIへ統合する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S2-03] `pytra-core` 内の SoT 再実装痕跡を棚卸しし、`pytra-gen` 移管計画へ反映する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-01] Java を先行対象として、runtime API 呼び出しを IR 解決経路へ統一（emitter 直書き撤去）する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-02] Java 以外の非C++ backend（`cs/js/ts/go/rs/swift/kotlin/ruby/lua/scala/php/nim`）へ同方針を展開する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S3-03] emitter 禁止ルール（ライブラリ名直書き）を lint 化し、PR/CI で fail-fast する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-01] 全対象言語で sample parity（artifact size+CRC32）を再実施し、差分を固定する。
- [ ] [ID: P2-RUNTIME-PARITY-CPP-02-S4-02] ルール違反の再発時に即検知できる運用手順（ローカル/CI）を `docs/ja/how-to-use` と `docs/en/how-to-use` に反映する。

決定ログ:
- 2026-03-05: ユーザー指示により、旧P2を破棄し、SoT厳守・生成優先・責務分離を前提とする再設計版へ置換した。
