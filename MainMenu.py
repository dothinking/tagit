# main menu bar and associated toolber for the app
# 
from PyQt5.QtCore import QFileInfo
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QAction)


class MainMenu(object):
    """main menu and toolbox for main window"""
    def __init__(self, parent):
        self.mainWindow = parent

        # menu: (text, [sub actions])
        # action: (text, slot, shortcut, icon, tips)
        # separator: ()
        img_path = QFileInfo(__file__).absolutePath() + '/images/'
        self.raw_menus = [
            ('&File',[
                ('&New', self.mainWindow.reset, QKeySequence.New, img_path+'new.png', 'Create new Tagit project'),
                ('&Open ...', self.open, QKeySequence.Open, img_path+'open.png', 'Open existing project'),
                ('&Save', self.save, QKeySequence.Save, img_path+'save.png', 'Save current project'),
                ('Save as ...', self.saveAs, None, 'Save as new a project'),
                (),
                ('E&xit', self.mainWindow.close, 'Ctrl+Q'),
            ]),
            ('&Edit',[
                ('New Item', None,'Ctrl+I', None, None),
                ('Edit Item', None, None, None, None),
                ('Remove Item', None, None, None, None),
                (),
                ('New Group',self.mainWindow.groupsView().slot_insertRow,'Ctrl+G',None,None),
                ('New Sub-Group',self.mainWindow.groupsView().slot_insertChild,None,None,None),                
                ('Remove Group',self.mainWindow.groupsView().slot_removeRow,None,None,'Delete currently selected group'),
                (),
                ('New Tag',None,'Ctrl+T',None,None),
                ('Remove Tag',None,None,None,'Delete currently selected tag'),
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
        self.mapActions = {} # name -> action/menu

        # menu status
        self.mainWindow.groupsView().selectionModel().selectionChanged.connect(self.refreshMenus)
        self.mainWindow.tabWidget.currentChanged.connect(self.refreshMenus)

    def createMenus(self, parent=None, config=None):
        '''init menu
           :param config: data for creating menus, e.g.
                  - menu: (text, [sub actions])
                  - action: (text, slot, shortcut, icon, tips)
                  - separator: ()
        '''
        # set default params
        if not parent:
            parent = self.mainWindow.menuBar()
            config = self.raw_menus

        for menu_item in config:
            if not menu_item or not menu_item[0]: # separator
                parent.addSeparator()
            else:
                if isinstance(menu_item[1], list): # menu
                    action = parent.addMenu(menu_item[0])
                    self.createMenus(action, menu_item[1])
                else:
                    action = self.createAction(*menu_item)
                    parent.addAction(action)

                # add action/menu to dict
                name = menu_item[0].replace('&','').replace('.','').lower().strip()
                self.mapActions[name] = action

    def refreshMenus(self):
        '''set enable status of menu actions'''
        group_activated = self.mainWindow.tabWidget.currentIndex() == 0
        group_selected = not self.mainWindow.groupsView().selectionModel().selection().isEmpty()
        group_default = False
        if group_selected:
            i_index = self.mainWindow.groupsView().selectionModel().currentIndex()
            group_default = self.mainWindow.groupsView().model().isDefaultItem(i_index)
        self.mapActions['new group'].setEnabled(group_activated and group_selected)
        self.mapActions['new sub-group'].setEnabled(group_activated and group_selected and not group_default)
        self.mapActions['remove group'].setEnabled(group_activated and group_selected and not group_default)

    def createToolBars(self):
        '''create tool bar based on menu items'''
        # files
        self.fileToolBar = self.mainWindow.addToolBar("File")
        self.fileToolBar.addAction(self.mapActions['new'])
        self.fileToolBar.addAction(self.mapActions['open'])
        self.fileToolBar.addAction(self.mapActions['save'])

        self.editToolBar = self.mainWindow.addToolBar("Edit")
        self.editToolBar.addAction(self.mapActions['new item'])
        self.editToolBar.addAction(self.mapActions['edit item'])
        self.editToolBar.addAction(self.mapActions['remove item'])
        self.editToolBar.addSeparator()
        self.editToolBar.addAction(self.mapActions['new group'])
        self.editToolBar.addAction(self.mapActions['new sub-group'])
        self.editToolBar.addAction(self.mapActions['remove group'])
        self.editToolBar.addSeparator()
        self.editToolBar.addAction(self.mapActions['new tag'])
        self.editToolBar.addAction(self.mapActions['remove tag'])



    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False):
        action = QAction(text, self.mainWindow)
        if icon:
            action.setIcon(QIcon(icon))
        if shortcut:
            action.setShortcut(shortcut)
        if tip:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action

    def open(self):
        '''open existing project'''
        filename, _ = QFileDialog.getOpenFileName(self.mainWindow, 
            'Open Prpject...', '', 
            'Tagit Project (*.dat);;All Files (*)')
        if not filename:
            return

        if not self.mainWindow.loadDatabase(filename):
            QMessageBox.critical(None, "Error", "Invalid database for Tagit project.")

    def save(self):
        '''save current database'''
        filename = self.mainWindow.database()
        if filename:
            self.mainWindow.serialize(filename)
        else:
            self.saveAs()

    def saveAs(self):
        '''save current data as new database'''
        filename, _ = QFileDialog.getSaveFileName(self.mainWindow, 
            'Save Prpject as...', '', 
            'Tagit Project (*.dat);;All Files (*)')
        if filename:
            self.mainWindow.serialize(filename)