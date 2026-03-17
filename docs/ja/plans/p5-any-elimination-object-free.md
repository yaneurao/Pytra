# P5: `Any` アノテーション禁止と `object`/`PyObj` フリーランタイムへの移行

最終更新: 2026-03-17（S1-01 決定ログ追記）

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

- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/runtime_parity_check.py --targets cpp --all-samples`

---

## フェーズ計画と分解

### S1: 棚卸しと設計仕様固定

- [x] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-01] `Any` / `object` の全量使用箇所を調査・分類する。
  - transpile-target Python（`src/pytra/std/`, `src/pytra/utils/`, `src/toolchain/`）での `Any` / `object` 使用箇所。
  - C++ emitter が `object` 型を生成するトリガー条件の全列挙。
  - 結果を決定ログに固定し、phase ごとの除去対象を確定する。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-02] `extern` 未知型の代替設計仕様を固定する。
  - `extern` 宣言された変数・関数の型を C++ テンプレートパラメータまたは前方宣言として透過させる方式を設計する。
  - EAST3 および C++ emitter での表現方法を仕様化する。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-03] クラス多態性（`list[Base]` 等）の `rc<Base>` 代替設計を仕様化する。
  - `PyObj` 継承なしでユーザー定義クラスを GC 管理する emitter 方針を定める。
  - `isinstance` / `type_id` の `PyObj` なし実装方針を定める。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-04] JSON / stdlib 内部 `object` の置き換え設計を仕様化する。
  - `JsonValue` を `object` ではなく closed enum または専用クラスで表現する設計案を作成する。
  - `dict[str, object]` / `list[object]` を内部で使っている他の stdlib モジュールを列挙する。

### S2: `Any` アノテーション禁止（transpiler 型チェック層）

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S2-01] EAST 型チェックパスに `Any` 検出・エラー化を追加する。
  - 変数 / 引数 / 返り値の型注釈に `Any` が現れた場合にコンパイルエラーを出す pass を実装する。
  - `typing` import（annotation-only no-op）は除外し、型として実際に使用された `Any` のみを対象とする。
  - エラーメッセージに「`Any` の代わりに使うべき型」のヒントを含める。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S2-02] `Any` を使っている stdlib / utils の内部コードを移行する。
  - `src/pytra/std/json.py` の `_dump_json_value(v: object, ...)` 等を具体的な union 型 or 専用型へ変更する。
  - その他の stdlib / utils で `Any` / `object` を使っている関数を列挙して順次置き換える。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S2-03] `Any` 禁止に関するドキュメント / エラーガイドを整備する。
  - 移行手順（`Any` を使っていたコードをどう書き直すか）を `docs/ja/` に追記する。

### S3: stdlib 内部 `object` 依存の除去

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S3-01] `json.py` の内部表現を `object` から closed 型へ移行する。
  - `_parse_value` / `_dump_json_value` など内部で `object` を往来する経路を、`JsonValue` 型（enum または クラス階層）に置き換える。
  - `loads` / `loads_obj` / `loads_arr` の公開 API parity を維持する。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S3-02] その他 stdlib / utils の `object` 内部使用を除去する。
  - S1-04 で列挙した残りモジュールを順次移行する。

### S4: クラス多態性の `PyObj` 依存除去

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S4-01] ユーザー定義クラスが `PyObj` を継承しなくてよい emitter 設計を実装する。
  - GC 管理は `rc<UserClass>` で行い、`PyObj` 基底を経由しない。
  - `class_def.py` の `bases.append("public PyObj")` 自動挿入ロジックを廃止する。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S4-02] `list[Base]` 等のコレクション格納を `list<rc<Base>>` として emit する。
  - emitter の型描画で `list[Base]` → `list<rc<Base>>` となるよう `type_bridge` を更新する。
  - `pyobj` list モデル（P1-LIST-PYOBJ-MIG-01 で導入）との関係を整理し、`list<object>` 経路を除去する。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S4-03] `isinstance` を `PyObj` なしで実装する。
  - ユーザー定義クラスの `type_id` を静的定数として生成し、C++ 側で `py_runtime_value_isinstance` を `PyObj` に依存しない形に置き換える。
  - `dynamic_cast` または `type_id` 比較のいずれかを選択し、仕様として固定する。

### S5: `extern` 型の透過的処理

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S5-01] `extern` 宣言された変数・関数の型を C++ テンプレート / 前方宣言として emit する。
  - S1-02 の設計に基づき EAST3 と C++ emitter を実装する。
  - `object` にボックス化せず、C++ コンパイラが型解決するよう生成コードを変更する。

### S6: `PyObj` / `object` の C++ ランタイムからの除去

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S6-01] `py_runtime.h` から `PyObj` 継承階層を除去する。
  - `PyIntObj / PyFloatObj / PyBoolObj / PyStrObj / PyListObj / PyDictObj / PySetObj` および各イテレータクラスを除去する。
  - 除去後も必要な GC 機構（`RcObject / rc<T>`）は維持する。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S6-02] `object` 型 / `make_object` / `rc<PyObj>` を除去する。
  - `using object = rc<PyObj>` 定義を廃止する。
  - `make_object` / `obj_to_rc` / `obj_to_rc_or_raise` / `py_to<T>(const object&)` 等を除去する。

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S6-03] `list` PyObj モデル（P1-LIST-PYOBJ-MIG-01 導入済み）を整理する。
  - `PyListObj` が除去されるため、`cpp_list_model=pyobj` の `list<object>` 経路を `list<rc<T>>` 経路に置き換える。
  - `--cpp-list-model value` rollback 経路も整理する。

### S7: 回帰・検証・ドキュメント同期

- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S7-01] 全 fixture / sample で transpile / compile / run / parity の非退行を確認する。
- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S7-02] selfhost ビルドおよび selfhost diff で非退行を確認する。
- [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01-S7-03] `docs/ja/spec/` / `README.md` / `docs/en/` ミラーを新設計に同期する。

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
