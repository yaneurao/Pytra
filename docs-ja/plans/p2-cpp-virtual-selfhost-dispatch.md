# P2: C++ selfhost virtual ディスパッチ簡略化

## 背景

`virtual`/`override` の扱いを現在のクラスモデルへ寄せたため、`cpp` selfhost 生成コードの一部で使われていた手作り分岐（`type_id` 判定 + switch 相当）を簡素化できる余地があります。
このままでも動作は維持できますが、簡略化すれば selfhost 出力の可読性・保守性・デバッグ性が向上します。

## 受け入れ基準

- selfhost 生成 C++ 側（`sample/` 系の再変換含む）で、同一メソッド呼び出しを `virtual` 経由へ置換して、`type_id` 分岐が不要な箇所を減らせること。
- `py2cpp.py` と `CppEmitter` が、`override` が付与される基底メソッドと同名呼び出しを前提に最小限の分岐で生成できること。
- `tools/check_selfhost_cpp_diff.py` / `tools/verify_selfhost_end_to_end.py` で回帰が発生しないこと。

## 子タスク

1. `P2-CPP-SELFHOST-VIRTUAL-01-S1`: selfhost 生成物（`sample`/`selfhost`）の class method 呼び出しを調査し、`type_id` 分岐で行われている箇所を洗い出す。
2. `P2-CPP-SELFHOST-VIRTUAL-01-S2`: `py2cpp.py` の emit 経路で、対象呼び出しを `virtual/override` 利用の既定経路へ寄せる。
3. `P2-CPP-SELFHOST-VIRTUAL-01-S3`: 既存の `type_id` 分岐と置換後の差分を比較し、回帰を `test/unit` + `sample` 再生成で固定化する。
4. `P2-CPP-SELFHOST-VIRTUAL-01-S4`: 成果を `docs-ja/spec/spec-dev.md`（必要なら追記）へ簡潔に反映する。

## 決定ログ

- [2026-02-25] `virtual` が override 済み基底メソッドのみ付与される方向へ変更済み。上記タスクの起点として `selfhost` 側の簡略化余地を低優先で追加。
