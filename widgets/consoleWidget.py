"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - qtconsole, Python console widget, https://qtconsole.readthedocs.io/en/stable/
"""

from sys import platform

from os.path import join
from os.path import exists
from os.path import abspath
from os.path import dirname

import types

import pkgutil

# < Revision 19/02/2025
from ants.core.ants_image import ANTsImage
# from Sisyphe.lib.ants.ants_image import ANTsImage
# Revision 19/02/2025 >

from numpy import ndarray

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton

from SimpleITK import Image as sitkImage

from vtk import vtkImageData

import darkdetect

from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.basicWidgets import messageBox

__all__ = ['ConsoleWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> ConsoleWidget

"""

class ConsoleWidget(QWidget):
    """
    Description
    ~~~~~~~~~~~

    Embedded IPython Qt console.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ConsoleWidget

    Last revision: 25/04/2025
    """

    @classmethod
    def isDarkMode(cls) -> bool:
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        return darkdetect.isLight()

    @classmethod
    def getDocDirectory(cls) -> str:
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'doc')
    
    # Special method

    """
    Private attribute

    _mainwindow     WindowSisyphe, PySisyphe main window
    _variables      dict
    _console        RichJupyterWidget
    _modules        QTreeWidget
    _globals        QTreeWidget
    _action         dict[QAction]
    _popup          QMenu
    """

    def __init__(self, variables=None, parent=None):
        super().__init__(parent)

        self._vol = None

        # Console

        self._mainwindow = None
        self._variables = variables
        # < Revision 08/03/2025
        # add font family and point size (QApplication font)
        self._console = RichJupyterWidget(gui_completion='droplist',
                                          font_family=self.font().family(),
                                          font_size=self.font().pointSize())
        # Revision 08/03/2025 >
        if self.isDarkMode(): self._console.set_default_style('linux')
        else: self._console.set_default_style('lightbg')
        self._console.paging = 'none'
        self._console.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel(show_banner=False)
        kernel_manager.kernel.gui = 'qt'
        self._console.kernel_client = kernel_client = self._console.kernel_manager.client()
        kernel_client.start_channels()
        self.pushVariables(variables)
        # self._console.execute('%config InProcessInteractiveShell.cache_size=0', hidden=True)
        self._console.execute('%matplotlib inline', hidden=True)
        if platform == 'win32':
            # bug fix of windows console encodings (code page 850 vs code page 1252)
            self._console.execute('import os', hidden=True)
            self._console.execute('os.system("chcp 65001")', hidden=True)

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
        # noinspection PyUnresolvedReferences
        self._globals.itemDoubleClicked.connect(self._globalsDblClicked)
        # noinspection PyUnresolvedReferences
        self._globals.itemClicked.connect(self._globalsClicked)
        # noinspection PyUnresolvedReferences
        self._modules.itemDoubleClicked.connect(self._modulesDblClicked)

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
        self._save = QPushButton('Save as HTML/XML...', parent=self)
        # noinspection PyUnresolvedReferences
        self._save.clicked.connect(self.save)
        self._save.setToolTip('Save console to HTML/XML file')
        # < Revision 25/04/2025
        # self._copy = QPushButton('Copy', parent=self)
        # self._copy.setToolTip('Copy selection to clipboard')
        # noinspection PyUnresolvedReferences
        # self._copy.clicked.connect(self.copy)
        # Revision 25/04/2025 >
        self._clear = QPushButton('Clear', parent=self)
        self._clear.setToolTip('Clear console display')
        # noinspection PyUnresolvedReferences
        self._clear.clicked.connect(self.clear)
        self._restart = QPushButton('Restart', parent=self)
        self._restart.setToolTip('Restart console')
        # noinspection PyUnresolvedReferences
        self._restart.clicked.connect(self.restart)
        self._import = QPushButton('Import', parent=self)
        self._import.setToolTip('Import PySisyphe modules')

        btnlyout.addStretch()
        btnlyout.addWidget(self._import)
        btnlyout.addWidget(self._clear)
        # < Revision 25/04/2025
        # btnlyout.addWidget(self._copy)
        # Revision 25/04/2025 >
        btnlyout.addWidget(self._restart)
        btnlyout.addWidget(self._save)

        # Popup menu

        self._action = dict()
        self._action['copy'] = QAction('Copy', self)
        self._action['clear'] = QAction('Clear', self)
        self._action['restart'] = QAction('Restart', self)
        self._action['save'] = QAction('Save as HTML/XML...', self)
        self._action['mod'] = QAction('View modules', self)
        self._action['glob'] = QAction('View Globals', self)
        self._action['mod'].setCheckable(True)
        self._action['glob'].setCheckable(True)
        self._action['mod'].setChecked(True)
        self._action['glob'].setChecked(True)
        self._action['main'] = QAction('PySisyphe main window as \"main\"', self)
        # noinspection PyUnresolvedReferences
        self._action['copy'].triggered.connect(self.copy)
        # noinspection PyUnresolvedReferences
        self._action['clear'].triggered.connect(self.clear)
        # noinspection PyUnresolvedReferences
        self._action['restart'].triggered.connect(self.restart)
        # noinspection PyUnresolvedReferences
        self._action['save'].triggered.connect(self.save)
        # noinspection PyUnresolvedReferences
        self._action['mod'].toggled.connect(self.setModuleVisibility)
        # noinspection PyUnresolvedReferences
        self._action['glob'].toggled.connect(self.setGlobalsVisibility)
        # noinspection PyUnresolvedReferences
        self._action['main'].triggered.connect(self.importMain)

        self._popup = QMenu()
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._popup.addAction(self._action['copy'])
        self._popup.addAction(self._action['clear'])
        self._popup.addAction(self._action['restart'])
        self._popup.addAction(self._action['save'])
        self._popup.addSeparator()
        self._popup.addAction(self._action['mod'])
        self._popup.addAction(self._action['glob'])
        self._popup.addSeparator()
        self._menuImport = self._popup.addMenu('Import')
        self._menuImport.addAction(self._action['main'])
        self._menuImport.addSeparator()
        import Sisyphe
        for pkg in pkgutil.iter_modules([join(Sisyphe.__path__[0], 'core')]):
            if not pkg.ispkg and pkg.name != 'PySisyphe':
                cmd = 'from Sisyphe.core.{} import *'.format(pkg.name)
                action = QAction(pkg.name, self)
                # noinspection PyUnresolvedReferences
                action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
                self._menuImport.addAction(action)
        self._menuImport.addSeparator()
        # ANTs
        cmd = 'import ants'
        action = QAction('ANTs', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Matplotlib
        cmd = 'from matplotlib import pyplot as plt'
        action = QAction('Matplotlib', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # NiBabel
        cmd = 'import nibabel as nib'
        action = QAction('NiBabel', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Nilearn
        cmd = 'import nilearn as nil'
        action = QAction('Nilearn', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Numpy
        cmd = 'import numpy as np'
        action = QAction('Numpy', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Pandas
        cmd = 'import pandas as pd'
        action = QAction('Pandas', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Pillow
        cmd = 'import PIL as pil'
        action = QAction('Pillow', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # PyDicom
        cmd = 'import pydicom as dcm'
        action = QAction('PyDicom', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # Scikit-image
        cmd = 'import skimage as ski'
        action = QAction('Scikit-image', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # SciPy
        cmd = 'import scipy as scp'
        action = QAction('SciPy', self)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda dummy, v=cmd: self._console.execute(v))
        self._menuImport.addAction(action)
        # SimpleITK
        cmd = 'import SimpleITK as sitk'
        action = QAction('SimpleITK', self)
        # noinspection PyUnresolvedReferences
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

    # noinspection PyUnusedLocal
    def _globalsDblClicked(self, item, c):
        if self.hasMainWindow():
            v = item.data(0, Qt.UserRole)
            if v != '':
                g = self._console.kernel_manager.kernel.shell.user_ns
                try:
                    if isinstance(g[v], (SisypheVolume, sitkImage, ANTsImage, vtkImageData, ndarray)):
                        if isinstance(g[v], SisypheVolume):
                            if not g[v].isEmpty():
                                self._vol = g[v].copy()
                                self._mainwindow.addVolume(self._vol)
                        elif isinstance(g[v], sitkImage):
                            self._vol = SisypheVolume()
                            self._vol.copyFromSITKImage(g[v])
                            self._mainwindow.addVolume(self._vol)
                        elif isinstance(g[v], ANTsImage):
                            self._vol = SisypheVolume()
                            self._vol.copyFromANTSImage(g[v])
                            self._mainwindow.addVolume(self._vol)
                        elif isinstance(g[v], vtkImageData):
                            self._vol = SisypheVolume()
                            self._vol.copyFromVTKImage(g[v])
                            self._mainwindow.addVolume(self._vol)
                        elif isinstance(g[v], ndarray):
                            if g[v].ndim == 3:
                                self._vol = SisypheVolume()
                                self._vol.copyFromNumpyArray(g[v])
                                self._mainwindow.addVolume(self._vol)
                except: return

    # noinspection PyUnusedLocal
    def _globalsClicked(self, item, c):
        v = item.data(0, Qt.UserRole)
        if v != '':
            g = self._console.kernel_manager.kernel.shell.user_ns
            try:
                if isinstance(g[v], (SisypheVolume, sitkImage, ANTsImage, vtkImageData, ndarray)):
                    info = '{}:\n{}'.format('Double-click to open in PSisyphe', str(g[v]))
                    item.setToolTip(0, info)
                else:
                    info = str(g[v])
                    item.setToolTip(0, info)
            except: return

    # noinspection PyUnusedLocal
    def _modulesDblClicked(self, item, c):
        if self.hasMainWindow():
            v = item.data(0, Qt.UserRole)
            if v != '':
                g = self._console.kernel_manager.kernel.shell.user_ns
                try:
                    module = g[v].__module__
                    if module[:12] == 'Sisyphe.core':
                        self._mainwindow.getDock().setCurrentIndex(5)
                        self._mainwindow.getHelp().setSearch(v)
                except: return

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
                info = '{}:\n{}'.format(v, g[v].__doc__)
                item.setToolTip(0, info)
                item.setData(0, Qt.UserRole, v)
                self._modules.addTopLevelItem(item)
            elif isinstance(g[v], (types.ModuleType, types.FunctionType)):
                rep = str(g[v])
                item = QTreeWidgetItem()
                item.setText(0, rep)
                info = '{}:\n{}'.format(v, g[v].__doc__)
                item.setToolTip(0, info)
                self._modules.addTopLevelItem(item)
            else:
                item = QTreeWidgetItem()
                item.setText(0, '{} ({})'.format(v, type(g[v])))
                if isinstance(g[v], (SisypheVolume, sitkImage, ANTsImage, vtkImageData, ndarray)):
                    item.setData(0, Qt.UserRole, v)
                    rep = '{}:\n{}'.format('Double-click to open in PSisyphe', str(g[v]))
                else:
                    item.setData(0, Qt.UserRole, v)
                    rep = str(g[v])
                item.setToolTip(0, rep)
                self._globals.addTopLevelItem(item)
        
    # Public methods

    def setModuleVisibility(self, v: bool = True):
        self._modules.setVisible(v)

    def getModuleVisibility(self):
        return self._modules.isVisible()

    def setGlobalsVisibility(self, v: bool = True):
        self._globals.setVisible(v)

    def getGlobalsVisibility(self):
        return self._globals.isVisible()

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
        self._console.execute('%matplotlib inline', hidden=True)
        self.update()

    def save(self):
        try: self._console.export_html()
        except Exception as err: messageBox(self,
                                            'Save console display to HTML/XML.',
                                            text='error : {}'.format(err))

    def importMain(self):
        if self._mainwindow is not None:
            v = {'main': self._mainwindow}
            self.pushVariables(v)
            self.update()

    def setFont(self, font: QFont):
        # noinspection PyProtectedMember
        self._console._set_font(font)

    def setMainWindow(self, w):
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(w, WindowSisyphe): self._mainwindow = w
        else: raise TypeError('parameter type {} is not WindowSisyphe.'.format(type(w)))

    def getMainWindow(self):
        return self._mainwindow

    def hasMainWindow(self):
        return self._mainwindow is not None

    # Qt event

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy): self.copy()
