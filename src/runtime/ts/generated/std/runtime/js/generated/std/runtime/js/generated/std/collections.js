import { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } from "./runtime/js/native/built_in/py_runtime.js";

class deque {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor() {
        this._items = [];
    this[PYTRA_TYPE_ID] = deque.PYTRA_TYPE_ID;
    }
    
    append(value) {
        this._items.push(value);
    }
    
    appendleft(value) {
        this._items.insert(0, value);
    }
    
    pop() {
        if ((this._items).length === 0) {
            throw new Error("pop from empty deque");
        }
        return this._items.pop();
    }
    
    popleft() {
        if ((this._items).length === 0) {
            throw new Error("pop from empty deque");
        }
        let item = this._items[(((0) < 0) ? ((this._items).length + (0)) : (0))];
        this._items = this._items.slice(1);
        return item;
    }
    
    __len__() {
        return (this._items).length;
    }
    
    clear() {
        this._items = [];
    }
}

"Pytra collections module — list-based deque implementation.\n\nProvides a deque compatible with all transpilation targets.\nBackends with native deque (C++ std::deque, Rust VecDeque, etc.)\ncan override this with emitter-level optimization.\n";
