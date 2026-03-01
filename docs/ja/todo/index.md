# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-01

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

### P0: sample/18 `tokenize` 入力の typed 化（`object` 退化撤去）（最優先）

文脈: [docs/ja/plans/p0-cpp-s18-tokenize-typed-input.md](../plans/p0-cpp-s18-tokenize-typed-input.md)

1. [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01] `tokenize` 引数の `object` 退化を撤去し、`list[str]` 型を境界越しに維持する。
2. [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S1-01] 現在 `object` に落ちる型決定経路（関数定義/呼び出し）を棚卸しし、fail-closed 条件を固定する。
3. [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S2-01] C++ emitter の型橋渡しを更新し、`tokenize(lines)` を typed 署名へ出力する。
4. [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S2-02] sample/18 回帰を追加し、`py_to_str_list_from_object(lines)` 非出力を固定する。
5. [x] [ID: P0-CPP-S18-TOKENIZE-TYPED-IN-01-S3-01] transpile/unit/sample 再生成を実行し、非退行を確認する。

### P0: sample/18 `enumerate(lines)` の direct typed unpack 化（最優先）

文脈: [docs/ja/plans/p0-cpp-s18-enumerate-direct-typed.md](../plans/p0-cpp-s18-enumerate-direct-typed.md)

1. [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01] `enumerate(lines)` を object 中継なしの direct typed unpack へ統一する。
2. [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S1-01] `For` lower の適用条件（iterable/list/tuple 型既知）を整理し、適用外は fail-closed に固定する。
3. [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S2-01] `for` header 出力を direct structured binding 優先へ更新する。
4. [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S2-02] sample/18 回帰を追加し、`object __itobj` + `py_at` 非出力を固定する。
5. [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S3-01] transpile/unit/sample 再生成で非退行を確認する。

### P0: sample/18 `str -> str` 同型変換の撤去（最優先）

文脈: [docs/ja/plans/p0-cpp-s18-str-identity-cast-elimination.md](../plans/p0-cpp-s18-str-identity-cast-elimination.md)

1. [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01] `str` 既知経路の `py_to_string` 同型変換を縮退する。
2. [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S1-01] `str` 同型変換の現状箇所を棚卸しし、適用条件/除外条件を固定する。
3. [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S2-01] emitter（必要なら EAST3 pass）へ縮退実装を追加し、`object` 経路は維持する。
4. [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S2-02] sample/18 回帰を追加し、`py_to_string` 不要出力の再発を防止する。
5. [x] [ID: P0-CPP-S18-STR-IDENTITY-CAST-01-S3-01] transpile/unit/sample 再生成で非退行を確認する。

### P0: sample/18 tokenizer の文字列分岐 tag 化（最優先）

文脈: [docs/ja/plans/p0-cpp-s18-token-dispatch-tagization.md](../plans/p0-cpp-s18-token-dispatch-tagization.md)

1. [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01] tokenizer の kind 判定を文字列比較連鎖から tag/enum 中心へ移行する。
2. [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S1-01] 現在の分岐列を棚卸しし、tag マップ（1文字->kind_tag）仕様を固定する。
3. [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S2-01] emitter 出力を tag 判定優先へ変更し、同値な kind 文字列は必要箇所のみ残す。
4. [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S2-02] sample/18 回帰を追加し、`if (ch == \"...\")` 連鎖の再発を防止する。
5. [x] [ID: P0-CPP-S18-TOKEN-DISPATCH-TAG-01-S3-01] transpile/unit/parity で非退行を確認する。

### P0: sample/18 benchmark ソース構築の typed list 化（最優先）

文脈: [docs/ja/plans/p0-cpp-s18-benchmark-source-typed-list.md](../plans/p0-cpp-s18-benchmark-source-typed-list.md)

1. [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01] `build_benchmark_source` と下流呼び出しを typed list へ寄せ、`object + py_append` を縮退する。
2. [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S1-01] `build_benchmark_source` から `tokenize`/`parse_program` までの型境界を棚卸しし、`list[str]` 維持条件を固定する。
3. [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S2-01] emitter を更新し、list 初期化/append/return を typed 経路で出力する。
4. [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S2-02] sample/18 回帰を追加し、`object lines` と `py_append(lines, ...)` の再発を防止する。
5. [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S3-01] transpile/unit/parity を再実行し、非退行を確認する。

### P0: sample/13 向け `cpp_list_model=pyobj` の typed list 拡張（最優先）

文脈: [docs/ja/plans/p0-cpp-s13-typed-list-expansion.md](../plans/p0-cpp-s13-typed-list-expansion.md)

1. [x] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01] sample/13 の `grid/stack/dirs/frames` の object 退化を抑制し、typed list 経路を拡張する。
2. [x] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01-S1-01] `cpp_list_model=pyobj` の typed list 判定拡張条件（concrete 要素型）を仕様化する。
3. [x] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01-S2-01] emitter 実装を更新し、sample/13 の `grid/stack/dirs/frames` を typed list へ寄せる。
4. [x] [ID: P0-CPP-S13-TYPED-LIST-EXPAND-01-S3-01] sample/13 断片回帰を追加し、transpile/check を通す。

### P0: sample/13 `candidates` 選択式の CSE/hoist（最優先）

文脈: [docs/ja/plans/p0-cpp-s13-candidate-index-cse.md](../plans/p0-cpp-s13-candidate-index-cse.md)

1. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-01] sample/13 の `sel` 抽出で重複する index 計算と要素取得を hoist し、同一式の再評価を削減する。
2. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-01-S1-01] `sel` 周辺の重複式パターンと適用条件（fail-closed）を定義する。
3. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-01-S2-01] index/要素取得の hoist を実装し、重複出力を削減する。
4. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-01-S3-01] sample/13 回帰を追加し、transpile/check を通す。

### P0: sample/13 同型 cast 連鎖の縮退（最優先）

文脈: [docs/ja/plans/p0-cpp-s13-samecast-reduction.md](../plans/p0-cpp-s13-samecast-reduction.md)

1. [x] [ID: P0-CPP-S13-SAMECAST-CUT-01] sample/13 の型既知経路に残る `int64(py_to<int64>(...))` 等の同型 cast 連鎖を縮退する。
2. [x] [ID: P0-CPP-S13-SAMECAST-CUT-01-S1-01] sample/13 の同型 cast パターンと縮退適用条件を固定する。
3. [x] [ID: P0-CPP-S13-SAMECAST-CUT-01-S2-01] EAST3 または C++ emitter で同型 cast 縮退を実装する。
4. [x] [ID: P0-CPP-S13-SAMECAST-CUT-01-S3-01] 回帰を追加し、transpile/check を通す。

### P0: sample/13 `grid` 行アクセス hoist（最優先）

文脈: [docs/ja/plans/p0-cpp-s13-grid-row-hoist.md](../plans/p0-cpp-s13-grid-row-hoist.md)

1. [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01] sample/13 の 2 次元 `grid` アクセスで同一行取得を hoist し、繰り返し `py_at(grid, idx)` を削減する。
2. [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01-S1-01] row hoist 対象パターン（同一 index の `grid` 再参照）を定義する。
3. [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01-S2-01] emitter/optimizer に row hoist を実装し、sample/13 出力を縮退する。
4. [x] [ID: P0-CPP-S13-GRID-ROW-HOIST-01-S3-01] 回帰を追加し、transpile/check を通す。

### P0: sample/13 `while stack` の `.empty()` fastpath（最優先）

文脈: [docs/ja/plans/p0-cpp-s13-while-empty-fastpath.md](../plans/p0-cpp-s13-while-empty-fastpath.md)

1. [x] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01] typed list 経路の `while py_len(list) != 0` / `== 0` を `.empty()` 判定へ縮退する。
2. [x] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01-S1-01] typed list 条件式の fastpath 適用条件（`py_len(list) ==/!= 0`）を定義する。
3. [x] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01-S2-01] 条件式描画へ `.empty()` fastpath を実装する。
4. [x] [ID: P0-CPP-S13-WHILE-EMPTY-FASTPATH-01-S3-01] sample/13 回帰を追加し、transpile/check を通す。

### P0: C++ module import 関数の keyword 引数型伝播修正（最優先）

文脈: [docs/ja/plans/p0-cpp-module-keyword-coercion-fix.md](../plans/p0-cpp-module-keyword-coercion-fix.md)

1. [ ] [ID: P0-CPP-MODULE-KW-COERCE-01] module import 関数の keyword 引数で AST ノードを正しく型強制へ伝播し、冗長 `int64(py_to<int64>(...))` を削減する。
2. [ ] [ID: P0-CPP-MODULE-KW-COERCE-01-S1-01] module import 関数呼び出しで `args`/`kw` マージ時に `arg_nodes`/`kw_nodes` も同順序でマージする。
3. [ ] [ID: P0-CPP-MODULE-KW-COERCE-01-S2-01] `_coerce_args_for_module_function()` に merged nodes を渡し、keyword リテラルの型既知経路で冗長 cast を抑止する。
4. [ ] [ID: P0-CPP-MODULE-KW-COERCE-01-S2-02] sample/15 と keyword 順序入替ケースの回帰テストを追加し、`..., 4, 0)` 形を固定する。
5. [ ] [ID: P0-CPP-MODULE-KW-COERCE-01-S3-01] transpile check / unit / sample 再生成で非退行を確認する。

### P0: C++ `py_enumerate_list_as<T>()` 導入（最優先）

文脈: [docs/ja/plans/p0-cpp-enumerate-list-as-fastpath.md](../plans/p0-cpp-enumerate-list-as-fastpath.md)

1. [ ] [ID: P0-CPP-ENUM-LIST-AS-01] `cpp_list_model=pyobj` の typed enumerate 復元で中間 list コピーを除去し、`py_enumerate_list_as<T>()` 経路へ移行する。
2. [ ] [ID: P0-CPP-ENUM-LIST-AS-01-S1-01] runtime に `py_enumerate_list_as<T>(object[, start])` を追加し、`object(list<object>)` から typed tuple 列挙を生成する。
3. [ ] [ID: P0-CPP-ENUM-LIST-AS-01-S2-01] `stmt.py` の typed enumerate fastpath を `py_enumerate_list_as<str>(...)` 出力へ切替える。
4. [ ] [ID: P0-CPP-ENUM-LIST-AS-01-S2-02] sample/18 回帰テストの期待値を更新し、`py_to_str_list_from_object` 非依存を固定する。
5. [ ] [ID: P0-CPP-ENUM-LIST-AS-01-S3-01] unit/transpile/sample 再生成を実行し、非退行を確認する。

### P0: C++ `float64` cast 表記統一（最優先）

文脈: [docs/ja/plans/p0-cpp-float-cast-style-unification.md](../plans/p0-cpp-float-cast-style-unification.md)

1. [ ] [ID: P0-CPP-FLOAT-CAST-STYLE-01] C++ backend の `float64` cast 出力を `static_cast<float64>` から `float64(...)` へ統一する。
2. [ ] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S1-01] C++ emitter の `float64` cast 出力箇所を棚卸しし、統一対象/除外対象を固定する。
3. [ ] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S2-01] `apply_cast` と直接出力箇所を `float64(expr)` 優先へ変更し、`static_cast<float64>` を排除する。
4. [ ] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S2-02] `object/Any/unknown` 経路で `py_to<float64>` 維持を確認する回帰テストを追加する。
5. [ ] [ID: P0-CPP-FLOAT-CAST-STYLE-01-S3-01] transpile check / unit / sample 再生成で非退行を確認し、`sample/16` の該当出力差分を固定する。

### P0: EAST3 同型 `py_to<T>` 縮退（最優先）

文脈: [docs/ja/plans/p0-east3-pyto-identity-elimination.md](../plans/p0-east3-pyto-identity-elimination.md)

1. [ ] [ID: P0-EAST3-PYTO-IDENTITY-01] 同型 `py_to<T>` の削減を EAST3 最適化層へ主担当として移し、C++ emitter 側は安全網へ縮退する。
2. [ ] [ID: P0-EAST3-PYTO-IDENTITY-01-S1-01] 同型 `py_to<T>` 縮退規約（適用条件/除外条件）を EAST3 pass 仕様として固定する。
3. [ ] [ID: P0-EAST3-PYTO-IDENTITY-01-S2-01] EAST3 optimizer に同型 cast 縮退 pass を実装し、既存 pass 順序へ組み込む。
4. [ ] [ID: P0-EAST3-PYTO-IDENTITY-01-S2-02] C++ emitter 側の同型 cast 抑止を最終ガードに整理し、EAST3 pass 非適用時も fail-closed を維持する。
5. [ ] [ID: P0-EAST3-PYTO-IDENTITY-01-S3-01] unit / transpile check / sample 再生成で回帰を固定する。

### P1: Kotlin runtime 外出し（inline helper 撤去）

文脈: [docs/ja/plans/p1-kotlin-runtime-externalization.md](../plans/p1-kotlin-runtime-externalization.md)

1. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01] Kotlin backend の生成コードから `__pytra_*` helper 本体を撤去し、runtime 外部参照方式へ統一する。
2. [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S1-01] Kotlin emitter の inline helper 出力一覧と runtime API 対応表を確定する。
3. [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-01] Kotlin runtime 正本（`src/runtime/kotlin/pytra`）を整備し、`__pytra_*` API を外部化する。
4. [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-02] Kotlin emitter から helper 本体出力を撤去し、runtime 呼び出し専用へ切り替える。
5. [x] [ID: P1-KOTLIN-RUNTIME-EXT-01-S2-03] `py2kotlin.py` の出力導線で runtime ファイルを配置する。
6. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S3-01] `check_py2kotlin_transpile` / Kotlin smoke / parity を更新し、回帰を固定する。
7. [ ] [ID: P1-KOTLIN-RUNTIME-EXT-01-S3-02] `sample/kotlin` を再生成し、inline helper 残存ゼロを確認する。
- `P1-KOTLIN-RUNTIME-EXT-01-S1-01` `kotlin_native_emitter.py` の `_emit_runtime_helpers()` で inline 出力される `__pytra_*` 32 API と class依存 helper（`__pytra_is/as_<Class>`）を棚卸しし、`src/runtime/kotlin/pytra/py_runtime.kt`（現状 `runEmbeddedNode` のみ）とのギャップを計画書へ固定した。
- `P1-KOTLIN-RUNTIME-EXT-01-S2-01` `src/runtime/kotlin/pytra/py_runtime.kt` を helper 正本へ更新し、`__pytra_*` 32 API を runtime 側に実装した。`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin_smoke.py' -v`（10件）を通過した。
- `P1-KOTLIN-RUNTIME-EXT-01-S2-02` Kotlin emitter から `_emit_runtime_helpers()` 出力を撤去し、生成 `.kt` が runtime helper 本体を内包しないことを `test_py2kotlin_smoke.py`（10件）で確認した。
- `P1-KOTLIN-RUNTIME-EXT-01-S2-03` `py2kotlin.py` に `py_runtime.kt` 同梱コピーを追加し、`src/py2kotlin.py sample/py/01_mandelbrot.py -o /tmp/pytra_kotlin_case01.kt` で `/tmp/py_runtime.kt` 生成を確認した。

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
