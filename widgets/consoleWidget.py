"""
    External packages/modules

        Name            Homepage link                                               Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        qtconsole       https://qtconsole.readthedocs.io/en/stable/                 Python console widget
"""

from os.path import join
from os.path import exists
from os.path import abspath
from os.path import dirname

import types

import pkgutil

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox

import darkdetect

from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget

__all__ = ['ConsoleWidget']

"""
    Class hierarchy
    
        QWidget -> ConsoleWidget
        
    Description
    
        Embedded IPython Qt console   
"""


class ConsoleWidget(QWidget):
    """
        ConsoleWidget

        Description

            Embedded IPython Qt console

        Inheritance

            QWidget -> ConsoleWidget

        Private attribute

            _mainwindow     WindowSisyphe, PySisyphe main window
            _variables      dict
            _console        RichJupyterWidget
            _modules        QListWidget
            _globals        QListWidget
            _action         dict() of QAction
            _popup          QMenu

        Public method

            QMenu = getPopup()
            pushVariables(dict)
            clear()
            copy()
            restart()
            save()
            importMain()
            setMainWindow(WindowSisyphe)
            WindowSisyphe = getMainWindow()
            bool = hasMainWindow()

            inherited QWidget
    """

    @classmethod
    def isDarkMode(cls):
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls):
        return darkdetect.isLight()

    @classmethod
    def getDocDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'doc')
    
    # Special method

    def __init__(self, variables=None, parent=None):
        super().__init__(parent)

        # Console

        self._mainwindow = None
        self._variables = variables
        self._console = RichJupyterWidget(gui_completion='droplist')
        if self.isDarkMode(): self._console.set_default_style('linux')
        else: self._console.set_default_style('lightbg')
        self._console.paging = 'none'
        self._console.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel(show_banner=False)
        kernel_manager.kernel.gui = 'qt'
        self._console.kernel_client = kernel_client = self._console.kernel_manager.client()
        kernel_client.start_channels()
        self.pushVariables(variables)
        self._console.execute('%matplotlib inline')

        path = join(self.getDocDirectory(), 'ipython.txt')
        if exists(path):
            with open(path, 'r') as f:
                buff = f.readlines()
            self.setToolTip(''.join(buff))

        # Modules and variables listwidgets

        self._modules = QTreeWidget()
        self._globals = QTreeWidget()
        self._modules.setHeaderLabel('Module(s) / Type(s) / Function(s)')
        self._globals.setHeaderLabel('Variables')
        self._modules.setToolTip('Module(s) / Type(s) / Function(s)')
        self._globals.setToolTip('Variables')
        self._modules.setAlternatingRowColors(True)
        self._globals.setAlternatingRowColors(True)

        splt = QSplitter()
        splt.addWidget(self._modules)
        splt.addWidget(self._globals)
        splt.setOrientation(Qt.Vertical)

        splitter = QSplitter()
        splitter.addWidget(self._console)
        splitter.addWidget(splt)
        splitter.setOrientation(Qt.Horizontal)

        # Buttons

        btnlyout = QHBoxLayout()
        btnlyout.setContentsMargins(0, 0, 0, 0)
        btnlyout.setSpacing(5)
        self._save = QPushButton('Save as HTML/XML...')
        self._save.clicked.connect(self.save)
        self._copy = QPushButton('Copy')
        self._copy.setToolTip('Copy selection to clipboard')
        self._copy.clicked.connect(self.copy)
        self._clear = QPushButton('Clear')
        self._clear.setToolTip('Clear console display')
        self._clear.clicked.connect(self.clear)
        self._restart = QPushButton('Restart')
        self._restart.setToolTip('Restart console')
        self._restart.clicked.connect(self.restart)
        self._import = QPushButton('Import')
        self._import.setToolTip('Import PySisyphe modules')

        btnlyout.addStretch()
        btnlyout.addWidget(self._import)
        btnlyout.addWidget(self._clear)
        btnlyout.addWidget(self._copy)
        btnlyout.addWidget(self._restart)
        btnlyout.addWidget(self._save)

        # Popup menu

        self._action = dict()
        self._action['copy'] = QAction('Copy', self)
        self._action['clear'] = QAction('Clear', self)
        self._action['restart'] = QAction('Restart', self)
        self._action['save'] = QAction('Save as HTML/XML...', self)
        self._action['main'] = QAction('PySisyphe main window as \"pysisyphe\"', self)
        self._action['copy'].triggered.connect(self.copy)
        self._action['clear'].triggered.connect(self.clear)
        self._action['restart'].triggered.connect(self.restart)
        self._action['save'].triggered.connect(self.save)
        self._action['main'].triggered.connect(self.importMain)

        self._popup = QMenu()
        self._popup.addAction(self._action['copy'])
        self._popup.addAction(self._action['clear'])
        self._popup.addAction(self._action['restart'])
        self._popup.addAction(self._action['save'])
        self._popup.addSeparator()
        self._menuImport = self._popup.addMenu('Import')
        self._menuImport.addAction(self._action['main'])
        import Sisyphe
        for pkg in pkgutil.iter_modules([join(Sisyphe.__path__[0], 'core')]):
            if not pkg.ispkg and pkg.name != 'PySisyphe':
                cmd = 'from Sisyphe.core.{} import *'.format(pkg.name)
                action = QAction(pkg.name, self)
                action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
                self._menuImport.addAction(action)
        self._popup.addMenu(self._menuImport)

        self._import.setMenu(self._menuImport)

        # Init layout

        lyout = QVBoxLayout()
        lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(0)
        lyout.addWidget(splitter)
        lyout.addLayout(btnlyout)
        self.setLayout(lyout)
        self.update()
        self._console.executed.connect(self.update)

    # Private methods

    def update(self):
        self._modules.clear()
        self._globals.clear()
        g = self._console.kernel_manager.kernel.shell.user_ns
        k = g.keys()
        for v in k:
            if v[0] == '_': continue
            elif v in ['In', 'Out', 'get_ipython', 'exit', 'quit']: continue
            elif type(g[v]) == type:
                rep = str(g[v])
                item = QTreeWidgetItem()
                item.setText(0, rep)
                item.setToolTip(0, v)
                self._modules.addTopLevelItem(item)
                # self._modules.addItem(item)
            elif isinstance(g[v], (types.ModuleType, types.FunctionType)):
                rep = str(g[v])
                item = QTreeWidgetItem()
                item.setText(0, rep)
                item.setToolTip(0, v)
                self._modules.addTopLevelItem(item)
                # self._modules.addItem(item)
            else:
                item = QTreeWidgetItem()
                item.setText(0, '{} ({})'.format(v, type(g[v])))
                rep = str(g[v])
                item.setToolTip(0, rep)
                self._globals.addTopLevelItem(item)
                # self._globals.addItem(item)
        
    # Public methods

    def getPopup(self):
        return self._popup

    def pushVariables(self, v):
        if v is not None:
            if isinstance(v, dict):
                self._console.kernel_manager.kernel.shell.push(v)
            else: raise TypeError('parameter type {} is not dict.'.format(type(v)))

    def clear(self):
        self._console.clear()

    def copy(self):
        self._console.copy()

    def restart(self):
        self._console.reset(clear=True)
        self.pushVariables(self._variables)
        self._console.execute('%matplotlib inline')
        self.update()

    def save(self):
        try: self._console.export_html()
        except Exception as err: QMessageBox.warning(self, 'Save console display to HTML/XML.',
                                                     'error : {}'.format(err))

    def importMain(self):
        if self._mainwindow is not None:
            v = {'pysisyphe': self._mainwindow}
            self.pushVariables(v)
            self.update()

    def setMainWindow(self, w):
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(w, WindowSisyphe):
            self._mainwindow = w
        else:
            raise TypeError('parameter type {} is not WindowSisyphe.'.format(type(w)))

    def getMainWindow(self):
        return self._mainwindow

    def hasMainWindow(self):
        return self._mainwindow is not None

    # Qt event

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy): self.copy()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv
    from PyQt5.QtWidgets import QApplication

    app = QApplication(argv)
    main = ConsoleWidget()
    main.show()
    app.exec_()
