# editable table view for tags:
# insert, remove, edit color
# 

import os
import time

from PyQt5.QtCore import QItemSelectionModel, Qt, QPersistentModelIndex
from PyQt5.QtWidgets import QHeaderView, QTableView, QMenu, QAction

from models.ItemModel import (ItemModel, ItemDelegate,
    NAME, GROUP, TAGS, PATH, DATE, NOTES)

from views.CreateItemDialog import CreateItemDialog

class ItemTableView(QTableView):
    def __init__(self, header, groupView, tagView, parent=None):
        super(ItemTableView, self).__init__(parent)

        self.groupView = groupView
        self.tagView = tagView

        # table style
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setStyleSheet("QHeaderView::section{background:#eee;}")
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setAlternatingRowColors(True)
        # self.resizeColumnsToContents()

        # model
        model = ItemModel(header)
        self.setModel(model)

        # delegate
        delegate = ItemDelegate(self)
        self.setItemDelegate(delegate)

        # context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customContextMenu)

    def setup(self, data=[]):
        '''reset tag table with specified model data'''
        self.model().setup(data)
        self.reset()

    def tags(self):
        '''get all tags data from tags table view'''
        return self.tagView.model().serialize(save=False)

    def rootGroup(self):
        '''get all groups in hierachical structure as defined in group class'''
        return self.groupView.model().serialize(save=False)

    def setupCascadeMenu(self, menu, config, keys=[]):
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
                action = menu.addAction(name, self.slot_moveRows)
                action.key = key

            # create menu if children items exist
            if children:
                sub_menu = menu.addMenu('{0}...'.format(name))
                self.setupCascadeMenu(sub_menu, children, keys)

    def customContextMenu(self, position):
        '''show context menu'''
        rows = self.selectionModel().selectedRows()
        if not len(rows):
            return

        # current group id
        index = self.model().index(rows[0].row(), GROUP)
        key = index.data()

        # init context menu        
        menu = QMenu()
        menu.addAction(self.tr("Edit"), self.slot_editRow)

        move = QMenu(self.tr('Move'))
        groups = self.rootGroup().get('children', [])
        self.setupCascadeMenu(move, groups, [key, 2, 3]) # 2->UNREFERENCED, 3->ALL GROUP
        menu.addMenu(move)        

        menu.addSeparator()
        menu.addAction(self.tr("Remove"), self.slot_removeRows)

        menu.exec_(self.viewport().mapToGlobal(position))

    def slot_appendRow(self):
        '''inset items'''
        dlg = CreateItemDialog()
        if dlg.exec_():
            # insert row at the end of table
            model = self.model()
            num_row = model.rowCount()
            if model.insertRow(num_row):
                path, name = dlg.values()
                c_time = time.strftime('%Y-%m-%d',time.localtime(time.time()))
                # set row values
                row_data = [name, 1, [], path, c_time, '']
                for i, data in enumerate(row_data):
                    index = model.index(num_row, i)
                    model.setData(index, data)

    def slot_moveRows(self):
        '''move selected items to specified group'''
        key = self.sender().key
        rows = self.selectionModel().selectedRows()
        for row in rows:
            index = self.model().index(row.row(), GROUP)
            self.model().setData(index, key)

    def slot_editRow(self):
        '''inset item at the same level with current selected item'''
        pass

    def slot_removeRows(self):
        '''delete selected item'''
        rows = self.selectionModel().selectedRows()
        reply = QMessageBox.question(self, 'Confirm', 
            "Confirm to remove the selected {0} item(s)?".format(len(rows)),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        index_list = []
        for model_index in rows:
            index = QPersistentModelIndex(model_index)
            index_list.append(index)

        model = self.model()
        for index in index_list:
            model.removeRow(index.row())  

    def slot_ungroupItems(self, keys):
        '''move all items with specified groups list to ungrouped'''
        model = self.model()
        for i in range(model.rowCount()):
            index = model.index(i, GROUP)
            if index.data() in keys:
                model.setData(index, 1) # 1->Ungrouped

    def slot_untagItems(self, key):
        '''remove specified tag from tags list of each item'''
        model = self.model()
        for i in range(model.rowCount()):
            index = model.index(i, TAGS)
            keys = index.data()
            if key in keys:
                keys.pop(keys.index(key))
                model.setData(index, keys)