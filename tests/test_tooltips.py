"""Every toolbar button carries long, Word-user-friendly hover help."""
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QToolBar  # noqa: E402

from khervedoc import tooltips  # noqa: E402


def test_every_toolbar_action_has_long_help():
    QApplication.instance() or QApplication([])
    from khervedoc.mainwindow import MainWindow
    w = MainWindow()
    names = {id(v): k for k, v in vars(w).items() if k.startswith("act_")}
    for tb in w.findChildren(QToolBar):
        for act in tb.actions():
            name = names.get(id(act))
            if name is None:
                continue
            assert name in tooltips.TIPS, name
            assert len(act.toolTip()) > 80, name
    assert "Document type" in w._class_button.toolTip()
    assert "Numbered heading" in w._numbered_cb.toolTip()
