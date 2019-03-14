from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import (QApplication, QWidget, QTabWidget, QAction, QDockWidget,
    QFileDialog, QMainWindow, QMessageBox, QSplitter, QTextEdit, QStackedWidget)

import os
import pickle

from views.MainMenu import MainMenu
from views.GroupTreeView import GroupTreeView
from views.TagTableView import TagTableView
from views.ItemTableView import ItemTableView

from models.GroupModel import GroupModel
from models.TagModel import TagModel
from models.ItemModel import ItemModel

class MainWindow(QMainWindow):

    APP_NAME = 'Tagit'
    APP_VERSION = '0.5'
    KEY_GROUP = 'groups'
    KEY_TAG = 'tags'
    KEY_ITEM = 'items'
    KEY_SETTING = 'settings'

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

    def itemsView(self):
        return self.itemsTableView

    def propertyView(self):
        return self.dockProperty

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
                if self.APP_NAME in data: # valid database
                    self._database = database
                    self._initData(data)
                    return ok
                else:
                    ok = False

        # init by default if load data from database failed
        self._database = None
        self._initData()

        return ok
        
    def _initData(self, data={}):
        '''load data from database'''
        # set window title      
        self.setTitle()
        self.groupsTreeView.setFocus()

        # get data
        if self.KEY_GROUP in data:
            groups = data.get(self.KEY_GROUP)[GroupModel.CHILDREN]
        else:
            groups = []
        tags = data.get(self.KEY_TAG, [])
        items = data.get(self.KEY_ITEM, [])

        selected_group = data.get(self.KEY_SETTING, {}).get('selected_group', GroupModel.ALLGROUPS)
        selected_tag = data.get(self.KEY_SETTING, {}).get('selected_tag', TagModel.NOTAG)

        # init groups tree view 
        self.groupsTreeView.setup(groups, selected_group)
        self.groupsTreeView.model().updateItems(items)
        self.groupsTreeView.setColumnHidden(GroupModel.KEY, True)

        # init tags table view
        self.tagsTableView.setup(tags, selected_tag)
        self.tagsTableView.model().updateItems(items)
        self.tagsTableView.setColumnHidden(TagModel.KEY, True) # hide first column -> key

        # init items table view
        self.itemsTableView.setup(items)
        self.itemsTableView.setColumnHidden(ItemModel.GROUP, True)
        self.itemsTableView.setColumnHidden(ItemModel.TAGS, True)
        self.itemsTableView.setColumnHidden(ItemModel.PATH, True)
        self.itemsTableView.setColumnHidden(ItemModel.NOTES, True)

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
            or self.itemsTableView.model().sourceModel().saveRequired()
            )

    def serialize(self, filename):
        '''save project data to database'''
        # current group
        if self.groupsTreeView.selectedIndexes():
            name_index = self.groupsTreeView.selectedIndexes()[0]
            selected_group = name_index.siblingAtColumn(GroupModel.KEY).data()
        else:
            selected_group = self.groupsTreeView.model().ALLGROUPS

        # current tag
        if self.tagsTableView.selectedIndexes():
            name_index = self.tagsTableView.selectedIndexes()[0]
            selected_tag = name_index.siblingAtColumn(TagModel.KEY).data()
        else:
            selected_tag = TagModel.NOTAG

        # collect all data
        data = {
            self.APP_NAME   : self.APP_VERSION,
            self.KEY_GROUP  : self.groupsTreeView.model().serialize(),
            self.KEY_TAG    : self.tagsTableView.model().serialize(),
            self.KEY_ITEM   : self.itemsTableView.model().sourceModel().serialize(),
            self.KEY_SETTING: {'selected_group': selected_group,
                'selected_tag': selected_tag},
        }
        print(data)

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

        # left widgets
        tabWidget = QTabWidget()
        self.groupsTreeView = GroupTreeView(['Group', 'Key'], tabWidget) # groups tree view        
        self.tagsTableView = TagTableView(['KEY', 'TAG', 'COLOR'], tabWidget) # tags table view
        tabWidget.addTab(self.groupsTreeView, "Groups")
        tabWidget.addTab(self.tagsTableView, "Tags")

        # central widgets: reference item table widget
        headers = ['Item Title', 'Group', 'Tags', 'Path', 'Create Date', 'Notes']
        self.itemsTableView = ItemTableView(headers, self.groupsTreeView, self.tagsTableView) 

        # arranged views
        splitter = QSplitter()        
        splitter.addWidget(tabWidget)
        splitter.addWidget(self.itemsTableView)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        # dock widgets
        self.dockProperty = QDockWidget(self.tr("Properties"),self)
        self.dockProperty.setFeatures(QDockWidget.DockWidgetClosable)  
        self.dockProperty.setAllowedAreas(Qt.RightDockWidgetArea)
        self.dockProperty.setWidget(QTextEdit())
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockProperty)


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
