# widget displaying and editing basic information of reference item
# name, source, comments
# 

import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (QWidget, QFileDialog, QMessageBox,
    QLabel, QGridLayout, QLineEdit, QTextEdit, QHeaderView,
    QFileSystemModel, QTreeView, QToolButton, QMenu, QTabWidget)
from PyQt5.QtGui import QDesktopServices

from models.ItemModel import ItemModel
from models.GroupModel import GroupModel

class PropertyWidget(QWidget):
    def __init__(self, itemView, parent=None):
        super(PropertyWidget, self).__init__(parent)
        self.itemView = itemView
        self.currentRow = None

        # labels
        nameLabel = QLabel("Title")
        fileLabel = QLabel("Source path")
        groupLabel = QLabel("Group")

        # line edit
        self.nameEdit = QLineEdit()
        self.pathEdit = QLineEdit()
        self.groupEdit = QLineEdit()
        self.noteEdit = QTextEdit()

        # buttons
        self.browseButton = QToolButton(self)
        self.browseButton.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.browseButton.setArrowType(Qt.DownArrow)
        self.browseButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.browseButton.setText('Browse...')
        self.browseButton.setAutoRaise(True)
        menu = QMenu(self)
        menu.addAction('Browse Path', lambda: self.slot_browse(0))
        menu.addAction('Browse file', lambda: self.slot_browse(1))
        self.browseButton.setMenu(menu)

        # dir tree
        self.tree = QTreeView()
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)

        model = QFileSystemModel()
        self.tree.setModel(model)
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)

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
        mainLayout.addWidget(self.browseButton, 1, 2)
        mainLayout.addWidget(groupLabel, 2, 0) # group
        mainLayout.addWidget(self.groupEdit, 2, 1, 1, 2)
        mainLayout.addWidget(self.tabWidget, 3, 0, 1, 3)
        self.setLayout(mainLayout)

        # initial status
        self.tabWidget.setTabEnabled(0, False)
        self.pathEdit.setEnabled(False)
        self.groupEdit.setEnabled(False)

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

    def setEditorsEnbaled(self, enabled=True):
        self.nameEdit.setEnabled(enabled)
        self.noteEdit.setEnabled(enabled)
        self.browseButton.setEnabled(enabled)

    def setup(self, index, data):
        '''set data
           :param index: index of source model, so the following process should 
                    also apply on source model, rather than proxy model by default
        '''
        self.setEditorsEnbaled(True)

        self.currentRow = index.row() if index else None
        name, group, path, comments = data
        self.setTextSafely(self.nameEdit, name)
        self.setTextSafely(self.pathEdit, path)
        self.setTextSafely(self.groupEdit, group)
        self.setTextSafely(self.noteEdit, comments)
        self.updateTree(path) # set dir tree status

    def slot_saveItem(self):
        '''save when changed'''        
        editor = self.sender()

        if editor==self.nameEdit:
            value = self.nameEdit.text()
            col = ItemModel.NAME
        elif editor==self.pathEdit:
            value = self.pathEdit.text()
            col = ItemModel.PATH
        elif editor==self.noteEdit:
            value = self.noteEdit.toPlainText()
            col = ItemModel.NOTES
        else:
            return

        # update values
        model = self.itemView.model().sourceModel()
        index = model.index(self.currentRow, col)
        if index.isValid():
            model.setData(index, value)

        # update unreferenced status if path is updated:
        # move item to UNGROUPED if current group is UNREFERENCED 
        if editor==self.pathEdit:
            group_index = model.index(self.currentRow, ItemModel.GROUP)
            if group_index.data() == GroupModel.UNREFERENCED:
                model.setData(group_index, GroupModel.UNGROUPED)

    def slot_openSource(self, index):
        '''open source file/folder from navigation tree'''
        path = self.tree.model().filePath(index)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))


    def slot_browse(self, path_type):
        if path_type==0:
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
