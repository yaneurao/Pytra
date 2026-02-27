# TASK GROUP: TG-P3-MICROGPT-SOURCE-PRESERVATION

最終更新: 2026-02-24

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-MSP-01`
- `docs/ja/todo/index.md` の `ID: P3-MSP-02`
- `docs/ja/todo/index.md` の `ID: P3-MSP-03`
- `docs/ja/todo/index.md` の `ID: P3-MSP-04`
- `docs/ja/todo/index.md` の `ID: P3-MSP-05`
- `docs/ja/todo/index.md` の `ID: P3-MSP-06`
- `docs/ja/todo/index.md` の `ID: P3-MSP-07`
- `docs/ja/todo/index.md` の `ID: P3-MSP-08`
- `docs/ja/todo/index.md` の `ID: P3-MSP-09`

背景:
- 2026-02-23 00:03〜00:13 の作業ログには、`py2cpp` 変換を通すために `microgpt-20260222.py` を段階的に書き換えた履歴が残っている。
- 現在はユーザーが `materials/refs/microgpt/microgpt-20260222.py` を復元済みで、変換用に改変した版は `work/tmp/microgpt-20260222-lite.py` として分離されている。
- `materials/refs/microgpt/microgpt-20260222.py` と `work/tmp/microgpt-20260222-lite.py` の差分は、元ソースの意味変更を含む大規模改変になっている。

抽出した改変項目（ログ + 差分）:
1. 関数シグネチャへ型注釈を追加（無注釈引数拒否を回避）。
2. クラス内 1 行メソッド定義（`def ...: return ...`）を複数行へ展開。
3. トップレベル `for` や多重代入を関数化/単文化して parser 制約を回避。
4. 内包表記・`zip`・generator・`sum(...)`・f-string 書式指定を明示ループへ展開。
5. `random.choices(range(...), weights=[...])` を helper 化して呼び出し形を変更。
6. `open('input.txt')` / `urllib` / `os.path.exists` の I/O 経路を削除し、固定データへ置換。
7. `Value` / autograd / GPT ブロックを含む元アルゴリズムを、軽量な `microgpt-lite` へ再構成。

改変項目の責務再分類（P3-MSP-01）:
1. 型注釈追加で回避した項目
   - 本来の責務: parser（`self_hosted`）/ EAST の引数型解決。
   - 吸収方針: 無注釈引数を受理するか（`unknown` 許容 or 推論）を parser 側仕様として明示し、入力側改変を不要にする。
2. 1 行メソッド定義の複数行展開で回避した項目
   - 本来の責務: parser の class-body 文法受理。
   - 吸収方針: `def f(...): return ...` 形式を class 内でも受理し、同等 EAST へ lower する。
3. トップレベル `for` / 多重代入の関数化・分解で回避した項目
   - 本来の責務: parser の top-level statement 受理範囲。
   - 吸収方針: top-level `for` と tuple unpack 代入を段階対応し、既存 Python スクリプト構造をそのまま受理する。
4. 内包・generator・f-string 書式の手展開で回避した項目
   - 本来の責務: parser expression lower + emitter の型整合。
   - 吸収方針: 内包表記内 `range(...)`、`sum(generator)`、f-string format spec の lower を整備する。
5. `random.choices(range(...), weights=...)` 形の変更で回避した項目
   - 本来の責務: emitter の call lower + runtime `random` API。
   - 吸収方針: `range` 反復体をそのまま `choices` に渡せる経路（または language profile での明示変換）を追加する。
6. I/O 経路（`open` / `urllib` / `os.path.exists`）の削除で回避した項目
   - 本来の責務: runtime 標準ライブラリ互換 + import 解決。
   - 吸収方針: `pytra.std` の API 充足と I/O 反復互換を拡張し、データ入力コードを改変せず変換可能にする。
7. autograd/GPT 全体を lite へ置換した項目
   - 本来の責務: parser / emitter / runtime を跨ぐ総合互換性。
   - 吸収方針: 原本 `microgpt` を入力した失敗点を機能別に分解し、各レイヤへ分配して段階解消する。

原本入力での失敗要因（P3-MSP-02）:
1. 再現コマンド（2026-02-23 実行）
   - `python3 src/py2cpp.py materials/refs/microgpt/microgpt-20260222.py -o work/out/msp2-microgpt.cpp`
   - 結果: `unsupported_syntax: self_hosted parser requires type annotation for parameter: data at 33:0`
2. 失敗要因列挙（再現 + 2026-02-23 00:03〜00:13 の作業ログ追跡）
   - 要因 A: 無注釈引数（`def __init__(self, data, ...)` ほか）
   - 要因 B: class 内 1 行メソッド定義（`def __pow__(...): return ...` 形式）
   - 要因 C: top-level `for` / tuple 同時代入 / 複数 `for` 内包など、top-level・式 lower の未対応構文
   - 要因 D: `range` を含む内包 lower の不整合（`unexpected raw range Call in EAST`）
   - 要因 E: `zip` / 内包経由での型崩れに起因する `object receiver` エラー
   - 要因 F: I/O/stdlib 互換不足（`open` 反復、`list.index`、`random.shuffle(list[str])` など）

実装タスクへの置換方針（P3-MSP-02 の成果物）:
1. 要因 A/B/C は parser（`self_hosted`）拡張タスクへ置換する。
2. 要因 D/E は EAST lower / emitter の型解決タスクへ置換する。
3. 要因 F は `pytra.std` / runtime API 互換タスクへ置換する。
4. 置換先タスク ID: `P3-MSP-04`〜`P3-MSP-09`（`docs/ja/todo/index.md`）。

回帰導線（P3-MSP-09）:
1. 固定入力:
   - `materials/refs/microgpt/microgpt-20260222.py`（原本）
2. 検査コマンド:
   - `python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known`
3. 期待結果:
   - `result=fail phase=transpile` か `result=fail phase=syntax-check` の場合は `stage=A..F` のいずれかで分類される。
   - `result=ok phase=transpile+syntax-check` の場合は `stage=SUCCESS` となる。
4. 再発検知運用:
   - ある失敗要因を解消した後は `--expect-stage` を次の期待値（例: `B`, `C`, ..., `success`）へ更新し、以前の要因へ戻った回帰を検知する。

parser 受理拡張（P3-MSP-04）:
1. 対応内容（2026-02-23）
   - 関数シグネチャで無注釈引数（`def f(x): ...`）を `unsupported_syntax` で拒否せず、`arg_types[name] = "unknown"` として受理する。
   - `def ...: return ...` 形式の 1 行定義を分割して、top-level / nested function / class method の各経路で本文付き `FunctionDef` として EAST 化する。
2. 実装箇所
   - `src/pytra/compiler/east_parts/core.py`:
     - `_sh_parse_def_sig`: 無注釈引数の `unknown` 受理を追加。
     - `_sh_split_def_header_and_inline_stmt`: `def` ヘッダと inline 本文の分割 helper を追加。
     - `convert_source_to_east_self_hosted` / `_sh_parse_stmt_block_mutable` / class 解析経路: inline 定義を synthetic body へ lower。
3. 検証
   - `python3 test/unit/test_self_hosted_signature.py`
     - `ok_untyped_param.py` と `ok_class_inline_method.py` を追加し、受理拡張の回帰を固定。
   - `python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known`
     - `stage=A`（無注釈引数）から `stage=C`（top-level/lower ギャップ）へ前進。
4. 境界
   - 本タスクは parser 受理範囲の拡張のみを対象にし、top-level `for` / tuple 同時代入 / 複数 `for` 内包や lower 不整合は `P3-MSP-05` 以降で扱う。

parser top-level/内包拡張（P3-MSP-05）:
1. 対応内容（2026-02-23）
   - top-level `if` / `for` を `convert_source_to_east_self_hosted` で文として受理し、式扱い（`expected token EOF`）へ落ちる経路を解消。
   - block parser（`_sh_parse_stmt_block_mutable`）に `import` / `from ... import ...` を追加し、`if` ブロック内 import を受理。
   - top-level 代入左辺の identifier 固定を廃止し、tuple 同時代入ターゲットを受理。
   - list comprehension の `for` 句を複数連結で解析できるようにし、`[x for a in A for x in a]` 形式を受理。
2. 実装箇所
   - `src/pytra/compiler/east_parts/core.py`:
     - `_sh_parse_stmt_block_mutable`: block 内 `Import` / `ImportFrom` 分岐を追加。
     - `convert_source_to_east_self_hosted`: top-level `if` / `for` 分岐を追加し、`_sh_parse_stmt_block` へ委譲。
     - top-level `asg_top` 処理: target を expression として parse する方式へ変更（tuple target 許容）。
     - `_sh_parse_expr_lowered` list-comp 分岐: chained `for` / `if` 句を順次解析し `generators` 配列へ lower。
3. 検証
   - `python3 test/unit/test_self_hosted_signature.py`
     - 追加 fixture:
       - `test/fixtures/signature/ok_top_level_if_import.py`
       - `test/fixtures/signature/ok_top_level_for.py`
       - `test/fixtures/signature/ok_top_level_tuple_assign.py`
       - `test/fixtures/signature/ok_multi_for_comp.py`
   - 最小再現:
     - `python3 src/py2cpp.py /tmp/msp5_top_if.py -o /tmp/msp5_top_if.cpp`
     - `python3 src/py2cpp.py /tmp/msp5_top_for.py -o /tmp/msp5_top_for.cpp`
     - `python3 src/py2cpp.py /tmp/msp5_top_tuple_assign.py -o /tmp/msp5_top_tuple_assign.cpp`
     - `python3 src/py2cpp.py /tmp/msp5_multi_for_comp.py -o /tmp/msp5_multi_for_comp.cpp`
   - 回帰導線:
     - `python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known`
     - 先頭失敗は `line 15`（top-level `if`）から `line 80`（lambda 既定値）へ前進。
4. 境界
   - ここで未対応だった lambda 既定値・generator tuple target・f-string format spec は後続の `P3-MSP-07` で段階対応した。

EAST/emitter `range(...)` lower 整合（P3-MSP-06）:
1. 対応内容（2026-02-23）
   - `src/py2cpp.py` に `range(...)` Name-call 専用 lower（`_render_range_name_call`）を追加し、`raw == "range"` で `RuntimeError("unexpected raw range Call in EAST ...")` を投げる経路を廃止した。
   - 位置引数 `range(stop)`, `range(start, stop)`, `range(start, stop, step)` を `py_range(start, stop, step)` へ正規化。
   - keyword 形のうち `range(stop=...)`, `range(start=?, stop=?, step=?)`, `range(start, stop=?, step=?)`, `range(start, stop, step=?)` の主要パターンを `py_range(...)` へ lower。
2. 実装箇所
   - `src/py2cpp.py`:
     - `CppEmitter._render_range_name_call` を追加。
     - `CppEmitter._render_call_name_or_attr` の `raw == "range"` 分岐を例外送出から helper 呼び出しへ切替。
   - `test/unit/test_py2cpp_features.py`:
     - `Py2CppFeatureTest.test_random_choices_range_call_lowers_to_py_range` を追加し、`random.choices(range(3), ...)` で `py_range(0, 3, 1)` が生成されることを固定。
3. 検証
   - `python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_random_choices_range_call_lowers_to_py_range`
   - `python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known`
     - `stage=C`（`unsupported lambda parameter token: = at 80:30`）を確認し、`stage=D` への後退が消えたことを確認。
   - `python3 tools/check_py2cpp_transpile.py`
     - `checked=124 ok=124 fail=0 skipped=6`
   - `python3 src/py2cpp.py /tmp/msp6_choices_range.py -o /tmp/msp6_choices_range.cpp`
     - 生成 C++ に `pytra::std::random::choices(py_range(0, 3, 1), ...)` を確認。
4. 残課題
   - `P3-MSP-06` 単体で解決できる範囲（`range(...)` lower 不整合）は完了。残差は parser/型崩れ側（当時 `stage=C`）として `P3-MSP-07` へ引き継いだ。

EAST/emitter `zip` 経由型崩れ安定化（P3-MSP-07）:
1. 対応内容（2026-02-23）
   - parser 側:
     - `lambda` 既定値引数（`lambda x, y=...: expr`）を受理し、arg `default` と推論型を保持。
     - generator 引数での括弧なし tuple target（`for a, b in ...`）を受理。
     - `zip(...)` 呼び出しの戻り型を `list[tuple[...]]` として推論。
     - `for` 文で tuple target へ要素型を個別束縛するよう調整。
     - `f-string` placeholder の format spec（`{x:4d}`, `{y:.4f}`）を受理。
     - `list/listcomp` 連結（`[A] + [comp] + [B]`）および tuple + `+` 混在式の誤解析を解消。
   - emitter 側:
     - `src/py2cpp.py::_emit_target_unpack` で未知型を `object` へ固定しないよう変更し、`zip` 経由 tuple unpack の過剰 `object receiver` 化を抑止。
2. 実装箇所
   - `src/pytra/compiler/east_parts/core.py`:
     - `_parse_lambda`（default 引数対応）
     - `_parse_comp_target`（括弧なし tuple target 対応）
     - `_parse_postfix`（`zip(...)` 戻り型推論）
     - `_sh_parse_stmt_block_mutable`（`for` tuple target 型束縛）
     - `_sh_parse_expr_lowered`（`+` と list/tuple/comp 誤判定の整理、f-string 経路整理）
     - `_sh_find_top_char`（f-string placeholder 分解補助）
   - `src/py2cpp.py`:
     - `_emit_target_unpack`（`unknown` を維持）
3. 検証
   - `python3 test/unit/test_self_hosted_signature.py`（16件成功）
     - 追加 fixture:
       - `ok_lambda_default.py`
       - `ok_generator_tuple_target.py`
       - `ok_list_concat_comp.py`
       - `ok_tuple_of_list_comp.py`
       - `ok_fstring_format_spec.py`
   - `python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_random_choices_range_call_lowers_to_py_range Py2CppFeatureTest.test_lambda_default_arg_emits_cpp_default Py2CppFeatureTest.test_zip_tuple_unpack_does_not_force_object_receiver`
   - `python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known`
     - `stage=F`（syntax-check 失敗）へ前進し、transpile 段階の `C/E` は解消。
   - `python3 tools/check_py2cpp_transpile.py`
     - `checked=129 ok=129 fail=0 skipped=6`
4. 残課題
   - 原本 `microgpt` は transpile 済みだが、生成 C++ の top-level 実行文配置など compile 互換差分が残り `stage=F`。`P3-MSP-03` で継続する。

runtime/std 互換差分整理（P3-MSP-08）:
1. 再現コマンド（2026-02-23 実行）
   - `python3 src/py2cpp.py /tmp/msp8_open_default_fn.py -o /tmp/msp8_open_default_fn.cpp && g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only /tmp/msp8_open_default_fn.cpp`
   - `python3 src/py2cpp.py /tmp/msp8_open_iter_mode_fn.py -o /tmp/msp8_open_iter_mode_fn.cpp && g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only /tmp/msp8_open_iter_mode_fn.cpp`
   - `python3 src/py2cpp.py /tmp/msp8_list_index_int_fn.py -o /tmp/msp8_list_index_int_fn.cpp && g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only /tmp/msp8_list_index_int_fn.cpp`
   - `python3 src/py2cpp.py /tmp/msp8_shuffle_str_fn.py -o /tmp/msp8_shuffle_str_fn.cpp && g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only /tmp/msp8_shuffle_str_fn.cpp`
   - `python3 src/py2cpp.py /tmp/msp8_shuffle_int_fn.py -o /tmp/msp8_shuffle_int_fn.cpp && g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only /tmp/msp8_shuffle_int_fn.cpp`
2. 差分マトリクス（原本依存 API）
   | API / 形 | 観測結果 | 吸収レイヤ決定 | 関連 TODO |
   | --- | --- | --- | --- |
   | `open("input.txt")` | `open(const str&, const str&)` に 1 引数呼び出しされ `too few arguments` | EAST/builtin lower 側で Python 既定値 `mode="r"` を補完する（必要なら runtime 側に 1 引数 overload 追加） | `P3-MSP-08`, `P3-MSP-03` |
   | `for line in open("input.txt", "r")` | `PyFile` に `begin/end` がなく range-for 不能 | runtime (`PyFile`) 側に反復 API を追加して吸収する | `P3-MSP-08`, `P3-MSP-03` |
   | `xs.index(v)` (`xs: list[int/str]`) | `list<T>` に `index` がなくコンパイル失敗 | runtime (`list<T>`) 側に `index` 実装を追加し、必要に応じて lower の method map を補完する | `P3-MSP-08`, `P3-MSP-03` |
   | `random.shuffle(xs)` (`xs: list[str]`) | `shuffle(list<int64>&)` 固定シグネチャへ束縛され型不一致 | `pytra.std.random` + C++ runtime `std/random` を要素型依存に一般化して吸収する | `P3-MSP-08`, `P3-MSP-03` |
3. 境界外（runtime/std ではなく別レイヤ）
   - `random.choices(range(...), weights=..., k=...)` は `unexpected raw range Call in EAST` で失敗し、EAST lower 問題（要因 D）であることを再確認した。runtime 互換タスクからは除外し、`P3-MSP-06` 側で扱う。
4. 実装根拠（現状コード）
   - `src/runtime/cpp/pytra/built_in/str.h`: `open(const str& path, const str& mode)` のみ。
   - `src/runtime/cpp/pytra/built_in/io.h`: `PyFile` は `read/write/close` のみで `begin/end` を未提供。
   - `src/runtime/cpp/pytra/built_in/list.h`: `append/extend/pop/...` はあるが `index` 未実装。
   - `src/runtime/cpp/pytra/std/random.h`: `shuffle(list<int64>&)` に固定。
   - `src/pytra/compiler/east_parts/core.py`: `list_map` に `index` エントリなし。

`stage=F` compile 互換の前進（P3-MSP-03 継続）:
1. 対応内容（2026-02-23）
   - `src/py2cpp.py` の module top-level 出力を「定義文」と「実行文」に分離し、実行文を `static void __pytra_module_init()` へ集約。`main` 冒頭で idempotent に呼び出すよう変更して、namespace 直下へ実行文が漏れる経路を解消した。
   - runtime 側に `open(path)` 既定 mode overload、`PyFile::begin/end`、`list<T>::index`、`random.shuffle(list<T>&)` を追加し、`P3-MSP-08` で洗い出した API 欠落の実装を開始した。
   - `src/py2cpp.py::_coerce_param_signature_default` を追加し、`object/Any` 引数既定値へ `make_object(...)` を補完して `std::make_tuple()` を直接 `const object&` へ渡す不整合を解消した。
   - `src/pytra/compiler/east_parts/core.py` に無注釈関数の戻り値推定（`return <expr>` 収集）を追加し、戻り注釈なし関数の `void` 固定化で発生する compile 不整合を縮退した。
   - `src/py2cpp.py` で `IfExp` の定数条件畳み込み、class 内 object 属性の `py_obj_cast<CurrentClass>` 経路、class 左辺算術（`+ - * /`）の dunder lower、class method 呼び出し引数の `object` 強制 boxing を追加し、`Value` 系の compile エラーを段階的に後退させた。
   - `src/runtime/cpp/pytra/built_in/py_runtime.h` に `object` 四則演算 overload（`+ - * /`）を追加し、`src/runtime/cpp/pytra/std/math.*` に `math.log/exp(object)` overload を追加した。
2. 検証
   - `python3 test/unit/test_self_hosted_signature.py`（16件成功）
   - `python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_random_choices_range_call_lowers_to_py_range Py2CppFeatureTest.test_lambda_default_arg_emits_cpp_default Py2CppFeatureTest.test_zip_tuple_unpack_does_not_force_object_receiver`（3件成功）
   - `python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）
   - `python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known`
     - `stage=F` は維持だが、先頭エラーは `std::make_tuple` 既定値不整合から `Value::__add__`、さらに `Value::__rtruediv__` 周辺へ前進。
3. 完了状態（2026-02-24）
   - `src/pytra/compiler/east_parts/core.py` の `/` 型推論を「数値同士のみ `float64`、それ以外は `unknown`」へ修正し、`softmax` 由来の `Value -> float64` 崩れを抑止した。
   - `src/py2cpp.py` で class ctor 引数のシグネチャ coercion（`__init__`）を有効化し、`object` 引数への boxing を徹底した。
   - `src/py2cpp.py` の `Attribute` lower（`obj_to_rc_or_raise`) で unknown owner を常に boxing するよう修正し、`loss.data` 経路の compile 崩れを解消した。
   - `src/runtime/cpp/pytra-core/built_in/py_runtime.h` で `py_div` の object 対応、`object` 複合代入、`rc<T>` の unary minus（`__neg__`）を追加し、`Value` 演算経路の compile 互換を確立した。
   - 検証: `python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known` が `result=ok phase=transpile+syntax-check, stage=SUCCESS` で通過した。

目的:
- 「変換器都合で元ソースを書き換える」運用を禁止し、必要な対応を parser/emitter/runtime 側タスクへ移す。
- `materials/refs/microgpt/microgpt-20260222.py`（原本）を無改変のまま扱える状態を作る。

対象:
- 変換失敗要因を parser 制約 / emitter lower 不整合 / runtime API 不足へ分類する。
- 原本改変で吸収していた差分を、実装タスクとして再配分する。
- 原本ファイルを入力にした回帰導線（transpile + syntax-check）を整備する。

非対象:
- `microgpt` 学習アルゴリズム自体の最適化。
- `work/tmp/microgpt-20260222-lite.py` の機能拡張。

受け入れ基準:
- 改変項目ごとに「どのレイヤで吸収すべきか」が明文化されている。
- 原本 `materials/refs/microgpt/microgpt-20260222.py` を直接入力したときの失敗原因が再現可能に列挙されている。
- 原本無改変のまま `py2cpp` transpile -> `g++ -fsyntax-only` を通すための実装タスクが TODO 化されている。

決定ログ:
- 2026-02-23: 2026-02-23 00:03〜00:13 の作業ログと `materials/refs/microgpt/microgpt-20260222.py` vs `work/tmp/microgpt-20260222-lite.py` 差分から、原本改変項目を抽出して本コンテキストを作成。
- 2026-02-23: `P3-MSP-01` を実施。改変 7 項目を parser / emitter / runtime の責務へ再分類し、入力側改変の代わりに実装側で吸収する方針を明文化。
- 2026-02-23: `P3-MSP-02` を実施。原本入力で先頭エラー（無注釈引数）を再現し、ログ追跡と合わせて失敗要因 A〜F を列挙。回避改変の内容を `P3-MSP-04`〜`P3-MSP-09` の実装タスクへ置換した。
- 2026-02-23: `P3-MSP-09` を実施。`tools/check_microgpt_original_py2cpp_regression.py` を追加し、原本固定入力の transpile/syntax-check を失敗ステージ A〜F で分類して再発検知できる導線を整備した。
- 2026-02-23: `P3-MSP-04` を実施。無注釈引数を `unknown` 受理へ切り替え、`def ...: stmt` の inline 定義を top-level / nested / class method で受理する parser 拡張を実装。`test_self_hosted_signature.py` の追加ケース通過と、原本 `microgpt` の失敗ステージ `A -> C` 前進を確認した。
- 2026-02-23: `P3-MSP-05` を実施。top-level `if` / `for`、tuple 同時代入、list-comp 複数 `for`、block 内 import を parser で受理するよう拡張。原本 `microgpt` の失敗先頭を `line 15` から `line 80`（lambda 既定値）へ前進させた。
- 2026-02-23: `P3-MSP-06` を実施。`src/py2cpp.py` で raw `range(...)` Name-call を `py_range(...)` へ lower する経路を追加し、`unexpected raw range Call in EAST` 例外を解消。`random.choices(range(...))` 再現ケースで transpile 通過を確認し、回帰ステージは `C` 維持（`D` 解消）を確認した。
- 2026-02-23: `P3-MSP-07` を実施。`zip`/内包/tuple unpack 経路の型崩れを parser+emitter で段階修正し、`object receiver` 起点の transpile 失敗を解消。原本 `microgpt` の回帰ステージを `C/E` から `F`（syntax-check）へ前進させた。
- 2026-02-23: `P3-MSP-08` を実施。`open`/`list.index`/`random.shuffle(list[str])` の最小再現を行い、runtime/std 互換差分の吸収レイヤを確定した。`random.choices(range(...))` は runtime ではなく `P3-MSP-06`（EAST lower）側で扱うと決定した。
- 2026-02-23: `P3-MSP-03` の継続として module init 分離・runtime API 追加・`object` 既定値補完・無注釈関数の戻り値推定を実装し、`stage=F` 先頭エラーを `std::make_tuple` 既定値不整合から `Value::__add__` 周辺へ前進させた。
- 2026-02-23: `P3-MSP-03` の継続として `IfExp` 定数畳み込み、class/object 境界の dunder lower・boxing 強化、runtime `object` 四則演算と `math.log/exp(object)` overload を追加し、`stage=F` 先頭エラーを `Value::__add__` から `Value::__rtruediv__` 周辺へ前進させた。
- 2026-02-24: `materials/` 再編後の導線ずれを解消するため、`tools/check_microgpt_original_py2cpp_regression.py` の既定入力を `materials/refs/microgpt/microgpt-20260222.py` へ更新し、`--source` 省略で `stage=F` を再現できる状態に復旧した。
- 2026-02-24: `P3-MSP-03` の継続として `x if isinstance(x, T) else T(x)` 形の `IfExp` で `else` 側を `make_object(...)` へ統一する lower を追加し、`stage=F` 先頭エラーを `Value::__add__` から `Value::log()` 周辺へ前進させた（`check_microgpt_original_py2cpp_regression.py --expect-stage any-known`）。
- 2026-02-24: P3-MSP-03 を完了。`core.py` の `/` 型推論、`py2cpp.py` の class ctor / 属性 access boxing、runtime `py_div` / `object` 複合代入 / `rc<T>` unary minus を段階適用し、`materials/refs/microgpt/microgpt-20260222.py` を入力した `transpile -> g++ -fsyntax-only` が `stage=SUCCESS` で通過した。
- 2026-02-24: `P3-MSP-03` の継続として module 関数引数 coercion に「数値シグネチャ + Any/unknown 引数の unbox」を追加し、`pytra::std::math::log/exp` へ `object` が流れる経路を縮退。`stage=F` 先頭エラーを `Value::log()` から lambda 内部（`val.data` / `(val - max_val).exp()`）へ前進させた。
- 2026-02-24: `P3-MSP-03` の継続として、モジュール内で属性名が一意な ref-class フィールドを `unknown/object` 受信でも `obj_to_rc_or_raise<Cls>(...)->field` に降ろす経路を追加。`max(val.data for val in logits)` 側の崩れを解消し、`stage=F` 先頭エラーを `(val - max_val).exp()` 側へ前進させた。
- 2026-02-24: `P3-MSP-03` の継続として、(1) モジュール内で属性名が一意な ref-class メソッドも `unknown/object` 受信時に `obj_to_rc_or_raise<Cls>(...)->method(...)` へ寄せる経路を追加、(2) `Subscript` の any-like 受信を `py_at(..., py_to_int64(...))` に統一、(3) runtime に `py_slice(object, int64, object/any)` overload を追加した。`check_py2cpp_transpile.py`（`checked=131 fail=0`）と `check_microgpt_original_py2cpp_regression.py`（`stage=F` 維持）を確認した。
- 2026-02-24: `P3-MSP-03` の継続として、(1) 関数内 Name 代入の宣言判定を module scope と分離し、global 名衝突でも local 変数宣言されるよう修正、(2) unknown/module レシーバの `append/index/strip/exists` などを legacy lower へ拡張、(3) runtime に `py_append(object, object)` / `py_index(object, object)` を追加、(4) `Subscript` 型推論（`dict[K,V]`/`list[T]`）を追加して dict 値代入の boxing を安定化した。`microgpt` の先頭エラーは `gpt` 内の `v` 未宣言・`append` 崩れから、`urllib` / `sorted(set(str))` / 後段最適化崩れへ前進した（`stage=F` 維持）。
- 2026-02-24: `P3-MSP-03` の継続として、(1) runtime に `sorted(list|set)`、`set<str>(str)`、`list<T> + list<T>`、`urllib.request.urlretrieve` の compile-compat shim を追加、(2) `py_index(list<T>, object)` overload を追加、(3) list 代入時の `list<object>` lambda 置換を「先頭 lambda のみ」に限定して nested lambda の誤型変換（`list<float64>` 内へ `object` append）を解消した。`microgpt` の先頭エラーは初期化フェーズの unresolved symbol 群から、学習本体の型崩れ（`probs[idx].log()` など）へ前進した（`stage=F` 維持）。
