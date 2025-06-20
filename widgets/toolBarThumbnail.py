""""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import getcwd
from os import chdir

from os.path import dirname
from os.path import basename
from os.path import splitext
from os.path import abspath

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QButtonGroup
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.imageWidgets import SisypheVolumeThumbnailButtonWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QToolBar -> ToolBarThumbnail
    
Description
~~~~~~~~~~~

Thumbnail bar widget typically placed at the top of the main window. 
Shows SisypheVolume loaded in PySisyphe environment.
Container of SisypheVolumeThumbnailButtonWidget.
"""


class ToolBarThumbnail(QToolBar):
    """
    ToolBarThumbnail class

    Description
    ~~~~~~~~~~~

    Image thumbnail bar widget typically placed at the top of the main window.
    Shows SisypheVolume loaded in PySisyphe environment.
    Container of SisypheVolumeThumbnailButtonWidget.

    Inheritance
    ~~~~~~~~~~~

    QToolBar -> ToolBarThumbnail

    Creation: 02/11/2022
    Last revision: 03/06/2025
    """

    # Special method

    """
    Private attributes

    _actions    list[SisypheVolumeThumbnailButtonWidget]
    _parent     QWidget
    """

    def __init__(self, size=128, mainwindow=None, views=None, parent=None):
        super().__init__(parent)

        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(mainwindow, WindowSisyphe): self._mainwindow = mainwindow
        else: self._mainwindow = None

        from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
        if isinstance(views, IconBarViewWidgetCollection): self._views = views
        else: self._views = None

        # self._actions = list()
        self._size = size
        self._group = QButtonGroup()
        self._group.setExclusive(True)

        policy = QSizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Fixed)
        policy.setHorizontalPolicy(QSizePolicy.Expanding)
        self.setSizePolicy(policy)
        self.setFixedHeight(size + 8)
        self.setMovable(False)
        self.setContentsMargins(5, 5, 5, 5)

        self.setToolTip('Double-click to open volume,\n'
                        'Right-click to display popup menu,\n'
                        'Drag and drop volume from finder to open it.')

        self.setStyleSheet('QPushButton#ThumbnailButton { max-height: 256px; } '
                           'QPushButton#ThumbnailButton:closed { background-color: black; border-color: black; border-style: solid; border-width: 8px; border-radius: 20px; } '
                           'QPushButton#ThumbnailButton:checked { background-color: black; border-color: rgb(0, 125, 255); border-style: solid; border-width: 8px; border-radius: 20px; } '
                           'QPushButton#ThumbnailButton:pressed { background-color: black; border-color: white; border-style: solid; border-width: 8px; border-radius: 20px; }')

        # Init popup menu

        self._popup = QMenu(self)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action = dict()
        self._action['open'] = QAction('Open volume', self)
        self._action['saveall'] = QAction('Save all volume(s)', self)
        self._action['closeall'] = QAction('Close all volume(s)', self)
        # noinspection PyUnresolvedReferences
        self._action['open'].triggered.connect(lambda dummy: self.open())
        # noinspection PyUnresolvedReferences
        self._action['saveall'].triggered.connect(self.saveAll)
        # noinspection PyUnresolvedReferences
        self._action['closeall'].triggered.connect(self.removeAll)
        self._popup.addAction(self._action['open'])
        self._popup.addAction(self._action['saveall'])
        self._popup.addAction(self._action['closeall'])

        # Drag and Drop

        self.setAcceptDrops(True)

    # Public method

    def setSize(self, s):
        if isinstance(s, int):
            self._size = s
            self.setFixedHeight(self._size + 8)
            n = self.getWidgetsCount()
            if n > 0:
                for i in range(n):
                    widget = self.getWidgetFromIndex(i)
                    widget.setSize(s)
        else: raise TypeError('parameter type {} is not int'.format(s))

    def getSize(self):
        return self._size

    def setMainWindow(self, w):
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(w, WindowSisyphe): self._mainwindow = w
        else: raise TypeError('parameter type {} is not WindowSisyphe.'.format(type(w)))

    def getMainWindow(self):
        return self._mainwindow

    def hasMainWindow(self):
        return self._mainwindow is not None

    def getViewsWidget(self):
        return self._views

    def setViewsWidget(self, w):
        from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
        if isinstance(w, IconBarViewWidgetCollection): self._views = w
        else: raise TypeError('parameter type {} is not IconBarViewWidgetCollection.'.format(type(w)))

    def hasViewsWidget(self):
        return self._views is not None

    def updateWidgets(self):
        if not self.isEmpty():
            # for i in range(0, len(self._actions)):
            for i in range(0, len(self.actions())):
                # widget = self._actions[i].defaultWidget()
                # noinspection PyUnresolvedReferences
                widget = self.actions()[i].defaultWidget()
                if not widget.isChecked():
                    widget.getActions()['slices'].setChecked(False)
                    widget.getActions()['orthogonal'].setChecked(False)
                    widget.getActions()['synchronised'].setChecked(False)
                    widget.getActions()['projections'].setChecked(False)
                    # < Revision 13/12/2024
                    widget.getActions()['multi'].setChecked(False)
                    # Revision 13/12/2024 >

    def getWidgetsCount(self):
        # return len(self._actions)
        return len(self.actions())

    def getSelectedIndex(self):
        if not self.isEmpty():
            # for i in range(0, len(self._actions)):
            for i in range(0, len(self.actions())):
                # if self._actions[i].defaultWidget().isChecked(): return i
                # noinspection PyUnresolvedReferences
                if self.actions()[i].defaultWidget().isChecked(): return i
        return None

    def getSelectedWidget(self):
        if not self.isEmpty():
            # for action in self._actions:
            for action in self.actions():
                # noinspection PyUnresolvedReferences
                if action.defaultWidget().isChecked():
                    # noinspection PyUnresolvedReferences
                    return action.defaultWidget()
        return None

    def getSelectedVolume(self):
        if not self.isEmpty():
            # for action in self._actions:
            for action in self.actions():
                # noinspection PyUnresolvedReferences
                if action.defaultWidget().isChecked():
                    # noinspection PyUnresolvedReferences
                    return action.defaultWidget().getVolume()
        return None

    def hasReference(self):
        if not self.isEmpty():
            # for action in self._actions:
            for action in self.actions():
                # noinspection PyUnresolvedReferences
                if action.defaultWidget().isChecked(): return True
        return False

    def getReference(self):
        if not self.isEmpty():
            # for action in self._actions:
            for action in self.actions():
                # noinspection PyUnresolvedReferences
                if action.defaultWidget().isChecked():
                    # noinspection PyUnresolvedReferences
                    return action.defaultWidget().getVolume()
        return None

    # < Revision 15/10/2024
    # add hasOverlay method
    def hasOverlay(self):
        if not self.isEmpty():
            # for action in self._actions:
            for action in self.actions():
                # noinspection PyUnresolvedReferences
                if action.defaultWidget().isDown(): return True
        return False
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # add getOverlays method
    def getOverlays(self):
        r = list()
        if not self.isEmpty():
            # for action in self._actions:
            for action in self.actions():
                # noinspection PyUnresolvedReferences
                if action.defaultWidget().isDown():
                    # < Revision 25/10/2024
                    # bugfix
                    # return action.defaultWidget().getVolume()
                    # noinspection PyUnresolvedReferences
                    r.append(action.defaultWidget().getVolume())
                    # Revision 25/10/2024 >
        return r
    # Revision 15/10/2024 >

    # < Revision 06/11/2024
    # add getOverlayCount method
    def getOverlayCount(self):
        n = 0
        if not self.isEmpty():
            # for action in self._actions:
            for action in self.actions():
                # noinspection PyUnresolvedReferences
                if action.defaultWidget().isDown(): n += 1
        return n
    # Revision 06/11/2024 >

    def getWidgetFromIndex(self, index):
        if isinstance(index, int):
            # if 0 <= index < len(self._actions):
            if 0 <= index < len(self.actions()):
                # return self._actions[index].defaultWidget()
                # noinspection PyUnresolvedReferences
                return self.actions()[index].defaultWidget()
            else: raise ValueError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def getVolumeFromIndex(self, index):
        if isinstance(index, int):
            # if 0 <= index < len(self._actions):
            if 0 <= index < len(self.actions()):
                # return self._actions[index].defaultWidget().getVolume()
                # noinspection PyUnresolvedReferences
                return self.actions()[index].defaultWidget().getVolume()
            else: raise ValueError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def getVolumeIndex(self, vol):
        if isinstance(vol, SisypheVolume):
            if not self.isEmpty():
                # for i in range(0, len(self._actions)):
                for i in range(0, len(self.actions())):
                    # if self._actions[i].defaultWidget().getVolume().getArrayID() == vol.getArrayID(): return i
                    # noinspection PyUnresolvedReferences
                    if self.actions()[i].defaultWidget().getVolume().getArrayID() == vol.getArrayID(): return i
            return None
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def containsVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            if not self.isEmpty():
                # for action in self._actions:
                for action in self.actions():
                    # noinspection PyUnresolvedReferences
                    if action.defaultWidget().getVolume().getArrayID() == vol.getArrayID(): return True
            return False
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def removeVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            if not self.isEmpty():
                # for action in self._actions:
                for action in self.actions():
                    # noinspection PyUnresolvedReferences
                    w = action.defaultWidget()
                    if w.getVolume() == vol:
                        if w.isChecked():
                            if self.hasMainWindow():
                                self._mainwindow.clearDockListWidgets()
                            self._views.removeVolume()
                            self.removeAllOverlays()
                        elif w.getActions()['overlay'].isChecked():
                            self._views.removeOverlay(vol)
                        self.removeAction(action)
                        # self._actions.remove(action)
            if self.hasMainWindow():
                self._mainwindow.updateMemoryUsage()
                self._mainwindow.setStatusBarMessage('Volume {} closed.'.format(vol.getBasename()))
                if not self.hasReference():
                    self._mainwindow.setDockEnabled(False)
                    # < Revision 16/102024
                    self._mainwindow.hideViewWidgets()
                    # Revision 16/10/2024 >
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def removeAllOverlays(self):
        n = self.getWidgetsCount()
        if n > 0:
            for i in range(n):
                self.getWidgetFromIndex(i).getActions()['overlay'].setChecked(False)
                self.getWidgetFromIndex(i).setDown(False)

    def addVolume(self, vol, wait=None):
        if isinstance(vol, SisypheVolume):
            # noinspection PyInconsistentReturns
            if not self.containsVolume(vol):
                if not self.isFull():
                    widget = SisypheVolumeThumbnailButtonWidget(vol, size=self._size, thumbnail=self, views=self._views)
                    QApplication.processEvents()
                    self._group.addButton(widget)
                    action = QWidgetAction(self)
                    action.setDefaultWidget(widget)
                    self.addAction(action)
                    # self._actions.append(action)
                    if self.hasMainWindow():
                        if vol.hasFilename: self._mainwindow.addRecent(vol.getFilename())
                        self._mainwindow.updateMemoryUsage()
                        self._mainwindow.setStatusBarMessage('Volume {} opened.'.format(vol.getBasename()))
                    return True
                else:
                    if wait is not None: wait.hide()
                    messageBox(self,
                               'Add PySisyphe volume',
                               text='Thumbnail is full.\n'
                                    'Close a volume to open a new one.',
                               icon=QMessageBox.Information)
                    return False
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(vol)))

    def open(self, filenames=None):
        if not self.isFull():
            title = 'Open PySisyphe volume(s)'
            if filenames is None: filenames = QFileDialog.getOpenFileNames(self, title, getcwd(), '*.xvol')[0]
            if isinstance(filenames, str): filenames = [filenames]
            if isinstance(filenames, list):
                n = len(filenames)
                if n > 0:
                    chdir(dirname(filenames[0]))
                    if n == 1:
                        progress = False
                        cancel = False
                    else:
                        progress = True
                        cancel = True
                    wait = DialogWait()
                    wait.open()
                    wait.setProgressRange(0, n)
                    wait.setProgressTextVisibility(True)
                    wait.setProgressVisibility(progress)
                    wait.setButtonVisibility(cancel)
                    for filename in filenames:
                        filename = abspath(filename)
                        if not wait.isVisible(): wait.show()
                        wait.setInformationText('Open {}...'.format(basename(filename)))
                        wait.incCurrentProgressValue()
                        vol = SisypheVolume()
                        try:
                            vol.load(filename)
                            QApplication.processEvents()
                        except Exception as err:
                            messageBox(self, 'Open PySisyphe volume', text='{}'.format(err))
                        if not self.containsVolume(vol):
                            # < Revision 10/12/2024
                            # multi-component management
                            if not self.addVolume(vol, wait): break
                            # Revision 10/12/2024 >
                            QApplication.processEvents()
                        else:
                            wait.hide()
                            messageBox(self,
                                       title=title,
                                       text='This volume is already open.',
                                       icon=QMessageBox.Information)
                        if wait.getStopped(): break
                    wait.close()
        else:
            messageBox(self,
                       'Open PySisyphe volume',
                       text='Thumbnail is full.'
                            'Close a volume to open a new one.',
                       icon=QMessageBox.Information)

    def saveSelected(self):
        w = self.getSelectedWidget()
        if w is not None: w.save()
        else: messageBox(self,
                         'Save PySisyphe volume',
                         'No displayed volume to save.',
                         icon=QMessageBox.Information)
        if self.hasMainWindow():
            self._mainwindow.setStatusBarMessage('Reference volume saved.')

    def saveSelectedAs(self):
        w = self.getSelectedWidget()
        if w is not None: w.saveas()
        else: messageBox(self,
                         'Save PySisyphe volume',
                         'No displayed volume to save.',
                         icon=QMessageBox.Information)
        if self.hasMainWindow():
            self._mainwindow.setStatusBarMessage('Reference volume saved.')

    def saveAll(self):
        if not self.isEmpty():
            # for i in range(len(self._actions)):
            for i in range(len(self.actions())):
                v = self.getVolumeFromIndex(i)
                v.save()
            if self.hasMainWindow():
                self._mainwindow.setStatusBarMessage('All volumes saved.')

    def editAttributesSelected(self):
        w = self.getSelectedWidget()
        if w is not None:
            w.editAttributes()
        else: messageBox(self,
                         'Edit PySisyphe volume attributes',
                         'No displayed volume to edit.',
                         icon=QMessageBox.Information)

    def removeSelected(self):
        if not self.isEmpty():
            if self.hasMainWindow():
                self._mainwindow.clearDockListWidgets()
            # for action in self._actions:
            for action in self.actions():
                # noinspection PyUnresolvedReferences
                if action.defaultWidget().isChecked():
                    self._views.removeVolume()
                    self.removeAction(action)
                    # self._actions.remove(action)
                    # break
                # < Revision 19/03/2025
                # disable overlays
                elif action.defaultWidget().isDown():
                    # noinspection PyUnresolvedReferences
                    action.defaultWidget().setDown(False)
                # Revision 19/03/2025 >
            if self.hasMainWindow():
                self._mainwindow.updateTimers(-1)
                self._mainwindow.updateMemoryUsage()
                self._mainwindow.setStatusBarMessage('Reference volume closed.')
                self._mainwindow.setDockEnabled(False)
                # < Revision 16/102024
                self._mainwindow.hideViewWidgets()
                # Revision 16/10/2024 >

    def removeAll(self):
        if not self.isEmpty():
            if self.hasMainWindow():
                self._mainwindow.clearDockListWidgets()
            self.removeSelected()
            self.clear()
            # self._actions.clear()
            if self.hasMainWindow():
                self._mainwindow.updateTimers(-1)
                self._mainwindow.updateMemoryUsage()
                self._mainwindow.setStatusBarMessage('All volumes closed.')
                self._mainwindow.setDockEnabled(False)
                # < Revision 16/102024
                self._mainwindow.hideViewWidgets()
                # Revision 16/10/2024 >

    def isEmpty(self):
        # return len(self._actions) == 0
        return len(self.actions()) == 0

    def isFull(self):
        s = self.layout().spacing()
        nmax = self.width() // (self._size + s)
        # return len(self._actions) == nmax
        return len(self.actions()) == nmax

    # < Revision 02/06/2025
    # add moveSelectedToFisrt method
    def moveSelectedToFisrt(self):
        if len(self.actions()) > 1:
            index = self.getSelectedIndex()
            if index is not None:
                action = self.actions()[index]
                self.removeAction(action)
                self.insertAction(self.actions()[0], action)
    # Revision 02/06/2025 >

    # Qt events

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            files = event.mimeData().text().split('\n')
            for file in files:
                if file != '':
                    # < Revision 03/06/2025
                    # filename = file.replace('file://', '')
                    if platform == 'win32': filename = file.replace('file:///', '')
                    else: filename = file.replace('file://', '')
                    # Revision 03/06/2025 >
                    if splitext(filename)[1] == SisypheVolume.getFileExt():
                        vol = SisypheVolume()
                        try:
                            vol.load(filename)
                            self.addVolume(vol)
                        except Exception as err:
                            messageBox(self, 'Open PySisyphe volume', text='{}'.format(err))
        else: event.ignore()

    def contextMenuEvent(self, event):
        # Popup
        self._popup.popup(event.globalPos())

    def mouseDoubleClickEvent(self, event):
        self.open()
