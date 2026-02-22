# TASK GROUP: TG-P1-MULTILANG-QUALITY

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-MQ-01` 〜 `P1-MQ-08`

背景:
- `sample/cpp/` と比べて、`sample/rs` および他言語（`cs/js/ts/go/java/swift/kotlin`）の生成コードは可読性の劣化が目立つ。
- 不要な `mut`、過剰な括弧・cast・clone、未使用 import などがレビュー/保守コストを押し上げている。
- C++ 以外では selfhost / 多段 selfhost の成立可否が未整理で、実行可能性の判断材料が不足している。
- `sample/py` を毎回 Python 実行して比較すると検証時間が増えるため、ゴールデン出力の保存と再利用導線が必要。

目的:
- 非 C++ 言語の生成コード品質を、`sample/cpp/` と同等の可読性水準まで段階的に引き上げる。

対象:
- `sample/{rs,cs,js,ts,go,java,swift,kotlin}` の出力品質改善
- 各言語の emitter/hooks/profile における冗長出力パターンの削減
- 品質回帰を防ぐ検査項目の追加
- 非 C++ 言語での selfhost 可否（自己変換生成物での再変換）検証
- 非 C++ 言語での多段 selfhost（生成物で再自己変換）検証

非対象:
- 生成コードの意味変更
- runtime 機能追加そのもの
- C++ 出力の追加最適化

受け入れ基準:
- 非 C++ 言語の `sample/` 生成物で、主要冗長パターン（過剰 `mut` / 括弧 / cast / clone / 未使用 import）が段階的に削減される。
- 可読性改善後も既存 transpile/smoke の通過を維持する。
- 品質指標と測定手順が文書化され、回帰時に再測定可能である。
- 非 C++ 各言語について、selfhost 可否と多段 selfhost 可否（1段目/2段目）が同一フォーマットで記録される。
- 失敗言語は、再現手順と失敗カテゴリ（変換失敗 / 実行失敗 / コンパイル失敗 / 出力不一致）まで記録される。
- `sample/` 生成物にタイムスタンプ等の非決定情報を埋め込まず、CI 再生成時に差分ゼロを維持する。
- `sample/py` のゴールデン出力置き場と更新手順（通常比較 / 明示更新）を文書化し、通常検証時に毎回 Python 実行しなくてよい状態にする。

確認コマンド:
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`

決定ログ:
- 2026-02-22: 初版作成（`sample/cpp` 水準を目標に、非 C++ 言語の出力品質改善を TODO 化）。
