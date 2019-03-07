# editable tree view for groups:
# append, insert child, remove, edit text
# 

from PyQt5.QtCore import (QItemSelectionModel, Qt)
from PyQt5.QtWidgets import (QTreeView, QMenu, QAction, QMessageBox)

from models.GroupModel import GroupModel

class GroupTreeView(QTreeView):
    def __init__(self, header, parent=None):
        ''':param headers: header of tree, e.g. ('name', 'value')
        '''
        super(GroupTreeView, self).__init__(parent)

        # init tree
        self.resizeColumnToContents(0)
        self.setAlternatingRowColors(True)
        self.header().hide()
        self.expandAll()

        # model
        model = GroupModel(header)
        self.setModel(model)

        # context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customContextMenu)

    def setup(self, data=[], selected_key=2):
        '''reset tree with specified model data,
           and set the item with specified key as selected
        '''
        self.model().setup(data)       

        # refresh tree view to activate the model setting
        self.reset()
        self.expandAll()

        # set selected item
        index = self.model().getIndexByKey(selected_key)
        if index.isValid():
            self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

    def customContextMenu(self, position):
        '''show context menu'''
        indexes = self.selectedIndexes()
        if not len(indexes):
            return

        # init context menu
        menu = QMenu()
        menu.addAction(self.tr("Create Group"), self.slot_insertRow)
        act_sb = menu.addAction(self.tr("Create Sub-Group"), self.slot_insertChild)
        menu.addSeparator()
        act_rv = menu.addAction(self.tr("Remove Group"), self.slot_removeRow)

        # set status
        model = self.model()
        s = not model.isDefaultItem(indexes[0])
        act_sb.setEnabled(s)
        act_rv.setEnabled(s)

        menu.exec_(self.viewport().mapToGlobal(position))

    def slot_insertChild(self):
        '''insert child item under current selected item'''
        index = self.selectionModel().currentIndex()
        model = self.model()

        # could not insert sub-items to default items
        if model.isDefaultItem(index):
            return

        # insert
        if model.insertRow(0, index):
            child = model.index(0, 0, index)
            model.setData(child, "[Sub Group]")
            self.selectionModel().setCurrentIndex(child, QItemSelectionModel.ClearAndSelect)

    def slot_insertRow(self):
        '''inset item at the same level with current selected item'''
        index = self.selectionModel().currentIndex()
        model = self.model()

        # could not prepend item to default items
        row = 2 if model.isDefaultItem(index) else index.row() + 1
        if model.insertRow(row, index.parent()):
            child = model.index(row, 0, index.parent())
            model.setData(child, "[New Group]")
            self.selectionModel().setCurrentIndex(child, QItemSelectionModel.ClearAndSelect)

    def slot_removeRow(self):
        '''delete selected item'''
        index = self.selectionModel().currentIndex()
        reply = QMessageBox.question(self, 'Confirm', self.tr(
            "Confirm to remove '{0}'?\n"
            "The items under this group will not be deleted.".format(index.data())), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        
        model = self.model()
        if not model.isDefaultItem(index): 
            model.removeRow(index.row(), index.parent())



if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    config = {'key': 0, 'name': 'Group', 'children': [{'key': 18, 'name': '[New Group1]', 'children': [{'key': 19, 'name': '[Sub Group2]'}]}, {'key': 12, 'name': '[New Group3]', 'children': [{'key': 13, 'name': '[Sub Group4]', 'children': [{'key': 14, 'name': '[Sub Group5]', 'children': [{'key': 15, 'name': '[Sub Group6]'}]}, {'key': 16, 'name': '[New Group7]'}]}]}]}
    tree = GroupTreeView(['GROUP'])
    tree.setup(config.get('children', []),12)
    tree.show()
    sys.exit(app.exec_())   