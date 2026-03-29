<a href="../../en/plans/p2-build-output-structure.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: ビルド出力ディレクトリ構造の標準化

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-BUILD-OUTPUT-STRUCTURE`

## 背景

spec-folder.md §2.8 で定義された標準ビルド出力構造に、linker / emitter / pytra-cli.py を対応させる。

旧構造:
- linker: `link-output.json` + `linked/` サブディレクトリ
- emitter: `out/<lang>/` に出力
- pytra-cli build: `.pytra_linked/` に linker 出力を隔離

新構造:
```
<output_root>/
├── manifest.json     # linker manifest（旧 link-output.json）
├── east3/            # linker 中間生成物（旧 linked/）
└── emit/             # emitter 最終出力（旧 out/<lang>/）
```

## 対象

| 変更対象 | 内容 |
|---|---|
| `src/toolchain/link/materializer.py` | `link-output.json` → `manifest.json`, `linked/` → `east3/` |
| `src/toolchain/link/global_optimizer.py` | `_linked_output_path` の prefix `linked/` → `east3/` |
| `src/toolchain/link/link_manifest_io.py` | ラベル更新 |
| `src/toolchain/link/cli.py` | デフォルト出力先・ドキュメント更新 |
| `src/toolchain/emit/*.py` (全 15 emitter) | docstring / ヘルプの `link-output.json` → `manifest.json` |
| `src/toolchain/emit/loader.py` | コメント更新 |
| `src/pytra-cli.py` | `.pytra_linked` 廃止、`emit/` サブディレクトリ導入 |
| `tools/check/check_py2x_transpile.py` | `linked_dir` → `build_dir`, `manifest.json` 参照 |
| `tools/build_selfhost.py` | `linked_dir` → `build_dir`, `manifest.json` 参照 |
| `tools/unittest/link/test_*.py` | `link-output.json` → `manifest.json`, `linked/` → `east3/` |
| `docs/ja/spec/spec-linker.md` | `link-output.json` → `manifest.json` |

## 非対象

- アーカイブドキュメント（歴史記録のため変更しない）
- `docs/en/` の翻訳同期（後追い許容）

## 受け入れ基準

- [x] linker が `manifest.json` + `east3/` を出力する
- [x] emitter が `manifest.json` を読み込む
- [x] `pytra-cli.py build` が新構造で動作する
- [x] `check_py2x_transpile.py --target cpp` が regression なく通過する

## 決定ログ

- 2026-03-22: S1〜S4 を一括実施。linker 出力名を `manifest.json` + `east3/` に変更、全 emitter の参照を更新、pytra-cli.py を `.pytra_linked` 廃止 + `emit/` サブディレクトリ導入に変更、tools / test / 現行仕様ドキュメントを更新。`check_py2x_transpile.py --target cpp` で 136/150 ok（既存の未対応機能のみ fail、regression なし）を確認。
