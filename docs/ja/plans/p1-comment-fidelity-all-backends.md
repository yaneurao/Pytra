# P1: 全言語コメント忠実性ポリシー（生成コメント禁止）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-COMMENT-FIDELITY-01`

背景:
- 現状の生成コードには、元ソースに存在しない emitter 固有コメント（`Auto-generated` / `Runtime helpers are provided` / `TypeScript preview` / `TODO: unsupported` / `pass` 代替コメント）が混在している。
- 一方で、元ソース先頭コメントが一部 backend で欠落するケースがあり、コメントの忠実性が backend 間で不統一になっている。
- 「コメントは元ソース由来のみ許可」という明確な契約を設けないと、将来の emitter 追加時に同じ逸脱が再発する。

目的:
- 全 backend で「元ソース由来コメントのみ出力」を強制する。
- emitter 固有の説明コメント/未対応 TODO コメントを全面禁止し、未対応は fail-closed（例外）へ統一する。
- コメント出力の回帰をテストとチェックツールで常時検知できる状態にする。

対象:
- `src/hooks/*/emitter/*.py`（`cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua`）
- `src/py2*.py`（必要な導線更新のみ）
- `test/unit/test_py2*smoke.py`
- （必要なら）`tools/check_comment_fidelity.py`
- `sample/*` 再生成導線

非対象:
- コメント文言の翻訳/整形ルール変更
- docstring 取り扱い仕様の全面再設計
- 非コメントのコード整形（改行・空白のみの差異）

受け入れ基準:
- 出力コードに emitter 固有の定型コメント（`Auto-generated` / `Runtime helpers are provided` / `preview` / `TODO: unsupported` / `pass` コメント）が含まれない。
- 元ソース先頭コメントと文前コメント（`module_leading_trivia` / `leading_trivia`）が、対応 backend で欠落なく出力される。
- `pass` はコメントではなく各言語の no-op 文で表現されるか、不要なら非出力となる。
- 未対応構文はコメント埋め込みではなく例外で停止する（fail-closed）。
- 主要 backend の smoke test でコメント忠実性の回帰テストが通過する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2*smoke.py' -v`
- `python3 tools/regenerate_samples.py --langs cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua --force`

決定ログ:
- 2026-02-28: ユーザー要望により「全言語で、元ソースにないコメント出力を禁止し、元コメントを強制反映する」方針を `P1-COMMENT-FIDELITY-01` として起票。

## 分解

- [ ] [ID: P1-COMMENT-FIDELITY-01-S1-01] 全 emitter の固定コメント/`TODO`/`pass` コメント出力箇所を棚卸しし、禁止パターン一覧を固定する。
- [ ] [ID: P1-COMMENT-FIDELITY-01-S1-02] コメント出力契約（許可ソース: `module_leading_trivia` / `leading_trivia` のみ）を仕様化し、fail-closed 方針を明文化する。
- [ ] [ID: P1-COMMENT-FIDELITY-01-S2-01] `ts/go/java/swift/kotlin/ruby/lua` の固定コメント出力を撤去し、元コメント伝播のみへ統一する。
- [ ] [ID: P1-COMMENT-FIDELITY-01-S2-02] `cpp/rs/cs/js` の `pass` / unsupported コメント経路を no-op または例外へ置換し、生成コメントを残さない実装へ寄せる。
- [ ] [ID: P1-COMMENT-FIDELITY-01-S3-01] 全 `test_py2*smoke.py` に禁止コメント検査と元コメント反映テストを追加し、回帰を固定する。
- [ ] [ID: P1-COMMENT-FIDELITY-01-S3-02] `sample/*` 再生成と差分検証を行い、全言語の出力先に固定コメントが残存しないことを確認する。
