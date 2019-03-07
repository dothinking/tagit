# model for group tree view
# an editable tree based on simple TreeModel

from PyQt5.QtCore import QModelIndex, Qt

from .TreeModel import TreeItem, TreeModel

class GroupItem(TreeItem):
    def __init__(self, key, data, parent=None):
        '''
        :param key: unique key for category item
                    - root item: key=0
                    - default item: 1=<key<10
                    - user defined item: key>=10
        :param data: columns to show in tree
        :param parent: parent item
        '''
        super(GroupItem, self).__init__(data, parent)

        self._key = key

    def key(self):
        return self._key

    def insertChildren(self, position, key, count, columns):
        '''insert children with specified columns at sprcified position
        :param position: position to insert children
        :param key: start key for the inserting items
        :param count: count of inserting items
        :param columns: count of columns of the inserting item
        '''
        # check range
        if position < 0 or position > len(self.childItems): 
            return False

        for i, row in enumerate(range(count)):
            data = [None for v in range(columns)] # None by default
            item = GroupItem(key+i, data, self)
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
        res = {'key': self._key, 'name': self.itemData[0]}
        if self.childItems:
            res['children'] = [child.serialize() for child in self.childItems]
        return res

class GroupModel(TreeModel):
    def __init__(self, header, parent=None):
        '''
           :param headers: header of tree, e.g. ('name', 'value')
           :param parent: parent object
        '''         
        # init model with root item only
        rootItem = GroupItem(0, header) # root item
        super(GroupModel, self).__init__(rootItem, parent)

        self._currentKey = 9 # key for each item
        self._saveRequired = False  # require saving if True 


    def setup(self, items=[], parent=None):
        '''setup model data for generating the tree
           :param items: list raw data for child items of parent, e.g.
                        [{'key':.., 'name':.., 'children':[]}, {}, ...]
           :param parent: parent item
        '''
        # reset data within beginResetModel() and endResetModel(),
        # so that these model data could be updated explicitly
        self.beginResetModel()        
        self._currentKey = 9
        self._saveRequired = False
        self._setupData(items, parent)
        self.endResetModel()

    def _setupData(self, items=[], parent=None):
        '''setup model data for generating the tree
           :param items: list raw data for child items of parent, e.g.
                        [{'key':.., 'name':.., 'children':[]}, {}, ...]
           :param parent: parent item
        '''
        if not parent:
            parent = self.rootItem

        parent.reset()
        for item in items:
            # append item
            key = item.get('key')
            parent.insertChildren(parent.childCount(), key, 1, 1)
            if self._currentKey<key:
                self._currentKey = key
            # set name
            currentItem = parent.child(parent.childCount() -1)
            currentItem.setData(0, item.get('name'))

            # setup child items
            self._setupData(item.get('children', []), currentItem)

    def _nextKey(self):
        '''next key for new item of this model'''
        self._currentKey += 1
        return self._currentKey

    def isDefaultItem(self, index):
        '''first two items under root is default item'''
        return not index.parent().isValid() and index.row()<2

    def saveRequired(self):
        return self._saveRequired

    def getIndexByKey(self, key, parent=QModelIndex()):
        '''get ModelIndex with specified key in the associated object'''
        for i in range(self.rowCount(parent)):
            index = self.index(i, 0, parent)
            if self._getItem(index).key() == key:
                return index
            else:
                # attention
                res = self.getIndexByKey(key, index) # found or QModelIndex()
                if res.isValid():
                    return res

        return QModelIndex()


    def serialize(self):
        '''store raw data'''
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
        item = self._getItem(index)
        if 0<item.key()<10:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def insertRows(self, position, rows, parent=QModelIndex()):
        '''insert rows'''
        parentItem = self._getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        success = parentItem.insertChildren(position, self._nextKey(), rows, self.rootItem.columnCount())
        self.endInsertRows()

        # flag for saving model
        if success:
            self._saveRequired = True

        return success
    
    def removeRows(self, position, rows, parent=QModelIndex()):
        '''remove rows starting from given position'''
        
        self.beginRemoveRows(parent, position, position+rows-1)
        parentItem = self._getItem(parent)
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

    def setData(self, index, value, role=Qt.EditRole):
        '''edit item data with specified index
           dataChanged signal should be emitted explictly
        '''
        if role != Qt.EditRole:
            return False

        # edit item
        item = self._getItem(index)
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