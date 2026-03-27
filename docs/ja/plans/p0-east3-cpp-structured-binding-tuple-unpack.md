<a href="../../en/plans/p0-east3-cpp-structured-binding-tuple-unpack.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: EAST3 マーカー経由で C++ tuple unpack を構造化束縛へ縮退

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01`

背景:
- `sample/cpp/16_glass_sculpture_chaos.cpp` では、tuple 戻り値の展開が
  `auto __tuple_n = call(...);` + `std::get<i>(__tuple_n)` 連鎖で出力される。
- C++17 以降は構造化束縛（`auto [x, y, z] = ...;`）で同等表現が可能で、可読性が高い。
- ただし、再代入・`Any/object` 境界・optional/union を誤って束縛化すると意味差分リスクがある。

目的:
- EAST3 側で「構造化束縛化して安全」な tuple unpack を明示マーカー化し、C++ emitter で `std::get` 連鎖を縮退する。
- 条件不成立時は現行経路（一時変数 + `std::get`）へフォールバックし、fail-closed を維持する。

対象:
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（新規/既存 pass でマーカー付与）
- `src/hooks/cpp/emitter/stmt.py`（tuple assign 出力）
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/16_glass_sculpture_chaos.cpp`（再生成確認）

非対象:
- `for` ループ tuple target（`for (auto [a,b] : ...)`）の方針変更
- Rust/Scala/Go など他 backend の tuple unpack 表現変更
- tuple 値の型推論アルゴリズム全体改修

受け入れ基準:
- `Assign` の tuple unpack で安全条件を満たすケースに EAST3 マーカーが付与される。
- C++ emitter はマーカー付きケースで `auto [a, b, c] = expr;` を出力する。
- 次のケースは従来経路を維持する:
  - 既存変数への再代入（宣言を伴わない unpack）
  - optional/union/Any/object 境界
  - 要素数不一致や `*rest` を含む unpack
- `check_py2cpp_transpile.py` と関連 unit が通り、`sample/cpp/16` で `std::get` 連鎖縮退を確認できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 16_glass_sculpture_chaos --force`

決定ログ:
- 2026-03-02: ユーザー指示により、EAST3 で安全条件マーカーを付与し、CppEmitter で構造化束縛へ縮退する P0 を起票。
- 2026-03-02: `TupleTargetDirectExpansionPass` を拡張し、`Assign(Tuple)` で `resolved_type == tuple[...]` かつ要素型が `Any/object/unknown` でない場合のみ `cpp_struct_bind_unpack_v1`（`version/names/types`）を付与。`union`・型不一致・非Name要素・重複名は fail-closed でマーカー除去に統一。
- 2026-03-02: `CppEmitter.emit_assign` にマーカー参照経路を追加し、`宣言時 unpack` かつヒント整合時だけ `auto [a, b, ...] = expr;` を出力。再代入やヒント不整合時は既存 `auto __tuple_n` + `std::get` 経路へフォールバック。
- 2026-03-02: 検証コマンドを実施し、`sample/cpp/16` で主要 tuple unpack を構造化束縛へ縮退したことを確認。
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`（49 tests, OK）
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`（98 tests, OK）
  - `python3 tools/regenerate_samples.py --langs cpp --stems 16_glass_sculpture_chaos --force`（regen=1 fail=0）
  - `python3 tools/check_py2cpp_transpile.py`（checked=136 ok=136 fail=0 skipped=6）

## 分解

- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S1-01] 適用条件（宣言時 unpack / tuple 要素確定 / 非Any-object）を仕様化する。
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S1-02] EAST3 マーカースキーマ（例: `cpp_struct_bind_unpack_v1`）と fail-closed 条件を定義する。
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S2-01] EAST3 optimizer pass で対象 `Assign(Tuple)` へマーカーを付与する。
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S2-02] CppEmitter tuple assign 分岐をマーカー参照型に切替え、構造化束縛出力を実装する。
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S2-03] マーカー不在/不整合時の fallback を固定し、現行 `std::get` 経路を維持する。
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S3-01] unit テストを追加して構造化束縛適用/非適用境界を回帰固定する。
- [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S3-02] `sample/cpp/16` 再生成と transpile チェックで非退行を確認する。
