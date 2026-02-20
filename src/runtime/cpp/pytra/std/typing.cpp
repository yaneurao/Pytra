#include "runtime/cpp/py_runtime.h"


namespace pytra::std::typing {

    
    int64 Any = 1;
    
    int64 List = 1;
    
    int64 Set = 1;
    
    int64 Dict = 1;
    
    int64 Tuple = 1;
    
    int64 Iterable = 1;
    
    int64 Sequence = 1;
    
    int64 Mapping = 1;
    
    int64 Optional = 1;
    
    int64 Union = 1;
    
    int64 Callable = 1;
    
    int64 TypeAlias = 1;
    
    int64 TypeVar(const str& name) {
        str _ = name;
        return 1;
    }
    
}  // namespace pytra::std::typing
