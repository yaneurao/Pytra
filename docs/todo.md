# TODO

## EAST C++ 可読性

- [ ] 比較・論理・算術の混在式で意味が変わらないことを `test/py` で回帰確認する。
- [ ] Python docstring を C++ の裸文字列文として出さず、コメントへ変換するか出力しない。
- [ ] 関数先頭の単独文字列式（docstring）を `east.py` 側で専用メタ情報へ分離する。
- [ ] `py2cpp.py` は `//` コメント出力に統一する（必要時のみ）。
- [ ] 式文としての識別子単体出力を禁止するガードを `py2cpp.py` に追加する。
- [ ] API 由来が追えるように、必要箇所に薄いコメントを付ける（例: `png_helper.write_rgb_png` 対応）。
- [ ] `write_rgb_png` / `save_gif` / `grayscale_palette` などランタイムブリッジ関数に限定して付与する。
- [ ] コメントが過剰にならないよう最小限に制御する。
- [ ] 生成コードのレイアウトを「意味単位」（初期化・計算・出力）で整える。
- [ ] 連続宣言ブロック、連続代入ブロック、I/O 呼び出しブロックの間にのみ空行を入れる。
- [ ] `sample/01` を可読性改善のゴールデンとして差分レビュー可能な形にする。

## self_hosted AST/Parser

- [ ] `src/common/east.py` に `parser_backend` 切替を導入する（`python_ast` / `self_hosted`）。
- [ ] CLI 引数で `--parser-backend` を受け付ける。
- [ ] デフォルトは `python_ast` のまま維持する。
- [ ] 変換結果メタに backend 名を記録する。
- [ ] `self_hosted` の最小字句解析器を追加する（コメント/改行/インデント含む）。
- [ ] `INDENT` / `DEDENT` / `NEWLINE` / `NAME` / `NUMBER` / `STRING` / 記号をトークン化する。
- [ ] `#` コメントを収集し、行番号つきで保持する。
- [ ] tokenize 失敗時のエラー位置・ヒントを EAST エラー形式で返す。
- [ ] `self_hosted` の最小構文木（内部ノード）を定義する。
- [ ] まず `Module`, `FunctionDef`, `Assign`, `AnnAssign`, `Return`, `Expr`, `If`, `For`, `Call`, `Name`, `Constant`, `BinOp`, `Compare` を対象にする。
- [ ] 各ノードに `lineno/col/end_lineno/end_col` を持たせる。
- [ ] `self_hosted` 用パーサ本体（再帰下降）を追加する。
- [ ] 式の優先順位テーブルを実装する（`* / %`, `+ -`, 比較, `and/or`）。
- [ ] `for ... in range(...)` と通常 `for ... in iterable` を識別する。
- [ ] 関数定義と型注釈（`x: int` / `-> int`）を解釈する。
- [ ] 既存 EAST ビルド処理に `self_hosted` ノード経路を追加する。
- [ ] 既存の型推論・lowering（`ForRange`, `Contains`, `SliceExpr` など）を共通で再利用できる形にする。
- [ ] `python_ast` と `self_hosted` で EAST の形が揃うように正規化する。
- [ ] コメント引き継ぎを実装する（`#` / docstring）。
- [ ] `#` コメントを `leading_comments` として関数/文に紐づける。
- [ ] `Expr(Constant(str))` の docstring と重複しないよう統合規則を決める。
- [ ] `src/py2cpp.py` で `leading_comments` を `/* ... */` 出力する。

### ケース順移行（test/py/case01 から順に）

- [ ] `case11_fib` を `self_hosted` で通す。
- [ ] `case12_string_ops` を `self_hosted` で通す。
- [ ] `case13_class` 〜 `case16_instance_member`（クラス系）を `self_hosted` で通す。
- [ ] `case17_loop` 〜 `case24_ifexp_bool`（ループ/例外/内包/ifexp）を `self_hosted` で通す。
- [ ] `case25_class_static` 〜 `case33_pathlib_extended`（拡張ケース）を `self_hosted` で通す。

### 切替完了条件

- [ ] `test/py` 全ケースで `python_ast` と `self_hosted` の EAST が意味的に一致する。
- [ ] `src/py2cpp.py` で `--parser-backend self_hosted` 時に `test/py` 全ケースが実行一致する。
- [ ] デフォルト backend を `self_hosted` に変更し、`python_ast` はフォールバック扱いにする。

## 生成画像不一致 調査（2026-02-17）

- [ ] `save_gif(..., delay_cs=..., loop=...)` の keyword 引数を `py2cpp.py` の非lowered `Call` 経路でも確実に反映する。
- [ ] 現状 `sample/cpp/*` で `save_gif(..., palette)` のみになり `delay_cs` が既定値 `4` に落ちる問題を修正する。
- [ ] `sample/05,06,08,10,11,14` で GIF の GCE delay 値が Python 実行結果と一致することを確認する。
- [ ] 浮動小数点式の再結合（演算順序変更）を抑制し、Python と同じ評価順を優先する。
- [ ] `a * (b / c)` が `a * b / c` に変わらないように、`render_expr` の括弧方針を見直す。
- [ ] `sample/01_mandelbrot` と `sample/03_julia_set` で PNG の raw scanline が一致することを確認する。
- [ ] PNG 出力の差分を「画素差」と「圧縮差」に切り分けた上で、仕様として扱いを明文化する。
- [ ] `sample/02_raytrace_spheres` は画素一致・IDAT 圧縮差のみであることを docs に追記する。
- [ ] 必要なら C++ 側 `src/cpp_module/png.cpp` を zlib 圧縮実装へ寄せ、IDAT 近似一致または完全一致方針を決める。
- [ ] GIF の `sample/12_sort_visualizer` / `sample/16_glass_sculpture_chaos` のフレーム画素差を解消する。
- [ ] `render()` 内の float→int 変換境界（bar幅/補間/正規化）の評価順を Python と一致させる。
- [ ] フレームデータ（LZW 展開後）が全フレーム一致することを確認する。
- [ ] 画像一致検証を自動化する。
- [ ] `sample/py` 全件について、`stdout` 比較に加えて PNG raw / GIF フレーム一致を検証するスクリプトを追加する。
- [ ] 差分時は「最初の不一致座標・チャネル・元式」を出力できるようにする。
