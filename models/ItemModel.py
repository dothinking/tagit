# model, delegate for Tags table view
# 

import os

from PyQt5.QtCore import QSortFilterProxyModel, QModelIndex, Qt, QRect, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QStyledItemDelegate, QHBoxLayout, QWidget, QStyle, QComboBox, QSizePolicy,QStyleOptionButton,
    QLabel, QPushButton)

from models.TableModel import TableModel

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
 
class SortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(SortFilterProxyModel, self).__init__(parent)
        self.groupList = []
        self.tagId = None

    def setGroupFilter(self, groups):
        self.groupList = groups

    def setTagFilter(self, tag_id):
        self.tagId = tag_id

    def filterAcceptsRow(self, sourceRow, sourceParent):
        '''filter with group and tag'''
        if self.filterKeyColumn() == GROUP:
            group = self.sourceModel().index(sourceRow, GROUP, sourceParent).data()
            # Unreferenced: path is invalid
            if not self.groupList:
                return False
            elif self.groupList[0]==2:
                path = self.sourceModel().index(sourceRow, PATH, sourceParent).data()                
                return not path or not os.path.exists(path)
            # ALL
            elif self.groupList[0]==3:
                return True
            else:
                return group in self.groupList

        elif self.filterKeyColumn() == TAGS:
            tags = self.sourceModel().index(sourceRow, TAGS, sourceParent).data()
            if not self.tagId:
                return False
            elif self.tagId==-1: # Untagged
                return tags==[]
            else:
                return self.tagId in tags

        # Not our business.
        return super(SortFilterProxyModel, self).filterAcceptsRow(sourceRow, sourceParent)

class ItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ItemDelegate, self).__init__(parent)
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
        '''render style for tags list'''
        if index.column() == TAGS:
            # reference button for the style of QStyleOptionButton            
            self.ref_btn.setStyleSheet('background-color: {0}'.format('#ffccaa'))

            # draw button
            btn = QStyleOptionButton()
            btn.text = '='
            btn.rect = self._getButtonRect(option)
            self.ref_btn.style().drawControl(QStyle.CE_PushButton, btn, painter, self.ref_btn)
        else:
            super(ItemDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        if index.column() == TAGS:
            editor = QComboBox(parent)
            editor.setEditable(True)
            tags = self.parent().tags()
            for tag in tags:
                editor.addItem(tag[1], tag) # KEY, NAME, COLOR
            editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            return editor
        else:
            return QStyledItemDelegate().createEditor(parent, option, index)

    # def setEditorData(self, editor, index):
    #     value = index.model().data(index, Qt.EditRole)

    #     editor.setValue(value)

    def setModelData(self, editor, model, index):
        '''set model data after editing'''        
        if index.column() == TAGS:
            tag = editor.currentData()
            keys = index.data()
            if tag[0] not in keys:
                keys.append(tag[0])
                model.setData(index, keys)
        else:
            super(ItemDelegate, self).setModelData(editor, model, index)

    