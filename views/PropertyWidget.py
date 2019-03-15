# widget displaying and editing basic information of reference item
# name, source, comments
# 

import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (QWidget, QFileDialog, QMessageBox,
    QLabel, QGridLayout, QLineEdit, QTextEdit,
    QFileSystemModel, QTreeView, QToolButton, QMenu, QTabWidget)
from PyQt5.QtGui import QDesktopServices

from models.ItemModel import ItemModel

class PropertyWidget(QWidget):
    def __init__(self, itemView, parent=None):
        super(PropertyWidget, self).__init__(parent)
        self.itemView = itemView
        self.currentRow = None

        # labels
        nameLabel = QLabel("Title")
        fileLabel = QLabel("Source path")

        # line edit
        self.nameEdit = QLineEdit()
        self.pathEdit = QLineEdit()        
        self.noteEdit = QTextEdit()

        # buttons
        browseButton = QToolButton(self)
        browseButton.setToolButtonStyle(Qt.ToolButtonTextOnly)
        browseButton.setArrowType(Qt.DownArrow)
        browseButton.setPopupMode(QToolButton.MenuButtonPopup)
        browseButton.setText('Browse...')
        browseButton.setAutoRaise(True)
        menu = QMenu(self)
        menu.addAction('Browse Path', lambda: self.slot_browse(0))
        menu.addAction('Browse file', lambda: self.slot_browse(1))
        browseButton.setMenu(menu)

        # dir tree
        self.tree = QTreeView()
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)

        model = QFileSystemModel()
        self.tree.setModel(model)        

        # tree and comments tabs
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.tree, "Navigation")
        self.tabWidget.addTab(self.noteEdit, "Comments")

        # set layout
        mainLayout = QGridLayout()
        mainLayout.addWidget(nameLabel, 0, 0) # title
        mainLayout.addWidget(self.nameEdit, 0, 1, 1, 2)
        mainLayout.addWidget(fileLabel, 1, 0) # path
        mainLayout.addWidget(self.pathEdit, 1, 1)
        mainLayout.addWidget(browseButton, 1, 2)        
        mainLayout.addWidget(self.tabWidget, 2, 0, 1, 3)
        self.setLayout(mainLayout)

        # initial status
        self.tabWidget.setTabEnabled(0, False)
        self.pathEdit.setEnabled(False)

        # signals
        self.nameEdit.textChanged.connect(self.slot_saveItem)
        self.pathEdit.textChanged.connect(self.slot_saveItem)
        self.noteEdit.textChanged.connect(self.slot_saveItem)
        self.tree.doubleClicked.connect(self.slot_openSource)

    @staticmethod
    def setTextSafely(textEdit, value):
        textEdit.blockSignals(True)
        textEdit.setText(value)
        textEdit.blockSignals(False)

    def setup(self, index, data):
        '''set data'''
        self.currentRow = index.row() if index else None
        name, path, comments = data
        self.setTextSafely(self.nameEdit, name)
        self.setTextSafely(self.pathEdit, path)
        self.setTextSafely(self.noteEdit, comments)
        self.updateTree(path) # set dir tree status

    def slot_saveItem(self):
        '''save when changed'''        
        editor = self.sender()
        model = self.itemView.model()

        if editor==self.nameEdit:
            name = self.nameEdit.text()
            index = model.index(self.currentRow, ItemModel.NAME)
            model.setData(index, name)
        elif editor==self.pathEdit:
            path = self.pathEdit.text()
            index = model.index(self.currentRow, ItemModel.PATH)
            model.setData(index, path)
        elif editor==self.noteEdit:
            note = self.noteEdit.toPlainText()
            index = model.index(self.currentRow, ItemModel.NOTES)
            model.setData(index, note)

    def slot_openSource(self, index):
        '''open source file/folder from navigation tree'''
        path = self.tree.model().filePath(index)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))


    def slot_browse(self, type):
        if type==0:
            path = QFileDialog.getExistingDirectory(self, "Select directory...")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select file...")
        if path:
            self.pathEdit.setText(path)            
            if not self.nameEdit.text():
                self.nameEdit.setText(os.path.basename(path))

            # update dir tree
            self.updateTree(path)

    def updateTree(self, path):
        '''show dir tree if directory else set disabled'''
        if os.path.isdir(path):
            # set root path
            model = self.tree.model()
            model.setRootPath(path)
            self.tree.setRootIndex(model.index(path))
            # activate tree tab
            self.tabWidget.setTabEnabled(0, True)
            self.tabWidget.setCurrentIndex(0)
        else:
            self.tabWidget.setTabEnabled(0, False)
