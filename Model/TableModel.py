# base class for table model
# 

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt


class TableModel(QAbstractTableModel):
    def __init__(self, headers, parent=None):        
        super(TableModel, self).__init__(parent)
        self.headers = headers
        # data in table: [[...], [...], ...]
        self.data = []

        # require saving if any changes are made
        self._saveRequired = False    
 
    def setup(self, items=[]):
        '''setup model data:
           it is convenient to reset data after the model is created
        '''
        self.beginResetModel()
        self.data = items        
        self.endResetModel()

    def checkIndex(self, index):
        if not index.isValid():
            return False

        row, col = index.row(), index.column()
        if row<0 or row>=len(self.data):
            return False

        if col<0 or col>=len(self.headers):
            return False

        return True

    def saveRequired(self):
        return self._saveRequired

    def serialize(self):
        self._saveRequired = False # saved
        return [item for item in self.data]

    
    # --------------------------------------------------------------
    # reimplemented methods for reading data
    # --------------------------------------------------------------
    def rowCount(self, index=QModelIndex()):
        '''count of rows'''
        return len(self.data)
 
    def columnCount(self, index=QModelIndex()):
        '''count of columns'''
        return len(self.headers)
 
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        '''header data'''
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

        return None

    def data(self, index, role=Qt.DisplayRole):
        '''Table view could get data from this model'''
        if role != Qt.DisplayRole and role != Qt.EditRole:
            return None

        if not self.checkIndex(index):
            return None

        row, col = index.row(), index.column()        
        return self.data[row][col]
 
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
        self.data[row][col] = value

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
        if position < 0 or position>len(self.data): 
            return False

        self.beginInsertRows(parent, position, position+rows-1)
        for row in range(rows):
            data = [None for col in range(len(self.headers))]
            self.data.insert(position, data)
        self.endInsertRows()

        # flag for saving model
        self._saveRequired = True

        return True
 
    def removeRows(self, position, rows=1, parent=QModelIndex()):
        '''delete rows at position'''        
        if position < 0 or position+rows>len(self.data):
            return False

        self.beginRemoveRows(parent, position, position+rows-1)
        for row in range(rows):
            self.data.pop(position)
        self.endRemoveRows()

        # flag for saving model
        self._saveRequired = True

        return True
