// collections.dart — Pytra Dart collections runtime (deque)
// source: src/runtime/dart/std/collections.dart
import 'dart:collection';

class deque {
  final ListQueue<dynamic> _q = ListQueue<dynamic>();

  // append → add (Dart emitter maps Python .append() to .add())
  void add(dynamic v) => _q.addLast(v);
  void appendleft(dynamic v) => _q.addFirst(v);
  // pop/removeLast: Dart emitter maps Python .pop() to .removeLast()
  dynamic removeLast() => _q.removeLast();
  dynamic popleft() => _q.removeFirst();
  void clear() => _q.clear();
  int get length => _q.length;
}
