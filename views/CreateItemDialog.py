# create reference items dialog
# 

import os

from PyQt5.QtWidgets import (QDialog, QFileDialog, QMessageBox, QDialogButtonBox, QPushButton,
    QLabel, QHBoxLayout, QGridLayout, QLineEdit, QGroupBox, QRadioButton)


class CreateItemDialog(QDialog):
    def __init__(self, parent=None):
        super(CreateItemDialog, self).__init__(parent)

        # labels
        fileLabel = QLabel("Source path")
        nameLabel = QLabel("Item name")

        # line edit
        self.refEdit = QLineEdit()
        self.nameEdit = QLineEdit()

        # radio buttons
        self.radio1 = QRadioButton("Directory")
        self.radio2 = QRadioButton("File")
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
        mainLayout = QGridLayout()
        mainLayout.addWidget(fileLabel, 0, 0)
        mainLayout.addWidget(self.refEdit, 0, 1)
        mainLayout.addWidget(browseButton, 0, 2)
        mainLayout.addWidget(nameLabel, 1, 0)
        mainLayout.addWidget(self.nameEdit, 1, 1, 1, 2)
        mainLayout.addWidget(groupBox, 2, 0, 1, 3)
        mainLayout.addWidget(buttons, 3, 2)        
        self.setLayout(mainLayout)

        self.setWindowTitle("Create Reference Item")

    def browse(self):
        if self.radio1.isChecked():
            path = QFileDialog.getExistingDirectory(self, "Select directory...")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select file...")
        if path:            
            self.refEdit.setText(path)
            if not self.nameEdit.text():
                self.nameEdit.setText(os.path.basename(path))

    def accept(self):
        if not self.refEdit.text() or not self.nameEdit.text():
            QMessageBox.warning(self, 'Warning', 'Reference source path and name are required.')
        elif not os.path.exists(self.refEdit.text()):
            QMessageBox.warning(self, 'Warning', 'Referenced source is invalid, please check the path.')
        else:
            super(CreateItemDialog, self).accept()

    def values(self):
        return self.refEdit.text(), self.nameEdit.text()
