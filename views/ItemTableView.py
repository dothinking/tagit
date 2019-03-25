# editable table view for tags:
# insert, remove, edit color
# 

import os
import time
from functools import partial

from PyQt5.QtCore import QItemSelectionModel, Qt, QPersistentModelIndex, QModelIndex, pyqtSignal, QUrl
from PyQt5.QtWidgets import QHeaderView, QTableView, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon, QColor, QDesktopServices

from models.ItemModel import ItemModel, ItemDelegate, SortFilterProxyModel

from views.CreateItemDialog import SingleItemDialog, MultiItemsDialog

class ItemTableView(QTableView):

    itemsChanged = pyqtSignal(list) # signal for group/tag to update counting

    def __init__(self, header, groupView, tagView, parent=None):
        super(ItemTableView, self).__init__(parent)

        self.setObjectName("itemTable") # for qss

        self.groupView = groupView
        self.tagView = tagView        

        # source model
        self.sourceModel = ItemModel(header)

        # proxy model
        self.proxyModel = SortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.proxyModel.setSourceModel(self.sourceModel)
        self.setModel(self.proxyModel)

        # delegate
        delegate = ItemDelegate(self)
        self.setItemDelegate(delegate)

        # context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customContextMenu)

        # SIGNALS AND SLOTS BETWEEN ITEM AND (GROUP,TAG)
        self.setupSignalsAndSlots()

        # table style
        self.initTableStyle()

    def setupSignalsAndSlots(self):
        # reset items when remove group/tag
        self.groupView.groupRemoved.connect(self.slot_ungroupItems)
        self.tagView.tagRemoved.connect(self.slot_untagItems)       

        # update group/tag counter when items are changed
        # emit signal to request updating group counter
        self.sourceModel.dataChanged.connect(
            lambda: self.itemsChanged.emit(self.sourceModel.serialize(save=False))
            )
        self.sourceModel.layoutChanged.connect(
            lambda: self.itemsChanged.emit(self.sourceModel.serialize(save=False))
            )
        self.itemsChanged.connect(self.groupView.slot_updateCounter)
        self.itemsChanged.connect(self.tagView.slot_updateCounter)

        # filter items by group/tags
        self.groupView.selectionModel().selectionChanged.connect(self.slot_filterByGroup)
        self.tagView.selectionModel().selectionChanged.connect(self.slot_filterByTag)

        # drag items to add group/tag
        self.groupView.itemsDropped.connect(self.slot_moveGroup)
        self.tagView.itemsDropped.connect(self.slot_attachTag)

        # doule click to open source path
        self.doubleClicked.connect(self.slot_navigateTo)

    def initTableStyle(self):
        # table style
        self.setShowGrid(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(ItemModel.DATE, QHeaderView.ResizeToContents)        
        self.verticalHeader().hide()

        self.setSelectionBehavior(QTableView.SelectRows)
        self.setAlternatingRowColors(True)

        # drag
        self.setDragEnabled(True)

        # not editable
        self.setEditTriggers(QTableView.NoEditTriggers)

        # sorting
        self.setSortingEnabled(True)
        self.sortByColumn(ItemModel.NAME, Qt.AscendingOrder)
        

    def setup(self, data=[]):
        '''reset tag table with specified model data'''
        self.sourceModel.setup(data)
        self.reset()
        self.slot_filterByGroup()

    def tags(self):
        '''get all tags data from tags table view'''
        return self.tagView.model().serialize(save=False)

    def rootGroup(self):
        '''get all groups in hierachical structure as defined in group class'''
        return self.groupView.model().serialize(save=False)

    # ---------------------------------------------------
    # context menus
    # ---------------------------------------------------
    def setupCascadeGroupMenu(self, menu, config, keys=[]):
        '''create cascade menu according to specified groups
           :param menu: parent menu
           :param config: groups data for menu items
           :param key: groups id exclued from creating menu item, e.g. current group, ALL GROUP
        '''
        for item in config:
            # group information
            name, key, children = item

            # create menu action, but skip specified groups
            action = menu.addAction(name, partial(self.slot_moveGroup, key))

            if key in keys:
                action.setEnabled(False)

            # create menu if children items exist
            if children:
                sub_menu = menu.addMenu('{0}...'.format(name))
                self.setupCascadeGroupMenu(sub_menu, children, keys)

    def setupTagsMenu(self, menu, addTagMenu, delTagMenu, currentTags):
        '''attach oe detach tags for current item'''
        KEY, NAME, COLOR = self.tagView.model().KEY, self.tagView.model().NAME, self.tagView.model().COLOR

        for tag in self.tags():

            # set icon with bg-color same as tag
            pixmap = QPixmap(12, 12)
            pixmap.fill(QColor(tag[COLOR]))

            # tags not attached yet -> to be attached
            if tag[KEY] not in currentTags:
                action = addTagMenu.addAction(QIcon(pixmap), self.tr(tag[NAME]), partial(self.slot_attachTag, tag[KEY]))
            # current tags -> to be removed
            else:
                action = delTagMenu.addAction(QIcon(pixmap), self.tr(tag[NAME]), partial(self.slot_removeTag, tag[KEY]))

        if addTagMenu.actions():
            menu.addMenu(addTagMenu)

        if delTagMenu.actions() and not self.tagView.model().NOTAG in currentTags:
            menu.addMenu(delTagMenu)

    def customContextMenu(self, position):
        '''show context menu'''

        # menus on items
        menu = QMenu()

        indexes = self.selectionModel().selectedRows(ItemModel.GROUP)

        # refresh
        menu.addAction(self.tr("Refresh"), self.sourceModel.refresh)

        if indexes: # actions on index
            # group of current item
            gid = indexes[0].data()

            # tags of current item
            tids = self.selectionModel().selectedRows(ItemModel.TAGS)[0].data()

            if gid != self.groupView.model().UNREFERENCED:
                # open source path
                menu.addAction(self.tr("Open Reference"), self.slot_navigateTo)
                menu.addSeparator()

                # menus on groups            
                move = QMenu(self.tr('Move to Group'))
                groups = self.rootGroup()[self.groupView.model().CHILDREN]
                
                self.setupCascadeGroupMenu(move, groups, [gid, 
                        self.groupView.model().UNREFERENCED,
                        self.groupView.model().ALLGROUPS]) # 2->UNREFERENCED, 3->ALL GROUP
                menu.addMenu(move)
                menu.addSeparator()

            # menus on tags            
            addTag = QMenu(self.tr("Attach Tags"))
            delTag = QMenu(self.tr("Remove Tags"))
            self.setupTagsMenu(menu, addTag, delTag, tids)
            menu.addSeparator()

            # remove items            
            menu.addAction(self.tr("Remove Item"), self.slot_removeRows)
            
        else:
            # create item
            menu.addAction(self.tr("New Item"), partial(self.slot_appendRows, True))
            menu.addAction(self.tr("Import Items"), partial(self.slot_appendRows, False))

        menu.exec_(self.viewport().mapToGlobal(position))

    
    # ---------------------------------------------------
    # slots
    # ---------------------------------------------------
    def slot_appendRows(self, single=True):
        '''inset single item if single=True, otherwise insert items by MultiTiemsDialog'''
        # current gruop
        indexes = self.groupView.selectionModel().selectedRows(self.groupView.model().KEY)
        group = self.groupView.model().UNGROUPED # UNGROUP
        if indexes and indexes[0].isValid():
            group = indexes[0].data()

        # set default group as UNGROUP, though current group is UNREFERENCED(2) or ALL GROUPS(3)
        if group in [self.groupView.model().UNREFERENCED,self.groupView.model().ALLGROUPS]:
            group = self.groupView.model().UNGROUPED

        # add items        
        dlg = SingleItemDialog() if single else MultiItemsDialog()
        if dlg.exec_():
            # collect items data
            c_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))
            if single:
                path, name = dlg.values()
                rows = [(name, group, [self.tagView.model().NOTAG], path, c_time, '')]
            else:
                rows = [(os.path.basename(path), group, [self.tagView.model().NOTAG], path, c_time, '') for path in dlg.values()]

            # append to item table
            num_row = self.sourceModel.rowCount()
            if self.sourceModel.insertRows(num_row, len(rows)):
                for i, row in enumerate(rows):
                    for j, col in enumerate(row):
                        index = self.sourceModel.index(num_row+i, j)
                        self.sourceModel.setData(index, col)

    def slot_navigateTo(self):
        '''open current item'''
        index = self.selectionModel().currentIndex()
        if not index.isValid():
            return
        path = self.proxyModel.index(index.row(), ItemModel.PATH).data()
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def slot_removeRows(self):
        '''delete selected item'''
        rows = self.selectionModel().selectedRows()
        reply = QMessageBox.question(self, 'Confirm', 
            "Confirm to remove the selected {0} item(s)?".format(len(rows)),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        index_list = []
        for proxy_index in rows: # proxy index
            source_index = self.proxyModel.mapToSource(proxy_index)
            index = QPersistentModelIndex(source_index)
            index_list.append(index)

        for index in index_list:
            self.sourceModel.removeRow(index.row())

        # emit signal to request updating group/tag counter
        if index_list:
            self.itemsChanged.emit(self.sourceModel.serialize(save=False))

    def slot_moveGroup(self, key):
        '''move selected items to specified group'''
        indexes = self.selectionModel().selectedRows(ItemModel.GROUP)
        # ATTENTION: performing the moving action in descent order,
        # try not to destroy the default index of the model.
        # otherwise, multi-items could not be moved correctly.
        for index in indexes[::-1]:
            self.proxyModel.setData(index, key)

    def slot_attachTag(self, key):
        '''add tag to current item'''
        indexes = self.selectionModel().selectedRows(ItemModel.TAGS)
        NOTAG = self.tagView.model().NOTAG

        self.proxyModel.layoutAboutToBeChanged.emit()

        if key == NOTAG:
            for index in indexes[::-1]:
                # if key=NOTAG, remove all other tags
                self.proxyModel.setData(index, [NOTAG])
        else:
            for index in indexes[::-1]: # ATTENTION
                keys = index.data()

                # remove NOTAG first
                if NOTAG in keys:
                    keys.pop(keys.index(NOTAG))

                # then attach target tag
                if key not in keys:
                    keys.append(key)
                    self.proxyModel.setData(index, keys)

        self.proxyModel.layoutChanged.emit()

    def slot_removeTag(self, key):
        '''delete tag from currently selected item'''
        indexes = self.selectionModel().selectedRows(ItemModel.TAGS)
        for index in indexes[::-1]: # ATTENTION
            keys = index.data()
            if key in keys:
                keys.pop(keys.index(key))
                # if item tags are empty, set NOTAG then
                if not keys:
                    keys = [self.tagView.model().NOTAG]
                self.proxyModel.setData(index, keys)

    def slot_ungroupItems(self, keys):
        '''move all items with specified groups list to ungrouped'''
        for i in range(self.sourceModel.rowCount()):
            index = self.sourceModel.index(i, ItemModel.GROUP)
            if index.data() in keys:
                self.sourceModel.setData(index, self.groupView.model().UNGROUPED) # Ungrouped        

    def slot_untagItems(self, key):
        '''remove specified tag from all items'''
        for i in range(self.sourceModel.rowCount()):
            index = self.sourceModel.index(i, ItemModel.TAGS)
            keys = index.data()
            if key in keys:
                keys.pop(keys.index(key))
                # if item tags are empty, set NOTAG then
                if not keys:
                    keys = [self.tagView.model().NOTAG]
                self.sourceModel.setData(index, keys)        

    def slot_filterByGroup(self):
        '''triggered by group selection changed'''
        for groupIndex in self.groupView.selectedIndexes():
            break
        else:
            return

        # get selected group
        groups = groupIndex.internalPointer().keys()

        # set filter for column GROUP
        self.proxyModel.setGroupFilter(groups)
        self.proxyModel.setFilterKeyColumn(ItemModel.GROUP)

        # clear previous selection
        self.selectionModel().clear() 

    def slot_filterByTag(self):
        '''triggered by tag selection changed'''
        for tagIndex in self.tagView.selectedIndexes():
            break
        else:
            return

        # selected tag key
        tag = tagIndex.siblingAtColumn(self.tagView.model().KEY).data()

        # set filter for column GROUP
        self.proxyModel.setTagFilter(tag)
        self.proxyModel.setFilterKeyColumn(ItemModel.TAGS)

        # clear previous selection
        self.selectionModel().clear() 
