#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/utils/browser/widgets/dialog.h"


namespace pytra::utils::browser::widgets::dialog {

    /* browser.widgets.dialog shim. */
    
    
    struct Dialog : public PyObj {
        bool ok_cancel;
        str title;
        
        Dialog(const str& title = "", bool ok_cancel = false) {
            this->title = title;
            this->ok_cancel = ok_cancel;
        }
    };
    
    struct EntryDialog : public PyObj {
        str title;
        str value;
        
        EntryDialog(const str& title = "", const str& value = "") {
            this->title = title;
            this->value = value;
        }
    };
    
    struct InfoDialog : public PyObj {
        str text;
        str title;
        
        InfoDialog(const str& title = "", const str& text = "") {
            this->title = title;
            this->text = text;
        }
    };
    
}  // namespace pytra::utils::browser::widgets::dialog
