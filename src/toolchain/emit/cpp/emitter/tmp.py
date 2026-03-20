from __future__ import annotations

class CppTemporaryEmitter:
    """Temporary-name helpers used by C++ emitter."""

    def next_finally_guard_name(self) -> str:
        """`finally` 用スコープガード名を生成する。"""
        return self.next_tmp("__finally")

    def next_for_iter_name(self) -> str:
        """`for (...) : range` 系で使う反復一時変数名を生成する。"""
        return self.next_tmp("__it")

    def next_for_runtime_iter_name(self) -> str:
        """`runtime protocol` 系 for の object 反復一時変数名を生成する。"""
        return self.next_tmp("__itobj")

    def next_tuple_tmp_name(self) -> str:
        """タプル代入一時変数名を生成する。"""
        return self.next_tmp("__tuple")

    def next_yield_values_name(self) -> str:
        """ジェネレータ用 yield バッファ名を生成する。"""
        return self.next_tmp("__yield_values")

    def scope_names_with_tmp(self, scope_names: set[str], tmp_name: str) -> set[str]:
        """一時変数を含む生存域セットを返す。"""
        if tmp_name == "":
            return set(scope_names)
        tmp_scope = set(scope_names)
        tmp_scope.add(tmp_name)
        return tmp_scope
