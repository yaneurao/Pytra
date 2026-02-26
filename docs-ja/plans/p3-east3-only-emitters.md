# P3 非C++ emitter の EAST3 直結化と EAST2 互換撤去

最終更新: 2026-02-26

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
- 2026-02-26: `S1-S7` は粒度が大きく切り戻し単位が重いため、`S*-NN` へ細分化。1サブタスクあたり「機能実装 + 最小回帰確認」を完結単位にする。
- 2026-02-26: `S1-01` として 8本 CLI の `--east-stage 2` を警告から `parser.error` へ統一。`test/unit/test_py2{rs,cs,js,ts,go,java,swift,kotlin}_smoke.py` の stage2 警告依存を「非0終了 + エラーメッセージ期待」へ更新し、8本を実行して全通過を確認。
- 2026-02-26: `S1-02` として 8本 CLI から `load_east_document_compat` の import/call と stage2 分岐を削除し、`load_east` を `load_east3_document` 単一路線へ固定。対応 smoke 8本を再実行して全通過を確認。
- 2026-02-26: `S2-01` として `js_emitter` に `ForCore` 受理を追加し、`iter_plan=StaticRangeForPlan/RuntimeIterForPlan` を内部で `ForRange/For` へ変換して既存 emit 経路へ接続。`test_py2js_smoke.py` に ForCore 直受理回帰（range/runtime tuple target）を追加し、`test_py2js_smoke.py` + `test_py2ts_smoke.py` を実行して全通過を確認。
- 2026-02-26: `S2-02` として `js_emitter` に `ObjBool/ObjLen/ObjStr/ObjIterInit/ObjIterNext/ObjTypeId` の直接描画を実装（`pyBool/pyLen/pyStr/pyTypeId` import 収集を追加、iter/next は JS iterator 呼び出しへ lower）。`test_py2js_smoke.py` に object boundary ノード直受理回帰を追加し、`test_py2js_smoke.py` + `test_py2ts_smoke.py` を実行して全通過を確認。
- 2026-02-26: `S2-03` として `IsInstance/IsSubtype/IsSubclass` の直接描画を追加し、`PYTRA_TID_*`/型名を JS runtime 定数へ解決する `type_id` 変換と `pyIsSubtype` import 収集を実装。`test_py2js_smoke.py` に type predicate ノード直受理回帰を追加し、`test_py2js_smoke.py` + `test_py2ts_smoke.py` を実行して全通過を確認。
- 2026-02-26: `S2-04` として `Box/Unbox` を `render_expr` で直接受理し、値を透過する no-op lowering に統一。`test_py2js_smoke.py` に Box/Unbox 直受理回帰を追加し、`test_py2js_smoke.py` + `test_py2ts_smoke.py` を実行して全通過を確認。
- 2026-02-26: `S2-05` として JS/TS smoke と `check_py2{js,ts}_transpile.py` を全通し。付随して `tools/check_noncpp_east3_contract.py` の静的契約を EAST3-only（stage2 警告期待→stage2 非対応期待、compat import 禁止）へ更新し、`test_east3_cpp_bridge.py` の `py_to<int64>/py_to<bool>` 期待値を現実装へ同期して east3-contract 前提の失敗を解消。
- 2026-02-26: `S2-06` として Go/Java/Swift/Kotlin sidecar 経路の smoke（`test_py2{go,java,swift,kotlin}_smoke.py`）と `check_py2{go,java,swift,kotlin}_transpile.py` を全通しし、JS emitter 直処理化の波及回帰がないことを確認。
- 2026-02-26: `S3-01` として `rs_emitter` に `ForCore` 受理を追加し、`iter_plan=StaticRangeForPlan/RuntimeIterForPlan` を内部で `ForRange/For` へ変換する経路を実装。`test_py2rs_smoke.py` に ForCore 直受理回帰（range/runtime tuple target）を追加し、`test_py2rs_smoke.py` 全通過を確認。
- 2026-02-26: `S3-02` として `rs_emitter` に `ObjBool/ObjLen/ObjStr/ObjIterInit/ObjIterNext/ObjTypeId`・`IsInstance/IsSubtype/IsSubclass`・`Box/Unbox` の直接描画を追加。type_id helper 事前検出（`_doc_mentions_isinstance`）を direct ノード対応へ拡張し、`test_py2rs_smoke.py` に object boundary / type predicate / box-unbox 回帰を追加して全通過を確認。
- 2026-02-26: `S3-03` として Rust smoke（`test_py2rs_smoke.py`）と `check_py2rs_transpile.py` を実行し、132件（skip 6）の transpile チェック全通過を確認。
- 2026-02-26: `S4-01` として `cs_emitter` に `ForCore` 受理を追加し、`iter_plan=StaticRangeForPlan/RuntimeIterForPlan` を内部で `ForRange/For` へ変換する経路を実装。`test_py2cs_smoke.py` に ForCore 直受理回帰（range/runtime tuple target）を追加して全通過を確認。
- 2026-02-26: `S4-02` として `cs_emitter` に `ObjBool/ObjLen/ObjStr/ObjIterInit/ObjIterNext/ObjTypeId`・`IsInstance/IsSubtype/IsSubclass`・`Box/Unbox` の直接描画を追加。`test_py2cs_smoke.py` に object boundary / type predicate / box-unbox 回帰を追加し全通過を確認。
- 2026-02-26: `S4-03` として C# smoke（`test_py2cs_smoke.py`）と `check_py2cs_transpile.py` を実行し、132件（skip 6）の transpile チェック全通過を確認。

## 分解

- [x] [ID: P3-EAST3-ONLY-01-S1-01] 8本 CLI の `--east-stage 2` 入力を非対応エラーへ統一し、互換警告文言依存テストをエラー期待へ更新する。
- [x] [ID: P3-EAST3-ONLY-01-S1-02] 8本 CLI から `load_east_document_compat` の import/call を撤去し、`load_east3_document` 単一路線へ固定する。
- [x] [ID: P3-EAST3-ONLY-01-S2-01] `js_emitter` で `ForCore(iter_plan=StaticRangeForPlan/RuntimeIterForPlan)` を直接処理する。
- [x] [ID: P3-EAST3-ONLY-01-S2-02] `js_emitter` で `ObjBool/ObjLen/ObjStr/ObjIterInit/ObjIterNext/ObjTypeId` を直接処理する。
- [x] [ID: P3-EAST3-ONLY-01-S2-03] `js_emitter` で `IsInstance/IsSubtype/IsSubclass` を直接処理する。
- [x] [ID: P3-EAST3-ONLY-01-S2-04] `js_emitter` で `Box/Unbox` の legacy 前提を撤去し、EAST3 ノードを直接受理する。
- [x] [ID: P3-EAST3-ONLY-01-S2-05] JS/TS smoke + `check_py2{js,ts}_transpile.py` を通し、`js_emitter` 直処理化の回帰を固定する。
- [x] [ID: P3-EAST3-ONLY-01-S2-06] Go/Java/Swift/Kotlin sidecar bridge 経路（`py2{go,java,swift,kotlin}`）で `check_py2*_transpile.py` + smoke を通し、JS直処理化の波及回帰を固定する。
- [x] [ID: P3-EAST3-ONLY-01-S3-01] `rs_emitter` の `ForCore` 直接処理（range/runtime iter）を実装する。
- [x] [ID: P3-EAST3-ONLY-01-S3-02] `rs_emitter` の `Obj*` / `Is*` / `Box/Unbox` 直接処理を実装する。
- [x] [ID: P3-EAST3-ONLY-01-S3-03] Rust smoke + `check_py2rs_transpile.py` で回帰を固定する。
- [x] [ID: P3-EAST3-ONLY-01-S4-01] `cs_emitter` の `ForCore` 直接処理（range/runtime iter）を実装する。
- [x] [ID: P3-EAST3-ONLY-01-S4-02] `cs_emitter` の `Obj*` / `Is*` / `Box/Unbox` 直接処理を実装する。
- [x] [ID: P3-EAST3-ONLY-01-S4-03] C# smoke + `check_py2cs_transpile.py` で回帰を固定する。
- [ ] [ID: P3-EAST3-ONLY-01-S5-01] 8本 CLI から `normalize_east3_to_legacy` 呼び出しを撤去する。
- [ ] [ID: P3-EAST3-ONLY-01-S5-02] `src/pytra/compiler/east_parts/east3_legacy_compat.py` を削除し、参照ゼロを `rg` で確認する。
- [ ] [ID: P3-EAST3-ONLY-01-S6-01] `docs-ja/plans/plan-east123-migration.md` ほか関連文書から `stage=2` 互換前提を撤去し、`EAST3 only` へ更新する。
- [ ] [ID: P3-EAST3-ONLY-01-S6-02] 必要な `docs/` 翻訳同期を反映し、日英の不整合をなくす。
- [ ] [ID: P3-EAST3-ONLY-01-S7-01] 非C++ 8本の smoke/check（`test_py2*` + `check_py2*`）を全通しする。
- [ ] [ID: P3-EAST3-ONLY-01-S7-02] `runtime_parity_check --case-root sample --targets rs,cs,js,ts,go,java,swift,kotlin --all-samples --ignore-unstable-stdout` を実行し、整合を最終確認する。
