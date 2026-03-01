# P0: `regenerate_samples.py` への Scala 追加

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-REGEN-SCALA-SUPPORT-01`

背景:
- `sample/py` から `sample/scala` を更新する際、現状は `tools/regenerate_samples.py` が `scala` を言語一覧に持たない。
- そのため Scala だけ再生成導線が分断され、`sample` 更新運用と回帰手順が他言語と不一致になっている。

目的:
- `tools/regenerate_samples.py` で `--langs scala` を正式サポートし、`sample/scala` 再生成を既存導線へ統合する。

対象:
- `tools/regenerate_samples.py`
- 必要に応じて `src/pytra/compiler/transpiler_versions.json`（version token 依存定義）
- `sample/scala` の再生成確認
- 関連 unit/smoke（必要最小限）

非対象:
- Scala emitter の機能拡張
- Scala parity の仕様変更
- 他言語 backend の再設計

受け入れ基準:
- `python3 tools/regenerate_samples.py --langs scala --force` が成功し、`sample/scala/*.scala` を一括再生成できること。
- `--langs` 検証で `scala` が invalid 扱いされないこと。
- version token 判定に `scala` が組み込まれ、非強制実行時の skip/regen 判定が機能すること。
- 既存言語（少なくとも `cpp` と `go`）の導線に非退行がないこと。

確認コマンド（予定）:
- `python3 tools/regenerate_samples.py --langs scala --force`
- `python3 tools/regenerate_samples.py --langs scala --dry-run --verbose`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala_smoke.py' -v`

分解:
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S1-01] `LANG_CONFIGS` / `LANG_VERSION_DEPENDENCIES` / `--langs` default を棚卸しし、Scala 追加方針を確定する。
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S2-01] `tools/regenerate_samples.py` に `scala` 設定を追加し、CLI から `--langs scala` を受理できるようにする。
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S2-02] version token 判定に `scala` を接続し、cache ベースの skip/regen 判定を有効化する。
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S3-01] `sample/scala` を再生成し、生成差分が期待どおり更新されることを確認する。
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S3-02] smoke/check を実行し、非退行を確認する。

決定ログ:
- 2026-03-02: ユーザー指示により、`regenerate_samples.py` の Scala 非対応を P0 で優先修正する方針を確定した。
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S1-01] `LANG_CONFIGS`/`LANG_VERSION_DEPENDENCIES`/`--langs` 既定値に `scala` が未接続であることを確認し、`src/py2scala.py` + `sample/scala/*.scala` + `transpiler_versions.json.languages.scala` を追加接続する方針で確定した。
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S2-01] `tools/regenerate_samples.py` に `scala` 設定（`cli=src/py2scala.py`, `out_dir=sample/scala`, `ext=.scala`）と `--langs` 既定値を追加し、`unknown language(s): scala` を解消した。
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S2-02] `LANG_VERSION_DEPENDENCIES` に `scala` を追加し、`src/pytra/compiler/transpiler_versions.json` に `languages.scala=0.1.0` を追加して version token 判定を有効化した。
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S3-01] `python3 tools/regenerate_samples.py --langs scala --force` を実行し、`summary: total=18 skip=0 regen=18 fail=0` を確認した。
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S3-02] `--langs scala --dry-run --verbose`（18件 skip）と `--langs cpp,go --dry-run`（fail=0）を確認し、`test_py2scala_smoke`（17件）も通過した。
