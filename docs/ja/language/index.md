# 言語別仕様

<a href="../../en/language/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


各ターゲット言語の個別仕様をまとめた入口です。

- 共通 language feature:
  - nominal ADT v1 の canonical surface と staged rollout: [nominal ADT v1 ガイド](./nominal-adt-v1.md)
  - feature × backend の support state と rollout handoff: [Backend Parity Matrix](./backend-parity-matrix.md)
  - feature × required_lane × backend の bundle-based coverage seed と ownership: [Backend Coverage Matrix](./backend-coverage-matrix.md)
  - backend-owned test suite の実測 green 状態: [Backend Test Matrix](./backend-test-matrix.md)
- C++:
  - サポート状況（テスト根拠つき）: [py2cpp サポートマトリクス](./cpp/spec-support.md)
- Julia:
  - native emitter（EAST3 直接生成）: `src/toolchain/emit/julia/`
  - ランタイム: `src/runtime/julia/built_in/py_runtime.jl`
