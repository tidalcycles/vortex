import glob
import logging
import os
import sys

import pkg_resources
from PyQt5.Qsci import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from py_vortex import vortex_dsl

_logger = logging.getLogger(__name__)

RES_DIR = pkg_resources.resource_filename("py_vortex", "res")
FONTS_DIR = os.path.join(RES_DIR, "fonts")

DEFAULT_FONT_FAMILY = "Iosevka Term"
DEFAULT_CODE = r"""# this is an example code
p("test",
    s(stack([pure("gabba").fast(4), pure("cp").fast(3)]))
        >> speed(sequence([pure(2), pure(3)]))
        >> room(pure(0.5))
        >> size(pure(0.8))
    )
)

""".replace(
    "\n", "\r\n"
)


class VortexMainWindow(QMainWindow):
    def __init__(self, dsl_module):
        super(VortexMainWindow, self).__init__()

        self._dsl_module = dsl_module

        # Define the geometry of the main window
        self.setGeometry(300, 300, 800, 400)
        self.setWindowTitle("Vortex")

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

        # Create Python Lexer
        self._lexer = QsciLexerPython(self._editor)
        self._lexer.setFont(self._editorFont)
        self._editor.setLexer(self._lexer)

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
        print("TODO: Evaluate code")
        code = "hush()"
        print(f"Eval: '{code}'")
        exec(code, vars(self._dsl_module))


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
