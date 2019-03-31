# editable table view for tags:
# insert, remove, edit color
# 
import random

from PyQt5.QtCore import QItemSelectionModel, QModelIndex, Qt, pyqtSignal
from PyQt5.QtWidgets import (QHeaderView, QTableView, QMenu, QAction, QMessageBox)

from models.TagModel import TagModel, TagDelegate


class TagTableView(QTableView):

    tagCleared = pyqtSignal(int)
    itemsDropped = pyqtSignal(int) # drag items to tag and drop

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
        self.setShowGrid(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(TagModel.COLOR, QHeaderView.ResizeToContents)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        # drop
        self.setDragEnabled(True)
        self.setAcceptDrops(True)

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
        # group at cursor position
        index = self.indexAt(position)
        if not index.isValid():
            return

        # init context menu
        menu = QMenu()
        menu.addAction(self.tr("Create Tag"), self.slot_insertRow)
        menu.addSeparator()

        if not self.sourceModel.isDefaultTag(index):
            menu.addAction(self.tr("Empty Tag"), self.slot_emptyTag)
            menu.addAction(self.tr("Remove Tag"), self.slot_removeRow)

        menu.exec_(self.viewport().mapToGlobal(position))

    # ---------------------------------------------------
    # drag events
    # ---------------------------------------------------
    def dragEnterEvent(self, e):
        '''it is implemented in model, but pay attention that in case
           dragging item from other widget, we must accept this event first.
        '''
        e.accept()

    def dropEvent(self, e):
        '''accept drag event'''
        index = self.indexAt(e.pos())
        if self.sourceModel.canDropMimeData(e.mimeData(), None, -1, -1, index):
            if e.mimeData().hasFormat('tagit-item'):
                key = index.siblingAtColumn(TagModel.KEY).data()
                self.itemsDropped.emit(key)
            elif e.mimeData().hasFormat('tagit-tag'):
                itemData = e.mimeData().data('tagit-tag')
                drag_row = int(str(itemData, encoding='utf-8'))
                self.sourceModel.moveRows(QModelIndex(), drag_row, 1, QModelIndex(), index.row())
            e.accept()
        else:
            e.ignore()


    # ---------------------------------------------------
    # slots
    # ---------------------------------------------------

    @staticmethod
    def randomColor():
        chars = ['1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
        colors =  [chars[random.randint(0,14)] for i in range(6)]
        return "#" + ''.join(colors)

    def slot_finishedEditing(self, index):
        self.closePersistentEditor(index)

    def slot_insertRow(self):
        '''inset item at the same level with current selected item'''
        for index in self.selectionModel().selectedRows(TagModel.KEY):
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
            self.sourceModel.setData(child_color, self.randomColor())
            self.selectionModel().setCurrentIndex(child_name, QItemSelectionModel.ClearAndSelect)

            # enter editing status and quit when finished
            self.openPersistentEditor(child_name)
            editWidget = self.indexWidget(child_name)
            if editWidget:
                editWidget.setFocus()
                editWidget.editingFinished.connect(lambda:self.slot_finishedEditing(child_name))

    def slot_removeRow(self):
        '''delete selected tag'''
        index = self.selectionModel().currentIndex()

        reply = QMessageBox.question(self, 'Confirm', self.tr(
            "Confirm to remove '{0}'?\n"
            "Items with this TAG will not be deleted.".format(index.data())), 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply != QMessageBox.Yes:
            return
        
        key = self.sourceModel.index(index.row(), TagModel.KEY).data()
        if not self.sourceModel.isDefaultTag(index): 
            self.sourceModel.removeRow(index.row())
            # emit removing group signal            
            self.tagCleared.emit(key)

    def slot_emptyTag(self):
        '''remove selected tag from items'''
        index = self.selectionModel().currentIndex()
        key = self.sourceModel.index(index.row(), TagModel.KEY).data()
        self.tagCleared.emit(key)

    def slot_updateCounter(self, items):
        '''update count of items for each group
           :param items: the latest items list
        '''
        self.sourceModel.layoutAboutToBeChanged.emit()
        self.sourceModel.updateItems(items)
        self.sourceModel.layoutChanged.emit() # update display immediately
