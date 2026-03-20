# P0: Nim runtime 整備で `sample/` parity 全件通過

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01`

背景:
- `py2nim.py` と最小 smoke は成立したが、`sample/` 全件で parity pass した証跡は未固定。
- Nim backend は新規導入直後で、runtime API の不足や呼び出し契約ずれが残っている可能性が高い。
- `sample/` parity が不安定なままでは、Nim backend の品質指標として README 反映や最適化検討に進めない。

目的:
- `sample/py` を Nim に変換・実行し、`--ignore-unstable-stdout` 条件で parity を全件 pass させる。
- pass に必要な不足分を runtime 側中心に補完し、再発検知まで固定する。

対象:
- `src/runtime/nim/pytra/py_runtime.nim`
- `src/toolchain/emit/nim/emitter/nim_native_emitter.py`（runtime 契約接続に必要な範囲）
- `tools/runtime_parity_check.py` 実行導線（必要時のみ最小修正）
- `sample/nim/`（再生成結果）
- 必要な unit/transpile check

非対象:
- Nim backend の大規模最適化（生成品質改善の全面改修）
- 他言語 runtime の同時改修
- README ベンチマーク値更新

受け入れ基準:
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --ignore-unstable-stdout` が全件 pass。
- `python3 tools/check_py2nim_transpile.py` が pass。
- 追加/修正した runtime 契約について最小回帰（unit or check）を固定。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2nim_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --ignore-unstable-stdout`
- `python3 src/py2nim.py sample/py/<case>.py -o sample/nim/<case>.nim`（`regenerate_samples.py` は Nim 未対応）

## 分解

- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S1-01] `sample` 全件に対する Nim parity ベースラインを取得し、失敗ケース一覧と失敗カテゴリ（compile/runtime/output mismatch）を確定する。
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S1-02] 失敗ケースごとに runtime API 不足・契約不整合・emitter 側問題を切り分け、修正優先順を確定する。
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S2-01] `py_runtime.nim` の不足 API（型変換/コレクション/文字列/時刻/画像補助）を fail-closed で補完する。
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S2-02] emitter と runtime の呼び出し契約（関数名・引数順・戻り値型）を整合し、必要な出力修正を行う。
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S2-03] case 固有の崩れ（例: `sample/18` 相当の tokenizer/構文要素）を最小修正で解消する。
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-01] `sample/nim` を再生成し、Nim 実行でのエラー（transpile/compile/runtime）を全件解消する。
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-02] `runtime_parity_check --targets nim --ignore-unstable-stdout` 全件 pass を確認し、結果を記録する。
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-03] `check_py2nim_transpile` と関連回帰を実行し、非退行を確認する。

決定ログ:
- 2026-03-03: ユーザー指示により、Nim runtime 整備と `sample/` parity 全件通過を P0 として起票。
- 2026-03-03: `runtime_parity_check --case-root sample --targets nim --ignore-unstable-stdout` のベースラインで `cases=18 pass=18 fail=0` を確認し、失敗ケース分類（runtime不足/契約不整合/emitter問題）は空であることを確定。
- 2026-03-03: `tools/regenerate_samples.py --langs nim --force` は `unknown language(s): nim` で未対応だったため、`python3 src/py2nim.py sample/py/*.py -o sample/nim/*.nim` の手動再生成導線で `sample/nim` を更新（18ケース + `py_runtime.nim`）。
- 2026-03-03: 再生成後の parity 再実行で `cases=18 pass=18 fail=0` を確認し、`python3 tools/check_py2nim_transpile.py` も `checked=7 ok=7 fail=0` で通過。追加コード修正なしで受け入れ基準を満たした。
