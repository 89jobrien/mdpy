import sys
from dataclasses import dataclass

from markdown2 import Markdown
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTextBrowser,
    QTextEdit,
)

try:
    from pygments.formatters import HtmlFormatter
except ImportError:
    HtmlFormatter = None


@dataclass
class AppConfig:
    """Configuration settings for the application."""

    default_width: int = 1200
    default_height: int = 800
    window_title: str = "Joe's Markdown Viewer"
    editor_font_family: str = "Menlo"
    editor_font_size: int = 14


@dataclass
class Theme:
    """Stores the CSS for a specific theme."""

    pygments_css: str
    html_css: str
    app_stylesheet: str


class MarkdownViewer(QMainWindow):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.current_file_path = None
        self.is_dark_mode = True
        self.markdown_converter = Markdown(
            extras=["fenced-code-blocks", "tables", "strike"]
        )

        self._create_themes()
        self._setup_window()
        self._setup_ui()
        self._setup_menu()
        self._apply_theme()

        self.editor.setPlainText(
            "```python\n# Type your markdown here!\n# Syntax highlighting is now active.\ndef hello(name):\n    print(f'Hello, {name}!')\n\nhello('World')\n```\n\n| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |\n\n- Tables\n- ~~Strike-through~~\n- And more!\n"
        )
        self._update_window_title()

    def _create_themes(self):
        """Generates and stores the light and dark theme stylesheets."""
        light_pygments_css = (
            HtmlFormatter(style="default").get_style_defs(".codehilite")
            if HtmlFormatter
            else ""
        )
        light_html_css = """
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
                line-height: 1.6; background-color: #ffffff; color: #24292e; padding: 10px;
            }
            h1, h2, h3, h4, h5, h6 { border-bottom: 1px solid #eaecef; color: #24292e; }
            a { color: #0366d6; }
            code { background-color: rgba(27,31,35,.05); }
            blockquote { color: #6a737d; border-left: .25em solid #dfe2e5; }
            body > table th, body > table td { border: 1px solid #dfe2e5; }
            body > table tr { background-color: #fff; border-top: 1px solid #c6cbd1; }
            body > table tr:nth-child(2n) { background-color: #f6f8fa; }
            hr { background-color: #e1e4e8; }
        """
        light_app_stylesheet = """
            QMainWindow, QMenuBar, QMenu { background-color: #f6f8fa; color: #24292e; }
            QMenuBar::item:selected, QMenu::item:selected { background-color: #e1e4e8; }
            QTextEdit { background-color: #ffffff; color: #24292e; border: 1px solid #d1d5da; selection-background-color: #0366d6; selection-color: #ffffff; }
            QSplitter::handle { background-color: #e1e4e8; }
            QScrollBar::handle { background: #d1d5da; }
        """
        self.light_theme = Theme(
            light_pygments_css, light_html_css, light_app_stylesheet
        )

        # --- Dark Theme ---
        dark_pygments_css = (
            HtmlFormatter(style="monokai").get_style_defs(".codehilite")
            if HtmlFormatter
            else ""
        )
        dark_html_css = """
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
                line-height: 1.6; background-color: #2b2b2b; color: #f0f0f0; padding: 10px;
            }
            h1, h2, h3, h4, h5, h6 { border-bottom: 1px solid #444; color: #f0f0f0; }
            a { color: #61afef; }
            code { background-color: #3c3c3c; }
            blockquote { color: #999; border-left: .25em solid #555; }
            body > table th, body > table td { border: 1px solid #444; }
            body > table tr { background-color: #2b2b2b; border-top: 1px solid #444; }
            body > table tr:nth-child(2n) { background-color: #313131; }
            hr { background-color: #444; }
        """
        dark_app_stylesheet = """
            QMainWindow, QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QMenuBar, QMenu { background-color: #3c3c3c; color: #f0f0f0; }
            QMenuBar::item:selected, QMenu::item:selected { background-color: #555; }
            QTextEdit { background-color: #2b2b2b; color: #f8f8f2; border: 1px solid #444; selection-background-color: #4a4a4a; }
            QSplitter::handle { background-color: #3c3c3c; }
            QScrollBar::handle { background: #555; }
        """
        self.dark_theme = Theme(dark_pygments_css, dark_html_css, dark_app_stylesheet)

    def _setup_window(self):
        """Configures the main window properties."""
        self.setGeometry(
            100, 100, self.config.default_width, self.config.default_height
        )

    def _setup_ui(self):
        """Creates and configures the main user interface widgets."""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        self.editor = QTextEdit()
        self.editor.setFontFamily(self.config.editor_font_family)
        self.editor.setFontPointSize(self.config.editor_font_size)
        self.editor.textChanged.connect(self._update_preview)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes(
            [self.config.default_width // 2, self.config.default_width // 2]
        )

    def _setup_menu(self):
        """Creates the main menu bar and its actions."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_file)
        file_menu.addAction(save_action)
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menu_bar.addMenu("&View")
        self.dark_mode_action = QAction("Dark Mode", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setChecked(self.is_dark_mode)
        self.dark_mode_action.triggered.connect(self._toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)

    @Slot()
    def _toggle_dark_mode(self):
        """Switches the application theme between light and dark."""
        self.is_dark_mode = not self.is_dark_mode
        self.dark_mode_action.setChecked(self.is_dark_mode)
        self._apply_theme()

    def _apply_theme(self):
        """Applies the currently selected theme to the application."""
        theme = self.dark_theme if self.is_dark_mode else self.light_theme
        self.setStyleSheet(theme.app_stylesheet)
        self._update_preview()

    @Slot()
    def _update_preview(self):
        """
        Converts the Markdown text to styled HTML and updates the preview pane.
        """
        markdown_text = self.editor.toPlainText()
        html_output = self.markdown_converter.convert(markdown_text)

        theme = self.dark_theme if self.is_dark_mode else self.light_theme
        styled_html = f"""
        <html>
        <head>
            <style>
                /* Shared Styles */
                h1, h2, h3, h4, h5, h6 {{
                    font-weight: 600; line-height: 1.25; padding-bottom: .3em;
                }}
                a:hover {{ text-decoration: underline; }}
                code {{
                    padding: .2em .4em; margin: 0;
                    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
                    font-size: 85%; border-radius: 6px;
                }}
                .codehilite {{ border-radius: 6px; }}
                blockquote {{ padding: 0 1em; margin-left: 0; }}
                body > table {{
                    border-collapse: collapse; margin: 1rem 0; display: block;
                    width: 100%; overflow: auto;
                }}
                hr {{ border: 0; height: .25em; padding: 0; margin: 24px 0; }}
                ul, ol {{ padding-left: 2em; }}

                /* Theme-specific styles */
                {theme.pygments_css}
                {theme.html_css}
            </style>
        </head>
        <body>
            {html_output}
        </body>
        </html>
        """
        self.preview.setHtml(styled_html)

    def _update_window_title(self):
        """Updates the window title based on the current file path."""
        title = self.config.window_title
        if self.current_file_path:
            title = f"{self.current_file_path} - {title}"
        self.setWindowTitle(title)

    @Slot()
    def _open_file(self):
        """Opens a file dialog to load a Markdown file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Markdown Files (*.md *.markdown);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
                self.current_file_path = file_path
                self._update_window_title()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def _save_logic(self, file_path: str):
        """Contains the core logic for saving text to a file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.current_file_path = file_path
            self._update_window_title()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    @Slot()
    def _save_file(self):
        """Saves the current content to the existing file path."""
        if self.current_file_path:
            self._save_logic(self.current_file_path)
        else:
            self._save_file_as()

    @Slot()
    def _save_file_as(self):
        """Opens a file dialog to save the current content to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File As", "", "Markdown Files (*.md *.markdown);;All Files (*)"
        )
        if file_path:
            self._save_logic(file_path)


def main():
    app = QApplication(sys.argv)
    config = AppConfig()
    viewer = MarkdownViewer(config)
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
