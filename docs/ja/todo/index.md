# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-28

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。


## 未完了タスク

### P0: C++ `rc_new` 同型 cast 冗長除去（最優先）

文脈: [docs/ja/plans/p0-cpp-rcnew-samecast-elimination.md](../plans/p0-cpp-rcnew-samecast-elimination.md)

1. [x] [ID: P0-CPP-RCNEW-SAMECAST-01] C++ 出力の `rc<T>(::rc_new<T>(...))` を同型 cast 判定で除去し、`::rc_new<T>(...)` へ簡約する。
2. [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S1-01] `infer_rendered_arg_type()` で `::rc_new<T>(...) -> rc<T>` を推論できるようにする。
3. [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S1-02] `should_skip_same_type_cast` 判定で `rc_new` 起点の同型 cast を no-op として扱えるようにする。
4. [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S2-01] C++ cast 適用経路の回帰テストを追加し、`rc<T>(::rc_new<T>(...))` 再発を防止する。
5. [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S2-02] `sample/cpp` 再生成で `sample/18` の該当断片が `::rc_new<Token>(...)` へ簡約されることを確認する。
6. [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S3-01] `check_py2cpp_transpile` / smoke 実行で非退行を確認し、文脈の決定ログへ記録する。

### P0: Ruby 画像出力 runtime 実装とバイト parity 回復（最優先）

文脈: [docs/ja/plans/p0-ruby-image-runtime-parity.md](../plans/p0-ruby-image-runtime-parity.md)

1. [x] [ID: P0-RUBY-IMAGE-PARITY-01] Ruby backend の画像出力を no-op から実体 runtime へ移行し、`sample/01` の PNG を含む画像アーティファクト parity を回復する。
2. [x] [ID: P0-RUBY-IMAGE-PARITY-01-S1-01] Ruby 画像出力経路（emitter / runtime）の現状を棚卸しし、`__pytra_noop` 依存箇所を固定する。
3. [x] [ID: P0-RUBY-IMAGE-PARITY-01-S2-01] Ruby runtime に PNG 書き出し実体（Python runtime 互換）を実装する。
4. [x] [ID: P0-RUBY-IMAGE-PARITY-01-S2-02] Ruby runtime に GIF 書き出し実体（Python runtime 互換）を実装する。
5. [x] [ID: P0-RUBY-IMAGE-PARITY-01-S2-03] Ruby emitter の画像保存 lower を `__pytra_noop` から実体 runtime 呼び出しへ切り替える。
6. [x] [ID: P0-RUBY-IMAGE-PARITY-01-S3-01] `sample/01` の PNG バイト一致検証を自動化し、回帰テストへ組み込む。
7. [x] [ID: P0-RUBY-IMAGE-PARITY-01-S3-02] 代表 GIF ケースでバイト一致を検証し、`sample/ruby` 再生成と parity 非退行を確認する。

### P0: sample 画像 artifact_size の stdout parity 導入（最優先）

文脈: [docs/ja/plans/p0-sample-artifact-size-stdout-parity.md](../plans/p0-sample-artifact-size-stdout-parity.md)

1. [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01] `runtime_parity_check` で画像 artifact の実サイズ一致を検証し、stdout だけでは見えない回帰を検知可能にする。
2. [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S1-01] 画像出力ケースを棚卸しし、`output:` 行を起点に artifact 比較対象を固定する。
3. [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S2-01] Python baseline の artifact 実サイズ取得を `runtime_parity_check` に追加する。
4. [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S2-02] target 実行時の artifact presence/size 比較（stale file ガード含む）を追加する。
5. [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S3-01] `runtime_parity_check` 回帰テストを更新し、`artifact_size_mismatch` 検知を固定する。
6. [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S3-02] sample parity を再実行し、サイズ比較有効状態で非退行を確認する。

### P1: EAST3 関数間 non-escape 解析導入（RAII 候補注釈）

文脈: [docs/ja/plans/p1-east3-interprocedural-nonescape-analysis.md](../plans/p1-east3-interprocedural-nonescape-analysis.md)

1. [x] [ID: P1-EAST3-NONESCAPE-IPA-01] EAST3 最適化層へ関数間 non-escape 解析（SCC + fixed point）を導入し、RAII 変換候補注釈を `meta` に保存する。
2. [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S1-01] escape 判定ドメイン（arg escape / return escape / unknown-call policy）を仕様化し、`PassContext` に保持する。
3. [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S1-02] EAST3 から call graph を抽出し、SCC 分解ユーティリティを追加する。
4. [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S2-01] `NonEscapeInterproceduralPass` を実装し、summary fixed-point 更新を成立させる。
5. [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S2-02] 収束した summary を関数/式ノード `meta` へ注釈する。
6. [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S3-01] 再帰・相互再帰・外部呼び出し混在の unit テストを追加し、fail-closed と決定性を固定する。
7. [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S3-02] `east3 optimizer` 回帰と `check_py2cpp_transpile` を再実行し、非退行を確認する。

### P1: C++ `list` の PyObj/RC モデル移行（段階導入）

文脈: [docs/ja/plans/p1-list-pyobj-migration.md](../plans/p1-list-pyobj-migration.md)

1. [x] [ID: P1-LIST-PYOBJ-MIG-01] `list` を PyObj/RC 管理モデルへ段階移行し、non-escape 経路のみ RAII 縮退できる構成へ移行する。
2. [x] [ID: P1-LIST-PYOBJ-MIG-01-S0-01] `list` 参照セマンティクス契約（alias/共有/破壊的更新）を docs/spec に明文化する。
3. [x] [ID: P1-LIST-PYOBJ-MIG-01-S0-02] alias 期待 fixture（`a=b` 後の `append/pop` 共有）を追加し、現状差分を可視化する。
4. [x] [ID: P1-LIST-PYOBJ-MIG-01-S0-03] 現行 sample/fixture のうち list 値コピー依存箇所を棚卸しして決定ログに固定する。
5. [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-01] runtime に新 list PyObj モデル（型・寿命・iter/len/truthy 契約）を追加する。
6. [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-02] `make_object` / `obj_to_*` / `py_iter_or_raise` を新 list モデル対応へ拡張する。
7. [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-03] 旧値モデルとの互換ブリッジ（最小）を追加し、段階移行中の compile break を抑える。
8. [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-04] runtime 単体テスト（構築・alias・iter・境界変換）を追加する。
9. [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-01] C++ emitter の list 型描画を model switch（`value|pyobj`）経由へ集約する。
10. [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-02] list literal/ctor/append/extend/pop/index/slice の出力を `pyobj` モデル対応へ更新する。
11. [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-03] for/enumerate/comprehension の list 反復 lower を `pyobj` list で成立させる。
12. [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-04] `sample/18` を含む代表 fixture の compile/run/parity を `pyobj` モデルで通す。
13. [x] [ID: P1-LIST-PYOBJ-MIG-01-S3-01] `P1-EAST3-NONESCAPE-IPA-01` の注釈を C++ 側へ受け渡す経路を追加する。
14. [x] [ID: P1-LIST-PYOBJ-MIG-01-S3-02] non-escape local list のみ stack/RAII へ縮退する Cpp pass を追加する。
15. [x] [ID: P1-LIST-PYOBJ-MIG-01-S3-03] unknown/external/dynamic call 混在時に縮退しない fail-closed 回帰テストを追加する。
16. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-01] `value` vs `pyobj` の性能/サイズ/差分を sample で比較し、既定切替判断を記録する。
17. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02] 既定モデルを `pyobj` に切替し、rollback 手順（フラグで `value` 復帰）を整備する。
18. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S1] rollback 準備として `py2cpp` に `--cpp-list-model {value,pyobj}` を追加し、single/multi-file 出力へ反映する。
19. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2] `sample` 失敗 12 件（`05..16`）の compile/runtime blocker を段階解消し、`pyobj` モデルの実行成立範囲を拡張する。
20. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S1] pyobj で `grid[y][x] = ...` が `object[...]` へ落ちる compile blocker を `py_set_at(...)` lower で解消する。
21. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S2] `07/08/09` の runtime 失敗（`setitem on non-list object`）原因を特定し、`py_set_at` 入力が list object になるよう lower/runtime を補正する。
22. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S3] `12_sort_visualizer` の compile blocker（list 注釈引数が `object` シグネチャへ合わない）を callsite boxing 補正で解消する。
23. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S4] `13_maze_generation_steps` の tuple/list runtime blocker（tuple boxing 欠落と tuple subscript unbox 欠落）を解消する。
24. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S3] 既定モデルを `pyobj` へ切替し、`--cpp-list-model value` を rollback 手順として運用記述へ反映する。
25. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-03] 旧値モデルの互換コード撤去計画（別ID起票条件を含む）を確定する。
26. [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-04] docs/how-to-use/spec/todo の運用記述を同期し、最終受け入れ基準を満たす。

### P1: 全言語コメント忠実性ポリシー（生成コメント禁止）

文脈: [docs/ja/plans/p1-comment-fidelity-all-backends.md](../plans/p1-comment-fidelity-all-backends.md)

1. [x] [ID: P1-COMMENT-FIDELITY-01] 全 backend の出力で「元ソースにないコメントを禁止し、元コメントを欠落なく反映する」契約を実装とテストで固定する。
2. [x] [ID: P1-COMMENT-FIDELITY-01-S1-01] 全 emitter の固定コメント/`TODO`/`pass` コメント出力箇所を棚卸しし、禁止パターン一覧を固定する。
3. [x] [ID: P1-COMMENT-FIDELITY-01-S1-02] コメント出力契約（`module_leading_trivia` / `leading_trivia` のみ許可）と fail-closed 方針を仕様化する。
4. [x] [ID: P1-COMMENT-FIDELITY-01-S2-01] `ts/go/java/swift/kotlin/ruby/lua` の固定コメント出力を撤去し、元コメント伝播のみへ統一する。
5. [x] [ID: P1-COMMENT-FIDELITY-01-S2-02] `cpp/rs/cs/js` の `pass` / unsupported コメント経路を no-op または例外へ置換する。
6. [x] [ID: P1-COMMENT-FIDELITY-01-S3-01] 全 `test_py2*smoke.py` に禁止コメント検査と元コメント反映テストを追加し、回帰を固定する。
7. [x] [ID: P1-COMMENT-FIDELITY-01-S3-02] `sample/*` 再生成と差分検証を行い、固定コメント残存ゼロを確認する。

### P1: Kotlin runtime 外出し（inline helper 撤去）

文脈: [docs/ja/plans/p1-kotlin-runtime-externalization.md](../plans/p1-kotlin-runtime-externalization.md)

1. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01] Kotlin backend の生成コードから `__pytra_*` helper 本体を撤去し、runtime 外部参照方式へ統一する。
2. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S1-01] Kotlin emitter の inline helper 出力一覧と runtime API 対応表を確定する。
3. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-01] Kotlin runtime 正本（`src/runtime/kotlin/pytra`）を整備し、`__pytra_*` API を外部化する。
4. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-02] Kotlin emitter から helper 本体出力を撤去し、runtime 呼び出し専用へ切り替える。
5. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-03] `py2kotlin.py` の出力導線で runtime ファイルを配置する。
6. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S3-01] `check_py2kotlin_transpile` / Kotlin smoke / parity を更新し、回帰を固定する。
7. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S3-02] `sample/kotlin` を再生成し、inline helper 残存ゼロを確認する。

### P1: Lua sample 全18件対応（残り14件解消）

文脈: [docs/ja/plans/p1-lua-sample-full-coverage.md](../plans/p1-lua-sample-full-coverage.md)

1. [ ] [ID: P1-LUA-SAMPLE-FULL-01] Lua backend を `sample/py` 18件へ拡張し、`sample/lua` の欠落（現状4件のみ）を解消する。
2. [ ] [ID: P1-LUA-SAMPLE-FULL-01-S1-01] `sample/py` 残件14ケースの失敗要因を分類し、機能ギャップ一覧を固定する。
3. [ ] [ID: P1-LUA-SAMPLE-FULL-01-S2-01] 優先度順に未対応 lower（例: comprehension / lambda / tuple assign / stdlib 呼び出し差分）を実装する。
4. [ ] [ID: P1-LUA-SAMPLE-FULL-01-S2-02] `tools/check_py2lua_transpile.py` の `DEFAULT_EXPECTED_FAILS` から sample 対象を段階削除し、スキップ依存を解消する。
5. [ ] [ID: P1-LUA-SAMPLE-FULL-01-S3-01] `sample/lua` 全18件を再生成し、欠落ファイルゼロを確認する。
6. [ ] [ID: P1-LUA-SAMPLE-FULL-01-S3-02] Lua smoke/parity を再実行し、非退行を固定する。

### P2: Java 出力の過剰括弧削減（可読性）

文脈: [docs/ja/plans/p2-java-parentheses-reduction.md](../plans/p2-java-parentheses-reduction.md)

1. [ ] [ID: P2-JAVA-PARENS-01] Java backend の式出力を意味保存を維持した最小括弧へ移行し、`sample/java` の冗長括弧を縮退する。
2. [ ] [ID: P2-JAVA-PARENS-01-S1-01] Java emitter の括弧出力契約（最小括弧化ルールと fail-closed 条件）を文書化する。
3. [ ] [ID: P2-JAVA-PARENS-01-S2-01] `BinOp` 出力を優先順位ベースへ変更し、不要な全体括弧を削減する。
4. [ ] [ID: P2-JAVA-PARENS-01-S2-02] `Compare/BoolOp/IfExp` など周辺式との組み合わせで意味保存を担保する回帰ケースを追加する。
5. [ ] [ID: P2-JAVA-PARENS-01-S3-01] `sample/java` を再生成して縮退結果を確認し、回帰テストを固定する。

### P2: EAST 解決情報 + CodeEmitter 依存収集による最小 import 生成

文脈: [docs/ja/plans/p2-east-import-resolution-and-codeemitter-dep-collection.md](../plans/p2-east-import-resolution-and-codeemitter-dep-collection.md)

1. [ ] [ID: P2-EAST-IMPORT-RESOLUTION-01] EAST の import 解決情報と CodeEmitter 基底の依存収集を接続し、各 backend の import を必要最小へ統一する。
2. [ ] [ID: P2-EAST-IMPORT-RESOLUTION-01-S1-01] EAST3 で識別子/呼び出しの import 解決情報（module/symbol）を保持する仕様を定義する。
3. [ ] [ID: P2-EAST-IMPORT-RESOLUTION-01-S1-02] parser/lowering で解決情報を `meta` もしくはノード属性へ記録し、欠落時 fail-closed 条件を決める。
4. [ ] [ID: P2-EAST-IMPORT-RESOLUTION-01-S2-01] CodeEmitter 基底に `require_dep` / `finalize_deps` 等の依存収集 API を追加する。
5. [ ] [ID: P2-EAST-IMPORT-RESOLUTION-01-S2-02] backend 側で import 直書きを撤去し、基底の依存収集 API 経由へ段階移行する（先行: Go）。
6. [ ] [ID: P2-EAST-IMPORT-RESOLUTION-01-S2-03] 先行 backend（Go）で `var _ = math.Pi` など未使用回避ダミーを撤去し、必要 import のみ出力する。
7. [ ] [ID: P2-EAST-IMPORT-RESOLUTION-01-S3-01] import 回帰テスト（必要最小/未使用禁止/依存欠落禁止）を追加し、CI 導線へ固定する。

### P4: 全言語 selfhost 完全化（低低優先）

文脈: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] `cpp/rs/cs/js/ts/go/java/swift/kotlin` の selfhost を段階的に成立させ、全言語の multistage 監視を通過可能にする。
2. [x] [ID: P4-MULTILANG-SH-01-S1-01] 現状の stage1/stage2/stage3 未達要因を言語別に固定化し、優先順（blocking chain）を明文化する。
3. [x] [ID: P4-MULTILANG-SH-01-S1-02] multistage runner 未定義言語（go/java/swift/kotlin）の runner 契約を定義し、`runner_not_defined` を解消する実装方針を確定する。
4. [x] [ID: P4-MULTILANG-SH-01-S2-01] Rust selfhost の stage1 失敗（from-import 受理）を解消し、stage2 へ進める。
5. [ ] [ID: P4-MULTILANG-SH-01-S2-02] C# selfhost の stage2 compile 失敗を解消し、stage3 変換を通す。
6. [x] [ID: P4-MULTILANG-SH-01-S2-02-S1] C# emitter の selfhost 互換ギャップ（`Path`/`str.endswith|startswith`/定数デフォルト引数）を埋め、先頭 compile エラーを前進させる。
7. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2] `py2cs.py` selfhost 生成物の import 依存解決方針（単体 selfhost source 生成 or モジュール連結）を確定し、`sys/argparse/transpile_cli` 未解決を解消する。
8. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S1] C# selfhost 先頭エラーの足切り（`sys.exit` / docstring式）を解消し、import 依存未解決の先頭シンボルを確定する。
9. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2] C# selfhost 用の import 依存閉包方式（単体 selfhost source 生成 or モジュール連結）を実装し、`transpile_to_csharp` 未解決を解消する。
10. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S1] 単体 selfhost source 方式の PoC（`prepare_selfhost_source_cs.py`）を実装し、変換可否を実測で確認する。
11. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2] PoC 失敗要因（C# object receiver 制約）を解消するか、モジュール連結方式へ pivot して import 依存閉包を成立させる。
12. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S1] 単体 selfhost source PoC の parse 制約（object receiver access）を解消し、`selfhost/py2cs.py` の C# 変換を通す。
13. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2] 単体 selfhost source 生成物（`cs_selfhost_full_stage1.cs`）の compile 失敗を分類し、mcs 通過に必要な emit/runtime 互換ギャップを埋める。
14. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S1] compile 失敗の機械分類ツールを追加し、エラーコード/カテゴリの現状値をレポート化する。
15. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S2] 分類結果（テンプレート断片混入 / 呼び出し形状崩れ / shadowed local）に対応する修正を実装し、`CS1525/CS1002` を段階的に削減する。
16. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S3] `mcs` 内部例外（`tuples > 7`）を回避する emit 方針を実装し、stage2 compile を次段検証可能な状態へ戻す。
17. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S4] `mcs` で顕在化した通常 compile エラー（`CS1061/CS0103/CS1503` 上位群）の先頭カテゴリを削減し、stage2 失敗件数を継続的に縮退させる。
18. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S5] 残存上位エラー（`CS0103 set/list/json` と `CS0019 char/string`）を対象に emitter lower を追加し、stage2 compile 失敗件数をさらに縮退させる。
19. [x] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S6] 残存の主要失敗（`json` 未解決、`dict.get/items` 未lower、`CodeEmitter` static参照不整合）を段階解消し、stage2 compile の上位エラー構成を更新する。
20. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7] 残存上位エラー（`_add`/`item_expr` の未定義、`object` 由来の `CS1503/CS0266`）を対象に nested helper/型縮約を補強し、stage2 compile 件数をさらに削減する。
21. [ ] [ID: P4-MULTILANG-SH-01-S2-02-S3] C# selfhost の stage2/stage3 を通し、`compile_fail` から `pass` へ到達させる。
22. [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
23. [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
24. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
25. [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
26. [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
- `P4-MULTILANG-SH-01-S1-01` `check_multilang_selfhost_suite.py` を再実行し、`rs/cs/js/ts/go/java/swift/kotlin` の stage1/2/3 未達カテゴリと先頭原因を `docs/ja/plans/p4-multilang-selfhost-full-rollout.md` に固定した。
- `P4-MULTILANG-SH-01-S1-02` `go/java/swift/kotlin` の runner 契約（build/run と fail 分類）を `docs/ja/plans/p4-multilang-selfhost-full-rollout.md` に確定した。
- `P4-MULTILANG-SH-01-S2-01` `src/py2rs.py` の括弧付き `from-import` を解消し、`rs` の stage1 を pass（次段は `compile_fail`）へ遷移させた。
- `P4-MULTILANG-SH-01-S2-02-S1` C# emitter で `Path`/`str.endswith|startswith`/定数デフォルト引数を selfhost 互換化し、`cs` の先頭 compile エラーを `Path` 未解決から `sys` 未解決へ前進させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S1` `sys.exit` lower と docstring式除去を入れ、`cs` の先頭 compile エラーを `transpile_to_csharp` 未解決へ前進させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S1` `prepare_selfhost_source_cs.py` を追加して単体 selfhost source を検証し、C# object receiver 制約で現状は不成立と固定した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S1` hook 無効化パッチを追加しても `CSharpEmitter._walk_node_names` の `node.get(...)` で同制約違反が継続することを確認し、PoC阻害要因を具体化した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S1` `CSharpEmitter._walk_node_names` の `Any` 直アクセスを helper 化し、`selfhost/py2cs.py` の C# 変換を通過させた（次段は compile fail）。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S1` `check_cs_single_source_selfhost_compile.py` を追加し、`p4-cs-single-source-selfhost-compile-status.md` で compile 失敗の件数分類（`CS1525/CS1002` 中心）を固定した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S2` C# emitter の `JoinedStr`/`Set` lower・optional 引数順序・ローカル shadow 回避を実装し、`test/unit/test_py2cs_smoke.py`（26件）を通過。`check_cs_single_source_selfhost_compile.py` で `CS1525/CS1002` が 0 件化し、次ブロッカーが `mcs tuples > 7` 内部例外に収束した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S3` tuple arity が `1` または `>7` のとき `List<object>` へ lower する C# emitter 修正を追加し、`test/unit/test_py2cs_smoke.py`（28件）を通過。`check_cs_single_source_selfhost_compile.py` で `mcs tuples > 7` 内部例外が解消し、失敗モードを通常の compile エラー（`CS1061/CS0103/CS1503` など）へ遷移させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S4` C# class 定義に base 句（`class Child : Base`）を出力するよう修正し、継承欠落による `CS1061` を大幅削減。`check_cs_single_source_selfhost_compile.py` で `CS1061` を `469 -> 109` に縮退させ、`test/unit/test_py2cs_smoke.py` を 29 件で通過させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S5` `set/list/dict` の型ヒント連動 lower、`for ch in str` の string 化、`strip/find/rfind/replace` lower を追加し、`test/unit/test_py2cs_smoke.py` を 32 件で通過。`check_cs_single_source_selfhost_compile.py` で `CS1061` を `109 -> 20`、`CS0103` を `81 -> 36` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S6` `@staticmethod/@classmethod` の static 出力、`json.loads` lower、`dict.get/items` の unknown 型フォールバックを追加し、`check_cs_single_source_selfhost_compile.py` で `CS0120` を `5 -> 0`、`CS1061` を `20 -> 10`、`CS0103` を `36 -> 34` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `_collect_using_lines` のローカル helper をクラスメソッド化し、`_emit_assign` の `item_expr` 初期化を追加。`check_cs_single_source_selfhost_compile.py` で `CS0103` を `34 -> 12` に縮退させた（`CS1503/CS0266` は継続対応）。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` keyword 引数呼び出し崩れ対策（`code_emitter`/`cs_emitter`/`transpile_cli`）、`py2cs.py` の argparse 依存除去、`prepare_selfhost_source(_cs).py` の補助生成を追加し、`check_cs_single_source_selfhost_compile.py` で `CS0103` を `12 -> 1`、`CS0815` を `5 -> 3` まで縮退させた（`CS1502/CS1503/CS0266` は継続対応）。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の `__main__` ガード置換を `main([str(x) for x in args])` に更新し、`check_cs_single_source_selfhost_compile.py` で `CS0103` を `1 -> 0`、`CS1503` を `61 -> 60`、`CS1502` を `47 -> 46` へ縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `code_emitter.py` で `EmitterHooks.to_dict` の key を `str` 化し、`_root_scope_stack` の型付き初期化を明示した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1503` を `60 -> 58`、`CS1502` を `46 -> 45`、`CS1950` を `14 -> 13` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `py2cs.py` の `_arg_get_str` 型注釈を `dict[str, str]` に整合させ、selfhost 生成物の `Dictionary<string,string>` / `Dictionary<string,object>` 混在由来の型不一致を縮退した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1503` を `58 -> 46`、`CS1502` を `45 -> 33`、`CS0266` を `34 -> 33` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `py2cs.py` の `load_east()` fallback を型付き `dict[str, Any]`（`empty_doc`）へ固定し、自己変換生成物の conditional 式型崩れを抑制した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS0173` を `5 -> 4` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の parser stub で `_` 変数再利用を撤去し、`Path`/`str` 型衝突を `*_ignored_*` へ分離した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS0029` を `18 -> 17` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の support block で `write_text_file()` を `Path.write_text()` へ差し替え、`open(...)/PyFile` 経路を撤去した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS0246`/`CS0841` を 0 件化した。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の support block で `module_east_raw` 取得を型付き分岐へ差し替え、`dict_any_get_dict(...)` の型不一致経路を撤去した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1502` を `33 -> 32`、`CS1503` を `46 -> 45` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の support block で `resolve_module_name` の `dict[str, str]` 参照を型付きキー参照へ差し替え、`dict_any_get_str(...)` の型不一致経路を撤去した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1502` を `32 -> 29`、`CS1503` を `45 -> 42` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` の support block で import graph 解析ループの `resolved: dict[str, str]` 読み取りを `dict_str_get(...)` へ置換し、`dict_any_get_str(...)` 由来の型不一致を縮退した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1502` を `29 -> 26`、`CS1503` を `42 -> 39` に縮退させた。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source.py` の selfhost hook stub（`_call_hook`）を `return None` のみに簡素化し、C# 生成物の型衝突を削減した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS0266` を `33 -> 27`、`CS0029` を `17 -> 16` に縮退させた（`CS1502=26` / `CS1503=39` は維持）。
- `P4-MULTILANG-SH-01-S2-02-S2-S2-S2-S2-S7` `prepare_selfhost_source_cs.py` で `CodeEmitter.load_profile_with_includes()` の `includes_raw` 経路を selfhost 向けに簡素化し、`object -> List<string>` 変換を回避した。`test_py2cs_smoke.py`（34件）通過のうえ `check_cs_single_source_selfhost_compile.py` で `CS1502` を `26 -> 25`、`CS1503` を `39 -> 38`、`CS0266` を `27 -> 26` に縮退させた。
