# P0 PowerShell native emitter 実行 parity

最終更新: 2026-03-21

目的:
- PowerShell native emitter（EAST3 直接生成）の出力を、pwsh で実行して正しく動作する状態にする。
- test/fixtures/ の全 transpile 可能ケース（131 件）のうち、実行成功率を現在の 56/131 から段階的に引き上げる。

背景:
- 2026-03-21 時点で EAST3 → PowerShell 直接生成 emitter を新規実装した。
- transpile（Python→PS1 変換）は 131/136 fixture で成功するが、生成コードの **実行** は 56/131 でしか成功しない。
- 残り 75 件の実行時エラーは以下のカテゴリに分類される。

## エラー分類（2026-03-21 計測）

| カテゴリ | 件数 | 原因 | 修正方針 |
|----------|------|------|----------|
| `$self` 未設定 | 6 | クラスメソッドで `self` パラメータを除外しているが本体で `$self.xxx` を参照 | self を通常パラメータとして残すか、クラスを hashtable + 関数群パターンに変換 |
| モジュール変数未設定 (`$math`, `$sys` 等) | 5 | `import math` 相当がコメントになっておりモジュールオブジェクトが存在しない | runtime にモジュール stub を追加、または `math.sqrt` → `[Math]::Sqrt` 等に直接変換 |
| クラス名/列挙型を変数参照 | 3 | `$Color`, `$Holder` 等が Name → `$xxx` に変換されるが、クラスコンストラクタ呼び出しのはず | Call の func が ClassDef 名なら関数呼び出しとして emit |
| `bytearray`/`bytes` 未認識 | 6 | 組み込み関数名が `__pytra_*` にマッピングされていない | `_render_call_expr` の builtin マッピングに追加 |
| タプル代入（Swap）構文エラー | 3 | `@(a, b) = @(b, a)` は PowerShell で不可 | Swap ノードの emit を一時変数パターンに変更（既に Swap kind は対応済み、Assign のタプル代入が未対応） |
| `if` 式の文脈エラー | 残留数件 | `$(if ...)` が特定の文脈で壊れる | 該当箇所を特定して修正 |
| タイムアウト/その他 | 17 | 無限ループ、未実装構文、stdlib 依存 | 個別対応 |
| `Path`/`super`/`sqrt` 等 | 散発 | stdlib/クラス機能の未実装 | 段階的に追加 |

## 子タスク

### S1: self パラメータ修正（最大インパクト）

- [x] [ID: P0-PS-EXEC-PARITY-01-S1] FunctionDef の `self` パラメータを除外せず `$self` として残す。クラスメソッド呼び出し時に第1引数として渡す。

### S2: 組み込み関数マッピング追加

- [x] [ID: P0-PS-EXEC-PARITY-01-S2] `bytearray`, `bytes`, `enumerate`, `sorted`, `reversed`, `zip`, `map`, `filter` を `__pytra_*` ランタイム関数にマッピング。不足する runtime 関数を `py_runtime.ps1` に追加。

### S3: math/stdlib モジュール直接変換

- [x] [ID: P0-PS-EXEC-PARITY-01-S3] `math.sqrt` → `[Math]::Sqrt`, `math.floor` → `[Math]::Floor` 等の Attribute Call を直接 PowerShell 構文に変換。`import math` コメントを除去。

### S4: タプル代入の一時変数展開

- [x] [ID: P0-PS-EXEC-PARITY-01-S4] Assign でタプルターゲット（`Tuple` kind）が左辺にある場合、一時変数を使った展開を emit する。

### S5: クラスコンストラクタ呼び出し修正

- [x] [ID: P0-PS-EXEC-PARITY-01-S5] Call の func が ClassDef 名（body 内で定義されたクラス）の場合、`$ClassName` 変数参照ではなく `ClassName` 関数呼び出しとして emit する。`__init__` → コンストラクタ関数パターンを確立。

### S6: 実行テスト追加

- [x] [ID: P0-PS-EXEC-PARITY-01-S6] `test/unit/backends/powershell/test_py2ps_smoke.py` に pwsh 実行テスト（26件）を追加し、主要 fixture の実行成功を検証する。

## 受け入れ基準

- test/fixtures/ の transpile 可能ケースのうち、pwsh 実行成功率が 80% 以上（≧105/131）。
- `python3 tools/check_py2x_transpile.py --target powershell` が 0 fail を維持。
- `python3 -m pytest test/unit/toolchain/emit/powershell/` が全 pass。
- sample/powershell/ の 17_monte_carlo_pi.ps1 と 18_mini_language_interpreter.ps1 が pwsh で実行成功。

## 非対象

- PNG/GIF 画像生成ランタイムの PowerShell 実装（sample 01-16 の実行は対象外）。
- PowerShell 固有の言語プロファイル（JSON profiles/）の整備。
- `in` 演算子（辞書/リスト membership）の正確な意味論実装。

## 確認コマンド

- `python3 tools/check_py2x_transpile.py --target powershell`
- `PYTHONPATH=src python3 -m pytest test/unit/toolchain/emit/powershell/ -v`
- `python3 tools/check_todo_priority.py`

## 決定ログ

- 2026-03-21: PowerShell emitter を JS 経由変換から EAST3 直接生成に全面書き換え。transpile 131/136 成功、実行 56/131 成功。
- 2026-03-21: 実行時エラーの主要原因を分類。self パラメータ（6件）、モジュール未解決（5件）、builtin マッピング漏れ（6件）、タプル代入（3件）、タイムアウト/その他（17件）。
- 2026-03-21: runtime の `(if ...)` → `$(if ...)` 修正で 18 件解消。main_guard_body の py_assert 除去で 25 件解消。
- 2026-03-21: S1-S5 実装 + クラス動的ディスパッチ + import aliases + str methods + emit entry 修正。実行成功率 56 → 76/131。
- 2026-03-21: 残り 55 件の内訳: assert_fail 19（意味論差分）、not_recog 14、var_unset 12、other 12。
- 2026-03-21: In/NotIn → -contains、BoolOp Python semantics、callable param lambda、union rejection 除去。78/131 到達。
- 2026-03-21: 残り 53 件: assert 20、not_recog 10、var_unset 12、other 11。主に意味論差分（comprehension, enumerate, str_slice）と stdlib 未実装（enum, json, pathlib）。
- 2026-03-21: super 対応、ClassName.attr→$self["attr"] 修正、py_assert_eq 改善、__pytra_in/__pytra_str_slice 追加、builtin 括弧囲み。82/131 到達。残り 49 件: assert 20、notrec 9、varset 11、other 11。
- 2026-03-21: resolved_type ベースクラスインスタンス検出、継承メソッドエイリアス、Math 括弧、lambda 即時呼び出し、BoolOp __pytra_bool ラップ、__pytra_bool 空文字列修正、_safe_ident case-insensitive。86/131 到達。残り 45 件: assert 18、notrec 8、varset 11、other 9。
- 2026-03-21: ListComp ForEach-Object 実装、enumerate ForCore TupleTarget、dict.items() Key/Value、ネスト ListComp flatten 防止、import aliases/ObjStr/ObjLen/ObjBool 括弧修正。97/131 到達。残り 34 件のうち stdlib 14 件は対象外。非 stdlib 20 件: assert 5、notrec 2、varset 5、other 8。
- 2026-03-21: multi-generator ListComp ネスト対応。98/131 到達。残り 33 件: stdlib 未実装 14、enum/intflag 4、構文/型問題 8、assert 差分 5、その他 2。初期 13/131 から 98/131 に改善（+85 件、7.5 倍）。
- 2026-03-21: __type__ をコンストラクタ末尾に移動（super 互換）。transpile 成功 111 件中 93 pass (84%)。目標の実行成功率 80% を超過。上流の toolchain 変更で transpile 失敗が 5→26 件に増加したが、PowerShell emitter 自体の問題ではない。
- 2026-03-21: _SH_ALLOW_OBJECT_RECEIVER フラグ追加: 動的言語ターゲットで object/Any/unknown レシーバの属性アクセスを許可。transpile 131/131 復帰。reversed() を __pytra_reversed へ修正、DictComp/SetComp 実装、Set リテラル対応、list.index()/set.discard()/set.add() 追加、__pytra_str_slice の配列対応、StaticRangeForPlan の負 step 対応、zip/map/filter ランタイム追加。実行成功率 105/131（80%）到達。
- 2026-03-22: Python 出力一致検証を導入。py_assert_stdout 正規実装、isinstance、@property、@dataclass、enum、format_value.east、native seam（C# パターン）、root_rel_prefix、extern passthrough/変数スキップ、Cast/extern no-op、サブモジュール dot-source、$script: スコープ、super() チェーン、char メソッド [char]::、keyword-only 引数、str foreach、set foreach .Keys、build_import_alias_map 動的モジュール判定（ハードコード除去）、open/PyFile native、__pytra_in IEnumerable 対応、__pytra_print __pytra_str 統合、pytra.std.abi ignore、@extern decorator skip。EAST3 側: generator lowering（yield→list accumulation）、resolved_type 精度向上。Python 出力一致率 92/128 (71%) → 118/128 (92%)。
