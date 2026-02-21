// This file contains test/implementation code for `test/test_gc.cpp`.
// Additional comments are included to make responsibilities easier to understand.
// When modifying this file, always verify thread safety and reference-count consistency.

#include <atomic>
#include <cassert>
#include <iostream>
#include <thread>
#include <vector>

#include "../src/runtime/cpp/pytra/built_in/gc.h"

namespace gc = pytra::gc;

// Simple referenced object used to validate destructor call counts.
struct TestLeaf : public gc::PyObj {
    static std::atomic<int> destroyed;

    explicit TestLeaf(int v) : gc::PyObj(1), value(v) {}
    ~TestLeaf() override { destroyed.fetch_add(1, std::memory_order_relaxed); }

    int value;
};

std::atomic<int> TestLeaf::destroyed{0};

struct TestPair : public gc::PyObj {
    static std::atomic<int> destroyed;

    explicit TestPair(TestLeaf* l, TestLeaf* r) : gc::PyObj(2), left(l), right(r) {
        gc::incref(left);
        gc::incref(right);
    }

    ~TestPair() override { destroyed.fetch_add(1, std::memory_order_relaxed); }

    // When the parent object is destroyed, decref child references to trigger chained release.
    void rc_release_refs() override {
        gc::decref(left);
        gc::decref(right);
        left = nullptr;
        right = nullptr;
    }

    TestLeaf* left;
    TestLeaf* right;
};

std::atomic<int> TestPair::destroyed{0};

void test_basic_incref_decref() {
    TestLeaf::destroyed.store(0, std::memory_order_relaxed);

    TestLeaf* leaf = gc::rc_new<TestLeaf>(10);  // ref=1
    assert(leaf->ref_count() == 1);

    gc::incref(leaf);  // ref=2
    assert(leaf->ref_count() == 2);

    gc::decref(leaf);  // ref=1
    assert(TestLeaf::destroyed.load(std::memory_order_relaxed) == 0);

    gc::decref(leaf);  // ref=0, delete
    assert(TestLeaf::destroyed.load(std::memory_order_relaxed) == 1);
}

void test_recursive_release() {
    TestLeaf::destroyed.store(0, std::memory_order_relaxed);
    TestPair::destroyed.store(0, std::memory_order_relaxed);

    TestLeaf* a = gc::rc_new<TestLeaf>(1);  // ref=1
    TestLeaf* b = gc::rc_new<TestLeaf>(2);  // ref=1

    TestPair* pair = gc::rc_new<TestPair>(a, b);  // pair ref=1, a/b ref=2
    gc::decref(a);                                // a ref=1 (owned by pair)
    gc::decref(b);                                // b ref=1 (owned by pair)

    gc::decref(pair);  // pair delete -> decref(a,b) -> a,b delete

    assert(TestPair::destroyed.load(std::memory_order_relaxed) == 1);
    assert(TestLeaf::destroyed.load(std::memory_order_relaxed) == 2);
}

void test_raii_handle() {
    TestLeaf::destroyed.store(0, std::memory_order_relaxed);

    auto h1 = gc::RcHandle<TestLeaf>::adopt(gc::rc_new<TestLeaf>(7));
    {
        gc::RcHandle<TestLeaf> h2 = h1;  // incref
        assert(h1->ref_count() == 2);
    }                                    // decref
    assert(h1->ref_count() == 1);

    h1.reset();  // delete
    assert(TestLeaf::destroyed.load(std::memory_order_relaxed) == 1);
}

void test_multithread_atomic_rc() {
    TestLeaf::destroyed.store(0, std::memory_order_relaxed);

    TestLeaf* shared = gc::rc_new<TestLeaf>(99);  // ref=1 (root)

    constexpr int kThreads = 8;
    constexpr int kIters = 50000;

    std::vector<std::thread> threads;
    threads.reserve(kThreads);

    // Increment/decrement references to the same object from multiple threads to verify atomicity.
    for (int t = 0; t < kThreads; ++t) {
        threads.emplace_back([shared]() {
            for (int i = 0; i < kIters; ++i) {
                gc::incref(shared);
                gc::decref(shared);
            }
        });
    }

    for (auto& th : threads) {
        th.join();
    }

    assert(shared->ref_count() == 1);
    gc::decref(shared);
    assert(TestLeaf::destroyed.load(std::memory_order_relaxed) == 1);
}

int main() {
    test_basic_incref_decref();
    test_recursive_release();
    test_raii_handle();
    test_multithread_atomic_rc();

    std::cout << "test_gc: all tests passed" << std::endl;
    return 0;
}
