# TODO

- [x] セルフホスティング済みトランスパイラ実行ファイル（`test/obj/pycpp_transpiler_self_new`）を使って、`test/py/case05` から `test/py/case100` までを `test/cpp2/` に変換し、各生成 C++ がコンパイル可能かを一括検証した。
  - 実施結果: `CASE_TOTAL=96`, `TRANSPILE_FAIL=0`, `COMPILE_OK=96`, `COMPILE_FAIL=0`

## トランスパイラ機能 TODO（今回の不足点整理）

- [x] `AugAssign`（`+=`, `-=`, `*=`, `/=`, `%=`, `//=`, `|=` など）を網羅対応する。
- [x] `**`（べき乗）を C++ 側で正しく変換する（`pow` 変換や整数演算最適化を含む）。
- [x] `bytearray(n)` / `bytes(...)` の初期化と相互変換を Python 互換に強化する。
- [x] `list.pop()` / `list.pop(index)` の両方に対応する（現在は引数なし中心）。
- [x] `math` モジュール互換を拡張する（`sin`, `cos`, `exp`, `pi` 以外も含め網羅）。
- [ ] `gif` 出力ランタイム（`save_gif`, パレット関数）を `py_module` / `cpp_module` 対応で正式仕様化し、テストを追加する。
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

- [x] `sample/py/04_monte_carlo_pi.py` の実行結果不一致を解消する（`pi_estimate` が Python と一致するようにする）。
- [x] `for ... in range(...)` 変換時の一時変数名衝突を防ぐ（`sample/py/12_sort_visualizer.py` のコンパイル失敗を解消する）。

## sample/py/15 追加時に見えた変換器側TODO

- [ ] `int(<str>)` の数値変換を `py2cpp.py` / `py2cs.py` で正しく変換する（手動パース回避）。
- [ ] 文字列の 1 文字添字（`s[i]`）を Python と整合する形で C++/C# に変換する（`char`/`string` 差の吸収）。
- [ ] `str` の比較（`"a" <= ch <= "z"` のような範囲比較）を C# 含め正しく変換する。
- [ ] `while True: ... return ...` 形式で C# 側の「全経路 return」誤検知が出ないよう制御フロー解析を改善する。
- [ ] 空リスト初期化（`x: list[T] = []`）を C# 側で `List<T>` として安定生成する（`List<object>` への退化を防止）。
- [ ] メソッド呼び出し経由の型付き空コンテナ生成（`self.new_list()` 等）を常時許容し、`Only direct function calls are supported` を解消する。
- [ ] `dict` 参照で C++ 側が `const` 扱いになる問題（`env[key]`）を生成側で解決し、入力コードにダミー書き込みを要求しない。
- [ ] 整数除算 `//` と剰余 `%` の負数挙動を Python と完全一致させる（C++/C# の演算差をランタイム吸収）。
- [ ] 行連結文字列（`\n` を含む長いソース文字列）からのトークナイズが C++/C# 生成で壊れないよう文字列エスケープ処理を強化する。
- [ ] 変換器都合で入力 Python を書き換えなくて済むよう、`sample/py/15` で行った回避実装をトランスパイラ側へ吸収する。
