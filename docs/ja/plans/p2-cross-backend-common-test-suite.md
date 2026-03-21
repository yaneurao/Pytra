# P2: 全 backend 共通テストスイートの整備

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-COMMON-TEST-*`

## 背景

現在 C++ backend のみ 621 テスト（17 ファイル）が存在し、他言語は 7〜48 テスト（各 1 ファイル）に留まる。C++ テストの大部分は「Python ソースを変換し、コンパイル + 実行して正しい出力が出るか」という言語非依存のロジックであり、全 backend で共有できる。

| 問題 | 影響 |
|------|------|
| 新言語追加時にテストを一から書く必要がある | 開発コスト増 |
| 言語間の機能ギャップが見えない | 品質の非対称性 |
| C++ 固有の問題と transpiler 共通の問題が分離されていない | デバッグ困難 |

## 前提条件

- P0-18（Object\<T\> 移行）および P0-22（REPO_ROOT + import alias）が完了していること
- 各 backend の emit pipeline（compile → link → emit）が統一されていること

## 設計方針

### ディレクトリ構造

```
test/unit/backends/
  common/
    conftest.py            # lang fixture, skip marker, compile+run helper
    test_arithmetic.py     # 算術演算 (int, float, bool)
    test_string_ops.py     # 文字列操作
    test_list_ops.py       # リスト操作
    test_dict_ops.py       # dict 操作
    test_control_flow.py   # if/for/while/match
    test_functions.py      # 関数定義・呼出・再帰・デフォルト引数
    test_classes.py        # クラス・継承・super・dataclass
    test_imports.py        # import/from-import/alias
    test_comprehension.py  # リスト/dict/set 内包表記
    test_exceptions.py     # try/except/raise
    test_typing.py         # 型アノテーション・enum・Any
    ...
  cpp/                     # C++ 固有テスト（namespace, include, rc/Object 等）
  js/                      # JS 固有テスト
  ...
```

### テスト実行の仕組み

```python
# common/conftest.py
import pytest

ALL_LANGS = ["cpp", "js", "cs", "rs", "go", "java", "kotlin", "swift",
             "dart", "scala", "lua", "php", "rb", "nim", "zig",
             "julia", "powershell", "ts"]

@pytest.fixture(params=ALL_LANGS)
def lang(request):
    return request.param

def compile_and_run(lang: str, fixture_path: str) -> str:
    """pytra build → compile → run の共通ヘルパー。
    未サポート機能は pytest.skip() で飛ばす。"""
    ...
```

```python
# common/test_arithmetic.py
def test_int_add(lang, compile_and_run):
    out = compile_and_run(lang, "test/fixtures/arithmetic/int_add.py")
    assert out.strip() == "3"
```

### 言語ごとのスキップ管理

各言語のサポート範囲を宣言的に管理する:

```python
# common/lang_support.py
UNSUPPORTED = {
    "zig":  {"enum", "dataclass", "match", "try_except"},
    "lua":  {"type_annotation", "enum"},
    "php":  {"match"},
    ...
}

def skip_if_unsupported(lang: str, feature: str):
    if feature in UNSUPPORTED.get(lang, set()):
        pytest.skip(f"{lang} does not support {feature}")
```

### fixture の流用

既存の `test/fixtures/` をそのまま使う。各 fixture は `run_case()` または `_case_main()` を持ち、結果を stdout に出力する形式で統一されている。新規 fixture 追加時は全言語で自動的にテスト対象となる。

## 移行計画

### S1: 共通テスト基盤の構築

- `test/unit/backends/common/conftest.py` を作成
- `compile_and_run` ヘルパー: `pytra-cli.py build` 経由で任意言語のビルド + 実行
- `lang_support.py`: 言語ごとの unsupported feature set

### S2: 既存 fixture からの共通テスト抽出

C++ テストから言語非依存のケースを抽出:
- 算術・文字列・リスト・dict 操作（~50 ケース）
- 制御フロー（if/for/while）（~20 ケース）
- 関数・クラス（~30 ケース）
- import（~10 ケース）

### S3: 全 backend での実行と skip 登録

- 全言語で共通テストを実行し、失敗ケースを分類
- 「未サポート機能」→ skip 登録、「バグ」→ 個別 issue 起票

### S4: C++ 固有テストの分離

`test_py2cpp_features.py` から共通化済みのテストを除去し、C++ 固有テスト（namespace、include path、rc/Object、bounds_check_mode 等）のみに絞る。

## 非対象

- 各言語の runtime 実装の追加（既存 runtime で動く範囲のみ）
- パフォーマンステスト
- selfhost テスト（別テストスイート）

## 受け入れ基準

- [ ] `test/unit/backends/common/` に 50 ケース以上の共通テストがある
- [ ] 全 18 言語で共通テストが実行される（skip 含む）
- [ ] 各言語の skip 理由が `lang_support.py` に宣言的に管理されている
- [ ] `test_py2cpp_features.py` から共通化済みテストが除去され、C++ 固有テストのみになっている

## 決定ログ

### 2026-03-22: 起票

- C++ のみ 621 テスト、他言語 7〜48 テストの非対称性をユーザーが指摘
- Object\<T\> 移行完了後に着手する方針で合意
- P2 優先度として起票（P0-18, P0-22 完了後）
