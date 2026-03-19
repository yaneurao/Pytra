#ifndef PYTRA_BUILT_IN_PY_RUNTIME_H
#define PYTRA_BUILT_IN_PY_RUNTIME_H

// py_runtime.h — compatibility facade.
// New code should include individual headers directly.

#include "core/py_types.h"
#include "core/exceptions.h"
#include "core/io.h"
#include "built_in/base_ops.h"
#include "built_in/string_ops.h"
#include "core/str_methods.h"
#include "core/conversions.h"
#include "built_in/list_ops.h"
#include "built_in/dict_ops.h"
#include "built_in/bounds.h"
#include "core/type_id_support.h"
#include "built_in/type_id.h"
#include "core/rc_ops.h"

// py_div / py_floordiv / py_mod は built_in/scalar_ops.h へ移動済み。

#endif  // PYTRA_BUILT_IN_PY_RUNTIME_H
