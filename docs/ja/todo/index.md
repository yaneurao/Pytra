# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-11

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

### P0: relative import support

文脈: [docs/ja/plans/p0-relative-import-support.md](../plans/p0-relative-import-support.md)

1. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01] `from .m import x` / `from ..pkg import y` を multi-file 変換で正式対応する。
2. [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S1-01] relative import の syntax / diagnostics / root escape policy を spec と plan に固定する。
3. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-01] self-hosted parser が relative `from-import` を受理し、raw module text を保持できるようにする。
4. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-02] frontend の module map 構築で relative module を absolute module_id へ正規化し、EAST / import meta 全体へ反映する。
5. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-03] import graph 診断を relative import 正式対応の contract に更新し、root escape と missing module を区別して fail-closed にする。
6. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S3-01] representative CLI / unit 回帰（正常系・missing・duplicate・root escape・wildcard）を追加する。
7. [ ] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S3-02] `spec-user.md` / `spec-import.md` / tutorial の import 記述を更新する。

### P4: `py_runtime.h` final thin compat removal

文脈: [docs/ja/plans/p4-crossruntime-pyruntime-final-thincompat-removal.md](../plans/p4-crossruntime-pyruntime-final-thincompat-removal.md)

1. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01] `py_runtime.h` の final thin compat 2 本を cross-runtime で撤去する。
2. [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S1-01] residual を `cpp_header_final_thincompat_defs` / `cpp_generated_final_thincompat_blocker` / `rs_runtime_generic_alias_surface` / `cs_runtime_generic_alias_surface` に棚卸しし、inventory/test を追加する。
3. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S1-02] target end state と bundle 単位の削減順を docs/source guard に固定する。
4. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S2-01] checked-in C++ generated/native caller を thin helper へ寄せ、`cpp_generated_final_thincompat_blocker` を空にする。
5. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S2-02] Rust/C# runtime alias surface を internal/private seam へ縮める。
6. [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S3-01] `py_runtime.h` から template `py_runtime_type_id` / `py_isinstance` を削除し、representative regression / docs / archive を更新する。
