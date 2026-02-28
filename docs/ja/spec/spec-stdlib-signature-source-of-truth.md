# stdlib シグネチャ正本化仕様

この文書は、`P0-STDLIB-SOT-01` で実施する「`pytra/std` を型仕様の唯一正本にする」契約を定義する。

## 1. 目的

- compiler 側（`core.py`）に散在する標準ライブラリ仕様の直書きを撤去する。
- 型仕様の正本を `pytra/std/*.py` の型注釈へ一本化する。
- compiler は「仕様保持者」ではなく「参照者」として動作する。

## 2. 正本と参照境界

- 正本: `src/pytra/std/*.py` のトップレベル関数・クラスメソッドの戻り値注釈。
- 参照層: `src/pytra/compiler/stdlib/signature_registry.py`。
- 利用側: `src/pytra/compiler/east_parts/core.py` は参照層 API 経由で型を取得する。

禁止事項:

- `core.py` に `perf_counter -> float64` のような戻り値型を直書きすること。
- 同一シンボルについて `pytra/std` と compiler に別定義を持つこと。

## 3. 取得単位

初期の取得単位は次とする。

- 関数戻り値: `lookup_stdlib_function_return_type(function_name)`
- メソッド戻り値: `lookup_stdlib_method_return_type(owner_type, method_name)`

型表現は EAST 互換で正規化する（例: `float -> float64`, `int -> int64`, `list[int] -> list[int64]`）。

## 4. fail-closed

- 参照層で型が得られない場合、呼び出し側は暗黙既定値へフォールバックせず、`unknown` 扱いを維持する。
- 新規対応を追加する場合は、必ず `pytra/std` 側注釈を先に更新する。

## 5. 初期適用対象

- `perf_counter`（`pytra/std/time.py`）の戻り値型解決。
- `Path` クラス（`pytra/std/pathlib.py`）の主要メソッド戻り値取得。

## 6. 検証

- `test/unit/test_stdlib_signature_registry.py` で参照層の解決結果を固定する。
- `test/unit/test_east_core.py` で `perf_counter` call の `resolved_type` を固定する。
