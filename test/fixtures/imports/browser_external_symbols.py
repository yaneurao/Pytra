from __future__ import annotations

from browser import document, window as win
from browser.widgets.dialog import Dialog as Dlg


def run_case() -> bool:
    title = document.title
    _ = win
    _ = Dlg
    return title != ""


if __name__ == "__main__":
    print(run_case())

