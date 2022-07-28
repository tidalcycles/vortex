import glob
import logging
import os
import sys
import time

import pkg_resources
from PyQt5.Qsci import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from vortex import __version__, vortex_dsl

_logger = logging.getLogger(__name__)

RES_DIR = pkg_resources.resource_filename("vortex", "res")
FONTS_DIR = os.path.join(RES_DIR, "fonts")
HIGHLIGHT_INDICATOR_ID = 0

DEFAULT_FONT_FAMILY = "Fira Code"
DEFAULT_CODE = r"""# this is an example code

# some block

##
# another block
#

p("test", s(stack(pure("gabba").fast(4), pure("cp").fast(3))).every(3, fast(2))
    >> speed(sequence(2, 3))
    >> room(0.5)
    >> size(0.8)
)

hush()

""".replace(
    "\n", "\r\n"
)


class HighlightLines(QRunnable):
    def __init__(self, editor, range, interval=0.1):
        super().__init__()
        self.editor = editor
        self.range = range
        self.interval = interval

    def run(self):
        start, end = self.range
        editor = self.editor

        line, index = editor.getCursorPosition()
        editor.setSelection(start, 0, end, 0)
        editor.setSelectionBackgroundColor(QColor("#ff00ff00"))
        editor.setSelectionForegroundColor(QColor("#ff000000"))

        _logger.info("Wait")
        time.sleep(self.interval)

        # TODO: Should clear from 0 to end of document, just in case...
        # editor.clearIndicatorRange(start, 0, end, 0, HIGHLIGHT_INDICATOR_ID)
        # editor.setCursorPosition(line, index)
        editor.resetSelectionBackgroundColor()
        editor.resetSelectionForegroundColor()

        _logger.info("Done")


class VortexMainWindow(QMainWindow):
    def __init__(self, dsl_module):
        super(VortexMainWindow, self).__init__()

        self._dsl_module = dsl_module

        # Define the geometry of the main window
        # self.setGeometry(400, 100, 800, 600)
        self.setFixedSize(1280, 800)
        self.setWindowTitle(f"Vortex {__version__}")

        # Create frame and layout
        self._frame = QFrame(self)
        self._frame.setStyleSheet("QWidget { background-color: #ffeaeaea }")
        self._layout = QVBoxLayout()
        self._frame.setLayout(self._layout)
        self.setCentralWidget(self._frame)

        self._editorFont = QFont()
        self._editorFont.setPointSize(16)
        self._editorFont.setFamily(DEFAULT_FONT_FAMILY)

        # Create and configure Editor
        self._editor = QsciScintilla()
        self._editor.setText(DEFAULT_CODE)
        self._editor.setUtf8(True)
        self._editor.setIndentationsUseTabs(False)
        self._editor.setAutoIndent(True)
        self._editor.setTabIndents(True)
        self._editor.setTabWidth(4)
        self._editor.setIndentationGuides(True)
        self._editor.setCaretLineVisible(True)
        self._editor.setCaretLineBackgroundColor(QColor("#1fff0000"))
        self._editor.setCaretWidth(3)
        self._editor.setMarginType(0, QsciScintilla.NumberMargin)
        self._editor.setMarginWidth(0, "000")
        self._editor.setMarginsForegroundColor(QColor("#ff888888"))

        # Create Python Lexer
        self._lexer = QsciLexerPython(self._editor)
        self._lexer.setFont(self._editorFont)
        self._editor.setLexer(self._lexer)

        self._editor.indicatorDefine(
            QsciScintilla.FullBoxIndicator, HIGHLIGHT_INDICATOR_ID
        )

        # Commands and shortcuts
        commands = self._editor.standardCommands()
        command = commands.boundTo(Qt.ControlModifier | Qt.Key_Return)
        # Clear the default
        if command is not None:
            command.setKey(0)
        shortcut = QShortcut(Qt.ControlModifier | Qt.Key_Return, self._editor)
        shortcut.activated.connect(self.evaluate_block)

        # Add editor to layout
        self._layout.addWidget(self._editor)

        self.show()

    def evaluate_block(self):
        code, (start, end) = self.get_current_block()
        if code:
            _logger.info(f"Eval: '{code}'")
            try:
                exec(code, vars(self._dsl_module))
            except (TypeError, AttributeError) as e:
                _logger.info("error: %s", str(e))
        # self.highlight_block(start, end)

    def get_current_block(self):
        text = self._editor.text()
        lines = text.split("\n")
        line, _ = self._editor.getCursorPosition()
        if not lines[line].strip():
            return "", (line, line)
        start_line = line
        for i in reversed(range(0, line)):
            if not lines[i].strip():
                start_line = i + 1
                break
        end_line = line
        for i in range(line, len(lines)):
            if not lines[i].strip():
                end_line = i
                break
        _logger.debug("Block between lines %d and %d", start_line, end_line)
        block = "\n".join(lines[start_line : end_line + 1])
        return block, (start_line, end_line)

    def highlight_block(self, start_line, end_line):
        pool = QThreadPool.globalInstance()
        runnable = HighlightLines(self._editor, (start_line, end_line))
        pool.start(runnable)


def load_fonts():
    font_files = glob.glob(os.path.join(FONTS_DIR, "*"))
    for font_file in font_files:
        font = QFontDatabase.addApplicationFont(font_file)
        if font != -1:
            _logger.warn("Failed to load font %s", font_file)


def start_gui():
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create("Fusion"))

    load_fonts()

    with vortex_dsl() as module:
        window = VortexMainWindow(dsl_module=module)
        app.exec_()
