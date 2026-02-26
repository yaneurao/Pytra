"""No-op pass used as phase-1 optimizer skeleton."""

from __future__ import annotations

from pytra.compiler.east_parts.east3_optimizer import East3OptimizerPass
from pytra.compiler.east_parts.east3_optimizer import PassContext
from pytra.compiler.east_parts.east3_optimizer import PassResult


class NoOpPass(East3OptimizerPass):
    """入力を変更しない最小 pass。"""

    name = "NoOpPass"
    min_opt_level = 1

    def run(self, east3_doc: dict[str, object], context: PassContext) -> PassResult:
        _ = east3_doc
        _ = context
        return PassResult()

