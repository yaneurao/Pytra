# TODO

## selfhost（`py2cpp.py` を `py2cpp.py` で変換）

- [x] `test/fixtures` にシグネチャ構文テストを追加する（`*` を含むケース、拒否すべきケース）。
- [ ] `selfhost/py2cpp.py` のトランスパイルが通ったら、`selfhost/py2cpp.cpp` のコンパイルまで確認する。
- [ ] `selfhost/py2cpp.cpp` 実行で `sample/py/01` を変換させ、`src/py2cpp.py` の生成結果と一致比較する。
- [x] 一致条件を定義する（C++ソース全文一致か、コンパイル可能性＋実行結果一致か）を `docs/spec-dev.md` に追記する。
- [x] selfhost手順を `docs/how-to-use.md` に追記する（前提、コマンド、失敗時の確認ポイント）。

### selfhost C++コンパイル段階の未解決（2026-02-18）

#### A. 型系の正規化（EAST -> C++型）

- [x] `Any` を `object`（`std::any`）へ正規化するルールを `src/py2cpp.py` の型変換入口に一元化する。
- [ ] `Any` が関数引数・戻り値・ローカル変数・dict/list/set要素の全位置で同じルールで解決されることを確認する。
- [x] PEP604 (`T | None`) を EAST 側で正規化するか、C++型変換時に `optional<T>` へ正規化するかを決定し実装する。
- [x] `dict[str, Any]` / `dict[str, str | None]` を含むネスト型で、`cpp_type()` が一貫した型文字列を返すよう修正する。
- [ ] `list[set[str]]` など既知型プロパティへの代入で、RHS の `unknown` が残らないよう推論優先順位を定義・実装する。
- [x] 上記の型規則を `docs/spec-east.md` に追記する。

#### B. `std::any` と `optional` の橋渡し

- [x] `== None` / `!= None` / `is None` / `is not None` が `std::any` 値でも安全に評価できる補助関数を `py_runtime.h` に追加する。
- [x] `dict.get()` の戻り値が `std::any` の場合、`optional<T>` へ安全に変換するヘルパを追加する。
- [x] `emit_stmt` / `render_expr` で `std::any` と `optional<T>` の比較が直接生成されないようガードする。
- [ ] `selfhost/py2cpp.cpp` の `no match for operator==(... nullopt_t)` 系エラーが消えることを確認する。

#### C. 文字列/反復ユーティリティの selfhost 対応

- [x] `strip/rstrip/startswith/endswith/replace/join` を C++ ランタイム関数へマッピングする（`py_runtime.h`）。
- [x] `src/py2cpp.py` で上記メソッド呼び出しを C++ 標準APIまたはランタイムAPIへ lowering する。
- [x] `reversed()` の lowering を追加する（`for` で使うケースを優先）。
- [x] `enumerate()` の lowering を追加する（`for i, x in enumerate(...)` を優先）。
- [x] `no member named 'startswith'` / `'replace'` / `reversed not declared` / `enumerate not declared` のビルドエラー解消を確認する。

#### D. `dict/list` 動的アクセスの整合

- [x] `dict[str, Any]` に対する `.get(...).items()` の典型パターンを最小再現ケース化する（`test/fixtures` 追加）。
- [x] `py_dict_get_default` の戻り値型に応じて `.items()` を安全に展開する経路を実装する。
- [ ] `list<any>` / `dict<any>` 反復時の `begin/end` 解決をランタイム側かコード生成側のどちらかに統一する。
- [ ] `cannot convert std::any to dict/list` 系エラーが消えることを確認する。

#### E. BoolOp と値選択（`or/and`）

- [x] `BoolOp` を真偽演算として扱うケースと「値選択式」として扱うケースを仕様として分離する。
- [x] EAST 生成時に値選択用 `or/and` を明示ノードへ lower するか、`py2cpp.py` 側で特別扱いするかを決定する。
- [ ] selfhost の `t = x or ""` / `v = y and z` パターンで C++ 型崩壊しないことを確認する。
- [x] 仕様を `docs/spec-east.md` か `docs/spec.md` に追記する。

#### F. コメント・空行保持の復旧

- [x] 一時無効化した `emit_module_leading_trivia` を再有効化する。
- [x] 一時無効化した `emit_leading_comments` を再有効化する。
- [x] `selfhost/py2cpp.py` 変換時にもコメント行・空行が保持されることを `sample/py/01` で確認する。

#### G. 検証フローの固定

- [x] selfhost 用の固定コマンド列（EAST生成 -> C++生成 -> g++コンパイル）を `docs/how-to-use.md` に追記する。
- [x] ビルドエラーをカテゴリ別に出す簡易チェックコマンド（`rg "error:"`）を手順に含める。
- [x] `selfhost/py2cpp.cpp` がコンパイル成功することをゴール条件に明記する。
- [x] `selfhost` 実行で `sample/py/01` を変換し、`src/py2cpp.py` 生成結果と比較する検証手順を追記する。
- [x] 一致判定条件（ソース一致 / 実行一致 / 画像一致）を `docs/spec-dev.md` に明記する。

#### H. selfhost ビルドエラー直接解消（2026-02-18 再分類）

- [ ] `src/py2cpp.py` 内の `Any` パラメータ補助関数を廃止し、`dict`/`list[dict]` 前提の経路へ寄せる。
- [ ] `stmt.get(...)` の戻り値が `std::any` 化される箇所を、`isinstance(..., dict)` ガード付きローカル変数へ統一する。
- [ ] 1文字アクセス（`s[i]`）由来の `char`/`str` 型崩壊を避けるため、文字判定ロジックを再実装する。
- [ ] `strip/startswith/endswith/replace/join` の Python 文字列APIを C++ 側 API に落とす明示ルートを追加する。
- [ ] `enumerate` / `reversed` が生で残る経路を EAST か lowering で除去する。
- [ ] `py_is_none` 追加分を selfhost 側ランタイムにも同期し、未定義エラーを解消する。
- [x] `src/py2cpp.py -> selfhost/py2cpp.py` 同期後に `selfhost/py2cpp.cpp` を再生成し、エラー件数の減少を記録する。

進捗メモ（2026-02-18）:
- `py_runtime.h` に `std::any` 反復補助（`std::begin/std::end`）と `py_slice(std::any)`, `py_reversed(std::any)`, `py_enumerate(std::any)` を追加。
- `src/py2cpp.py` の `render_minmax` で `t` 未定義になる経路を修正。
- `src/py2cpp.py` の文字列リテラル生成で `json.dumps` 依存を除去（`cpp_string_lit`）。
- `src/py2cpp.py` の `cpp_type` 入力型を `Any` 化。
- `dict[str, Any]` 初期化時に `std::any` へ再帰変換する経路と、tuple unpack `for` の単文最適化不備を修正。
- `BoolOp` は C++ 生成時に「真偽演算」と「値選択式」を分離して出力する経路を追加（`test/fixtures/collections/boolop_value_select.py` で検証）。
- selfhost C++コンパイルエラー件数: `438 -> 396 -> 393 -> 374 -> 328 -> 333 -> 335`（新機能追加後の再計測）。
