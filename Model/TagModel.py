# model, delegate for Tags table view
# 

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QRect, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QStyledItemDelegate, QStyle, QStyleOptionButton, 
    QColorDialog, QPushButton)

class TagModel(QAbstractTableModel):
    def __init__(self, headers, parent=None):        
        super(TagModel, self).__init__(parent)
        self.headers = headers
        # item in tags: [key, tag_name, color]
        # but only name and color will show in table view
        self.tags = []

        # key for each item
        # key=1 is the default item: No Tag
        # so common item starts from key=2
        self._currentKey = 1

        # require saving if ant changes are made
        self._saveRequired = False

    def getIndexByKey(self, key):
        '''get ModelIndex with specified key in the associated object'''
        for i, (tag_key, *_) in enumerate(self.tags):
            if tag_key == key:
                return self.index(i, 0)
        return QModelIndex()

    def getKeyByIndex(self, index):
        row = index.row()
        if 0<=row<len(self.tags):
            return self.tags[row][0]
        else:
            return -1
 
    def setup(self, items=[]):
        '''setup model data:
           it is convenient to reset data after the model is created
        '''
        self._currentKey = 2
        for key, name, color in items:
            if self._currentKey<key:
                self._currentKey = key

        self.beginResetModel()
        self.tags = items        
        self.endResetModel()

    def checkIndex(self, index):
        if not index.isValid():
            return False

        row, col = index.row(), index.column()
        if row<0 or row>=len(self.tags):
            return False

        if col<0 or col>=len(self.headers):
            return False

        return True

    def _nextKey(self):
        '''next key for new item of this model'''
        self._currentKey += 1
        return self._currentKey 

    def isDefaultItem(self, index):
        '''first row is default item -> No Tag'''
        return index.row()==0

    def saveRequired(self):
        return self._saveRequired

    def serialize(self):
        self._saveRequired = False # saved
        return [tag for tag in self.tags]

    
    # --------------------------------------------------------------
    # reimplemented methods for reading data
    # --------------------------------------------------------------
    def rowCount(self, index=QModelIndex()):
        '''count of rows'''
        return len(self.tags)
 
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
        return self.tags[row][col+1]
 
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
        self.tags[row][col+1] = value

        # emit signal if successed
        self._saveRequired = True
        self.dataChanged.emit(index, index)

        return True
 
    def flags(self, index):
        '''item status'''
        if not index.isValid() or index.column()==1:
            return Qt.ItemIsEnabled

        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
 
    def insertRows(self, position, rows=1, parent=QModelIndex()):
        '''insert rows at given position'''
        # check range
        if position < 0 or position>len(self.tags): 
            return False

        self.beginInsertRows(parent, position, position+rows-1)
        for i, row in enumerate(range(rows)):
            data = [self._nextKey(), '[New Tag]', '#000000']
            self.tags.insert(position, data)
        self.endInsertRows()

        # flag for saving model
        self._saveRequired = True

        return True
 
    def removeRows(self, position, rows=1, parent=QModelIndex()):
        '''delete rows at position'''        
        if position < 0 or position+rows>len(self.tags):
            return False

        self.beginRemoveRows(parent, position, position+rows-1)
        for row in range(rows):
            self.tags.pop(position)
        self.endRemoveRows()

        # flag for saving model
        self._saveRequired = True

        return True


class TagDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(TagDelegate, self).__init__(parent)
        self.ratio = 0.7 # button width=height=ration*cell_height
        self.ref_btn = QPushButton() # style reference button

    def _getButtonRect(self, option):
        '''determin button rectange area according to QStyleOptionViewItem'''
        R = option.rect
        h = self.ratio*R.height()
        w = h
        x = R.left() + (R.width()-w)/2
        y = R.top() + (1-self.ratio)/2*R.height()
        return QRect(x,y,w,h)

    def paint(self, painter, option, index):
        '''paint item in column 1 as user defined'''

        # dismiss focus style        
        if option.state & QStyle.State_HasFocus: 
            option.state ^= QStyle.State_HasFocus

        if index.column() == 1:
            # reference button for the style of QStyleOptionButton            
            self.ref_btn.setStyleSheet('background-color: {0}'.format(index.data()))

            # draw button
            btn = QStyleOptionButton()
            btn.rect = self._getButtonRect(option)
            self.ref_btn.style().drawControl(QStyle.CE_PushButton, btn, painter, self.ref_btn)
        else:
            super(TagDelegate, self).paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        '''it called when editing of an item starts.
           only single click on the drawn button is allowable
        '''
        if index.column() == 1:
            if self._getButtonRect(option).contains(event.pos()) and event.button() == Qt.LeftButton:
                self.setModelData(None, model, index)
            return True
        else:
            return super(TagDelegate, self).editorEvent(event, model, option, index)

    def setModelData(self, editor, model, index):
        '''set model data after editing'''        
        if index.column() == 1:
            color = QColorDialog.getColor(QColor(index.data()))
            if color.isValid():
                model.setData(index, color.name())
        else:
            super(TagDelegate, self).setModelData(editor, model, index)