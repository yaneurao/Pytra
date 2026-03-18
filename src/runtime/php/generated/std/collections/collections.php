<?php
declare(strict_types=1);

require_once __DIR__ . '/pytra/py_runtime.php';

class Deque {
    public function __construct() {
        $this->_items = [];
    }

    public function append($value) {
        $this->_items[] = $value;
    }

    public function appendleft($value) {
        $this->_items->insert(0, $value);
    }

    public function pop() {
        if ((__pytra_len($this->_items) == 0)) {
            throw new Exception(strval(IndexError("pop from empty deque")));
        }
        return array_pop($this->_items);
    }

    public function popleft() {
        if ((__pytra_len($this->_items) == 0)) {
            throw new Exception(strval(IndexError("pop from empty deque")));
        }
        $item = $this->_items[__pytra_index($this->_items, 0)];
        $this->_items = __pytra_str_slice($this->_items, 1, __pytra_len($this->_items));
        return $item;
    }

    public function __len__() {
        return __pytra_len($this->_items);
    }

    public function clear() {
        $this->_items = [];
    }
}

function __pytra_main(): void {
}

__pytra_main();
