// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/toolchain/compiler/transpile_cli.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/native/core/py_runtime.h"

#include "runtime/cpp/generated/compiler/transpile_cli.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"

#include "runtime/cpp/generated/compiler/typed_boundary.h"

namespace pytra::compiler::transpile_cli {

    object normalize_east1_to_east2_document_stage;
    object load_east1_document_stage;
    object load_east3_document_stage;
    
    /* Compatibility shim for transpile CLI helpers.

Canonical implementation moved to ``toolchain.frontends.transpile_cli``.
 */
    
    object normalize_east1_to_east2_document(const object& east_doc) {
        auto stage_fn = ([&]() { auto&& __dict_1 = globals(); auto __dict_key_2 = "normalize_east1_to_east2_document_stage"; return __dict_1.contains(__dict_key_2) ? __dict_1.at(__dict_key_2) : object{}; }());
        if (callable(stage_fn)) {
            auto out = stage_fn(east_doc);
            if (py_runtime_value_isinstance(out, PYTRA_TID_DICT))
                return make_object(out);
        }
        return make_object(_front.normalize_east1_to_east2_document(east_doc));
    }
    
    object load_east1_document(const object& input_path, const object& parser_backend) {
        auto stage_fn = ([&]() { auto&& __dict_3 = globals(); auto __dict_key_4 = "load_east1_document_stage"; return __dict_3.contains(__dict_key_4) ? __dict_3.at(__dict_key_4) : object{}; }());
        if (callable(stage_fn))
            return make_object(stage_fn(input_path, parser_backend, load_east_document));
        return make_object(_front.load_east1_document(input_path, parser_backend));
    }
    
    object load_east3_document(const object& input_path, const object& parser_backend, const object& object_dispatch_mode, const object& east3_opt_level, const object& east3_opt_pass, const object& dump_east3_before_opt, const object& dump_east3_after_opt, const object& dump_east3_opt_trace, const object& target_lang) {
        auto stage_fn = ([&]() { auto&& __dict_5 = globals(); auto __dict_key_6 = "load_east3_document_stage"; return __dict_5.contains(__dict_key_6) ? __dict_5.at(__dict_key_6) : object{}; }());
        if (callable(stage_fn))
            return make_object(stage_fn(input_path, parser_backend, object_dispatch_mode, east3_opt_level, east3_opt_pass, dump_east3_before_opt, dump_east3_after_opt, dump_east3_opt_trace, target_lang, load_east_document, make_user_error));
        return make_object(_front.load_east3_document(input_path, parser_backend, object_dispatch_mode, east3_opt_level, east3_opt_pass, dump_east3_before_opt, dump_east3_after_opt, dump_east3_opt_trace, target_lang));
    }
    
    CompilerRootDocument load_east3_document_typed(const object& input_path, const object& parser_backend, const object& object_dispatch_mode, const object& east3_opt_level, const object& east3_opt_pass, const object& dump_east3_before_opt, const object& dump_east3_after_opt, const object& dump_east3_opt_trace, const object& target_lang) {
        return _front.load_east3_document_typed(input_path, parser_backend, object_dispatch_mode, east3_opt_level, east3_opt_pass, dump_east3_before_opt, dump_east3_after_opt, dump_east3_opt_trace, target_lang);
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        normalize_east1_to_east2_document_stage = make_object(_front.normalize_east1_to_east2_document_stage);
        load_east1_document_stage = make_object(_front.load_east1_document_stage);
        load_east3_document_stage = make_object(_front.load_east3_document_stage);
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::compiler::transpile_cli
