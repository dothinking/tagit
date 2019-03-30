# create reference items dialog
# 

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QFileDialog, QMessageBox, QDialogButtonBox, 
    QPushButton,QLabel, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit, 
    QGroupBox, QRadioButton, QTableWidget, QHeaderView, QTableWidgetItem)


class SingleItemDialog(QDialog):
    def __init__(self, parent=None):
        super(SingleItemDialog, self).__init__(parent)

        # labels
        fileLabel = QLabel("Source path")
        nameLabel = QLabel("Item name")

        # line edit
        self.refEdit = QLineEdit()
        self.refEdit.setEnabled(False)
        self.nameEdit = QLineEdit()

        # radio buttons
        self.radio1 = QRadioButton("Directory")
        self.radio2 = QRadioButton("File")        
        self.radio1.toggled.connect(self.clearContent)
        self.radio2.toggled.connect(self.clearContent)
        self.radio1.setChecked(True)

        hbox = QHBoxLayout()
        hbox.addWidget(self.radio1)
        hbox.addWidget(self.radio2)

        groupBox = QGroupBox("Referenced type")
        groupBox.setLayout(hbox)

        # buttons
        browseButton = QPushButton("&Browse...")
        browseButton.clicked.connect(self.browse)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # set layout
        gridLayout = QGridLayout()
        gridLayout.addWidget(fileLabel, 0, 0)
        gridLayout.addWidget(self.refEdit, 0, 1)
        gridLayout.addWidget(browseButton, 0, 2)
        gridLayout.addWidget(nameLabel, 1, 0)
        gridLayout.addWidget(self.nameEdit, 1, 1, 1, 2)
        gridLayout.addWidget(groupBox, 2, 0, 1, 3)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(gridLayout)
        mainLayout.addWidget(buttons)
        self.setLayout(mainLayout)

        self.setWindowTitle("Create Reference Item")
        self.setFixedWidth(500)

    def browse(self):
        if self.radio1.isChecked():
            path = QFileDialog.getExistingDirectory(self, "Select directory...")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select file...")
        if path:            
            self.refEdit.setText(path)
            if not self.nameEdit.text():
                self.nameEdit.setText(os.path.basename(path))

    def clearContent(self):
        self.refEdit.setText('')
        self.nameEdit.setText('')

    def accept(self):
        '''default methos if button OK is clicked'''
        if not self.refEdit.text() or not self.nameEdit.text():
            QMessageBox.warning(self, 'Warning', 'Reference source path and name are required.')
        elif not os.path.exists(self.refEdit.text()):
            QMessageBox.warning(self, 'Warning', 'Referenced source is invalid, please check the path.')
        else:
            super(SingleItemDialog, self).accept()

    def values(self):
        return self.refEdit.text(), self.nameEdit.text()


class MultiItemsDialog(QDialog):
    def __init__(self, parent=None):
        super(MultiItemsDialog, self).__init__(parent)

        # path edit
        label = QLabel("Root Path:")
        self.rootPathEdit = QLineEdit()
        self.rootPathEdit.setEnabled(False)

        # sub-path table
        self.createFilesTable()

        # buttons
        browseButton = QPushButton("&Browse...")
        browseButton.clicked.connect(self.browse)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # layouts
        gridLayout = QGridLayout()
        gridLayout.addWidget(label, 0, 0)
        gridLayout.addWidget(self.rootPathEdit, 0, 1)
        gridLayout.addWidget(browseButton, 0, 2)
        gridLayout.addWidget(self.filesTable, 1, 0, 1, 3)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(gridLayout)
        mainLayout.addWidget(buttons)

        self.setLayout(mainLayout)

        self.setWindowTitle("Import Reference Items")
        self.setFixedWidth(500)

    def createFilesTable(self):
        self.filesTable = QTableWidget(0, 2)
        self.filesTable.setHorizontalHeaderLabels(("Checked", "Source Path"))
        self.filesTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.filesTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.filesTable.setSelectionBehavior(QTableWidget.SelectRows)        
        self.filesTable.verticalHeader().hide()


    def browse(self):
        root = QFileDialog.getExistingDirectory(self, "Select directory...")
        if not root:
            return

        # set root path
        if not root.endswith('/'):
            root += '/'
        self.rootPathEdit.setText(root)
        paths = [os.path.join(root, filename) for filename in os.listdir(root) if not filename.startswith('.')]

        # show in table
        self.filesTable.setRowCount(0) # clear table
        for i, path in enumerate(paths):
            self.filesTable.insertRow(i)
            check = QTableWidgetItem()
            check.setCheckState(Qt.Checked);
            self.filesTable.setItem(i, 0, check)
            self.filesTable.setItem(i, 1, QTableWidgetItem(path))

    def accept(self):
        '''default methos if button OK is clicked'''
        if not self.values():
            QMessageBox.warning(self, 'Warning', 'Source path to be imported is empty.')
        else:
            super(MultiItemsDialog, self).accept()

    def values(self):
        num = self.filesTable.rowCount()
        paths = [self.filesTable.item(i, 1).text() for i in range(num)
            if self.filesTable.item(i, 0).checkState() == Qt.Checked]
        return paths