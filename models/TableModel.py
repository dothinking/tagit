# base class for table model
# 

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt


class TableModel(QAbstractTableModel):
    def __init__(self, headers, parent=None):        
        super(TableModel, self).__init__(parent)
        self.headers = headers
        # data in table: [[...], [...], ...]
        self.dataList = []

        # require saving if any changes are made
        self._saveRequired = False    
 
    def setup(self, items=[]):
        '''setup model data:
           it is convenient to reset data after the model is created
        '''
        self.beginResetModel()
        self.dataList = items        
        self.endResetModel()

    def checkIndex(self, index):
        if not index.isValid():
            return False

        row, col = index.row(), index.column()
        if row<0 or row>=len(self.dataList):
            return False

        if col<0 or col>=len(self.headers):
            return False

        return True

    def saveRequired(self):
        return self._saveRequired

    def serialize(self, save=True):
        if save:
            self._saveRequired = False # saved
        return [item for item in self.dataList]

    
    # --------------------------------------------------------------
    # reimplemented methods for reading data
    # --------------------------------------------------------------
    def rowCount(self, index=QModelIndex()):
        '''count of rows'''
        return len(self.dataList)
 
    def columnCount(self, index=QModelIndex()):
        '''count of columns'''
        return len(self.headers)
 
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        '''header data'''
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section+1

        return None

    def data(self, index, role=Qt.DisplayRole):
        '''Table view could get data from this model'''
        if role != Qt.DisplayRole and role != Qt.EditRole:
            return None

        if not self.checkIndex(index):
            return None

        row, col = index.row(), index.column()        
        return self.dataList[row][col]
 
    # --------------------------------------------------------------
    # reimplemented methods for editing data
    # --------------------------------------------------------------
    def setData(self, index, value, role=Qt.EditRole):
        '''update model data when editing from view'''
        if role != Qt.EditRole:
            return False

        if not self.checkIndex(index):
            return False

        row, col = index.row(), index.column()
        self.dataList[row][col] = value

        # emit signal if successed
        self._saveRequired = True
        self.dataChanged.emit(index, index)

        return True
 
    def flags(self, index):
        '''item status'''
        if not index.isValid():
            return Qt.ItemIsEnabled

        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
 
    def insertRows(self, position, rows=1, parent=QModelIndex()):
        '''insert rows at given position'''
        # check range
        if position < 0:
            position = 0
        if position>len(self.dataList):
            position = len(self.dataList)

        self.beginInsertRows(parent, position, position+rows-1)
        for row in range(rows):
            data = [None for col in range(len(self.headers))]
            self.dataList.insert(position, data)
        self.endInsertRows()

        # flag for saving model
        self._saveRequired = True

        return True
 
    def removeRows(self, position, rows=1, parent=QModelIndex()):
        '''delete rows at position'''        
        if position < 0:
            position = 0
        if position+rows>len(self.dataList):
            rows = len(self.dataList) - position

        self.beginRemoveRows(parent, position, position+rows-1)
        for row in range(rows):
            self.dataList.pop(position)
        self.endRemoveRows()

        # flag for saving model
        self._saveRequired = True

        return True

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        '''moves count rows starting with the given sourceRow under parent sourceParent 
           to row destinationChild under parent destinationParent.
        '''
        if sourceRow < 0:
            sourceRow = 0
        if sourceRow+count>len(self.dataList):
            count = len(self.dataList)-sourceRow
        if sourceRow<=destinationChild<=sourceRow+count:
            return True

        # rows to be moved
        rows = self.dataList[sourceRow:sourceRow+count]
        dest = self.dataList[destinationChild]

        # move rows in the same table
        self.beginMoveRows(sourceParent, sourceRow, sourceRow+count-1, sourceParent, destinationChild)
        # remove rows in original position
        for row in range(count):
            self.dataList.pop(sourceRow)

        # insert to destination position
        dest_row = self.dataList.index(dest)
        for row in rows[::-1]:
            self.dataList.insert(dest_row, row)
        self.endMoveRows()

        # flag for saving model
        self._saveRequired = True

        return True
