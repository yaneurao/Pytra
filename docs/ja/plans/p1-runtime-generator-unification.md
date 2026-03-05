# P1: runtime生成導線の単一化（`pytra-cli` / `py2x` 正規経路へ統合）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RUNTIME-GEN-UNIFY-01`

背景:
- 現在 `tools/` には、canonical source（`src/pytra/std/*.py`, `src/pytra/utils/*.py`）を各言語へ変換するための特殊スクリプトが複数存在する。
  - `tools/gen_image_runtime_from_canonical.py`
  - `tools/gen_java_std_runtime_from_canonical.py`
  - `tools/gen_cs_image_runtime_from_canonical.py`
- これらは本質的に `py2x`/`pytra-cli` 呼び出しの薄いラッパであるにもかかわらず、言語別分岐・命名変換・専用後処理を内包しており、責務が backend 実装へ漏れている。
- ユーザー方針として、runtime生成は「SoTの Python 実装を正規 CLI で変換する」単一経路で運用し、言語特例スクリプトを増やさないことが必要。

目的:
- runtime生成導線を `pytra-cli` / `py2x` 正規経路へ統一し、言語別 ad-hoc generator を撤去する。
- 出力先/命名/marker 付与は宣言的定義（プロファイルまたは manifest）へ寄せ、ツールコード内の言語分岐を最小化する。
- CI で「特殊 generator 再導入」を fail-fast にする。

対象:
- `tools/gen_image_runtime_from_canonical.py`
- `tools/gen_java_std_runtime_from_canonical.py`
- `tools/gen_cs_image_runtime_from_canonical.py`
- runtime 生成の呼び出し元（必要な `tools/*`, `docs/*`）
- 監査系スクリプト（再導入防止ガード）

非対象:
- backend コード生成品質の改善
- runtime API の新機能追加
- selfhost 導線の再設計

受け入れ基準:
- 上記 3 スクリプトが削除され、runtime 生成は単一の汎用導線（`pytra-cli`/`py2x` + 宣言設定）で実行できる。
- 生成物の `source:` / `generated-by:` marker 契約が維持される。
- `tools/check_runtime_*` / parity / smoke の既存回帰が非退行。
- CI ガードで、言語別特殊 generator の再追加を検知して fail できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m py_compile tools/*.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/check_runtime_pytra_gen_naming.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp,java,ruby,lua,php 01_mandelbrot`

## 分解

- [ ] [ID: P1-RUNTIME-GEN-UNIFY-01-S1-01] 既存 generator 3本の責務差分（入出力、後処理、命名ルール）を棚卸しし、単一導線へ移せる要件を固定する。
- [ ] [ID: P1-RUNTIME-GEN-UNIFY-01-S1-02] runtime生成の宣言設定（対象モジュール、target、出力先、marker）を定義し、言語分岐を設定ファイルへ移す。
- [ ] [ID: P1-RUNTIME-GEN-UNIFY-01-S2-01] 汎用 generator（単一スクリプト）を実装し、`pytra-cli`/`py2x` を呼ぶ共通導線へ統合する。
- [ ] [ID: P1-RUNTIME-GEN-UNIFY-01-S2-02] 既存 3 スクリプトの呼び出し元を新導線へ置換する。
- [ ] [ID: P1-RUNTIME-GEN-UNIFY-01-S2-03] 既存 3 スクリプトを削除し、関連ドキュメントを更新する。
- [ ] [ID: P1-RUNTIME-GEN-UNIFY-01-S3-01] 再導入防止ガード（special generator 禁止）を CI に追加する。
- [ ] [ID: P1-RUNTIME-GEN-UNIFY-01-S3-02] runtime 監査 + parity 回帰を実施し、非退行を固定する。

決定ログ:
- 2026-03-05: ユーザー指示により、`tools/gen_*_from_canonical.py` の言語別特殊化は設計違反として扱い、P1で統廃合する方針を確定。
