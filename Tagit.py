from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QAction, 
    QFileDialog, QMainWindow, QMessageBox, QTextEdit, QSplitter)

import os
import pickle

from MainMenu import MainMenu
from GroupTreeView import GroupTreeView
from TagTableView import TagTableView


class MainWindow(QMainWindow):

    app_name = 'Tagit'
    app_version = '0.5'
    key_group = 'groups'
    key_tag = 'tags'
    key_setting = 'settings'

    def __init__(self):
        super(MainWindow, self).__init__()

        # whole views
        self.setupViews()

        # menu and toolbox
        self.createMainMenu()

        # init data: last saved database
        self.setting = QSettings('dothinking', 'tagit')
        filename = self.setting.value('database')
        self.initData(filename)

        # status bar
        self.createStatusBar()

        # window
        self.setTitle()
        self.resize(1000,800)
        # self.showMaximized()

    # ----------------------------------------------
    # --------------- properties ---------------
    # ----------------------------------------------
    def groupsView(self):
        return self.groupsTreeView

    def tagsView(self):
        return self.tagsTableView

    def database(self):
        return self._database 

    # ----------------------------------------------
    # --------------- data operation ---------------
    # ----------------------------------------------
    def initData(self, database=None):
        '''load data from specified database, init default if failed.
           two failing situations:
           - database is not specified -> init by default and return true
           - specified but is invalid  -> init by default but return false
        '''
        default_groups = [
            {'key':1, 'name':'Imported'},
            {'key':2, 'name':'All Groups'},
        ]
        default_tags = [[1, 'No Tag', '#000000']]

        ok = True
        if database and os.path.exists(database):
            # load database
            try:
                with open(database, 'rb') as f:
                    data = pickle.load(f)
            except Exception as e:
                ok = False
            else:
                if self.app_name in data: # valid database
                    self._database = database
                    self._initData(default_groups, default_tags, data)
                    return ok
                else:
                    ok = False

        # init by default if load data from database failed
        self._database = None
        self._initData(default_groups, default_tags)

        return ok
        
    def _initData(self, default_groups, default_tags, data={}):
        '''load data from database'''
        # set window title      
        self.setTitle()
        self.groupsTreeView.setFocus()

        # init groups tree view
        groups = data.get(self.key_group, {}).get('children', default_groups)
        key = data.get(self.key_setting, {}).get('selected_group', 2)
        self.groupsTreeView.setup(groups, key)

        # init tags table view
        tags = data.get(self.key_tag, [[1, 'No Tag', '#000000']])
        key = data.get(self.key_setting, {}).get('selected_tag', 1)
        self.tagsTableView.setup(tags, key)

    def closeEvent(self, event):
        '''default method called when trying to close the app'''
        if self.main_menu.maybeSave():
            event.accept()
        else:
            event.ignore()

    def saveRequired(self):
        '''saving is required if anything is changed'''
        return (
            self.groupsTreeView.model().saveRequired() 
            or self.tagsTableView.model().saveRequired()
            )

    def serialize(self, filename):
        '''save project data to database'''
        # current group
        if self.groupsTreeView.selectedIndexes():
            index = self.groupsTreeView.selectionModel().currentIndex()
            selected_group = index.internalPointer().key()
        else:
            selected_group = -1

        # current tag
        if self.tagsTableView.selectedIndexes():
            index = self.tagsTableView.selectionModel().currentIndex()
            selected_tag = self.tagsTableView.model().getKeyByIndex(index)
        else:
            selected_tag = -1

        # collect all data
        data = {
            self.app_name: self.app_version,
            self.key_group: self.groupsTreeView.model().serialize(),
            self.key_tag: self.tagsTableView.model().serialize(),
            self.key_setting: {'selected_group': selected_group,
                'selected_tag': selected_tag},
        }
        # print(data)

        # dump pickle file
        try:
            with open(filename, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            QMessageBox.critical(None, "Error", "Could not save current project to\n {0}.".format(filename))
        else:
            self._database = filename
            self.setting.setValue('database', filename)
            self.setTitle()
            self.statusBar().showMessage('File saved.')
            return True

        return False

    # ----------------------------------------------
    # --------------- user interface ---------------
    # ----------------------------------------------
    def setupViews(self):
        '''create main views'''
        # separate widgets        
        self.groupsTreeView = GroupTreeView(['GROUP']) # groups tree view        
        self.tagsTableView = TagTableView(['Tag', 'Color']) # tags table view
        self.textEdit = QTextEdit() # main table widget: to do

        # arranged views
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.groupsTreeView, "Groups")
        self.tabWidget.addTab(self.tagsTableView, "Tags")

        splitter = QSplitter()        
        splitter.addWidget(self.tabWidget)
        splitter.addWidget(self.textEdit)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

    def createMainMenu(self):
        '''main menu'''
        self.main_menu = MainMenu(self)        
        # create menu items
        self.main_menu.createMenus()
        # set menu enable status 
        self.main_menu.refreshMenus()
        # toolbar
        self.main_menu.createToolBars()

    def setTitle(self):
        '''set window title'''
        title = self._database if self._database else 'untitled.dat'
        self.setWindowTitle("Tagit - {0}".format(title))

    def createStatusBar(self):
        if self._database:
            msg = 'loading database successfully - {0}'.format(self._database)
        else:
            msg = 'New database'
        self.statusBar().showMessage(msg)


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
