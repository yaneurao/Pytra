# TODO

- [x] セルフホスティング済みトランスパイラ実行ファイル（`test/transpile/obj/pycpp_transpiler_self_new`）を使って、`test/fixtures/case05` から `test/fixtures/case100` までを `test/transpile/cpp2/` に変換し、各生成 C++ がコンパイル可能かを一括検証した。
  - 実施結果: `CASE_TOTAL=96`, `TRANSPILE_FAIL=0`, `COMPILE_OK=96`, `COMPILE_FAIL=0`

## トランスパイラ機能 TODO（今回の不足点整理）

- [x] `AugAssign`（`+=`, `-=`, `*=`, `/=`, `%=`, `//=`, `|=` など）を網羅対応する。
- [x] `**`（べき乗）を C++ 側で正しく変換する（`pow` 変換や整数演算最適化を含む）。
- [x] `bytearray(n)` / `bytes(...)` の初期化と相互変換を Python 互換に強化する。
- [x] `list.pop()` / `list.pop(index)` の両方に対応する（現在は引数なし中心）。
- [x] `math` モジュール互換を拡張する（`sin`, `cos`, `exp`, `pi` 以外も含め網羅）。
- [x] `gif` 出力ランタイム（`save_gif`, パレット関数）を `py_module` / `cpp_module` 対応で正式仕様化し、テストを追加する。
- [x] 連鎖比較（例: `0 <= x < n`）を AST から正しく展開して変換する。

## サンプル作成時に判明した追加TODO（05〜14対応）

- [x] `int / int` を含む `/` 演算で、Python互換の実数除算を保証する型昇格ルールを導入する。
- [x] `list` など空コンテナ初期化（`x = []`, `x = {}`）の型推論を強化し、`auto x = {}` の誤生成を防止する。
- [x] `bytes` / `bytearray` 系 API の変換規則を整理し、`extend(tuple)` のような利用も含めて互換を高める。
- [x] `def main()` がある入力でのエントリポイント衝突を避けるルール（自動リネームなど）を実装する。
- [x] list comprehension / nested list comprehension をサポートする（現状は手書きループへ書き換えが必要）。
- [x] 添字代入（`a[i] = v`, `a[i][j] = v`）を含む代入系の回帰テストを追加し、`// unsupported assignment` 混入を検知する。
- [x] `list.pop()` / `list.pop(index)` / `append` / `extend` など主要メソッド変換の互換テストを拡充する。

## sample/py 実行一致で追加対応が必要な項目

### py2cs.py 側

- [x] `import math` / `math.sqrt` などモジュール経由呼び出しを C# 側で正しく解決する（`math` 名未解決エラーを解消する）。
- [x] `from __future__ import annotations` を C# 変換時に無視する（`using __future__` を生成しない）。
- [x] Python 変数名が C# 予約語（例: `base`）と衝突した場合の自動リネーム規則を実装する。
- [x] `for ... in range(...)` 変換時の一時変数名衝突を防ぐ（ネスト時に `__range_*` が重複しないようにする）。
- [x] `for ... in range(...)` 変換時のループ変数再宣言衝突を防ぐ（既存ローカルと同名を再宣言しない）。
- [x] 大きな整数リテラル（例: `4294967296`）を含む代入で型変換エラーが出ないようにする（`int` / `long` の扱いを調整する）。

### py2cpp.py 側

- [x] `sample/py/04_monte_carlo_pi.py` を浮動小数点依存のサンプルから整数チェックサム系サンプルへ置き換え、言語間比較の安定性を上げる。
- [x] `for ... in range(...)` 変換時の一時変数名衝突を防ぐ（`sample/py/12_sort_visualizer.py` のコンパイル失敗を解消する）。

## sample/py/15 追加時に見えた変換器側TODO

- [x] `int(<str>)` の数値変換を `py2cpp.py` / `py2cs.py` で正しく変換する（手動パース回避）。
- [x] 文字列の 1 文字添字（`s[i]`）を Python と整合する形で C++/C# に変換する（`char`/`string` 差の吸収）。
- [x] `str` の比較（`"a" <= ch <= "z"` のような範囲比較）を C# 含め正しく変換する。
- [x] `while True: ... return ...` 形式で C# 側の「全経路 return」誤検知が出ないよう制御フロー解析を改善する。
- [x] 空リスト初期化（`x: list[T] = []`）を C# 側で `List<T>` として安定生成する（`List<object>` への退化を防止）。
- [x] メソッド呼び出し経由の型付き空コンテナ生成（`self.new_list()` 等）を常時許容し、`Only direct function calls are supported` を解消する。
- [x] `dict` 参照で C++ 側が `const` 扱いになる問題（`env[key]`）を生成側で解決し、入力コードにダミー書き込みを要求しない。
- [x] C++ の `%` はランタイム吸収せず直接生成する方針へ変更し、負数オペランドを仕様対象外として明記する。
- [x] 行連結文字列（`\n` を含む長いソース文字列）からのトークナイズが C++/C# 生成で壊れないよう文字列エスケープ処理を強化する。
- [x] 変換器都合で入力 Python を書き換えなくて済むよう、`sample/py/15` で行った回避実装をトランスパイラ側へ吸収する。

## sample/py の簡潔化候補（Python組み込み活用）

- [x] `sample/py/15_mini_language_interpreter.py`: 手動の数値文字列パースを `int(token_num.text)` に置き換える。
- [x] `sample/py/14_raymarching_light_cycle.py`: `if x > 255: x = 255` 系を `min(255, x)` に統一する（`r`, `g`, `b`, `v`）。
- [x] `sample/py/11_lissajous_particles.py`: `if v < 0: v = 0` を `max(0, v)` に置き換える。
- [x] `sample/py/09_fire_simulation.py`: 二重ループ初期化を `[[0] * w for _ in range(h)]` に置き換える。
- [x] `sample/py/13_maze_generation_steps.py`: `grid` 初期化を `[[1] * cell_w for _ in range(cell_h)]` に置き換える。
- [x] `sample/py/13_maze_generation_steps.py`: `while len(stack) > 0` を `while stack` に置き換える。
- [x] `sample/py/13_maze_generation_steps.py`: `stack[-1]` を使って末尾要素アクセスを簡潔化する。
- [x] `sample/py/12_sort_visualizer.py`: 一時変数スワップをタプル代入（`a, b = b, a`）へ置き換える。

## Go / Java ネイティブ変換の追加TODO

- [x] `py2go.py` / `py2java.py` を Python 呼び出し不要のネイティブ変換モードへ移行する。
- [x] `test/fixtures`（case01〜30）を Go/Java ネイティブ変換して、Python 実行結果と一致させる。
- [x] `sample/py` で使っている `math` モジュール呼び出し（`sqrt`, `sin`, `cos` など）を Go/Java ネイティブ変換で対応する。
- [x] `sample/py` で使っている `png_helper.write_rgb_png` の Go/Java ランタイム実装を追加する。
- [x] `sample/py` で使っている `gif_helper.save_gif` / `grayscale_palette` の Go/Java ランタイム実装を追加する。

## Rust 追加TODO（現時点）

- [x] `src/rs_module/py_runtime.rs` の `py_write_rgb_png` で、Python 側 `png_helper.write_rgb_png` とバイナリ完全一致（IDAT 圧縮形式を含む）を実現する。
  - 方針変更: この厳密一致要件は今後は実施不要とし、完了扱いとする。
- [x] `py2rs.py` の `use py_runtime::{...}` 生成を使用関数ベースに最適化し、未使用 import 警告を削減する。

## 言語間ランタイム平準化 TODO

- [x] C++ のみ対応になっている `math` 拡張関数（`tan`, `log`, `log10`, `fabs`, `ceil`, `pow` など）を、Rust / C# / JS / TS / Go / Java / Swift / Kotlin の各ランタイムにも同等実装する。
- [x] C++ のみ実装が進んでいる `pathlib` 相当機能を、他ターゲット言語にも同一 API で実装する（`Path` の生成・結合・存在確認・文字列化など）。
  - [x] `pathlib` 最小共通 API を確定する（`Path(...)`, `/`, `exists`, `resolve`, `parent`, `name`, `stem`, `read_text`, `write_text`, `mkdir`, `str`）。
  - [x] `src/rs_module` / `src/cs_module` / `src/js_module` / `src/ts_module` / `src/go_module` / `src/java_module` に `pathlib` 相当ランタイムを追加する。
  - [x] `py2cpp.py` 以外の各トランスパイラで `import pathlib` と `Path` 呼び出しのマッピングを実装する。
  - [x] `sample/py` もしくは `test/fixtures` にファイルI/Oを伴う `pathlib` 利用ケースを追加し、各言語で実行確認する。
- [x] 上記の平準化後、`docs/pytra-readme.md` の「対応module」を言語別の対応関数一覧で更新し、差分がある場合は理由を明記する。
  - [x] `math` / `pathlib` の言語別対応表を `docs/pytra-readme.md` に追加する。
  - [x] 未対応関数が残る言語には「未対応理由・代替手段・予定」を併記する。
  - [x] `README.md` / `docs/how-to-use.md` から参照される説明との整合を確認する。
- [x] `test/fixtures` に `math` / `pathlib` の共通回帰テストを追加し、全ターゲット言語で同一期待値を満たすことを CI 相当手順で確認する。
  - [x] `test/fixtures` に `math` 拡張（`tan/log/log10/fabs/ceil/pow`）の共通テストケースを追加する。
  - [x] `test/fixtures` に `pathlib` 共通テストケース（生成・結合・存在確認・読み書き）を追加する。
  - [x] 各ターゲット（C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin）への変換・実行コマンドを自動化スクリプトへ集約する。
  - [x] Python 実行結果との差分比較を自動化し、失敗ケースを一覧出力できるようにする。
  - 実行補足: 現在の開発環境では `mcs/go/javac/swiftc/kotlinc` が未導入のため、`tools/runtime_parity_check.py` は該当ターゲットを `SKIP` 表示で処理する。

## EAST / CppEmitter 簡素化 TODO

- [x] `east.py` 側で式を低レベル化し、`CppEmitter` の `Call` 分岐を削減する。
  - [x] `math.*`, `Path.*`, `len`, `print`, `str`, `int`, `float`, `bool`, `bytes`, `bytearray` を `BuiltinCall` 系ノードへ正規化する。
  - [x] `CppEmitter` は `BuiltinCall` 名と引数をそのまま C++ ランタイム呼び出しへマッピングする。
- [x] `Compare` の `in` / `not in` を専用ノード化し、コンテナ種別分岐を `east.py` 側で確定する。
  - [x] `Contains(container, key, negated)` ノードを追加する。
  - [x] `dict` と `list/set/tuple/str` の判定分岐を `east.py` 側に寄せる。
- [x] `slice` を専用ノード化し、`CppEmitter` の `Subscript` 条件分岐を削減する。
  - [x] `SliceExpr(value, lower, upper)` ノードを追加する。
  - [x] `Subscript` は単一添字アクセスに限定して表現する。
- [x] `JoinedStr`（f-string）を `Concat` 系へ事前展開し、文字列化規則を `east.py` で確定する。
  - [x] `FormattedValue` の型に応じた `to_string` 方針を EAST ノードに埋め込む。
  - [x] `CppEmitter` 側は連結出力のみを行う。
- [x] 代入ノードに宣言情報を持たせ、`CppEmitter` 側のスコープ推測ロジックを削減する。
  - [x] `Assign` / `AnnAssign` に `declare` / `decl_type` を追加する。
  - [x] `AugAssign` の未宣言時挙動を `east.py` で正規化する。
- [x] クラスノード情報を拡張し、`emit_class` の推測処理を削減する。
  - [x] `ClassDef` に `base`, `field_types`, `field_defaults`, `constructor_signature` を持たせる。
  - [x] dataclass/`__init__` の constructor 生成方針を EAST 側で確定する。
- [x] `For` 系の正規化を強化し、`CppEmitter` の `for` 出力を単純化する。
  - [x] `ForRange` と `ForEach` を完全分離し、`target_type` を持たせる。

## 保留（Go / Java は EAST 化まで凍結）

- Go/Java で、Python 側に型注釈がある変数・引数・戻り値を `any` / `Object` へ退化させず、可能な限り静的型（`int`/`float64`/`string`/`bool`/`[]byte`/`byte[]`/コンテナ型）へ落とす。
- `src/common/go_java_native_transpiler.py` の型注釈解釈を拡張し、`list[T]` / `dict[K,V]` / `set[T]` / `tuple[...]` を内部型タグへ保持する。
- 関数シグネチャ生成で、引数・戻り値の型注釈を Go/Java の静的型へ優先反映する（未注釈時のみ `any` / `Object`）。
- ローカル変数宣言で、型注釈付き代入 (`AnnAssign`) を `var/object` ではなく具体型で宣言する。
- コンテナ操作（`append`, `pop`, `pyGet`, `pySet`）のコード生成を型付きコンテナ前提で整合させる。
- `sample/py/15` 相当の複合ケースで Go/Java 生成コードの型退化が再発しないことを確認する。
- Go/Java の `bytes` / `bytearray` 型注釈を優先して `[]byte` / `byte[]` へ反映し、`any` / `Object` ベース実装は型未確定ケースのみに限定する。
- 型注釈 `bytes` / `bytearray` を内部型タグで区別し、宣言時に Go:`[]byte` / Java:`byte[]` で出力する。
- `bytes(...)` / `bytearray(...)` / `pyToBytes` 周辺の生成コードで不要な `any` / `Object` キャストを削減する。
- 添字アクセス・代入・`append` / `extend` / `pop` の `[]byte` / `byte[]` パスを優先する分岐を追加する。
- `sample/py` の PNG/GIF 系ケースで、バイト列が終始 `[]byte` / `byte[]` で通ることを確認する。
  - [x] `range_mode` と境界条件の確定を `east.py` 側で完了させる。
- [x] `CppEmitter` を「文字列出力専用」へ段階移行し、挙動回帰を防ぐ。
  - [x] 各段階で `test/fixtures` の `test/transpile/cpp` 実行結果一致を確認する。
  - [x] 各段階で `sample/py` の PNG/GIF 一致（バイナリ比較）を確認する。

## EAST C++可読性改善 TODO

- [x] `east/py2cpp.py` の括弧出力を簡素化し、不要な多重括弧（`if ((((...)))` など）を削減する。
  - [x] 演算子優先順位テーブルを導入し、必要な箇所だけ括弧を残す。
- [x] `r; g; b;` のような無意味な式文を出さない。
  - [x] 未初期化宣言のみ必要な場合は `int64 r;` の宣言で完結させる。
- [x] `for (i += (1))` 形式を C++らしい表記（`++i` など）へ寄せる。
  - [x] `step == 1` / `-1` の場合は `++i` / `--i` を使う。
  - [x] その他の step のみ `i += step` を維持する。

## EAST py2cpp sample対応 TODO（完了）

- [x] `sample/py` の `list.append(...)` / `frames.append(...)` を C++ `vector::push_back` へ正しく変換する。
  - [x] `Call(Attribute(..., "append"))` の lowered 情報を優先し、`append` を生のまま出力しない。
  - [x] `list[uint8]` / `list[list[uint8]]` / `list[Token]` など複数型で回帰テストする。
- [x] `perf_counter()` を C++ で解決する（`time` ランタイム呼び出しへマップ）。
  - [x] `east/cpp_module/py_runtime.h` もしくは適切な `cpp_module/time.h` 経由で利用可能にする。
  - [x] `sample/py` の計測系ケース（04,05,06,08,10,12,13）でコンパイル通過を確認する。
- [x] `range(...)` は `py2cpp.py` で処理せず、EAST 構築時点で消し切る。
  - [x] list comprehension 等の lowered 出力で `range` を未定義関数として出さない（生の `Call(Name("range"))` を残さない）。
  - [x] `for in range` 以外の利用（式位置・代入・引数渡し）がある場合も、EAST専用ノードへ lower して後段へ渡す。
  - [x] `py2cpp.py` 側に `range` 意味解釈を追加しない（残っていたらバグとして検出する）。
- [x] `min` / `max` の出力を `std::min` / `std::max`（型整合付き）へ統一する。
  - [x] `int`/`int64` 混在でテンプレート推論エラーが出ないよう型キャスト規則を追加する。
  - [x] `sample/py/14` での `min(255, ...)` / `max(0, ...)` を回帰テストする。
- [x] タプル分解代入の宣言不足を修正する（未宣言変数に代入だけが出る問題）。
  - [x] `a, b, c = f(...)` で `a,b,c` が未宣言なら型付き宣言を生成する。
  - [x] `sample/py/16` の `normalize(...)` 展開で `fwd_x` 等の未宣言エラーが消えることを確認する。
- [x] 上記対応後、`sample/py` 全16件で `east/py2cpp.py` 変換→コンパイル→実行を再実施し、実行時間一覧を更新する。

## self_hosted AST/Parser 段階移行 TODO


### ケース順移行（test/fixtures/case01 から順に）

- [x] `case01_add` を `self_hosted` で通す（EAST生成 + C++実行一致）。
- [x] `case02_sub_mul` を `self_hosted` で通す。
- [x] `case03_if_else` を `self_hosted` で通す。
- [x] `case04_assign` を `self_hosted` で通す。
- [x] `case05_compare` を `self_hosted` で通す。
- [x] `case06_string` を `self_hosted` で通す。
- [x] `case07_float` を `self_hosted` で通す。
- [x] `case08_nested_call` を `self_hosted` で通す。
- [x] `case09_top_level` を `self_hosted` で通す。
- [x] `case10_not` を `self_hosted` で通す。

### 切替完了条件


## 生成画像不一致 調査ベース TODO（2026-02-17）
## 移管済み（docs/todo.md から） 2026-02-18

- [x] 比較・論理・算術の混在式で意味が変わらないことを `test/fixtures` で回帰確認する。
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
- [x] `case11_fib` を `self_hosted` で通す。
- [x] `case12_string_ops` を `self_hosted` で通す。
- [x] `case13_class` 〜 `case16_instance_member`（クラス系）を `self_hosted` で通す。
- [x] `case17_loop` 〜 `case24_ifexp_bool`（ループ/例外/内包/ifexp）を `self_hosted` で通す。
- [x] `case25_class_static` 〜 `case33_pathlib_extended`（拡張ケース）を `self_hosted` で通す。
- [x] `test/fixtures` 全ケースで `self_hosted` EAST が意味的に安定していることを確認する。
- [x] `src/py2cpp.py` で `--parser-backend self_hosted` 時に `test/fixtures` 全ケースが実行一致する。
- [x] デフォルト backend を `self_hosted` に変更する。
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
- [x] 方針を明文化する: Pythonのユーザー定義クラスは参照セマンティクスを原則とし、値型化は「意味保存が証明できる場合のみ」許可する。
- [x] `case34_gc_reassign` を回帰ゴールデンに設定し、`a = b` 後に同一オブジェクト共有（コピーで2個化しない）を必須条件にする。
- [x] 値型化の適用条件を仕様化する（例: インスタンスフィールドなし、`__del__` なし、インスタンス同一性に依存する操作なし、代入/引数渡しで共有観測されない）。
- [x] EAST 解析段階で「値型化候補クラス」と「参照必須クラス」を分類するメタ情報を追加する。
- [x] `src/py2cpp.py` にクラスごとのストレージ戦略選択（`rc<T>` / `T`）を実装し、混在ケースで正しく `.` と `->` を切り替える。
- [x] `case15_class_member` は以前どおり `Counter c = Counter();` へ戻す（最適化適用例）。
- [x] `case34_gc_reassign` は `rc<Tracked>` のまま維持する（最適化非適用例）。
- [x] 新規テストを追加する: 同一性依存ケース（代入共有、関数引数経由の更新共有、コンテナ格納後の共有）では必ず参照型を選ぶことを検証する。
- [x] 新規テストを追加する: 値型化候補（実質 stateless クラス）では出力C++が値型になり、実行結果がPython一致することを検証する。
- [x] selfhost一次ゴールを固定する: `python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` が成功する。
- [x] self-hosted parser で関数定義シグネチャの `*`（keyword-only 引数マーカー）を解釈可能にする。
- [x] `*` 対応後、`selfhost/py2cpp.py` の EAST 生成が最後まで通ることを確認する。
- [x] 関数定義シグネチャでの未対応要素（`/`, `*args`, `**kwargs`）の扱いを仕様化する（受理/拒否とエラーメッセージ）。
- [x] `src/common/east.py` の対応箇所へ最小コメントを追加し、どのシグネチャ構文をサポートするか明記する。
- [x] self_hosted parser の `STR` 解析で prefix 付き文字列（`f/r/b/u/rf/fr`）を正しく扱えるようにする。
- [x] self_hosted parser の `f-string` を `JoinedStr/FormattedValue` に落とす（最低限 `{expr}` と `{{` `}}`）。

## 移管: 2026-02-18（docs/todo.md から完了済みを移動）

### Any/object 方針への移行（完了）

- [x] `src/cpp_module/py_runtime.h` に `using object = rc<PyObj>;` を導入する。
- [x] `Any -> object` 変換のためのボックス型を実装する。
- [x] `PyIntObj` / `PyFloatObj` / `PyBoolObj` / `PyStrObj`
- [x] `PyListObj` / `PyDictObj`（`list<object>` / `dict<str, object>` ベース）
- [x] `make_object(...)` / `obj_to_int64` / `obj_to_float64` / `obj_to_bool` / `obj_to_str` を実装する。
- [x] `py_is_none(object)` を実装し、null `object` 判定を統一する。
- [x] `py_to_string(object)` を実装する。

### py2cpp 側 Any lowering（完了）

- [x] `src/py2cpp.py` の `cpp_type()` で `Any` / `object` を `object` 型へ解決する。
- [x] `dict[str, Any]` を `dict<str, object>` に変換する。
- [x] `list[Any]` を `list<object>` に変換する。
- [x] `Any` 代入時に `make_object(...)` を生成する。
- [x] `Any` 利用演算時に明示的 unbox (`obj_to_*`) を生成する。
- [x] `Any is None` / `Any is not None` を `py_is_none` ベースへ統一する。

### selfhost 回復（部分完了）

- [x] `selfhost/py2cpp.cpp` を再生成し、現時点のコンパイルエラー件数を計測する。
  - 計測値: `305` errors（`g++ -std=c++20 -O2 -I src selfhost/py2cpp.cpp ...`）

### 内包表現・lambda 追加回帰（完了）

- [x] `test/fixtures/collections` に内包表現の追加ケースを増やす。
- [x] 二重内包（nested comprehension）
- [x] `if` 句を複数持つ内包
- [x] `range(start, stop, step)` を使う内包
- [x] `test/fixtures/core` に lambda の追加ケースを増やす。
- [x] `lambda` 本体が `ifexp` を含むケース
- [x] 外側変数 capture + 複数引数
- [x] 関数引数として lambda を渡すケース
- [x] 上記を `test/unit/test_py2cpp_features.py` の C++ 実行回帰に追加する。

### ドキュメント更新（完了）

- [x] `docs/spec-east.md` に `Any -> object(rc<PyObj>)` 方針を明記する。
- [x] `docs/spec.md` に `Any` の制約（boxing/unboxing, None 表現）を追記する。
- [x] `readme.md` に `Any` 実装状況（移行中）を明記する。

## 移管: 2026-02-18（todo.md から完了済みを移動・2）

### selfhost 回復（完了分）

- [x] `selfhost/py2cpp.py` のパース失敗を最小再現ケースへ分離する（`except ValueError:` 近傍）。
- [x] `src/common/east.py` self_hosted parser に不足構文を追加する。
- [x] 2. の再発防止として unit test を追加する。
- [x] `PYTHONPATH=src python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` を成功させる。
- [x] `selfhost/py2cpp.cpp` をコンパイルし、エラー件数を再計測する。
- [x] コンパイルエラー上位カテゴリを3分類し、順に削減する。
- [x] `src/py2cpp.py` 実行結果との一致条件を定義し、比較確認する。
- [x] `selfhost/` には `src` 最新をコピーしてよい前提で、`selfhost/py2cpp.py` と `selfhost/cpp_module/*` を同期する（`cp -f src/py2cpp.py selfhost/py2cpp.py` / `cp -f src/cpp_module/* selfhost/cpp_module/`）。
- [x] `g++` ログ取得を `> selfhost/build.all.log 2>&1` に統一し、`stderr` 空でも原因追跡できるようにする。

### object 制約の実装反映（汎用）

- [x] EAST で `object` レシーバの属性アクセス・メソッド呼び出しを検出し、`unsupported_syntax` を返す。
- [x] `py2cpp.py` の emit 時にもガードを追加し、`object` レシーバの呼び出し漏れを最終防止する。
- [x] `test/fixtures/signature/` に `object` レシーバ呼び出し禁止の NG ケースを追加する。
- [x] `test/unit` に NG ケースが失敗することを確認する回帰テストを追加する。

### 追加回帰（super）

- [x] `super()` の回帰 fixture を追加する（`test/fixtures/oop/super_init.py`）。
- [x] EAST parser 側で `super().__init__()` を含むコードが parse できる unit test を追加する。
- [x] C++ 変換して実行まで通る runtime test を追加する（`test/unit/test_py2cpp_features.py`）。

### EAST へ移譲（py2cpp 簡素化・第2段）

- [x] `src/common/east_parts/core.py` で `Call(Name(...))` の `len/str/int/float/bool/min/max/Path/Exception` を全て `BuiltinCall` 化し、`py2cpp` の生分岐を削減する。
- [x] `src/common/east_parts/core.py` で `Attribute` 呼び出しの `owner_t == "unknown"` フォールバック依存を減らし、型確定時は EAST で runtime_call を確定させる。
- [x] `src/py2cpp.py` の `render_expr(kind=="Call")` から、EAST で吸収済みの `raw == ...` / `owner_t.startswith(...)` 分岐を段階削除する。
- [x] `test/unit/test_py2cpp_features.py` に `BuiltinCall` 正規化の回帰（`dict.get/items/keys/values`, `str` メソッド, `Path` メソッド）を追加する。
- [x] `test/unit` 一式を再実行し、`test/fixtures` 一括実行で退行がないことを確認する。

### BaseEmitter 共通化（言語非依存 EAST ユーティリティ）

- [x] `src/common/base_emitter.py` に言語非依存ヘルパ（`any_dict_get`, union型分解、`Any` 判定）を移し、`CppEmitter` の重複を削減する。
- [x] ノード補助（`is_name/is_call/is_attr` などの軽量判定）を `BaseEmitter` に追加し、各エミッタの分岐可読性を上げる。
- [x] 型文字列ユーティリティ（`is_list_type/is_dict_type/is_set_type`）を `BaseEmitter` へ寄せる。
- [x] `py2cpp.py` で `BaseEmitter` の新規ユーティリティ利用へ置換し、挙動差分がないことを回帰テストで確認する。
- [x] 次段として `py2rs.py` / `py2cs.py` でも流用可能な API 形に揃え、適用候補箇所を `todo.md` に追記する。

## 移管: 2026-02-18（todo.md から完了済みを移動・3）

### selfhost 回復（完了分）

- [x] self_hosted parser で `return`（値なし）を文として受理する。
- [x] `return`（値なし）の再発防止 unit test（`test/unit/test_east_core.py`）を追加する。
- [x] `BaseEmitter` に `any_to_dict/any_to_list/any_to_str` ヘルパを追加する（自己変換時の型崩れ分析の土台）。
- [x] `py_runtime.h` に `optional<dict<...>>` 向け `py_dict_get/py_dict_get_default` 補助オーバーロードを追加する。

## 移管: 2026-02-18（C++ runtime wrapper 方針の整合）

- [x] `py_runtime.h` の `str/list/dict/set` を STL 継承ベースから「非継承 wrapper（composition）」へ移行する。
- [x] 非継承 `str` で range-for が自然に書けるよう、`begin()/end()`（必要なら iterator wrapper）を整理する。
- [x] `py2cpp.py` の生成コードから STL 依存の前提（継承由来の暗黙利用）を除去し、wrapper API のみで成立させる。
- [x] `test/fixtures/strings/str_for_each.py` を含む文字列走査ケースで、生成 C++ が簡潔な `for (str c : s)` を維持することを回帰確認する。
- [x] `docs/spec-dev.md` / `docs/how-to-use.md` / `docs/spec-east.md` の wrapper 記述を実装実態と一致させる（移行完了時に再更新）。

## 移管: 2026-02-18（selfhost 回復 1-3）

- [x] `selfhost/py2cpp.cpp` で `object -> optional<dict<...>> / list<object> / str` 代入が失敗している箇所を、`any_to_dict/any_to_list/any_to_str` を通る形へ統一する。
- [x] `py_dict_get_default(...)` 呼び出しの曖昧解決（`bool` 既定値など）を解消するため、`dict_get_bool/str/list/node` など型付き helper 呼び出しへ置換する。
- [x] `emit_stmt` / `emit_assign` / `render_expr` の `dict|None` 固定引数を段階的に `Any` 受け + 内部 `dict` 化へ寄せ、selfhost 生成コードの `std::any` 入力と整合させる。
