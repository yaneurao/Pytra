# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-18（P0-TAGGED-UNION-TID-UNIFY-01 追加）

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。

## 未完了タスク

### P0: 緊急修正

#### P0-1: 整数 widening cast の冗長 emit 除去

文脈: [docs/ja/plans/p0-cpp-redundant-widening-cast.md](../plans/p0-cpp-redundant-widening-cast.md)

1. [x] [ID: P0-CPP-REDUNDANT-WIDENING-CAST-01] `int64(static_cast<int64>(b))` のような三重冗長キャストを除去し、narrowing cast を `uint8(x)` 形式に統一する。(1) widening cast（uint8→int64 等）は C++ 暗黙変換で足りるため cast を emit しない。(2) narrowing cast / 同型 cast は `static_cast<T>` より短い関数形式 `T(x)` に統一して可読性を改善する。

#### P0-2: tagged union の tag を PYTRA_TID に統一

文脈: [docs/ja/plans/p0-tagged-union-tid-unify.md](../plans/p0-tagged-union-tid-unify.md)

2. [x] [ID: P0-TAGGED-UNION-TID-UNIFY-01] tagged struct の tag をローカル enum から `uint32` (PYTRA_TID) に変更し、isinstance を既存の type_id レンジ方式で統一する。isinstance ガード内の型ナローイング（フィールドアクセス自動挿入）を実装し、json.py を `type JsonVal = ...` で書き直して動作確認する。

### P1: 言語機能追加

#### P1-1: `type X = T` 型エイリアスサポート

文脈: [docs/ja/plans/p1-type-alias-support.md](../plans/p1-type-alias-support.md)

2. [x] [ID: P1-TYPE-ALIAS-SUPPORT-01] Python の `type X = T`（PEP 695）をモジュールレベルの型エイリアス宣言として認識し、C++ では `using X = <cpp_type>;` を emit する。型式レンダリング時に alias 名を逆引きして使用することで、`::std::variant<str, bool, ::std::monostate>` のような長い型を alias 名で置き換え、生成コードの可読性を改善する。

#### P1-2: `type X = A | B | ...` タグ付き union struct 全バックエンド対応

文脈: [docs/ja/plans/p1-tagged-union-all-backends.md](../plans/p1-tagged-union-all-backends.md)

3. [x] [ID: P1-TAGGED-UNION-ALL-BACKENDS-01] `type X = A | B | ...` 宣言をタグ付き struct（tagged union）として全バックエンドで emit する。`std::variant` の再帰型制約を解消し、JSON のような再帰的データ構造を `type` 宣言で自然に表現可能にする。C++ union によるメモリ最適化は後続の CLI オプションとして分離する。

### P5: py_runtime.h 縮小

#### P5-1: py_is_type デッドコード除去

文脈: [docs/ja/plans/p5-cpp-py-is-type-dead-code-remove.md](../plans/p5-cpp-py-is-type-dead-code-remove.md)

1. [x] [ID: P5-CPP-PY-IS-TYPE-DEAD-CODE-REMOVE-01] `py_is_dict` / `py_is_list` / `py_is_set` / `py_is_str` / `py_is_bool` / `py_is_int` / `py_is_float` を `py_runtime.h` から削除する。emitter は `PYTRA_TID_*` + `py_runtime_value_isinstance` 体系に移行済みでありデッドコード化している。
- 進捗メモ: 完了。7 関数削除・テスト1件修正。fixture/sample pass、selfhost mismatches=0。

#### P5-2: FloorDiv / Mod の EAST3 IR ノード化

文脈: [docs/ja/plans/p5-east3-floordiv-mod-node.md](../plans/p5-east3-floordiv-mod-node.md)

2. [x] [ID: P5-EAST3-FLOORDIV-MOD-NODE-01] `py_floordiv` / `py_mod` を EAST3 IR ノード経由の C++ インライン emit に変更し、`py_runtime.h` から除去する。各言語バックエンドが floor 除算・modulo を言語ネイティブに生成できる基盤を整える。
- 進捗メモ: 完了。py_div/floordiv/mod を py_runtime.h から除去し scalar_ops.h へ移動。py_div は算術型確定時インライン化（object 境界は fallback 維持）。mismatches=0。cpp 0.581.1。

### P6: py_runtime.h 縮小・多言語対応

#### P6-1: C++ emitter リストミューテーション IR バイパス修正

文脈: [docs/ja/plans/p6-cpp-list-mut-ir-bypass-fix.md](../plans/p6-cpp-list-mut-ir-bypass-fix.md)

1. [x] [ID: P6-CPP-LIST-MUT-IR-BYPASS-FIX-01] `cpp_emitter.py` が `py_list_*_mut()` を直接 emit しているパスを IR ノード（ListAppend 等）経由に統一し、`py_runtime.h` から 6 関数を除去する。
- 進捗メモ: 完了。6 関数を list_ops.h へ移動、emitter を直接メソッド呼び出し（`.append()` 等）に切り替え。生成 C++ から py_list_*_mut 呼び出し除去。mismatches=0。cpp 0.581.2。

#### P6-2: py_len / py_slice の EAST3 IR ノード化

文脈: [docs/ja/plans/p6-east3-len-slice-node.md](../plans/p6-east3-len-slice-node.md)

2. [x] [ID: P6-EAST3-LEN-SLICE-NODE-01] `py_len` / `py_slice` を EAST3 IR ノード化し、C++ emitter がインライン式を生成するよう変更。`py_runtime.h` から除去する。
- 進捗メモ: 完了。py_len を base_ops.h へ移動、py_slice の str 版を py_str_slice にリネーム（同 base_ops.h）、list 版は emitter が py_list_slice_copy を直接 emit するため除去。truthy_len_expr オーバーライドで .empty() 判定を生成。selfhost mismatches=0。cpp 0.581.3。

#### P6-2a: list/dict .clear() の BuiltinCall lowering

文脈: [docs/ja/plans/p6-cpp-emit-list-dict-clear.md](../plans/p6-cpp-emit-list-dict-clear.md)

3. [x] [ID: P6-CPP-EMIT-LIST-DICT-CLEAR-01] C++ emitter が `list[T].clear()` / `dict[K,V].clear()` を BuiltinCall として lowering し `v.clear()` を emit できるようにする。`type_id.py` 再生成のブロッカー解除。
- 進捗メモ: 完了。ListClear/DictClear IR ノードが既実装済み。type_id.py transpile 成功・再生成一致・mismatches=0。

#### P6-2b: 一般ユニオン型 → std::variant / 多言語 tagged union

文脈: [docs/ja/plans/p6-east3-general-union-variant.md](../plans/p6-east3-general-union-variant.md)

4. [x] [ID: P6-EAST3-GENERAL-UNION-VARIANT-01] `str | bool | None` 等の一般ユニオン型を C++ では `std::variant<...>` に変換して emit できるようにする。`argparse.py` / `assertions.py` 再生成のブロッカー解除。
- Progress: 完了。type_bridge.py/_header_cpp_type_from_east で std::variant 生成実装。argparse.cpp/assertions.cpp 再生成済み。tests=145 pass, mismatches=0。cpp 0.582.0。

#### P6-3: py_is_none のインライン emit 化

文脈: [docs/ja/plans/p6-east3-is-none-inline.md](../plans/p6-east3-is-none-inline.md)

5. [x] [ID: P6-EAST3-IS-NONE-INLINE-01] `py_is_none(v)` を型ベースのインライン式（`!v.has_value()` / `!v` / `false`）に置き換え、`py_runtime.h` から除去する。
- Progress: 完了。_render_is_none_expr() を cpp_emitter.py に追加済み（前セッション）。py_is_none を py_runtime.h から base_ops.h へ移動済み。新規生成コードに py_is_none 呼び出しなし。mismatches=0。

#### P6-4: py_to 系のインライン emit 化

文脈: [docs/ja/plans/p6-east3-py-to-inline.md](../plans/p6-east3-py-to-inline.md)

6. [x] [ID: P6-EAST3-PY-TO-INLINE-01] `py_to<T>` / `py_to_int64` / `py_to_float64` を型確定ケースで `static_cast` / `std::stoll` 等にインライン置き換えし、`py_runtime.h` から除去する。
- Progress: 完了。emitter 全体で算術型確定ケースを static_cast に切替え。py_to_int64/py_to_float64 を scalar_ops.h へ移動・py_runtime.h から除去。18サンプル failures=0。cpp v0.584.0。

#### P6-5: py_to_string のインライン emit 化

文脈: [docs/ja/plans/p6-east3-py-to-string-inline.md](../plans/p6-east3-py-to-string-inline.md)

7. [ ] [ID: P6-EAST3-PY-TO-STRING-INLINE-01] `py_to_string(v)` を型確定ケースで `std::to_string` / identity 等にインライン置き換えし、`py_runtime.h` から除去する。

#### P6-6: py_at（list/rc 版）のインライン emit 化

文脈: [docs/ja/plans/p6-east3-py-at-inline.md](../plans/p6-east3-py-at-inline.md)

8. [ ] [ID: P6-EAST3-PY-AT-INLINE-01] `py_at(list_or_rc, idx)` の emit を `py_list_at_ref` 直接 emit に統一し、list/rc 版の `py_at` を `py_runtime.h` から除去する。

#### P6-7: Any 混入ユニオン・式の object フォールバック排除

文脈: [docs/ja/plans/p6-cpp-any-union-object-fallback.md](../plans/p6-cpp-any-union-object-fallback.md)

9. [ ] [ID: P6-CPP-ANY-UNION-OBJECT-FALLBACK-01] `int | Any` 等の動的ユニオン・Any-like 二項演算でサイレントに `object` を返す箇所（type_bridge.py L591, cpp_emitter.py L471/L2082）を排除する。

#### P6-8: unknown / 空文字型の object フォールバック排除

文脈: [docs/ja/plans/p6-cpp-unknown-type-object-fallback.md](../plans/p6-cpp-unknown-type-object-fallback.md)

10. [ ] [ID: P6-CPP-UNKNOWN-TYPE-OBJECT-FALLBACK-01] 型名 `"unknown"` / 空文字列で `object` にサイレントフォールバックする箇所（type_bridge.py L668, header_builder.py L1373）をコンパイルエラー化する。

#### P6-9: if/else 分岐型マージ失敗の object フォールバック排除

文脈: [docs/ja/plans/p6-cpp-branch-merge-object-fallback.md](../plans/p6-cpp-branch-merge-object-fallback.md)

11. [ ] [ID: P6-CPP-BRANCH-MERGE-OBJECT-FALLBACK-01] if/else 両分岐の型マージ失敗時に `object` フォールバックする箇所（cpp_emitter.py L2101-2105）を `std::variant` または明示エラーに置き換える。

#### P6-10: for ループ変数型不明の object フォールバック排除

文脈: [docs/ja/plans/p6-cpp-for-loop-type-object-fallback.md](../plans/p6-cpp-for-loop-type-object-fallback.md)

12. [ ] [ID: P6-CPP-FOR-LOOP-TYPE-OBJECT-FALLBACK-01] for ループ変数型不明時に `object` フォールバックする 5 箇所（stmt.py L1135/1161/1217/1278/1865）を型推論強化またはエラー化で排除する。

#### P6-11: グローバル変数型推論失敗の object フォールバック排除

文脈: [docs/ja/plans/p6-cpp-global-var-type-object-fallback.md](../plans/p6-cpp-global-var-type-object-fallback.md)

13. [ ] [ID: P6-CPP-GLOBAL-VAR-TYPE-OBJECT-FALLBACK-01] グローバル変数型推論失敗時に `object` フォールバックする箇所（module.py L1155）をコンパイルエラー化する。

### P7: selfhost 完全自立化

#### P7-1: native/compiler/ 完全削除

文脈: [docs/ja/plans/p7-selfhost-native-compiler-elim.md](../plans/p7-selfhost-native-compiler-elim.md)

14. [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01] `src/runtime/cpp/native/compiler/` を完全削除し、selfhost バイナリがホスト Python をシェルアウトなしで動作できるようにする。
