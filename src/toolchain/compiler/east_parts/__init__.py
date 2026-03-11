"""Split EAST modules."""
from toolchain.ir.core import (  # noqa: F401
    FLOAT_TYPES,
    INT_TYPES,
    convert_source_to_east_self_hosted,
)
from toolchain.ir.core_entrypoints import (  # noqa: F401
    EastBuildError,
    convert_path,
    convert_source_to_east,
    convert_source_to_east_with_backend,
)
from .east2_to_human_repr import (  # noqa: F401
    render_east2_to_human_repr,
    render_east_to_human_repr,
    render_east2_human_cpp,
    render_east_human_cpp,
)
from .east3_to_human_repr import (  # noqa: F401
    render_east3_to_human_repr,
    render_east3_human_cpp,
)
from .east3_optimizer import (  # noqa: F401
    East3OptimizerPass,
    PassContext,
    PassManager,
    PassResult,
    optimize_east3_document,
    parse_east3_opt_pass_overrides,
    render_east3_opt_trace,
    resolve_east3_opt_level,
)
from .cli import main  # noqa: F401
from .code_emitter import CodeEmitter  # noqa: F401
from .east2_to_east3_lowering import lower_east2_to_east3  # noqa: F401
# NOTE:
# `east1_build` imports many helpers from `transpile_cli`, and `transpile_cli` imports
# `toolchain.compiler.east_parts.*`. Re-exporting `east1_build` here makes import cycles
# easier to trigger depending on import order. Keep `east1_build` as an explicit import
# target (`toolchain.compiler.east_parts.east1_build`) instead of package-level re-export.
