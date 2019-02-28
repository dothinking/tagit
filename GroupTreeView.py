from PyQt5.QtCore import QItemSelectionModel, QModelIndex, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeView, QMenu, QAction

from Model.GroupModel import GroupModel

class GroupTreeView(QTreeView):
    def __init__(self, header, parent=None):
        '''
        :param headers: header of tree, e.g. ('name', 'value')
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

        self.menu_map = [
            ("Create Group", self.slot_insertRow),
            ("Create Sub-Group", self.slot_insertChild),
            (None, None), # separator
            ("Remove Group", self.slot_removeRow)
        ]

    def setup(self, data=[]):
        '''reset tree with specified model data'''
        self.model().setup(data)       

        # refresh tree view to activate the model setting
        self.reset()
        self.expandAll()

    def customContextMenu(self, position):
        '''show context menu'''
        indexes = self.selectedIndexes()
        if not len(indexes):
            return

        # init context menu
        menu = QMenu()
        actions = []
        for menu_item in self.menu_map:
            if not menu_item or not menu_item[0]:
                menu.addSeparator()
            else:
                name, slot = menu_item
                actions.append(menu.addAction(self.tr(name), slot))                

        # set status
        model = self.model()
        s = not model.isDefaultItem(indexes[0])
        actions[1].setEnabled(s)
        actions[2].setEnabled(s)

        menu.exec_(self.viewport().mapToGlobal(position))

    def slot_insertChild(self):
        '''insert child item under current selected item'''
        index = self.selectionModel().currentIndex()
        model = self.model()

        # could not insert sub-items to default items
        if model.isDefaultItem(index):
            return

        # insert
        if not model.insertRow(0, index):
            return
        else:
            child = model.index(0, 0, index)
            model.setData(child, "[Sub Group]")
            self.selectionModel().setCurrentIndex(child, QItemSelectionModel.ClearAndSelect)

    def slot_insertRow(self):
        '''inset item at the same level with current selected item'''
        index = self.selectionModel().currentIndex()
        model = self.model()

        # could not prepend item to default items
        row = 2 if model.isDefaultItem(index) else index.row() + 1

        if not model.insertRow(row, index.parent()):
            return
        else:
            child = model.index(row, 0, index.parent())
            model.setData(child, "[New Group]")

    def slot_removeRow(self):
        index = self.selectionModel().currentIndex()
        model = self.model()
        if not model.isDefaultItem(index): 
            model.removeRow(index.row(), index.parent())



if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    config = {'key': 0, 'name': 'Group', 'children': [{'key': 18, 'name': '[New Group]', 'children': [{'key': 19, 'name': '[Sub Group]'}]}, {'key': 12, 'name': '[New Group]', 'children': [{'key': 13, 'name': '[Sub Group]', 'children': [{'key': 14, 'name': '[Sub Group]', 'children': [{'key': 15, 'name': '[Sub Group]'}]}, {'key': 16, 'name': '[New Group]'}]}]}]}
    tree = GroupTreeView(['GROUP'])
    tree.setup(config.get('children', []))
    tree.show()
    sys.exit(app.exec_())   