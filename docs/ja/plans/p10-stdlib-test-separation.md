<a href="../../en/plans/p10-stdlib-test-separation.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P10-STDLIB-TEST-SEPARATION: stdlib テストを fixture から分離し、モジュール別マトリクスを生成する

最終更新: 2026-03-30
ステータス: 保留

## 背景

現在 stdlib のテストは `test/fixture/source/py/stdlib/` に fixture として配置されている。fixture は「言語機能の単体テスト」が目的で、stdlib モジュールの API 網羅テストとは性質が異なる。

また、ユーザーが「この言語でこのモジュールが使えるか」を判断するためのモジュール別マトリクスが必要。

## 設計

### ディレクトリ構成

```
test/stdlib/source/py/
  math/
    test_sqrt.py
    test_trig.py
    test_constants.py
  json/
    test_loads.py
    test_dumps.py
    test_unicode.py
  pathlib/
    test_read_write.py
    test_joinpath.py
  re/
    test_match.py
    test_search.py
    test_sub.py
  argparse/
    test_basic.py
  sys/
    test_argv.py
  os/
    test_makedirs.py
    test_glob.py
  sqlite3/
    test_connect.py
    test_query.py
```

モジュールごとにフォルダを分け、テストファイルを配置する。

### parity check 対応

- `--case-root stdlib` を追加
- `.parity-results/<lang>_stdlib.json` に結果蓄積
- モジュール名はフォルダ名から自動取得

### モジュール別マトリクス

`gen_backend_progress.py` が stdlib 結果を読んでモジュール × 言語のマトリクスを生成する。

```
| モジュール | C++ | Go | Rust | TS | JS | ... |
|---|---|---|---|---|---|---|
| math | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | |
| json | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | |
| pathlib | 🟩 | 🟩 | 🟥 | 🟥 | 🟥 | |
| re | 🟩 | 🟥 | 🟥 | 🟥 | 🟥 | |
| sqlite3 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | |
```

PASS 条件: モジュールフォルダ内の全テストが parity PASS。1件でも FAIL ならモジュール全体が FAIL。

出力先: `docs/ja/progress/backend-progress-stdlib.md`（日英同時生成）

progress/index.md にリンクを追加する。

### fixture からの移行

- `test/fixture/source/py/stdlib/` の既存テストを `test/stdlib/source/py/<module>/` に移動する
- fixture マトリクスからは消え、stdlib マトリクスに表示される
- 移行は段階的に行い、まず1モジュール（math）で仕組みを作ってから残りを移行する

### ユーザー向けの価値

ユーザーが「Go で json 使えるか？」「Rust で pathlib 使えるか？」を一目で判断できる。spec-pylib-modules.md と連携し、モジュールのドキュメントからマトリクスにリンクする。

## 前提条件

重い stdlib（sqlite3 等）を追加するタイミングで着手する。今の軽い stdlib テストだけなら急がない。

## 決定ログ

- 2026-03-30: stdlib テストを fixture から分離し、モジュール別マトリクスを生成する方針に決定。最初の移行は重い stdlib が追加されるタイミングで行う。
