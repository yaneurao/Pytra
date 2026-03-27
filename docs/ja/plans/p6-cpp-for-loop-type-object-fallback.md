<a href="../../en/plans/p6-cpp-for-loop-type-object-fallback.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P6: for ループ変数型不明の object フォールバック排除

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-CPP-FOR-LOOP-TYPE-OBJECT-FALLBACK-01`

## 背景

`stmt.py` の for ループ emit が、ループ変数の型を決定できない場合に
複数箇所で `object` にサイレントフォールバックしている。

| ファイル | 行 | 関数 | 条件 |
|---|---|---|---|
| `src/toolchain/emit/cpp/emitter/stmt.py` | L1135 | `_emit_for_each_target_bind()` | タプル展開要素の型が空 |
| `src/toolchain/emit/cpp/emitter/stmt.py` | L1161 | `_emit_for_each_runtime_target_bind()` | ランタイム for ループのターゲット型が不明 |
| `src/toolchain/emit/cpp/emitter/stmt.py` | L1217 | `_emit_for_each_runtime_loop()` | ジェネリックイテレーション |
| `src/toolchain/emit/cpp/emitter/stmt.py` | L1278 | `_emit_target_unpack_declared()` | タプル展開の要素型推論失敗 |
| `src/toolchain/emit/cpp/emitter/stmt.py` | L1865 | `_emit_for_core()` | ループターゲットが Any-like |

## 方針

- イテラブルの型が既知であれば、要素型はそこから導出できるはず。
  型推論ロジックを強化し、イテラブル型から要素型を正しく引き出す。
- それでも型が不明な場合はコンパイルエラーとして Python ソース側に型注釈を要求する。
- タプル展開については、タプル要素型を EAST3 IR から引き継げるよう型伝播を改善する。

## 対象

- `src/toolchain/emit/cpp/emitter/stmt.py` L1135, 1161, 1217, 1278, 1865

## 受け入れ基準

- for ループ変数の型不明によるサイレント `object` フォールバックが 0 になる。
- selfhost mismatches=0。

## 決定ログ

- 2026-03-18: object 排除方針の下、カテゴリ B フォールバックとして特定。
