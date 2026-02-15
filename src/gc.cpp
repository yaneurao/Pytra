// このファイルは `src/gc.cpp` のテスト/実装コードです。
// 読み手が責務を把握しやすいように、日本語コメントを追記しています。
// 変更時は、スレッド安全性と参照カウント整合性を必ず確認してください。

#include "gc.h"

namespace pycs::gc {

void PyObj::rc_release_refs() {
    // デフォルト実装: 子参照を持たないオブジェクト。
}

void incref(PyObj* obj) noexcept {
    if (obj == nullptr) {
        return;
    }
    obj->ref_count_.fetch_add(1, std::memory_order_relaxed);
}

void decref(PyObj* obj) noexcept {
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

}  // namespace pycs::gc
