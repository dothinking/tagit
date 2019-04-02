# main menu bar and associated toolber for the app
# 
import os
from functools import partial

from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (QApplication, QWidget, QSizePolicy, 
    QFileDialog, QMessageBox, QAction, QLineEdit)

import views.resources


class MainMenu(object):
    """main menu and toolbox for main window"""
    def __init__(self, parent):
        self.mainWindow = parent
        scriptPath = os.path.dirname(os.path.abspath(__file__))
        self._rootPath = os.path.dirname(scriptPath)
        self._styleSheet = None

        self.groupsView = parent.groupsView()
        self.tagsView = parent.tagsView()
        self.itemsView = parent.itemsView()

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
                ('New Item', partial(self.itemsView.slot_appendRows, True), 'Ctrl+I', 'item.png', 'Create item'),
                ('Import Items', partial(self.itemsView.slot_appendRows, False), None, 'import_item.png', 'Import items from selected path'),
                ('Move to Trash', partial(self.itemsView.slot_moveToGroup, self.groupsView.model().TRASH), None, 'del_item.png', 'Soft delete: move items to trash'),
                (),
                ('Open Reference', self.itemsView.slot_navigateTo,'Ctrl+R', 'item_source.png', 'Open attached reference'),
                ('Find Duplicated', self.itemsView.slot_findDuplicatedItems,'Ctrl+D', 'item_duplicated.png', 'Find duplicated items'),
                ('Find Unreferenced', self.itemsView.slot_findUnreferencedItems, 'F5', 'item_unreferenced.png', 'Find unreferenced items'),
                (),
                ('New Group', self.groupsView.slot_insertRow, 'Ctrl+G', 'group.png', 'Create group'),
                ('New Sub-Group', self.groupsView.slot_insertChild, None, 'sub_group.png', 'Create sub-group'),                
                ('Remove Group', self.groupsView.slot_removeRow, None, 'del_group.png','Delete selected group'),
                (),
                ('New Tag', self.tagsView.slot_insertRow, 'Ctrl+T', 'tag.png', 'Create tag'),
                ('Remove Tag', self.tagsView.slot_removeRow, None, 'del_tag','Delete selected tag'),
            ]),
            ('&View', [
                ('Style', self.getStyleSheetNames())
            ]),
            ('&Help',[
                ('About', self.about, None, None, None),
            ])
        ]
        self.mapActions = {} # name -> action/menu

        # menu enabled status
        self.groupsView.selectionModel().selectionChanged.connect(self.refreshMenus)
        self.tagsView.selectionModel().selectionChanged.connect(self.refreshMenus)
        self.mainWindow.tabViews().currentChanged.connect(self.refreshItems) # tabwidget
        QApplication.instance().focusChanged.connect(self.refreshMenus) # all widgets

        # reference item signals
        self.itemsView.selectionModel().selectionChanged.connect(self.slot_selected_item_changed)

        # search items
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText('Searching')
        self.searchEdit.textChanged.connect(self.slot_search)       
        

    # ---------------------------------------------------
    # menus and actions
    # ---------------------------------------------------
    def getStyleSheetNames(self):
        qss_path = '{0}/qss/'.format(self._rootPath)
        # style sheets
        sheets = []
        for filename in os.listdir(qss_path):
            qss_file = os.path.join(qss_path, filename)
            if filename.endswith('.qss') and os.path.isfile(qss_file):
                sheets.append(filename[0:-4])
        # menu items
        res = []
        for name in sheets:
            qss_file = '{0}/{1}.qss'.format(qss_path, name)
            res.append((
                name, 
                partial(self.setStyleSheet, qss_file), 
                None, None, 
                'Apply style sheet {0}.qss under path {1}'.format(name, qss_path)))
        return res

    def createMenus(self):
        '''init menus: common menus + dock widget view menu'''
        # common menu from config dict
        self.createMenusFromConfig()

        # add widget converted menu
        self.dockAction = self.mainWindow.propertyView().toggleViewAction()
        self.dockAction.setIcon(QIcon(':icon/images/edit_item.png'))
        self.dockAction.setToolTip('Edit reference item')
        self.dockAction.setStatusTip('Edit reference item')
        self.mapActions['view'].addAction(self.dockAction)

    def createMenusFromConfig(self, parent=None, config=None):
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
                    self.createMenusFromConfig(action, menu_item[1])
                else:
                    action = self.createAction(*menu_item)
                    parent.addAction(action)

                # add action/menu to dict
                name = menu_item[0].replace('&','').replace('.','').lower().strip()
                self.mapActions[name] = action

    def refreshMenus(self):
        '''set enable status of menu actions'''
        # groups menu
        group_activated = self.groupsView.hasFocus()
        for index in self.groupsView.selectedIndexes():
            group_selected = True
            group_default = self.groupsView.model().isDefaultGroup(index)
            key = index.siblingAtColumn(self.groupsView.model().KEY).data()
            break
        else:
            group_selected = False
            group_default = False
            key = None
        self.mapActions['new group'].setEnabled(group_activated and group_selected and 
                                        (not group_default or key==self.groupsView.model().ALLGROUPS))
        self.mapActions['new sub-group'].setEnabled(group_activated and group_selected and not group_default)
        self.mapActions['remove group'].setEnabled(group_activated and group_selected and not group_default)

        # tags menu
        tag_activated = self.tagsView.hasFocus()
        for index in self.tagsView.selectedIndexes():
            tag_selected = True
            tag_default = self.tagsView.model().isDefaultTag(index)
            break
        else:
            tag_selected = False
            tag_default = False
        self.mapActions['new tag'].setEnabled(tag_activated and tag_selected)
        self.mapActions['remove tag'].setEnabled(tag_activated and tag_selected and not tag_default)

        # items menu
        item_activated = self.itemsView.hasFocus()
        item_selected = not self.itemsView.selectionModel().selection().isEmpty()
        self.mapActions['move to trash'].setEnabled(item_activated and item_selected)
        self.mapActions['open reference'].setEnabled(item_activated and item_selected)

    def createToolBars(self):
        '''create tool bar based on menu items'''
        # files
        self.fileToolBar = self.mainWindow.addToolBar('File')
        self.fileToolBar.addAction(self.mapActions['new'])
        self.fileToolBar.addAction(self.mapActions['open'])
        self.fileToolBar.addAction(self.mapActions['save'])

        # edit
        self.editToolBar = self.mainWindow.addToolBar('Edit')
        self.editToolBar.addAction(self.mapActions['new item'])
        self.editToolBar.addAction(self.mapActions['import items'])
        self.editToolBar.addAction(self.mapActions['move to trash'])
        self.editToolBar.addAction(self.mapActions['open reference'])
        self.editToolBar.addAction(self.mapActions['find duplicated'])
        self.editToolBar.addAction(self.mapActions['find unreferenced'])

        self.editToolBar.addSeparator()
        self.editToolBar.addAction(self.mapActions['new group'])
        self.editToolBar.addAction(self.mapActions['new sub-group'])
        self.editToolBar.addAction(self.mapActions['remove group'])
        
        self.editToolBar.addSeparator()
        self.editToolBar.addAction(self.mapActions['new tag'])
        self.editToolBar.addAction(self.mapActions['remove tag'])

        # view
        self.viewToolBar = self.mainWindow.addToolBar('View')
        self.viewToolBar.addAction(self.dockAction)

        # search
        self.searchToolBar = self.mainWindow.addToolBar('Search')
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.searchToolBar.addWidget(spacer)
        self.searchToolBar.addWidget(self.searchEdit)

    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False):
        # create action from text or convert from dock view        
        action = QAction(text, self.mainWindow)

        if icon:            
            action.setIcon(QIcon(':icon/images/{0}'.format(icon)))

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
            self.itemsView.slot_filterByGroup()
        else:
            self.itemsView.slot_filterByTag()

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

    def setStyleSheet(self, styleSheet):
        if not styleSheet:
            styleSheet = '{0}/qss/{1}'.format(self._rootPath, 'default.qss')
        if os.path.isfile(styleSheet):
            self._styleSheet = styleSheet
            # apply style sheet
            with open(styleSheet, 'r', encoding='utf8') as f:
                qss = f.read()
            QApplication.instance().setStyleSheet(qss)
            # set menu status
            style_name = os.path.basename(styleSheet)[0:-len('.qss')]
            for action in self.mapActions['style'].actions():
                action.setEnabled(True)
            self.mapActions[style_name].setEnabled(False)

    def getCurrentSheetStyle(self):
        '''get current style sheet path'''
        return self._styleSheet

    def about(self):
        QMessageBox.about(self.mainWindow, "About Tagit",
                "Manage your documents with <b>Groups</b> and <b>Tags</b>.")


    # ---------------------------------------------------
    # slots for main widgets
    # ---------------------------------------------------

    def slot_selected_item_changed(self):

        # refresh menu status
        self.refreshMenus()

        # current index
        # if no items are selected,
        # keep orginal item showing but read only in dock
        for index in self.itemsView.selectedIndexes():
            break
        else:
            self.mainWindow.statusBar().showMessage('')
            self.mainWindow.propertyView().widget().setEditorsEnbaled(False)
            return

        # show path of current reference item in status bar
        path_index = index.siblingAtColumn(self.itemsView.sourceModel.PATH)
        path = path_index.data()
        self.mainWindow.statusBar().showMessage(path)

        # show detailed information of current item in dock view
        name, group, note = [index.siblingAtColumn(col).data() 
                    for col in (self.itemsView.sourceModel.NAME,
                        self.itemsView.sourceModel.GROUP,
                        self.itemsView.sourceModel.NOTES)]
        # get group name
        groups = self.groupsView.model().getParentsByKey(group)
        groups = ' | '.join(groups[::-1]) if groups else ''

        # get source index from proxy model index
        # the edit process should apply on source model since proxy model index keeps changing
        # due to reorder when the title is changed
        index = self.itemsView.model().mapToSource(index)
        self.mainWindow.propertyView().widget().setup(index, (name, groups, path, note))

    def slot_search(self):
        regExp = QRegExp(self.searchEdit.text(), Qt.CaseInsensitive, QRegExp.Wildcard)
        self.itemsView.model().setFilterRegExp(regExp)
