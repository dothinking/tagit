# Base class for simple tree model

from PyQt5.QtCore import (QAbstractItemModel, QModelIndex, Qt)


class TreeItem(object):
    def __init__(self, data, parent=None):
        '''
           :param data: column contents of tree item, e.g. [name, description]
        '''        
        self.itemData = data
        self.parentItem = parent
        self.childItems = []

    def columnCount(self):
        '''count of columns'''
        return len(self.itemData)

    def data(self, column):
        '''get data of current item at specified column'''
        return self.itemData[column]

    def parent(self):
        '''get parent'''
        return self.parentItem

    def child(self, row):
        '''get child item at position=row'''
        return self.childItems[row]

    def childCount(self):
        '''count of child items'''
        return len(self.childItems)

    def childNumber(self):
        '''get position in parent tree item'''
        if self.parentItem != None:
            return self.parentItem.childItems.index(self)
        return 0


class TreeModel(QAbstractItemModel):
    def __init__(self, rootItem, parent=None):        
        '''init model with a root item only, model data could be setup
           explictly later by setup(data, parent)
           :param rootItem: root node, header of tree by default
           :param parent: parent object
        '''
        super(TreeModel, self).__init__(parent)
        self.rootItem = rootItem


    def setup(self, data, parent):
        '''user defined method to setup model data,
           which are used to generate the tree.
           if it would be used to reset the tree model after
           the tree view was created, make sure the reset process
           is implemented between beginResetModel() and
           endResetModel()
        '''
        raise NotImplementedError

    def getItem(self, index):
        '''get the real instance of current tree item'''
        if index.isValid():
            item = index.internalPointer() 
            if item: return item

        return self.rootItem

    def rowCount(self, parent=QModelIndex()):
        '''count rows under the given parent'''
        parentItem = self.getItem(parent)
        return parentItem.childCount()

    def columnCount(self, parent=QModelIndex()):
        '''count of tree item columns'''
        return self.rootItem.columnCount()

    def data(self, index, role):
        '''get value at current index'''
        if not index.isValid():
            return None

        if role != Qt.DisplayRole and role != Qt.EditRole:
            return None

        item = self.getItem(index)
        return item.data(index.column())    

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        '''header at the specified column'''
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)
        return None

    def index(self, row, column, parent=QModelIndex()):
        '''returns the index of the item in the model
           specified by the given row, column and parent index.
        '''
        if self.hasIndex(row, column, parent):
            parentItem = self.getItem(parent)
            childItem = parentItem.child(row)
            if childItem:
                # creates a model index for the given row and column with the internal item.
                return self.createIndex(row, column, childItem)
        return QModelIndex()    

    def parent(self, index):
        '''parent of the model item with the given index'''
        if not index.isValid():
            return QModelIndex()

        childItem = self.getItem(index)
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()
        else:
            return self.createIndex(parentItem.childNumber(), 0, parentItem)

    