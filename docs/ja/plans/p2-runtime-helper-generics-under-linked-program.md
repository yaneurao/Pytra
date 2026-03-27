<a href="../../en/plans/p2-runtime-helper-generics-under-linked-program.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2案: linked runtime 向け helper generics 導入

最終更新: 2026-03-08

関連:
- [p2-runtime-sot-linked-program-integration.md](./p2-runtime-sot-linked-program-integration.md)
- [p1-runtime-abi-decorator-for-generated-helpers.md](./p1-runtime-abi-decorator-for-generated-helpers.md)
- [p1-cpp-py-runtime-core-slimming.md](./p1-cpp-py-runtime-core-slimming.md)
- [../spec/spec-template.md](../spec/spec-template.md)

注記:

- この文書は未スケジュールの構想メモであり、現時点では `docs/ja/todo/index.md` へは積まない。
- 目的は「linked runtime 統合後に generic helper をどう扱うか」の文脈を固定することである。
- 直ちに実装する前提ではない。

背景:
- runtime SoT を事前生成 artifact として扱う間は、helper 境界に fixed ABI を与える `@abi` が実務上必要になる。
- しかし runtime SoT を linked program へ ordinary module として統合できるなら、helper は user code と同じ optimizer の対象にできる。
- その状態では `str.join`, `dict.keys`, `take`, `map` 相当の helper を pure Python で generic に書けると、`object` 退化や target 固有 hand-written helper を減らしやすい。
- 現行 spec では `typing.TypeVar` は注釈専用であり、generic/template 機能は未提供である。[spec-template.md](../spec/spec-template.md)
- そのため、この案は「言語全体の template 実装」ではなく、「linked runtime helper 限定の関数 generic」を最小スコープで入れる構想として扱うべきである。

目的:
- linked runtime helper を pure Python で書きやすくし、`list[T]`, `dict[K, V]`, `tuple[T, U]` などを generic helper として表現できるようにする。
- runtime helper を ordinary module として linked-program optimizer に載せたまま、具体的な使用型に応じて monomorphization / specialization できるようにする。
- `@abi` の必要範囲をさらに減らし、helper ごとの手書き value/ref adapter を減らす。
- `py_runtime` へ残っている collection/string helper を SoT 側へ戻しやすくする。

対象:
- runtime/internal helper module の generic 関数構文
- linked-program 段での generic helper 実体化
- C++ backend における specialized helper 出力
- runtime helper 限定の type parameter 解析
- docs/spec の責務境界

非対象:
- user program 全般への generic/template 一般公開
- class generic / protocol / higher-kinded type
- generic method / nested generic function
- compile-time branch 機能全般
- 全 backend 同時対応
- 既存 `spec-template` 草案の全面実装

受け入れ基準（将来着手時の目安）:
- linked runtime helper で rank-1 generic function を書ける。
- runtime helper の利用箇所から具体型が集まり、linked-program 段で deterministic に実体化できる。
- C++ backend では、specialized helper が `object` 退化なしに出力される。
- `list[T]` / `dict[K, V]` / `tuple[T, U]` を扱う representative helper が pure Python SoT で表現できる。
- `@abi` は generic helper 一般には必須ではなくなり、external/public/prebuilt 境界に限定される。

## 1. 問題の本質

runtime helper を linked program に統合しても、generic が無いと次の問題が残る。

- `list[T]` を扱う helper を `object` ベースで書くと型精度が落ちる
- `list[str]`, `list[int]`, `list[Token]` ごとに別 helper を手で書くと SoT が冗長になる
- collection helper を `native/core` に残したくなる

つまり、runtime helper を pure Python SoT へ戻すには

- linked runtime integration
- helper-limited generics

の 2 つが噛み合う必要がある。

## 2. 目標スコープ

本案で狙うのは「小さい generic」である。

### 2.1 許可するもの

- top-level function generic
- rank-1 type parameter
- `T`, `K`, `V`, `U` のような単純 type parameter
- `list[T]`, `dict[K, V]`, `set[T]`, `tuple[T, U]`
- linked-program 段での monomorphization

### 2.2 最初は許可しないもの

- generic class
- constrained TypeVar
- variance
- protocol / trait bound
- generic recursion の高度な推論
- backend ごとの native template 直接出力

## 3. どういう helper に効くか

代表例:

```python
def py_head[T](xs: list[T]) -> T:
    return xs[0]
```

```python
def py_take[T](xs: list[T], n: int) -> list[T]:
    out: list[T] = []
    i = 0
    while i < n and i < len(xs):
        out.append(xs[i])
        i += 1
    return out
```

```python
def py_dict_keys[K, V](d: dict[K, V]) -> list[K]:
    out: list[K] = []
    for k in d:
        out.append(k)
    return out
```

これらは、linked-program 段で具体型ごとに実体化できれば、C++ ではかなり素直な specialized helper になる。

## 4. `@abi` との関係

この案は `@abi` を否定するものではないが、位置づけを変える。

### 4.1 generic helper では不要になりやすい

- helper が ordinary call になる
- 具体型は linked-program 段で見える
- `rc<>` / value model は helper 境界ではなく whole-program optimization で決められる

このため、generic helper 一般に固定 ABI を先に与える必要が薄くなる。

### 4.2 それでも残る用途

- prebuilt runtime artifact
- external/native helper
- public helper API を固定したい場合

要するに、`@abi` は generic helper の正本手段ではなく、境界固定が必要な場合の escape hatch に縮退するのが自然である。

## 5. どこで実体化するか

最重要点はここで、実体化は `emit-runtime-*` の前ではなく linked-program 段で行うべきである。

理由:

- user code 側で実際に使われる具体型が見える
- runtime helper と user module を同じ call graph で見られる
- 未使用 specialization を出さずに済む
- C++ の ref-first / value-lowering も specialization 後に判断できる

したがって pipeline は概念的にこうなる。

```text
runtime helper generic definition
user module call sites
  -> LinkedProgramLoader
  -> generic helper specialization collector
  -> helper monomorphization
  -> global optimizer
  -> backend lower / emit
```

## 6. syntax の候補

長期的には `spec-template` と整合させる必要があるが、runtime helper 限定の最小案としては次のどちらかがよい。

### 6.1 `@template("T")` 系（canonical）

```python
@template("T")
def py_head(xs: list[T]) -> T:
    return xs[0]
```

利点:

- `spec-template` 草案と整合しやすい
- 将来 user-facing template と合流しやすい

欠点:

- 今の runtime helper には少し重い

### 6.2 `TypeVar` 注釈だけを限定採用（不採用）

```python
T = TypeVar("T")

def py_head(xs: list[T]) -> T:
    return xs[0]
```

利点:

- Python 的に自然
- runtime helper には書きやすい

欠点:

- 現行 spec では `TypeVar` は注釈専用で template 機能未提供
- user-facing generic と runtime-only generic の線引きが曖昧になりやすい

2026-03-08 時点では、この案は採らない。  
理由は、runtime helper v1 で必要なのは「関数単位の型パラメータ宣言」を surface 上で明示することであり、`TypeVar` だけでは declaration site が曖昧になるためである。したがって linked runtime helper generics の canonical syntax は `@template("T", ...)` とする。future explicit instantiation を入れる場合も、同じ decorator family に `@instantiate(...)` を足す方向で拡張する。

## 7. linked-program で必要な仕組み

### 7.1 specialization collector

- helper generic definition を見つける
- callsite ごとの concrete type tuple を集める
- deterministic order で specialization list を作る
- collector の入口は raw decorator ではなく `FunctionDef.meta.template_v1` とし、linked runtime helper v1 plan で固定した `schema_version/params/scope/instantiation_mode` を正本にする

### 7.2 monomorphization rule

- `py_head[T]` + `list[str]` -> `py_head__str`
- `py_dict_keys[K, V]` + `dict[str, int]` -> `py_dict_keys__str__int64`

命名は user-visible である必要はないが、deterministic で diff-friendly であるべき。

### 7.3 optimization integration

- specialization 後の helper body を global optimizer の入力に含める
- helper specialization も type_id / call graph / non-escape / ownership の対象にする

## 8. C++ に対する効果

### 8.1 良い点

- `object` 退化を減らせる
- `list<T>` / `dict<K, V>` helper を pure Python SoT へ戻しやすい
- `py_runtime` の collection helper を減らしやすい
- specialized helper に対して list ref-first optimization を適用できる

### 8.2 注意点

- specialization 後も mutable container の internal model は ref-first を維持すべき
- `list[T]` helper があるからといって即 value helper にしてはいけない
- C++ だけを見て template 直接出力へ寄せるのは早すぎる

## 9. 段階導入するなら

### Phase 1: design only

- runtime helper 限定 generic の syntax 候補を固める
- `TypeVar` 記法と `@template` 記法のどちらで始めるか決める
- linked-program integration 側との責務境界を明文化する

### Phase 2: helper-only monomorphization

- runtime helper module だけを対象に collector + monomorphization を導入する
- C++ backend だけで smoke する

### Phase 3: optimizer integration

- specialization helper も global optimizer の ordinary node にする
- representative helper で `object` 退化しないことを固定する

### Phase 4: generic runtime helper expansion

- `list`, `dict`, `tuple` helper を SoT 側へ戻す
- `@abi` が不要になった helper を洗い出す

## 10. 前提条件

この案は、少なくとも次が先に必要である。

1. `P0-LINKED-PROGRAM-OPT-01`
2. runtime SoT linked-program integration の土台
3. `P1-RUNTIME-ABI-DECORATOR-01`
   - 移行期の boundary tool

つまり、これは `@abi` の代替を今すぐ入れる話ではなく、より本命の後段構想である。

## 決定ログ

- 2026-03-07: runtime helper を linked program に統合できるなら、generic を入れることで collection/string helper を pure Python SoT でかなり自然に書けると判断した。
- 2026-03-07: ただし現行 spec では `TypeVar` は注釈専用で template 機能未提供のため、この案は「runtime helper 限定の小さい generic」から始めるべきだと整理した。
- 2026-03-07: 実体化は事前生成ではなく linked-program 段で行うべきだと記録した。これにより helper specialization も ordinary module/function として global optimizer の対象にできる。
