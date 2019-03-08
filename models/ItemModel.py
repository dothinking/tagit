# model, delegate for Tags table view
# 

from PyQt5.QtCore import QModelIndex, Qt, QRect, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QStyledItemDelegate, QHBoxLayout,QWidget,QStyle, QStyleOptionButton, 
    QColorDialog, QPushButton)

from .TableModel import TableModel

NAME, GROUP, TAGS, PATH, DATE, NOTES = range(6)

class ItemModel(TableModel):
    def __init__(self, headers, parent=None):        
        super(ItemModel, self).__init__(headers, parent)

    def flags(self, index):
        '''item status'''
        if not index.isValid():
            return Qt.ItemIsEnabled

        if index.column() not in (NAME, TAGS):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role=Qt.DisplayRole):
        '''Table view could get data from this model'''
        if role != Qt.DisplayRole and role != Qt.EditRole:
            return None

        if not self.checkIndex(index):
            return None

        row, col = index.row(), index.column() 

        if index.column() == TAGS:
            return ','.join(self.dataList[row][col])
               
        return self.dataList[row][col]
 

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