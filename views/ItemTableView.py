# editable table view for tags:
# insert, remove, edit color
# 

import os
import time

from PyQt5.QtCore import QItemSelectionModel, Qt, QPersistentModelIndex, QModelIndex, pyqtSignal, QUrl
from PyQt5.QtWidgets import QHeaderView, QTableView, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon, QColor, QDesktopServices

from models.ItemModel import ItemModel, ItemDelegate, SortFilterProxyModel

from views.CreateItemDialog import CreateItemDialog

class ItemTableView(QTableView):

    itemsChanged = pyqtSignal(list) # signal for group/tag to update counting

    def __init__(self, header, groupView, tagView, parent=None):
        super(ItemTableView, self).__init__(parent)

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

        # update group/tag counter when items are changed
        # emit signal to request updating group counter
        self.sourceModel.dataChanged.connect(
            lambda: self.itemsChanged.emit(self.sourceModel.serialize(save=False))
            )

        # table style
        self.initTableStyle()

    def initTableStyle(self):
        # table style
        self.horizontalHeader().setStyleSheet("QHeaderView::section{background:#eee;}")
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(ItemModel.DATE, QHeaderView.ResizeToContents)        
        self.verticalHeader().hide()

        self.setSelectionBehavior(QTableView.SelectRows)
        self.setAlternatingRowColors(True)

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

    def setupCascadeGroupMenu(self, menu, config, keys=[]):
        '''create cascade menu according to specified groups
           :param menu: parent menu
           :param config: groups data for menu items
           :param key: groups id exclued from creating menu item, e.g. current group, ALL GROUP
        '''
        for item in config:
            # group information
            key = item.get('key', 1)
            name = item.get('name')
            children = item.get('children', [])

            # create menu action, but skip current group
            if key not in keys:                
                action = menu.addAction(name, self.slot_moveGroup)
                action.key = key

            # create menu if children items exist
            if children:
                sub_menu = menu.addMenu('{0}...'.format(name))
                self.setupCascadeGroupMenu(sub_menu, children, keys)

    def setupTagsMenu(self, menu, addTagMenu, delTagMenu, currentTags):
        '''attach oe detach tags for current item'''        
        for tag in self.tags():
            # UNTAGGED
            if tag[0]<0:
                continue

            # set icon with bg-color same as tag
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(tag[2]))

            # tags not attached yet -> to be attached
            if tag[0] not in currentTags:
                action = addTagMenu.addAction(QIcon(pixmap), self.tr(tag[1]), self.slot_attachTag)
            # current tags -> to be removed
            else:
                action = delTagMenu.addAction(QIcon(pixmap), self.tr(tag[1]), self.slot_removeTag)

            # set tag key for slot
            action.key = tag[0]

        if addTagMenu.actions():
            menu.addMenu(addTagMenu)

        if delTagMenu.actions():
            menu.addMenu(delTagMenu)

    def customContextMenu(self, position):
        '''show context menu'''
        indexes = self.selectionModel().selectedRows(ItemModel.GROUP)
        if not indexes:
            return

        # group of current item
        gid = indexes[0].data()

        # tags of current item
        tids = self.selectionModel().selectedRows(ItemModel.TAGS)[0].data()

        # menus on items
        menu = QMenu()

        # edit item
        menu.addAction(self.tr("New Item"), self.slot_appendRow)
        menu.addAction(self.tr("Edit Item"), self.slot_editRow)
        menu.addAction(self.tr("Remove Item"), self.slot_removeRows)

        menu.addSeparator()
        menu.addAction(self.tr("Open Reference"), self.slot_navigateTo)
        menu.addAction(self.tr("Comments"), self.slot_navigateTo)

        # menus on groups
        menu.addSeparator()
        move = QMenu(self.tr('Move to Group'))
        groups = self.rootGroup().get('children', [])
        
        self.setupCascadeGroupMenu(move, groups, [gid, 2, 3]) # 2->UNREFERENCED, 3->ALL GROUP
        menu.addMenu(move)

        # menus on tags
        menu.addSeparator()
        addTag = QMenu(self.tr("Attach Tags"))
        delTag = QMenu(self.tr("Remove Tags"))
        self.setupTagsMenu(menu, addTag, delTag, tids)

        menu.exec_(self.viewport().mapToGlobal(position))

    def slot_appendRow(self):
        '''inset items'''
        # current gruop
        indexes = self.groupView.selectionModel().selectedRows()
        group = 1 # UNGROUP
        if indexes and indexes[0].isValid():
            group = indexes[0].internalPointer().key()
        # set default group as UNGROUP, though current group is UNREFERENCED(2) or ALL GROUPS(3)
        if group in [2,3]:
            group = 1

        # add item
        dlg = CreateItemDialog()
        if dlg.exec_():
            # insert row at the end of table
            num_row = self.sourceModel.rowCount()
            if self.sourceModel.insertRow(num_row):
                path, name = dlg.values()
                c_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))
                # set row values
                row_data = [name, group, [], path, c_time, '']
                for i, data in enumerate(row_data):
                    index = self.sourceModel.index(num_row, i)
                    self.sourceModel.setData(index, data)

    def slot_editRow(self):
        pass


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

    def slot_moveGroup(self):
        '''move selected items to specified group'''
        key = self.sender().key
        indexes = self.selectionModel().selectedRows(ItemModel.GROUP)
        # ATTENTION: performing the moving action in descent order,
        # try not to destroy the default index of the model.
        # otherwise, multi-items could not be moved correctly.
        for index in indexes[::-1]:
            self.proxyModel.setData(index, key)

    def slot_attachTag(self):
        '''add tag to current item'''
        key = self.sender().key
        indexes = self.selectionModel().selectedRows(ItemModel.TAGS)
        for index in indexes[::-1]: # ATTENTION
            keys = index.data()
            if key not in keys:
                keys.append(key)
                self.proxyModel.setData(index, keys)

    def slot_removeTag(self):
        '''delete tag from current item'''
        key = self.sender().key
        indexes = self.selectionModel().selectedRows(ItemModel.TAGS)
        for index in indexes[::-1]: # ATTENTION
            keys = index.data()
            if key in keys:
                keys.pop(keys.index(key))
                self.proxyModel.setData(index, keys)

    def slot_ungroupItems(self, keys):
        '''move all items with specified groups list to ungrouped'''
        for i in range(self.sourceModel.rowCount()):
            index = self.sourceModel.index(i, ItemModel.GROUP)
            if index.data() in keys:
                self.sourceModel.setData(index, 1) # 1->Ungrouped        

    def slot_untagItems(self, key):
        '''remove specified tag from tags list of each item'''
        for i in range(self.sourceModel.rowCount()):
            index = self.sourceModel.index(i, ItemModel.TAGS)
            keys = index.data()
            if key in keys:
                keys.pop(keys.index(key))
                self.sourceModel.setData(index, keys)        

    def slot_filterByGroup(self):
        '''triggered by group selection changed'''
        # get selected group
        indexes = self.groupView.selectionModel().selectedRows()
        if indexes and indexes[0].isValid():
            groups = indexes[0].internalPointer().keys()
        else:
            groups = None       

        # set filter for column GROUP
        self.proxyModel.setGroupFilter(groups)
        self.proxyModel.setFilterKeyColumn(ItemModel.GROUP)

    def slot_filterByTag(self):
        '''triggered by tag selection changed'''
        # get selected tag
        indexes = self.tagView.selectionModel().selectedIndexes()
        if indexes and indexes[0].isValid():
            tag = self.tagView.model().index(indexes[0].row(), 0).data()
        else:
            tag = None       

        # set filter for column GROUP
        self.proxyModel.setTagFilter(tag)
        self.proxyModel.setFilterKeyColumn(ItemModel.TAGS)