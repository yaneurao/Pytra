<a href="../../en/plans/p1-lua-emitter.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-LUA-EMITTER: Lua emitter を toolchain2 に新規実装する

最終更新: 2026-04-02
ステータス: 進行中

## 背景

旧 toolchain1 に Lua emitter と runtime が存在するが、toolchain2 の新パイプラインに移行する必要がある。

## 設計

- `src/toolchain2/emit/lua/` に CommonRenderer + override 構成で実装
- 旧 `src/toolchain/emit/lua/` と TS emitter（`src/toolchain2/emit/ts/`）を参考にする
- `src/runtime/lua/mapping.json` に `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義
- parity check: `runtime_parity_check_fast.py --targets lua` で fixture + sample + stdlib の3段階検証

## 決定ログ

- 2026-03-31: Lua backend 担当を新設。emitter guide に従い toolchain2 emitter を実装する方針。
- 2026-04-01: `src/toolchain2/emit/lua/` と `src/runtime/lua/mapping.json` の実装存在を確認。fixture emit は 136/136 success。
- 2026-04-01: `check_emitter_hardcode_lint.py --lang lua -v --no-write` を 0 件まで解消。
- 2026-04-01: parity は未完了。代表残差は `add`, `deque_basic`, `class_instance`, `json_*`, `sys_extended`, `argparse_extended`, `pathlib_extended`。
- 2026-04-01: stdlib parity は `16/16 pass` まで回復。Path/json/sys/png/glob/deque/ArgumentParser、class 継承、list/bytearray/string method、linked `pytra_isinstance` を Lua runtime/emitter に実装。
- 2026-04-01: fixture parity は `119/137 pass` まで改善。`StaticRangeForPlan`、staticmethod dispatch、varargs 復元、list concat、zip/sum、table repr を追加。
- 2026-04-01: sample parity は `1/18 pass`。画像 artifact、loop/continue、helper 関数不足、sample 特有の lowered パターンが残る。
- 2026-04-01: `docs/ja/spec/spec-exception.md` に合わせて Lua profile を `exception_style=union_return` に変更。`ErrorReturn` / `ErrorCheck` / `ErrorCatch` を emitter に実装し、`pytra.built_in.error` を pure Python exception class として emit/load するように修正。例外 fixture 5 件は pass に回復。
- 2026-04-01: `dict.get/items` owner 補完、`continue` lowering 吸収、`import math` shim、`ArgumentParser.add_argument` keyword 反映、dataclass default constructor 生成、`sys.set_argv/set_path` と `re.sub(count=0)` の runtime 整合を追加。stdlib は `16/16 pass` に回復、fixture は `115/137 pass` まで改善。
- 2026-04-01: Lua emitter/runtime を継続修正。`type(v).__name__`、bare re-raise、truthiness、property getter、tuple-return unpack、dict/set comprehension、`range(1引数)`、union 経由 dict dispatch、`deque`/container `len()` を修正し、fixture は `131/137 pass`、stdlib は `16/16 pass` に改善。現行の残差は `class_tuple_assign`, `reversed_enumerate`, `ok_fstring_format_spec`, `ok_lambda_default`, `object_container_access`, `str_repr_containers`。
- 2026-04-01: class field の `decl_type` 回収、Lambda `args[].default` 対応、`str([])/str({})` の静的型付き emit、float repr の条件分岐を追加し、fixture は `137/137 pass`、stdlib は `16/16 pass` に回復。sample は `1/18 pass` で、syntax error 系、row/base nil 系、artifact missing が残る。
- 2026-04-02: pure-Python generated module の load を emitter guide に沿って修正。`pytra.utils.png/gif` を Lua runtime shim に逃がさず `dofile()` で接続し、module alias import も `runtime_module_id` ベースで読ませるよう変更。`continue` label は inner `do ... end` で包んで syntax error を解消。
- 2026-04-02: `__pytra_bytearray_append` を Python `bytearray.append(int(...))` に寄せて整数化し、hot path を `table.insert()` から direct append に変更。`03_julia_set` は `--cmd-timeout-sec 600` で PASS、PNG helper 単体も byte-level 一致。残る sample 差分は主に性能で、`07_game_of_life_loop` と `18_mini_language_interpreter` は 600s timeout を確認。
