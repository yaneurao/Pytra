# Object\<T\> 設計仕様

<a href="../../en/spec/spec-object.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


## 1. 背景

現行の `object` 型（`{pytra_type_id tag; rc<RcObject> _rc;}` の型消去済み単一型）には以下の問題がある:

- `dict<K,V>` や `list<T>` を格納するのに `rc_new` ラップが必要
- `py_types.h` の forward declaration 時点で `RcObject` のサブクラスか判定できず、テンプレート SFINAE が失敗する
- upcast/downcast に `static_cast` を使い、型安全性がない

本仕様は `Object<T>` テンプレート + `ControlBlock` による新設計を定義する。

## 2. 設計原則

| 概念 | 役割 |
|---|---|
| `ControlBlock` | 実体を管理する（rc, type_id, base_ptr） |
| `Object<T>` | 実体への「view（見え方）」を提供する |
| `type_id` | 実体型で固定。upcast しても変わらない |
| upcast | `ptr` だけ変える。`ControlBlock` は共有 |

一言でいうと：**「X のオブジェクトを、Y として見るだけ」**。

## 3. 前提

```
class Y
class X : Y
```

やりたいこと：

```cpp
Object<X> x = make_object<X>();
Object<Y> y = x;  // upcast — view 変換
```

## 4. 型情報（区間方式）

```cpp
using type_id_t = uint32_t;

struct TypeInfo {
    type_id_t id;
    type_id_t entry;
    type_id_t exit;
    void (*deleter)(void*);
};

extern TypeInfo* g_type_table[];
```

- `isinstance` 判定は区間包含で行う: `entry <= type_id < exit`
- deleter は実体型で固定（正しいデストラクタが呼ばれる）

## 5. ControlBlock

```cpp
struct ControlBlock {
    int rc;
    type_id_t type_id;  // 実体型（X）— cast しても変わらない
    void* base_ptr;     // 常に最も派生型（X*）
};
```

## 6. Object\<T\>

```cpp
template<typename T>
struct Object {
    ControlBlock* cb;
    T* ptr;

    Object() : cb(nullptr), ptr(nullptr) {}

    Object(ControlBlock* cb_, T* ptr_)
        : cb(cb_), ptr(ptr_) {
        retain();
    }

    Object(const Object& other)
        : cb(other.cb), ptr(other.ptr) {
        retain();
    }

    ~Object() {
        release();
    }

    Object& operator=(const Object& other) {
        if (this != &other) {
            release();
            cb = other.cb;
            ptr = other.ptr;
            retain();
        }
        return *this;
    }

private:
    void retain() {
        if (cb) ++cb->rc;
    }

    void release() {
        if (!cb) return;
        if (--cb->rc == 0) {
            auto* ti = g_type_table[cb->type_id];
            ti->deleter(cb->base_ptr);
            delete cb;
        }
    }
};
```

## 7. make_object

```cpp
template<typename T>
Object<T> make_object(type_id_t tid) {
    T* obj = new T();
    ControlBlock* cb = new ControlBlock{1, tid, obj};
    return Object<T>(cb, obj);
}
```

## 8. subtype 判定

```cpp
bool is_subtype(type_id_t t, TypeInfo* base) {
    return base->entry <= t && t < base->exit;
}
```

## 9. upcast（X → Y）

```cpp
template<typename To, typename From>
Object<To> upcast(Object<From> from, TypeInfo* target) {
    assert(is_subtype(from.cb->type_id, target));
    To* new_ptr = static_cast<To*>(from.ptr);
    return Object<To>(from.cb, new_ptr);
}
```

## 10. 使用例

```cpp
int main() {
    Object<X> x = make_object<X>(TYPE_X);

    // X → Y（view 変換）
    Object<Y> y = upcast<Y>(x, &type_Y);

    y.ptr->foo();  // → X::foo 42

    return 0;
}
```

## 11. 重要ポイント

1. **type_id は常に X** — `cb->type_id = TYPE_X`。cast しても変わらない。
2. **ptr だけ変わる** — `X*` → `Y*`。view 変更。
3. **rc は共有** — `x.cb == y.cb`。+1 されるだけ。
4. **delete は X で行われる** — `deleter_impl<X>`。正しいデストラクタが呼ばれる。
5. **`y: Y = x` の意味** — `Object<Y> y = upcast<Y>(x)`。コピーではなく view 変換。

## 12. クラス定義例

```cpp
struct Y {
    virtual ~Y() {}
    virtual void foo() {
        std::cout << "Y::foo\n";
    }
};

struct X : Y {
    int value = 42;
    void foo() override {
        std::cout << "X::foo " << value << "\n";
    }
};

// deleter
template<typename T>
void deleter_impl(void* p) {
    delete static_cast<T*>(p);
}

// 型テーブル
enum { TYPE_Y, TYPE_X };

TypeInfo type_Y = {TYPE_Y, 0, 2, &deleter_impl<Y>};  // Y は [0, 2)
TypeInfo type_X = {TYPE_X, 1, 2, &deleter_impl<X>};  // X は [1, 2)

TypeInfo* g_type_table[] = {&type_Y, &type_X};
```

## 13. まとめ

- **ControlBlock** は「実体」
- **Object\<T\>** は「見え方」
- **upcast** は ptr 変更のみ
- **rc** は共有
- **type_id** は不変
