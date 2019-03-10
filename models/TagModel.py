# model, delegate for Tags table view
# 

from PyQt5.QtCore import QModelIndex, Qt, QRect, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QStyledItemDelegate, QHBoxLayout,QWidget,QStyle, QStyleOptionButton, 
    QColorDialog, QPushButton)

from .TableModel import TableModel

KEY, NAME, COLOR = range(3)

class TagModel(TableModel):
    def __init__(self, headers, parent=None):        
        super(TagModel, self).__init__(headers, parent)

        # key for each item
        # key=-1 is the default item: untagged
        # so common item starts from key=1
        self._currentKey = 0

        # item count for each group
        self.itemsList = []


    def getIndexByKey(self, key):
        '''get ModelIndex with specified key in the associated object'''
        for i, (tag_key, *_) in enumerate(self.dataList):
            if tag_key == key:
                return self.index(i, NAME)
        return QModelIndex()

    def getKeyByIndex(self, index):
        row = index.row()
        if 0<=row<len(self.dataList):
            return self.dataList[row][0]
        else:
            return -1
 
    def setup(self, tags=[]):
        '''setup model data:
           it is convenient to reset data after the model is created
        '''
        self._currentKey = 0
        for key, name, color in tags:
            if self._currentKey<key:
                self._currentKey = key

        self.beginResetModel()
        self.dataList = tags        
        self.endResetModel()

    def updateItems(self, items):
        '''items for counting'''
        self.itemsList = items

    def nextKey(self):
        '''next key for new item of this model'''
        self._currentKey += 1
        return self._currentKey 

    def isDefaultItem(self, index):
        '''first row is default item -> No Tag'''
        return index.row()==0 

    def flags(self, index):
        '''item status'''
        if not index.isValid():
            return Qt.ItemIsEnabled

        if index.row()==0 or index.column() != NAME:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role=Qt.DisplayRole):
        '''Table view could get data from this model'''
        if not self.checkIndex(index):
            return None

        row, col = index.row(), index.column()
        # display
        if role == Qt.DisplayRole:
            if col == 1: # NAME
                key = self.dataList[row][0] # KEY, NAME, COLOR
                name = self.dataList[row][1]
                count = 0
                # UNTAGGED: check empty tags list from items
                if key==-1:
                    for item in self.itemsList:
                        if not item[2]:
                            count += 1
                # common tag
                else:
                    for item in self.itemsList:
                        if key in item[2]: # 2=>TAGS
                            count += 1
                return '{0} ({1})'.format(name, count) if count else name
            else:
                return self.dataList[row][col]
        #edit
        elif role == Qt.EditRole:
            return self.dataList[row][col]
        else:
            return None


class TagDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(TagDelegate, self).__init__(parent)
        self.ratio = 0.55 # button width=height=ration*cell_height
        self.ref_btn = QPushButton() # style reference button

    def _getButtonRect(self, option):
        '''determin button rectange area according to QStyleOptionViewItem'''
        R = option.rect
        h = self.ratio*R.height()
        w = h
        dx = (R.width()-w)/2
        dy = (1-self.ratio)/2*R.height()
        return R.adjusted(dx, dy, -dx, -dy)

    def paint(self, painter, option, index):
        '''paint item in column 1 as user defined'''

        # dismiss focus style        
        if option.state & QStyle.State_HasFocus: 
            option.state ^= QStyle.State_HasFocus

        if index.column() == COLOR: # since KEY is not shown in the view
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
        if index.column() == COLOR:
            if self._getButtonRect(option).contains(event.pos()) and event.button() == Qt.LeftButton:
                self.setModelData(None, model, index)
            return True
        else:
            return super(TagDelegate, self).editorEvent(event, model, option, index)

    def setModelData(self, editor, model, index):
        '''set model data after editing'''        
        if index.column() == COLOR:
            color = QColorDialog.getColor(QColor(index.data()))
            if color.isValid():
                model.setData(index, color.name())
        else:
            super(TagDelegate, self).setModelData(editor, model, index)