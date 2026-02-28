# P0: Ruby 画像出力 runtime 実装とバイト parity 回復

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUBY-IMAGE-PARITY-01`

背景:
- `sample/ruby/01_mandelbrot.rb` は画像保存箇所で `__pytra_noop(...)` を呼んでおり、PNG を実際には出力していない。
- `src/runtime/ruby/pytra/py_runtime.rb` の `__pytra_noop` は no-op 実装であり、画像ファイルが生成されない。
- その結果、`runtime_parity_check`（stdout 比較）では pass でも、画像アーティファクトの parity は未成立。

目的:
- Ruby backend で PNG/GIF を実際に書き出せる runtime を実装し、`sample/01` を含む画像系サンプルで Python 実行結果とのバイト一致を回復する。

対象:
- `src/runtime/ruby/pytra/py_runtime.rb`（画像出力 helper の実体実装）
- Ruby emitter の画像保存呼び出し lower（`__pytra_noop` 経路の撤去）
- `sample/ruby` 再生成
- 画像アーティファクト parity 検証導線（少なくとも `sample/01` PNG）

非対象:
- Ruby backend 全体の性能最適化
- 画像以外の runtime helper 全面再設計
- 他言語 backend の画像 runtime 変更

受け入れ基準:
- Ruby 実行時に `sample/01` の PNG が実際に生成される。
- `sample/01` で Python 実行出力 PNG と Ruby 実行出力 PNG のバイト列が一致する。
- 代表 GIF ケース（`sample/06` など）でも Python と Ruby の GIF バイト一致（または差分理由の仕様化）が確認される。
- `runtime_parity_check --targets ruby --all-samples` が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs ruby --force`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `python3 tools/check_py2rb_transpile.py`

決定ログ:
- 2026-02-28: ユーザー指示により、Ruby 画像出力の no-op 経路を最優先（P0）で修正する計画を起票した。
- 2026-02-28: Ruby emitter の `save_gif` / `write_rgb_png` / `grayscale_palette` lower を `__pytra_noop` / `[]` から実体 runtime 呼び出しへ切替え、`save_gif` keyword（`delay_cs`/`loop`）を位置引数へ反映する実装方針を採用した。
- 2026-02-28: `src/runtime/ruby/pytra/py_runtime.rb` に PNG（CRC32/Adler32/zlib store）・GIF（LZW/パレット）書き出し実装を追加し、Ruby 単体で画像を生成可能にした。
- 2026-02-28: `tools/verify_ruby_sample_artifact_parity.py --samples 01_mandelbrot 06_julia_parameter_sweep` を追加実行し、PNG/GIF の Python vs Ruby バイト一致を確認した。
- 2026-02-28: `runtime_parity_check --case-root sample --targets ruby --all-samples --ignore-unstable-stdout` を実行し、18/18 case pass を確認した。

## 分解

- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S1-01] Ruby 画像出力経路（emitter / runtime）の現状を棚卸しし、`__pytra_noop` 依存箇所を固定する。
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S2-01] Ruby runtime に PNG 書き出し実体（Python runtime 互換）を実装する。
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S2-02] Ruby runtime に GIF 書き出し実体（Python runtime 互換）を実装する。
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S2-03] Ruby emitter の画像保存 lower を `__pytra_noop` から実体 runtime 呼び出しへ切り替える。
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S3-01] `sample/01` の PNG バイト一致検証を自動化し、回帰テストへ組み込む。
- [x] [ID: P0-RUBY-IMAGE-PARITY-01-S3-02] 代表 GIF ケースでバイト一致を検証し、`sample/ruby` 再生成と parity 非退行を確認する。
