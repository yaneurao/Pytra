#include "runtime/cpp/py_runtime.h"

#include "pytra/std/typing.h"

namespace pytra::std::typing {

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    object TypeVar(const str& name) {
        return py_typing_typevar(name);
    }
    
}  // namespace pytra::std::typing
