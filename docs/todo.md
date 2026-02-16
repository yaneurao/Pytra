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
