"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform
from os.path import join
from os.path import dirname
from os.path import abspath

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QActionGroup
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.widgets.sliceViewWidgets import SliceROIViewWidget
from Sisyphe.widgets.multiViewWidgets import OrthogonalSliceViewWidget
from Sisyphe.widgets.multiViewWidgets import OrthogonalRegistrationViewWidget
from Sisyphe.widgets.multiViewWidgets import OrthogonalReorientViewWidget
from Sisyphe.widgets.multiViewWidgets import OrthogonalSliceVolumeViewWidget
from Sisyphe.widgets.multiViewWidgets import OrthogonalTrajectoryViewWidget
from Sisyphe.widgets.multiViewWidgets import MultiSliceGridViewWidget
from Sisyphe.widgets.multiViewWidgets import SynchronisedGridViewWidget
from Sisyphe.widgets.multiViewWidgets import GridViewWidget
from Sisyphe.widgets.multiViewWidgets import MultiViewWidget
from Sisyphe.widgets.sliceViewWidgets import SliceOverlayViewWidget
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import RoundedButton
from Sisyphe.widgets.basicWidgets import LabeledSlider
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.basicWidgets import LabeledLineEdit
from Sisyphe.widgets.basicWidgets import ColorSelectPushButton
from Sisyphe.widgets.basicWidgets import OpacityPushButton
from Sisyphe.widgets.LUTWidgets import TransferWidget

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> IconBarWidget -> IconBarOrthogonalSliceViewWidget
                               -> IconBarOrthogonalRegistrationViewWidget -> IconBarOrthogonalRegistrationViewWidget2
                               -> IconBarOrthogonalReorientViewWidget
                               -> IconBarOrthogonalSliceVolumeViewWidget
                               -> IconBarOrthogonalTrajectoryViewWidget
                               -> IconBarMultiSliceGridViewWidget -> IconBarSynchronisedGridViewWidget
                                                                  -> IconBarViewWidgetCollection
    - QObject -> IconBarViewWidgetCollection
                                                                
Description
~~~~~~~~~~~

Adds iconbar support to MultiViewWidget derived classes.
"""


class IconBarWidget(QWidget):
    """
    IconBarWidget class

    Description
    ~~~~~~~~~~~

    Base class that adds icon bar support to image display widgets (derived from MultiViewWidget)

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget

    Creation: 17/04/2023
    Last revision: 01/05/2025
    """

    _BTSIZE = 40    # default button size
    _VSIZE = 24

    # Custom Qt signals

    NameChanged = pyqtSignal()

    # Class methods

    @classmethod
    def _getDefaultIconDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'baricons')

    # Special methods

    """
    Private Attributes

    _widget             MultiViewWidget, display widget
    _bar                QFrame, icon bar
    _transfer           TransferWidget, widget for transfer function settings
    _menulut            QWidgetAction
    _ax                 QIcon, axial icon
    _cor                QIcon, coronal icon
    _sag                QIcon, sagittal icon
    _icons              Dict[str, QPushButton], iconbar buttons
    _visibilityflags    Dict[str, bool], buttons visibility flags
    _btsize             int, button size
    _timerid            int, QTimer identifier
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._widget = None
        self._menulut = None
        self._transfer = None
        self._thumbnail = None
        self._timerid = None

        # < Revision 17/03/2025
        # add icon size management
        settings = SisypheSettings()
        self._btsize = settings.getFieldValue('Viewport', 'IconSize')
        if self._btsize is None: self._btsize = self._BTSIZE
        # Revision 17/03/2025 >

        # Icon bar

        self._ax = QIcon(QPixmap(join(self._getDefaultIconDirectory(), 'wdimz.png')))
        self._cor = QIcon(QPixmap(join(self._getDefaultIconDirectory(), 'wdimy.png')))
        self._sag = QIcon(QPixmap(join(self._getDefaultIconDirectory(), 'wdimx.png')))

        self._icons = dict()
        self._icons['pin'] = self._createButton('wpin.png', 'pin.png', checkable=True, autorepeat=False)
        self._icons['pin'].setChecked(True)
        self._icons['screen'] = self._createButton('wfullscreen.png', 'fullscreen.png', checkable=True, autorepeat=False)
        self._icons['screen'].setVisible(False)
        self._icons['expand'] = self._createButton('wexpand.png', 'expand.png', checkable=True, autorepeat=False)
        self._icons['zoomin'] = self._createButton('wzoomin.png', 'zoomin.png', checkable=False, autorepeat=True)
        self._icons['zoomout'] = self._createButton('wzoomout.png', 'zoomout.png', checkable=False, autorepeat=True)
        self._icons['zoom1'] = self._createButton('wzoom1.png', 'zoom1.png', checkable=False, autorepeat=False)
        self._icons['actions'] = self._createButton('whand.png', 'hand.png', checkable=False, autorepeat=False)
        self._icons['show'] = self._createButton('wshow.png', 'show.png', checkable=False, autorepeat=False)
        self._icons['info'] = self._createButton('winfo.png', 'info.png', checkable=False, autorepeat=False)
        self._icons['iso'] = self._createButton('wiso.png', 'iso.png', checkable=False, autorepeat=False)
        self._icons['colorbar'] = self._createButton('wlut.png', 'lut.png', checkable=False, autorepeat=False)
        self._icons['ruler'] = self._createButton('waxis.png', 'axis.png', checkable=False, autorepeat=False)
        self._icons['tools'] = self._createButton('wruler.png', 'ruler.png', checkable=False, autorepeat=False)
        self._icons['capture'] = self._createButton('wphoto.png', 'photo.png', checkable=False, autorepeat=False)
        self._icons['clipboard'] = self._createButton('wclipboard.png', 'clipboard.png', checkable=False, autorepeat=False)

        self._visibilityflags = dict()
        self._visibilityflags['pin'] = True
        self._visibilityflags['screen'] = False
        self._visibilityflags['expand'] = True
        self._visibilityflags['zoomin'] = True
        self._visibilityflags['zoomout'] = True
        self._visibilityflags['zoom1'] = True
        self._visibilityflags['actions'] = True
        self._visibilityflags['show'] = True
        self._visibilityflags['info'] = True
        self._visibilityflags['iso'] = True
        self._visibilityflags['tools'] = True
        self._visibilityflags['colorbar'] = True
        self._visibilityflags['ruler'] = True
        self._visibilityflags['capture'] = True
        self._visibilityflags['clipboard'] = True

        self._icons['pin'].setToolTip('Pin iconbar.\n'
                                      'p key')
        self._icons['screen'].setToolTip('Switch to full-screen view.\n'
                                         'F11 key')
        self._icons['expand'].setToolTip('Expand selected view.\n'
                                         '+ key')
        self._icons['zoomin'].setToolTip('Zoom in.\n'
                                         'Up key + CTRL key (CMD key MacOS)\n'
                                         'MouseWheel + CTRL key (CMD key MacOS)')
        self._icons['zoomout'].setToolTip('Zoom out.\n'
                                          'Down key + CTRL key (CMD key MacOS)\n'
                                          'MouseWheel + CTRL key (CMD key MacOS)')
        self._icons['zoom1'].setToolTip('Default zoom.\n'
                                        '0 key')
        self._icons['actions'].setToolTip('Mouse actions management.')
        self._icons['info'].setToolTip('Set information visibility options.')
        self._icons['iso'].setToolTip('Set isovalue lines.')
        self._icons['colorbar'].setToolTip('Set color bar position.')
        self._icons['ruler'].setToolTip('Set ruler position.')
        self._icons['tools'].setToolTip('Add tools.')
        self._icons['capture'].setToolTip('Save capture to disk.\n'
                                          'SPACE key, send selected capture to screenshot manager')
        self._icons['clipboard'].setToolTip('Copy capture to clipboard.')

        submenu = QMenu()
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        submenu.addAction('Distance')
        submenu.addAction('Orthogonal distances')
        submenu.addAction('Angle')
        submenu.addSeparator()
        submenu.addAction('Remove all')
        # noinspection PyUnresolvedReferences
        submenu.triggered.connect(self._onMenuTools)
        self._icons['tools'].setMenu(submenu)

        self._isoedit = LabeledLineEdit('Isoline values', fontsize=10)
        self._isoedit.getQLineEdit().setClearButtonEnabled(True)
        # noinspection PyUnresolvedReferences
        self._isoedit.getQLineEdit().editingFinished.connect(self._onIsoEditingFinished)

        self._isocolor = ColorSelectPushButton()
        self._isocolor.setFixedSize(self._VSIZE, self._VSIZE)
        self._isocolor.setFloatColor(1.0, 1.0, 1.0, signal=False)
        self._isocolor.colorChanged.connect(self._onIsoColorChanged)

        self._isoopacity = OpacityPushButton()
        self._isoopacity.setFixedSize(self._VSIZE, self._VSIZE)
        self._isoopacity.setOpacity(1.0)
        self._isoopacity.opacityChanged.connect(self._onIsoOpacityChanged)

        self._isoprop = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.addWidget(self._isocolor)
        layout.addWidget(self._isoopacity)
        layout.addWidget(self._isoedit)
        self._isoprop.setLayout(layout)
        self._isoprop.setMaximumWidth(400)

        self._isoMenu = QMenu()
        # noinspection PyTypeChecker
        self._isoMenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._isoMenu.setWindowFlag(Qt.FramelessWindowHint, True)
        self._isoMenu.setAttribute(Qt.WA_TranslucentBackground, True)
        action = QWidgetAction(self)
        action.setDefaultWidget(self._isoprop)
        action.setData(-1)
        self._isoMenu.addAction(action)
        self._isoMenu.addSeparator()
        # noinspection PyUnresolvedReferences
        self._isoMenu.aboutToShow.connect(self._onShowMenuIso)
        # noinspection PyUnresolvedReferences
        self._isoMenu.triggered.connect(self._onMenuIso)
        self._icons['iso'].setMenu(self._isoMenu)

        self._bar = QFrame(self)
        # < Revision 14/03/2025
        if platform == 'win32':
            self._bar.setObjectName('IconBar')
            self._bar.setStyleSheet('QFrame#IconBar { background-color: #000000; border-color: #000000; } '
                                    'QToolTip#IconBar { color: #000000; background-color: #FFFFE0; border: 0px; font-size: 8pt; }')
        else:
            pal = self.palette()
            # noinspection PyTypeChecker
            pal.setColor(QPalette.Background, Qt.black)
            self.setAutoFillBackground(True)
            self.setPalette(pal)
        # Revision 14/03/2025 >
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(self._icons['pin'])
        layout.addWidget(self._icons['screen'])
        layout.addWidget(self._icons['expand'])
        layout.addWidget(self._icons['zoomin'])
        layout.addWidget(self._icons['zoomout'])
        layout.addWidget(self._icons['zoom1'])
        layout.addWidget(self._icons['actions'])
        layout.addWidget(self._icons['show'])
        layout.addWidget(self._icons['info'])
        layout.addWidget(self._icons['iso'])
        layout.addWidget(self._icons['colorbar'])
        layout.addWidget(self._icons['ruler'])
        layout.addWidget(self._icons['tools'])
        layout.addWidget(self._icons['capture'])
        layout.addWidget(self._icons['clipboard'])
        layout.addStretch()
        self._bar.setLayout(layout)

        # Shortcuts

        self._icons['expand'].setShortcut(Qt.Key_Plus)
        self._icons['zoom1'].setShortcut('0')
        self._shcutp = QShortcut('p', self) # Pin shortcut
        # noinspection PyUnresolvedReferences
        self._shcutp.activated.connect(self._onPin)
        self._shcutA = QShortcut('A', self) # Axial shortcut
        self._shcutC = QShortcut('C', self) # Coronal shortcut
        self._shcutS = QShortcut('S', self) # Sagittal shortcut
        self._shcut1 = QShortcut(Qt.Key_1, self) # Grid 1x1 shortcut
        self._shcut2 = QShortcut(Qt.Key_2, self) # Grid 1x2 shortcut
        self._shcut3 = QShortcut(Qt.Key_3, self) # Grid 1x3 shortcut
        self._shcut4 = QShortcut(Qt.Key_4, self) # Grid 2x2 shortcut
        self._shcut6 = QShortcut(Qt.Key_6, self) # Grid 2x3 shortcut
        self._shcut9 = QShortcut(Qt.Key_9, self) # Grid 3x3 shortcut
        self._shcutx = QShortcut('x', self) # Show cursor shortcut
        self._shcuti = QShortcut('i', self) # Show information shortcut
        self._shcutl = QShortcut('l', self) # Show orientation labels shortcut
        self._shcutm = QShortcut('m', self)  # Show orientation marker shortcut
        self._shcutb = QShortcut('b', self)  # Show color bar shortcut
        self._shcutr = QShortcut('r', self)  # Show ruler shortcut
        self._shcutt = QShortcut('t', self)  # Show tooltip shortcut

        # Drop settings

        # < Revision 18/10/2024
        # Default setting for drag & drop action
        self._drop = settings.getFieldValue('Viewport', 'DropInView')
        if self._drop is not None: self._drop = self._drop[0]
        else: self._drop = 'Replace'
        # Revision 18/10/2024 >

        # Layout

        self._layout = QHBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignVCenter)
        self._layout.addWidget(self._bar)

        self._vlayout = QVBoxLayout()
        self._vlayout.setSpacing(0)
        self._vlayout.setContentsMargins(0, 0, 0, 0)
        self._vlayout.addLayout(self._layout)

        self.setLayout(self._vlayout)
        self.setAcceptDrops(True)

    def __call__(self):
        if self._widget is not None: return self._widget
        else: raise AttributeError('Widget attribute is not defined.')

    # Private methods

    def _createButton(self, icon0, icon1='', checkable=False, autorepeat=False):
        button = RoundedButton()
        # < Revision 17/03/2025
        # button.setSize(self._BTSIZE)
        button.setSize(self._btsize)
        # Revision 17/03/2025 >
        button.setBorderWidth(5)
        button.setBorderRadius(10)
        button.setBorderColorToBlack()
        button.setBackgroundColorToBlack()
        button.setCheckedBorderColorToWhite()
        button.setCheckedBackgroundColorToWhite()
        button.setNormalIcon(join(self._getDefaultIconDirectory(), icon0))
        if icon1 != '': button.setCheckedIcon(join(self._getDefaultIconDirectory(), icon1))
        button.setCheckable(checkable)
        button.setAutoRepeat(autorepeat)
        return button

    def _getBaseParent(self):
        w = None
        w2 = self.parent()
        while w2 is not None:
            w = w2
            w2 = w.parent()
        return w

    def _onMenuTools(self, action):
        s = str(action.text())[0]
        w = self.getViewWidget()
        if w is not None:
            if s == 'R':
                w2 = w.getFirstSliceViewWidget()
                if w2 is not None:
                    w2.removeAll2DTools()
            else:
                w2 = w.getSelectedViewWidget()
                if w2 is not None:
                    if s == 'D': w2.addDistanceTool()
                    elif s == 'O': w2.addOrthogonalDistanceTool()
                    else: w2.addAngleTool()
                else: messageBox(self, title=action.text(), text='Select a view before adding a tool.')

    def _onMenuSaveCapture(self, action):
        w = self.getViewWidget()
        if w is not None:
            s = action.text().split()
            if s[0] == 'Save':
                if s[1] == 'grid': w.saveCapture()
                elif s[1] == 'selected':
                    w2 = w.getSelectedViewWidget()
                    if w2 is not None: w2.saveCapture()
                    else: messageBox(self,
                                     'Save selected view capture',
                                     'No selected view.')
                elif s[1] == 'captures': w.saveSeriesCaptures()
                elif s[1] == 'single': w.saveSeriesCapture()
            elif s[0] == 'Send':
                if s[1] == 'selected':
                    w2 = w.getSelectedViewWidget()
                    if w2 is not None:
                        if self.hasThumbnail():
                            mainwindow = self.getThumbnail().getMainWindow()
                            if mainwindow is not None:
                                cap = w2.getPixmapCapture()
                                mainwindow.getScreenshots().paste(cap)
                    else: messageBox(self,
                                     'Send selected view capture',
                                     'No selected view.')
                elif s[1] == 'captures':
                    if self.hasThumbnail():
                        mainwindow = self.getThumbnail().getMainWindow()
                        if mainwindow is not None:
                            caps = self().getFirstVolumeViewWidget().getSeriesPixmapCaptures()
                            for cap in caps:
                                mainwindow.getScreenshots().paste(cap)

    def _onMenuCopyCapture(self, action):
        s = str(action.text())[5]
        w = self.getViewWidget()
        if w is not None:
            if s == 's':
                w2 = w.getSelectedViewWidget()
                if w2 is not None: w2.copyToClipboard()
                else: messageBox(self,
                                 'Copy to clipboard',
                                 'No view selected.')
            elif s == 'g': w.copyToClipboard()

    def _onMenuOrientation(self, v):
        if v == 0: self._icons['orient'].setIcon(self._ax)
        elif v == 1: self._icons['orient'].setIcon(self._cor)
        else: self._icons['orient'].setIcon(self._sag)

    def _onMenuIso(self, action):
        view = self._widget.getFirstSliceViewWidget()
        if view is not None and isinstance(view, SliceOverlayViewWidget):
            n = int(action.data())
            if n > -1:
                if action.isChecked():
                    if n == 0: v = view.getVolume()
                    else: v = view.getOverlayFromIndex(n - 1)
                    iso = v.getMean()
                    if v.isIntegerDatatype(): iso = int(iso)
                    else: iso = round(iso, 1)
                    self._isoedit.setEditText('{}'.format(iso))
                    view.setIsoValues([iso], signal=True)
                    view.setIsoIndex(n, signal=True)
                else: view.setIsoIndex(-1, signal=True)

    def _onShowMenuIso(self):
        view = self._widget.getFirstSliceViewWidget()
        if view is not None and isinstance(view, SliceOverlayViewWidget):
            n = view.getIsoIndex()
            if n > -1:
                c = view.getIsoLinesColor()
                self._isocolor.setFloatColor(c[0], c[1], c[2], signal=False)
                self._isoopacity.setOpacity(view.getIsoLinesOpacity())
                self._isoprop.setEnabled(True)
            else: self._isoprop.setEnabled(False)
            actions = self._isoMenu.actions()
            for action in actions:
                d = action.data()
                if d is not None and d != -1:
                    self._isoMenu.removeAction(action)
            if self.hasVolume():
                group = QActionGroup(self)
                group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
                name = self.getVolume().getName()
                if name == '': name = 'Displayed volume'
                action = QAction(name)
                action.setData(0)
                group.addAction(action)
                action.setCheckable(True)
                action.setChecked(n == 0)
                self._isoMenu.addAction(action)
                if view.hasOverlay():
                    for i in range(view.getOverlayCount()):
                        name = view.getOverlayFromIndex(i).getName()
                        if name == '': name = 'Overlay volume #{}'.format(i)
                        action = QAction(name)
                        action.setData(i + 1)
                        group.addAction(action)
                        action.setCheckable(True)
                        action.setChecked(n == i + 1)
                        self._isoMenu.addAction(action)

    def _onIsoEditingFinished(self):
        view = self._widget.getFirstSliceViewWidget()
        if view is not None and isinstance(view, SliceOverlayViewWidget):
            if self._isoedit.isEmpty():
                view.setIsoIndex(-1, signal=True)
            else:
                n = view.getIsoIndex()
                if n == 0: dt = view.getVolume().isIntegerDatatype()
                else: dt = view.getOverlayFromIndex(n - 1).isIntegerDatatype()
                l = self._isoedit.getEditText().split(' ')
                iso = list()
                for v in l:
                    try:
                        if dt: iso.append(int(v))
                        else: iso.append(round(float(v), 1))
                    except: continue
                if len(iso) > 0:
                    view.setIsoValues(iso, signal=True)
                    self._isoedit.setEditText(' '.join([str(i) for i in iso]))
                    if n > -1: view.setIsoIndex(n, signal=True)
                else:
                    self._isoedit.setEditText('')
                    view.setIsoIndex(-1, signal=True)

    def _onIsoColorChanged(self):
        view = self._widget.getFirstSliceViewWidget()
        if view is not None and isinstance(view, SliceOverlayViewWidget):
            n = view.getIsoIndex()
            if n > -1:
                c = list(self._isocolor.getFloatColor())
                view.setIsoLinesColor(c, signal=True)

    # noinspection PyUnusedLocal
    def _onIsoOpacityChanged(self, w):
        view = self._widget.getFirstSliceViewWidget()
        if view is not None and isinstance(view, SliceOverlayViewWidget):
            n = view.getIsoIndex()
            if n > -1:
                v = self._isoopacity.getOpacity()
                view.setIsoLinesOpacity(v, signal=True)

    # < Revision 01/05/2025
    # add _onTransferMenuChanged method
    def _onTransferMenuChanged(self):
        if self._transfer is not None:
            menu = self._icons['transfer'].menu()
            self._transfer.adjustSize()
            menu.hide()
            menu.setFixedHeight(self._transfer.size().height())
            menu.show()
            QApplication.processEvents()
    # Revision 01/05/2025 >

    def _onExpand(self):
        if self._widget is not None:
            if self._icons['expand'].isChecked():
                w = self._widget.getSelectedViewWidget()
                if w is not None:
                    w.getAction()['expand'].toggle()
                    self._widget.expandViewWidget(w)
            else:
                for i in range(0, self._widget.getRows()):
                    for j in range(0, self._widget.getCols()):
                        action = self._widget[i, j].getAction()['expand']
                        if action.isChecked(): action.setChecked(False)
                        self._widget[i, j].setVisible(True)

    def _onFullScreen(self):
        w = self._getBaseParent()
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(w, WindowSisyphe): w.toggleFullscreen()
        else: self._icons['screen'].setVisible(False)

    def _onPin(self):
        if self._icons['pin'].isVisible():
            self._icons['pin'].setChecked(False)
        else: self._icons['pin'].setChecked(True)

    def _connectExpandAction(self):
        for i in range(0, self._widget.getRows()):
            for j in range(0, self._widget.getCols()):
                try:
                    action = self._widget[i, j].getAction()['expand']
                    if action is not None:
                        action.triggered.connect(self._icons['expand'].setChecked)
                except: return

    def _showViewWidget(self):
        self._bar.show()
        self._widget.show()
        QApplication.processEvents()

    def _hideViewWidget(self):
        self._bar.hide()
        self._widget.hide()
        QApplication.processEvents()

    # Public method

    # < Revision 17/03/2025
    # add setIconSize method
    def setIconSize(self, size: int | None):
        if size > 64: self._btsize = 64
        elif size < 0: self._btsize = self._BTSIZE
        elif size is None: self._btsize = self._BTSIZE
        else: self._btsize = size
        for k in self._icons:
            self._icons[k].setSize(self._btsize)
    # Revision 17/03/2025 >

    # < Revision 17/03/2025
    # add getIconSize method
    def getIconSize(self) -> int:
        return self._btsize

    # < Revision 08/03/2025
    # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
    # finalize method must be called before destruction
    def finalize(self):
        if self._widget is not None:
            self._widget.finalize()
    # Revision 08/03/2025 >

    def timerEnabled(self):
        # timer used to detect when mouse leaves icon bar
        # call timerEvent Qt event method
        if self._widget.hasVolume():
            if self._timerid is None:
                self._timerid = self.startTimer(0)

    def timerDisabled(self):
        # timer used to detect when mouse leaves icon bar
        # call timerEvent Qt event method
        if self._timerid is not None:
            self.killTimer(self._timerid)
            self._timerid = None

    def updateRender(self):
        self._widget.updateRender()

    def getName(self):
        return self.objectName()

    def setName(self, name):
        if isinstance(name, str):
            self.setObjectName(name)
            # noinspection PyUnresolvedReferences
            self.NameChanged.emit()
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    # Public reference volume methods

    def setVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            if self._widget is not None:
                self._widget.setVolume(vol)
                self._showViewWidget()

    # < Revision 18/10/2024
    # add replaceVolume method
    def replaceVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            if self._widget is not None:
                self._widget.replaceVolume(vol)
    # Revision 18/10/2024 >

    def getVolume(self):
        return self._widget.getVolume()

    def hasVolume(self):
        return self._widget.hasVolume()

    def removeVolume(self):
        if self._widget is not None:
            self._hideViewWidget()
            QApplication.processEvents()
            self._widget.removeVolume()

    # Public overlay methods

    def addOverlay(self, volume):
        if self._widget is not None:
            if self._widget.hasVolume():
                self._widget.addOverlay(volume)

    def getOverlayCount(self):
        if self._widget is not None:
            if self._widget.hasVolume(): return self._widget.getOverlayCount()
            else: raise AttributeError('no volume in _widget attribute.')
        else: raise AttributeError('_widget attribute is None.')

    def hasOverlay(self):
        if self._widget is not None:
            if self._widget.hasVolume(): return self._widget.hasOverlay()
            else: raise AttributeError('no volume in _widget attribute.')
        else: raise AttributeError('_widget attribute is None.')

    def getOverlayIndex(self, o):
        if self._widget is not None:
            if self._widget.hasVolume(): return self._widget.getOverlayIndex(o)
            else: raise AttributeError('no volume in _widget attribute.')
        else: raise AttributeError('_widget attribute is None.')

    def removeOverlay(self, o):
        if self._widget is not None:
            if self._widget.hasVolume():
                self._widget.removeOverlay(o)

    def removeAllOverlays(self):
        if self._widget is not None:
            if self._widget.hasVolume():
                self._widget.removeAllOverlays()

    def getOverlayFromIndex(self, index):
        if self._widget is not None:
            if self._widget.hasVolume(): return self._widget.getOverlayFromIndex(index)
            else: raise AttributeError('no volume in _widget attribute.')
        else: raise AttributeError('_widget attribute is None.')

    def setAlignCenters(self, v: bool):
        if self._widget is not None:
            self._widget.setAlignCenters(v)

    def alignCentersOn(self):
        if self._widget is not None:
            self._widget.setAlignCentersOn()

    def alignCentersOff(self):
        if self._widget is not None:
            self._widget.setAlignCentersOff()

    def getAlignCenters(self):
        if self._widget is not None: return self._widget.getAlignCenters()
        else: raise AttributeError('_widget attribute is None.')

    # Public view widget methods

    def setViewWidget(self, widget):
        if isinstance(widget, MultiViewWidget):
            self._widget = widget
            self._widget.setParent(self)
            self._layout.addWidget(widget)
            grid = isinstance(widget, GridViewWidget)
            multi = isinstance(widget, MultiSliceGridViewWidget)
            orthoslc = isinstance(widget, OrthogonalSliceViewWidget)
            orthovol = isinstance(widget, OrthogonalSliceVolumeViewWidget)
            view1 = widget.getFirstSliceViewWidget()
            view2 = widget.getFirstVolumeViewWidget()
            """
            Common to all widgets 
            """
            # noinspection PyUnresolvedReferences
            self._icons['expand'].clicked.connect(self._onExpand)
            self._connectExpandAction()
            # noinspection PyUnresolvedReferences
            self._icons['screen'].clicked.connect(lambda _: self._onFullScreen())
            # noinspection PyUnresolvedReferences
            self._icons['zoomin'].clicked.connect(view1.zoomIn)
            # noinspection PyUnresolvedReferences
            self._icons['zoomout'].clicked.connect(view1.zoomOut)
            # noinspection PyUnresolvedReferences
            self._icons['zoom1'].clicked.connect(view1.zoomDefault)
            self._icons['actions'].setMenu(view1.getPopupActions())
            self._icons['info'].setMenu(view1.getPopupInformation())
            self._icons['colorbar'].setMenu(view1.getPopupColorbarPosition())
            self._icons['ruler'].setMenu(view1.getPopupRulerPosition())
            submenu = QMenu()
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.FramelessWindowHint, True)
            submenu.setAttribute(Qt.WA_TranslucentBackground, True)
            submenu.addAction('Copy grid capture to clipboard')
            submenu.addAction('Copy selected view capture to clipboard')
            # noinspection PyUnresolvedReferences
            submenu.triggered.connect(self._onMenuCopyCapture)
            self._icons['clipboard'].setMenu(submenu)
            """
            Grid widget actions
            """
            if grid:
                self._icons['orient'] = self._createButton('wdimz.png', 'dimz.png', checkable=False, autorepeat=False)
                self._icons['sliceminus'] = self._createButton('wminus.png', 'minus.png', checkable=False, autorepeat=True)
                self._icons['sliceplus'] = self._createButton('wplus.png', 'plus.png', checkable=False, autorepeat=True)
                self._icons['orient'].setMenu(view1.getPopupOrientation())
                menu = view1.getPopupOrientation()
                menu.actions()[0].triggered.connect(lambda dummy, v=0: self._onMenuOrientation(v))
                menu.actions()[1].triggered.connect(lambda dummy, v=1: self._onMenuOrientation(v))
                menu.actions()[2].triggered.connect(lambda dummy, v=2: self._onMenuOrientation(v))
                # noinspection PyUnresolvedReferences
                self._shcutA.activated.connect(lambda: menu.actions()[0].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutC.activated.connect(lambda: menu.actions()[1].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutS.activated.connect(lambda: menu.actions()[2].trigger())
                # noinspection PyUnresolvedReferences
                self._icons['sliceminus'].clicked.connect(view1.slicePlus)
                # noinspection PyUnresolvedReferences
                self._icons['sliceplus'].clicked.connect(view1.sliceMinus)
                self._visibilityflags['orient'] = True
                self._visibilityflags['sliceminus'] = True
                self._visibilityflags['sliceplus'] = True
                layout = self._bar.layout()
                layout.insertWidget(3, self._icons['sliceplus'])
                layout.insertWidget(3, self._icons['sliceminus'])
                layout.insertWidget(3, self._icons['orient'])
                self._icons['sliceminus'].setToolTip('Previous slice.\n'
                                                     'Up or Left key\n'
                                                     'MouseWheel')
                self._icons['sliceplus'].setToolTip('Next slice.\n'
                                                    'Down or Right key\n'
                                                    'MouseWheel')
                self._icons['orient'].setToolTip('Set view orientation (axial, coronal, sagittal).\n'
                                                 'A key to set axial orientation,\n'
                                                 'C key to set coronal orientation,\n'
                                                 'S key to set sagitall orientation.')
                self._icons['sliceminus'].setToolTip('Go to previous slice.\n'
                                                     'Up or Left key')
                self._icons['sliceplus'].setToolTip('Go to next slice.\n'
                                                    'Down or Right key')
                self._icons['show'].setMenu(view1.getPopupVisibility())
                self._icons['show'].setToolTip('Set visibility options.\n'
                                               'x key show/hide cursor\n'
                                               'i key show/hide information\n'
                                               'l key show/hide orientation labels\n'
                                               'm key show/hide orientation marker\n'
                                               'b key show/hide colorbar\n'
                                               'r key show/hide ruler\n'
                                               't key show/hide tooltip')
                # noinspection PyUnresolvedReferences
                self._shcutx.activated.connect(lambda: self._icons['show'].menu().actions()[0].trigger())
                # noinspection PyUnresolvedReferences
                self._shcuti.activated.connect(lambda: self._icons['show'].menu().actions()[1].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutl.activated.connect(lambda: self._icons['show'].menu().actions()[2].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutm.activated.connect(lambda: self._icons['show'].menu().actions()[3].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutb.activated.connect(lambda: self._icons['show'].menu().actions()[6].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutr.activated.connect(lambda: self._icons['show'].menu().actions()[7].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutt.activated.connect(lambda: self._icons['show'].menu().actions()[8].trigger())
                widget.popupMenuROIDisabled()
                if multi:
                    self._icons['grid'] = self._createButton('wgrid.png', 'grid.png', checkable=False, autorepeat=False)
                    self._visibilityflags['grid'] = True
                    self._icons['grid'].setToolTip('Set row and column count.\n'
                                                   '1 key 1x1\n'
                                                   '2 key 1x2\n'
                                                   '3 key 1x3\n'
                                                   '4 key 2x2\n'
                                                   '6 key 2x3\n'
                                                   '9 key 3x3')
                    self._icons['grid'].setMenu(widget.getPopupMenuNumberOfVisibleViews())
                    # noinspection PyUnresolvedReferences
                    self._shcut1.activated.connect(lambda: self._icons['grid'].menu().actions()[0].trigger())
                    # noinspection PyUnresolvedReferences
                    self._shcut2.activated.connect(lambda: self._icons['grid'].menu().actions()[1].trigger())
                    # noinspection PyUnresolvedReferences
                    self._shcut3.activated.connect(lambda: self._icons['grid'].menu().actions()[2].trigger())
                    # noinspection PyUnresolvedReferences
                    self._shcut4.activated.connect(lambda: self._icons['grid'].menu().actions()[3].trigger())
                    # noinspection PyUnresolvedReferences
                    self._shcut6.activated.connect(lambda: self._icons['grid'].menu().actions()[4].trigger())
                    # noinspection PyUnresolvedReferences
                    self._shcut9.activated.connect(lambda: self._icons['grid'].menu().actions()[5].trigger())
                    layout.insertWidget(3, self._icons['grid'])
            if grid or orthoslc:
                self._icons['show'].setMenu(view1.getPopupVisibility())
                submenu = QMenu()
                # noinspection PyTypeChecker
                submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyTypeChecker
                submenu.setWindowFlag(Qt.FramelessWindowHint, True)
                submenu.setAttribute(Qt.WA_TranslucentBackground, True)
                submenu.addAction('Save grid capture...')
                submenu.addAction('Save selected view capture...')
                submenu.addAction('Save captures from slice series...')
                submenu.addSeparator()
                action = submenu.addAction('Send selected view capture to screenshots preview')
                action.setShortcut(Qt.Key_Space)
                # noinspection PyUnresolvedReferences
                submenu.triggered.connect(self._onMenuSaveCapture)
                self._icons['capture'].setMenu(submenu)
            """    
            OrthogonalSliceVolume widget actions 
            """
            if orthovol:
                self._icons['campos'] = self._createButton('wrotate.png', 'rotate.png', checkable=False,
                                                           autorepeat=False)
                self._icons['texture'] = self._createButton('whead.png', 'head.png', checkable=False, autorepeat=False)
                self._icons['transfer'] = self._createButton('wtransfer.png', 'transfer.png', checkable=False,
                                                             autorepeat=False)
                self._icons['align'] = self._createButton('wview.png', 'view.png', checkable=False, autorepeat=False)
                self._icons['campos'].setMenu(view2.getPopupCameraPosition())
                self._icons['texture'].setMenu(view2.getPopupTextureActor())
                self._icons['align'].setMenu(view1.getPopupAlignment())

                self._transfer = TransferWidget(size=256)
                self._transfer.colorDialogClosed.connect(self._icons['transfer'].showMenu)
                self._transfer.gradientTransferVisibilityChanged.connect(self._onTransferMenuChanged)

                submenu = QMenu()
                # noinspection PyTypeChecker
                submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyTypeChecker
                submenu.setWindowFlag(Qt.FramelessWindowHint, True)
                submenu.setAttribute(Qt.WA_TranslucentBackground, True)
                a = QWidgetAction(self)
                a.setDefaultWidget(self._transfer)
                submenu.addAction(a)
                self._icons['transfer'].setMenu(submenu)

                layout = self._bar.layout()
                layout.insertWidget(3, self._icons['align'])
                layout.insertWidget(3, self._icons['transfer'])
                layout.insertWidget(3, self._icons['campos'])
                layout.insertWidget(3, self._icons['texture'])

                self._icons['show'].setMenu(view2.getPopupVisibility())
                self._icons['show'].setToolTip('Set visibility options.\n'
                                               'x key show/hide cursor\n'
                                               'i key show/hide information\n'
                                               'm key show/hide orientation marker\n'
                                               'b key show/hide colorbar\n'
                                               'r key show/hide ruler\n'
                                               't key show/hide tooltip')
                # noinspection PyUnresolvedReferences
                self._shcutx.activated.connect(lambda: self._icons['show'].menu().actions()[0].trigger())
                # noinspection PyUnresolvedReferences
                self._shcuti.activated.connect(lambda: self._icons['show'].menu().actions()[1].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutm.activated.connect(lambda: self._icons['show'].menu().actions()[2].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutb.activated.connect(lambda: self._icons['show'].menu().actions()[3].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutr.activated.connect(lambda: self._icons['show'].menu().actions()[4].trigger())
                # noinspection PyUnresolvedReferences
                self._shcutt.activated.connect(lambda: self._icons['show'].menu().actions()[5].trigger())


                # < Revision 12/12/2024
                # add align visibility flag
                self._visibilityflags['align'] = True
                # Revision 12/12/2024 >
                self._visibilityflags['campos'] = True
                self._visibilityflags['texture'] = True
                self._visibilityflags['transfer'] = True

                self._icons['campos'].setToolTip('Predefined camera positions in 3D view.')
                self._icons['align'].setToolTip('Slice normal direction.')
                self._icons['texture'].setToolTip('3D texture volume rendering settings.')
                self._icons['transfer'].setToolTip('Set color and alpha transfer functions.')

                submenu = QMenu()
                # noinspection PyTypeChecker
                submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyTypeChecker
                submenu.setWindowFlag(Qt.FramelessWindowHint, True)
                submenu.setAttribute(Qt.WA_TranslucentBackground, True)
                submenu.addAction('Save grid capture...')
                submenu.addAction('Save selected view capture...')
                submenu.addAction('Save captures from multiple camera positions...')
                submenu.addAction('Save single capture from multiple camera positions...')
                submenu.addSeparator()
                action = submenu.addAction('Send selected view capture to screenshots preview')
                action.setShortcut(Qt.Key_Space)
                submenu.addAction('Send captures from multiple camera positions to screenshots preview')
                # noinspection PyUnresolvedReferences
                submenu.triggered.connect(self._onMenuSaveCapture)
                self._icons['capture'].setMenu(submenu)

        else: raise TypeError('parameter type {} is not MultiViewWidget.'.format(type(widget)))

    def getViewWidget(self):
        return self._widget

    def viewWidgetVisibleOn(self):
        self.setViewWidgetVisibility(True)

    def viewWidgetVisibleOff(self):
        self.setViewWidgetVisibility(False)

    def setViewWidgetVisibility(self, v):
        if isinstance(v, bool):
            self._widget.setVisible(v)
            QApplication.processEvents()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getViewWidgetVisibility(self):
        return self._widget.isVisible()

    # Public icon bar widget methods

    def iconBarVisibleOff(self):
        self.setIconBarVisibility(False)

    def iconBarVisibleOn(self):
        self.setIconBarVisibility(True)

    def setIconBarVisibility(self, v):
        if isinstance(v, bool):
            if self._icons['pin'].isChecked(): v = True
            for key in self._icons:
                if self._visibilityflags[key]: self._icons[key].setVisible(v)
                else: self._icons[key].setVisible(False)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getIconBarVisibility(self):
        return self._icons['pin'].isVisible()

    def setFullscreenButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['screen'] = v
            self._icons['screen'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setPinButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['pin'] = v
            if not v: self._icons['pin'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setExpandButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['expand'] = v
            if not v: self._icons['expand'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setGridButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['grid'] = v
            if not v: self._icons['grid'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setOrientButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['orient'] = v
            if not v: self._icons['orient'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['info'] = v
            if not v: self._icons['info'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setIsoButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['iso'] = v
            if not v: self._icons['iso'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setSliceButtonsAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['sliceplus'] = v
            self._visibilityflags['sliceminus'] = v
            if not v:
                self._icons['sliceplus'].setVisible(v)
                self._icons['sliceminus'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setShowButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['show'] = v
            if not v: self._icons['show'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setZoomButtonsAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['zoomin'] = v
            self._visibilityflags['zoomout'] = v
            self._visibilityflags['zoom1'] = v
            if not v:
                self._icons['zoomin'].setVisible(v)
                self._icons['zoomout'].setVisible(v)
                self._icons['zoom1'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setActionButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['actions'] = v
            if not v: self._icons['actions'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setToolButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['tools'] = v
            if not v: self._icons['tools'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setCaptureButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['capture'] = v
            if not v: self._icons['capture'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setClipboardButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['clipboard'] = v
            if not v: self._icons['clipboard'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setTransferButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['transfer'] = v
            if not v: self._icons['transfer'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setColorbarButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['colorbar'] = v
            if not v: self._icons['colorbar'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setRulerButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['ruler'] = v
            if not v: self._icons['ruler'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFullscreenButtonAvailability(self):
        return self._visibilityflags['screen']

    def getPinButtonAvailability(self):
        return self._visibilityflags['pin']

    def getExpandButtonAvailability(self):
        return self._visibilityflags['expand']

    def getGridButtonAvailability(self):
        return self._visibilityflags['grid']

    def getOrientButtonAvailability(self):
        return self._visibilityflags['orient']

    def getSliceButtonsAvailability(self):
        return self._visibilityflags['sliceplus']

    def getShowButtonAvailability(self):
        return self._visibilityflags['show']

    def getInfoButtonAvailability(self):
        return self._visibilityflags['info']

    def getIsoButtonAvailability(self):
        return self._visibilityflags['iso']

    def getActionButtonAvailability(self):
        return self._visibilityflags['actions']

    def getZoomButtonsAvailability(self):
        return self._visibilityflags['zoomin']

    def getToolButtonAvailability(self):
        return self._visibilityflags['tools']

    def getCaptureButtonAvailability(self):
        return self._visibilityflags['capture']

    def getClipboardButtonAvailability(self):
        return self._visibilityflags['clipboard']

    def getTransferButtonAvailability(self):
        return self._visibilityflags['transfer']

    def getColorbarButtonAvailability(self):
        return self._visibilityflags['colorbar']

    def getRulerButtonAvailability(self):
        return self._visibilityflags['ruler']

    def getThumbnail(self):
        return self._thumbnail

    def setThumbnail(self, thumbnail):
        from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
        if isinstance(thumbnail, ToolBarThumbnail):
            self._thumbnail = thumbnail
        else: raise TypeError('parameter type {} is not ToolBarThumbnail.'.format(type(thumbnail)))

    def hasThumbnail(self):
        return self._thumbnail is not None

    def getButtons(self):
        return self._icons

    # Event loop, solves VTK mouse move event bug

    @classmethod
    def _widgetUnderCursor(cls, widget):
        p = widget.cursor().pos()
        p = widget.mapFromGlobal(p)
        return 0 <= p.x() < widget.width() and 0 <= p.y() < widget.height()

    def timerEvent(self, event):
        w = self._widget
        # Icon bar visibility management
        if self._icons['pin'].isChecked():
            if not self.getIconBarVisibility(): self.iconBarVisibleOn()
        else:
            if self.getIconBarVisibility():
                if self._widgetUnderCursor(w): self.iconBarVisibleOff()
            else:
                p = w.cursor().pos()
                p = w.mapFromGlobal(p)
                if 0 <= p.x() < self._icons['pin'].width() and 0 <= p.y() < w.height(): self.iconBarVisibleOn()

    # Qt events

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            txt = event.mimeData().text()
            if txt[0:3] == 'idx':
                index = int(txt.split()[1])
                if self.hasThumbnail():
                    if self.hasVolume():
                        # Replace setting
                        if self._drop == 'Replace': self._thumbnail.getWidgetFromIndex(index).displayInSliceView()
                        # Overlay setting
                        elif self._drop == 'Overlay': self._thumbnail.getWidgetFromIndex(index).displayOverlay()
                        # Registered setting
                        elif self._drop == 'Registered':
                            moving = self._thumbnail.getWidgetFromIndex(index).getVolume()
                            fixed = self.getVolume()
                            if moving is not None:
                                if moving.hasSameID(fixed):
                                    self._thumbnail.getWidgetFromIndex(index).displayOverlay()
                                    return
                                elif moving.hasTransform(fixed):
                                    self._thumbnail.getWidgetFromIndex(index).displayOverlay()
                                    return
                            self._thumbnail.getWidgetFromIndex(index).displayInSliceView()
                        # Dialog setting
                        else:
                            # noinspection PyTypeChecker
                            dialog = QMessageBox(icon=QMessageBox.Question,
                                                 title='Display volume',
                                                 text='Display volume as overlay or replace ?')
                            btReplace = dialog.addButton('Replace', QMessageBox.AcceptRole)
                            btOverlay = dialog.addButton('Overlay', QMessageBox.AcceptRole)
                            dialog.setDefaultButton(btReplace)
                            dialog.addButton('Cancel', QMessageBox.RejectRole)
                            if platform == 'win32':
                                import pywinstyles
                                cl = self.palette().base().color()
                                c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                                pywinstyles.change_header_color(dialog, c)
                            dialog.exec()
                            if dialog.clickedButton() == btReplace:
                                self._thumbnail.getWidgetFromIndex(index).displayInSliceView()
                            elif dialog.clickedButton() == btOverlay:
                                self._thumbnail.getWidgetFromIndex(index).displayOverlay()
                    else: self._thumbnail.getWidgetFromIndex(index).displayInSliceView()


class IconBarOrthogonalSliceViewWidget(IconBarWidget):
    """
    IconBarOrthogonalSliceViewWidget class

    Description
    ~~~~~~~~~~~

    OrthogonalSliceViewWidget with icon bar.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalSliceViewWidget

    Creation: 17/04/2022
    Last revision: 17/04/2022
    """

    # Special method

    def __init__(self, widget=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = OrthogonalSliceViewWidget()
        if isinstance(widget, OrthogonalSliceViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not OrthogonalSliceViewWidget.'.format(type(widget)))
        self._hideViewWidget()


class IconBarOrthogonalRegistrationViewWidget(IconBarWidget):
    """
    IconBarOrthogonalRegistrationViewWidget class

    Description
    ~~~~~~~~~~~

    OrthogonalRegistrationViewWidget with icon bar.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalRegistrationViewWidget

    Creation: 17/04/2022
    Last revision: 17/04/2022
    """

    # Special method

    def __init__(self, widget=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = OrthogonalRegistrationViewWidget()
        if isinstance(widget, OrthogonalRegistrationViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not OrthogonalRegistrationViewWidget.'.format(type(widget)))
        self.setPinButtonAvailability(False)
        self.setExpandButtonAvailability(False)
        self.setShowButtonAvailability(False)
        self.setInfoButtonAvailability(False)
        self.setColorbarButtonAvailability(False)
        self.setToolButtonAvailability(False)
        self.setRulerButtonAvailability(False)
        self.setIsoButtonAvailability(False)
        self._hideViewWidget()

        # Registration area box synchronisation

        for view1 in self.getViewWidget().getSliceViewWidgets():
            view1.setSelectable(False)
            for view2 in self.getViewWidget().getSliceViewWidgets():
                if view1 != view2:
                    view1.RegistrationBoxVisibilityChanged.connect(view2.synchroniseRegistrationBoxVisibilityChanged)
                    view1.RegistrationBoxChanged.connect(view2.synchroniseRegistrationBoxChanged)

    # Public methods

    def setCrop(self, crop):
        if isinstance(crop, bool):  self._widget.getFirstSliceViewWidget().setCrop(crop)
        else: raise TypeError('parameter type {} is not bool'.format(type(crop)))

    def getCrop(self):
        return self._widget.getFirstSliceViewWidget().getCrop()

    def cropOn(self):
        self.setCrop(True)

    def cropOff(self):
        self.setCrop(False)

    def setRegistrationBoxVisibility(self, v):
        if isinstance(v, bool): self._widget.getFirstSliceViewWidget().setRegistrationBoxVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getRegistrationBoxVisibility(self):
        return self._widget.getFirstSliceViewWidget().getRegistrationBoxVisibility()

    def registrationBoxOn(self):
        self.setRegistrationBoxVisibility(True)

    def registrationBoxOff(self):
        self.setRegistrationBoxVisibility(False)

    def getRegistrationBoxMatrixArea(self):
        return self._widget.getFirstSliceViewWidget().getRegistrationBoxMatrixArea()

    def displayEdge(self):
        self._widget.getFirstSliceViewWidget().displayEdge()

    def displayNative(self):
        self._widget.getFirstSliceViewWidget().displayNative()

    def displayEdgeAndNative(self):
        self._widget.getFirstSliceViewWidget().displayEdgeAndNative()


class IconBarOrthogonalRegistrationViewWidget2(IconBarOrthogonalRegistrationViewWidget):
    """
    IconBarOrthogonalRegistrationViewWidget2 class

    Description
    ~~~~~~~~~~~

    OrthogonalRegistrationViewWidget with icon bar and rigid transformation buttons.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalRegistrationViewWidget -> IconBarOrthogonalRegistrationViewWidget2

    Creation: 17/04/2022
    Last revision: 22/05/2025
    """

    # Special method

    def __init__(self, widget=None, parent=None):
        super().__init__(widget, parent)

        self._buttons = dict()
        self._step = 0.5

        # Axial buttons

        self._buttons['up0'] = self._createButton('wup.png', 'up.png', checkable=False, autorepeat=True)
        self._buttons['down0'] = self._createButton('wdown.png', 'down.png', checkable=False, autorepeat=True)
        self._buttons['left0'] = self._createButton('wleft.png', 'left.png', checkable=False, autorepeat=True)
        self._buttons['right0'] = self._createButton('wright.png', 'right.png', checkable=False, autorepeat=True)
        self._buttons['rotc0'] = self._createButton('wrot1.png', 'rot1.png', checkable=False, autorepeat=True)
        self._buttons['rota0'] = self._createButton('wrot2.png', 'rot2.png', checkable=False, autorepeat=True)
        # noinspection PyUnresolvedReferences
        self._buttons['up0'].clicked.connect(lambda: self._ytranslation(self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['down0'].clicked.connect(lambda: self._ytranslation(-self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['left0'].clicked.connect(lambda: self._xtranslation(self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['right0'].clicked.connect(lambda: self._xtranslation(-self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['rotc0'].clicked.connect(lambda: self._zrotation(self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['rota0'].clicked.connect(lambda: self._zrotation(-self._step))
        self._buttons['up0'].setToolTip('Forward translation')
        self._buttons['down0'].setToolTip('Backward translation')
        self._buttons['left0'].setToolTip('Right translation')
        self._buttons['right0'].setToolTip('Left translation')
        self._buttons['rotc0'].setToolTip('Clockwise Z rotation')
        self._buttons['rota0'].setToolTip('Counter-clockwise Z rotation')
        layout0 = QHBoxLayout()
        layout0.setSpacing(0)
        layout0.setContentsMargins(0, 0, 0, 0)
        layout0.addWidget(self._buttons['up0'])
        layout0.addWidget(self._buttons['down0'])
        layout0.addWidget(self._buttons['left0'])
        layout0.addWidget(self._buttons['right0'])
        layout0.addWidget(self._buttons['rotc0'])
        layout0.addWidget(self._buttons['rota0'])

        # Coronal buttons

        self._buttons['up1'] = self._createButton('wup.png', 'up.png', checkable=False, autorepeat=True)
        self._buttons['down1'] = self._createButton('wdown.png', 'down.png', checkable=False, autorepeat=True)
        self._buttons['left1'] = self._createButton('wleft.png', 'left.png', checkable=False, autorepeat=True)
        self._buttons['right1'] = self._createButton('wright.png', 'right.png', checkable=False, autorepeat=True)
        self._buttons['rotc1'] = self._createButton('wrot1.png', 'rot1.png', checkable=False, autorepeat=True)
        self._buttons['rota1'] = self._createButton('wrot2.png', 'rot2.png', checkable=False, autorepeat=True)
        # noinspection PyUnresolvedReferences
        self._buttons['up1'].clicked.connect(lambda: self._ztranslation(self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['down1'].clicked.connect(lambda: self._ztranslation(-self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['left1'].clicked.connect(lambda: self._xtranslation(self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['right1'].clicked.connect(lambda: self._xtranslation(-self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['rotc1'].clicked.connect(lambda: self._yrotation(-self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['rota1'].clicked.connect(lambda: self._yrotation(self._step))
        self._buttons['up1'].setToolTip('Cranial translation')
        self._buttons['down1'].setToolTip('Caudal translation')
        self._buttons['left1'].setToolTip('Right translation')
        self._buttons['right1'].setToolTip('Left translation')
        self._buttons['rotc1'].setToolTip('Clockwise Y rotation')
        self._buttons['rota1'].setToolTip('Counter-clockwise Y rotation')
        layout1 = QHBoxLayout()
        layout1.setSpacing(0)
        layout1.setContentsMargins(0, 0, 0, 0)
        layout1.addWidget(self._buttons['up1'])
        layout1.addWidget(self._buttons['down1'])
        layout1.addWidget(self._buttons['left1'])
        layout1.addWidget(self._buttons['right1'])
        layout1.addWidget(self._buttons['rotc1'])
        layout1.addWidget(self._buttons['rota1'])

        # Sagittal buttons

        self._buttons['up2'] = self._createButton('wup.png', 'up.png', checkable=False, autorepeat=True)
        self._buttons['down2'] = self._createButton('wdown.png', 'down.png', checkable=False, autorepeat=True)
        self._buttons['left2'] = self._createButton('wleft.png', 'left.png', checkable=False, autorepeat=True)
        self._buttons['right2'] = self._createButton('wright.png', 'right.png', checkable=False, autorepeat=True)
        self._buttons['rotc2'] = self._createButton('wrot1.png', 'rot1.png', checkable=False, autorepeat=True)
        self._buttons['rota2'] = self._createButton('wrot2.png', 'rot2.png', checkable=False, autorepeat=True)
        # noinspection PyUnresolvedReferences
        self._buttons['up2'].clicked.connect(lambda: self._ztranslation(self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['down2'].clicked.connect(lambda: self._ztranslation(-self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['left2'].clicked.connect(lambda: self._ytranslation(self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['right2'].clicked.connect(lambda: self._ytranslation(-self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['rotc2'].clicked.connect(lambda: self._xrotation(self._step))
        # noinspection PyUnresolvedReferences
        self._buttons['rota2'].clicked.connect(lambda: self._xrotation(-self._step))
        self._buttons['up2'].setToolTip('Cranial translation')
        self._buttons['down2'].setToolTip('Caudal translation')
        self._buttons['left2'].setToolTip('Forward translation')
        self._buttons['right2'].setToolTip('Backward translation')
        self._buttons['rotc2'].setToolTip('Clockwise X rotation')
        self._buttons['rota2'].setToolTip('Counter-clockwise X rotation')
        layout2 = QHBoxLayout()
        layout2.setSpacing(0)
        layout2.setContentsMargins(0, 0, 0, 0)
        layout2.addWidget(self._buttons['up2'])
        layout2.addWidget(self._buttons['down2'])
        layout2.addWidget(self._buttons['left2'])
        layout2.addWidget(self._buttons['right2'])
        layout2.addWidget(self._buttons['rotc2'])
        layout2.addWidget(self._buttons['rota2'])

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(layout0)
        layout.addLayout(layout1)
        layout.addLayout(layout2)

        # < Revision 22/05/2025
        # black background of button bar
        self._frame = QFrame(self)
        if platform == 'win32':
            self._frame.setObjectName('TrfBar')
            self._frame.setStyleSheet('QFrame#TrfBar { background-color: #000000; border-color: #000000; } '
                                      'QToolTip#TrfBar { color: #000000; background-color: #FFFFE0; border: 0px; font-size: 8pt; }')
        else:
            self._frame.setAutoFillBackground(True)
            # noinspection PyTypeChecker
            self._frame.palette().setColor(QPalette.Window, Qt.black)
        self._frame.setLayout(layout)
        # Revision 22/05/2025 >

        for view in self.getViewWidget().getSliceViewWidgets():
            view.TranslationsChanged.connect(lambda d1, d2: self._updateTooltips())
            view.RotationsChanged.connect(lambda d1, d2: self._updateTooltips())

        # < Revision 22/05/2025
        # self._vlayout.addLayout(layout)
        self._vlayout.addWidget(self._frame)
        # Revision 22/05/2025 >
        self._hideViewWidget()

    # Private methods

    def _updateTooltips(self):
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations())
        t = list(widget.getTranslations())
        self._buttons['up0'].setToolTip('Forward translation\nY Translation {:.1f} mm'.format(t[1]))
        self._buttons['down0'].setToolTip('Backward translation\nY Translation {:.1f} mm'.format(t[1]))
        self._buttons['left0'].setToolTip('Right translation\nX Translation {:.1f} mm'.format(t[0]))
        self._buttons['right0'].setToolTip('Left translation\nX Translation {:.1f} mm'.format(t[0]))
        self._buttons['rotc0'].setToolTip('Clockwise Z rotation\nZ Rotation {:.1f}°'.format(r[2]))
        self._buttons['rota0'].setToolTip('Counter-clockwise Z Rotation\nZ Rotation {:.1f}°'.format(r[2]))
        self._buttons['up1'].setToolTip('Forward translation\nZ Translation {:.1f} mm'.format(t[2]))
        self._buttons['down1'].setToolTip('Backward translation\nZ Translation {:.1f} mm'.format(t[2]))
        self._buttons['left1'].setToolTip('Right translation\nX Translation {:.1f} mm'.format(t[0]))
        self._buttons['right1'].setToolTip('Left translation\nX Translation {:.1f} mm'.format(t[0]))
        self._buttons['rotc1'].setToolTip('Clockwise Y rotation\nY Rotation {:.1f}°'.format(r[1]))
        self._buttons['rota1'].setToolTip('Counter-clockwise Y Rotation\nY Rotation {:.1f}°'.format(r[1]))
        self._buttons['up2'].setToolTip('Forward translation\nZ Translation {:.1f} mm'.format(t[2]))
        self._buttons['down2'].setToolTip('Backward translation\nZ Translation {:.1f} mm'.format(t[2]))
        self._buttons['left2'].setToolTip('Forward translation\nY Translation {:.1f} mm'.format(t[1]))
        self._buttons['right2'].setToolTip('Backward translation\nY Translation {:.1f} mm'.format(t[1]))
        self._buttons['rotc2'].setToolTip('Clockwise X rotation\nX Rotation {:.1f}°'.format(r[0]))
        self._buttons['rota2'].setToolTip('Counter-clockwise X Rotation\nX Rotation {:.1f}°'.format(r[0]))

    def _xtranslation(self, v):
        widget = self().getFirstSliceViewWidget()
        t = list(widget.getTranslations(index=0))
        t[0] += v
        widget.setTranslations(tuple(t), index=0)
        self._buttons['left0'].setToolTip('Right translation\nX Translation {:.2f} mm'.format(t[0]))
        self._buttons['right0'].setToolTip('Left translation\nX Translation {:.2f} mm'.format(t[0]))
        self._buttons['left1'].setToolTip('Right translation\nX Translation {:.2f} mm'.format(t[0]))
        self._buttons['right1'].setToolTip('Left translation\nX Translation {:.2f} mm'.format(t[0]))

    def _ytranslation(self, v):
        widget = self().getFirstSliceViewWidget()
        t = list(widget.getTranslations(index=0))
        t[1] += v
        widget.setTranslations(tuple(t), index=0)
        self._buttons['up0'].setToolTip('Forward translation\nY Translation {:.2f} mm'.format(t[1]))
        self._buttons['down0'].setToolTip('Backward translation\nY Translation {:.2f} mm'.format(t[1]))
        self._buttons['left2'].setToolTip('Forward translation\nY Translation {:.2f} mm'.format(t[1]))
        self._buttons['right2'].setToolTip('Backward translation\nY Translation {:.2f} mm'.format(t[1]))

    def _ztranslation(self, v):
        widget = self().getFirstSliceViewWidget()
        t = list(widget.getTranslations(index=0))
        t[2] += v
        widget.setTranslations(tuple(t), index=0)
        self._buttons['up1'].setToolTip('Cranial translation\nZ Translation {:.2f} mm'.format(t[2]))
        self._buttons['down1'].setToolTip('Caudal translation\nZ Translation {:.2f} mm'.format(t[2]))
        self._buttons['up2'].setToolTip('Cranial translation\nZ Translation {:.2f} mm'.format(t[2]))
        self._buttons['down2'].setToolTip('Caudal translation\nZ Translation {:.2f} mm'.format(t[2]))

    def _xrotation(self, v):
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations(index=0))
        r[0] += v
        widget.setRotations(tuple(r), index=0)
        self._buttons['rotc2'].setToolTip('Clockwise X rotation\nX Rotation {:.2f}°'.format(r[0]))
        self._buttons['rota2'].setToolTip('Counter-clockwise X Rotation\nX Rotation {:.2f}°'.format(r[0]))

    def _yrotation(self, v):
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations(index=0))
        r[1] += v
        widget.setRotations(tuple(r), index=0)
        self._buttons['rotc1'].setToolTip('Clockwise Y rotation\nY Rotation {:.2f}°'.format(r[1]))
        self._buttons['rota1'].setToolTip('Counter-clockwise Y Rotation\nY Rotation {:.2f}°'.format(r[1]))

    def _zrotation(self, v):
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations(index=0))
        r[2] += v
        widget.setRotations(tuple(r), index=0)
        self._buttons['rotc0'].setToolTip('Clockwise Z rotation\nZ Rotation {:.2f}°'.format(r[2]))
        self._buttons['rota0'].setToolTip('Counter-clockwise Z Rotation\nZ Rotation {:.2f}°'.format(r[2]))

    # Public methods

    def addOverlay(self, volume):
        super().addOverlay(volume)
        self._updateTooltips()

    def setMoveOverlayOn(self):
        widget = self().getFirstSliceViewWidget()
        widget.setMoveOverlayFlag()

    def setMoveOverlayOff(self):
        widget = self().getFirstSliceViewWidget()
        widget.setMoveOverlayOff()

    def setMoveButtonsVisibility(self, v):
        if isinstance(v, bool):
            for key in self._buttons:
                self._buttons[key].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getMoveButtonsVisibility(self):
        return self._buttons['up0'].isVisible()

    def setMoveStep(self, v):
        if isinstance(v, float): self._step = v
        else: raise TypeError('parameter type {} is not float.'.format(float))

    def getMoveStep(self):
        return self._step


class IconBarOrthogonalReorientViewWidget(IconBarWidget):
    """
    IconBarOrthogonalReorientViewWidget class

    Description
    ~~~~~~~~~~~

    OrthogonalReorientViewWidget with icon bar.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalReorientViewWidget

    Creation: 17/04/2022
    Last revision:
    """

    def __init__(self, widget=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = OrthogonalReorientViewWidget()
        if isinstance(widget, OrthogonalReorientViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not OrthogonalReorientViewWidget.'.format(type(widget)))
        self.setIsoButtonAvailability(False)
        self._hideViewWidget()


class IconBarOrthogonalSliceVolumeViewWidget(IconBarWidget):
    """
    IconBarOrthogonalSliceVolumeViewWidget class

    Description
    ~~~~~~~~~~~

    OrthogonalSliceVolumeViewWidget with icon bar.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalSliceVolumeViewWidget

    Creation: 17/04/2022
    Last revision:
    """

    # Special method

    def __init__(self, widget=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = OrthogonalSliceVolumeViewWidget()
        if isinstance(widget, OrthogonalSliceVolumeViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not OrthogonalSliceVolumeViewWidget.'.format(type(widget)))
        self._hideViewWidget()

    # Public methods

    def setVolume(self, vol):
        super().setVolume(vol)
        self._transfer.setViewWidget(self().getFirstVolumeViewWidget())

    def setCameraPositionButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['campos'] = v
            if not v: self._icons['campos'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setTextureSettingsButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['texture'] = v
            if not v: self._icons['texture'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getCameraPositionButtonAvailability(self):
        return self._visibilityflags['campos']

    def getTextureSettingsButtonAvailability(self):
        return self._visibilityflags['texture']


class IconBarOrthogonalSliceTrajectoryViewWidget(IconBarWidget):
    """
    IconBarOrthogonalSliceTrajectoryViewWidget class

    Description
    ~~~~~~~~~~~

    OrthogonalSliceTrajectoryViewWidget with icon bar.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalSliceTrajectoryViewWidget

    Creation: 17/04/2022
    Last Revision: 06/12/2024
    """

    def __init__(self, widget=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = OrthogonalTrajectoryViewWidget()
        if isinstance(widget, OrthogonalTrajectoryViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not OrthogonalTrajectoryViewWidget.'.format(type(widget)))
        self._hideViewWidget()
        self().setActionVisibility('target', False)
        self().setActionVisibility('trajectory', False)

        # Slab thickness button

        self._icons['thick'] = self._createButton('wthickness.png', 'thickness.png', checkable=True, autorepeat=False)
        self._icons['thick'].setToolTip('Slab thickness management.')

        self._sstep = LabeledDoubleSpinBox(title='Slice step', fontsize=10)
        self._sstep.setValue(1.0)
        self._sstep.setRange(0.5, 5.0)
        self._sstep.setSingleStep(0.1)
        self._sstep.setSuffix(' mm')
        self._sthick = LabeledDoubleSpinBox(title='Slab thickness', fontsize=10)
        self._sthick.setValue(0.0)
        self._sthick.setRange(0.0, 5.0)
        self._sthick.setSingleStep(0.1)
        self._sthick.setSuffix(' mm')

        menu = QMenu()
        # noinspection PyTypeChecker
        menu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        menu.setWindowFlag(Qt.FramelessWindowHint, True)
        menu.setAttribute(Qt.WA_TranslucentBackground, True)
        a = QWidgetAction(self)
        a.setDefaultWidget(self._sstep)
        menu.addAction(a)
        a = QWidgetAction(self)
        a.setDefaultWidget(self._sthick)
        menu.addAction(a)
        submenu = menu.addMenu('Slab type')
        action = dict()
        action['min'] = QAction('Min', self)
        action['max'] = QAction('Max', self)
        action['mean'] = QAction('Mean', self)
        action['sum'] = QAction('Sum', self)
        action['min'].setCheckable(True)
        action['max'].setCheckable(True)
        action['mean'].setCheckable(True)
        action['sum'].setCheckable(True)
        action['mean'].setChecked(True)
        # noinspection PyUnresolvedReferences
        action['min'].triggered.connect(lambda _: self._slabTypeChanged(0))
        # noinspection PyUnresolvedReferences
        action['max'].triggered.connect(lambda _: self._slabTypeChanged(1))
        # noinspection PyUnresolvedReferences
        action['mean'].triggered.connect(lambda _: self._slabTypeChanged(2))
        # noinspection PyUnresolvedReferences
        action['sum'].triggered.connect(lambda _: self._slabTypeChanged(3))
        self._group = QActionGroup(self)
        self._group.setExclusive(True)
        self._group.addAction(action['min'])
        self._group.addAction(action['max'])
        self._group.addAction(action['mean'])
        self._group.addAction(action['sum'])
        submenu.addAction(action['mean'])
        submenu.addAction(action['sum'])
        submenu.addAction(action['min'])
        submenu.addAction(action['max'])
        # noinspection PyUnresolvedReferences
        menu.aboutToHide.connect(self._slabThicknessChanged)
        self._icons['thick'].setMenu(menu)

        layout = self._bar.layout()
        layout.insertWidget(7, self._icons['thick'])

        # Sphere cursor

        self._icons['sphere'] = self._createButton('wcursor.png', 'cursor.png', checkable=True, autorepeat=False)
        self._icons['sphere'].setToolTip('Sphere cursor management.')

        view = self._widget[0, 0]
        menu = QMenu()
        # noinspection PyTypeChecker
        menu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        menu.setWindowFlag(Qt.FramelessWindowHint, True)
        menu.setAttribute(Qt.WA_TranslucentBackground, True)
        a = QWidgetAction(self)
        w = LabeledSlider(title='Cursor radius', fontsize=10)
        w.setRange(0, 50)
        w.setValue(0)
        # noinspection PyUnresolvedReferences
        w.valueChanged.connect(view.setSphereCursorRadius)
        a.setDefaultWidget(w)
        menu.addAction(a)
        a = QWidgetAction(self)
        w = LabeledSlider(title='Cursor opacity', fontsize=10)
        w.setRange(0, 100)
        w.setValue(50)
        # noinspection PyUnresolvedReferences
        w.valueChanged.connect(view.setSphereCursorOpacity)
        a.setDefaultWidget(w)
        menu.addAction(a)
        self._icons['sphere'].setMenu(menu)

        layout.insertWidget(13, self._icons['sphere'])

        # < Revision 06/12/2024
        self._visibilityflags['thick'] = True
        self._visibilityflags['sphere'] = True
        # Revision 06/12/2024 >

    # Private methods

    def _slabThicknessChanged(self):
        view = self._widget[0, 1]
        if self._sthick.value() != view.getSlabThickness(): view.setSlabThickness(self._sthick.value(), signal=True)
        if self._sstep.value() != view.getSliceStep(): view.setSliceStep(self._sstep.value(), signal=True)

    def _slabTypeChanged(self, slab):
        if isinstance(slab, int):
            view = self._widget[0, 1]
            if slab == 0: view.setSlabTypeToMin(signal=True)
            elif slab == 1: view.setSlabTypeToMax(signal=True)
            elif slab == 2: view.setSlabTypeToMean(signal=True)
            elif slab == 3: view.setSlabTypeToSum(signal=True)
        else: raise TypeError('parameter type {} is not str.'.format(type(int)))

    # Public method

    def setVolume(self, vol):
        super().setVolume(vol)
        self._transfer.setViewWidget(self().getFirstVolumeViewWidget())
        # < Revision 18/10/2024
        # Reset slab properties
        self._sstep.setValue(1.0)
        self._sthick.setValue(0.0)
        self._widget[0, 1].setSlabThickness(0.0, signal=False)
        self._widget[0, 1].setSliceStep(1.0, signal=False)
        # Revision 18/10/2024

    def setSlabThicknessButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['thick'] = v
            if not v: self._icons['thick'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getSlabThicknessButtonAvailability(self):
        return self._visibilityflags['thick']


class IconBarMultiSliceGridViewWidget(IconBarWidget):
    """
    IconBarMultiSliceGridViewWidget class

    Description
    ~~~~~~~~~~~

    MultiSliceGridViewWidget with icon bar.
    Displays several adjacent slices in 3 x 3 grid with overlays and ROI support.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarMultiSliceGridViewWidget

    Creation: 17/04/2022
    Last revision:
    """

    def __init__(self, widget=None, rois=None, draw=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = MultiSliceGridViewWidget(rois=rois, draw=draw)
        if isinstance(widget, MultiSliceGridViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not MultiSliceGridViewWidget.'.format(type(widget)))
        self._hideViewWidget()

    # Public method

    def setVolume(self, vol):
        super().setVolume(vol)
        if vol.isThickAnisotropic():
            # Display in native orientation
            orient = vol.getNative2DOrientation()
            if orient == 1: self().setAxialOrientation()
            elif orient == 2: self().setCoronalOrientation()
            elif orient == 3: self().setSagittalOrientation()
            else: self().setAxialOrientation()


class IconBarSynchronisedGridViewWidget(IconBarWidget):
    """
    IconBarSynchronisedGridViewWidget class

    Description
    ~~~~~~~~~~~

    SynchronisedGridViewWidget with icon bar.
    Displays same slices of multiple volumes in 3 x 3 grid.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarSynchronisedGridViewWidget

    Creation: 17/04/2022
    Last revision:
    """

    def __init__(self, widget=None, rois=None, draw=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = SynchronisedGridViewWidget(rois=rois, draw=draw)
        if isinstance(widget, SynchronisedGridViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not SynchronisedGridViewWidget.'.format(type(widget)))
        self._hideViewWidget()

    # Private method

    def setVolume(self, vol):
        super().setVolume(vol)
        if vol.isThickAnisotropic():
            # Display in native orientation
            orient = vol.getNative2DOrientation()
            if orient == 1: self().setAxialOrientation()
            elif orient == 2: self().setCoronalOrientation()
            elif orient == 3: self().setSagittalOrientation()
            else: self().setAxialOrientation()


class IconBarSliceViewWidget(IconBarWidget):
    """
    IconBarSliceViewWidget class

    Description
    ~~~~~~~~~~~

    SliceViewWidget with icon bar.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarSliceViewWidget

    Creation: 17/04/2022
    Last revision: 07/12/2024
    """

    def __init__(self, widget=None, rois=None, draw=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = SliceROIViewWidget(rois=rois, draw=draw)
        if isinstance(widget, SliceROIViewWidget): self._setViewWidget(widget)
        else: raise TypeError('parameter type {} is not SliceROIViewWidget.'.format(type(widget)))
        self._hideViewWidget()

    # Private methods

    def _onMenuTools(self, action):
        s = str(action.text())[0]
        w = self.getViewWidget()
        if w is not None:
            if s == 'D': w.addDistanceTool()
            elif s == 'O': w.addOrthogonalDistanceTool()
            else: w.addAngleTool()

    def _setViewWidget(self, widget):
        if isinstance(widget, SliceROIViewWidget):
            self._widget = widget
            self._widget.setName('SliceViewWidget')
            self._layout.addWidget(widget)
            widget.setSelectable(False)
            self.setExpandButtonAvailability(False)
            self._icons['orient'] = self._createButton('wdimz.png', 'dimz.png', checkable=False, autorepeat=False)
            self._icons['sliceminus'] = self._createButton('wminus.png', 'minus.png', checkable=False, autorepeat=True)
            self._icons['sliceplus'] = self._createButton('wplus.png', 'plus.png', checkable=False, autorepeat=True)
            self._icons['orient'].setMenu(widget.getPopupOrientation())
            # noinspection PyUnresolvedReferences
            self._icons['sliceminus'].clicked.connect(widget.sliceMinus)
            # noinspection PyUnresolvedReferences
            self._icons['sliceplus'].clicked.connect(widget.slicePlus)
            self._visibilityflags['orient'] = True
            self._visibilityflags['sliceminus'] = True
            self._visibilityflags['sliceplus'] = True
            layout = self._bar.layout()
            layout.insertWidget(2, self._icons['sliceplus'])
            layout.insertWidget(2, self._icons['sliceminus'])
            layout.insertWidget(2, self._icons['orient'])
            self._icons['show'].setMenu(widget.getPopupVisibility())
            self._icons['actions'].setMenu(widget.getPopupActions())
            self._icons['colorbar'].setMenu(widget.getPopupColorbarPosition())
            # noinspection PyUnresolvedReferences
            self._icons['zoomin'].clicked.connect(widget.zoomIn)
            # noinspection PyUnresolvedReferences
            self._icons['zoomout'].clicked.connect(widget.zoomOut)
            # noinspection PyUnresolvedReferences
            self._icons['zoom1'].clicked.connect(widget.zoomDefault)
            # noinspection PyUnresolvedReferences
            self._icons['capture'].clicked.connect(widget.saveCapture)
            # noinspection PyUnresolvedReferences
            self._icons['clipboard'].clicked.connect(widget.copyToClipboard)
            widget.getAction()['axial'].triggered.connect(lambda: self._icons['orient'].setIcon(self._ax))
            widget.getAction()['coronal'].triggered.connect(lambda: self._icons['orient'].setIcon(self._cor))
            widget.getAction()['sagittal'].triggered.connect(lambda: self._icons['orient'].setIcon(self._sag))
        else: raise TypeError('parameter type {} is not SliceROIViewWidget.'.format(type(widget)))

    # Public methods

    def setVolume(self, vol):
        super().setVolume(vol)
        # timer used to detect when mouse leaves icon bar
        # call timerEvent Qt event method
        self.timerEnabled()

    def removeVolume(self):
        super().removeVolume()
        # timer used to detect when mouse leaves icon bar
        # call timerEvent Qt event method
        self.timerDisabled()

    def timerEvent(self, event):
        w = self._widget
        # Icon bar visibility management
        if not self._icons['pin'].isChecked():
            if self.getIconBarVisibility():
                if self._widgetUnderCursor(w): self.iconBarVisibleOff()
            else:
                p = w.cursor().pos()
                p = w.mapFromGlobal(p)
                if 0 <= p.x() < self._icons['pin'].width() and 0 <= p.y() < w.height(): self.iconBarVisibleOn()
        """
        # < Revision 13/03/2025
        # Mouse move event management
        # solves VTK mouse move event bug
        interactor = w.getWindowInteractor()
        p = w.cursor().pos()
        p = w.mapFromGlobal(p)
        p.setY(w.height() - p.y() - 1)
        interactor.SetEventInformation(p.x(), p.y())
        interactor.MouseMoveEvent()
        # Revision 13/03/2025 >
        """


class IconBarViewWidgetCollection(QObject):
    """
    IconBarViewWidgetCollection

    Description
    ~~~~~~~~~~~

    Indexed dict-like container of IconBarWidgets.

    Inheritance
    ~~~~~~~~~~~

    QObject -> IconBarViewWidgetCollection

    Creation: 17/04/2022
    Last Revision: 27/05/2025
    """

    __slots__ = ['_widgets', '_index']

    # Class method

    def _KeyToIndex(self, key):
        keys = [k[0] for k in self._widgets]
        return keys.index(key)

    # Special methods

    """
    Private attributes

    _widgets    list[IconBarWidget]
    _index      int, index for Iterator
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._widgets = list()
        self._index = 0

    def __str__(self):
        index = 0
        buff = 'IconBarWidget count #{}\n'.format(len(self._widgets))
        for widget in self._widgets:
            index += 1
            buff += 'IconBarWidget #{}\n'.format(index)
            buff += '{}\n'.format(str(widget))
        return buff

    def __repr__(self):
        return 'IconBarViewWidgetCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container special methods

    def __getitem__(self, index):
        if isinstance(index, str):
            index = self._KeyToIndex(index)
        if isinstance(index, int):
            if 0 <= index < len(self._widgets): return self._widgets[index][1]
            else: raise IndexError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int or str.'.format(type(index)))

    def __setitem__(self, index, value):
        if isinstance(value, IconBarWidget):
            if isinstance(index, int):
                if 0 <= index < len(self._widgets):
                    if value.getName() not in self._widgets:
                        self._widgets[index] = [value.getName(), value]
                else: raise IndexError('parameter value {} is out of range.'.format(index))
            else: raise TypeError('first parameter type {} is not int.'.format(type(index)))
        else: raise TypeError('second parameter type {} is not IconBarWidget.'.format(type(value)))

    def __delitem__(self, index):
        if isinstance(index, str):
            index = self._KeyToIndex(index)
        if isinstance(index, int):
            if 0 <= index < len(self._widgets):
                del self._widgets[index]
            else: IndexError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int or str.'.format(index))

    def __len__(self):
        return len(self._widgets)

    def __contains__(self, value):
        if isinstance(value, str):
            keys = [k[0] for k in self._widgets]
            return value in keys
        elif isinstance(value, IconBarWidget):
            values = [k[1] for k in self._widgets]
            return value in values
        else: raise TypeError('parameter type {} is not str or IconBarWidget.'.format(type(value)))

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self._widgets):
            n = self._index
            self._index += 1
            return self._widgets[n][1]
        else:
            raise StopIteration

    # Container public methods

    def isEmpty(self):
        return len(self._widgets) == 0

    def count(self):
        return len(self._widgets)

    def remove(self, value):
        self._widgets.remove(self._widgets[value])

    def keys(self):
        return [k[0] for k in self._widgets]

    def index(self, value):
        if isinstance(value, IconBarWidget):
            values = [k[1] for k in self._widgets]
            return values.index(value)
        elif isinstance(value, str):
            keys = [k[0] for k in self._widgets]
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or IconBarWidget.'.format(type(value)))

    def reverse(self):
        self._widgets.reverse()

    def append(self, value):
        if isinstance(value, IconBarWidget):
            if value.getName() not in self.keys():
                self._widgets.append([value.getName(), value])
                self._widgets[-1][1].NameChanged.connect(self.updateKeys)
        else: raise TypeError('parameter type {} is not IconBarWidget.'.format(type(value)))

    def insert(self, value, index):
        if isinstance(value, IconBarWidget):
            if isinstance(index, int):
                if 0 <= index < len(self._widgets):
                    if value.getName() not in self.keys():
                        self._widgets.insert(index, [value.getName(), value])
                else: raise ValueError('parameter value {} is out of range.'.format(index))
            else: raise TypeError('parameter type {} is not int.'.format(type(index)))
        else: raise TypeError('parameter type {} is not IconBarWidget.'.format(type(value)))

    def clear(self):
        self._widgets.clear()

    def sort(self, reverse=False):
        self._widgets.sort(reverse=reverse)

    def copy(self):
        widgets = IconBarViewWidgetCollection()
        for widget in self._widgets:
            widgets.append(widget[1])
        return widgets

    def copyToList(self):
        return [k[1] for k in self._widgets]

    def updateKeys(self):
        for widget in self._widgets:
            widget[0] = widget[1].getName()

    # Volume methods

    def setVolume(self, vol, wait=None):
        if isinstance(vol, SisypheVolume):
            if self.count() > 0:
                if wait is not None:
                    wait.setProgressRange(0, self.count())
                    wait.progressVisibilityOn()
                for widget in self:
                    if wait is not None:
                        info = '{} display in {} view...'.format(vol.getBasename(), widget.getName())
                        wait.setInformationText(info)
                        wait.incCurrentProgressValue()
                    if not vol.isThickAnisotropic():
                        widget.setVolume(vol)
                        widget.setVisible(True)
                    elif isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        widget.setVolume(vol)
                        widget.setVisible(True)
                    else: widget.setVisible(False)
                    QApplication.processEvents()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def getVolume(self):
        # < Revision 20/02/2025
        # if self.count() > 0: return self[0].getVolume()
        # else: return None
        n = self.count()
        if n > 0:
            for i in range(n):
                if self[i].hasVolume():
                    return self[i].getVolume()
        return None
        # Revision 20/02/2025 >

    def hasVolume(self):
        if self.count() > 0: return self[0].hasVolume()
        else: return False

    def removeVolume(self):
        if self.count() > 0:
            for widget in self:
                if widget.hasVolume():
                    widget.removeVolume()

    # Overlay methods

    def addOverlay(self, vol, wait=None):
        if isinstance(vol, SisypheVolume):
            # < Revision 27/05/2025
            # add flag return value
            # add overlay count test
            flag = False
            if self.count() > 0:
                if wait is not None:
                    wait.setProgressRange(0, self.count())
                    wait.progressVisibilityOn()
                if self.getFirstSliceView().getOverlayCount() < 8:
                    for widget in self:
                        if wait is not None:
                            info = '{} display as overlay in {} view...'.format(vol.getBasename(), widget.getName())
                            wait.setInformationText(info)
                            wait.incCurrentProgressValue()
                        widget.addOverlay(vol)
                        QApplication.processEvents()
                    flag = True
                else:
                    wait.hide()
                    messageBox(title='Add overlay...',
                               text='Maximum number of overlays reached.\n'
                                    'Removing an overlay before opening a new one.')

            return flag
            # Revision 27/05/2025 >
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def removeOverlay(self, vol):
        if isinstance(vol, SisypheVolume):
            if self.count() > 0:
                for widget in self:
                    widget.removeOverlay(vol)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def removeAllOverlays(self):
        if self.count() > 0:
            for widget in self:
                widget.removeAllOverlays()

    def setAlignCenters(self, v: bool):
        if self.count() > 0:
            for widget in self:
                widget.setAlignCenters(v)

    def alignCentersOn(self):
        if self.count() > 0:
            for widget in self:
                widget.setAlignCentersOn()

    def alignCentersOff(self):
        if self.count() > 0:
            for widget in self:
                widget.setAlignCentersOff()

    def getAlignCenters(self):
        return self._widgets[0].getAlignCenters()

    # ROI methods

    # < Revision 20/02/2025
    # add canDisplayROI method
    def canDisplayROI(self):
        r = False
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, IconBarMultiSliceGridViewWidget):
                    if widget.hasVolume():
                        r = True
                        break
                elif isinstance(widget, IconBarSynchronisedGridViewWidget):
                    if widget.hasVolume():
                        r = True
                        break
        return r
    # Revision 20/02/2025 >

    def getROICollection(self):
        # noinspection PyInconsistentReturns
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getROICollection()
                    else: return None
        return None

    def getROIDraw(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getDrawInstance()
                    else: return None
        return None

    def getCurrentSliceIndex(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getSliceIndex()
                    else: return None
        return None

    def getSelectedSliceIndex(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getSelectedViewWidget()
                    if sliceview is not None: return sliceview.getSliceIndex()
                    else: return None
        return None

    def getCurrentOrientation(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getOrientation()
                    else: return None
        return None

    def updateROIDisplay(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.updateROIDisplay(signal=True)

    def updateROIAttributes(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.updateROIAttributes(signal=True)

    def updateROIName(self, old, name):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    widget().updateROIName(old, name)

    def setUndoOn(self):
        draw = self.getROIDraw()
        if draw is not None: draw.setUndoOn()

    def setUndoOff(self):
        draw = self.getROIDraw()
        if draw is not None: draw.setUndoOff()

    def clearUndo(self):
        draw = self.getROIDraw()
        if draw is not None: draw.clearLIFO()

    def setROIVisibility(self, v):
        if isinstance(v, bool):
            if self.count() > 0:
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None: sliceview.setROIVisibility(v, signal=True)
        else: raise TypeError('parameter type {} is not bool.'.format(v))

    def setActiveROI(self, roiname):
        if isinstance(roiname, str):
            if self.count() > 0:
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None:
                            if sliceview.hasVolume():
                                sliceview.setActiveROI(roiname, signal=True)
        else: raise TypeError('parameter type {} is not str.'.format(type(roiname)))

    def setBrushRadiusROI(self, radius=10):
        if isinstance(radius, int):
            if self.count() > 0:
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None: sliceview.setBrushRadius(radius, signal=True)
        else: raise TypeError('parameter type {} is not int.'.format(type(radius)))

    def setNoROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.setNoROIFlag(signal=True)

    def getBrushFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getBrushFlag()
        return None

    def setBrushROIFlag(self, brushtype=0):
        if isinstance(brushtype, int):
            if self.count() > 0:
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None:
                            # < Revision 20/03/2025
                            # fix order, as used in TabROIToolsWidget _brushtype attribute
                            if brushtype == 0: sliceview.setSolidBrushFlag(True, signal=True)
                            elif brushtype == 1: sliceview.setThresholdBrushFlag(True, signal=True)
                            elif brushtype == 2: sliceview.setSolidBrush3Flag(True, signal=True)
                            elif brushtype == 3: sliceview.setThresholdBrush3Flag(True, signal=True)
                            else: sliceview.setSolidBrushFlag(False, signal=True)
                            # Revision 20/03/2025 >

    def setFillHolesROIFlag(self, f):
        if self.count() > 0:
            if isinstance(f, bool):
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None: sliceview.setFillHolesFlag(f, signal=True)
            else: raise TypeError('parameter type {} is not bool.'.format(type(f)))

    def getFillHolesROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getFillHolesFlag()
        return None

    def set2DBlobDilateROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobDilateFlagOn(signal=True)

    def set2DBlobErodeROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobErodeFlagOn(signal=True)

    def set2DBlobCloseROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobCloseFlagOn(signal=True)

    def set2DBlobOpenROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobOpenFlagOn(signal=True)

    def set2DBlobCopyROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobCopyFlagOn(signal=True)

    def set2DBlobCutROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobCutFlagOn(signal=True)

    def set2DBlobPasteROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobPasteFlagOn(signal=True)

    def set2DBlobRemoveROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobRemoveFlagOn(signal=True)

    def set2DBlobKeepROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobKeepFlagOn(signal=True)

    def set2DBlobThresholdROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobThresholdFlagOn(signal=True)

    def set2DFillROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DFillFlagOn(signal=True)

    def set2DRegionGrowingROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DRegionGrowingFlagOn(signal=True)

    def set2DRegionConfidenceROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DRegionConfidenceFlagOn(signal=True)

    def set2DBlobRegionGrowingROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobRegionGrowingFlagOn(signal=True)

    def set2DBlobRegionConfidenceROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobRegionConfidenceFlagOn(signal=True)

    def set3DBlobDilateROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobDilateFlagOn(signal=True)

    def set3DBlobErodeROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobErodeFlagOn(signal=True)

    def set3DBlobCloseROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobCloseFlagOn(signal=True)

    def set3DBlobOpenROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobOpenFlagOn(signal=True)

    def set3DBlobCopyROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobCopyFlagOn(signal=True)

    def set3DBlobCutROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobCutFlagOn(signal=True)

    def set3DBlobPasteROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobPasteFlagOn(signal=True)

    def set3DBlobRemoveROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobRemoveFlagOn(signal=True)

    def set3DBlobKeepROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobKeepFlagOn(signal=True)

    def set3DBlobExpandFlagOn(self, v):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobExpandFlagOn(v, signal=True)

    def set3DBlobShrinkFlagOn(self, v):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobShrinkFlagOn(v, signal=True)

    def set3DBlobThresholdROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobThresholdFlagOn(signal=True)

    def set3DFillROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DFillFlagOn(signal=True)

    def set3DRegionGrowingROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DRegionGrowingFlagOn(signal=True)

    def set3DRegionConfidenceROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DRegionConfidenceFlagOn(signal=True)

    def set3DBlobRegionGrowingROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobRegionGrowingFlagOn(signal=True)

    def set3DBlobRegionConfidenceROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobRegionConfidenceFlagOn(signal=True)

    def setActiveContourROIFlag(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.setActiveContourFlagOn(signal=True)

    # Mesh/Tools methods

    def getVolumeView(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarOrthogonalSliceVolumeViewWidget,
                                       IconBarOrthogonalSliceTrajectoryViewWidget)):
                    return widget().getFirstVolumeViewWidget()
        return None

    def getFirstSliceView(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, IconBarWidget):
                    return widget().getFirstSliceViewWidget()
        return None

    def getOrthogonalSliceTrajectoryViewWidget(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, IconBarOrthogonalSliceTrajectoryViewWidget):
                    return widget()
        return None

    def getMultiSliceGridViewWidget(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, IconBarMultiSliceGridViewWidget):
                    return widget()
        return None

    def getSynchronisedGridViewWidget(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, IconBarSynchronisedGridViewWidget):
                    return widget()
        return None

    # < Revision 15/10/2024
    # add getProjectionViewWidget method
    def getProjectionViewWidget(self):
        if self.count() > 0:
            from Sisyphe.widgets.projectionViewWidget import IconBarMultiProjectionViewWidget
            for widget in self:
                if isinstance(widget, IconBarMultiProjectionViewWidget):
                    return widget()
        return None
    # Revision 15/10/2024 >

    # < Revision 11/12/2024
    # add getMultiComponentViewWidget method
    def getMultiComponentViewWidget(self):
        if self.count() > 0:
            from Sisyphe.widgets.multiComponentViewWidget import IconBarMultiComponentViewWidget
            for widget in self:
                if isinstance(widget, IconBarMultiComponentViewWidget):
                    return widget()
        return None
    # Revision 11/12/2024 >

    def getMeshCollection(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarOrthogonalSliceVolumeViewWidget,
                                       IconBarOrthogonalSliceTrajectoryViewWidget)):
                    view = widget().getFirstVolumeViewWidget()
                    if view is not None: return view.getMeshCollection()
        return None

    def getToolCollection(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarOrthogonalSliceVolumeViewWidget,
                                       IconBarOrthogonalSliceTrajectoryViewWidget)):
                    view = widget().getFirstVolumeViewWidget()
                    if view is not None: return view.getToolCollection()
        return None

    def getTractCollection(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarOrthogonalSliceVolumeViewWidget,
                                       IconBarOrthogonalSliceTrajectoryViewWidget)):
                    view = widget().getFirstVolumeViewWidget()
                    if view is not None: return view.getTractCollection()
        return None

    def updateRender(self):
        if self.count() > 0:
            for widget in self:
                widget.updateRender()
