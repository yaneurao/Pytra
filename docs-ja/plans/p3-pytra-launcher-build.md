# TASK GROUP: TG-P3-LAUNCHER-BUILD

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P3-LB-01`
- `docs-ja/todo/index.md` の `ID: P3-LB-01-S1`
- `docs-ja/todo/index.md` の `ID: P3-LB-01-S2`
- `docs-ja/todo/index.md` の `ID: P3-LB-01-S3`
- `docs-ja/todo/index.md` の `ID: P3-LB-01-S4`

背景:
- `P3-SD-01` は `spec-make.md` の照合作業（採用済み項目の仕様移管）として完了した。
- そのため、`./pytra --build` / `src/pytra/cli.py` / `tools/gen_makefile_from_manifest.py` は未実装のまま残っている。
- この未実装分を、草案照合タスクとは分離して実装タスクとして再登録する。

目的:
- C++ 向けに「変換 -> Makefile 生成 -> build」を `./pytra ... --target cpp --build` の 1 コマンドで実行可能にする。
- `PYTHONPATH=src` 手動設定を不要化し、実行導線を標準化する。

対象:
- `tools/gen_makefile_from_manifest.py`
- `src/pytra/cli.py`
- リポジトリ直下ランチャー `./pytra`
- `spec-make.md` / `spec-dev.md` / `spec-tools.md` の同期

非対象:
- C++ 以外の `--build` 実装
- IDE プロジェクト生成（Visual Studio / Xcode）
- `manifest.json` 契約の全面再設計

受け入れ基準:
1. `./pytra sample/py/01_mandelbrot.py --target cpp --output-dir out/mandelbrot` で multi-file 出力が生成される。  
2. `./pytra sample/py/01_mandelbrot.py --target cpp --build --output-dir out/mandelbrot` で `Makefile` 生成と build が連続実行される。  
3. `--target cpp` 以外での `--build` 指定は仕様どおりエラー終了する。  
4. `spec-make.md` の未実装注記が実装状況に同期される。  

サブタスク実行順（todo 同期）:
1. `P3-LB-01-S1`: `manifest.json` -> `Makefile` 生成スクリプトを実装する。  
2. `P3-LB-01-S2`: `src/pytra/cli.py` に `--target cpp --build` 導線を実装する。  
3. `P3-LB-01-S3`: `./pytra` ランチャーを追加し、`python3 -m pytra.cli` へ委譲する。  
4. `P3-LB-01-S4`: test と docs を同期し、回帰を固定する。  

決定ログ:
- 2026-02-24: `spec-make` のランチャー/ビルド導線が未実装のまま `todo` から外れていたため、`P3-LB-01` として低優先で再登録した。
