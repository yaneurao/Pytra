<a href="../../en/plans/p6-cpp-fixture-parity-failures.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P6: C++ fixture parity failures 解消

最終更新: 2026-03-31

関連 TODO:
- `docs/ja/todo/cpp.md` の `ID: P6-CPP-FIXPAR-*`

## 背景

`PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2`
を実行したところ、C++ fixture parity は `131 cases / 126 pass / 5 fail` だった。

失敗 5 件は次のとおり。

| ケース | 種別 | 症状 |
|---|---|---|
| `any_none` | output mismatch | `Any | None` の出力が Python と一致しない |
| `integer_promotion` | output mismatch | 整数昇格の実行結果が Python と一致しない |
| `nested_closure_def` | compile failure | nested closure の参照先が `::inner` / `::rec` になり未解決 |
| `ok_generator_tuple_target` | compile failure | `zip_ops.h` と `list_ops.h` の `py_zip` / `py_sum` が再定義 |
| `ok_typed_varargs_representative` | compile failure | `const ControllerState&` を `ControllerState&` へ束縛して const 修飾が壊れる |

`docs/ja/progress/backend-progress-fixture.md` 上でもこの 5 件は既知の C++ 赤ケースとして残っている。今回の目的は、この残件を個別に潰して fixture parity を引き上げること。

## 対象

- `src/toolchain2/emit/cpp/` — C++ emitter / signature / closure / include 生成
- `src/toolchain2/emit/common/` — 共通 renderer / lowering 接続で必要な範囲
- `src/runtime/cpp/built_in/` — `zip_ops.h` / `list_ops.h` の重複定義整理が必要なら修正
- `tools/unittest/toolchain2/` / `tools/unittest/emit/cpp/` — 回帰テスト追加
- `docs/ja/todo/cpp.md` — 進捗更新

## 非対象

- sample parity の新規改善（fixture failure 解消に伴う非退行確認のみ）
- C++ backend 全体の既知赤ケース以外の包括改善

## 受け入れ基準

- [ ] `any_none` が C++ fixture parity で PASS する
- [ ] `integer_promotion` が C++ fixture parity で PASS する
- [ ] `nested_closure_def` が C++ fixture parity で PASS する
- [ ] `ok_generator_tuple_target` が C++ fixture parity で PASS する
- [ ] `ok_typed_varargs_representative` が C++ fixture parity で PASS する
- [ ] representative unit / parity を追加し、新規回帰がない

## サブタスク

1. [ ] [ID: P6-CPP-FIXPAR-S1] `any_none` の `output mismatch` を解消する
2. [ ] [ID: P6-CPP-FIXPAR-S2] `integer_promotion` の `output mismatch` を解消する
3. [ ] [ID: P6-CPP-FIXPAR-S3] `nested_closure_def` の closure 参照解決を修正する
4. [ ] [ID: P6-CPP-FIXPAR-S4] `ok_generator_tuple_target` の `py_zip` / `py_sum` 再定義を解消する
5. [ ] [ID: P6-CPP-FIXPAR-S5] `ok_typed_varargs_representative` の const 修飾不整合を解消する

## 決定ログ

- 2026-03-31: 起票。まず compile failure の 3 件（`nested_closure_def`, `ok_generator_tuple_target`, `ok_typed_varargs_representative`）を優先し、その後に `output mismatch` の 2 件（`any_none`, `integer_promotion`）を詰める。
- 2026-03-31: C++ emitter で local closure を visible local scope に登録し、mutable param を call graph ベースで補正した。`zip_ops.h` は `list_ops.h` への shim に整理し、`is None` は `py_is_none(...)`、stale な integer `numeric_promotion` cast は emit 時に無視する方針にした。
- 2026-03-31: 検証完了。`PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2` は `131/131 PASS`、`--case-root sample` は `18/18 PASS`。P6 の 5 件は全て解消。
