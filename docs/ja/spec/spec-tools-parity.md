<a href="../../en/spec/spec-tools-parity.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# `tools/` — 言語間 parity 確認

[索引に戻る](./spec-tools.md)

## 1. ツール一覧

- `tools/check/runtime_parity_check.py`
  - 目的: 複数ターゲット言語でのランタイム平準化チェックを実行する。
  - 主要オプション: `--targets <langs>`（カンマ区切り）, `--case-root {fixture,sample}`, `--category <subdir>`（fixture サブディレクトリで絞り込み。例: `oop`, `control`, `typing`）, `--all-samples`, `--east3-opt-level`, `--cpp-codegen-opt`, `--cmd-timeout-sec`, `--summary-json`
  - 補足: `--category` を指定すると、`test/fixture/source/py/<category>/` 配下のケースのみ実行する。全 fixture（132+ 件）を回さず、カテゴリ単位で回帰を確認したい場合に使う。
  - 補足: `elapsed_sec` / `elapsed` / `time_sec` のような不安定な時間行は、既定で比較対象から除外する。
  - 補足: artifact 比較は `output:` で報告された生成物に対して `存在 + size + CRC32` を必須一致条件とする。
  - 補足: ケース実行前に `sample/out`, `test/out`, `out` の同名 artifact を削除し、前回実行物の取り違えを防止する。
  - 補足: timeout 時は process-group 単位で kill し、`*_swift.out` などの子プロセス孤立を許容しない。
- `tools/check/runtime_parity_check_fast.py`
  - 目的: `runtime_parity_check.py` の高速版。transpile 段を toolchain2 Python API のインメモリ呼び出しに置き換え、プロセス起動と中間ファイル I/O を省略する。
  - 主要オプション: `runtime_parity_check.py` と同一（`--targets`, `--case-root`, `--category`, `--all-samples`, `--east3-opt-level`, `--cmd-timeout-sec`, `--summary-json`）
  - 制限: `--cpp-codegen-opt` は未対応。対応ターゲットは現時点で `cpp` と `go`。
  - 実行方法: `PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py [options]`
- `tools/check/check_all_target_sample_parity.py`
  - 目的: canonical parity group（`cpp`, `js_ts`, `compiled`, `scripting_mixed`）を順に実行し、全 target sample parity を確定する。
  - 主要オプション: `--groups`, `--east3-opt-level`, `--cpp-codegen-opt`, `--summary-dir`
- `tools/check/check_noncpp_backend_health.py`
  - 目的: linked-program 後の non-C++ backend health gate を family 単位で集約し、`primary_failure` / `toolchain_missing` / family の broken/green を 1 コマンドで確認する。
  - 主要オプション: `--family`, `--targets`, `--skip-parity`, `--summary-json`
- `tools/gen/export_backend_test_matrix.py`
  - 目的: `tools/unittest/emit/**` と shared starred smoke を実行し、JA/EN の backend test matrix docs を再生成する。

## 2. parity check の高速化: インメモリパイプライン

### 現状の問題

`runtime_parity_check.py` は各ケースで `python src/pytra-cli.py ...` をサブプロセスとして起動し、中間ファイル（`.east1` → `.east2` → `.east3` → linked JSON → emit）をディスク経由でやり取りする。132 fixture × 複数言語で数時間かかる主因はこのプロセス起動 + disk I/O のオーバーヘッドである。

### 解決策

toolchain2 の各段は dict in / dict out の Python API を持つ:

```python
from toolchain2.parse.py.parse_python import parse_python_file       # → dict (EAST1)
from toolchain2.resolve.py.resolver import resolve_east1_to_east2     # → dict (EAST2)
from toolchain2.optimize.optimizer import optimize_east3_document     # → dict (EAST3-opt)
from toolchain2.link.linker import link_modules                       # → LinkResult
from toolchain2.emit.go.emitter import emit_go_module                 # → str (Go source)
from toolchain2.emit.cpp.emitter import emit_cpp_module               # → str (C++ source)
```

parity check で CLI サブプロセスの代わりにこれらの API を直接呼べば、中間ファイルのディスク書き出しを省略できる。1 プロセス内で parse → resolve → compile → optimize → link → emit をインメモリで回すことで大幅に高速化される。

### 移行方針

1. `runtime_parity_check.py` の transpile 段を CLI 呼び出しから Python API 直接呼び出しに変更する
2. compile + run 段は引き続きサブプロセス（`g++`, `go run` 等）を使う（ターゲット言語のコンパイラはプロセス外）
3. `--cli-mode` フラグで従来の CLI 経由実行も残し、API 呼び出しとの結果一致を検証可能にする

実装: `tools/check/runtime_parity_check_fast.py`（registry を1回だけロードし、全ケースで共有する高速版）

### 使い方

```bash
# oop カテゴリだけ C++ で回す
PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py \
  --category oop --targets cpp

# 全 fixture を Go で回す
PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py \
  --targets go

# sample 18 件を C++ で回す
PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py \
  --case-root sample --all-samples --targets cpp

# 個別ケース指定
PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py \
  class inheritance super_init --targets cpp

# benchmark モード（sample 実行時間を計測し .parity-results/ に記録）
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets go,cpp --case-root sample --all-samples --benchmark

# benchmark 結果から sample/README の表を手動更新
python3 tools/gen/gen_sample_benchmark.py
```

注: `PYTHONPATH=src:tools/check` は toolchain2 と runtime_parity_check モジュールの解決に必要。

`--benchmark` は warmup=1, repeat=3, 中央値で計測する。通常の parity check は 1 回実行のまま。計測結果は `.parity-results/<target>_sample.json` の各ケースの `elapsed_sec` に記録され、parity check 末尾で `gen_sample_benchmark.py` が自動実行される（前回生成から10分以上経過時のみ）。

参照: `docs/ja/plans/plan-pipeline-redesign.md` §3.5「パフォーマンスノウハウ: インメモリパイプライン」

## 3. smoke テスト運用

- 共通 smoke（CLI 成功、`--east-stage 2` 拒否、`load_east`、add fixture）は `tools/unittest/common/test_py2x_smoke_common.py` を正本とする。
- 言語別 smoke（`tools/unittest/emit/<lang>/test_py2*_smoke.py`）は言語固有の emitter/runtime 契約だけを保持し、共通ケースを再実装しない。
- 各言語 smoke には責務境界コメント（`Language-specific smoke suite...`）を必須とし、`tools/check/check_noncpp_east3_contract.py` で静的検証する。
- smoke 実行時の `PYTHONPATH` は `src:.:test/unit` を正本とする。`comment_fidelity.py` など `test/unit` 直下 helper を読む smoke suite があるため、`test/unit` を落として実行してはならない。
- 回帰の推奨順は次の 3 本:
  - `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s tools/unittest/common -p 'test_py2x_smoke*.py'`
  - `python3 tools/check/check_noncpp_east3_contract.py --skip-transpile`
  - `python3 tools/check/check_py2x_transpile.py --target <lang>`（対象言語分）

## 4. non-C++ backend health matrix（linked-program 後）

- non-C++ backend の recovery baseline は `static_contract -> common_smoke -> target_smoke -> transpile -> parity` の順で評価する。
- `parity` は前段 gate をすべて通した target にだけ実行する。前段 failure がある target を parity failure として集計してはならない。
- `toolchain_missing` は `runtime_parity_check.py` の skip をそのまま infra baseline として保持し、`parity_fail` と分離して扱う。
- 2026-03-08 snapshot では Wave 1 は `js/ts` が green、`rs/cs` が `toolchain_missing`、Wave 2 の `go/java/kotlin/swift/scala` と Wave 3 の `ruby/lua/php/nim` も sample parity 18 case 全件 `toolchain_missing` とする。
- 日常の family 単位 health check は `python3 tools/check/check_noncpp_backend_health.py --family wave1` のように実行し、family status は `broken_targets == 0` なら `green` とする。`toolchain_missing` は family を壊さず、別カウンタで表示する。
- `tools/run/run_local_ci.py` は `python3 tools/check/check_noncpp_backend_health.py --family all --skip-parity` を含み、parity 非依存の smoke/transpile gate を日常回帰へ常設する。
- `tools/run/run_local_ci.py` は `python3 tools/check/check_jsonvalue_decode_boundaries.py` も含み、selfhost/host の JSON artifact 境界が raw `json.loads(...)` へ戻る増分を local CI で止める。

## 5. 全 target sample parity 完了条件

- canonical parity target order は `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim` とする。これは `list_parity_targets()` の返却順と一致させる。
- 「全target parity green」は `python3 tools/check/runtime_parity_check.py --targets cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2 --cpp-codegen-opt 3` 実行時に、全 target / 全 18 sample case が `ok` のみで完了する状態を指す。
- full green 判定では `toolchain_missing` を例外扱いしない。`case_missing`, `python_failed`, `python_artifact_missing`, `toolchain_missing`, `transpile_failed`, `run_failed`, `output_mismatch`, `artifact_presence_mismatch`, `artifact_missing`, `artifact_size_mismatch`, `artifact_crc32_mismatch` はすべて 0 件でなければならない。
- target 群を分けて確認する場合も、基準は同じとする。
  - baseline target: `python3 tools/check/runtime_parity_check.py --targets cpp --case-root sample --all-samples --east3-opt-level 2 --cpp-codegen-opt 3`
  - JS/TS: `python3 tools/check/runtime_parity_check.py --targets js,ts --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2`
  - compiled target: `python3 tools/check/runtime_parity_check.py --targets rs,cs,go,java,kotlin,swift,scala --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2`
  - scripting / mixed target: `python3 tools/check/runtime_parity_check.py --targets ruby,lua,php,nim --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2`
- 日常の full-target 再実行は `python3 tools/check/check_all_target_sample_parity.py --summary-dir work/logs/all_target_sample_parity` を canonical wrapper とする。wrapper は上記 4 group を順に実行し、`all-target-summary.json` に統合結果を書き出す。

## 6. Debian 12 parity bootstrap snapshot

- 2026-03-08 時点の current machine は Debian 12 (`bookworm`) / `root` 前提で bootstrap を実施した。
- compiled target の bootstrap command:
  - `apt-get update`
  - `apt-get install -y rustc mono-mcs golang-go openjdk-17-jdk kotlin scala nim`
  - `apt-get install -y binutils-gold gcc git libcurl4-openssl-dev libedit-dev libpython3-dev libsqlite3-dev uuid-dev gnupg2`
  - `curl -fL -o /opt/swift-6.2.2-RELEASE-debian12.tar.gz https://download.swift.org/swift-6.2.2-release/debian12/swift-6.2.2-RELEASE/swift-6.2.2-RELEASE-debian12.tar.gz`
  - `tar -xf /opt/swift-6.2.2-RELEASE-debian12.tar.gz -C /opt`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swift /usr/local/bin/swift`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swiftc /usr/local/bin/swiftc`
- scripting / mixed target の bootstrap command:
  - `apt-get install -y ruby lua5.4 php-cli`
- bootstrap 後の `runner_needs` 実測では `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim` がすべて `OK` になっていることを確認済みとする。
