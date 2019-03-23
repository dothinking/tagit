# model for group tree view
# an editable tree based on simple TreeModel

import os
from PyQt5.QtCore import QModelIndex, Qt
from .TreeModel import TreeItem, TreeModel

class GroupItem(TreeItem):

    def __init__(self, data, parent=None):
        '''       
        :param data: columns of tree
        :param parent: parent item
        '''
        super(GroupItem, self).__init__(data, parent)


    def keys(self):
        '''all keys including children'''
        groups = [self.itemData[GroupModel.KEY]]
        for item in self.childItems:
            groups.extend(item.keys())
        return groups

    def insertChildren(self, position, count, columns):
        '''insert children with specified columns at sprcified position
        :param position: position to insert children
        :param count: count of inserting items
        :param columns: count of columns of the inserting item
        '''
        # check range
        if position < 0 or position > len(self.childItems): 
            return False

        for i, row in enumerate(range(count)):
            data = [None for v in range(columns)] # None by default
            item = GroupItem(data, self)
            self.childItems.insert(position, item)
        
        return True

    def removeChildren(self, position, count):
        '''remove children from given position'''
        if position < 0 or position + count > len(self.childItems):
            return False

        for row in range(count):
            self.childItems.pop(position)

        return True

    def setData(self, column, value):
        '''edit data at given column'''
        if column < 0 or column >= len(self.itemData):
            return False
        else:
            self.itemData[column] = value
            return True

    def reset(self):
        '''remove all child items'''
        self.childItems = []

    def serialize(self):
        '''store data'''
        res = self.itemData[:] # copy
        res.append([child.serialize() for child in self.childItems])

        return res # key, name, children

class GroupModel(TreeModel):

    # KEY: unique key for each item
    #    - root item: key=0
    #    - default item: 1=<key<10
    #    - user defined item: key>=10
    # NAME: display name

    NAME, KEY, CHILDREN = range(3)

    # default groups
    UNGROUPED, UNREFERENCED, ALLGROUPS = range(1,4)

    def __init__(self, header, parent=None):
        '''
           :param headers: header of tree, e.g. ['key', 'name']
           :param parent: parent object
        '''         
        # init model with root item only
        rootItem = GroupItem(header) # root item
        super(GroupModel, self).__init__(rootItem, parent)

        self.defaultGroups = [
            ['Ungrouped', GroupModel.UNGROUPED, []],
            ['Unreferenced', GroupModel.UNREFERENCED, []],
            ['All Groups', GroupModel.ALLGROUPS, []]]

        self.initData()


    def initData(self):
        # key for each item
        self._currentKey = 9
        # require saving if True
        self._saveRequired = False  
        # reference item count for each group
        self.referenceList = []

    def setup(self, items=[], parent=None):
        '''setup model data for generating the tree
           :param items: list raw data for child items of parent, e.g.
                        [[key, name, [children]], ..., []]
           :param parent: parent item
        '''
        if not items:
            items = self.defaultGroups

        # reset data within beginResetModel() and endResetModel(),
        # so that these model data could be updated explicitly
        self.beginResetModel()        
        self.initData()
        self._setupData(items, parent)
        self.endResetModel()

    def updateItems(self, items):
        '''items for counting'''
        self.referenceList = items

    def _setupData(self, items, parent):
        '''setup model data for generating the tree
           :param items: list raw data for child items of parent, e.g.
                        [[name, key, [children]], ..., []]
           :param parent: parent item
        '''
        if not parent:
            parent = self.rootItem

        parent.reset()
        for name, key, children in items:
            # append item
            parent.insertChildren(parent.childCount(), 1, parent.columnCount())
            if self._currentKey < key:
                self._currentKey = key
            # set data
            currentItem = parent.child(parent.childCount()-1)            
            currentItem.setData(GroupModel.NAME, name)
            currentItem.setData(GroupModel.KEY, key)

            # setup child items
            self._setupData(children, currentItem)

    def nextKey(self):
        '''next key for new item of this model'''
        self._currentKey += 1
        return self._currentKey

    def isDefaultItem(self, index):
        '''default item: 0<key<10'''
        if not index.isValid():
            return True
        key = self.index(index.row(), GroupModel.KEY, index.parent()).data()
        return 0<key<10

    def saveRequired(self):
        return self._saveRequired

    def getIndexByKey(self, key, parent=QModelIndex()):
        '''get ModelIndex with specified key in the associated object'''
        for i in range(self.rowCount(parent)):
            index = self.index(i, GroupModel.KEY, parent)
            if index.data() == key:
                return self.index(index.row(), GroupModel.NAME, parent)
            else:
                # attention
                res = self.getIndexByKey(key, index) # found or QModelIndex()
                if res.isValid():
                    return res

        return QModelIndex()

    def serialize(self, save=True):
        '''store raw data'''
        if save:
            self._saveRequired = False # saved
        return self.rootItem.serialize()

    # --------------------------------------------------------------
    # ------------ default methods requiring overloaded ------------
    # --------------------------------------------------------------
    def flags(self, index):
        '''tree item status'''
        if not index.isValid():
            return Qt.NoItemFlags

        # default items should not be modified
        if self.isDefaultItem(index) or index.column()==GroupModel.KEY:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def insertRows(self, position, rows, parent=QModelIndex()):
        '''insert rows'''
        parentItem = self.getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        success = parentItem.insertChildren(position, rows, self.rootItem.columnCount())
        self.endInsertRows()

        # flag for saving model
        if success:
            self._saveRequired = True

        return success
    
    def removeRows(self, position, rows, parent=QModelIndex()):
        '''remove rows starting from given position'''
        
        self.beginRemoveRows(parent, position, position+rows-1)
        parentItem = self.getItem(parent)
        success = parentItem.removeChildren(position, rows)
        self.endRemoveRows()

        # flag for saving model
        if success:
            self._saveRequired = True           

        return success

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        '''edit headers at given column as specified value.
           headerDataChanged signal should be emitted explictly
        '''
        if role != Qt.EditRole or orientation != Qt.Horizontal:
            return False

        # edit header
        result = self.rootItem.setData(section, value)

        # emit signal if successed
        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result

    def data(self, index, role):
        '''get value at current index'''
        if not index.isValid():
            return None

        # underlying data
        row, col = index.row(), index.column()
        group = self.getItem(index)

        # displaying
        if role == Qt.DisplayRole:
            if col == GroupModel.NAME:
                keys, name = group.keys(), group.data(col)
                count = 0 # count

                # unreferenced items
                if keys==[GroupModel.UNREFERENCED]:
                    for item in self.referenceList:
                        path = item[3]
                        if not path or not os.path.exists(path):
                            count += 1
                # all items
                elif keys==[GroupModel.ALLGROUPS]:
                    count = len(self.referenceList)
                # common items
                else:                
                    for item in self.referenceList:
                        if item[1] in keys:
                            count += 1
                return '{0} ({1})'.format(name, count) if count else name
            else:
                return group.data(col)

        # editing
        elif role == Qt.EditRole:
            return group.data(col)
        else:
            return None       
            
    def setData(self, index, value, role=Qt.EditRole):
        '''edit item data with specified index
           dataChanged signal should be emitted explictly
        '''
        if role != Qt.EditRole:
            return False

        # edit item
        item = self.getItem(index)
        result = item.setData(index.column(), value)

        # emit signal if successed
        if result:
            self._saveRequired = True
            self.dataChanged.emit(index, index)

        return result


if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication, QTreeView

    app = QApplication(sys.argv)
    model = GroupModel()
    tree = QTreeView()    
    tree.setModel(model)
    tree.show()
    sys.exit(app.exec_())   