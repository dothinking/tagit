# editable table view for tags:
# insert, remove, edit color
# 

from PyQt5.QtCore import QItemSelectionModel, Qt
from PyQt5.QtWidgets import (QColorDialog,QHeaderView, QTableView, QMenu, QAction, QMessageBox)
from PyQt5.QtGui import QColor

from models.ItemModel import ItemModel, TagDelegate


class ItemTableView(QTableView):
    def __init__(self, header, parent=None):
        super(ItemTableView, self).__init__(parent)

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
        # delegate = TagDelegate(self)
        # self.setItemDelegate(delegate)

        # context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customContextMenu)


    def setup(self, data=[]):
        '''reset tag table with specified model data'''
        self.model().setup(data)
        self.reset()

    def customContextMenu(self, position):
        '''show context menu'''
        indexes = self.selectedIndexes()
        if not len(indexes):
            return

        # init context menu
        menu = QMenu()
        menu.addAction(self.tr("Create Item"), self.slot_appendRow)
        menu.addAction(self.tr("Edit Item"), self.slot_editRow)        
        menu.addSeparator()
        menu.addAction(self.tr("Remove Item"), self.slot_removeRows)

        menu.exec_(self.viewport().mapToGlobal(position))


    def slot_appendRow(self):
        '''inset item at the same level with current selected item'''
        index = self.selectionModel().currentIndex()
        model = self.model()

        row = index.row() + 1
        if model.insertRow(row, index.parent()):
            child_key = model.index(row, 0, index.parent())
            child_name = model.index(row, 1, index.parent())
            child_color = model.index(row, 2, index.parent())

            # set default data
            model.setData(child_key, model.nextKey())
            model.setData(child_name, 'New Tag')
            model.setData(child_color, '#000000')
            self.selectionModel().setCurrentIndex(child_name, QItemSelectionModel.ClearAndSelect)

    def slot_editRow(self):
        '''inset item at the same level with current selected item'''
        index = self.selectionModel().currentIndex()
        model = self.model()

        row = index.row() + 1
        if model.insertRow(row, index.parent()):
            child_key = model.index(row, 0, index.parent())
            child_name = model.index(row, 1, index.parent())
            child_color = model.index(row, 2, index.parent())

            # set default data
            model.setData(child_key, model.nextKey())
            model.setData(child_name, 'New Tag')
            model.setData(child_color, '#000000')
            self.selectionModel().setCurrentIndex(child_name, QItemSelectionModel.ClearAndSelect)


    def slot_removeRows(self):
        '''delete selected item'''
        index = self.selectionModel().currentIndex()
        reply = QMessageBox.question(self, 'Confirm', self.tr(
            "Confirm to remove '{0}'?\n"
            "Items with this TAG will not be deleted.".format(index.data())), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        
        model = self.model()
        if not model.isDefaultItem(index): 
            model.removeRow(index.row(), index.parent())