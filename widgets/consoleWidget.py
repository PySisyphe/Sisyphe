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

from numpy import array
from numpy import ndarray

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint
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
# < Revision 02/12/2025
from SimpleITK import GetArrayViewFromImage
# Revision 02/12/2025 >

from vtk import vtkImageData

import darkdetect

from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget

from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.gui.dialogFromXml import DialogFromXml

__all__ = ['ConsoleWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> ConsoleWidget

"""

class RichJupyterWidget2(RichJupyterWidget):

    def _event_filter_console_keypress(self, event):
        # noinspection PyProtectedMember
        r = super()._event_filter_console_keypress(event)
        k = event.text()
        if k == '.':
            self._control.insertPlainText('.')
            self._complete()
            r = True
        elif k == '(':
            self._control.insertPlainText('()')
            self._control.moveCursor(9, 0)
            r = True
        elif k == '[':
            self._control.insertPlainText('[]')
            self._control.moveCursor(9, 0)
            r = True
        elif k == '{':
            self._control.insertPlainText('{}')
            self._control.moveCursor(9, 0)
            r = True
        elif k == '\'':
            self._control.insertPlainText('\'\'')
            self._control.moveCursor(9, 0)
            r = True
        elif k == '\"':
            self._control.insertPlainText('\"\"')
            self._control.moveCursor(9, 0)
            r = True
        return r


class ConsoleWidget(QWidget):
    """
    Description
    ~~~~~~~~~~~

    Embedded IPython Qt console.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ConsoleWidget

    Last revision: 01/12/2025
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
        # < Revision 01/12/2025
        # self._console = RichJupyterWidget(gui_completion='droplist',
        #                                   font_family=self.font().family(),
        #                                   font_size=self.font().pointSize())
        self._console = RichJupyterWidget2(gui_completion='droplist',
                                           font_family=self.font().family(),
                                           font_size=self.font().pointSize())
        # Revision 01/12/2025 >
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
        self._modules.setHeaderLabel('Module(s) / Type(s) / Function(s)')
        self._modules.setToolTip('Module(s) / Type(s) / Function(s)')
        self._modules.setAlternatingRowColors(True)
        # noinspection PyUnresolvedReferences
        self._modules.itemDoubleClicked.connect(self._modulesDblClicked)

        self._globals = QTreeWidget()
        self._globals.setHeaderLabel('Variables')
        self._globals.setToolTip('Variables')
        self._globals.setAlternatingRowColors(True)
        # < Revision 01/12/2025
        self._globals.setContextMenuPolicy(Qt.CustomContextMenu)
        # noinspection PyUnresolvedReferences
        self._globals.customContextMenuRequested.connect(self._popupGlobals)
        # Revision 01/12/2025 >
        # noinspection PyUnresolvedReferences
        self._globals.itemDoubleClicked.connect(self._globalsDblClicked)
        # noinspection PyUnresolvedReferences
        self._globals.itemClicked.connect(self._globalsClicked)

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

    # < Revision 01/12/2025
    # add _popupGlobals method
    # noinspection PyTypeChecker
    def _popupGlobals(self, p: QPoint):
        item = self._globals.itemAt(p)
        if item is not None:
            g = self._console.kernel_manager.kernel.shell.user_ns
            try:
                v = g[item.data(0, Qt.UserRole)]
                popup = QMenu()
                popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                popup.setWindowFlag(Qt.FramelessWindowHint, True)
                popup.setAttribute(Qt.WA_TranslucentBackground, True)
                actions = dict()
                actions['plot'] = QAction('Line plot')
                actions['bar'] = QAction('Bar plot')
                actions['stairs'] = QAction('Stairs plot')
                actions['box'] = QAction('Box-and-Whisker plot')
                actions['violin'] = QAction('Violin plot')
                actions['hist'] = QAction('Histogram plot')
                actions['scatter'] = QAction('Scatter plot')
                actions['mat'] = QAction('Matrix plot')
                actions['image'] = QAction('Image plot')
                actions['plot'].triggered.connect(lambda _: self._plot(0, item))
                actions['bar'].triggered.connect(lambda _: self._plot(1, item))
                actions['stairs'].triggered.connect(lambda _: self._plot(2, item))
                actions['box'].triggered.connect(lambda _: self._plot(3, item))
                actions['violin'].triggered.connect(lambda _: self._plot(4, item))
                actions['hist'].triggered.connect(lambda _: self._plot(5, item))
                actions['scatter'].triggered.connect(lambda _: self._plot(6, item))
                actions['mat'].triggered.connect(lambda _: self._plot(7, item))
                actions['image'].triggered.connect(lambda _: self._plot(8, item))
                # Revision 01/12/2025 >
                if isinstance(v, list): v = array(v)
                if isinstance(v, sitkImage):
                    if v.GetDimension() == 2:
                        popup.addAction(actions['image'])
                        popup.exec(self._globals.mapToGlobal(p))
                if isinstance(v, ndarray):
                    if v.ndim < 3:
                        if v.ndim == 1:
                            popup.addAction(actions['plot'])
                            popup.addAction(actions['bar'])
                            popup.addAction(actions['stairs'])
                            popup.addAction(actions['box'])
                            popup.addAction(actions['violin'])
                            popup.addAction(actions['hist'])
                        elif v.ndim == 2:
                            if 2 in v.shape:
                                popup.addAction(actions['plot'])
                                popup.addAction(actions['bar'])
                                popup.addAction(actions['stairs'])
                                popup.addAction(actions['box'])
                                popup.addAction(actions['violin'])
                                popup.addAction(actions['hist'])
                                popup.addAction(actions['scatter'])
                            else:
                                popup.addAction(actions['plot'])
                                popup.addAction(actions['bar'])
                                popup.addAction(actions['stairs'])
                                popup.addAction(actions['box'])
                                popup.addAction(actions['violin'])
                                popup.addAction(actions['hist'])
                                popup.addAction(actions['mat'])
                                popup.addAction(actions['image'])
                        popup.exec(self._globals.mapToGlobal(p))
            except: pass
    # Revision 01/12/2025 >

    # < Revision 01/12/2025
    # add _plot method
    def _plot(self, chart: int, item: QTreeWidgetItem) -> None:
        g = self._console.kernel_manager.kernel.shell.user_ns
        try:
            vstr = item.data(0, Qt.UserRole)
            v = g[vstr]
            if isinstance(v, list): v = array(v)
            if isinstance(v, sitkImage): v = GetArrayViewFromImage(v)
            if isinstance(v, ndarray):
                if v.ndim in (1, 2):
                    self._console.execute('import numpy as np', hidden=True)
                    self._console.execute('import matplotlib.pyplot as plt', hidden=True)
                    #
                    # Line plot
                    #
                    if chart == 0:
                        dialog = DialogFromXml('Line plot settings', 'LinePlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            ls = settings['linestyle'][0].split(' ')[0]
                            gls = settings['glinestyle'][0].split(' ')[0]
                            mk = settings['marker'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            if v.ndim == 1: buff = 'r = ax.plot(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.plot(np.array({}).T, '.format(vstr)
                            buff += 'ls=\'{}\', '.format(ls)
                            buff += 'lw={}, '.format(float(settings['linewidth']))
                            buff += 'marker=\'{}\', '.format(mk)
                            buff += 'ms={})'.format(float(settings['markersize']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['raxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Bar plot
                    #
                    elif chart == 1:
                        dialog = DialogFromXml('Bar plot settings', 'BarPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            ls = settings['linestyle'][0].split(' ')[0]
                            gls = settings['glinestyle'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            if v.ndim == 1: buff = 'r = plt.bar(range(len({0})), np.array({0}), '.format(vstr)
                            else: buff = 'r = plt.bar(range({0}.shape[1]), np.array({0}).T, '.format(vstr)
                            buff += 'width={}, '.format(float(settings['barwidth']))
                            buff += 'ls=\'{}\', '.format(ls)
                            buff += 'lw={})'.format(float(settings['linewidth']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Stairs plot
                    #
                    elif chart == 2:
                        dialog = DialogFromXml('Stairs plot settings', 'StairsPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            ls = settings['linestyle'][0].split(' ')[0]
                            gls = settings['glinestyle'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            if v.ndim == 1: buff = 'r = plt.stairs(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.stairs(np.array({}).T, '.format(vstr)
                            buff += 'fill={}, '.format(str(settings['fill']))
                            buff += 'ls=\'{}\', '.format(ls)
                            buff += 'lw={})'.format(float(settings['linewidth']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Box-and-Whisker plot
                    #
                    elif chart == 3:
                        dialog = DialogFromXml('Box & Whisker plot settings', 'WhiskerPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            sym = settings['symbol'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            gls = settings['glinestyle'][0].split(' ')[0]
                            if v.ndim == 1: buff = 'r = plt.boxplot(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.boxplot(np.array({}).T, '.format(vstr)
                            buff += 'notch={}, '.format(str(settings['notch']))
                            buff += 'sym=\'{}\', '.format(sym)
                            buff += 'widths={}, '.format(float(settings['boxwidth']))
                            buff += 'showcaps={}, '.format(str(settings['showcaps']))
                            buff += 'showbox={}, '.format(str(settings['showbox']))
                            buff += 'showfliers={}, '.format(str(settings['showfliers']))
                            buff += 'showmeans={})'.format(str(settings['showmeans']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={})'.format(str(settings['grid'])), hidden=True)

                            self._console.execute('ax.get_xgridlines().set_linestyle(\'{}\')'.format(gls), hidden=True)
                            self._console.execute('ax.get_xgridlines().set_linewidth({})'.format(float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.get_xgridlines().set_color(({}, {}, {}))'.format(gcolor[0], gcolor[1], gcolor[2]), hidden=True)
                            self._console.execute('ax.get_ygridlines().set_linestyle(\'{}\')'.format(gls), hidden=True)
                            self._console.execute('ax.get_ygridlines().set_linewidth({})'.format(float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.get_ygridlines().set_color(({}, {}, {}))'.format(gcolor[0], gcolor[1], gcolor[2]), hidden=True)

                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Violin plot
                    #
                    elif chart == 4:
                        dialog = DialogFromXml('Violin plot settings', 'ViolinPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            gls = settings['glinestyle'][0].split(' ')[0]
                            if v.ndim == 1: buff = 'r = plt.violinplot(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.violinplot(np.array({}).T, '.format(vstr)
                            buff += 'widths={}, '.format(float(settings['boxwidth']))
                            buff += 'showmeans={}, '.format(str(settings['showmeans']))
                            buff += 'showextrema={}, '.format(str(settings['showextrema']))
                            buff += 'showmedians={})'.format(str(settings['showmedians']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Histogram plot
                    #
                    elif chart == 5:
                        dialog = DialogFromXml('Histogram plot settings', 'HistPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            gls = settings['glinestyle'][0].split(' ')[0]
                            if v.ndim == 1: buff = 'r = plt.hist(np.array({}), '.format(vstr)
                            else: buff = 'r = plt.hist(np.array({}).T, '.format(vstr)
                            buff += 'cumulative={}, '.format(str(settings['cumulative']))
                            buff += 'histtype=\'{}\')'.format(settings['histtype'][0])
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Scatter plot
                    #
                    elif chart == 6:
                        dialog = DialogFromXml('Scatter plot settings', 'ScatterPlot')
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            mk = settings['marker'][0].split(' ')[0]
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            gcolor = settings['gcolor']
                            gls = settings['glinestyle'][0].split(' ')[0]
                            if v.shape[0] == 2: self._console.execute('buff = np.array({})'.format(vstr), hidden=True)
                            elif v.shape[1] == 2: self._console.execute('buff = np.array({}).T'.format(vstr), hidden=True)
                            else: return
                            buff = 'r = ax.scatter(buff[0], buff[1], '
                            buff += 'marker=\'{}\')'.format(mk)
                            # buff += 'ms={})'.format(float(settings['markersize']))
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible({})'.format(str(settings['laxis'])), hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible({})'.format(str(settings['baxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.grid(visible={}, color=({}, {}, {}), ls=\'{}\', lw={})'.format(str(settings['grid']),
                                                                                                                     gcolor[0], gcolor[1], gcolor[2],
                                                                                                                     gls,
                                                                                                                     float(settings['glinewidth'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('del buff', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Matrix plot
                    #
                    elif chart == 7:
                        dialog = DialogFromXml('Matrix plot settings', 'MatrixPlot')
                        dialog.getFieldsWidget().getParameterWidget('cmap').removeFilesLut()
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            cmap = SisypheLut.getInternalColormapFromName(settings['cmap'])
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            buff = 'r = ax.matshow(np.array({}), '.format(vstr)
                            buff += 'cmap=\'{}\')'.format(cmap)
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            if settings['colorbar']:
                                self._console.execute('from mpl_toolkits.axes_grid1 import make_axes_locatable', hidden=True)
                                self._console.execute('d = make_axes_locatable(ax)', hidden=True)
                                self._console.execute('cax = d.append_axes(\'right\', size=\'5%\', pad=0.05)', hidden=True)
                                self._console.execute('fig.colorbar(r, cax=cax, orientation=\'vertical\')', hidden=True)
                                self._console.execute('del d', hidden=True)
                                self._console.execute('del cax', hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
                    #
                    # Image plot
                    #
                    elif chart == 8:
                        dialog = DialogFromXml('Matrix plot settings', 'MatrixPlot')
                        dialog.getFieldsWidget().getParameterWidget('cmap').removeFilesLut()
                        if platform == 'win32':
                            import pywinstyles
                            cl = self.palette().base().color()
                            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                            pywinstyles.change_header_color(dialog, c)
                        if dialog.exec() == dialog.Accepted:
                            settings = dialog.getFieldsDict()
                            cmap = SisypheLut.getInternalColormapFromName(settings['cmap'])
                            title = settings['title']
                            xlabel = settings['xlabel']
                            ylabel = settings['ylabel']
                            color = settings['color']
                            if isinstance(g[vstr], sitkImage):
                                self._console.execute('from SimpleITK import GetArrayFromImage', hidden=True)
                                self._console.execute('buff = GetArrayFromImage({})'.format(vstr), hidden=True)
                            else: self._console.execute('buff = np.array({}), '.format(vstr), hidden=True)
                            buff = 'r = ax.imshow(np.fliplr(buff), origin=\'lower\', '
                            buff += 'cmap=\'{}\')'.format(cmap)
                            self._console.execute('plt.ioff()', hidden=True)
                            self._console.execute('fig, ax = plt.subplots()', hidden=True)
                            self._console.execute('fig.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.set_facecolor(({}, {}, {}))'.format(color[0], color[1], color[2]), hidden=True)
                            self._console.execute('ax.spines[\'top\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.spines[\'right\'].set_visible({})'.format(str(settings['taxis'])), hidden=True)
                            self._console.execute('ax.get_xaxis().set_visible(False)', hidden=True)
                            self._console.execute('ax.get_yaxis().set_visible(False)', hidden=True)
                            self._console.execute('ax.set_frame_on({})'.format(str(settings['frame'])), hidden=True)
                            self._console.execute('ax.set_title(\'{}\')'.format(title), hidden=True)
                            self._console.execute('ax.set_xlabel(\'{}\')'.format(xlabel), hidden=True)
                            self._console.execute('ax.set_ylabel(\'{}\')'.format(ylabel), hidden=True)
                            self._console.execute(buff, hidden=True)
                            if settings['colorbar']:
                                self._console.execute('from mpl_toolkits.axes_grid1 import make_axes_locatable', hidden=True)
                                self._console.execute('d = make_axes_locatable(ax)', hidden=True)
                                self._console.execute('cax = d.append_axes(\'right\', size=\'5%\', pad=0.05)', hidden=True)
                                self._console.execute('fig.colorbar(r, cax=cax, orientation=\'vertical\')', hidden=True)
                                self._console.execute('del d', hidden=True)
                                self._console.execute('del cax', hidden=True)
                            self._console.execute('del buff', hidden=True)
                            self._console.execute('plt.ion()', hidden=True)
                            self._console.execute('plt.show(block=False)', hidden=False)
                            dialog.getFieldsWidget().saveSettings()
        except: pass
    # Revision 01/12/2025 >

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

    # < Revision 29/11/2025
    # add hasVariable method
    def hasVariable(self, v: str) -> bool:
        """
        Check if a variable exists in the console.

        Parameters
        ----------
        v : str
            variable name to check.

        Returns
        -------
        bool
            True if the variable exists in the console, False otherwise.
        """
        g = self._console.kernel_manager.kernel.shell.user_ns
        k = g.keys()
        return v in k
    # Revision 29/11/2025 >

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
