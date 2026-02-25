# P3 非C++ emitter の EAST3 直結化と EAST2 互換撤去

最終更新: 2026-02-25

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P3-EAST3-ONLY-01`

背景:
- 非C++ 8ターゲット（`rs/cs/js/ts/go/java/swift/kotlin`）は、既定で `EAST3` を読み込む一方で `east3_legacy_compat` による legacy 互換変換を経由している。
- さらに `--east-stage 2` 互換モードと `load_east_document_compat` 経路が残っており、コード経路と回帰面積を増やしている。
- `EAST3` を唯一の契約に統一し、互換層を撤去してメンテナンス面積を縮小する。

目的:
- 非C++ 8ターゲットを `EAST3` 直結へ移行し、`EAST2` 互換経路を廃止する。

対象:
- CLI: `src/py2{rs,cs,js,ts,go,java,swift,kotlin}.py`
- emitter: `src/hooks/{rs,cs,js,ts,go,java,swift,kotlin}/emitter/*.py`
- compiler shared: `src/pytra/compiler/transpile_cli.py`, `src/pytra/compiler/east_parts/east3_legacy_compat.py`
- tests/docs: `test/unit/test_py2*_smoke.py`, `tools/check_py2*_transpile.py`, `docs-ja/plans/plan-east123-migration.md` ほか関連仕様

非対象:
- C++ backend の `EAST3` 主経路変更。
- 性能最適化のみを目的としたリファクタ。
- sample プログラム内容自体の変更。

受け入れ基準:
- `py2{rs,cs,js,ts,go,java,swift,kotlin}` が `EAST3` のみを受け付ける（`--east-stage 2` 非対応化またはオプション削除）。
- `normalize_east3_to_legacy` への参照が 0 件である。
- `load_east_document_compat` の非C++ CLI からの参照が 0 件である。
- `east3_legacy_compat.py` を削除し、回帰テスト（smoke/check/parity）が通る。

決定ログ:
- 2026-02-25: 低優先タスクとして追加。`EAST3` 直結を最終形にし、`EAST2` 互換と legacy 変換の撤去を段階移行で進める方針を確定。

## 分解

- [ ] [ID: P3-EAST3-ONLY-01-S1] 仕様/CLI 契約を `EAST3` のみに更新し、`--east-stage 2` の互換警告テストを廃止して非対応エラー基準へ移行する。
- [ ] [ID: P3-EAST3-ONLY-01-S2] `js_emitter` を `EAST3` ノード直処理へ移行し、`js/ts/go/java/swift/kotlin` で `east3_legacy_compat` 非依存の生成経路を成立させる。
- [ ] [ID: P3-EAST3-ONLY-01-S3] `rs_emitter` の `EAST3` 直処理を実装し、legacy 形状依存（`For/ForRange` 前提など）を撤去する。
- [ ] [ID: P3-EAST3-ONLY-01-S4] `cs_emitter` の `EAST3` 直処理を実装し、legacy 形状依存を撤去する。
- [ ] [ID: P3-EAST3-ONLY-01-S5] 8本 CLI から `load_east_document_compat` / `normalize_east3_to_legacy` 依存を削除し、`east3_legacy_compat.py` を削除する。
- [ ] [ID: P3-EAST3-ONLY-01-S6] ドキュメント/仕様（`docs-ja/plans/plan-east123-migration.md` ほか）から `stage=2 互換` 前提を撤去して `EAST3 only` を明記する。
- [ ] [ID: P3-EAST3-ONLY-01-S7] 回帰検証（`test_py2*_smoke`, `check_py2*_transpile`, `runtime_parity_check --case-root sample --all-samples`）を通し、8ターゲットのゴールデン整合を維持する。
