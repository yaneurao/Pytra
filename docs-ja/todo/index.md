# TODO（未完了）

> `docs-ja/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../../docs/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-26

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs-ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs-ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs-ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs-ja/todo/index.md` / `docs-ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。

## P0: sample C++/Rust 実行時間乖離の是正（最優先）

文脈: `docs-ja/plans/p0-sample-cpp-rs-perf-gap.md`（`P0-SAMPLE-CPP-RS-PERF-01`）

1. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01] sample の C++/Rust 実行時間乖離を外れ値なしの状態へ是正し、再計測手順と結果を文書化する。
2. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S1-01] 現行 README 値の C++/Rust 差分表（比率順）を自動抽出し、外れ値ケースを固定する。
3. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S1-02] 再現可能な計測プロトコル（warmup/repeat/中央値、コンパイル時間の扱い）を文書化する。
4. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-01] Rust emitter の `save_gif`/`write_rgb_png` 呼び出しで不要 clone を除去する。
5. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-02] Rust emitter の list subscript read でコピー不要型の clone を抑止する。
6. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-03] Rust emitter の文字列比較/トークナイズ経路で `to_string()` 連鎖を削減する。
7. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-04] `01/09/18` を再計測し、Rust 側改善の寄与をケース別に記録する。
8. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S3-01] C++ GIF runtime に `py_slice`/`py_len`/`py_to_int64` 依存を減らす fast-path を追加する。
9. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S3-02] C++ PNG runtime の scanline/chunk 処理を typed 操作中心へ寄せる。
10. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S3-03] `11/12/13/16` を再計測し、C++ 側改善の寄与をケース別に記録する。
11. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S4-01] `sample` 生成コードのフレーム二重コピー（例: `bytes(bytes(frame))`）を削減する。
12. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S4-02] 出力 parity を維持したまま高速化できることを `runtime_parity_check`/`verify_sample_outputs` で確認する。
13. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S5-01] C++/Rust 18 件の再計測結果を `readme.md` / `readme-ja.md` へ反映する。
14. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S5-02] 乖離が残るケースは未解消要因と次の打ち手を文書へ追記する。
15. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S6-01] C++ runtime の `list/bytearray` 拡張処理を range insert 化し、GIF/PNG の byte コピー hot path を短縮する。
16. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S6-02] 主要乖離ケース（`01/03/04/09/11/12/13/14/15/16/18`）を再計測し、寄与を記録する。
17. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S7-01] Rust emitter の nested subscript 読み取りで中間 list clone を抑止し、`enumerate` ループの二重 clone を削減する。
18. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S7-02] `01/04/09/18` を再計測し、clone 抑止の寄与と未解消乖離を記録する。
19. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S8-01] Rust emitter の subscript->attribute 二重 clone と文字列比較 `to_string()` を削減し、`18` の hot path を軽量化する。
20. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S8-02] `01/04/09/18` を再計測し、`18` 改善量と残課題（`01/04/09`）を記録する。
21. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S9-01] Rust emitter で `bytearray()/bytes()` の空初期化に容量推定 (`with_capacity`) を導入し、`pixels` 系ホットパスの再確保を抑止する。
22. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S9-02] `01/04/09/18` を再計測し、`with_capacity` 導入の寄与と未解消外れ値を更新する。
23. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S10-01] C++ emitter の `/` 数値演算を `py_div`（Python互換 true division）へ統一し、`01/04` の整数除算寄り経路を解消する。
24. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S10-02] `01/04/09/18` を再計測し、`/` セマンティクス修正の寄与と残外れ値（`09/18`）を記録する。
25. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S11-01] Rust emitter の list/enumerate 反復で list 全体 clone を削減し、`18` のトークナイズ/文実行 hot path を軽量化する。
26. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S11-02] `01/04/09/18` を再計測し、反復 clone 削減の寄与と残外れ値（`09/18`）を更新する。
27. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S12-01] Rust emitter の class method 引数で `str` を `&str` 受けへ縮退し、`py_match/expect` 系の文字列一時確保を削減する。
28. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S12-02] `01/04/09/18` を再計測し、`&str` 化の寄与と残外れ値（`09/18`）を更新する。
29. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S13-01] C++ GIF runtime の `to_bytes` 多用箇所を little-endian 直書きと `reserve` へ置換し、`09` の encode/write 常用コストを削減する。
30. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S13-02] 影響ケース parity と `01/04/09/18` 再計測を実行し、`S13-01` の寄与と残外れ値（`09/18`）を更新する。
31. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S14-01] Rust runtime helper `py_str_at/py_slice_str` の `Vec<char>` 常時構築を撤去し、ASCII fast-path + 非ASCII fallback へ置換する。
32. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S14-02] `01/04/09/18` と `18` 単体の再計測で `S14-01` 寄与を確認し、残外れ値を `09` へ収束させる。
33. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S15-01] C++ runtime `PyFile::write(bytes)` を 1byte `put` ループから一括 `write` へ切替え、PNG/GIF 出力の I/O hot path を短縮する。
34. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S15-02] `01/04/09/18` と `01/09/18` 再計測で `S15-01` の再現性を確認し、`09` の外れ値解消を記録する。
35. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S16-01] 全18サンプルを再計測し、最新版の C++/Rust 実測値を `readme.md` / `readme-ja.md` に反映する。
36. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S16-02] 外れ値判定を更新し、残課題を `16_glass_sculpture_chaos` 単体へ絞り込んだことを計画文書へ記録する。
37. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S17-01] C++ emitter の if-join 名宣言で数値型推論を補強し、`16` の hot loop で `object` 退化していた局所変数（`hx/lxv/glow` など）を型付き値へ復帰させる。
38. [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S17-02] `16` 再計測と全18件再計測を実行し、`>1.5x` 外れ値が解消した最新版を `readme.md` / `readme-ja.md` と計画文書へ反映する。

## P2: C++ selfhost の virtual ディスパッチ簡略化（低優先）

文脈: `docs-ja/plans/p2-cpp-virtual-selfhost-dispatch.md`（`P2-CPP-SELFHOST-VIRTUAL-01`）

1. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01] `virtual/override` ベースの selfhost クラス呼び出し経路へ縮退できる箇所を洗い出し、`type_id` 分岐を低優先で簡素化する。
2. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S2-01] `py2cpp.py` 側 emit を切り出しして、`virtual` へ寄せる対象経路と fallback 経路を分離する。
3. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S2-02] `CppEmitter` の class method 呼び出し描画で、`virtual`/`override` 有無に応じた分岐を明示化する。
4. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S2-03] 置換できない `type_id` 分岐は理由付きで残し、非対象リストへ接続する。
5. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S3-01] `sample` の 2〜3 件から `type_id` 分岐を `virtual` 呼び出しに移行する。
6. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S3-02] 移行対象を段階的に拡大し、selfhost 再変換（`sample`/`test`）の成功率を評価する。
7. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S3-03] 移行不能ケースは判定ロジックで固定し、次回に回す明細を更新する。
8. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S4-01] `test/unit` と `sample` 再生成の回帰ケースを追加・更新して diff を固定する。
9. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S4-02] `tools/check_selfhost_cpp_diff.py` と `tools/verify_selfhost_end_to_end.py` を再実行し、回帰条件が満たされることを確認する。
10. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S4-03] `docs-ja/spec/spec-dev.md`（必要なら `spec-type_id`）へ簡潔に反映する。
11. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S5-01] `test/unit` へ `Base`/`Child` の `virtual/override` 呼び出しケース（`Base.f` 明示呼び出し、`super().f`、`virtual` 期待差分）を追加し、`type_id` 分岐除去を固定する。
12. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S5-02] `sample` 再変換で `type_id` 分岐が残る境界 (`staticmethod`/`class` method/`object` receiver) を明文化した回帰ケースを追加する。
13. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S5-03] `tools/verify_selfhost_end_to_end.py` を使う selfhost 回帰（最低2ケース）に virtual 化前後の差分検証を追加し、再変換可能性を固定する。

## P3: 非C++ emitter の EAST3 直結化と EAST2 互換撤去（低優先）

文脈: `docs-ja/plans/p3-east3-only-emitters.md`（`P3-EAST3-ONLY-01`）

1. [ ] [ID: P3-EAST3-ONLY-01] 非C++ 8ターゲット（`rs/cs/js/ts/go/java/swift/kotlin`）を `EAST3` 直結に統一し、`EAST2` 互換経路（`--east-stage 2` / `load_east_document_compat` / `east3_legacy_compat`）を撤去する。
2. [ ] [ID: P3-EAST3-ONLY-01-S1-01] 8本 CLI の `--east-stage 2` 入力を非対応エラーへ統一し、互換警告文言依存テストをエラー期待へ更新する。
3. [ ] [ID: P3-EAST3-ONLY-01-S1-02] 8本 CLI から `load_east_document_compat` の import/call を撤去し、`load_east3_document` 単一路線へ固定する。
4. [ ] [ID: P3-EAST3-ONLY-01-S2-01] `js_emitter` で `ForCore(iter_plan=StaticRangeForPlan/RuntimeIterForPlan)` を直接処理する。
5. [ ] [ID: P3-EAST3-ONLY-01-S2-02] `js_emitter` で `ObjBool/ObjLen/ObjStr/ObjIterInit/ObjIterNext/ObjTypeId` を直接処理する。
6. [ ] [ID: P3-EAST3-ONLY-01-S2-03] `js_emitter` で `IsInstance/IsSubtype/IsSubclass` を直接処理する。
7. [ ] [ID: P3-EAST3-ONLY-01-S2-04] `js_emitter` で `Box/Unbox` の legacy 前提を撤去し、EAST3 ノードを直接受理する。
8. [ ] [ID: P3-EAST3-ONLY-01-S2-05] JS/TS smoke + `check_py2{js,ts}_transpile.py` を通し、`js_emitter` 直処理化の回帰を固定する。
9. [ ] [ID: P3-EAST3-ONLY-01-S2-06] Go/Java/Swift/Kotlin sidecar bridge 経路（`py2{go,java,swift,kotlin}`）で `check_py2*_transpile.py` + smoke を通し、JS直処理化の波及回帰を固定する。
10. [ ] [ID: P3-EAST3-ONLY-01-S3-01] `rs_emitter` の `ForCore` 直接処理（range/runtime iter）を実装する。
11. [ ] [ID: P3-EAST3-ONLY-01-S3-02] `rs_emitter` の `Obj*` / `Is*` / `Box/Unbox` 直接処理を実装する。
12. [ ] [ID: P3-EAST3-ONLY-01-S3-03] Rust smoke + `check_py2rs_transpile.py` で回帰を固定する。
13. [ ] [ID: P3-EAST3-ONLY-01-S4-01] `cs_emitter` の `ForCore` 直接処理（range/runtime iter）を実装する。
14. [ ] [ID: P3-EAST3-ONLY-01-S4-02] `cs_emitter` の `Obj*` / `Is*` / `Box/Unbox` 直接処理を実装する。
15. [ ] [ID: P3-EAST3-ONLY-01-S4-03] C# smoke + `check_py2cs_transpile.py` で回帰を固定する。
16. [ ] [ID: P3-EAST3-ONLY-01-S5-01] 8本 CLI から `normalize_east3_to_legacy` 呼び出しを撤去する。
17. [ ] [ID: P3-EAST3-ONLY-01-S5-02] `src/pytra/compiler/east_parts/east3_legacy_compat.py` を削除し、参照ゼロを `rg` で確認する。
18. [ ] [ID: P3-EAST3-ONLY-01-S6-01] `docs-ja/plans/plan-east123-migration.md` ほか関連文書から `stage=2` 互換前提を撤去し、`EAST3 only` へ更新する。
19. [ ] [ID: P3-EAST3-ONLY-01-S6-02] 必要な `docs/` 翻訳同期を反映し、日英の不整合をなくす。
20. [ ] [ID: P3-EAST3-ONLY-01-S7-01] 非C++ 8本の smoke/check（`test_py2*` + `check_py2*`）を全通しする。
21. [ ] [ID: P3-EAST3-ONLY-01-S7-02] `runtime_parity_check --case-root sample --targets rs,cs,js,ts,go,java,swift,kotlin --all-samples --ignore-unstable-stdout` を実行し、整合を最終確認する。

## P0: C++ emitter 肥大化の段階縮退（最優先）

文脈: `docs-ja/plans/p0-cpp-emitter-slimming.md`（`P0-CPP-EMITTER-SLIM-01`）

1. [ ] [ID: P0-CPP-EMITTER-SLIM-01] `cpp_emitter.py` の肥大要因（互換層/責務集中/巨大 `render_expr`）を段階分割で解消し、EAST3 単一契約へ寄せる。
2. [x] [ID: P0-CPP-EMITTER-SLIM-01-S1-01] `cpp_emitter.py` の行数・メソッド数・長大メソッドを計測し、基準値を `docs-ja/plans/p0-cpp-emitter-slimming.md` に固定する。
3. [x] [ID: P0-CPP-EMITTER-SLIM-01-S1-02] `sample` と `test/unit` の C++ 生成差分基線（golden 比較）を更新し、以後の分割作業の回帰判定点を固定する。
4. [x] [ID: P0-CPP-EMITTER-SLIM-01-S2-01] `stage2/self_hosted` 前提の legacy builtin compat（`_render_legacy_builtin_call_compat` / `_render_legacy_builtin_method_call_compat`）を撤去する。
5. [x] [ID: P0-CPP-EMITTER-SLIM-01-S2-02] `For`/`ForRange` から `ForCore` への bridge と逆写像を撤去し、`ForCore` 直接受理へ統一する。
6. [x] [ID: P0-CPP-EMITTER-SLIM-01-S2-03] legacy `isinstance/issubclass` Name-call 許容経路を撤去し、type_id 系は EAST3 ノード前提へ統一する。
7. [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-01] import/include/namespace/module-init 生成責務を `src/hooks/cpp/emitter/` 配下の専用モジュールへ分離する。
8. [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-02] class emit（`virtual/override`・`PYTRA_TYPE_ID`・基底継承処理）を専用モジュールへ分離する。
9. [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-03] 型変換 (`_cpp_type_text`) と Any 境界補正 helper を専用モジュールへ分離する。
10. [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-04] built-in runtime_call（list/set/dict/str/path/special）分岐をディスパッチモジュールへ分離する。
11. [x] [ID: P0-CPP-EMITTER-SLIM-01-S4-01] `render_expr` の kind 分岐を `kind -> handler` テーブル駆動へ置換する骨格を導入する。
12. [x] [ID: P0-CPP-EMITTER-SLIM-01-S4-02] collection literal/comprehension 系ハンドラを `render_expr` から分離し、独立テストを追加する。
13. [x] [ID: P0-CPP-EMITTER-SLIM-01-S4-03] runtime/type_id/path 系ハンドラを `render_expr` から分離し、`render_expr` をディスパッチ専任へ縮退する。
14. [x] [ID: P0-CPP-EMITTER-SLIM-01-S5-01] `repr` 依存ノードを parser/lowerer 側で構造化ノードへ落とす前提を整理し、対象ノード一覧を確定する。
15. [x] [ID: P0-CPP-EMITTER-SLIM-01-S5-02] `_render_repr_expr` の利用箇所を段階削減し、必要な最終 fallback 以外を除去する。
16. [x] [ID: P0-CPP-EMITTER-SLIM-01-S5-03] `_render_repr_expr` を撤去（または no-op 化）し、`repr` 文字列依存経路が残らないことを `rg` で確認する。
17. [x] [ID: P0-CPP-EMITTER-SLIM-01-S6-01] Rust/C++ で共通化可能な helper（条件式・cast 補助・ループ骨格）を棚卸しし、`CodeEmitter` へ移管候補を確定する。
18. [x] [ID: P0-CPP-EMITTER-SLIM-01-S6-02] 共通化候補のうち 1〜2 系統を `CodeEmitter` へ移管し、C++/Rust 両 emitter の重複を削減する。
19. [x] [ID: P0-CPP-EMITTER-SLIM-01-S7-01] `test/unit/test_py2cpp_*.py` と `tools/check_py2cpp_transpile.py` を通し、分割後の回帰を固定する。
20. [x] [ID: P0-CPP-EMITTER-SLIM-01-S7-02] `tools/check_selfhost_cpp_diff.py` / `tools/verify_selfhost_end_to_end.py` を再実行し、selfhost 再変換可能性を確認する。
21. [ ] [ID: P0-CPP-EMITTER-SLIM-01-S7-03] `cpp_emitter.py` の最終メトリクス（行数・`render_expr` 行数・legacy 関数残数）を更新し、完了判定を記録する。
