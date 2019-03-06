# model, delegate for Tags table view
# 

from PyQt5.QtCore import QModelIndex, Qt, QRect, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QStyledItemDelegate, QStyle, QStyleOptionButton, 
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


    def getIndexByKey(self, key):
        '''get ModelIndex with specified key in the associated object'''
        for i, (tag_key, *_) in enumerate(self.data):
            if tag_key == key:
                return self.index(i, NAME)
        return QModelIndex()

    def getKeyByIndex(self, index):
        row = index.row()
        if 0<=row<len(self.data):
            return self.data[row][0]
        else:
            return -1
 
    def setup(self, items=[]):
        '''setup model data:
           it is convenient to reset data after the model is created
        '''
        self._currentKey = 0
        for key, name, color in items:
            if self._currentKey<key:
                self._currentKey = key

        self.beginResetModel()
        self.data = items        
        self.endResetModel()

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

        if index.column() != NAME:
            return Qt.ItemIsEnabled

        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
 

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
        x = R.left() + (R.width()-w)/2
        y = R.top() + (1-self.ratio)/2*R.height()
        return QRect(x,y,w,h)

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