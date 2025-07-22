from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QToolTip
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCursor, QPainter, QPalette, QTextCharFormat, QTextFormat
from PySide6.QtCore import QRegularExpression, QSize, Qt, QRect, Signal, QTimer
import re


# MARK: - Syntax Highlighter
class GCodeSyntaxHighlighter(QSyntaxHighlighter):
    """Simple and robust G-code syntax highlighter"""
    
    def __init__(self, document):
        super().__init__(document)
        
        font = QFont('Consolas', 18)
        font.setFixedPitch(True)
        
        # Define all formats
        self.variable_format = QTextCharFormat()
        self.variable_format.setForeground(QColor('#ff8c00'))  # Orange
        self.variable_format.setFont(font)
        
        self.g0_format = QTextCharFormat()
        self.g0_format.setForeground(QColor('#d15e43'))  # Red for rapid
        self.g0_format.setFont(font)
        
        self.g1_format = QTextCharFormat()
        self.g1_format.setForeground(QColor('#286c34'))  # Dark green for linear
        self.g1_format.setFont(font)
        
        self.gm_format = QTextCharFormat()
        self.gm_format.setForeground(QColor('#5e9955'))  # Green for other G/M
        self.gm_format.setFont(font)
        
        self.x_format = QTextCharFormat()
        self.x_format.setForeground(QColor("#c8b723"))  # Green for X
        self.x_format.setFont(font)
        
        self.y_format = QTextCharFormat()
        self.y_format.setForeground(QColor('#009ccb'))  # Blue for Y
        self.y_format.setFont(font)
        
        self.z_format = QTextCharFormat()
        self.z_format.setForeground(QColor('#ff4a7c'))  # Pink for Z
        self.z_format.setFont(font)
        
        self.r_format = QTextCharFormat()
        self.r_format.setForeground(QColor("#6320a1"))  # Purple for R
        self.r_format.setFont(font)
        
        self.i_format = QTextCharFormat()
        self.i_format.setForeground(QColor('#dc2626'))  # Red for I
        self.i_format.setFont(font)
        
        self.j_format = QTextCharFormat()
        self.j_format.setForeground(QColor('#059669'))  # Emerald for J
        self.j_format.setFont(font)
        
        self.fs_format = QTextCharFormat()
        self.fs_format.setForeground(QColor('#e66c00'))  # Orange for F/S
        self.fs_format.setFont(font)
        
        self.line_format = QTextCharFormat()
        self.line_format.setForeground(QColor('#8A817C'))  # Gray for line numbers
        self.line_format.setFont(font)
        
        self.l_var_format = QTextCharFormat()
        self.l_var_format.setForeground(QColor('#BB86FC'))  # Purple for L variables
        self.l_var_format.setFont(font)
        
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor('#B0B8B4'))  # Light gray for comments
        self.comment_format.setFont(font)

    def highlightBlock(self, text):
        """Apply syntax highlighting using simple character-by-character parsing"""
        i = 0
        length = len(text)
        
        while i < length:
            # Skip whitespace
            if text[i].isspace():
                i += 1
                continue
            
            # Handle comments - everything after semicolon
            if text[i] == ';':
                self.setFormat(i, length - i, self.comment_format)
                break
            
            # Handle variables {anything}
            if text[i] == '{':
                start = i
                i += 1
                while i < length and text[i] != '}':
                    i += 1
                if i < length:  # Found closing }
                    i += 1
                    self.setFormat(start, i - start, self.variable_format)
                continue
            
            # Handle letters followed by values
            if text[i].isalpha():
                letter_start = i
                letter = text[i].upper()
                i += 1
                
                # Skip any whitespace after letter
                while i < length and text[i].isspace():
                    i += 1
                
                # Different parsing for L vs other letters
                if letter == 'L':
                    # L variables only have numbers (L1, L24, L245)
                    value_start = i
                    while i < length and text[i].isdigit():
                        i += 1
                    
                    # Only highlight if there are digits after L
                    if i > value_start:
                        self.setFormat(letter_start, i - letter_start, self.l_var_format)
                else:
                    # Other letters can have complex values (numbers, +, -, *, /, L, variables)
                    value_start = i
                    while i < length and (text[i].isdigit() or text[i] in '+-*/.L' or 
                                         (text[i] == '{' and self._find_closing_brace(text, i) != -1)):
                        if text[i] == '{':
                            # Skip entire variable
                            close_pos = self._find_closing_brace(text, i)
                            if close_pos != -1:
                                i = close_pos + 1
                            else:
                                i += 1
                        else:
                            i += 1
                    
                    # Apply formatting based on letter (only if there's a value)
                    total_length = i - letter_start
                    if total_length > 1:
                        if letter == 'G':
                            # Check for specific G codes
                            value_text = text[value_start:i].strip()
                            if value_text in ['0', '00']:
                                self.setFormat(letter_start, total_length, self.g0_format)
                            elif value_text in ['1', '01']:
                                self.setFormat(letter_start, total_length, self.g1_format)
                            else:
                                self.setFormat(letter_start, total_length, self.gm_format)
                        elif letter == 'M':
                            self.setFormat(letter_start, total_length, self.gm_format)
                        elif letter == 'X':
                            self.setFormat(letter_start, total_length, self.x_format)
                        elif letter == 'Y':
                            self.setFormat(letter_start, total_length, self.y_format)
                        elif letter == 'Z':
                            self.setFormat(letter_start, total_length, self.z_format)
                        elif letter == 'R':
                            self.setFormat(letter_start, total_length, self.r_format)
                        elif letter == 'I':
                            self.setFormat(letter_start, total_length, self.i_format)
                        elif letter == 'J':
                            self.setFormat(letter_start, total_length, self.j_format)
                        elif letter in ['F', 'S']:
                            self.setFormat(letter_start, total_length, self.fs_format)
                        elif letter == 'N':
                            self.setFormat(letter_start, total_length, self.line_format)
                continue
            
            # Skip any other character
            i += 1
    
    def _find_closing_brace(self, text, start):
        """Find the closing brace for a variable starting at position start"""
        i = start + 1
        while i < len(text):
            if text[i] == '}':
                return i
            i += 1
        return -1


# MARK: - Line Number Area
class LineNumberArea(QWidget):
    """Line number area with error indication"""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor
        self.setMouseTracking(True)
        self.clickedLineNumber = None

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)
        
    def mousePressEvent(self, event):
        """Handle error tooltip display"""
        if event.button() == Qt.LeftButton:
            block = self.codeEditor.firstVisibleBlock()
            blockNumber = block.blockNumber()
            top = self.codeEditor.blockBoundingGeometry(block).translated(self.codeEditor.contentOffset()).top()
            bottom = top + self.codeEditor.blockBoundingRect(block).height()

            while block.isValid() and top <= event.pos().y():
                if block.isVisible() and bottom >= event.pos().y():
                    lineNumber = blockNumber + 1
                    if lineNumber in self.codeEditor.errors:
                        if self.clickedLineNumber == lineNumber:
                            self.clickedLineNumber = None
                            QToolTip.hideText()
                        else:
                            self.clickedLineNumber = lineNumber
                            errors = self.codeEditor.errors[lineNumber]
                            tooltip_text = "\n".join([f"- {trigger} : {message}" for message, trigger, _ in errors])
                            QToolTip.showText(event.globalPos(), tooltip_text, self)
                    else:
                        self.clickedLineNumber = None
                        QToolTip.hideText()
                    break

                block = block.next()
                top = bottom
                bottom = top + self.codeEditor.blockBoundingRect(block).height()
                blockNumber += 1


# MARK: - Main Editor
class GCodeEditor(QPlainTextEdit):
    """G-code editor with smart highlighting and selection features"""
    
    variables_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.module = parent
        self.lineNumberArea = LineNumberArea(self)
        self.errors = {}
        self.variables = []
        self.selected_text = ""
        self.selection_timer = QTimer()
        self.selection_timer.setSingleShot(True)
        self.selection_timer.timeout.connect(self.highlightSelections)

        # Setup appearance
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor('#1d1f28'))
        palette.setColor(QPalette.Text, QColor('#bec3c9'))
        self.setPalette(palette)
        
        self.setFont(QFont('Consolas', 18))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Setup highlighter
        self.highlighter = GCodeSyntaxHighlighter(self.document())

        # Connect signals
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.onCursorPositionChanged)
        self.textChanged.connect(self.onTextChanged)
        self.selectionChanged.connect(self.onSelectionChanged)
        
        self.updateLineNumberAreaWidth(0)

    # MARK: - Line Numbers
    def lineNumberAreaWidth(self):
        """Calculate line number area width"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num /= 10
            digits += 1
        return 3 + self.fontMetrics().boundingRect('9').width() * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        """Paint line numbers"""
        painter = QPainter(self.lineNumberArea)
        
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                if (blockNumber + 1) in self.errors:
                    painter.fillRect(0, top, self.lineNumberArea.width(), bottom - top, QColor('#ff4a7c'))
                    painter.setPen(QColor('#1d1f28'))
                else:
                    painter.fillRect(0, top, self.lineNumberArea.width(), bottom - top, QColor('#1d1f28'))
                    painter.setPen(QColor('#8b95c0'))
                    
                painter.drawText(0, top, self.lineNumberArea.width() - 2, self.fontMetrics().height(), Qt.AlignRight, number)
                
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    # MARK: - Highlighting
    def onCursorPositionChanged(self):
        self.highlightCurrentLine()
        if hasattr(self.module, 'updatePreviewColors'):
            self.module.updatePreviewColors()

    def highlightCurrentLine(self):
        """Highlight current line"""
        extraSelections = []
        if not self.isReadOnly():
            lineColor = QColor('#00c4fe')
            lineColor.setAlpha(15)
            
            cursor = self.textCursor()
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                block = self.document().findBlock(start)
                while block.isValid() and block.position() <= end:
                    selection = QTextEdit.ExtraSelection()
                    selection.format.setBackground(lineColor)
                    selection.format.setProperty(QTextFormat.FullWidthSelection, True)
                    selection.cursor = QTextCursor(block)
                    extraSelections.append(selection)
                    block = block.next()
            else:
                selection = QTextEdit.ExtraSelection()
                selection.format.setBackground(lineColor)
                selection.format.setProperty(QTextFormat.FullWidthSelection, True)
                selection.cursor = cursor
                selection.cursor.clearSelection()
                extraSelections.append(selection)
        
        self.setExtraSelections(extraSelections)

    def onSelectionChanged(self):
        """Handle selection changes for highlighting occurrences"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText().strip()
            if len(selected) > 1 and selected != self.selected_text:
                self.selected_text = selected
                self.selection_timer.start(300)
        else:
            self.selected_text = ""
            self.highlightCurrentLine()

    def highlightSelections(self):
        """Highlight all occurrences of selected text"""
        if not self.selected_text:
            self.highlightCurrentLine()
            return

        extraSelections = []
        
        # Current line
        lineColor = QColor('#00c4fe')
        lineColor.setAlpha(15)
        cursor = self.textCursor()
        if not cursor.hasSelection():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = cursor
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        # All occurrences
        selectionColor = QColor('#1e3a8a')
        selectionColor.setAlpha(120)
        
        document = self.document()
        cursor = QTextCursor(document)
        
        while True:
            cursor = document.find(self.selected_text, cursor)
            if cursor.isNull():
                break
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(selectionColor)
            selection.cursor = cursor
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def getHighlightedLines(self):
        """Get highlighted line numbers"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            startBlock = self.document().findBlock(start)
            endBlock = self.document().findBlock(end)
            startLineNumber = startBlock.blockNumber() + 1
            endLineNumber = endBlock.blockNumber() + 1
            return list(range(startLineNumber, endLineNumber + 1))
        else:
            return [cursor.blockNumber() + 1]

    # MARK: - Variables
    def onTextChanged(self):
        """Extract variables from text"""
        text = self.toPlainText()
        pattern = r'\{([A-Z]\d+)(?::([0-9.]+))?\}'
        matches = re.findall(pattern, text)
        
        new_variables = []
        seen = set()
        for var_name, default in matches:
            if var_name not in seen:
                new_variables.append((var_name, default))
                seen.add(var_name)
        
        new_variables.sort(key=lambda x: x[0])
        
        if new_variables != self.variables:
            self.variables = new_variables
            self.variables_changed.emit(self.variables)

    def getVariables(self):
        return self.variables.copy()

    def insertVariable(self, variable_name, default_value=None):
        cursor = self.textCursor()
        if default_value:
            cursor.insertText(f"{{{variable_name}:{default_value}}}")
        else:
            cursor.insertText(f"{{{variable_name}}}")

    # MARK: - Utilities
    def setErrors(self, errors):
        self.errors = errors
        self.lineNumberArea.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if hasattr(self.lineNumberArea, 'clickedLineNumber'):
            self.lineNumberArea.clickedLineNumber = None
            QToolTip.hideText()