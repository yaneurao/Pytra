#ifndef PYTRA_BUILT_IN_CONTAINER_COMMON_H
#define PYTRA_BUILT_IN_CONTAINER_COMMON_H

// py_runtime.h 側で定義される object からの安全キャスト補助。
template <class D>
::std::optional<D> py_object_try_cast(const object& v);

#endif  // PYTRA_BUILT_IN_CONTAINER_COMMON_H
