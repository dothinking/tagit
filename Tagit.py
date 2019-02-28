from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (QAction, QApplication, QWidget, QDockWidget,
        QFileDialog, QMainWindow, QMessageBox, QTextEdit)

from MenuBar import MenuBar
from GroupTreeView import GroupTreeView

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # init window
        self.setWindowTitle("Tagit")
        self.resize(1000,800)
        self.showMaximized()

        # main area
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)

        # group widget
        config = {'key': 0, 'name': 'Group', 'children': [{'key': 18, 'name': '[New Group]', 'children': [{'key': 19, 'name': '[Sub Group]'}]}, {'key': 12, 'name': '[New Group]', 'children': [{'key': 13, 'name': '[Sub Group]', 'children': [{'key': 14, 'name': '[Sub Group]', 'children': [{'key': 15, 'name': '[Sub Group]'}]}, {'key': 16, 'name': '[New Group]'}]}]}]}
        default_groups = [
            {'key':1, 'name':'Imported'},
            {'key':2, 'name':'All Groups'},
            ]
        self.groupTreeView = GroupTreeView(['GROUP'])
        self.groupTreeView.setup(default_groups)
        dock_1 = self.createDockWindows('Groups', self.groupTreeView)

        # tab widget:to do
        self.tagsView = QWidget()
        dock_2 = self.createDockWindows('Tags', self.tagsView)

        self.tabifyDockWidget(dock_1, dock_2)
        dock_1.raise_()

        # menu and toolbox
        MenuBar(self)

        # status bar
        self.createStatusBar()

    def groupsView(self):
        return self.groupTreeView

    def tagsView(self):
        return self.tagsView

    def createStatusBar(self):
        self.statusBar().showMessage("Ready")

    def createDockWindows(self, text, widget):
        dock = QDockWidget(text, self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)                
        dock.setWidget(widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        # self.viewMenu.addAction(dock.toggleViewAction())
        return dock

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
