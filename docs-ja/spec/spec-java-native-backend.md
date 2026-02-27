# Java Native Backend 契約仕様

<a href="../../docs/spec/spec-java-native-backend.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

この文書は、`P3-JAVA-NATIVE-01` で導入した `EAST3 -> Java native emitter` 経路の契約を定義する。  
対象は「入力 EAST3 の責務」「未対応時 fail-closed」「runtime 境界」「preview 出力との差分」である。

## 1. 目的

- Java backend の既定経路を sidecar bridge から native 生成へ移行する際の設計境界を固定する。
- 実装中フェーズでも「どこまで対応し、未対応はどう失敗するか」を明文化する。
- `sample/java` が preview ラッパーへ戻る回帰を防ぐ。

## 2. preview 出力との差分

旧経路（preview / sidecar, 撤去済み）:

- `py2java.py` は `transpile_to_js` を呼び、`.java` と `.js` を同時生成する。
- Java 側出力は `ProcessBuilder` で `node <sidecar.js>` を実行するラッパーで、EAST3 本文ロジックを直接表現しない。
- 実行時依存は Java runtime + Node.js + JS runtime shim（`pytra/runtime.js`）である。

移行後（native）:

- `py2java.py` 既定は Java native emitter のみを通し、`.js` sidecar を生成しない。
- Java 側出力は EAST3 本文ロジック（式/文/制御/クラス）を直接 Java コードとして保持する。
- 実行時依存は Java runtime（`src/runtime/java/pytra/`）へ収束し、Node.js 依存を既定経路から排除する。

## 3. 入力 EAST3 ノード責務

native emitter は次の入力契約を満たす EAST3 ドキュメントのみを受理する。

- ルートは `dict` かつ `kind == "Module"`。
- `east_stage == 3` であること（`--east-stage 2` は受理しない）。
- `body` は EAST3 statement ノード列であること。

段階責務（最小セット）:

- S1（骨格）: `Module` / `FunctionDef` / `ClassDef` の枠組みを処理する。
- S2（本文）: 主要 statement/expression（代入、条件、ループ、呼び出し、基本型）を処理する。
- S3（運用）: sample 実運用で使う `math` / 画像 runtime 呼び出しを含む最小互換を処理する。

## 4. fail-closed 契約

native 経路では「未対応入力を暗黙に sidecar へフォールバック」してはならない。

- 未対応ノード `kind` を検出した場合は即時 `RuntimeError` で失敗する。
- エラー文面には少なくとも `lang=java`, `node kind`, `location`（可能な範囲）を含める。
- CLI は非 0 終了し、不完全な `.java` を成功扱いで出力しない。
- 未対応入力を sidecar へ退避する互換モードは持たない。

## 5. runtime 境界

native 経路の Java 生成物は、以下のみを実行時境界として利用する。

- `src/runtime/java/pytra/` 配下の Java runtime API。
- JDK 標準ライブラリ（`java.lang`, `java.util` など）。

禁止事項:

- `ProcessBuilder` による Node.js 起動。
- `.js` sidecar 生成と `pytra/runtime.js` 依存。
- Java 生成物内での JS bridge 前提 import。

## 6. 移行時の検証観点

- `tools/check_py2java_transpile.py` が native 経路で通る。
- `test/unit/test_py2java_*.py` で native-only 前提アサーションを固定する。
- `tools/runtime_parity_check.py --targets java` で Python 基準との出力一致を監視する。
