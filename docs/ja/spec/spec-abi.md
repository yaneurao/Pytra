# Pytra トランスパイラ仕様: `@extern` 関数と固定 ABI 型（C++ バックエンド）

## 1. 目的

Pytra は Python から C++ 等へ変換するトランスパイラであり、C++ backend 内部では `rc<T>` などの所有権表現を使ってオブジェクト寿命を管理する。

一方、変換時の最適化により、同じ Python 型が複数の C++ 内部表現を取りうる。例:

- `rc<list<rc<bytearray>>>` -> `list<rc<bytearray>>`
- `list<rc<bytearray>>` -> `list<bytearray>`

この揺れは、外部実装（C++ 側で定義する関数）に委譲する `@extern` 関数の呼び出し時に問題となる。`@extern` 関数は「呼び出し点における内部表現」に依存せず、常に同一の境界型で呼べる必要がある。

本仕様は、`@extern` 関数に **固定 ABI 型** を与え、呼び出し点で必要に応じて **ABI 変換（アダプト）** を挿入することで、この問題を解決する。

重要:

- `rc<T>` は C++ backend の内部所有権表現であり、ABI そのものではない。
- `str`, `bytes`, `bytearray`, `list[T]`, `dict[K,V]`, `set[T]`, `tuple[...]` のような **値型 / コンテナ型 ABI には `rc<>` を露出させない**。
- `rc<>` を ABI に使ってよいのは、user class など **参照意味論が本質の型** に限る。
- backend 内部最適化の都合で `rc<list<T>>` などの typed handle を使ってよいが、これは **内部型** であり ABI 型ではない。
- 特に `cpp_list_model=pyobj` の alias 維持で `rc<list<T>>` を使う場合でも、`@extern` 境界では `list<T>` に正規化して渡す。

本仕様において `@extern` は **デコレータ引数なし** のみをサポートする。

## 2. 用語

- **内部型 (Internal Type)**  
  最適化・変換過程で用いられる C++ 側の実際の表現型。縮退により複数パターンがありうる。
  例: `list<bytearray>`, `rc<list<bytearray>>`, `object`

- **ABI 型 (ABI Type)**  
  `@extern` 関数呼び出しの境界で用いる固定の C++ 型。外部実装（ランタイム / ターゲット言語側）で定義される関数シグネチャと一致する。

- **ABI 変換 (ABI Adaptation)**  
  呼び出し点の内部型から ABI 型へ変換する処理。必要なときのみ挿入される。恒等変換（no-op）も含む。

- **値型 ABI (Value ABI)**  
  `rc<>` を含まない境界型。`str`, `bytes`, `bytearray`, `list[T]`, `dict[K,V]`, `set[T]`, `tuple[...]` など。

- **参照型 ABI (Reference ABI)**  
  user class や `object` のように identity / dynamic dispatch を保持する境界型。

## 3. `@extern` の基本仕様

### 3.1 記法

Python ソース上では以下のみを許可する。

```python
@extern
def write_png(image: list[bytearray]) -> None: ...
```

```python
from pytra.std import extern

@extern
def write_png(image: list[bytearray]) -> None: ...
```

`extern` は単なるマーカーで、Python 実行時には no-op として振る舞う。

```python
def extern(fn):
    return fn
```

- `@extern(...)` のような引数付きデコレータはサポートしない。
- 変数に対する extern マーカーは `name = extern(expr)` 形式で表す。

### 3.2 意味

`@extern` が付与された関数は、ターゲット言語（ここでは C++）側で提供される関数へ委譲される。

Pytra は `@extern` 関数に対し、次を決定する。

- 外部名（シンボル名）
- ABI 型

呼び出し点では、実引数が内部型で表現されていても、ABI 型へ変換して外部関数を呼ぶ。

Python 実行時互換のため、`@extern` 関数は Python で実行可能な本体（例: `return __m.sin(x)`) を持ってよい。  
トランスパイラは `@extern` 関数の本体をターゲット実装としては採用せず、外部シンボル呼び出しへ lower する。

### 3.3 host-only import (`as __name`) 規約

`import ... as __m` のように alias が `__` で始まる import は host-only import として扱う。

- host-only import は Python 実行時の補助（`@extern` 関数の Python 本体評価）にのみ使う。
- ターゲット言語コードにはこの import を出力しない。
- host-only import の参照は、`@extern` 関数本体または `extern(expr)` 初期化式の中でのみ許可する。
- それ以外の箇所で `__m` 参照が出現した場合はコンパイルエラーとする。
- `_name`（先頭 `_` 1 個）は host-only とみなさない。通常 import として扱う。

## 4. 外部名（シンボル名）の決定規約

`@extern` 関数 `M.f` に対し、外部名は以下で決定する。

外部名:

```text
pytra_<module>_<function>
```

- `<module>` は Python モジュール名（例: `pytra.std.math`, `pytra.utils.png`）
- `<function>` は関数名

例:

- `pytra.std.math.sin` -> `pytra_std_math_sin`
- `pytra.utils.png.write_png` -> `pytra_utils_png_write_png`

注意:

- モジュール名の決定はパッケージ名に基づき一意に決める。
- ネスト関数・ローカル関数は対象外。
- `@extern` はトップレベル関数のみ許可してよい。

## 5. ABI 型の決定規約

### 5.1 基本方針

ABI 型は Python 型注釈から決定される固定の C++ 型であり、内部の最適化で揺れない。

ABI 型は「境界の正規形」として扱う。

必須ルール:

- ABI は **backend 内部所有権表現を露出しない**。
- 値型 / コンテナ型 ABI では `rc<>` を使わない。
- `rc<>` を ABI に使うのは、user class など identity を保持すべき参照型に限定する。
- `rc<list<T>>` はあくまで backend 内部の alias 維持・最適化用表現であり、ABI 正規形には含めない。

### 5.1.1 backend 内部表現の既定方針

ABI の正規形と、backend 内部で最初に採用する表現は分けて考える。

必須ルール:

- `str` のような immutable 型は、backend 内部でも値型を既定としてよい。
- `list`, `dict`, `set`, `bytearray` などの mutable 型、および mutable な user class は、backend 内部では **参照共有を保持する表現** を既定とする。
- C++ backend では、その参照共有表現として `rc<>` や同等の handle を使ってよい。
- ただし、その `rc<>` はあくまで内部表現であり、ABI へ露出してはならない。

値型への縮退は、最適化結果としてのみ許可する。

- `a = b` の alias 共有が観測されうる mutable 値を、証明なしに値型へ落としてはならない。
- 値型への縮退は、少なくとも mutation / alias / escape の各解析で安全が証明できた場合に限る。
- 関数をまたぐ縮退は、call graph を構築し、再帰・相互再帰を含む SCC 単位で summary を固定してから行う。
- `Any/object` 境界、`@extern` 境界、未知関数呼び出し、型不明経路が混ざる場合は fail-closed とし、参照共有表現のまま保持する。

要するに、ABI は `list<T>` のような値型正規形で固定しつつ、backend 内部では mutable 型を ref-first に扱い、安全が証明できた経路だけ後から値型へ縮退する。

### 5.2 値型 ABI の正規形

本仕様での推奨正規形:

```text
bool -> bool

int -> int64
※ Pytra では Python の int は int64（符号付き 64bit 整数）として扱う。

float -> float64

str -> str

bytes -> bytes

bytearray -> bytearray

list[T] -> list<ABI(T)>

dict[K,V] -> dict<ABI(K), ABI(V)>

set[T] -> set<ABI(T)>

tuple[T1, T2, ...] -> std::tuple<ABI(T1), ABI(T2), ...>

None（戻り値） -> void
```

ここで `ABI(T)` は要素型の ABI 正規形を表す。

重要:

- `list[str]` の ABI は `list<str>` であり、`list<rc<str>>` ではない。
- `list[bytearray]` の ABI は `list<bytearray>` であり、`rc<list<rc<bytearray>>>` ではない。
- `dict[str, int]` の ABI は `dict<str, int64>` である。
- `list[int]` の内部表現が `rc<list<int64>>` に縮退していても、ABI は `list<int64>` のままである。

### 5.3 参照型 ABI の正規形

以下のような型は、値型ではなく参照型 ABI として扱ってよい。

```text
Any / object -> object

user class C -> rc<C>

identity が必要な runtime object -> 現行 runtime 参照型
```

例:

- `Animal` -> `rc<Animal>`
- `Token` -> `rc<Token>`
- `object` / `Any` -> `object`

つまり、`rc<>` を完全禁止するのではなく、**値型 ABI では使わない**、というのが本仕様の意味である。

### 5.4 C++ での引数受け渡し形

ABI 型そのものと、C++ の関数宣言でどう受けるかは分けて考える。

例:

- ABI 型: `list<bytearray>`
- C++ 宣言形（推奨例）:
  - `const list<bytearray>& image`
  - `list<bytearray> image`
  - `list<bytearray>& image`

どの宣言形を使うかは、mutation / copy cost / backend 方針に依存する。  
ただし、**要素型の正規形 (`list<bytearray>` であること) は変えてはならない**。

## 6. ABI 変換（アダプト）の仕様

### 6.1 変換の挿入点

`@extern` 関数呼び出しを外部名へ lowering する段階（例: `CppLower`）で、各引数について以下を行う。

1. 実引数の内部型 `Tin` を得る（最適化結果の型）
2. 対応する ABI 型 `Tabi` を得る（固定規約により決定）
3. `Tin` と `Tabi` が一致すればそのまま渡す
4. 一致しなければ `adapt(Tin -> Tabi)` を挿入し、その結果を渡す

### 6.2 変換関数の形

ABI 変換は、生成コード上で例えば次のように表現する。

```cpp
adapt_to_abi<list<bytearray>>(x)
```

関数名は backend 実装依存でよいが、役割は次に限定する。

- 内部型 -> 固定 ABI 型 への正規化
- no-op のときは余計な変換を挿入しない

### 6.3 必須の変換ケース（例: `list[bytearray]`）

`Tabi = list<bytearray>` に対し、少なくとも以下を扱えること。

#### Case 1: `Tin = list<bytearray>`

-> no-op

#### Case 2: `Tin = list<rc<bytearray>>`

-> 各要素を `bytearray` へ正規化し、`list<bytearray>` を構築する

#### Case 3: `Tin = rc<list<bytearray>>`

-> 外側の `rc<>` を外し、`list<bytearray>` を構築する

#### Case 4: `Tin = rc<list<rc<bytearray>>>`

-> 外側の `rc<>` を外し、各要素も `bytearray` へ正規化して `list<bytearray>` を構築する

上記以外の型が来た場合はコンパイルエラーとしてよい。

### 6.4 変換コストに関する方針

ABI 変換はコピーや再構築を伴う可能性があるが、以下の原則で許容する。

- 外部境界で ABI を固定することを優先する
- 変換は「必要なときのみ」挿入する（型一致なら no-op）
- I/O 的な `write_png` のような関数は、境界コピーが支配的になりにくい
- もし性能上問題が出た場合は、個別に専用 ABI（例: span / pointer + size / writable buffer）を設計する

## 7. 生成される C++ 宣言とリンク

### 7.1 宣言の提供方法

外部関数の宣言は、次のいずれかで提供される。

- 方式1: トランスパイラが使用された外部関数だけ forward 宣言を自動生成する
- 方式2: 共通ヘッダを常に include し、そこに宣言を置く

いずれも許可するが、初期は方式1を推奨する。

### 7.2 `extern "C"` について

本仕様の「ABI」は **Pytra の固定境界型** を意味し、plain C ABI を意味しない。

したがって:

- `extern "C"` は名前修飾抑止のために使ってよい
- ただし `list<bytearray>` や `dict<str, int64>` のような C++ 型を含む場合、それは C から直接呼べることを意味しない

`extern "C"` は任意だが、シンボル名安定化のため採用してよい。

## 8. 仕様上の制約

- `@extern` 関数は Python 側ではスタブ（`...` / `pass`）でもよいし、Python 実行可能な本体を持ってもよい。
- ただしターゲット言語への lower では、関数本体は外部実装に置き換わる。
- `@extern` 関数は型注釈（引数・戻り値）を必須とすることを推奨する。
- `@extern` の対象はトップレベル関数のみに制限してよい。
- `import ... as __name`（host-only import）の利用箇所制約は必須とする。

## 9. 例（`write_png`）

Python:

```python
from pytra import extern

@extern
def write_png(image: list[bytearray]) -> None: ...
```

ABI 型（規約）:

- `image: list<bytearray>`
- 戻り値: `void`

生成（概念）:

```cpp
// forward decl の例
extern "C" void pytra_utils_png_write_png(const list<bytearray>& image);

void callsite(...) {
    // image_in は最適化により型が揺れる（例: rc<list<rc<bytearray>>> など）
    auto image_abi = adapt_to_abi<list<bytearray>>(image_in);
    pytra_utils_png_write_png(image_abi);
}
```

外部実装（C++ 側）:

```cpp
extern "C" void pytra_utils_png_write_png(const list<bytearray>& image) {
    // PNG 書き出し処理
}
```

## 10. 実装チェックリスト

- `@extern` 付与関数を AST / EAST から検出できる
- Python 型注釈から ABI 型を一意に決められる
- 外部名 `pytra_<module>_<func>` を一意に決められる
- 呼び出し点で `(Tin, Tabi)` を比較し、必要なら `adapt` を挿入できる
- `list[bytearray]` など代表例で、縮退後の複数内部型を ABI に正規化できる
- 外部関数宣言（forward decl または runtime header）を生成できる

## 11. runtime ディレクトリ構成（本仕様での前提）

runtime の正規配置は `docs/ja/spec/spec-runtime.md` に従う。

本仕様で前提とする要点だけ抜粋すると、現行 C++ runtime は次の 4 区分で構成する。

- `runtime/cpp/core/`
- `runtime/cpp/generated/{built_in,std,utils}/`
- `runtime/cpp/native/{built_in,std,utils}/`
- `runtime/cpp/pytra/{built_in,std,utils}/`

ownership 規則:

- SoT から生成される宣言 / thin wrapper は `generated/`
- OS / SDK / C++ 標準ライブラリへ接着する最小 native 実装は `native/`
- 生成コードが include する public header は `pytra/`
- `core/` は低レベル runtime の stable include surface であり、当面 `.ext.*` naming を使う

補足:

- C++ module runtime の ownership は suffix ではなく directory で判別する。
- `src/runtime/cpp/{built_in,std,utils}` の suffix ベース module runtime は legacy-closed であり、再導入しない。
- `core` についても承認済み次段では `runtime/cpp/generated/core/` と `runtime/cpp/native/core/` に ownership を分離し、`runtime/cpp/core/` は互換 include 面へ縮退する。
- `pytra/core` は導入しない。`pytra/` は module runtime の generated public shim に限定する。
- ABI の考え方自体は変わらない。
- 詳細は `docs/ja/spec/spec-runtime.md`、`docs/ja/plans/archive/20260307-p0-cpp-runtime-layout-generated-native.md`、`docs/ja/plans/p0-cpp-core-ownership-split.md` に従う。

## 12. `pytra.std.math` の例

`src/pytra/std/math.py` は `@extern` を含むため、C++ runtime では次のように構成する。

- 生成宣言:
  - `runtime/cpp/generated/std/math.h`
- native 実体:
  - `runtime/cpp/native/std/math.cpp`
- public shim:
  - `runtime/cpp/pytra/std/math.h`

重要:

- `math` は header-only 生成なので、`runtime/cpp/generated/std/math.cpp` は生成しない
- `math.cpp` が `math.h` に対する native 実体を提供する
- 生成コードは `runtime/cpp/pytra/std/math.h` を include し、build graph が `generated/native` を解決する
- manifest / build 入力は `spec-runtime.md` の配置規約に従う

つまり、`@extern` を含むモジュールであっても、

- ABI 型は値型正規形で固定し
- 生成物と native 実体は ownership が見える形で分離し
- `rc<>` は ABI ではなく内部表現に閉じ込める

というのが本仕様の要点である。
