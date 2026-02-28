# P1: Kotlin runtime 外出し（inline helper 撤去）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-KOTLIN-RUNTIME-EXT-01`

背景:
- `sample/kotlin/*.kt` の生成コードには `fun __pytra_truthy(v: Any?): Boolean` をはじめとする runtime helper 本体が inline 出力されている。
- 既存の `P1-RUNTIME-EXT-01` は Go/Java/Swift/Ruby のみを対象として完了しており、Kotlin は対象外だった。
- Kotlin も runtime 外部化しないと、生成コード肥大化・runtime 実装重複・差し替え困難が継続する。

目的:
- Kotlin backend の生成コードから `__pytra_*` helper 本体定義を撤去し、runtime ファイル参照方式へ統一する。

対象:
- `src/hooks/kotlin/emitter/kotlin_native_emitter.py`
- `src/runtime/kotlin/pytra/`（runtime 正本の新設または整理）
- `src/py2kotlin.py`（runtime 配置導線）
- `test/unit/test_py2kotlin_smoke.py`
- `tools/check_py2kotlin_transpile.py`
- `tools/runtime_parity_check.py` の Kotlin 導線
- `sample/kotlin` 再生成

非対象:
- Kotlin backend の最適化（性能改善、式簡約など）
- sidecar 撤去済み範囲の再設計
- 他言語 backend の runtime 方式変更

受け入れ基準:
- `py2kotlin` 生成コードに `fun __pytra_truthy` を含む runtime helper 本体が inline 出力されない。
- 生成コードは runtime ファイル（例: `py_runtime.kt`）を参照してビルド/実行できる。
- `check_py2kotlin_transpile` / Kotlin smoke / parity（少なくとも `sample/18` と `--all-samples`）が非退行で通る。
- `sample/kotlin` 再生成後も inline helper が残存しない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets kotlin --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs kotlin --force`
- `rg -n \"fun __pytra_truthy\\(v: Any\\?\\): Boolean\" sample/kotlin`

決定ログ:
- 2026-02-28: ユーザー指示により、Kotlin の runtime 外出しを `P1` で新規起票した。

## 分解

- [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S1-01] Kotlin emitter の inline helper 出力一覧と runtime API 対応表を確定する。
- [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-01] Kotlin runtime 正本（`src/runtime/kotlin/pytra`）を整備し、`__pytra_*` API を外部化する。
- [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-02] Kotlin emitter から helper 本体出力を撤去し、runtime 呼び出し専用へ切り替える。
- [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-03] `py2kotlin.py` の出力導線で runtime ファイルを配置する。
- [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S3-01] `check_py2kotlin_transpile` / smoke / parity を更新し、回帰を固定する。
- [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S3-02] `sample/kotlin` 再生成で inline helper 残存ゼロを確認する。
