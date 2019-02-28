from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (QAction, QApplication, QWidget, QDockWidget,
        QFileDialog, QMainWindow, QMessageBox, QTextEdit)

import os
import pickle

from MainMenu import MainMenu
from GroupTreeView import GroupTreeView


class MainWindow(QMainWindow):

    app_name = 'Tagit'
    app_version = '0.5'
    key_group = 'groups'
    key_tag = 'tags'

    def __init__(self):
        super(MainWindow, self).__init__()        

        # main area
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)

        # left widgets: groups and tags
        self.createLeftWidgets()

        # menu and toolbox
        self.createMainMenu()

        # init data: last saved database
        self.reset()
        self.loadDatabase()

        # status bar
        self.createStatusBar()

        # window
        title = self._database if self._database else 'untitled project.dat'
        self.setWindowTitle("Tagit - {0}".format(title))
        self.resize(1000,800)
        self.showMaximized()

    # --------------- properties ---------------
    def groupsView(self):
        return self.groupTreeView

    def tagsView(self):
        return self.tagsView

    def database(self):
        return self._database 

    # --------------- data operation ---------------
    def reset(self):
        '''clear data'''
        self._database = None
        default_groups = [
            {'key':1, 'name':'Imported'},
            {'key':2, 'name':'All Groups'},
        ]
        self.groupTreeView.setup(default_groups)

    def loadDatabase(self, filename=None):
        '''load data from specified file,
           or the latest saved database
        '''
        # try to get database from local setting
        if not filename:
            setting = QSettings('dothinking', 'tagit')
            filename = setting.value('database', None)

        if not filename or not os.path.exists(filename):
            return False

        # load database
        try:
            with open(str(filename), 'rb') as f:
                data = pickle.load(f)
        except Exception as e:
            return False

        # check
        if not self.app_name in data:
            return False

        # init groups
        groups = data.get(self.key_group, {}).get('children', [])
        self.groupTreeView.setup(groups)

        # set current database
        self._database = filename

        return True

    def serialize(self, filename):
        '''save project data to database'''        
        data = {
            self.app_name: self.app_version,
            self.key_group: self.groupTreeView.model().serialize()
        }
        try:
            with open(filename, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            QMessageBox.critical(None, "Error", "Could not save current project to\n {0}.".format(filename))
        else:
            QSettings('dothinking', 'tagit').setValue('database', filename)
            # set current database
            self._database = filename

    # --------------- user interface ---------------
    def createLeftWidgets(self):
        '''init groups and tags widgets'''
        # group widget        
        self.groupTreeView = GroupTreeView(['GROUP'])        
        dock_1 = self.createDockWindows('Groups', self.groupTreeView)

        # tab widget:to do
        self.tagsView = QWidget()
        dock_2 = self.createDockWindows('Tags', self.tagsView)

        self.tabifyDockWidget(dock_1, dock_2)
        dock_1.raise_()

    def createMainMenu(self):
        '''main menu'''
        main_menu = MainMenu(self)
        # menu: (text, [sub actions])
        # action: (text, slot, shortcut, icon, tips)
        # separator: ()
        menus = [
            ('&File',[
                ('&New Project', self.reset, QKeySequence.New),
                ('&Open Project', lambda:main_menu.open(), QKeySequence.Open),
                ('&Save', lambda:main_menu.save(), QKeySequence.Save),
                ('Save as',lambda:main_menu.saveAs()),
                (),
                ('E&xit', self.close, 'Ctrl+Q'),
            ]),
            ('&Group',[
                ('New Group',self.groupTreeView.slot_insertRow,None,None,None),
                ('Create Sub-Group',self.groupTreeView.slot_insertChild,None,None,None),
                (),
                ('Remove Group',self.groupTreeView.slot_removeRow,None,None,None),
            ]),
            ('&View', []),
            ('&Help',[
                ('About',None,None,None,None),
                ('Test', [
                    ('Test1',None,None,None,'hiaha, test1'),
                    ('Test2',None,None,None,'hiaha, test2'),
                ])
            ])
        ]
        
        main_menu.createMenus(self.menuBar(), menus)

    def createStatusBar(self):
        if self._database:
            msg = 'loading database successfully - {0}'.format(self._database)
        else:
            msg = 'New database'
        self.statusBar().showMessage(msg)

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
