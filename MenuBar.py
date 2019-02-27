from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction


class MenuBar(object):
    """menu bar and toolbox for main window"""
    def __init__(self, parent):
        self.mainWindow = parent

        # menu map:
        # menu: (text, [sub actions])
        # action: (text, slot, shortcut, icon, tips)
        # separator: ()
        menuMap = [
            ('&File',[
                ('New',None,None,None,None),
                ('Save',None,None,None,None),
                (),
                ('Quit',self.mainWindow.close,None,None,None),
            ]),
            ('&Group',[
                ('New Group',self.mainWindow.groupsView().slot_insertRow,None,None,None),
                ('Create Sub-Group',self.mainWindow.groupsView().slot_insertChild,None,None,None),
                (),
                ('Remove Group',self.mainWindow.groupsView().slot_removeRow,None,None,None),
            ]),
            ('&Help',[
                ('About',None,None,None,None),
                ('Test', [
                    ('Test1',None,None,None,'hiaha, test1'),
                    ('Test2',None,None,None,'hiaha, test2'),
                ])
            ])
        ]
        self.createMenus(parent.menuBar(), menuMap)

        # init toolbar
        self.createToolBars()

    def createMenus(self, parent, config):
        '''init menu'''
        for menu_item in config:
            if not menu_item: # ()=>separator
                parent.addSeparator()
            elif isinstance(menu_item[1], list): # menu
                menu = parent.addMenu(menu_item[0])
                self.createMenus(menu, menu_item[1])
            else:
                action = self.createAction(*menu_item)
                parent.addAction(action)

    def createToolBars(self):
        pass
        # self.fileToolBar = self.addToolBar("File")
        # self.fileToolBar.addAction(self.newLetterAct)
        # self.fileToolBar.addAction(self.saveAct)
        # self.fileToolBar.addAction(self.printAct)

        # self.editToolBar = self.addToolBar("Edit")
        # self.editToolBar.addAction(self.undoAct)

    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False):
        action = QAction(text, self.mainWindow)
        if icon:
            action.setIcon(QIcon("{0}.png".format(icon)))
        if shortcut:
            action.setShortcut(shortcut)
        if tip:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action
