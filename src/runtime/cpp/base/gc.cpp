// このファイルは `src/gc.cpp` のテスト/実装コードです。
// 読み手が責務を把握しやすいように、日本語コメントを追記しています。
// 変更時は、スレッド安全性と参照カウント整合性を必ず確認してください。

#include "runtime/cpp/base/gc.h"

namespace pytra::gc {

void PyObj::rc_release_refs() {
    // デフォルト実装: 子参照を持たないオブジェクト。
}

void incref(PyObj* obj) noexcept {
    // obj:
    //   参照カウントを増やす対象オブジェクト。nullptr は無視する。
    if (obj == nullptr) {
        return;
    }
    obj->ref_count_.fetch_add(1, std::memory_order_relaxed);
}

void decref(PyObj* obj) noexcept {
    // obj:
    //   参照カウントを減らす対象オブジェクト。0到達時に破棄する。
    if (obj == nullptr) {
        return;
    }

    // oldは減算前の値。old==1なら今回のdecrefで0になる。
    const uint32_t old = obj->ref_count_.fetch_sub(1, std::memory_order_acq_rel);
    assert(old > 0 && "decref underflow");

    if (old == 1) {
        // delete前に、保持している子参照を先に解放して連鎖的に回収する。
        obj->rc_release_refs();
        delete obj;
    }
}

}  // namespace pytra::gc
