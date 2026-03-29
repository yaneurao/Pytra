<a href="../../ja/plans/p2-checker-unification.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p2-checker-unification.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p2-checker-unification.md`

# P2: `check_py2*` checker の単一化（`--target` + プロファイル化）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-CHECKER-UNIFY-01`

背景:
- `tools/check/check_py2cpp_transpile.py` など言語別 checker が多数存在し、CI・計画書・テストが個別ファイル名へ強く依存している。
- 役割は本質的に共通（`py2x --target <lang>` で fixture/sample を変換し、成功/既知失敗契約を検証）であり、分割ファイル維持は重複実装と運用コストを増やす。
- ユーザー方針として、checker も単一入口へ統一し、言語差分は設定で扱う構成が望ましい。

目的:
- checker を `tools/check/check_py2x_transpile.py --target <lang>` の単一入口へ統一する。
- 言語差分（ケース集合、expected-fail、追加アサーション）はプロファイル定義へ移し、スクリプト本体の分岐を縮小する。
- 既存 `check_py2*.py` は段階移行後に削除する（移行期間は互換ラッパ許容）。

対象:
- `tools/check/check_py2*.py` 群
- 新規統一 checker（`tools/check/check_py2x_transpile.py`）
- checker 設定（target別プロファイル）
- 呼び出し元（`tools/run/run_local_ci.py`, 契約検証スクリプト, docs/plan のコマンド例）

非対象:
- backend 生成品質の改善
- parity ロジックそのものの変更
- selfhost 実行経路の再設計

受け入れ基準:
- 単一 checker で `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php/nim` を `--target` 指定で実行できる。
- 言語別 expected-fail/追加検証は設定ファイルで管理される。
- `run_local_ci.py` と関連スクリプトは単一 checker 呼び出しへ移行済み。
- 旧 `check_py2*.py` は最終的に削除される（中間段階では薄い互換ラッパのみ許容）。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 -m py_compile tools/check/check_py2x_transpile.py`
- `python3 tools/check/check_py2x_transpile.py --target cpp`
- `python3 tools/check/check_py2x_transpile.py --target java`
- `python3 tools/check/check_py2x_transpile.py --target scala`
- `python3 tools/run/run_local_ci.py`

## 分解

- [x] [ID: P2-CHECKER-UNIFY-01-S1-01] 既存 `check_py2*.py` の差分（ケース選定・expected-fail・追加品質検証）を棚卸しして統一仕様を定義する。
- [x] [ID: P2-CHECKER-UNIFY-01-S1-02] target別プロファイル形式（ケース集合、許容失敗、追加検証フック）を設計する。
- [x] [ID: P2-CHECKER-UNIFY-01-S2-01] `tools/check/check_py2x_transpile.py` を実装し、`--target` で全言語の共通検証を実行可能にする。
- [x] [ID: P2-CHECKER-UNIFY-01-S2-02] 既存 `check_py2*.py` を互換ラッパ化し、新checkerへ委譲させる。
- [x] [ID: P2-CHECKER-UNIFY-01-S2-03] `run_local_ci.py` / 契約検証スクリプト / docs の呼び出しを単一 checker に置換する。
- [x] [ID: P2-CHECKER-UNIFY-01-S3-01] 互換期間終了後に `check_py2*.py` を削除し、再導入防止ガードを追加する。
- [x] [ID: P2-CHECKER-UNIFY-01-S3-02] unit/CI 回帰を実行し、単一化後の非退行を固定する。

決定ログ:
- 2026-03-05: ユーザー指示により、言語別 checker 群は将来削除前提とし、`--target` 駆動の単一 checker へ統合する方針を確定。
- 2026-03-05: [ID: `P2-CHECKER-UNIFY-01-S1-01`] `check_py2*_transpile.py` 14本の差分を棚卸しし、差分軸を「ケース集合（全fixture+sample or 明示CASES）」「expected-fail 形式（単純集合 or 構造化spec）」「追加品質フック（scala sample01 / php sample18）」「追加CLI（`--skip-east3-contract-tests` / `--check-multi-file` / `--check-yanesdk-smoke` / stage2 probe）」へ固定した。
- 2026-03-05: [ID: `P2-CHECKER-UNIFY-01-S1-02`] 単一 checker 用 profile 形式を `target / case_mode / cases / expected_failures / quality_hooks / flags / stage2_probe` で固定し、単純 expected-fail 一覧を構造化 `expected_failures` へ正規化する仕様を確定した。
- 2026-03-05: [ID: `P2-CHECKER-UNIFY-01-S2-01`] `tools/check/check_py2x_transpile.py` と `tools/check/check_py2x_profiles.json` を追加し、共通実行器（cases解決・expected-fail skip/validate・quality hook・stage2 probe）を実装。まず `cpp/java/scala` profile を移植し、`sample/py/01_mandelbrot.py` で3target smoke 通過を確認した。
- 2026-03-05: [ID: `P2-CHECKER-UNIFY-01-S2-01`] profile を `cpp/cs/go/java/js/kotlin/lua/nim/php/ruby/rs/scala/swift/ts` へ拡張し、`php_sample18` 品質フック・runtime sidecar 内容検証・`cpp_emitter_separation` preflight を共通実行器へ追加。`--skip-east3-contract-tests` 付きで `sample/py/01_mandelbrot.py` 全target smoke（14件）を通過して S2-01 を完了。
- 2026-03-05: [ID: `P2-CHECKER-UNIFY-01-S2-02`] `check_py2cpp/cs/go/java/js/kotlin/lua/nim/php/rb/rs/scala/swift/ts` を互換ラッパ化し、実処理を `check_py2x_transpile.py --target` へ委譲。`cpp` 互換維持のため unified 側へ `--check-multi-file-imports` / `--check-yanesdk-smoke` を追加し、`nim/cpp/js` ラッパ実行（`js` は `--skip-east3-contract-tests`）で委譲結果が旧導線と整合することを確認。
- 2026-03-05: [ID: `P2-CHECKER-UNIFY-01-S2-03`] `run_local_ci.py`・`check_noncpp_east3_contract.py`・`check_gsk_native_regression.py` の checker 呼び出しを `check_py2x_transpile.py --target ...` へ置換。`check_noncpp` からの `js/ts` 呼び出しは `--skip-east3-contract-tests` を付与して再帰を回避し、unified 側 preflight も旧仕様（`test_east2_to_east3_lowering.py` / `test_east3_cpp_bridge.py`）へ戻して非循環化した。`check_noncpp --skip-transpile` + `check_py2js_transpile.py` + `check_py2ts_transpile.py` を通過。
- 2026-03-05: [ID: `P2-CHECKER-UNIFY-01-S3-01`] 旧 `tools/check/check_py2{cpp,cs,go,java,js,kotlin,lua,nim,php,rb,rs,scala,swift,ts}_transpile.py` を削除し、`tools/check/check_legacy_transpile_checkers_absent.py` + `test_check_legacy_transpile_checkers_absent.py` を追加して再導入を fail-fast 化。`run_local_ci.py` に新ガードを統合し、Scala checker unit は `check_py2x_transpile.py` の profile 検証へ移行した。
- 2026-03-05: 回帰セット（`py_compile`、`test_check_legacy_transpile_checkers_absent.py`、`test_check_py2scala_transpile.py`、`check_legacy_transpile_checkers_absent.py`、`check_noncpp_east3_contract.py --skip-transpile`、`check_py2x_transpile.py --target cpp/java/scala/js/ts`）を再実行し全通過。単一 checker への置換後も `cpp/java/scala` の全ケース回帰が維持されることを確認した。

## S1-01 棚卸し結果（固定）

| checker | ケース集合 | expected-fail | 追加検証 / 追加CLI |
| --- | --- | --- | --- |
| `cpp` | 全 `fixtures+sample` | 6件（単純集合） | `--check-multi-file`, `--check-yanesdk-smoke`, stage2 probe |
| `js` / `ts` | 全 `fixtures+sample` | 各8件（単純集合） | `--skip-east3-contract-tests` |
| `cs` | 全 `fixtures+sample` | 8件（単純集合） | 追加なし |
| `go` / `java` / `kotlin` / `rb` / `rs` / `swift` | 全 `fixtures+sample` | 各10件（単純集合） | `rb` のみ stage2 probe |
| `lua` | 全 `fixtures+sample` | 53件（単純集合） | stage2 probe |
| `scala` | 全 `fixtures+sample` | 構造化 `ExpectedFailureSpec`（カテゴリ+部分一致） | `sample/01` 品質フック |
| `php` | 明示 `CASES` 9件 | なし | `sample/18` 品質フック + stage2 probe |
| `nim` | 明示 `CASES` 6件 | なし | stage2 probe |

### 統一仕様への入力（S1-01 結論）

1. 単一 checker は `profile.case_mode = all|explicit` を持ち、`explicit` は `cases[]` で指定する。
2. expected-fail は `profile.expected_failures` を `{"path": {"category": "...", "contains": "..."}}` の構造化形式へ統一し、単純集合は `category=expected_failure` へ正規化する。
3. 追加品質検証は `profile.quality_hooks[]`（`sample01_scala`, `sample18_php` など）へ分離し、本体は hook dispatcher のみ持つ。
4. 追加CLIは `profile.flags`（`check_multi_file`, `check_yanesdk_smoke`, `skip_east3_contract_tests`, `stage2_probe`）へ収束させる。

## S1-02 profile 仕様（固定）

```json
{
  "target": "java",
  "case_mode": "all",
  "cases": [],
  "expected_failures": {
    "test/fixtures/signature/ng_kwargs.py": {
      "category": "expected_failure",
      "contains": ""
    }
  },
  "quality_hooks": [],
  "flags": {
    "check_multi_file": false,
    "check_yanesdk_smoke": false,
    "skip_east3_contract_tests": false
  },
  "stage2_probe": {
    "enabled": false,
    "source": ""
  }
}
```

1. `case_mode`: `all` は `test/fixtures/**/*.py + sample/py/*.py`、`explicit` は `cases[]` のみを検証。
2. `expected_failures`: すべて `path -> {category, contains}` 形式へ統一。旧「単純集合」は `category=expected_failure` / `contains=\"\"` へ変換。
3. `quality_hooks`: 言語固有の品質検証（`scala_sample01`, `php_sample18` など）を checker 本体から分離。
4. `flags`: 旧 checker の追加CLI分岐（multi-file/yanesdk/skip-east3-contract）をここへ移す。
5. `stage2_probe`: 旧 checker の `--east-stage 2` 互換検証を profile 側で有効化する。
