# model for group tree view
# an editable tree based on simple TreeModel

from PyQt5.QtCore import QModelIndex, Qt
from models.TreeModel import TreeItem, TreeModel

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
        # ignore default group
        res.append([child.serialize() for child in self.childItems if child.itemData[GroupModel.KEY]>9])

        return res # key, name, children

class GroupModel(TreeModel):

    # KEY: unique key for each item
    #    - root item: key=0
    #    - default item: 1=<key<10
    #    - user defined item: key>=10
    # NAME: display name

    NAME, KEY, CHILDREN = range(3)

    # default groups
    ALLGROUPS, UNGROUPED, UNREFERENCED, DUPLICATED, TRASH = range(1,6)    

    def __init__(self, header, parent=None):
        '''
           :param headers: header of tree, e.g. ['key', 'name']
           :param parent: parent object
        '''         
        # init model with root item only
        rootItem = GroupItem(header) # root item
        super(GroupModel, self).__init__(rootItem, parent)

        self.defaultGroups = [['All Groups', GroupModel.ALLGROUPS, [
            ['Ungrouped', GroupModel.UNGROUPED, []],
            ['Unreferenced', GroupModel.UNREFERENCED, []],
            ['Duplicated', GroupModel.DUPLICATED, []],
            ['Trash', GroupModel.TRASH, []]
        ]]]

        self.initData()


    def initData(self):
        # key for each item
        self._currentKey = 9
        # require saving if True
        self._saveRequired = False  
        # reference item count for each group
        self.referenceList = []
        # clear all groups first
        self.rootItem.reset()

    def setup(self, items=[]):
        '''setup model data for generating the tree
           :param items: list raw data for child items of parent, e.g.
                        [[key, name, [children]], ..., []]
        '''
        # reset data within beginResetModel() and endResetModel(),
        # so that these model data could be updated explicitly
        self.beginResetModel()        
        self.initData()
        self._setupData(self.defaultGroups, self.rootItem, True)
        self._setupData(items, self.rootItem)
        self.endResetModel()

    def updateItems(self, items):
        '''items for counting'''
        self.referenceList = items

    def _setupData(self, items, parent, default=False):
        '''setup model data for generating the tree
           :param items: list raw data for child items of parent, e.g.
                        [[name, key, [children]], ..., []]
           :param parent: parent item
           :param default: if not default, :param items: should be checked ->
                        0<key<10 is invalid, so these items should be ignored
        '''
        for name, key, children in items:

            # default group should not exist in user data 
            if not default and 0<key<10:
                continue

            # append item
            parent.insertChildren(parent.childCount(), 1, parent.columnCount())
            if self._currentKey < key:
                self._currentKey = key
            # set data
            currentItem = parent.child(parent.childCount()-1)            
            currentItem.setData(GroupModel.NAME, name)
            currentItem.setData(GroupModel.KEY, key)

            # setup child items
            self._setupData(children, currentItem, default)

    def nextKey(self):
        '''next key for new item of this model'''
        self._currentKey += 1
        return self._currentKey

    def isDefaultGroup(self, index):
        '''default item: 0<key<10'''
        if not index.isValid():
            return True
        key = index.siblingAtColumn(GroupModel.KEY).data()
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

    def getParentsByKey(self, key):
        '''get all parents'''
        index = self.getIndexByKey(key)
        res = []
        while True:
            if not index.isValid():
                break
            else:
                res.append(index.data(Qt.EditRole))
                index = self.parent(index)
        return res


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
            return Qt.ItemIsDropEnabled

        # default items should not be modified
        if self.isDefaultGroup(index) or index.column()==GroupModel.KEY:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled

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

                if GroupModel.ALLGROUPS in keys:
                    count = len(self.referenceList)
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

    # implement drop methods
    def canDropMimeData(self, data, action, row, column, parent):

        # accept item table only
        if not data.hasFormat('tagit-item'):
            return False

        # can drop exactly on the group
        # row=-1, column=-1 => drop as child of parent => drop exactly on parent
        # row>=0, column>=0, drop at index(row, column, parent)
        if not parent.isValid() or row != -1:
            return False        
        
        target_group = parent.siblingAtColumn(GroupModel.KEY).data()
        itemData = data.data('tagit-item')
        item_group = int(str(itemData, encoding='utf-8'))

        # target group should not be the original group which the dragging items belong to
        if item_group==target_group:
            return False

        # target group should only be TRASH if target is default group
        if self.isDefaultGroup(parent) and target_group!=GroupModel.TRASH:
            return False
        
        # target group should only be TRASH if item group is UNREFERENCED
        if item_group==GroupModel.UNREFERENCED and target_group!=GroupModel.TRASH:
            return False

        return True


if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication, QTreeView

    app = QApplication(sys.argv)
    model = GroupModel()
    tree = QTreeView()    
    tree.setModel(model)
    tree.show()
    sys.exit(app.exec_())   
