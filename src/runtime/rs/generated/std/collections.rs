mod py_runtime;
pub use crate::py_runtime::{pytra};
use crate::py_runtime::*;

#[derive(Clone, Debug)]
struct deque {
    _items: Vec<i64>,
}
impl deque {
    fn new() -> Self {
        Self {
            _items: vec![],
        }
    }
    
    fn append(&mut self, value: i64) {
        self._items.push(value);
    }
    
    fn appendleft(&mut self, value: i64) {
        self._items.insert(0, value);
    }
    
    fn pop(&mut self) -> i64 {
        if self._items.len() as i64 == 0 {
            panic!("{}", ("pop from empty deque").to_string());
        }
        return self._items.pop().unwrap_or_default();
    }
    
    fn popleft(&mut self) -> i64 {
        if self._items.len() as i64 == 0 {
            panic!("{}", ("pop from empty deque").to_string());
        }
        let item: i64 = self._items[((0) as usize)];
        self._items = self._items[1..];
        return item;
    }
    
    fn __len__(&self) -> i64 {
        return self._items.len() as i64;
    }
    
    fn clear(&mut self) {
        self._items = vec![];
    }
}


fn main() {
    ("Pytra collections module — list-based deque implementation.\n\nProvides a deque compatible with all transpilation targets.\nBackends with native deque (C++ std::deque, Rust VecDeque, etc.)\ncan override this with emitter-level optimization.\n").to_string();
}
