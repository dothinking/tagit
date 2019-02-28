from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QAction)


class MainMenu(object):
    """main menu and toolbox for main window"""
    def __init__(self, parent):
        self.mainWindow = parent

    def createMenus(self, parent, config):
        '''init menu
           :param config: data for creating menus, e.g.
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
                ('&Help',[
                    ('About',None,None,None,None),
                    ('Test', [
                        ('Test1',None,None,None,'hiaha, test1'),
                        ('Test2',None,None,None,'hiaha, test2'),
                    ])
                ])
            ]
        '''
        for menu_item in config:
            if not menu_item or not menu_item[0]: # ()=>separator
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

    def open(self):
        '''open existing project'''
        filename, _ = QFileDialog.getOpenFileName(self.mainWindow, 
            'Open Prpject...', '', 
            'Tagit Project (*.dat);;All Files (*)')
        if not filename:
            return

        if not self.mainWindow.loadDatabase(filename):
            QMessageBox.critical(None, "Error", "Invalid database for Tagit project.")

    def save(self):
        '''save current database'''
        filename = self.mainWindow.database()
        if filename:
            self.mainWindow.serialize(filename)
        else:
            self.saveAs()

    def saveAs(self):
        '''save current data as new database'''
        filename, _ = QFileDialog.getSaveFileName(self.mainWindow, 
            'Save Prpject as...', '', 
            'Tagit Project (*.dat);;All Files (*)')
        if filename:
            self.mainWindow.serialize(filename)