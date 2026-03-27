<a href="../../ja/plans/p6-cpp-list-mut-ir-bypass-fix.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p6-cpp-list-mut-ir-bypass-fix.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p6-cpp-list-mut-ir-bypass-fix.md`

# P6: C++ emitter のリストミューテーション IR バイパスを修正

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-CPP-LIST-MUT-IR-BYPASS-FIX-01`

## 背景

EAST3 IR には `ListAppend` / `ListPop` / `ListExtend` / `ListClear` / `ListReverse` / `ListSort` のノードが存在するが、C++ バックエンドの `cpp_emitter.py` がこれらを経由せず `py_list_append_mut()` 等の関数呼び出しを直接 emit しているパスが存在する。

問題：
- IR ノードを迂回した直接 emit は、他バックエンドが同じ IR ノードを実装しても C++ 側が活用しないため、多バックエンド間での一貫性が崩れる。
- `py_list_*_mut()` 関数が `py_runtime.h` に存在し続ける理由の一つがこのバイパスであるため、ヘッダ縮小の妨げになっている。

## 目的

- `cpp_emitter.py` の直接 emit パスを特定し、すべて IR ノード経由に統一する。
- `py_list_append_mut` / `py_list_extend_mut` / `py_list_pop_mut` / `py_list_clear_mut` / `py_list_reverse_mut` / `py_list_sort_mut` を `py_runtime.h` から削除する（または宣言を生成コードに移動する）。
- 副次効果として、他バックエンドが既存 IR ノードを活用すれば py_runtime.h 相当のヘルパを持たなくて済む状態に近づける。

## 対象

- `src/toolchain/emit/cpp/emitter/cpp_emitter.py`（直接 emit の `py_list_*_mut` 箇所）
- `src/runtime/cpp/native/core/py_runtime.h`（関数除去）
- `test/unit/toolchain/emit/cpp/`（回帰テスト）

## 非対象

- `py_list_at_ref` / `py_list_normalize_index_or_raise`（インデックス境界チェック系、別途検討）
- 非 C++ バックエンドへの IR ノード実装（本タスクは C++ 側の整理のみ）
- `py_list_set_at_mut`（IR ノードが未存在、別途 P6-EAST3-LEN-SLICE-NODE-01 等で検討）

## 受け入れ基準

- 生成 C++ に `py_list_append_mut` / `py_list_extend_mut` / `py_list_pop_mut` / `py_list_clear_mut` / `py_list_reverse_mut` / `py_list_sort_mut` の呼び出しが残らない。
- 上記 6 関数が `py_runtime.h` から削除されている。
- fixture 3/3・sample 18/18 pass、selfhost diff mismatches=0。

## 子タスク（案）

- [ ] [ID: P6-CPP-LIST-MUT-IR-BYPASS-FIX-01-S1-01] `cpp_emitter.py` における `py_list_*_mut` 直接 emit 箇所を全列挙し、対応する IR ノードの emit 経路と照合する。
- [ ] [ID: P6-CPP-LIST-MUT-IR-BYPASS-FIX-01-S2-01] 直接 emit パスを IR ノード経由 emit に切り替え、生成コードが正しいことを確認する。
- [ ] [ID: P6-CPP-LIST-MUT-IR-BYPASS-FIX-01-S2-02] `py_runtime.h` から 6 関数を削除し、コンパイル・テストが通ることを確認する。
- [ ] [ID: P6-CPP-LIST-MUT-IR-BYPASS-FIX-01-S3-01] fixture / sample / selfhost で非退行を確認する。

## 決定ログ

- 2026-03-18: py_runtime.h 縮小・多言語対応容易化の調査において、IR ノードが存在するにもかかわらず C++ emitter が直接 emit しているパスを確認し起票。`cpp_emitter.py` の 4369/4397/4451/4502/4519/4536 行付近が対象。P5-EAST3-FLOORDIV-MOD-NODE-01 の後に着手予定。
- 2026-03-18: 実装完了。手順: (1) list 操作 12 関数を py_runtime.h から native/built_in/list_ops.h へ移動し py_runtime.h は include のみに変更。(2) cpp_emitter.py の ListAppend/ListExtend/ListPop/ListClear/ListReverse/ListSort ハンドラで `py_list_*_mut()` 呼び出しを `.append()` / `.extend()` / `.pop()` / `.clear()` / `::std::reverse()` / `::std::sort()` 直接呼び出しに置換。(3) 生成済み C++ ファイル（json.cpp 等 9 件）のコールサイトも一括置換。py_list_set_at_mut は IR ノード未存在のため stmt.py に残存（次タスク P6-EAST3-LEN-SLICE-NODE-01 等で対応）。selfhost mismatches=0、fixture pass。cpp 0.581.2。
