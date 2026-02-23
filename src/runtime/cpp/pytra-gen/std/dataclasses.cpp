#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/dataclasses.h"

#include "pytra/std/dataclasses-impl.h"
#include "pytra/std/typing.h"

namespace pytra::std::dataclasses {

    /* pytra.std.dataclasses: thin wrapper over dataclasses_impl. */
    
    
    
    
    object dataclass(const object& _cls, bool init, bool repr, bool eq) {
        /* `@dataclass` の最小互換入口。実装本体は dataclasses_impl 側。 */
        return pytra::std::dataclasses_impl::dataclass(_cls, init, repr, eq);
    }
    
}  // namespace pytra::std::dataclasses
