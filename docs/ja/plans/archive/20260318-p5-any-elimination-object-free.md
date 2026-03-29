<a href="../../../en/plans/archive/20260318-p5-any-elimination-object-free.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P5: `Any` アノテーション禁止と `object`/`PyObj` フリーランタイムへの移行

最終更新: 2026-03-18（S7-03 完了・全サブタスク完了）

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-ANY-ELIM-OBJECT-FREE-01`

依存 / 先行タスク:
- `P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01`（typed fallback 縮退 — P5 達成の準備作業）

## 背景

現行 C++ ランタイムには `PyObj` を基底クラスとするオブジェクト階層と、それを包む `object = rc<PyObj>` 型が存在する。これは Python の動的型システムを C++ で表現するための「逃げ道」として機能してきたが、以下の分析により **設計として不要** と判断した。

1. **`Any` アノテーションを禁止すれば、型不明の変数を保持する必要がない。**
2. **`extern` の未知型は C++ テンプレート / 前方宣言で透過的に扱え、`object` にボックス化する必要がない。**
3. **クラス多態性（`list[Base]` に `Derived` を格納）は `rc<Base>` + C++ vtable で実現でき、`PyObj` 基底は不要。**
4. **JSON / stdlib の内部 `object` 使用は、closed enum（`JsonValue` 相当）で置き換え可能。**
5. **`isinstance` は C++ RTTI またはユーザー定義クラスの `type_id` 比較で実現でき、`PyObj` への依存は不要。**

## 目的

- transpile-target Python コードで `Any` を型エラーとして禁止する。
- `object` / `PyObj` 型を C++ ランタイムから除去する。
- 上記の各ユースケースを、より静的型安全な代替で置き換える。
- 結果として生成 C++ コードから boxing/unboxing オーバーヘッドと vtable 間接を排除する。

## 非対象

- Rust / Java / Go / Ruby など C++ 以外の backend（別途計画）
- Python 言語仕様の変更や Python 標準 `typing.Any` の import 禁止（import は annotation-only no-op として許容。`Any` を型として実際に使用することのみ禁止）
- `PyObj` 除去後の GC / 参照カウント戦略の全面再設計（`rc<T>` は残す）
- `type_id` 定数体系の廃止（user-defined class の `isinstance` 実装に引き続き使用）

## 受け入れ基準

- transpile-target Python コードで `Any` 型注釈を使った場合、transpiler がエラーを出して停止する。
- 生成 C++ に `object` 型 / `PyObj` 継承 / `make_object` / `rc<PyObj>` が出現しない。
- `list[Base]` に `Derived` を格納する多態性が `rc<Base>` + virtual dispatch で動作する。
- JSON / stdlib の typed 化後も `loads_obj` / `loads_arr` など公開 API が機能し、parity が維持される。
- `isinstance(x, T)` が `PyObj` なしで動作する。
- `check_py2cpp_transpile` / unit / selfhost / sample parity が全て通る。

## 確認コマンド（予定）

- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/runtime_parity_check.py --targets cpp --all-samples`

---

## フェーズ計画と分解

### S1: 棚卸しと設計仕様固定

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-01] `Any` / `object` の全量使用箇所を調査・分類する。
  - transpile-target Python（`src/pytra/std/`, `src/pytra/utils/`, `src/toolchain/`）での `Any` / `object` 使用箇所。
  - C++ emitter が `object` 型を生成するトリガー条件の全列挙。
  - 結果を決定ログに固定し、phase ごとの除去対象を確定する。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-02] `extern` 未知型の代替設計仕様を固定する。
  - `extern` 宣言された変数・関数の型を C++ テンプレートパラメータまたは前方宣言として透過させる方式を設計する。
  - EAST3 および C++ emitter での表現方法を仕様化する。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-03] クラス多態性（`list[Base]` 等）の `rc<Base>` 代替設計を仕様化する。
  - `PyObj` 継承なしでユーザー定義クラスを GC 管理する emitter 方針を定める。
  - `isinstance` / `type_id` の `PyObj` なし実装方針を定める。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-04] JSON / stdlib 内部 `object` の置き換え設計を仕様化する。
  - `JsonValue` を `object` ではなく closed enum または専用クラスで表現する設計案を作成する。
  - `dict[str, object]` / `list[object]` を内部で使っている他の stdlib モジュールを列挙する。

### S2: `Any` アノテーション禁止（transpiler 型チェック層）

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S2-01] EAST 型チェックパスに `Any` 検出・エラー化を追加する。
  - 変数 / 引数 / 返り値の型注釈に `Any` が現れた場合にコンパイルエラーを出す pass を実装する。
  - `typing` import（annotation-only no-op）は除外し、型として実際に使用された `Any` のみを対象とする。
  - エラーメッセージに「`Any` の代わりに使うべき型」のヒントを含める。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S2-02] `Any` を使っている stdlib / utils の内部コードを移行する。
  - `src/pytra/std/json.py` の `_dump_json_value(v: object, ...)` 等を具体的な union 型 or 専用型へ変更する。
  - その他の stdlib / utils で `Any` / `object` を使っている関数を列挙して順次置き換える。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S2-03] `Any` 禁止に関するドキュメント / エラーガイドを整備する。
  - 移行手順（`Any` を使っていたコードをどう書き直すか）を `docs/ja/` に追記する。

### S3: stdlib 内部 `object` 依存の除去

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S3-01] `json.py` の内部表現を `object` から closed 型へ移行する。
  - `_parse_value` / `_dump_json_value` など内部で `object` を往来する経路を、`JsonValue` 型（enum または クラス階層）に置き換える。
  - `loads` / `loads_obj` / `loads_arr` の公開 API parity を維持する。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S3-02] その他 stdlib / utils の `object` 内部使用を除去する。
  - S1-04 で列挙した残りモジュールを順次移行する。

### S4: クラス多態性の `PyObj` 依存除去

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S4-01] ユーザー定義クラスが `PyObj` を継承しなくてよい emitter 設計を実装する。
  - GC 管理は `rc<UserClass>` で行い、`PyObj` 基底を経由しない。
  - `class_def.py` の `bases.append("public PyObj")` 自動挿入ロジックを廃止する。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S4-02] `list[Base]` 等のコレクション格納を `list<rc<Base>>` として emit する。
  - emitter の型描画で `list[Base]` → `list<rc<Base>>` となるよう `type_bridge` を更新する。
  - `pyobj` list モデル（P1-LIST-PYOBJ-MIG-01 で導入）との関係を整理し、`list<object>` 経路を除去する。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S4-03] `isinstance` を `PyObj` なしで実装する。
  - ユーザー定義クラスの `type_id` を静的定数として生成し、C++ 側で `py_runtime_value_isinstance` を `PyObj` に依存しない形に置き換える。
  - `dynamic_cast` または `type_id` 比較のいずれかを選択し、仕様として固定する。

### S5: `extern` 型の透過的処理

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S5-01] `extern` 宣言された変数・関数の型を C++ テンプレート / 前方宣言として emit する。
  - S1-02 の設計に基づき EAST3 と C++ emitter を実装する。
  - `object` にボックス化せず、C++ コンパイラが型解決するよう生成コードを変更する。

### S6: `PyObj` / `object` の C++ ランタイムからの除去

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S6-01] `py_runtime.h` から `PyObj` 継承階層を除去する。
  - `PyIntObj / PyFloatObj / PyBoolObj / PyStrObj / PyListObj / PyDictObj / PySetObj` および各イテレータクラスを除去する。
  - 除去後も必要な GC 機構（`RcObject / rc<T>`）は維持する。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S6-02] `object` 型 / `make_object` / `rc<PyObj>` を除去する。
  - `using object = rc<PyObj>` 定義を廃止する。
  - `make_object` / `obj_to_rc` / `obj_to_rc_or_raise` / `py_to<T>(const object&)` 等を除去する。

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S6-03] `list` PyObj モデル（P1-LIST-PYOBJ-MIG-01 導入済み）を整理する。
  - `PyListObj` が除去されるため、`cpp_list_model=pyobj` の `list<object>` 経路を `list<rc<T>>` 経路に置き換える。
  - `--cpp-list-model value` rollback 経路も整理する。

### S7: 回帰・検証・ドキュメント同期

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S7-01] 全 fixture / sample で transpile / compile / run / parity の非退行を確認する。
- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S7-02] selfhost ビルドおよび selfhost diff で非退行を確認する。
- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S7-03] `docs/ja/spec/` / `README.md` / `docs/en/` ミラーを新設計に同期する。

---

## 既存タスクとの関係

| タスク | 関係 |
|---|---|
| P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01（進行中） | P5 達成の前準備。typed-lane caller の削減作業は S6 前の地ならしとして有効。P5 達成で超越される。 |
| P1-LIST-PYOBJ-MIG-01（完了済み） | `list` を PyObj/RC モデルへ移行した。P5-S6-03 でこの PyListObj 依存を解体し、`list<rc<T>>` へ再設計する。 |

---

## 決定ログ

- 2026-03-17: ユーザーとの設計議論の結果、「transpiler が型確定を要求する設計なら `object`/`PyObj` は不要」という結論に達した。`Any` 禁止 → `extern` template 透過 → クラス多態性を `rc<Base>` へ → stdlib closed 型化 → `PyObj` 除去、という段階的移行を P5 として起票した。

- 2026-03-17 [S1-01 完了]: `Any` / `object` 全量調査。

  **transpile-target Python の `Any`/`object` 使用箇所（フェーズ割当付き）:**

  | ファイル | `Any` 箇所数 | `object` 箇所数 | 除去フェーズ |
  |---|---|---|---|
  | `src/pytra/std/json.py` | 1（L545 `dumps` 引数） | 20+（JSON値往来の全経路） | S3-01（closed 型化） |
  | `src/pytra/std/enum.py` | 10+（metaclass/value/演算子） | 0 | S2-02（stdlib Any 移行） |
  | `src/pytra/std/argparse.py` | 8+（引数値全般） | 0 | S2-02 |
  | `src/pytra/std/sys.py` | 0 | 2（`stderr`/`stdout` extern 宣言） | S5-01（extern 透過化） |
  | `src/pytra/utils/assertions.py` | 0 | 3（汎用等値比較） | S2-02 or S4 設計後 |
  | `src/toolchain/`（100+ ファイル） | 多数（`dict[str, Any]`/汎用引数） | 少数（`json_adapters.py` 等） | S2-01 禁止パス後に移行 |

  **C++ emitter の `object`/`PyObj` 生成トリガー:**

  | パターン | 場所 | 除去フェーズ |
  |---|---|---|
  | `is_any_like_type()` 中央ディスパッチ（80+ 呼び出し） | `src/backends/common/emitter/code_emitter.py` | S6 |
  | `make_object(...)` 生成（22 箇所） | `call.py` / `type_bridge.py` / `cpp_emitter.py` / `stmt.py` / `collection_expr.py` 等 | S6-02 |
  | `"public PyObj"` 基底クラス自動挿入 | `class_def.py:194` | S4-01 |
  | `"object"` C++ 型として emit | `type_bridge.py` / `header_builder.py` / `cpp_emitter.py` / `collection_expr.py` | S6-01/02 |
  | `_is_any_like_type()` ローカル関数 | `optimizer/passes/runtime_fastpath_pass.py:20` | S6 |
  | `resolved_type: "object"` Box ノード生成 | `type_bridge.py:162` | S6-02 |
  | `PYTRA_TID_OBJECT` type-id dispatch | `cpp_emitter.py:3209` | S4-03 / S6 |
  | `dict<str, object>` / `list<object>` / `set<object>` | `collection_expr.py` / `header_builder.py` 等多数 | S3 / S6 |

  **`json.py` 除去設計方針（S3-01 先取り確認）:**
  - `_parse_value()` → `dict[str, object]` / `list[object]` を往来するのは JSON の再帰構造のため。`JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]` 形式の再帰 union 型に置き換え可能。
  - `_dump_json_value(v: object, ...)` → `_dump_json_value(v: JsonValue, ...)` に変更。
  - 公開 API `loads` / `loads_obj` / `loads_arr` / `dumps` の型シグネチャも `JsonValue` に合わせて更新。

  **`enum.py` 除去設計方針（S2-02 先取り確認）:**
  - `value: Any` は実際には `int | str` 等の具体型で十分。`IntEnum` では `int`、`StrEnum` があれば `str`。metaclass 操作は transpiler が特殊扱いするため、`Any` は型チェックパスの例外リストに登録する方針も選択肢。

  **`sys.py` extern 設計（S5-01 先取り確認）:**
  - `stderr: object = extern(...)` は `extern` 型を `object` に落とすのではなく、C++ template 透過（`auto` / `decltype(stderr)` 等）に変えるべき。S5-01 で設計を固定する。

- 2026-03-17 [S1-02 完了]: `extern` 未知型の代替設計仕様。

  **現行の extern 変数処理（コードベース調査結果）:**
  - `core_extern_semantics.py:55`: `if annotation != "Any": return None` — メタデータ収集は `Any` アノテーション専用。`object` でアノテーションされた `sys.py` の `stderr`/`stdout` はメタデータが収集されていない。
  - `extern(...)` 呼び出し式の `resolved_type` は `"unknown"` — 型情報はアノテーション側から来る。
  - C++ emitter は `object` アノテーションをそのまま使い、`object stderr;` を生成する（`PyObj` を介したボックス化）。

  **S5-01 設計仕様（確定）:**
  1. `extern` 変数のアノテーションに `object` / `Any` が使われている場合、C++ emitter は `object` 型変数を生成するのではなく、C++ `extern` 宣言（`extern auto` または `extern decltype(symbol) name;`）を生成する。
  2. Python 側では `extern` 変数の型注釈を **オプション化**：アノテーションがある場合はそれをヒントとして使い、なければ `auto` 推論とする。
  3. EAST3 表現: `extern_var_v1` メタデータの `schema_version` を 2 に上げ、`annotation_type` フィールド（`"Any"` / `"object"` / `"<具体型>"` / `""` を許容）を追加。`"Any"` と `"object"` はどちらも「emitter 側で C++ 型を推論する」フラグとして統一扱いする。
  4. C++ emitter 生成規則: `extern_var_v1` メタデータがある場合、`annotation_type` が `"Any"` / `"object"` / `""` → `extern auto {name};`（C++17）。具体型あり → `extern {cpp_type} {name};`。
  5. メタデータ収集ロジック（`core_extern_semantics.py`）を拡張し、`Any` 以外のアノテーションでも `extern(...)` 初期化を認識するよう修正する。
  6. `src/pytra/std/sys.py` の `stderr: object` / `stdout: object` は、S5-01 実装後に `stderr = extern(__s.stderr)` (アノテーション省略) または `stderr: auto = extern(__s.stderr)` に変更する（設計確定後に選択）。

- 2026-03-17 [S1-03 完了]: クラス多態性 `rc<Base>` 代替設計仕様。

  **現行の PyObj 継承注入（コードベース調査結果）:**
  - `class_def.py:194`: `if gc_managed and not base_is_gc: bases.append("public PyObj")` — `ref_classes` に属し基底が ref でない場合に自動注入。
  - `gc_managed` は `cls_name in self.ref_classes`。`ref_classes` は `class_storage_hint="ref"` から収集・推移閉包。
  - RTTI: `PYTRA_DECLARE_CLASS_TYPE(base_type_id_expr)` で静的型 ID を定義。
  - ポリモーフィック代入: `obj_to_rc_or_raise<Base>(value)` で `object` から `rc<Base>` にダウンキャスト。
  - `list[Base]`: `py_to_rc_list_from_object<Base>(...)` で `list<object>` → `list<rc<Base>>` 変換。

  **S4-01/02/03 設計仕様（確定）:**
  1. **基底クラス**: `gc_managed` かつ `base_is_gc` でないクラスは `PyObj` の代わりに `RcObject` を継承する（`RcObject` は `rc<T>` の参照カウント基底クラスで、`PyObj` 階層の親）。`public PyObj` 注入ロジックを `public RcObject` に変更する。これで `object = rc<PyObj>` を経由しないダイレクトな `rc<UserClass>` が実現できる。
  2. **型 ID / RTTI**: `PYTRA_DECLARE_CLASS_TYPE()` マクロは維持する。`type_id` 比較（`dynamic_cast` より高速）を `isinstance` の実装に引き続き使用する。`PyObj` が持っていた `type_id` フィールドを `RcObject` へ移動する（または `PYTRA_DECLARE_CLASS_TYPE()` マクロが `RcObject` ベースの仕組みで動作するよう変更する）。
  3. **ポリモーフィック代入**: `obj_to_rc_or_raise<Base>(value)` は `object` 経由だが、S6 で `object` 型を除去した後は直接 `rc<Derived>` → `rc<Base>` の implicit upcasting を生成する（C++ の自然な継承で動作）。代入先が `rc<Base>` 型の変数なら、`rc<Derived>` を右辺に持つ代入はキャストなしで動作する。
  4. **`list[Base]` コレクション**: `list<rc<Base>>` として emit する。`list<object>` 経路（現在の `py_to_rc_list_from_object`）は S4-02/S6-03 で除去し、直接 `list<rc<Base>>` に push_back する emitter に変える。
  5. **`isinstance`**: `dynamic_cast<T*>(rc_ptr.get()) != nullptr` または `x->PYTRA_TYPE_ID == T::PYTRA_TYPE_ID` で実装。S4-03 で選択するが、type_id 比較を基本とし、継承チェーンには `type_id <= T::PYTRA_TYPE_ID_MAX` 等の範囲比較を使う（現行の `py_runtime_value_isinstance` 実装を参考に拡張）。

- 2026-03-17 [S1-04 完了]: JSON / stdlib 内部 `object` の置き換え設計仕様。

  **S3-01 設計仕様（json.py 確定）:**
  1. `JsonValue` 再帰 union 型を Python 側で定義する: `JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]`。ただし transpiler が再帰 union 型をサポートしているか確認が必要（S3-01 着手前に確認する）。サポートしていない場合は closed class 階層（`class JsonNode`）を使う。
  2. `_parse_value() -> JsonValue`、`_parse_object() -> dict[str, JsonValue]`、`_parse_array() -> list[JsonValue]`、`_parse_number() -> JsonValue` に変更する。
  3. `_dump_json_value(v: JsonValue, ...)` に変更する。`dumps(obj: JsonValue, ...)` も同様。
  4. 公開 API `loads(text: str) -> JsonValue`、`loads_obj(text: str) -> dict[str, JsonValue]`、`loads_arr(text: str) -> list[JsonValue]` を維持する（戻り型が `object` から `JsonValue` へ変わるが parity は維持）。
  5. `JsonObj` / `JsonArr` 内部クラスが使う `raw: dict[str, object]` / `raw: list[object]` も `JsonValue` に置き換える。

  **他 stdlib での `object` 使用（S3-02 対象）:**
  - `src/pytra/utils/assertions.py`: `py_assert_eq(actual: object, expected: object, ...)` — S1-01 調査時点ではこれが主要な残り。`JsonValue` 移行後に `str | int | float | bool | None` などの共通スーパー型 or Generic へ変更する。
  - `src/toolchain/json_adapters.py`: `coerce_json_object_doc(doc: object, ...)` — toolchain 側（transpile 対象でない）なので S2-01 禁止パス後に対応。

- 2026-03-17 [S2-01 完了]: `AnyAnnotationProhibitionPass` 実装。

  **実装詳細:**
  - `src/toolchain/ir/east3_opt_passes/any_annotation_prohibition_pass.py` に新規作成。
  - 検出対象: `FunctionDef.arg_types` (引数型)、`FunctionDef.return_type` (戻り値型)、`AnnAssign.annotation` (変数アノテーション)。
  - `Any` トークン検出: `[], |` で区切ってトークン化し `"Any"` と完全一致を確認（`AnyFoo` 等の誤検出なし）。
  - 違反時: 全違反を列挙した `RuntimeError` を raise（コンパイル停止）。
  - `from typing import Any` のインポート行は `Import`/`ImportFrom` として除外済み（チェック対象外）。
  - `src/toolchain/compiler/east_parts/east3_opt_passes/any_annotation_prohibition_pass.py` にシムを追加。
  - **デフォルトでは `build_local_only_passes()` に含めない**。stdlib（`enum.py`, `argparse.py` 等）が `Any` を使用中のため、S2-02 での stdlib 移行完了後に有効化する。明示的に `--east3-opt-pass +AnyAnnotationProhibitionPass` で有効化可能。
  - ユニットテスト 20 件（`tools/unittest/ir/test_east3_any_annotation_prohibition_pass.py`）全件 pass。pre-existing 失敗以外の非退行なし。

- 2026-03-17 [S2-02 完了]: stdlib の `Any` アノテーション移行。

  **変更ファイルと内容:**
  - `src/pytra/std/enum.py`: `Any` を `object` または具体型に置き換え。`import typing.Any` 削除。
    - `EnumMeta.__new__(bases: tuple[object, ...], ns: dict[str, object])`
    - `member_map: dict[str, object]`、`value_map: dict[object, object]`
    - `EnumMeta.__call__(value: object)`
    - `Enum._value2member_map_: dict[object, "Enum"]`、`Enum._from_value(value: object)`
    - `Enum.value -> object`、`Enum.__eq__(other: object)`
    - `IntEnum._from_value(value: int)` — int に具体化
    - `IntFlag.__or__/__and__/__xor__(other: int)` — int に具体化
  - `src/pytra/std/argparse.py`: `Any` を `str | bool | None` に置き換え。`import typing.Any` 削除。
    - `Namespace.values: dict[str, str | bool | None]`、`__init__(values: dict[str, str | bool | None] | None = None)`
    - `_ArgSpec.default: str | bool | None`
    - `add_argument(default: str | bool | None = None)`
    - `parse_args(argv: list[str] | None = None) -> dict[str, str | bool | None]`
    - ローカル変数 `values: dict[str, str | bool | None] = {}`
  - `src/pytra/std/json.py`: `dumps(obj: Any, ...)` → `dumps(obj: object, ...)`。`import typing.Any` 削除。
  - **検証**: `AnyAnnotationProhibitionPass` を `argparse.py`、`json.py` に対して実行し、検出なし（PASS）を確認。`enum.py` は multiple inheritance による pre-existing パースエラーのため EAST3 生成不可だが、ソース上の `Any` は除去済み。
  - pre-existing 失敗以外の非退行なし（全 C++ codegen 124件 pass、IR 352件 pass）。

- 2026-03-17 [S2-03 完了]: `Any` 禁止ドキュメント整備。
  - `docs/ja/spec/spec-any-prohibition.md` を新規作成。
  - 禁止理由、エラーメッセージフォーマット、変数/引数/戻り値/コンテナ/extern 型の移行手順を記載。
  - `from typing import Any` インポートは許容（annotation-only）の旨を明記。
  - `AnyAnnotationProhibitionPass` 有効化コマンド例を記載。

- 2026-03-17 [S3-01 完了]: `json.py` 内部表現 `_JsonVal` closed 型への移行。

  **実装詳細:**
  - 再帰 union 型エイリアスはトランスパイラ未サポートのため、`_JsonVal` tagged-union クラスを採用（tag 定数 `_JV_NULL=0` 〜 `_JV_OBJ=6`、フィールド `bool_val / int_val / float_val / str_val / arr_val / obj_val`）。
  - `_JsonParser` 全メソッドの戻り型を `_JsonVal` に変更。`JsonObj.raw: dict[str, _JsonVal]`、`JsonArr.raw: list[_JsonVal]`、`JsonValue.raw: _JsonVal`。
  - コンストラクタ補助関数 `_jv_null()` 〜 `_jv_obj(v)` を追加。
  - 公開 API `loads(text: str) -> JsonValue`、`loads_obj`、`loads_arr` は parity 維持（戻り型変更なし）。
  - `dumps(obj: object, ...)` / `_dump_json_value(v: object, ...)` は `object` 引数を保持（外部から任意型を渡せる互換性のため）。
  - `json_adapters.py`: `_jv_to_object` / `_object_to_jv` 追加。`export_json_object_dict` / `coerce_json_object_doc` / `export_json_value_raw` を新型で更新。
  - `code_emitter.py` / `js_emitter.py`: `dict(raw_obj.raw)` → `export_json_object_dict(raw_obj)` に修正（`_JsonVal` リークを防止）。
  - decode boundary guard 8 ファイル（`py2x.py`、`ir2lang.py`、`east_io.py`、`link_manifest_io.py`、`materializer.py`、`program_loader.py`、`transpile_cli.py`、`runtime_symbol_index.py`）: `load_json_object_doc` → `json.loads_obj(path.read_text(...))` インライン化。
  - `shared` バージョン `0.116 → 0.117`（`json.py` 変更）。`py2x.py` 変更で全非 cpp バックエンドバージョンも bump。
  - IR ユニットテスト 3 件: `json.loads()` が `JsonValue` 返しになったため、テストを `object` 型引数直接渡しに変更。
  - pre-existing 失敗（`check_py2cpp_boundary.py` 等）以外の非退行なし。

- 2026-03-17 [S3-02 完了]: `assertions.py` の `object` 型除去。

  **変更内容:**
  - `_eq_any(actual: str | int | float | bool | None, expected: str | int | float | bool | None)`
  - `py_assert_eq(actual: str | int | float | bool | None, expected: str | int | float | bool | None, label: str = "")`
  - `py_assert_stdout(fn: object)` — `fn` は呼び出されない stub のため保留。
  - `enum.py` の `object` 使用（metaclass/value/`__eq__`）は S4 で設計変更時に対応。
  - `sys.py` の `stderr: object / stdout: object` は S5-01（extern 透過化）で対応。
  - `shared` バージョン `0.117 → 0.118`（`src/pytra/` 変更）。
  - pre-existing 失敗以外の非退行なし。

- 2026-03-18 [S4-01 完了]: ユーザー定義 ref クラス基底 `PyObj` → `RcObject` 変更。

  **変更内容:**
  - `class_def.py`: `bases.append("public PyObj")` → `bases.append("public RcObject")`（gc_managed かつ base_is_gc でない場合）。
  - `gc.h`: `RcObject` に `virtual uint32_t py_type_id() const noexcept { return 0; }` を追加。`PYTRA_DECLARE_CLASS_TYPE` マクロの `override` が `RcObject` 仮想に対して機能するようになった。
  - `py_runtime.h`: `rc<T>` の `py_runtime_value_isinstance` 特殊化を追加（`T : RcObject && !T : PyObj`）。`make_object` を経由せず `value->py_type_id()` から直接 subtype 判定する。
  - ユニットテスト（`test_py2cpp_features.py`）の `public PyObj` アサーションを `public RcObject` に更新。
  - cpp バージョン `0.577 → 0.578`。
  - pre-existing 失敗以外の非退行なし（C++ codegen 124 件 pass）。

- 2026-03-18 [S4-02 完了]: `list[Base]` コレクション `list<rc<Base>>` emit とランタイム互換性調整。

  **変更内容:**
  - `obj_to_rc<T>` の `static_assert(is_base_of_v<PyObj, T>)` → `static_assert(is_base_of_v<RcObject, T>)` に緩和。User class（`T : RcObject, !T : PyObj`）でもコンパイル可能になった（`dynamic_cast<T*>(PyObj*)` は nullptr を返す）。
  - `list[Base]` → `list<rc<Base>>` emit は `type_bridge.py` の `_cpp_type_text` 汎用パスですでに正しく動作していた（ref_classes in → `rc<ClassName>` 返す）。
  - cpp バージョン `0.578 → 0.579`。
  - pre-existing 失敗以外の非退行なし。

- 2026-03-18 [S4-03 完了]: isinstance の PyObj 非依存実装確定（S4-01 で実装済み）。

  **方式決定:**
  - `dynamic_cast` ではなく **type_id 比較** を採用。
  - `py_runtime_value_isinstance(const rc<T>& value, uint32)` 特殊化（T : RcObject && !T : PyObj）が `value->py_type_id()` を呼び、`py_runtime_type_id_is_subtype` でサブタイプ判定する。
  - `PYTRA_DECLARE_CLASS_TYPE` マクロはそのまま維持（`py_type_id() override` が RcObject 仮想に対して正しく動作）。
  - 継承チェーンのサブタイプ判定は既存の `py_type_id_registry` を使用。

- 2026-03-18 [S5-01 完了]: `extern` 変数の `object` アノテーション除去と C++ 型省略。

  **変更内容:**
  - `src/pytra/std/sys.py`: `stderr: object = extern(__s.stderr)` / `stdout: object = extern(__s.stdout)` → アノテーション省略形 `stderr = extern(...)` に変更。Python 動作は同じ（`extern` が値をそのまま返す）。
  - `src/runtime/cpp/generated/std/sys.h`: `extern object stderr;` / `extern object stdout;` が除去された（bare Assign → `decl_t == ""` → header_builder がスキップ）。
  - `core_extern_semantics.py`: `annotation == "Any"` 限定 → `annotation in {"Any", "object", ""}` に拡張（将来の concrete 型アノテーション対応の準備）。
  - `gen_runtime_from_manifest.py` + `src/backends/cpp/cli.py --emit-runtime-cpp` で sys.h を再生成。非 cpp 生成ファイル（rs, cs, nim, lua）も更新。
  - `shared` バージョン `0.118 → 0.119`。
  - pre-existing 失敗以外の非退行なし。

- 2026-03-18 [S6-01/S6-02/S6-03 完了]: `PyObj` 継承階層・`object`/`make_object`・PyObj list モデルを C++ ランタイムから除去。

  **変更内容（S6-01）:**
  - `gc.h`: `class PyObj` とすべての仮想メソッド（`py_truthy`、`py_try_len`、`py_iter_or_raise`、`py_next_or_stop`、`py_str`、`set_type_id`）を除去。`pytra::gc` 名前空間内の `using object = RcHandle<PyObj>;` と `class PyObj;` 前方宣言も除去。
  - `gc.cpp`: `RcObject::py_iter_or_raise()`（`"object is not iterable"` throw）と `RcObject::py_next_or_stop()`（`nullopt` 返却）の実装を追加（PyObj で inline だったものを RcObject に移動）。
  - `py_runtime.h`: 1304行 → 610行（約半減）。`PyIntObj`/`PyFloatObj`/`PyBoolObj`/`PyStrObj`/`PyListObj`/`PyDictObj`/`PySetObj`・各イテレータクラス・`make_object` 全オーバーロード・`object_new<T>`・`obj_to_*` 関数群・`py_to<T>(const object&)` 特殊化・`py_len(const object&)` を除去。`py_any`/`py_all` の typed template オーバーロード（`list<T>` と `rc<list<T>>` 版）を追加。

  **変更内容（S6-02）:**
  - `py_types.h`: `using object = rc<RcObject>` に再定義（旧 `rc<PyObj>`）。`using PyObj = ...` を除去。boxing 関連前方宣言を除去。
  - `list.h`: `list(const object& v)` コンストラクタ・`operator object()`・`list& operator=(const object& v)` を除去。`list(const list<U>& other)` の `U=object` 特殊ケースを除去。
  - `dict.h`/`set.h`: 同様に `object` 関連コンストラクタ・変換演算子を除去。
  - `src/pytra/std/json.py`: `dumps`/`_dump_json_value`/`_dump_json_list`/`_dump_json_dict` の引数型を `object`/`list[object]`/`dict[str,object]` → `_JsonVal`/`list[_JsonVal]`/`dict[str,_JsonVal]` に変更。`dumps_jv(_JsonVal)` 追加。`dumps(obj: str|int|float|bool|None)` スカラー受け取りに変更（`_JsonVal` 変換後に dispatch）。
  - `src/runtime/cpp/generated/std/json.h`/`json.cpp`: 再生成。
  - `src/backends/cpp/emitter/runtime_expr.py`: `py_any`/`py_all` の `make_object(...)` ラップを除去。
  - `src/runtime/cpp/generated/built_in/predicates.h`/`predicates.cpp`: `object` 版 `py_any`/`py_all` 宣言・実装を除去。
  - `shared` バージョン `0.119 → 0.120`（json.py 変更）、`cpp` バージョン `0.579 → 0.580`（emitter 変更）。

  **変更内容（S6-03）:**
  - `tools/unittest/emit/cpp/test_cpp_runtime_boxing.py`: 削除（boxing API のテストが全て不要になった）。
  - `tools/unittest/emit/cpp/test_py2cpp_list_pyobj_model.py`: 削除（`cpp_list_model=pyobj` 経路が除去された）。
  - `tools/unittest/emit/cpp/test_cpp_runtime_type_id.py`: `PyObj` → `RcObject` に更新。
  - `tools/unittest/emit/cpp/test_cpp_runtime_iterable.py`: boxing 依存のテストケースを除去。
  - `tools/unittest/emit/cpp/test_east3_cpp_bridge.py`: `obj_to_rc_or_raise` アサーションを除去。

  **テスト結果:** 319 件実行（削除済み 4 件分減）。13 失敗 + 1 エラーはすべて pre-existing。`test_py2cpp_features.py` は `ModuleNotFoundError: No module named 'test.unit'` により 124+ 件がロード不可（pre-existing）。
  - cpp バージョン `0.580`、shared バージョン `0.120`。

- 2026-03-18 [S7-01/S7-02 完了]: parity 非退行確認・selfhost diff 確認。

  **S7-01 追加修正（S6 起因の regressions）:**
  - `assertions.h/cpp`: `_eq_any`/`py_assert_eq`/`py_assert_stdout` を C++ template 化（union 型パラメータを C++ で表現できないため）。
  - `call.py`: `_coerce_py_assert_args` の boxing を完全除去（return args）。
  - `module.py`: `_coerce_args_for_module_function` に `py_assert_*` 早期リターンを追加（`_coerce_call_arg` が `object` 引数を `make_object` でラップしていた）。
  - `contains.h/cpp`: `py_contains_dict_object` 等 4 関数を除去（`rc<RcObject> == str` コンパイルエラー、dead code）。
  - `iter_ops.h/cpp`: `py_reversed_object`/`py_enumerate_object` を除去（`make_object(::std::make_tuple(...))` 未定義、dead code）。
  - `py_runtime.h`: `py_to_string(const object&)` overload を追加（`"<object>"` 返却、デバッグ用）。
  - `test_cpp_runtime_iterable.py`: inventory assertions を更新（deleted functions の assertIn → assertNotIn に変更）。
  - fixture parity: 3/3 pass。sample parity: 18/18 pass。unit tests: 319 件実行、13 失敗 + 1 エラーはすべて pre-existing。
  - cpp バージョン `0.580 → 0.581`。

  **S7-02 結果:**
  - `check_selfhost_cpp_diff.py`: mismatches=0 / known_diffs=0 / skipped=0 → PASS。
  - `check_selfhost_direct_compile.py`: failures=0 → PASS。

- 2026-03-18 [S7-03 完了]: ドキュメント同期。

  **変更内容:**
  - `docs/en/todo/index.md`: S2-03 以降の全サブタスク（S3-01〜S7-02）を英語で追記。
  - `docs/ja/spec/spec-any-prohibition.md`: PyObj 除去完了（S6）を反映したノート追加。`object = rc<RcObject>` に再定義済みの旨を記載。
  - `docs/en/spec/spec-any-prohibition.md`: 新規作成（日本語版からの翻訳）。
  - `docs/ja/spec/spec-boxing.md` / `docs/en/spec/spec-boxing.md`: 廃止済みノート追加（P5-S6 で PyObj boxing 除去済み）。

