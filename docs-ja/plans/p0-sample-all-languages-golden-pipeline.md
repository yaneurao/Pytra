# P0 サンプル全言語ゴールデン一致パイプライン

最終更新: 2026-02-25

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-SAMPLE-GOLDEN-ALL-01` 〜 `P0-SAMPLE-GOLDEN-ALL-01-S8`

背景:
- `sample/py` の18件（`01_`〜`18_`）はゴールデンベースラインを持つが、検証がC++中心の経路に偏り、他言語では未完了のまま残っている。
- 全言語で、変換結果の `コンパイル`/`実行`/`ゴールデン比較` が同一条件で成立していないため、言語別に回帰を積み上げると修正の優先順位が崩れやすい。
- `docs-ja/todo` 運用上、変換器変更時の最終受け入れ条件は「未完了P0なし」「全言語全ケースの green」を同時に満たす状態に統一したい。

対象:
- `sample/py` の全サンプル（`01_mandelbrot` 〜 `18_mini_language_interpreter`）
- ターゲット言語: `cpp, rs, cs, js, ts, go, java, swift, kotlin`
- サンプル出力（stdoutと生成物）を `sample/golden/manifest.json` と比較

非対象:
- 新規サンプル追加・削除（今回のゴールデン整合運用外）
- runtime の根本リファクタ（別タスクで分離）
- `sample` README の表現調整（差分検証後に別タスクで実施）

受け入れ条件:
- 各言語について18件全てで `compile -> run -> 比較` が通る。
- 比較は `golden` と stdout 正規化（`normalize_stdout_for_compare`）と artifact hash/size が一致。
- `tools/runtime_parity_check.py` + `tools/verify_sample_outputs.py` が、実行可能な言語で全件NG=0で終了。
- ターゲット言語ごとの残件は、`docs-ja/plans/p0-sample-all-languages-golden-pipeline.md` に失敗カテゴリ（変換/コンパイル/実行/比較）と再試行条件を残す。

方針:
1. 事前整備
   - `sample/py` 全件と `sample/golden/manifest.json` の突合し、対象リストを固定。
   - 全言語で共通で使うコマンドラインとワークディレクトリを `tools/runtime_parity_check.py` 側に整理。
2. C++を基準線として固定
   - 事前に C++ で 18件が完全一致する状態を再確認し、baseline を安定化。
3. 言語別に変換器修正を反復
   - 各言語で `compile -> run -> compare` を1件ずつ完走し、同一種類の失敗は同一ルールで潰す。
   - 18件完了後、次言語へ移動。
4. 横断結果の収束
   - 完了時点で失敗言語が残らないことを確認。
   - 結果を `docs-ja/todo/index.md` と `readme-ja.md` / `readme.md` の対応更新（差分が出た場合）へ接続。

子タスク分解（P0-SAMPLE-GOLDEN-ALL-01 の子）:
- `P0-SAMPLE-GOLDEN-ALL-01-S1`: 全件・全言語の検証スコープ確定（サンプル18件、言語9件、比較ルール）
- `P0-SAMPLE-GOLDEN-ALL-01-S2`: runtime parity 実行フローを全言語実行前提（toolchain要件・失敗分類）に整備
- `P0-SAMPLE-GOLDEN-ALL-01-S3`: `cpp` 18件の compile/run/compare 完全一致（ゴールデンベース固定）
- `P0-SAMPLE-GOLDEN-ALL-01-S4`: `rs` 18件の compile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S5`: `cs` 18件の compile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S6`: `js/ts` 18件の transpile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S7`: `go/java/swift/kotlin` 18件の transpile/run/compare 完全一致
- `P0-SAMPLE-GOLDEN-ALL-01-S8`: 全言語集約結果を `readme-ja.md` / `readme.md` のサンプル実行状況とリンクへ反映

`P0-SAMPLE-GOLDEN-ALL-01-S1` 確定内容（2026-02-25）:
- 検証対象サンプル: `sample/py` の `01_mandelbrot` 〜 `18_mini_language_interpreter`（18件固定）。
- 検証対象言語: `cpp, rs, cs, js, ts, go, java, swift, kotlin`（9言語固定）。
- 比較ルール:
  - stdout は `normalize_stdout_for_compare`（`elapsed*`/`time_sec` 行除外）で正規化して比較する。
  - 生成 artifact は `sample/golden/manifest.json` の `suffix` / `size` / `sha256` で比較する。
  - baseline source hash（`source_sha256`）が不一致なら stale 扱いで `--refresh-golden` を要求する。
- 再現手順（共通）:
  - スコープ確認: `ls sample/py/*.py | sort`
  - parity 実行（任意言語集合）:
    `python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs,cs,js,ts,go,java,swift,kotlin 01_mandelbrot ... 18_mini_language_interpreter`
  - golden 照合（C++ baseline）:
    `python3 tools/verify_sample_outputs.py --manifest sample/golden/manifest.json`

決定ログ:
- 2026-02-25: 新規P0として追加。全言語/全件一致までを完了条件にする方針を確定。
- 2026-02-25: `P0-SAMPLE-GOLDEN-ALL-01-S1` として検証対象（18サンプル/9言語）と比較ルール（stdout 正規化 + artifact hash/size + source hash）および再現コマンドを固定した。
