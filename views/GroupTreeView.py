# editable tree view for groups:
# append, insert child, remove, edit text
# 

from PyQt5.QtCore import (QItemSelectionModel, Qt, pyqtSignal)
from PyQt5.QtWidgets import (QTreeView, QMenu, QAction, QMessageBox)

from models.GroupModel import GroupModel

class GroupTreeView(QTreeView):

    groupCleared = pyqtSignal(list)
    emptyTrash = pyqtSignal(int)
    itemsDropped = pyqtSignal(int) # drag items to group and drop

    def __init__(self, header, parent=None):
        ''':param headers: header of tree, e.g. ('name', 'value')
        '''
        super(GroupTreeView, self).__init__(parent)

        # model
        self.sourceModel = GroupModel(header)
        self.setModel(self.sourceModel)

        # context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customContextMenu)

        # table style
        self.initTableStyle()
        

    def initTableStyle(self):
        # tree style
        self.resizeColumnToContents(0)
        self.header().hide()
        self.expandAll()

        # drop
        self.setAcceptDrops(True)

        self.setSelectionMode(QTreeView.SingleSelection)
        self.setSelectionBehavior(QTreeView.SelectRows)


    def setup(self, data=[], selected_key=GroupModel.ALLGROUPS):
        '''reset tree with specified model data,
           and set the item with specified key as selected
        '''
        self.sourceModel.setup(data)       

        # refresh tree view to activate the model setting
        self.reset()
        self.expandAll()

        # set selected item        
        index = self.sourceModel.getIndexByKey(selected_key)
        if index.isValid():
            self.selectionModel().setCurrentIndex(index, QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
            self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

    def selectedIndex(self):
        '''get currently selected index'''
        for index in self.selectedIndexes():
            return index
        else:
            QMessageBox.warning(self, 'Warning', self.tr("Please select a group first"))
            return None

    def customContextMenu(self, position):
        '''show context menu'''

        # group at cursor position
        index = self.indexAt(position)
        if not index.isValid():
            return

        # init context menu
        menu = QMenu()
        if not self.sourceModel.isDefaultGroup(index):
            menu.addAction(self.tr("Create Group"), self.slot_insertRow)
            menu.addAction(self.tr("Create Sub-Group"), self.slot_insertChild)
            menu.addSeparator()
            menu.addAction(self.tr("Empty Group"), self.slot_emptyGroup)
            menu.addAction(self.tr("Remove Group"), self.slot_removeRow)
        else:
            key = index.siblingAtColumn(GroupModel.KEY).data()

            if key==GroupModel.ALLGROUPS:
                menu.addAction(self.tr("Create Group"), self.slot_insertRow)

            if key==GroupModel.TRASH:
                trash = menu.addAction(self.tr("Empty Trash"), lambda: self.emptyTrash.emit(key))
                # no items in trash
                if '(' not in index.siblingAtColumn(GroupModel.NAME).data():
                    trash.setEnabled(False)

        if menu.actions():
            menu.exec_(self.viewport().mapToGlobal(position))

    # ---------------------------------------------------
    # drag events
    # ---------------------------------------------------
    def dragEnterEvent(self, e):
        '''it is implemented in model, but pay attention that in case
           dragging item from other widget, we must accept this event first.
        '''
        e.acceptProposedAction()

    def dropEvent(self, e):
        '''accept drag event'''
        index = self.indexAt(e.pos())
        if self.sourceModel.canDropMimeData(e.mimeData(), None, -1, -1, index):            
            key = index.siblingAtColumn(GroupModel.KEY).data()
            self.itemsDropped.emit(key)
            e.accept()
        else:
            e.ignore()
          

    # ---------------------------------------------------
    # slots
    # ---------------------------------------------------
    def slot_insertChild(self):
        '''insert child item under current selected item'''
        index = self.selectedIndex()
        if not index:
            return

        # could not insert sub-items to default items
        if self.sourceModel.isDefaultGroup(index):
            return

        # insert
        if self.sourceModel.insertRow(0, index):
            child_name = self.sourceModel.index(0, GroupModel.NAME, index)
            child_key = self.sourceModel.index(0, GroupModel.KEY, index)
            self.sourceModel.setData(child_name, "[Sub Group]")
            self.sourceModel.setData(child_key, self.sourceModel.nextKey())            
            self.selectionModel().setCurrentIndex(child_name, QItemSelectionModel.ClearAndSelect)

    def slot_insertRow(self):
        '''inset item at the same level with current selected item'''
        index = self.selectedIndex()
        if not index:
            return

        # for default items, only ALLGROUPS is allowable to append siblings
        key = index.siblingAtColumn(GroupModel.KEY).data()
        if 1<key<10:
            return

        # could not prepend item to default items
        row = index.row() + 1
        if self.sourceModel.insertRow(row, index.parent()):
            child_name = self.sourceModel.index(row, GroupModel.NAME, index.parent())
            child_key = self.sourceModel.index(row, GroupModel.KEY, index.parent())            
            self.sourceModel.setData(child_name, "[New Group]")
            self.sourceModel.setData(child_key, self.sourceModel.nextKey())            
            self.selectionModel().setCurrentIndex(child_name, QItemSelectionModel.ClearAndSelect)

    def slot_removeRow(self):
        '''delete selected group'''
        index = self.selectedIndex()
        if not index:
            return

        reply = QMessageBox.question(self, 'Confirm', self.tr(
            "Confirm to remove '{0}' and all sub-groups under this group?\n"
            "The reference items under this group will be moved to Trash.".format(index.data(Qt.EditRole))), 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply != QMessageBox.Yes:
            return        
        
        # ATTENTION: get the key before any actions are applied to the tree model
        keys = index.internalPointer().keys()
        if not self.sourceModel.isDefaultGroup(index): 
            self.sourceModel.removeRow(index.row(), index.parent())
            # emit removing group signal
            self.groupCleared.emit(keys)

    def slot_emptyGroup(self):
        '''move items from selected group to TRASH'''
        index = self.selectedIndex()
        if not index:
            return

        keys = index.internalPointer().keys()
        self.groupCleared.emit(keys)


    def slot_updateCounter(self, items):
        '''update count of items for each group
           :param items: the latest items list
        '''
        self.sourceModel.layoutAboutToBeChanged.emit()
        self.sourceModel.updateItems(items)
        self.sourceModel.layoutChanged.emit() # update display immediately
