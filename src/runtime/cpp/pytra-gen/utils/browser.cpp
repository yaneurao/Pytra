// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/browser.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/utils/browser.h"


namespace pytra::utils::browser {

    /* Minimal browser shim for transpilation and non-browser backends. */
    
    
    struct Touch {
        int64 clientX() {
            return 0;
        }
        int64 clientY() {
            return 0;
        }
        int64 identifier() {
            return 0;
        }
    };
    
    struct DOMEvent {
        int64 keyCode() {
            return 0;
        }
        int64 offsetX() {
            return 0;
        }
        int64 offsetY() {
            return 0;
        }
        int64 buttons() {
            return 0;
        }
        list<Touch> touches() {
            return list<Touch>{};
        }
        void preventDefault() {
            /* pass */
        }
        void stopPropagation() {
            /* pass */
        }
    };
    
    struct TextMetrics : public PyObj {
        int64 height;
        int64 width;
        
        TextMetrics() {
            this->width = 0;
            this->height = 0;
        }
    };
    
    struct HtmlImage : public PyObj {
        int64 naturalHeight;
        int64 naturalWidth;
        
        HtmlImage() {
            this->naturalWidth = 0;
            this->naturalHeight = 0;
        }
        rc<Element> __setitem__(const str& name, const str& value) {
            str _ = name;
            _ = value;
            return ::rc_new<Element>();
        }
    };
    
    struct CanvasRenderingContext : public PyObj {
        str fillStyle;
        str font;
        str strokeStyle;
        str textBaseline;
        
        CanvasRenderingContext() {
            this->fillStyle = "";
            this->strokeStyle = "";
            this->font = "";
            this->textBaseline = "";
        }
        void fillRect(const object& x, const object& y, const object& w, const object& h) {
            object _ = x;
            _ = y;
            _ = w;
            _ = h;
        }
        void fillText(const str& text, const object& x, const object& y) {
            (void)text;
            (void)x;
            (void)y;
        }
        void strokeRect(const object& x, const object& y, const object& w, const object& h) {
            object _ = x;
            _ = y;
            _ = w;
            _ = h;
        }
        void drawImage(const rc<HtmlImage>& image, const object& sx, const object& sy, const object& sw, const object& sh, const object& px, const object& py, const object& dw, const object& dh) {
            (void)image;
            (void)sx;
            (void)sy;
            (void)sw;
            (void)sh;
            (void)px;
            (void)py;
            (void)dw;
            (void)dh;
        }
        rc<TextMetrics> measureText(const str& text) {
            str _ = text;
            return ::rc_new<TextMetrics>();
        }
    };
    
    struct ImageCreator {
        rc<HtmlImage> py_new() {
            return ::rc_new<HtmlImage>();
        }
    };
    
    struct IntervalHandle {
        /* pass */
    };
    
    struct window {
        ImageCreator Image = ImageCreator();
        IntervalHandle setInterval(const object& callback, const object& t) {
            object _ = make_object(callback);
            _ = make_object(t);
            return IntervalHandle();
        }
        void clearInterval(const IntervalHandle& handle) {
            IntervalHandle _ = handle;
        }
    };
    
    struct Element : public PyObj {
        object currentTime;
        int64 height;
        object volume;
        int64 width;
        
        Element() {
            this->currentTime = make_object(int64(0));
            this->volume = make_object(int64(0));
            this->width = 0;
            this->height = 0;
        }
        rc<Element> createElement(const str& name) {
            str _ = name;
            return ::rc_new<Element>();
        }
        void addEventListener(const str& eventName, const object& callback) {
            str _ = eventName;
            _ = py_to_string(callback);
        }
        void removeEventListener(const str& eventName, const object& callback) {
            str _ = eventName;
            _ = py_to_string(callback);
        }
        rc<Element> __getitem__(const str& name) {
            str _ = name;
            return ::rc_new<Element>();
        }
        rc<Element> __setitem__(const str& name, const str& value) {
            str _ = name;
            _ = value;
            return ::rc_new<Element>();
        }
        void play() {
            /* pass */
        }
        void stop() {
            /* pass */
        }
        void pause() {
            /* pass */
        }
        rc<CanvasRenderingContext> getContext(const str& name) {
            str _ = name;
            return ::rc_new<CanvasRenderingContext>();
        }
    };
    
    rc<Element> document = ::rc_new<Element>();
    
}  // namespace pytra::utils::browser
