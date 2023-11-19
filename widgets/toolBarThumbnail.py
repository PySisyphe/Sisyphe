"""

    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import getcwd, chdir
from os.path import dirname
from os.path import basename
from os.path import splitext

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
from Sisyphe.widgets.imageWidgets import SisypheVolumeThumbnailButtonWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy

        QToolBar -> ToolBarThumbnail
        
    Description

        Thumbnail widget typically placed at the top of the main window. 
        Shows SisypheVolume loaded en PySisyphe environment.
        Container of SisypheVolumeThumbnailButtonWidget.
"""


class ToolBarThumbnail(QToolBar):
    """
        ToolBarThumbnail

        Description

            Image thumbnail widget typically placed at the top of the main window.

        Inheritance

            QToolBar -> ToolBarThumbnail

        Private attributes

            _actions            list of SisypheVolumeThumbnailButtonWidget
            _parent             QWidget

        Public methods

            setSize(int)
            int = getSize()
            WindowSisyphe = getMainWindow()
            setMainWindow(WindowSisyphe)
            bool = hasWindowSisyphe()
            IconBarViewWidgetCollection = getViewsWidget()
            setViewsWidget(IconBarViewWidgetCollection)
            bool = hasViewsWidget()
            SisypheVolumeThumbnailButtonWidget = getSelectedWidget()
            SisypheVolume = getSelectedVolume()
            int = getVolumeIndex(SisypheVolume)
            bool = containsVolume(SisypheVolume)
            removeVolume(SisypheVolume)
            removeAllOverlays()
            addVolume(SisypheVolume)
            open()
            saveSelected()
            saveSelectedAs()
            saveAll()
            editAttributesSelected()
            removeSelected()
            removeAll()
            isEmpty()

            inherited QToolBar methods

        Qt Events

            mousePressEvent         override
            mouseDoubleClickEvent   override
            dragEnterEvent          override
            dropEvent               override

        Revisions:

            15/09/2023  getVolumeIndex() method, test arrayID attribute equality
    """

    # Special method

    def __init__(self, size=128, mainwindow=None, views=None, parent=None):
        super().__init__(parent)

        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(mainwindow, WindowSisyphe): self._mainwindow = mainwindow
        else: self._mainwindow = None

        from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
        if isinstance(views, IconBarViewWidgetCollection): self._views = views
        else: self._views = None

        self._actions = list()
        self._size = size
        self._group = QButtonGroup()
        self._group.setExclusive(True)

        policy = QSizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Fixed)
        policy.setHorizontalPolicy(QSizePolicy.Expanding)
        self.setSizePolicy(policy)
        self.setFixedHeight(size + 8)
        self.setMovable(False)

        self.setToolTip('Double-click to open volume,\n'
                        'Right click to display popup menu,\n'
                        'Drag and drop volume from finder to open it.')

        self.setStyleSheet("QPushButton:checked {background-color: black; border-color: rgb(0, 125, 255); "
                           "border-style: solid; border-width: 8px; border-radius: 20px;}")

        # Init popup menu

        self._popup = QMenu(self)
        self._action = dict()
        self._action['open'] = QAction('Open volume', self)
        self._action['saveall'] = QAction('Save all volume(s)', self)
        self._action['closeall'] = QAction('Close all volume(s)', self)
        self._action['open'].triggered.connect(lambda dummy: self.open())
        self._action['saveall'].triggered.connect(self.saveAll)
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
        if isinstance(w, IconBarViewWidgetCollection):
            self._views = w
        else: raise TypeError('parameter type {} is not IconBarViewWidgetCollection.'.format(type(w)))

    def hasViewsWidget(self):
        return self._views is not None

    def getWidgetsCount(self):
        return len(self._actions)

    def getSelectedIndex(self):
        if not self.isEmpty():
            for i in range(0, len(self._actions)):
                if self._actions[i].defaultWidget().isChecked(): return i
        return None

    def getSelectedWidget(self):
        if not self.isEmpty():
            for action in self._actions:
                if action.defaultWidget().isChecked():
                    return action.defaultWidget()
        return None

    def getSelectedVolume(self):
        if not self.isEmpty():
            for action in self._actions:
                if action.defaultWidget().isChecked():
                    return action.defaultWidget().getVolume()
        return None

    def hasReference(self):
        if not self.isEmpty():
            for action in self._actions:
                if action.defaultWidget().isChecked(): return True
        return False

    def getWidgetFromIndex(self, index):
        if isinstance(index, int):
            if 0 <= index < len(self._actions):
                return self._actions[index].defaultWidget()
            else: raise ValueError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def getVolumeFromIndex(self, index):
        if isinstance(index, int):
            if 0 <= index < len(self._actions):
                return self._actions[index].defaultWidget().getVolume()
            else: raise ValueError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def getVolumeIndex(self, vol):
        if isinstance(vol, SisypheVolume):
            if not self.isEmpty():
                for i in range(0, len(self._actions)):
                    if self._actions[i].defaultWidget().getVolume().getArrayID() == vol.getArrayID(): return i
            return None
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def containsVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            if not self.isEmpty():
                for action in self._actions:
                    if action.defaultWidget().getVolume().getArrayID() == vol.getArrayID(): return True
            return False
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def removeVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            if not self.isEmpty():
                for action in self._actions:
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
                        self._actions.remove(action)
            if self.hasMainWindow():
                self._mainwindow.updateMemoryUsage()
                self._mainwindow.setStatusBarMessage('Volume {} closed.'.format(vol.getBasename()))
                self._mainwindow.setDockEnabled(self.hasReference())
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def removeAllOverlays(self):
        n = self.getWidgetsCount()
        if n > 0:
            for i in range(n):
                self.getWidgetFromIndex(i).getActions()['overlay'].setChecked(False)

    def addVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            if not self.containsVolume(vol):
                widget = SisypheVolumeThumbnailButtonWidget(vol, size=self._size, thumbnail=self, views=self._views)
                QApplication.processEvents()
                self._group.addButton(widget)
                action = QWidgetAction(self)
                action.setDefaultWidget(widget)
                self.addAction(action)
                self._actions.append(action)
            if self.hasMainWindow():
                if vol.hasFilename: self._mainwindow.addRecent(vol.getFilename())
                self._mainwindow.updateMemoryUsage()
                self._mainwindow.setStatusBarMessage('Volume {} opened.'.format(vol.getBasename()))
        else: raise TypeError('parameter type {} is not str or SisypheVolume.'.format(type(vol)))

    def open(self, filenames=None):
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
                wait = DialogWait(title=title, progress=progress, progressmin=0, progressmax=n,
                                  progresstxt=True, anim=False, cancel=cancel, parent=self)
                wait.open()
                for filename in filenames:
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    vol = SisypheVolume()
                    try:
                        vol.load(filename)
                        QApplication.processEvents()
                    except Exception as err:
                        QMessageBox.warning(self, 'Open PySisyphe volume', '{}'.format(err))
                    if not self.containsVolume(vol):
                        n = vol.getNumberOfComponentsPerPixel()
                        if n > 1:
                            wait.hide()
                            r = QMessageBox.question(self, 'Open PySisyphe volume',
                                                     '{} is a multi-component volume.\n'
                                                     'Do you want to open all sub-volumes ?\n'
                                                     'If not, only first volume will be opened.'.format(vol.getBasename()),
                                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                                     QMessageBox.Cancel)
                            wait.open()
                            if r == QMessageBox.Yes:
                                fix = len(str(n))
                                for i in range(n):
                                    wait.setInformationText('Open {} Subvolume #{}...'.format(basename(filename), i+1))
                                    sub = vol.copyComponent(i)
                                    sub.copyAttributesFrom(vol)
                                    sub.updateArrayID()
                                    suffix = '#' + str(i).zfill(fix)
                                    sub.setFilename(vol.getFilename())
                                    sub.setFilenameSuffix(suffix)
                                    self.addVolume(sub)
                            elif r == QMessageBox.No:
                                wait.setInformationText('Open {} Subvolume #{}...'.format(basename(filename), 1))
                                sub = vol.copyComponent(0)
                                sub.copyAttributesFrom(vol)
                                sub.updateArrayID()
                                suffix = '#' + str(0).zfill(len(str(n)))
                                sub.setFilename(vol.getFilename())
                                sub.setFilenameSuffix(suffix)
                                self.addVolume(sub)
                        else: self.addVolume(vol)
                        QApplication.processEvents()
                    else:
                        QMessageBox.information(self, title, 'This volume is already open.')
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
                wait.close()

    def saveSelected(self):
        w = self.getSelectedWidget()
        if w is not None: w.save()
        else: QMessageBox.information(self, 'Save PySisyphe volume', 'No displayed volume to save.')
        if self.hasMainWindow():
            self._mainwindow.setStatusBarMessage('Reference volume saved.')

    def saveSelectedAs(self):
        w = self.getSelectedWidget()
        if w is not None: w.saveas()
        else: QMessageBox.information(self, 'Save PySisyphe volume', 'No displayed volume to save.')
        if self.hasMainWindow():
            self._mainwindow.setStatusBarMessage('Reference volume saved.')

    def saveAll(self):
        if not self.isEmpty():
            for i in range(len(self._actions)):
                v = self.getVolumeFromIndex(i)
                v.save()
            if self.hasMainWindow():
                self._mainwindow.setStatusBarMessage('All volumes saved.')

    def editAttributesSelected(self):
        w = self.getSelectedWidget()
        if w is not None:
            w.editAttributes()
        else: QMessageBox.information(self, 'Edit PySisyphe volume attributes', 'No displayed volume to edit.')

    def removeSelected(self):
        if not self.isEmpty():
            if self.hasMainWindow():
                self._mainwindow.clearDockListWidgets()
            for action in self._actions:
                if action.defaultWidget().isChecked():
                    self._views.removeVolume()
                    self.removeAction(action)
                    self._actions.remove(action)
                    break
            if self.hasMainWindow():
                self._mainwindow.updateTimers(-1)
                self._mainwindow.updateMemoryUsage()
                self._mainwindow.setStatusBarMessage('Reference volume closed.')
                self._mainwindow.setDockEnabled(False)

    def removeAll(self):
        if not self.isEmpty():
            if self.hasMainWindow():
                self._mainwindow.clearDockListWidgets()
            self.removeSelected()
            self.clear()
            self._actions.clear()
            if self.hasMainWindow():
                self._mainwindow.updateTimers(-1)
                self._mainwindow.updateMemoryUsage()
                self._mainwindow.setStatusBarMessage('All volumes closed.')
                self._mainwindow.setDockEnabled(False)

    def isEmpty(self):
        return len(self._actions) == 0

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
                    filename = file.replace('file://', '')
                    if splitext(filename)[1] == SisypheVolume.getFileExt():
                        vol = SisypheVolume()
                        try:
                            vol.load(filename)
                            self.addVolume(vol)
                        except Exception as err:
                            QMessageBox.warning(self, 'Open PySisyphe volume', '{}'.format(err))
        else: event.ignore()

    def contextMenuEvent(self, event):
        # Popup
        self._popup.popup(event.globalPos())

    def mouseDoubleClickEvent(self, event):
        self.open()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    main = ToolBarThumbnail(size=128)
    main.setFixedWidth(1000)
    main.show()
    app.exec_()
