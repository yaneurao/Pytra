# TODO

## EAST C++ 可読性

- [x] 比較・論理・算術の混在式で意味が変わらないことを `test/py` で回帰確認する。
- [x] Python docstring を C++ の裸文字列文として出さず、コメントへ変換するか出力しない。
- [x] 関数先頭の単独文字列式（docstring）を `east.py` 側で専用メタ情報へ分離する。
- [x] `py2cpp.py` は `//` コメント出力に統一する（必要時のみ）。
- [x] 式文としての識別子単体出力を禁止するガードを `py2cpp.py` に追加する。
- [x] API 由来が追えるように、必要箇所に薄いコメントを付ける（例: `png_helper.write_rgb_png` 対応）。
- [x] `write_rgb_png` / `save_gif` / `grayscale_palette` などランタイムブリッジ関数に限定して付与する。
- [x] コメントが過剰にならないよう最小限に制御する。
- [x] 生成コードのレイアウトを「意味単位」（初期化・計算・出力）で整える。
- [x] 連続宣言ブロック、連続代入ブロック、I/O 呼び出しブロックの間にのみ空行を入れる。
- [x] `sample/01` を可読性改善のゴールデンとして差分レビュー可能な形にする。

## self_hosted AST/Parser

- [x] 方針変更: `python_ast` backend は廃止し、`self_hosted` 単独運用とする。
- [x] `src/common/east.py` に `parser_backend` 切替インターフェースを導入する。
- [x] CLI 引数で `--parser-backend` を受け付ける。
- [x] デフォルトは `self_hosted` とする。
- [x] 変換結果メタに backend 名を記録する。
- [x] `self_hosted` の最小字句解析器を追加する（コメント/改行/インデント含む）。
- [x] `INDENT` / `DEDENT` / `NEWLINE` / `NAME` / `NUMBER` / `STRING` / 記号をトークン化する。
- [x] `#` コメントを収集し、行番号つきで保持する。
- [x] tokenize 失敗時のエラー位置・ヒントを EAST エラー形式で返す。
- [x] `self_hosted` の最小構文木（内部ノード）を定義する。
- [x] まず `Module`, `FunctionDef`, `Assign`, `AnnAssign`, `Return`, `Expr`, `If`, `For`, `Call`, `Name`, `Constant`, `BinOp`, `Compare` を対象にする。
- [x] 各ノードに `lineno/col/end_lineno/end_col` を持たせる。
- [x] `self_hosted` 用パーサ本体（再帰下降）を追加する。
- [x] 式の優先順位テーブルを実装する（`* / %`, `+ -`, 比較, `and/or`）。
- [x] `for ... in range(...)` と通常 `for ... in iterable` を識別する。
- [x] 関数定義と型注釈（`x: int` / `-> int`）を解釈する。
- [x] 既存 EAST ビルド処理に `self_hosted` ノード経路を追加する。
- [x] 既存の型推論・lowering（`ForRange`, `Contains`, `SliceExpr` など）を共通で再利用できる形にする。
- [x] `self_hosted` 単独運用で EAST の形が安定するように正規化する。
- [x] コメント引き継ぎを実装する（`#` / docstring）。
- [x] `#` コメントを `leading_comments` として関数/文に紐づける。
- [x] `Expr(Constant(str))` の docstring と重複しないよう統合規則を決める。
- [x] `src/py2cpp.py` で `leading_comments` を `// ...` 出力する。

### ケース順移行（test/py/case01 から順に）

- [x] `case11_fib` を `self_hosted` で通す。
- [x] `case12_string_ops` を `self_hosted` で通す。
- [x] `case13_class` 〜 `case16_instance_member`（クラス系）を `self_hosted` で通す。
- [x] `case17_loop` 〜 `case24_ifexp_bool`（ループ/例外/内包/ifexp）を `self_hosted` で通す。
- [x] `case25_class_static` 〜 `case33_pathlib_extended`（拡張ケース）を `self_hosted` で通す。

### 切替完了条件

- [x] `test/py` 全ケースで `self_hosted` EAST が意味的に安定していることを確認する。
- [x] `src/py2cpp.py` で `--parser-backend self_hosted` 時に `test/py` 全ケースが実行一致する。
- [x] デフォルト backend を `self_hosted` に変更する。

## 生成画像不一致 調査（2026-02-17）

- [x] `save_gif(..., delay_cs=..., loop=...)` の keyword 引数を `py2cpp.py` の非lowered `Call` 経路でも確実に反映する。
- [x] 現状 `sample/cpp/*` で `save_gif(..., palette)` のみになり `delay_cs` が既定値 `4` に落ちる問題を修正する。
- [x] `sample/05,06,08,10,11,14` で GIF の GCE delay 値が Python 実行結果と一致することを確認する。
- [x] 浮動小数点式の再結合（演算順序変更）を抑制し、Python と同じ評価順を優先する。
- [x] `a * (b / c)` が `a * b / c` に変わらないように、`render_expr` の括弧方針を見直す。
- [x] `sample/01_mandelbrot` と `sample/03_julia_set` で PNG の raw scanline が一致することを確認する。
- [x] PNG 出力の差分を「画素差」と「圧縮差」に切り分けた上で、仕様として扱いを明文化する。
- [x] `sample/02_raytrace_spheres` は画素一致・IDAT 圧縮差のみであることを docs に追記する。
- [x] 必要なら C++ 側 `src/cpp_module/png.cpp` を zlib 圧縮実装へ寄せ、IDAT 近似一致または完全一致方針を決める。
- [x] GIF の `sample/12_sort_visualizer` / `sample/16_glass_sculpture_chaos` のフレーム画素差を解消する。
- [x] `render()` 内の float→int 変換境界（bar幅/補間/正規化）の評価順を Python と一致させる。
- [x] フレームデータ（LZW 展開後）が全フレーム一致することを確認する。
- [x] 画像一致検証を自動化する。
- [x] `sample/py` 全件について、`stdout` 比較に加えて PNG raw / GIF フレーム一致を検証するスクリプトを追加する。
- [x] 差分時は「最初の不一致座標・チャネル・元式」を出力できるようにする。

## クラス値型最適化の再設計（case15 / case34）

- [x] 方針を明文化する: Pythonのユーザー定義クラスは参照セマンティクスを原則とし、値型化は「意味保存が証明できる場合のみ」許可する。
- [x] `case34_gc_reassign` を回帰ゴールデンに設定し、`a = b` 後に同一オブジェクト共有（コピーで2個化しない）を必須条件にする。
- [x] 値型化の適用条件を仕様化する（例: インスタンスフィールドなし、`__del__` なし、インスタンス同一性に依存する操作なし、代入/引数渡しで共有観測されない）。
- [x] EAST 解析段階で「値型化候補クラス」と「参照必須クラス」を分類するメタ情報を追加する。
- [x] `src/py2cpp.py` にクラスごとのストレージ戦略選択（`rc<T>` / `T`）を実装し、混在ケースで正しく `.` と `->` を切り替える。
- [x] `case15_class_member` は以前どおり `Counter c = Counter();` へ戻す（最適化適用例）。
- [x] `case34_gc_reassign` は `rc<Tracked>` のまま維持する（最適化非適用例）。
- [x] 新規テストを追加する: 同一性依存ケース（代入共有、関数引数経由の更新共有、コンテナ格納後の共有）では必ず参照型を選ぶことを検証する。
- [x] 新規テストを追加する: 値型化候補（実質 stateless クラス）では出力C++が値型になり、実行結果がPython一致することを検証する。

## selfhost（`py2cpp.py` を `py2cpp.py` で変換）

- [x] selfhost一次ゴールを固定する: `python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` が成功する。
- [x] self-hosted parser で関数定義シグネチャの `*`（keyword-only 引数マーカー）を解釈可能にする。
- [x] `*` 対応後、`selfhost/py2cpp.py` の EAST 生成が最後まで通ることを確認する。
- [x] 関数定義シグネチャでの未対応要素（`/`, `*args`, `**kwargs`）の扱いを仕様化する（受理/拒否とエラーメッセージ）。
- [x] `src/common/east.py` の対応箇所へ最小コメントを追加し、どのシグネチャ構文をサポートするか明記する。
- [ ] `test/py` にシグネチャ構文テストを追加する（`*` を含むケース、拒否すべきケース）。
- [ ] `selfhost/py2cpp.py` のトランスパイルが通ったら、`selfhost/py2cpp.cpp` のコンパイルまで確認する。
- [ ] `selfhost/py2cpp.cpp` 実行で `sample/py/01` を変換させ、`src/py2cpp.py` の生成結果と一致比較する。
- [ ] 一致条件を定義する（C++ソース全文一致か、コンパイル可能性＋実行結果一致か）を `docs/spec-dev.md` に追記する。
- [ ] selfhost手順を `docs/how-to-use.md` に追記する（前提、コマンド、失敗時の確認ポイント）。

### selfhost C++コンパイル段階の未解決（2026-02-18）

- [x] self_hosted parser の `STR` 解析で prefix 付き文字列（`f/r/b/u/rf/fr`）を正しく扱えるようにする。
- [x] self_hosted parser の `f-string` を `JoinedStr/FormattedValue` に落とす（最低限 `{expr}` と `{{` `}}`）。
- [ ] 型注釈 `Any` を C++出力で扱えるようにする（最低でも `object` 互換に正規化する）。
- [ ] PEP604 形式の union (`T | None`) を EAST または C++型変換段で受理し、C++型へ正規化する。
- [ ] `dict[str, Any]` / `dict[str, str | None]` のようなネスト型注釈を C++出力時に安全に解決する。
- [ ] `call(generator_exp)` の lowering を明示仕様化する（`list-comp` へ正規化するか、専用 `GeneratorExp` を実装するか）。
- [ ] selfhost 生成C++（`selfhost/py2cpp.cpp`）のコンパイルエラーをカテゴリ別に整理し、最小修正順で潰す。
- [ ] `dict[str, Any]` に対する `.get(...).items()` 連鎖を C++ で確実に展開できるようにする（`py_dict_get_default` と `items` 展開の型整合）。
- [ ] `list[set[str]]` など「属性側の既知型」と「RHS リテラルの unknown 推論」の不一致を解消する（例: `self.scope_stack = [set()]`）。
- [ ] self_hosted parser の `BoolOp`（`or/and`）を値選択用途で使った場合の扱いを定義する（現状は bool 演算へ寄るため selfhost で破綻しやすい）。
- [ ] `str` メソッドの selfhost 対応を追加する（`strip/rstrip/startswith/endswith/replace/join`）。
- [ ] `reversed/enumerate` の selfhost 変換を追加する（ランタイムヘルパ or EAST lower）。
- [ ] `std::any` と `optional[T]` の橋渡しを整理する（`== None`、`if x is None`、`dict.get` 戻り値）。
- [ ] `emit_module_leading_trivia` / `emit_leading_comments` の一時無効化を解除し、コメント/空行保持を selfhost でも再有効化する。
