<a href="../../en/plans/p1-isinstance-pod-exact.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-ISINSTANCE-POD: POD 型の isinstance exact match 実装

最終更新: 2026-03-27
ステータス: 完了

## 背景

spec-type_id.md §4.2 で POD 型の `isinstance` は exact type match と規定した。しかし現時点では未実装であり、fixture（`test/fixture/source/py/typing/isinstance_pod_exact.py`）も先行配置のみで golden が未生成。

## 対象

### パーサー / resolve

- `isinstance(x, int16)` 等の POD 型リテラルを第二引数に取る `isinstance` を正しく parse / resolve できること
- POD 型の exact match 判定を EAST3 で命令化すること

### fixture / golden

- `test/fixture/source/py/typing/isinstance_pod_exact.py` がパイプライン全段を通過すること
- golden ファイル（east1/east2/east3/east3-opt/linked）を生成・配置すること

### emitter

- 各 emitter が POD isinstance の EAST3 命令を正しく言語写像できること

## 受け入れ基準

1. `isinstance_pod_exact.py` が parse → resolve → compile → optimize → link を通過
2. golden ファイルが生成され、回帰テストに組み込まれている
3. C++ emitter + Go emitter で compile + run + stdout 一致（`py_assert_stdout` 通過）
4. spec-type_id.md §4.2 の規定と実装が一致している

## 決定ログ

- 2026-03-26: spec-type_id.md §4.2 に POD / クラス型の isinstance 判定分離を規定。fixture を先行配置。
- 2026-03-27: `isinstance(x, int16)` などの POD 判定は、EAST3 で `expected_type_id=Name("int16")` の exact-match lane として保持する形に整理した。`int` / `float` は compile lowering で `int64` / `float64` へ正規化する。
- 2026-03-27: Go emitter は `py_is_exact_int16` などの exact helper へ、C++ emitter は `py_runtime_value_exact_is<int16>(...)` へ描画するようにした。fixture `isinstance_pod_exact.py` の golden を生成し、`pytra-cli.py build ... --target cpp/go --run` は両方 `True` を返すことを確認した。
