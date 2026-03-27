<a href="../../en/plans/p2-pyobj-semantics-pure-python-sot.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2案: `PyObj` semantics を pure Python SoT へ戻す

最終更新: 2026-03-14

関連 TODO:
- なし（backlog draft / TODO 未登録）

関連:
- [p2-runtime-sot-linked-program-integration.md](./p2-runtime-sot-linked-program-integration.md)
- [p2-runtime-helper-generics-under-linked-program.md](./p2-runtime-helper-generics-under-linked-program.md)
- [p2-cpp-pyruntime-upstream-fallback-shrink.md](./p2-cpp-pyruntime-upstream-fallback-shrink.md)

注記:

- この文書は未スケジュールの構想メモであり、現時点では `docs/ja/todo/index.md` へは積まない。
- 目的は、`PyObj` とその派生 class を pure Python SoT に寄せたい場合の障害と現実的な分割案を先に固定することである。
- 「`PyObj` class 階層をそのまま pure Python class で再現する」ことを今すぐ前提にしない。

背景:
- 現在の C++ runtime では `PyObj` 基底は [gc.h](../../src/runtime/cpp/native/core/gc.h) にあり、`RcObject` / `RcHandle<T>` / virtual dispatch / type_id を含む native ABI core として実装されている。
- `PyIntObj`, `PyFloatObj`, `PyBoolObj`, `PyStrObj`, `PyListObj`, `PyDictObj`, `PySetObj`, iterator 群は [py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h) に handwritten class として置かれている。
- 一方で runtime の長期方針は pure Python SoT を拡大したいが、[generated/core/README.md](../../src/runtime/cpp/generated/core/README.md) では `gc`, object/container 表現, RC/GC, 例外/I/O 集約など C++ 固有の ownership/ABI glue を `generated/core` へ流し込むことを禁止している。
- そのため、`PyObj` 周辺を pure Python 化したいとしても、葉の意味論と native ABI core を切り分けない限り破綻する。

目的:
- `PyObj` 周辺について、何が pure Python SoT に戻せて、何が native ABI core に残るべきかを整理する。
- class 階層全体の移植ではなく、まず `truthy`, `len`, `str`, iterator semantics などの「意味論」を SoT 化する段階案を定義する。
- linked runtime integration / helper-limited generics が揃ったときに、どこまで `PyListObj` / `PyDictObj` 系を SoT に寄せられるかの前提を明文化する。

対象:
- `src/runtime/cpp/native/core/gc.h`
- `src/runtime/cpp/native/core/py_types.h`
- `src/runtime/cpp/native/core/py_runtime.h` 内の `Py*Obj` class と iterator class
- `generated/core` / linked runtime / helper generics の責務境界

非対象:
- 今すぐ実装すること
- `RcHandle<T>` / `RcObject` / `PyObj` の pure Python class 化
- generic class や class template の user-facing 実装
- Rust/C#/他 backend まで同時に一括適用すること

受け入れ基準（将来着手時の目安）:
- native ABI core と pure Python SoT へ戻せる意味論が明確に分離されている。
- `PyIntObj` / `PyFloatObj` / `PyBoolObj` / `PyStrObj` のような leaf semantics は、class 直書きではなく generated helper へ委譲できる構造が定義されている。
- `PyListObj` / `PyDictObj` / iterator 群については、何が blocker で何が linked runtime/generics 待ちかが明示されている。
- `generated/core` を肥大化逃がし bucket にせず、SoT 化対象と native 残留対象の境界が壊れない。

## 1. 結論

2026-03-14 時点の現実的な案は、`PyObj` class 階層を pure Python class として丸ごと再生成することではない。  
まずは次の二分割が妥当である。

- native に残す:
  - `RcObject`
  - `RcHandle<T>`
  - `PyObj`
  - type_id registry / subtype check / low-level ownership
- pure Python SoT に戻す候補:
  - `PyIntObj` / `PyFloatObj` / `PyBoolObj` / `PyStrObj` の truthy/str/len/iter semantics
  - 将来的な container helper / iterator helper の一部

要するに、「class を SoT に戻す」のではなく、「class の意味論を SoT に戻し、native class は thin shell にする」のが第一段階である。

## 2. どこが障害か

### 2.1 native ABI core

`PyObj` 基底は単なる Python object model ではなく、参照カウントと virtual dispatch を持つ C++ ABI core である。

- `RcObject` は atomic refcount を持つ
- `RcHandle<T>` は copy/move/adopt/upcast を持つ
- `PyObj` は virtual `py_truthy`, `py_try_len`, `py_iter_or_raise`, `py_next_or_stop`, `py_str` を持つ

この層は [gc.h](../../src/runtime/cpp/native/core/gc.h) の責務であり、pure Python SoT にそのまま移す対象ではない。

### 2.2 template / generic 依存

`object = rc<PyObj>`, `rc<list<T>>`, `dict<K, V>`, `set<T>` のように runtime の基本表現が template 前提である。  
現行の linked runtime generic 構想でも、最初に狙うのは helper-limited generic function であり、generic class ではない。[p2-runtime-helper-generics-under-linked-program.md](./p2-runtime-helper-generics-under-linked-program.md)

したがって、`class PyListObj[T]` のような class generic を pure Python SoT へ直接持ち込むのは時期尚早である。

### 2.3 RTTI / C++ 専用機構

`PyListIterObj` などは `dynamic_cast`, function-local static, macro (`PYTRA_DECLARE_CLASS_TYPE`) のような C++ 専用機構に依存する。  
これらは単純な Python AST から自動変換するには不向きで、native companion として扱う方が自然である。

### 2.4 `generated/core` の境界

[generated/core/README.md](../../src/runtime/cpp/generated/core/README.md) は、`gc`, object/container 表現, RC/GC, 例外/I/O 集約などを `generated/core` に置いてはいけないと明示している。  
したがって「`PyObj` class 階層を pure Python SoT にしたいから generated/core に全部出す」はルール違反になりやすい。

### 2.5 linked runtime integration 未整備

runtime SoT はまだ主に事前生成 artifact として扱われている。  
本命は runtime SoT を linked program に ordinary module として統合することだが、その導線はまだ draft 段階である。[p2-runtime-sot-linked-program-integration.md](./p2-runtime-sot-linked-program-integration.md)

この前提がないと、SoT 化した helper も結局 ABI 固定された generated artifact として扱われやすく、`PyObj` 縮小への効果が限定される。

## 3. 推奨アーキテクチャ

### 3.1 native shell + generated semantics

第一段階の推奨形はこれである。

- native class は残す
- class の中身は thin shell にする
- `truthy`, `str`, `len`, `iter` などの意味論は generated helper へ委譲する

概念的には次のようになる。

```cpp
class PyIntObj : public PyObj {
public:
    explicit PyIntObj(int64 v) : PyObj(PYTRA_TID_INT), value(v) {}
    int64 value;

    bool py_truthy() const override { return pyobj_semantics::int_truthy(value); }
    ::std::string py_str() const override { return pyobj_semantics::int_str(value); }
};
```

ここで `pyobj_semantics::*` は pure Python SoT から generated される低レベル helper 群である。

### 3.2 class ではなく関数 SoT にする

最初から pure Python class で `PyIntObj` を再現しようとすると、継承、virtual、layout、ownership がすぐ問題になる。  
したがって SoT 側は class ではなく、まずは次のような関数群に分ける方がよい。

```python
def py_int_truthy(v: int) -> bool:
    return v != 0

def py_int_str(v: int) -> str:
    return str(v)

def py_str_truthy(s: str) -> bool:
    return len(s) != 0

def py_str_len(s: str) -> int:
    return len(s)
```

この粒度なら、class generic や native layout を持ち込まずに SoT 化しやすい。

## 4. どこまでなら先にできるか

### 4.1 先にやりやすいもの

- `PyIntObj`
- `PyFloatObj`
- `PyBoolObj`
- `PyStrObj` の truthy/len/str

これらは value field が単純で、C++ shell から helper 呼び出しへ置き換えやすい。

### 4.2 まだ重いもの

- `PyListObj`
- `PyDictObj`
- `PySetObj`
- `PyListIterObj`
- `PyDictKeyIterObj`
- `PyStrIterObj`

理由:

- `list<object>` / `dict<str, object>` / `set<object>` の container ownership が絡む
- iterator が `object` handle と `dynamic_cast` を使う
- helper generic が無いと `list[T]` / `dict[K, V]` semantics を自然に書きにくい

## 5. linked runtime / helper generics が入ると何が変わるか

長期的には、linked runtime integration と helper-limited generics が入ると container 系 SoT 化の地盤ができる。

- runtime helper を ordinary module として call graph に入れられる
- `list[T]`, `dict[K, V]`, `tuple[T, U]` helper を pure Python で書きやすくなる
- `object` 退化を減らせる
- `py_runtime.h` に残る collection helper を SoT に戻しやすくなる

ただし、その場合でも `RcObject` / `RcHandle<T>` / `PyObj` 自体は native ABI core に残ると考えるのが自然である。

## 6. 段階導入するなら

### Phase 1: design only

- `PyObj` 周辺を `native ABI core` と `semantic helper` に二分する契約を spec/plan に固定する
- leaf semantics の候補を棚卸しする

### Phase 2: scalar/string leaf extraction

- `PyIntObj`, `PyFloatObj`, `PyBoolObj`, `PyStrObj` の truthy/str/len semantics を pure Python SoT helper に切り出す
- native class は thin shell にする

### Phase 3: iterator/container helper draft

- `PyStrIterObj` など比較的単純な iterator semantics から SoT 化可能性を試す
- `PyListObj` / `PyDictObj` は blocker を維持したまま helper-limited generic を待つ

### Phase 4: linked runtime integration 後の再評価

- runtime SoT linked-program integration と helper generics が入った段階で、container/iterator を再評価する
- `PyObj` の meaning layer と ownership/ABI layer をさらに切り離せるか判断する

## 7. 判断基準

次のどちらかに当たるものは pure Python SoT へ戻しやすい。

- native layout を知らなくてよい
- template/generic class を要しない

逆に、次のどれかに当たるものは native 残留が妥当である。

- refcount/ownership を直接持つ
- `dynamic_cast` や virtual layout に依存する
- function-local static や macro で class metadata を抱える
- `generated/core` の禁止事項に触れる

## 決定ログ

- 2026-03-14: `PyObj` とその派生 class を pure Python から C++ へ直接再生成する案について、難所は class 自体より `RcObject/RcHandle/PyObj` の native ABI core にあると整理した。
- 2026-03-14: 当面の本命は「class の pure Python 化」ではなく、「leaf semantics を pure Python SoT helper に出し、native class を thin shell にする」案だと判断した。
