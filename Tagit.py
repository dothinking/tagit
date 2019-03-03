from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QAction, 
    QFileDialog, QMainWindow, QMessageBox, QTextEdit, QSplitter)

import os
import pickle

from MainMenu import MainMenu
from GroupTreeView import GroupTreeView


class MainWindow(QMainWindow):

    app_name = 'Tagit'
    app_version = '0.5'
    key_group = 'groups'
    key_tag = 'tags'

    class Settings(object):
        def __init__(self):
            self.setting = QSettings('dothinking', 'tagit')

        def get(self, key, default=None):
            return self.setting.value(key, default)

        def set(self, key, value=None):
            if isinstance(key, str):
                self.setting.setValue(key, value)
            elif isinstance(key, dict):
                for k, v in key:
                    self.setting.setValue(k, v)

    def __init__(self):
        super(MainWindow, self).__init__()

        # whole views
        self.setupViews()

        # menu and toolbox
        self.createMainMenu()

        # init data: last saved database
        self.setting = self.Settings()
        filename = self.setting.get('database')
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
        return self.groupTreeView

    def tagsView(self):
        return self.tagsView

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
                    self._initFromDatabase(data)
                    return ok
                else:
                    ok = False

        # init by default if load data from database failed
        self._database = None
        self._initByDefault()

        return ok

    def _initByDefault(self):
        '''init default data'''
        # set window title      
        self.setTitle()
        self.groupTreeView.setFocus()

        # init groups tree view
        default_groups = [
            {'key':1, 'name':'Imported'},
            {'key':2, 'name':'All Groups'},
        ]
        self.groupTreeView.setup(default_groups, 2)      
        
    def _initFromDatabase(self, data):
        '''load data from database'''
        # set window title      
        self.setTitle()
        self.groupTreeView.setFocus()

        # init groups tree view
        groups = data.get(self.key_group, {}).get('children', [])
        key = self.setting.get('selected_group', 2)
        self.groupTreeView.setup(groups, key)

    def closeEvent(self, event):
        '''default method called when trying to close the app'''
        if self.main_menu.maybeSave():
            event.accept()
        else:
            event.ignore()

    def saveRequired(self):
        '''saving is required if anything is changed'''
        return self.groupTreeView.model().saveRequired()

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
            self._database = filename
            self._writeSettings()
            self.setTitle()
            return True

        return False

    def _writeSettings(self):
        '''config data written in QSetting'''
        # current database
        self.setting.set('database', self._database)

        # current group
        if self.groupTreeView.selectedIndexes():
            index = self.groupTreeView.selectionModel().currentIndex()
            key = index.internalPointer().key()
            self.setting.set('selected_group', key)


    # ----------------------------------------------
    # --------------- user interface ---------------
    # ----------------------------------------------
    def setupViews(self):
        '''create main views'''
        # separate widgets        
        self.groupTreeView = GroupTreeView(['GROUP']) # groups tree view        
        self.tagsView = QWidget() # tags table widget: to do        
        self.textEdit = QTextEdit() # main table widget: to do

        # arranged views
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.groupTreeView, "Groups")
        self.tabWidget.addTab(self.tagsView, "Tags")

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
