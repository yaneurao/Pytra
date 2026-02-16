# TODO

- [x] セルフホスティング済みトランスパイラ実行ファイル（`test/obj/pycpp_transpiler_self_new`）を使って、`test/py/case05` から `test/py/case100` までを `test/cpp2/` に変換し、各生成 C++ がコンパイル可能かを一括検証した。
  - 実施結果: `CASE_TOTAL=96`, `TRANSPILE_FAIL=0`, `COMPILE_OK=96`, `COMPILE_FAIL=0`

## トランスパイラ機能 TODO（今回の不足点整理）

- [ ] `AugAssign`（`+=`, `-=`, `*=`, `/=`, `%=`, `//=`, `|=` など）を網羅対応する。
- [ ] `**`（べき乗）を C++ 側で正しく変換する（`pow` 変換や整数演算最適化を含む）。
- [ ] `bytearray(n)` / `bytes(...)` の初期化と相互変換を Python 互換に強化する。
- [ ] `list.pop()` / `list.pop(index)` の両方に対応する（現在は引数なし中心）。
- [ ] `math` モジュール互換を拡張する（`sin`, `cos`, `exp`, `pi` 以外も含め網羅）。
- [ ] `gif` 出力ランタイム（`save_gif`, パレット関数）を `py_module` / `cpp_module` 対応で正式仕様化し、テストを追加する。
- [ ] 連鎖比較（例: `0 <= x < n`）を AST から正しく展開して変換する。
