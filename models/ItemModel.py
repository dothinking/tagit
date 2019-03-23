# model, delegate for Tags table view
# 

import os

from PyQt5.QtCore import (QSortFilterProxyModel, QModelIndex, Qt, QRect, QEvent, QPointF, QMimeData)
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle

from models.TableModel import TableModel
from models.TagModel import TagModel
from models.GroupModel import GroupModel


class ItemModel(TableModel):

    NAME, GROUP, TAGS, PATH, DATE, NOTES = range(6)

    def __init__(self, headers, parent=None):        
        super(ItemModel, self).__init__(headers, parent)

    def flags(self, index):
        '''item status'''
        if not index.isValid():
            return Qt.ItemIsEnabled

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled

    def mimeTypes(self):
        return ['tagit-item']

    def mimeData(self, indexes):
        '''store current group'''
        group = indexes[0].siblingAtColumn(ItemModel.GROUP).data()
        mimedata = QMimeData()        
        mimedata.setData('tagit-item', str(group).encode())
        return mimedata

 
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

        # always filtered by searching text
        name = self.sourceModel().index(sourceRow, ItemModel.NAME, sourceParent).data()
        path = self.sourceModel().index(sourceRow, ItemModel.PATH, sourceParent).data()
        text_filter = self.filterRegExp().indexIn(name)>=0 or self.filterRegExp().indexIn(path)>=0

        # filtered by group
        if self.filterKeyColumn() == ItemModel.GROUP:
            group = self.sourceModel().index(sourceRow, ItemModel.GROUP, sourceParent).data()
            # Unreferenced: path is invalid
            if not self.groupList:
                return False
            elif self.groupList[0]==GroupModel.UNREFERENCED:
                return text_filter and not (path and os.path.exists(path))
            # ALL
            elif self.groupList[0]==GroupModel.ALLGROUPS:
                return text_filter
            else:
                return text_filter and group in self.groupList

        # filtered by tag
        elif self.filterKeyColumn() == ItemModel.TAGS:
            tags = self.sourceModel().index(sourceRow, ItemModel.TAGS, sourceParent).data()
            if tags==None or self.tagId==None:
                return False
            elif self.tagId==TagModel.NOTAG: # Untagged
                return text_filter and tags==[]
            else:
                return text_filter and self.tagId in tags

        # Not our business.
        return super(SortFilterProxyModel, self).filterAcceptsRow(sourceRow, sourceParent)

class ItemDelegate(QStyledItemDelegate):    

    def __init__(self, parent=None):
        super(ItemDelegate, self).__init__(parent)
        self.ratio = 0.55
        self.space_ratio = 0.5

    def allTags(self):
        '''get latest tags list from parent -> ItemTanleView'''
        tags = self.parent().tags()
        return {key:(name, color) for key, name, color in tags}

    def paint(self, painter, option, index):
        '''render style for tags list'''
        if index.column() == ItemModel.NAME:
            painter.save()

            # paint selection style
            # otherwise, no selection style is shown
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            painter.setRenderHint(QPainter.Antialiasing, True)           

            # filling rect
            H = option.rect.height() # cell height
            h = self.ratio*H # fill area height
            dy_fill = (H-h)/2

            # font rect
            fm = painter.fontMetrics()
            dy_text = (H-fm.ascent()-fm.descent())/2+fm.ascent()

            # seperate space
            single_space = 0.5*self.space_ratio*h

            # move painter to top left side of cell
            painter.translate(option.rect.x(), option.rect.y())           
            
            # draw text: name
            name = index.data()
            painter.translate(single_space, dy_text) # move to start point
            painter.drawText(QPointF(0.0,0.0), name) # draw text
            painter.translate(fm.width(name), -dy_text) # move to next position

            # draw tags: filling area with tag name
            tags = index.model().index(index.row(), ItemModel.TAGS).data()
            allTags = self.allTags()
            for key in tags:
                tag_name, color_name = allTags.get(key, (None, None))
                if not tag_name or not color_name:
                    continue

                w = fm.width(tag_name) + 2*single_space
                # move to point starting to draw filling rect
                painter.translate(2*single_space, dy_fill)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(color_name))
                painter.drawRoundedRect(0, 0, w, h, single_space, single_space) # draw rect
                painter.translate(0, -dy_fill) # move to baseline in y direction

                painter.translate(single_space, dy_text) # start point for drawing text
                painter.setPen(QColor('#ffffff'))
                painter.drawText(QPointF(0.0,0.0), tag_name) # draw text
                painter.translate(w-single_space, -dy_text) # move to baseline in y direction

            painter.restore()

        else:
            super(ItemDelegate, self).paint(painter, option, index)