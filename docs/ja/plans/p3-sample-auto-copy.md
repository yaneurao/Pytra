<a href="../../en/plans/p3-sample-auto-copy.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3-SAMPLE-AUTO-COPY: sample parity PASS 時に sample/<lang>/ へ自動コピー

最終更新: 2026-03-30
ステータス: 未着手

## 背景

`sample/<lang>/` には各言語への変換結果が展示用に配置されている。現在は `regenerate_samples.py` を手動で回して更新しているが、emitter を改善しても再生成を忘れることがある。

parity check は sample を変換して実行結果を検証する。PASS したコードは「正しく動く変換結果」なので、そのまま `sample/<lang>/` にコピーすれば、手動再生成が不要になる。

## 設計

### コピー条件

- parity check の sample 実行で **PASS** したケースのみコピーする
- FAIL のケースは既存ファイルをそのまま維持する（壊れたコードで上書きしない）
- Python 実行が失敗した場合は何もコピーしない

### コピー先

emit ディレクトリのファイルを `sample/<lang>/` にコピーする。

```
emit ディレクトリ:
  work/transpile/parity-fast/.../transpile/go/emit/01_mandelbrot.go

コピー先:
  sample/go/01_mandelbrot.go
```

ファイル名は既存の命名規則（`<番号>_<名前>.<ext>`）に合わせる。

### 対象言語

toolchain2 で emit できる全言語（cpp, go, rs, ts, js 等）。`sample/<lang>/` ディレクトリが存在しない言語は `mkdir -p` で作成する。

### `regenerate_samples.py` との関係

parity check が自動コピーするようになると `regenerate_samples.py` の主要な役割（変換 + 配置）は parity check に吸収される。ただし:

- parity check は Python 実行が前提（stdout 比較が必要）。Python が動かない環境では使えない
- `regenerate_samples.py` は emit だけで配置できる（実行不要）

当面は両方残し、parity check の自動コピーが安定したら `regenerate_samples.py` の廃止を検討する。

## 決定ログ

- 2026-03-30: parity PASS 時に sample/<lang>/ へ自動コピーする方針に決定。手動の `regenerate_samples.py` 実行忘れを解消する。
