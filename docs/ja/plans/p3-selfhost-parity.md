<a href="../../en/plans/p3-selfhost-parity.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3-SELFHOST-PARITY: selfhost 済みコンパイラによる fixture/sample parity 検証

最終更新: 2026-03-30
ステータス: 未着手

## 背景

selfhost マトリクスは「toolchain2 を言語 X に変換し、変換後のコンパイラで言語 Y のコードを生成できるか」を示す。しかし「emit できる」だけでは不十分で、「emit されたコードが正しく動く」ことを fixture/sample parity で検証する必要がある。

## フロー

例: selfhost 言語 = C++、emit 先 = Go の場合:

```
1. Python toolchain2 → C++ に変換（pytra-cli2 -build --target cpp）
2. C++ をコンパイル（g++ → selfhost バイナリ生成）
3. selfhost バイナリで fixture の .py → Go に変換
4. Go コードを go run で実行
5. Python 直接実行の stdout と比較（parity check）
```

ステップ 3 が「Python の pytra-cli2 の代わりに selfhost 済みバイナリを使う」点が新しい。ステップ 4〜5 は既存の parity check インフラを再利用できる。

## 設計

### スクリプト

`tools/run/run_selfhost_parity.py` を新設する。

```bash
# C++ selfhost で Go の fixture parity を検証
python3 tools/run/run_selfhost_parity.py \
  --selfhost-lang cpp --emit-target go --case-root fixture

# C++ selfhost で全言語の sample parity を検証
python3 tools/run/run_selfhost_parity.py \
  --selfhost-lang cpp --emit-target go,rs,ts --case-root sample --all-samples
```

### 処理の流れ

1. **selfhost ビルド**: `pytra-cli2 -build --target <selfhost-lang>` で toolchain2 を変換。ターゲット言語のコンパイラでバイナリを生成
2. **emit**: selfhost バイナリを使って fixture/sample の `.py` をターゲット言語に変換
3. **parity check**: 既存の parity check の compile + run + stdout 比較ロジックを再利用
4. **結果記録**: `.parity-results/selfhost_<selfhost-lang>.json` に emit/build/parity の結果を記録

### JSON 形式

```json
{
  "selfhost_lang": "cpp",
  "stages": {
    "emit": {"status": "ok", "timestamp": "2026-03-30T15:00:00"},
    "build": {"status": "ok", "timestamp": "2026-03-30T15:01:00"},
    "parity": {"status": "ok", "timestamp": "2026-03-30T15:10:00"}
  },
  "emit_targets": {
    "go": {
      "status": "ok",
      "fixture_pass": 144,
      "fixture_fail": 2,
      "sample_pass": 18,
      "sample_fail": 0,
      "timestamp": "2026-03-30T15:10:00"
    },
    "rs": {"status": "not_tested", "timestamp": ""},
    "ts": {"status": "not_tested", "timestamp": ""}
  }
}
```

### マトリクスへの反映

`gen_backend_progress.py` は既に `.parity-results/selfhost_<lang>.json` を読む仕組みがある。本スクリプトがこの JSON を書き出せば、selfhost マトリクスに自動反映される。

PASS 条件: `emit_targets.<lang>.fixture_fail == 0 && sample_fail == 0`

### Python 行のハードコード廃止

現在の selfhost マトリクスの Python 行は `_build_selfhost_matrix` 内でハードコードされている（C++ と Go だけ 🟩）。本スクリプトで Python → 各言語の parity も検証し、結果を `.parity-results/selfhost_python.json` に記録する形に移行する。

## 前提条件

- 各言語の selfhost バイナリがビルドできること（P4-CPP-SELFHOST, P6-GO-SELFHOST 等が完了していること）
- fixture/sample の parity check インフラが動作すること（P0-CLI2-RS-TS 等が完了済み）

## 決定ログ

- 2026-03-30: selfhost 済みコンパイラで fixture/sample parity まで通す方針に決定。emit だけでは 🟩 にしない。
