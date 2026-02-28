# P1: EAST3 関数間 non-escape 解析導入（RAII 候補注釈）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-EAST3-NONESCAPE-IPA-01`

背景:
- C++ 出力の `rc` / `object` 経路を縮退するには、値が関数外へ escape するかを先に判定する必要がある。
- 単一関数内の局所判定だけでは、呼び出し先経由の escape を取りこぼす。
- ユーザー方針として「non-escape が判明した箇所を RAII 化候補にする」ことを優先する。

目的:
- EAST3 最適化層に関数間（interprocedural）non-escape 解析を追加し、関数 summary と値注釈を `meta` に保存する。
- 再帰・相互再帰を含む call graph に対して、SCC 単位の固定点反復で保守的に収束させる。
- 下流（CppOptimizer / CppEmitter）が RAII 変換可否を判断できる注釈境界を提供する。

対象:
- `src/pytra/compiler/east_parts/east3_optimizer.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（新規 `NonEscapeInterproceduralPass` 追加）
- `src/pytra/compiler/east_parts/east3_optimizer_cli.py`（必要なら trace/dump 拡張）
- `test/unit/test_east3_optimizer*.py`（解析結果の回帰固定）
- 必要なら `docs/ja/spec/spec-east3-optimizer.md` へ最小反映

非対象:
- C++ 側での実際の `rc/object -> RAII` 置換（別タスク）
- 他 backend の最適化適用
- 振る舞いが不確定な dynamic call の aggressive 推論

解析方針:
- まず関数 summary を作る。
  - 例: `arg_i` が escape するか、戻り値が escape 起源か、ローカル生成値が外部へ出るか。
- call graph を構築し、SCC 単位で反復する。
  - SCC 内は summary を同時更新し、変化がなくなるまで繰り返す。
- 未解決呼び出し（dynamic dispatch / external / Any-object 経路）は fail-closed で `escape=true` 扱いに倒す。
- 収束後、EAST3 ノード `meta` へ注釈する。
  - 関数ノード: `escape_summary`
  - 式/代入ノード: `non_escape_candidate` など

受け入れ基準:
- 関数間呼び出しを含む fixture で、局所解析では不可だった non-escape 候補が `meta` へ反映される。
- 再帰/相互再帰ケースで固定点計算が収束し、結果が決定的（再実行で同一）である。
- 未解決呼び出しが混ざるケースで fail-closed（安全側）に倒れる。
- 既存 `east3 optimizer` 回帰が非退行。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer*.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-02-28: ユーザー指示により、RAII 置換の前段として EAST3 側に関数間 non-escape 解析（SCC + fixed point）を導入する方針を確定した。
- 2026-02-28: `PassContext` に `non_escape_policy` を導入し、fail-closed 既定（`unknown_call_escape` など）を正規化して pass へ配布する実装方針を確定した。
- 2026-02-28: `optimize_east3_document` の report へ `non_escape_policy` を出力し、unit test で default/override/報告値の安定性を固定した。
- 2026-02-28: `non_escape_call_graph.py` を追加し、EAST3 Module から関数/メソッド symbol を抽出して resolved edge と unresolved call 件数を返す call graph ユーティリティ、および deterministic Tarjan SCC 分解を実装した。
- 2026-02-28: `test_east3_non_escape_call_graph.py` を追加し、top-level/class method/mutual recursion の call graph・SCC 回帰を固定した。
- 2026-02-28: `NonEscapeInterproceduralPass` を追加し、`arg_escape` / `return_from_args` / `return_escape` を fixed-point で収束させる summary 計算を実装した（fail-closed な unknown-call policy 反映）。
- 2026-02-28: `test_east3_non_escape_interprocedural_pass.py` で summary 伝播（sink->wrap）・return 起源伝播（identity->wrap2）・policy override を回帰固定した。
- 2026-02-28: 収束後 summary を関数ノード `meta.escape_summary` と call 式 `meta.non_escape_callsite` へ注釈する実装を追加し、unit test に注釈 payload の回帰アサーションを追加した。
- 2026-02-28: 相互再帰 + 外部呼び出し混在ケース（`a <-> b` と `unknown_sink`）の summary 伝播テストと、2回目実行で `changed=False` になる決定性テストを追加した。

## 分解

- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S1-01] escape 判定ドメイン（arg escape / return escape / unknown-call policy）を仕様化し、`PassContext` に保持する。
- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S1-02] EAST3 から call graph を抽出し、SCC 分解ユーティリティを追加する。
- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S2-01] `NonEscapeInterproceduralPass` を実装し、summary fixed-point 更新を成立させる。
- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S2-02] 収束した summary を関数/式ノード `meta` へ注釈する。
- [x] [ID: P1-EAST3-NONESCAPE-IPA-01-S3-01] 再帰・相互再帰・外部呼び出し混在の unit テストを追加し、fail-closed と決定性を固定する。
- [ ] [ID: P1-EAST3-NONESCAPE-IPA-01-S3-02] `east3 optimizer` 既存回帰と `check_py2cpp_transpile` を再実行し、非退行を確認する。
