# editable table view for tags:
# insert, remove, edit color
# 

from PyQt5.QtCore import QItemSelectionModel, Qt, pyqtSignal
from PyQt5.QtWidgets import (QColorDialog,QHeaderView, QTableView, QMenu, QAction, QMessageBox)
from PyQt5.QtGui import QColor

from models.TagModel import TagModel, TagDelegate


class TagTableView(QTableView):

    tagRemoved = pyqtSignal(int)

    def __init__(self, header, parent=None):
        super(TagTableView, self).__init__(parent)

        # model
        self.sourceModel = TagModel(header)
        self.setModel(self.sourceModel)

        # delegate
        delegate = TagDelegate(self)
        self.setItemDelegate(delegate)

        # context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customContextMenu)

        # table style
        self.initTableStyle()

    def initTableStyle(self):
        # table style
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(TagModel.COLOR, QHeaderView.ResizeToContents)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self.setSelectionMode(QTableView.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectRows)

        self.setAlternatingRowColors(True)
      
    def setup(self, data=[], selected_key=-1):
        '''reset tag table with specified model data,
           and set the row with specified key as selected
        '''
        self.sourceModel.setup(data)
        self.reset()
        # set selected item
        index = self.sourceModel.getIndexByKey(selected_key)        
        if index.isValid():
            self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

    def customContextMenu(self, position):
        '''show context menu'''
        indexes = self.selectedIndexes()
        if not len(indexes):
            return

        # init context menu
        menu = QMenu()
        menu.addAction(self.tr("Create Tag"), self.slot_insertRow)
        menu.addSeparator()
        act_rv = menu.addAction(self.tr("Remove Tag"), self.slot_removeRow)

        # set status
        s = not self.sourceModel.isDefaultItem(indexes[0])
        act_rv.setEnabled(s)

        menu.exec_(self.viewport().mapToGlobal(position))

    def slot_finishedEditing(self, index):
        self.closePersistentEditor(index)

    def slot_insertRow(self):
        '''inset item at the same level with current selected item'''
        for index in self.selectionModel().selectedRows(self.sourceModel.KEY):
            break
        else:
            return

        row = index.row() + 1
        if self.sourceModel.insertRow(row, index.parent()):
            child_key = self.sourceModel.index(row, TagModel.KEY)
            child_name = self.sourceModel.index(row, TagModel.NAME)
            child_color = self.sourceModel.index(row, TagModel.COLOR)

            # set default data
            self.sourceModel.setData(child_key, self.sourceModel.nextKey())
            self.sourceModel.setData(child_name, 'New Tag')
            self.sourceModel.setData(child_color, '#000000')
            self.selectionModel().setCurrentIndex(child_name, QItemSelectionModel.ClearAndSelect)

            # enter editing status and quit when finished
            self.openPersistentEditor(child_name)
            editWidget = self.indexWidget(child_name)
            if editWidget:
                editWidget.setFocus()
                editWidget.editingFinished.connect(lambda:self.slot_finishedEditing(child_name))


    def slot_removeRow(self):
        '''delete selected item'''
        index = self.selectionModel().currentIndex()

        reply = QMessageBox.question(self, 'Confirm', self.tr(
            "Confirm to remove '{0}'?\n"
            "Items with this TAG will not be deleted.".format(index.data())), 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply != QMessageBox.Yes:
            return
        
        key = self.sourceModel.index(index.row(), TagModel.KEY).data()
        if not self.sourceModel.isDefaultItem(index): 
            self.sourceModel.removeRow(index.row())
            # emit removing group signal            
            self.tagRemoved.emit(key)

    def slot_updateCounter(self, items):
        '''update count of items for each group
           :param items: the latest items list
        '''
        self.sourceModel.updateItems(items)
        self.sourceModel.layoutChanged.emit() # update display immediately