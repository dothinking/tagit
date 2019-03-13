# main menu bar and associated toolber for the app
# 
from PyQt5.QtCore import QFileInfo
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (QApplication, QFileDialog, QMessageBox, QAction)


class MainMenu(object):
    """main menu and toolbox for main window"""
    def __init__(self, parent):
        self.mainWindow = parent

        # menu: (text, [sub actions])
        # action: (text, slot, shortcut, icon, tips)
        # separator: ()        
        self.raw_menus = [
            ('&File',[
                ('&New', self.new, QKeySequence.New, 'new.png', 'Create new Tagit project'),
                ('&Open ...', self.open, QKeySequence.Open, 'open.png', 'Open existing project'),
                ('&Save', self.save, QKeySequence.Save, 'save.png', 'Save current project'),
                ('Save as ...', self.saveAs, None, 'Save as new a project'),
                (),
                ('E&xit', self.mainWindow.close, 'Ctrl+Q'),
            ]),
            ('&Edit',[
                ('New Item', self.mainWindow.itemsView().slot_appendRow,'Ctrl+I', 'item.png', 'Create item'),
                ('Edit Item', None, None, 'edit_item.png', 'Edit item'),
                ('Remove Item', self.mainWindow.itemsView().slot_removeRows, None, 'del_item.png', 'Delete item'),
                (),
                ('Open Reference', self.mainWindow.itemsView().slot_navigateTo,'Ctrl+R', 'item_attachment.png', 'Open attached reference'),
                ('Comments', self.mainWindow.itemsView().slot_navigateTo,'Ctrl+M', 'item_comments.png', 'Edit/view comments on current item'),
                (),
                ('New Group', self.mainWindow.groupsView().slot_insertRow, 'Ctrl+G', 'group.png', 'Create group'),
                ('New Sub-Group', self.mainWindow.groupsView().slot_insertChild, None, 'sub_group.png', 'Create sub-group'),                
                ('Remove Group', self.mainWindow.groupsView().slot_removeRow, None, 'del_group.png','Delete selected group'),
                (),
                ('New Tag', self.mainWindow.tagsView().slot_insertRow,'Ctrl+T', 'tag.png', 'Create tag'),
                ('Remove Tag', self.mainWindow.tagsView().slot_removeRow, None, 'del_tag','Delete selected tag'),
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
        path = QFileInfo(__file__).absolutePath()
        self.img_path = QFileInfo(path).absolutePath() + '/images/'

        # menu status
        self.mainWindow.groupsView().selectionModel().selectionChanged.connect(self.refreshMenus)
        self.mainWindow.tagsView().selectionModel().selectionChanged.connect(self.refreshMenus)
        self.mainWindow.itemsView().selectionModel().selectionChanged.connect(self.refreshMenus)
        QApplication.instance().focusChanged.connect(self.refreshMenus)

        # filter items
        self.mainWindow.groupsView().selectionModel().selectionChanged.connect(self.mainWindow.itemsView().slot_filterByGroup)
        self.mainWindow.tagsView().selectionModel().selectionChanged.connect(self.mainWindow.itemsView().slot_filterByTag)
        self.mainWindow.groupsView().parent().currentChanged.connect(self.refreshItems) # tabwidget

        # edit items triggered by removing group or tag
        self.mainWindow.groupsView().groupRemoved.connect(self.mainWindow.itemsView().slot_ungroupItems)
        self.mainWindow.tagsView().tagRemoved.connect(self.mainWindow.itemsView().slot_untagItems)

        # item counter for group, tag
        self.mainWindow.itemsView().itemsChanged.connect(self.mainWindow.groupsView().slot_updateCounter)
        self.mainWindow.itemsView().itemsChanged.connect(self.mainWindow.tagsView().slot_updateCounter)

        # show item properties: source path, detail property
        self.mainWindow.itemsView().selectionModel().selectionChanged.connect(self.slot_showReferencePath)
        self.mainWindow.itemsView().selectionModel().selectionChanged.connect(self.slot_showProperties)

        # switch from comment view to item view
        self.mainWindow.groupsView().clicked.connect(lambda: self.mainWindow.itemsView().parent().setCurrentIndex(0))
        self.mainWindow.tagsView().clicked.connect(lambda: self.mainWindow.itemsView().parent().setCurrentIndex(0))
        


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
        # groups menu
        group_activated = self.mainWindow.groupsView().hasFocus()
        group_selected = not self.mainWindow.groupsView().selectionModel().selection().isEmpty()
        group_default = False
        if group_selected:
            i_index = self.mainWindow.groupsView().selectionModel().currentIndex()
            group_default = self.mainWindow.groupsView().model().isDefaultItem(i_index)
        self.mapActions['new group'].setEnabled(group_activated and group_selected)
        self.mapActions['new sub-group'].setEnabled(group_activated and group_selected and not group_default)
        self.mapActions['remove group'].setEnabled(group_activated and group_selected and not group_default)

        # tags menu
        tag_activated = self.mainWindow.tagsView().hasFocus()
        tag_selected = not self.mainWindow.tagsView().selectionModel().selection().isEmpty()
        tag_default = False
        if tag_selected:
            i_index = self.mainWindow.tagsView().selectionModel().currentIndex()
            tag_default = self.mainWindow.tagsView().model().isDefaultItem(i_index)
        self.mapActions['new tag'].setEnabled(tag_activated and tag_selected)
        self.mapActions['remove tag'].setEnabled(tag_activated and tag_selected and not tag_default)

        # items menu
        item_activated = self.mainWindow.itemsView().hasFocus()
        item_selected = not self.mainWindow.itemsView().selectionModel().selection().isEmpty()
        self.mapActions['edit item'].setEnabled(item_activated and item_selected)
        self.mapActions['remove item'].setEnabled(item_activated and item_selected)
        self.mapActions['open reference'].setEnabled(item_activated and item_selected)
        self.mapActions['comments'].setEnabled(item_activated and item_selected)

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
        self.editToolBar.addAction(self.mapActions['open reference'])
        self.editToolBar.addAction(self.mapActions['comments'])
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
            action.setIcon(QIcon(self.img_path+icon))
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

    def refreshItems(self, index):
        if index==0:
            self.mainWindow.itemsView().slot_filterByGroup()
        else:
            self.mainWindow.itemsView().slot_filterByTag()

    def new(self):
        if self.maybeSave():
            self.mainWindow.initData()
            self.refreshMenus()

    def open(self):
        if self.maybeSave():
            '''open existing project'''
            filename, _ = QFileDialog.getOpenFileName(self.mainWindow, 
                'Open Prpject...', '', 
                'Tagit Project (*.dat);;All Files (*)')
            if not filename:
                return

            if not self.mainWindow.initData(filename):
                QMessageBox.critical(None, "Error", "Invalid database for Tagit project.")

            self.refreshMenus()

    def save(self):
        '''save current database'''
        filename = self.mainWindow.database()
        if filename:
            return self.mainWindow.serialize(filename)
        else:
            self.saveAs()

    def saveAs(self):
        '''save current data as new database'''
        filename, _ = QFileDialog.getSaveFileName(self.mainWindow, 
            'Save Prpject as...', '', 
            'Tagit Project (*.dat);;All Files (*)')
        if filename:
            return self.mainWindow.serialize(filename)
        else:
            return False

    def maybeSave(self):
        '''show message dialog if the application is not saved'''
        if self.mainWindow.saveRequired():
            ret = QMessageBox.warning(self.mainWindow, "Application",
                    "Current project has been modified.\nDo you want to save your changes?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

            if ret == QMessageBox.Save:                
                return self.save()

            if ret == QMessageBox.Cancel:
                return False

        return True

    def slot_showReferencePath(self, selection):
        '''show reference path in status bar when selected'''
        for index in selection.indexes():
            path_index = index.siblingAtColumn(self.mainWindow.itemsView().sourceModel.PATH)
            break
        else:
            return
        self.mainWindow.statusBar().showMessage(path_index.data())

    def slot_showProperties(self, selection):
        '''show detailed information the current item'''
        for index in selection.indexes():
            name_index = index.siblingAtColumn(self.mainWindow.itemsView().sourceModel.NAME)
            break
        else:
            return
        self.mainWindow.propertyView().widget().setText(name_index.data())