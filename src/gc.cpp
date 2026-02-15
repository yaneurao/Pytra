#include "gc.h"

namespace pycs::gc {

void PyObj::rc_release_refs() {
    // Default: no outgoing references.
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

    const uint32_t old = obj->ref_count_.fetch_sub(1, std::memory_order_acq_rel);
    assert(old > 0 && "decref underflow");

    if (old == 1) {
        obj->rc_release_refs();
        delete obj;
    }
}

}  // namespace pycs::gc
