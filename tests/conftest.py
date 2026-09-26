"""Keep the test suite away from the user's real app settings.

MainWindow persists preferences (layout mode, fit-to-width, side panel,
theme...) through QSettings("kherveDOC", "kherveDOC"). Without this,
running the tests on a developer's machine rewrote their actual
KherveTeX preferences. That constructor uses QSettings' default format,
so switching it to an INI file in a throwaway directory isolates every
test at once.
"""
import tempfile

try:
    from PySide6.QtCore import QSettings
except ImportError:          # pure-model tests still run without Qt
    QSettings = None

if QSettings is not None:
    _dir = tempfile.mkdtemp(prefix="khervedoc-test-settings-")
    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, _dir)
