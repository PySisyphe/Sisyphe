"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os.path import join
from os.path import dirname
from os.path import abspath

from platform import system

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
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication


from Sisyphe.core.sisypheVolume import SisypheVolume
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
from Sisyphe.widgets.basicWidgets import RoundedButton
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.LUTWidgets import TransferWidget

"""
    Class hierarchy
    
        QWidget -> IconBarWidget -> IconBarOrthogonalSliceViewWidget
                                 -> IconBarOrthogonalRegistrationViewWidget -> IconBarOrthogonalRegistrationViewWidget2
                                 -> IconBarOrthogonalReorientViewWidget
                                 -> IconBarOrthogonalSliceVolumeViewWidget
                                 -> IconBarOrthogonalTrajectoryViewWidget
                                 -> IconBarMultiSliceGridViewWidget -> IconBarSynchronisedGridViewWidget
                                                                    -> IconBarViewWidgetCollection
        QObject -> IconBarViewWidgetCollection
                                                                    
    Description
    
        Adds iconbar support to MultiViewWidget derived classes.
"""


class IconBarWidget(QWidget):
    """
        IconBarWidget class

        Description

            Base class that adds icon bar support to image display widgets (derived from MultiViewWidget)

        Inheritance

            QWidget -> IconBarWidget

        Private Attributes

            _widget             MultiViewWidget, display widget
            _bar                QFrame, icon bar
            _transfer           TransferWidget, widget for transfer function settings
            _menulut            QWidgetAction
            _ax                 QIcon, axial icon
            _cor                QIcon, coronal icon
            _sag                QIcon, sagittal icon
            _icons              Dict of QPushButton, iconbar buttons
            _visibilityflags    Dict of bool, buttons visibility
            _timerid            int, QTimer identifier

        Custom Qt Signals

            NameChanged.emit()          Emitted when widget name is changed

        Public methods

            MultiViewWidget = __call__()            return encapsulated MultiViewWidget (_widget private attribute)
            timerEnabled()
            timerDisabled()
            updateRender()                          to update volume display
            str = getName()
            setName(str)
            setVolume(SisypheVolume)
            SisypheVolume = getVolume()
            addOverlay(SisypheVolume)
            bool = hasVolume()
            int = getOverlayCount()
            bool = hasOverlay()
            int = getOverlayIndex(SisypheVolume)
            removeOverlay(SisypheVolume)
            removeAllOverlays()
            SisypheVolume = getOverlayFromIndex(int)
            setViewWidget(MultiViewWidget)
            MultiViewWidget = getViewWidget()
            setIconBarVisibility(bool)
            iconBarVisibilityOn()
            iconBarVisibilityOff()
            bool = getIconBarVisibility()
            setPinButtonAvailability(bool)
            setExpandButtonAvailability(bool)
            setGridButtonAvailability(bool)
            setOrientButtonAvailability(bool)
            setSliceButtonsAvailability(bool)
            setShowButtonAvailability(bool)
            setZoomButtonsAvailability(bool)
            setActionButtonAvailability(bool)
            setColorbarButtonAvailability(bool)
            setLutButtonAvailability(bool)
            setToolButtonAvailability(bool)
            setCaptureButtonAvailability(bool)
            setClipboardButtonAvailability(bool)
            bool = getPinButtonAvailability()
            bool = getExpandButtonAvailability()
            bool = getGridButtonAvailability()
            bool = getOrientButtonAvailability()
            bool = getSliceButtonsAvailability()
            bool = getShowButtonAvailability()
            bool = getZoomButtonsAvailability()
            bool = getActionButtonAvailability()
            bool = getColorbarButtonAvailability()
            bool = getLutButtonAvailability(bool)
            bool = getToolButtonAvailability()
            bool = getCaptureButtonAvailability()
            bool = getClipboardButtonAvailability()
            ToolBarThumbnail = getThumbnail()
            setThumbnail(ToolBarThumbnail)
            bool = hasThumbnail()
            timerEvent(QEvent)                      override QWidget

            inherited QWidget methods
    """

    _BTSIZE = 40    # button size 48

    # Custom Qt signals

    NameChanged = pyqtSignal()

    # Class methods

    @classmethod
    def _getDefaultIconDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'baricons')

    @classmethod
    def _createButton(cls, icon0, icon1='', checkable=False, autorepeat=False):
        button = RoundedButton()
        button.setSize(cls._BTSIZE)
        button.setBorderWidth(5)
        button.setBorderRadius(10)
        button.setBorderColorToBlack()
        button.setBackgroundColorToBlack()
        button.setCheckedBorderColorToWhite()
        button.setCheckedBackgroundColorToWhite()
        button.setNormalIcon(join(cls._getDefaultIconDirectory(), icon0))
        if icon1 != '': button.setCheckedIcon(join(cls._getDefaultIconDirectory(), icon1))
        button.setCheckable(checkable)
        button.setAutoRepeat(autorepeat)
        return button

    # Special methods

    def __init__(self, parent=None):
        super().__init__(parent)

        self._widget = None
        self._menulut = None
        self._transfer = None
        self._thumbnail = None
        self._timerid = None

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
        self._visibilityflags['tools'] = True
        self._visibilityflags['colorbar'] = True
        self._visibilityflags['ruler'] = True
        self._visibilityflags['capture'] = True
        self._visibilityflags['clipboard'] = True

        self._icons['screen'].setToolTip('Switch to full-screen view.')
        self._icons['expand'].setToolTip('Expand selected view.')
        self._icons['zoomin'].setToolTip('Zoom in.')
        self._icons['zoomout'].setToolTip('Zoom out.')
        self._icons['zoom1'].setToolTip('Default zoom.')
        self._icons['actions'].setToolTip('Mouse actions management.')
        self._icons['show'].setToolTip('Set visibility options.')
        self._icons['info'].setToolTip('Set information visibility options.')
        self._icons['colorbar'].setToolTip('Set color bar position.')
        self._icons['ruler'].setToolTip('Set ruler position.')
        self._icons['tools'].setToolTip('Add tools.')
        self._icons['capture'].setToolTip('Save capture to disk.')
        self._icons['clipboard'].setToolTip('Copy capture to clipboard.')

        submenu = QMenu()
        submenu.addAction('Distance')
        submenu.addAction('Orthogonal distances')
        submenu.addAction('Angle')
        submenu.addSeparator()
        submenu.addAction('Remove all')
        submenu.triggered.connect(self._onMenuTools)
        self._icons['tools'].setMenu(submenu)

        self._bar = QFrame(self)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        pal = self.palette()
        pal.setColor(QPalette.Background, Qt.black)
        self.setAutoFillBackground(True)
        self.setPalette(pal)
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
        layout.addWidget(self._icons['colorbar'])
        layout.addWidget(self._icons['ruler'])
        layout.addWidget(self._icons['tools'])
        layout.addWidget(self._icons['capture'])
        layout.addWidget(self._icons['clipboard'])
        layout.addStretch()
        self._bar.setLayout(layout)

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

    def _getBaseParent(self):
        w = None
        w2 = self.parent()
        while w2 is not None:
            print(type(w2))
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
                else: QMessageBox.warning(self, action.text(), 'Select a view before adding a tool.')

    def _onMenuSaveCapture(self, action):
        w = self.getViewWidget()
        if w is not None:
            s = action.text().split()
            if s[0] == 'Save':
                if s[1] == 'grid':
                    w.saveCapture()
                elif s[1] == 'selected':
                    w2 = w.getSelectedViewWidget()
                    if w2 is not None: w2.saveCapture()
                    else: QMessageBox.warning(self, 'Save selected view capture', 'Select a view before capturing.')
                elif s[1] == 'captures':
                    w.saveSeriesCaptures()
                elif s[1] == 'single':
                    w.saveSeriesCapture()
            elif s[0] == 'Send':
                if s[1] == 'selected':
                    w2 = w.getSelectedViewWidget()
                    if w2 is not None:
                        if self.hasThumbnail():
                            mainwindow = self.getThumbnail().getMainWindow()
                            if mainwindow is not None:
                                cap = w2.getPixmapCapture()
                                mainwindow.getScreenshots().paste(cap)
                    else: QMessageBox.warning(self, 'Send selected view capture', 'Select a view before capturing.')
                elif s[1] == 'captures':
                    if self.hasThumbnail():
                        mainwindow = self.getThumbnail().getMainWindow()
                        if mainwindow is not None:
                            caps = self().getFirstVolumeViewWidget().getSeriesPixmapCaptures()
                            for cap in caps:
                                mainwindow.getScreenshots().paste(cap)

    def _onMenuCopyCapture(self, action):
        s = str(action.text())[-25:-21]
        w = self.getViewWidget()
        if w is not None:
            if s == 'view':
                w2 = w.getSelectedViewWidget()
                if w2 is not None:
                    w2.copyToClipboard()
                else: QMessageBox.warning(self, 'Copy selected view capture', 'Select a view before capturing.')
            elif s == 'grid': w.copyToClipboard()

    def _onMenuOrientation(self, v):
        if v == 0: self._icons['orient'].setIcon(self._ax)
        elif v == 1: self._icons['orient'].setIcon(self._cor)
        else: self._icons['orient'].setIcon(self._sag)

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

    def _connectExpandAction(self):
        for i in range(0, self._widget.getRows()):
            for j in range(0, self._widget.getCols()):
                action = self._widget[i, j].getAction()['expand']
                if action is not None:
                    action.triggered.connect(self._icons['expand'].setChecked)

    def _showViewWidget(self):
        self._bar.show()
        self._widget.show()

    def _hideViewWidget(self):
        self._bar.hide()
        self._widget.hide()

    # Public method

    def timerEnabled(self):
        if self._widget.hasVolume():
            if self._timerid is None:
                self._timerid = self.startTimer(0)

    def timerDisabled(self):
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
            self.NameChanged.emit()
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    def setVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            if self._widget is not None:
                self._widget.setVolume(vol)
                self._showViewWidget()

    def getVolume(self):
        return self._widget.getVolume()

    def hasVolume(self):
        return self._widget.hasVolume()

    def removeVolume(self):
        if self._widget is not None:
            self._widget.removeVolume()
            self._hideViewWidget()

    def addOverlay(self, volume):
        if self._widget is not None:
            if self._widget.hasVolume():
                self._widget.addOverlay(volume)

    def getOverlayCount(self):
        if self._widget is not None:
            if self._widget.hasVolume():
                return self._widget.getOverlayCount()

    def hasOverlay(self):
        if self._widget is not None:
            if self._widget.hasVolume():
                return self._widget.hasOverlay()

    def getOverlayIndex(self, o):
        if self._widget is not None:
            if self._widget.hasVolume():
                return self._widget.getOverlayIndex(o)

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
            if self._widget.hasVolume():
                return self._widget.getOverlayFromIndex(index)

    def setViewWidget(self, widget):
        if isinstance(widget, MultiViewWidget):
            self._widget = widget
            self._widget.setParent(self)
            self._layout.addWidget(widget)
            grid = isinstance(widget, GridViewWidget)
            orthoslc = isinstance(widget, OrthogonalSliceViewWidget)
            orthovol = isinstance(widget, OrthogonalSliceVolumeViewWidget)
            view1 = widget.getFirstSliceViewWidget()
            view2 = widget.getFirstVolumeViewWidget()
            """
            
                Common to all widgets
                
            """
            self._icons['expand'].clicked.connect(self._onExpand)
            self._connectExpandAction()
            # self._icons['screen'].clicked.connect(self.getViewWidget().toggleDisplay)
            self._icons['screen'].clicked.connect(lambda _: self._onFullScreen())
            self._icons['zoomin'].clicked.connect(view1.zoomIn)
            self._icons['zoomout'].clicked.connect(view1.zoomOut)
            self._icons['zoom1'].clicked.connect(view1.zoomDefault)
            self._icons['actions'].setMenu(view1.getPopupActions())
            self._icons['info'].setMenu(view1.getPopupInformation())
            self._icons['colorbar'].setMenu(view1.getPopupColorbarPosition())
            self._icons['ruler'].setMenu(view1.getPopupRulerPosition())
            submenu = QMenu()
            submenu.addAction('Copy grid capture to clipboard')
            submenu.addAction('Copy selected view capture to clipboard')
            submenu.triggered.connect(self._onMenuCopyCapture)
            self._icons['clipboard'].setMenu(submenu)
            """
            
                Grid widget actions
            
            """
            if grid:
                self._icons['grid'] = self._createButton('wgrid.png', 'grid.png', checkable=False, autorepeat=False)
                self._icons['orient'] = self._createButton('wdimz.png', 'dimz.png', checkable=False, autorepeat=False)
                self._icons['sliceminus'] = self._createButton('wminus.png', 'minus.png', checkable=False, autorepeat=True)
                self._icons['sliceplus'] = self._createButton('wplus.png', 'plus.png', checkable=False, autorepeat=True)
                self._icons['orient'].setMenu(view1.getPopupOrientation())
                menu = view1.getPopupOrientation()
                menu.actions()[0].triggered.connect(lambda dummy, v=0: self._onMenuOrientation(v))
                menu.actions()[1].triggered.connect(lambda dummy, v=1: self._onMenuOrientation(v))
                menu.actions()[2].triggered.connect(lambda dummy, v=2: self._onMenuOrientation(v))
                self._icons['sliceminus'].clicked.connect(view1.slicePlus)
                self._icons['sliceplus'].clicked.connect(view1.sliceMinus)
                self._visibilityflags['grid'] = True
                self._visibilityflags['orient'] = True
                self._visibilityflags['sliceminus'] = True
                self._visibilityflags['sliceplus'] = True
                layout = self._bar.layout()
                layout.insertWidget(3, self._icons['sliceplus'])
                layout.insertWidget(3, self._icons['sliceminus'])
                layout.insertWidget(3, self._icons['orient'])
                layout.insertWidget(3, self._icons['grid'])
                self._icons['grid'].setToolTip('Set row and column counts.')
                self._icons['orient'].setToolTip('Set view orientation (axial, coronal, sagittal).')
                self._icons['sliceminus'].setToolTip('Go to previous slice.')
                self._icons['sliceplus'].setToolTip('Go to next slice.')
                self._icons['show'].setMenu(view1.getPopupVisibility())
                self._icons['grid'].setMenu(widget.getPopupMenuNumberOfVisibleViews())
                widget.popupMenuROIDisabled()
            if grid or orthoslc:
                self._icons['show'].setMenu(view1.getPopupVisibility())
                submenu = QMenu()
                submenu.addAction('Save grid capture...')
                submenu.addAction('Save selected view capture...')
                submenu.addAction('Save captures from slice series...')
                submenu.addSeparator()
                submenu.addAction('Send selected view capture to screenshots preview')
                submenu.triggered.connect(self._onMenuSaveCapture)
                self._icons['capture'].setMenu(submenu)
            """
                
                OrthogonalSliceVolume widget actions
                
            """
            if orthovol:

                self._icons['campos'] = self._createButton('wrotate.png', 'rotate.png', checkable=False,
                                                           autorepeat=False)
                self._icons['texture'] = self._createButton('whead.png', 'head.png', checkable=False, autorepeat=False)
                self._icons['transfer'] = self._createButton('wtransfer.png', 'trasnfer.png', checkable=False,
                                                             autorepeat=False)
                self._icons['align'] = self._createButton('wview.png', 'view.png', checkable=False, autorepeat=False)
                self._icons['campos'].setMenu(view2.getPopupCameraPosition())
                self._icons['texture'].setMenu(view2.getPopupTextureActor())
                self._icons['align'].setMenu(view1.getPopupAlignment())

                self._transfer = TransferWidget(size=256)
                self._transfer.colorDialogClosed.connect(self._icons['transfer'].showMenu)

                submenu = QMenu()
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

                self._visibilityflags['campos'] = True
                self._visibilityflags['texture'] = True
                self._visibilityflags['transfer'] = True

                self._icons['campos'].setToolTip('Predefined camera positions.')
                self._icons['texture'].setToolTip('3D texture volume rendering settings.')
                self._icons['transfer'].setToolTip('Set color and alpha transfer functions.')

                submenu = QMenu()
                submenu.addAction('Save grid capture...')
                submenu.addAction('Save selected view capture...')
                submenu.addAction('Save captures from multiple camera positions...')
                submenu.addAction('Save single capture from multiple camera positions...')
                submenu.addSeparator()
                submenu.addAction('Send selected view capture to screenshots preview')
                submenu.addAction('Send captures from multiple camera positions to screenshots preview')
                submenu.triggered.connect(self._onMenuSaveCapture)
                self._icons['capture'].setMenu(submenu)

        else: raise TypeError('parameter type {} is not MultiViewWidget.'.format(type(widget)))

    def getViewWidget(self):
        return self._widget

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

    # Event loop, solves VTK mouse move event bug

    @classmethod
    def _widgetUnderCursor(cls, widget):
        p = widget.cursor().pos()
        p = widget.mapFromGlobal(p)
        return 0 <= p.x() < widget.width() and 0 <= p.y() < widget.height()

    def timerEvent(self, event):
        w = self._widget
        # Icon bar visibility management
        if not self._icons['pin'].isChecked():
            if self.getIconBarVisibility():
                if not self._bar.underMouse(): self.iconBarVisibleOff()
            else:
                p = w.cursor().pos()
                p = w.mapFromGlobal(p)
                if p.x() < self._icons['pin'].width(): self.iconBarVisibleOn()
        # Mouse move event management
        # solves VTK mouse move event bug
        if self._widgetUnderCursor(w):
            for i in range(0, w.getRows()):
                for j in range(0, w.getCols()):
                    view = w.getViewWidgetAt(i, j)
                    if self._widgetUnderCursor(view):
                        interactor = view.getWindowInteractor()
                        p = view.cursor().pos()
                        p = view.mapFromGlobal(p)
                        p.setY(view.height() - p.y() - 1)
                        interactor.SetEventInformation(p.x(), p.y())
                        interactor.MouseMoveEvent()

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
                    self._thumbnail.getWidgetFromIndex(index).display()


class IconBarOrthogonalSliceViewWidget(IconBarWidget):
    """
        IconBarOrthogonalSliceViewWidget class

        Description

            OrthogonalSliceViewWidget with icon bar.

        Inheritance

            QWidget -> IconBarWidget -> IconBarOrthogonalSliceViewWidget

        Private Attributes

        Public methods

            inherited IconBarWidget
            inherited QWidget methods
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

            OrthogonalRegistrationViewWidget with icon bar.

        Inheritance

            QWidget -> IconBarWidget -> IconBarOrthogonalRegistrationViewWidget

        Private Attributes

        Public methods

            setCrop(bool)
            bool = getCrop()
            cropOn()
            cropOff()
            setRegistrationBoxVisibility(bool)
            bool = getRegistrationBoxVisibility()
            registrationBoxOn()
            registrationBoxOff()
            getRegistrationBoxMatrixArea()
            displayEdge()
            displayNative()
            displayEdgeAndNative()

            inherited IconBarWidget
            inherited QWidget methods
    """

    # Special method

    def __init__(self, widget=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = OrthogonalRegistrationViewWidget()
        if isinstance(widget, OrthogonalRegistrationViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not OrthogonalRegistrationViewWidget.'.format(type(widget)))
        self.setShowButtonAvailability(False)
        self.setInfoButtonAvailability(False)
        self.setColorbarButtonAvailability(False)
        self.setToolButtonAvailability(False)
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

            OrthogonalRegistrationViewWidget with icon bar and rigid transformation buttons.

        Inheritance

            QWidget -> IconBarWidget -> IconBarOrthogonalRegistrationViewWidget
            -> IconBarOrthogonalRegistrationViewWidget2

        Private Attributes

        Public methods

            setMoveOverlayOn()
            setMoveOverlayOff()
            setMoveButtonsVisibility(bool)
            bool = getMoveButtonsVisibility()
            setMoveStep(float)
            float = getMoveStep()

            inherited IconBarWidget
            inherited QWidget methods

        Revision 16/04/2023, button tooltips update
    """

    # Special method

    def __init__(self, widget=None, parent=None):
        super().__init__(widget, parent)

        self._buttons = dict()
        self._step = 0.5

        # Axial buttons

        self._buttons['up0'] = self._createButton('wup.png', 'up.ong', checkable=False, autorepeat=True)
        self._buttons['down0'] = self._createButton('wdown.png', 'down.png', checkable=False, autorepeat=True)
        self._buttons['left0'] = self._createButton('wleft.png', 'left.png', checkable=False, autorepeat=True)
        self._buttons['right0'] = self._createButton('wright.png', 'right.png', checkable=False, autorepeat=True)
        self._buttons['rotc0'] = self._createButton('wrot1.png', 'rot1.png', checkable=False, autorepeat=True)
        self._buttons['rota0'] = self._createButton('wrot2.png', 'rot2.png', checkable=False, autorepeat=True)
        self._buttons['up0'].clicked.connect(lambda: self._ytranslation(self._step))
        self._buttons['down0'].clicked.connect(lambda: self._ytranslation(-self._step))
        self._buttons['left0'].clicked.connect(lambda: self._xtranslation(self._step))
        self._buttons['right0'].clicked.connect(lambda: self._xtranslation(-self._step))
        self._buttons['rotc0'].clicked.connect(lambda: self._zrotation(self._step))
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

        self._buttons['up1'] = self._createButton('wup.png', 'up.ong', checkable=False, autorepeat=True)
        self._buttons['down1'] = self._createButton('wdown.png', 'down.png', checkable=False, autorepeat=True)
        self._buttons['left1'] = self._createButton('wleft.png', 'left.png', checkable=False, autorepeat=True)
        self._buttons['right1'] = self._createButton('wright.png', 'right.png', checkable=False, autorepeat=True)
        self._buttons['rotc1'] = self._createButton('wrot1.png', 'rot1.png', checkable=False, autorepeat=True)
        self._buttons['rota1'] = self._createButton('wrot2.png', 'rot2.png', checkable=False, autorepeat=True)
        self._buttons['up1'].clicked.connect(lambda: self._ztranslation(self._step))
        self._buttons['down1'].clicked.connect(lambda: self._ztranslation(-self._step))
        self._buttons['left1'].clicked.connect(lambda: self._xtranslation(self._step))
        self._buttons['right1'].clicked.connect(lambda: self._xtranslation(-self._step))
        self._buttons['rotc1'].clicked.connect(lambda: self._yrotation(-self._step))
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

        self._buttons['up2'] = self._createButton('wup.png', 'up.ong', checkable=False, autorepeat=True)
        self._buttons['down2'] = self._createButton('wdown.png', 'down.png', checkable=False, autorepeat=True)
        self._buttons['left2'] = self._createButton('wleft.png', 'left.png', checkable=False, autorepeat=True)
        self._buttons['right2'] = self._createButton('wright.png', 'right.png', checkable=False, autorepeat=True)
        self._buttons['rotc2'] = self._createButton('wrot1.png', 'rot1.png', checkable=False, autorepeat=True)
        self._buttons['rota2'] = self._createButton('wrot2.png', 'rot2.png', checkable=False, autorepeat=True)
        self._buttons['up2'].clicked.connect(lambda: self._ztranslation(self._step))
        self._buttons['down2'].clicked.connect(lambda: self._ztranslation(-self._step))
        self._buttons['left2'].clicked.connect(lambda: self._ytranslation(self._step))
        self._buttons['right2'].clicked.connect(lambda: self._ytranslation(-self._step))
        self._buttons['rotc2'].clicked.connect(lambda: self._xrotation(self._step))
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

        for view in self.getViewWidget().getSliceViewWidgets():
            view.TranslationsChanged.connect(lambda d1, d2: self._updateTooltips())
            view.RotationsChanged.connect(lambda d1, d2: self._updateTooltips())

        self._vlayout.addLayout(layout)
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
        t = list(widget.getTranslations())
        t[0] += v
        widget.setTranslations(tuple(t))
        self._buttons['left0'].setToolTip('Right translation\nX Translation {:.2f} mm'.format(t[0]))
        self._buttons['right0'].setToolTip('Left translation\nX Translation {:.2f} mm'.format(t[0]))
        self._buttons['left1'].setToolTip('Right translation\nX Translation {:.2f} mm'.format(t[0]))
        self._buttons['right1'].setToolTip('Left translation\nX Translation {:.2f} mm'.format(t[0]))

    def _ytranslation(self, v):
        widget = self().getFirstSliceViewWidget()
        t = list(widget.getTranslations())
        t[1] += v
        widget.setTranslations(tuple(t))
        self._buttons['up0'].setToolTip('Forward translation\nY Translation {:.2f} mm'.format(t[1]))
        self._buttons['down0'].setToolTip('Backward translation\nY Translation {:.2f} mm'.format(t[1]))
        self._buttons['left2'].setToolTip('Forward translation\nY Translation {:.2f} mm'.format(t[1]))
        self._buttons['right2'].setToolTip('Backward translation\nY Translation {:.2f} mm'.format(t[1]))

    def _ztranslation(self, v):
        widget = self().getFirstSliceViewWidget()
        t = list(widget.getTranslations())
        t[2] += v
        widget.setTranslations(tuple(t))
        self._buttons['up1'].setToolTip('Cranial translation\nZ Translation {:.2f} mm'.format(t[2]))
        self._buttons['down1'].setToolTip('Caudal translation\nZ Translation {:.2f} mm'.format(t[2]))
        self._buttons['up2'].setToolTip('Cranial translation\nZ Translation {:.2f} mm'.format(t[2]))
        self._buttons['down2'].setToolTip('Caudal translation\nZ Translation {:.2f} mm'.format(t[2]))

    def _xrotation(self, v):
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations())
        r[0] += v
        widget.setRotations(tuple(r))
        self._buttons['rotc2'].setToolTip('Clockwise X rotation\nX Rotation {:.2f}°'.format(r[0]))
        self._buttons['rota2'].setToolTip('Counter-clockwise X Rotation\nX Rotation {:.2f}°'.format(r[0]))

    def _yrotation(self, v):
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations())
        r[1] += v
        widget.setRotations(tuple(r))
        self._buttons['rotc1'].setToolTip('Clockwise Y rotation\nY Rotation {:.2f}°'.format(r[1]))
        self._buttons['rota1'].setToolTip('Counter-clockwise Y Rotation\nY Rotation {:.2f}°'.format(r[1]))

    def _zrotation(self, v):
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations())
        r[2] += v
        widget.setRotations(tuple(r))
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

            OrthogonalReorientViewWidget with icon bar.

        Inheritance

            QWidget -> IconBarWidget -> IconBarOrthogonalReorientViewWidget

        Private Attributes

        Public methods

            inherited IconBarWidget
            inherited QWidget methods
    """

    def __init__(self, widget=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = OrthogonalReorientViewWidget()
        if isinstance(widget, OrthogonalReorientViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not OrthogonalReorientViewWidget.'.format(type(widget)))
        self._hideViewWidget()


class IconBarOrthogonalSliceVolumeViewWidget(IconBarWidget):
    """
        IconBarOrthogonalSliceVolumeViewWidget class

        Description

            OrthogonalSliceVolumeViewWidget with icon bar.

        Inheritance

            QWidget -> IconBarWidget -> IconBarOrthogonalSliceVolumeViewWidget

        Private Attributes

        Public methods

            setCameraPositionButtonAvailability(bool)
            setTextureSettingsButtonAvailability(bool)
            bool = getCameraPositionButtonAvailability()
            bool = getTextureSettingsButtonAvailability()

            inherited IconBarWidget
            inherited QWidget methods
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
        IconBarOrthogonalSliceTrajectoryViewWidget

        Description

            OrthogonalSliceTrajectoryViewWidget with icon bar.

        Inheritance

            QWidget -> IconBarWidget -> IconBarOrthogonalSliceTrajectoryViewWidget

        Private Attributes

        Public methods

            setSlabThicknessButtonAvailability(bool)
            bool = getSlabThicknessButtonAvailability()

            inherited IconBarWidget
            inherited QWidget methods

        Revisions:

            02/10/2023  add slab thickness management
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
        self._visibilityflags['thick'] = True

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
        action['min'].triggered.connect(lambda _: self._slabTypeChanged(0))
        action['max'].triggered.connect(lambda _: self._slabTypeChanged(1))
        action['mean'].triggered.connect(lambda _: self._slabTypeChanged(2))
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
        menu.aboutToHide.connect(self._slabThicknessChanged)
        self._icons['thick'].setMenu(menu)

        layout = self._bar.layout()
        layout.insertWidget(7, self._icons['thick'])

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

    def setSlabThicknessButtonAvailability(self, v):
        if isinstance(v, bool):
            self._visibilityflags['thick'] = v
            if not v: self._icons['thick'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getSlabThicknessButtonAvailability(self):
        return self._visibilityflags['thick']


class IconBarMultiSliceGridViewWidget(IconBarWidget):
    """
        IconBarMultiSliceGridViewWidget

        Description

            MultiSliceGridViewWidget with icon bar.
            Displays several adjacent slices in 3 x 3 grid with overlays and ROI support.

        Inheritance

            QWidget -> IconBarWidget -> IconBarMultiSliceGridViewWidget

        Private Attributes

        Public methods

            addOverlay(SisypheVolume)

            inherited IconBarWidget
            inherited QWidget methods
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
        IconBarSynchronisedGridViewWidget

        Description

            SynchronisedGridViewWidget with icon bar.
            Displays same slices of multiple volumes in 3 x 3 grid.

        Inheritance

            QWidget -> IconBarWidget -> IconBarSynchronisedGridViewWidget

        Private Attributes

        Public methods

            inherited IconBarWidget
            inherited QWidget methods
    """

    def __init__(self, widget=None, rois=None, draw=None, parent=None):
        super().__init__(parent)
        if widget is None: widget = SynchronisedGridViewWidget(rois=rois, draw=draw)
        if isinstance(widget, SynchronisedGridViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not SynchronisedGridViewWidget.'.format(type(widget)))
        self._hideViewWidget()


class IconBarSliceViewWidget(IconBarWidget):
    """
        IconBarSliceViewWidget

        Description

            SliceViewWidget with icon bar.

        Inheritance

            QWidget -> IconBarWidget -> IconBarSliceViewWidget

        Private Attributes

        Public methods

            inherited IconBarWidget
            inherited QWidget methods
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
            self._layout.addWidget(widget)
            widget.setSelectable(False)
            self.setExpandButtonAvailability(False)
            self._icons['orient'] = self._createButton('wdimz.png', 'dimz.png', checkable=False, autorepeat=False)
            self._icons['sliceminus'] = self._createButton('wminus.png', 'minus.png', checkable=False, autorepeat=True)
            self._icons['sliceplus'] = self._createButton('wplus.png', 'plus.png', checkable=False, autorepeat=True)
            self._icons['orient'].setMenu(widget.getPopupOrientation())
            self._icons['sliceminus'].clicked.connect(widget.sliceMinus)
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
            self._icons['zoomin'].clicked.connect(widget.zoomIn)
            self._icons['zoomout'].clicked.connect(widget.zoomOut)
            self._icons['zoom1'].clicked.connect(widget.zoomDefault)
            self._icons['capture'].clicked.connect(widget.saveCapture)
            self._icons['clipboard'].clicked.connect(widget.copyToClipboard)
            widget.getAction()['axial'].triggered.connect(lambda: self._icons['orient'].setIcon(self._ax))
            widget.getAction()['coronal'].triggered.connect(lambda: self._icons['orient'].setIcon(self._cor))
            widget.getAction()['sagittal'].triggered.connect(lambda: self._icons['orient'].setIcon(self._sag))
        else: raise TypeError('parameter type {} is not SliceROIViewWidget.'.format(type(widget)))

    # Public methods

    def setVolume(self, vol):
        super().setVolume(vol)
        self.timerEnabled()

    def removeVolume(self):
        super().removeVolume()
        self.timerDisabled()

    def timerEvent(self, event):
        w = self._widget
        # Icon bar visibility management
        if not self._icons['pin'].isChecked():
            if self.getIconBarVisibility():
                if not self._bar.underMouse(): self.iconBarVisibleOff()
            else:
                p = w.cursor().pos()
                p = w.mapFromGlobal(p)
                if p.x() < self._icons['pin'].width(): self.iconBarVisibleOn()
        # Mouse move event management
        # solves VTK mouse move event bug
        interactor = w.getWindowInteractor()
        p = w.cursor().pos()
        p = w.mapFromGlobal(p)
        p.setY(w.height() - p.y() - 1)
        interactor.SetEventInformation(p.x(), p.y())
        interactor.MouseMoveEvent()


class IconBarViewWidgetCollection(QObject):
    """
        IconBarViewWidgetCollection

        Description

            Indexed dict-like container of IconBarWidgets.

        Inheritance

            object -> IconBarViewWidgetCollection

        Private attributes

            _widgets    list of IconBarWidget
            _index      index for Iterator

        Public methods

            __getitem__(int)
            __setitem__(IconBarWidget)
            __delitem__(int)
            __len__
            __contains__(str or IconBarWidget)
            __iter__
            __next__
            clear()
            bool = isEmpty()
            int = count()
            remove(int, str or IconBarWidget)
            list = keys()
            int = index(str or IconBarWidget)
            reverse()
            append(IconBarWidget)
            insert(str or int, IconBarWidget)
            clear()
            sort()
            IconBarViewWidgetCollection = copy()
            list = copyToList()
            updateKeys()
            setVolume(SisypheVolume, DIALOGWait)
            SisypheVolume = getVolume()
            removeVolume()
            addOverlay(SisypheVolume, DIALOGWait)
            removeOverlay(SisypheVolume)
            SisypheROICollection = getROICollection()
            SisypheROIDraw = getROIDraw()
            int = getCurrentSliceIndex()
            int = getSelectedSliceIndex()
            int = getCurrentOrientation()
            updateROIDisplay()
            updateROIAttributes()
            setUndoOn()
            setUndoOff()
            setROIVisibility(bool)
            setActiveROI(str)
            setBrushRadiusROI(int)
            setBrushROIFlag(int)
            setFillHolesROIFlag(bool)
            bool = getFillHolesROIFlag()
            set2DBlobDilateROIFlag()
            set2DBlobErodeROIFlag()
            set2DBlobCloseROIFlag()
            set2DBlobOpenROIFlag()
            set2DBlobCopyROIFlag()
            set2DBlobCutROIFlag()
            set2DBlobPasteROIFlag()
            set2DBlobRemoveROIFlag()
            set2DBlobKeepROIFlag()
            set3DBlobDilateROIFlag()
            set3DBlobErodeROIFlag()
            set3DBlobCloseROIFlag()
            set3DBlobOpenROIFlag()
            set3DBlobCopyROIFlag()
            set3DBlobCutROIFlag()
            set3DBlobPasteROIFlag()
            set3DBlobRemoveROIFlag()
            set3DBlobKeepROIFlag()
            OrthogonalSliceTrajectoryViewWidget = getOrthogonalSliceTrajectoryViewWidget()
            MultiSliceGridViewWidget = getMultiSliceGridViewWidget()
            SynchronisedGridViewWidget = getSynchronisedGridViewWidget()
            updateRender()

        Revisions:

            03/08/2023  Add setNoROIFlag() and getBrushFlag() methods
    """

    __slots__ = ['_widgets', '_index']

    # Class method

    def _KeyToIndex(self, key):
        keys = [k[0] for k in self._widgets]
        return keys.index(key)

    # Special methods

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
            if 0 <= index < len(self._widgets):
                return self._widgets[index][1]
            else: IndexError('parameter value {} is out of range.'.format(index))
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
                    wait.setProgressMinimum(0)
                    wait.setProgressMaximum(self.count())
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
        if self.count() > 0:
            return self[0].getVolume()

    def removeVolume(self):
        if self.count() > 0:
            for widget in self:
                widget.removeVolume()

    # Overlay methods

    def addOverlay(self, vol, wait=None):
        if isinstance(vol, SisypheVolume):
            if self.count() > 0:
                if wait is not None:
                    wait.setProgressMinimum(0)
                    wait.setProgressMaximum(self.count())
                    wait.progressVisibilityOn()
                for widget in self:
                    if wait is not None:
                        info = '{} display as overlay in {} view...'.format(vol.getBasename(), widget.getName())
                        wait.setInformationText(info)
                        wait.incCurrentProgressValue()
                    widget.addOverlay(vol)
                    QApplication.processEvents()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def removeOverlay(self, vol):
        if isinstance(vol, SisypheVolume):
            if self.count() > 0:
                for widget in self:
                    widget.removeOverlay(vol)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    # ROI methods

    def getROICollection(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getROICollection()
                    else: return None

    def getROIDraw(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getDrawInstance()
                    else: return None

    def getCurrentSliceIndex(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getSliceIndex()
                    else: return None

    def getSelectedSliceIndex(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getSelectedViewWidget()
                    if sliceview is not None: return sliceview.getSliceIndex()
                    else: return None

    def getCurrentOrientation(self):
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getOrientation()
                    else: return None

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
                        if sliceview is not None: sliceview.setActiveROI(roiname, signal=True)
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

    def setBrushROIFlag(self, brushtype=0):
        if isinstance(brushtype, int):
            if self.count() > 0:
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None:
                            if brushtype == 0: sliceview.setSolidBrushFlag(True, signal=True)
                            elif brushtype == 1: sliceview.setSolidBrush3Flag(True, signal=True)
                            elif brushtype == 2: sliceview.setThresholdBrushFlag(True, signal=True)
                            elif brushtype == 3: sliceview.setThresholdBrush3Flag(True, signal=True)
                            else: sliceview.setSolidBrushFlag(False, signal=True)

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

    def updateRender(self):
        if self.count() > 0:
            for widget in self:
                widget.updateRender()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit

    test = 2
    app = QApplication(argv)
    # IconBarOrthogonalSliceViewWidget
    if test == 0:
        print('Test IconBarOrthogonalSliceViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/anat.nii'
        file2 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/overlay.nii'
        img1 = SisypheVolume()
        img2 = SisypheVolume()
        img1.loadFromNIFTI(file1)
        img2.loadFromNIFTI(file2)
        img2.display.getLUT().setLutToRainbow()
        img2.display.getLUT().setDisplayBelowRangeColorOn()
        main = IconBarOrthogonalSliceViewWidget()
        main().setVolume(img1)
        main().addOverlay(img2)
        main().getFirstSliceViewWidget().setOverlayOpacity(0, 0.2)
    # IconBarOrthogonalRegistrationViewWidget
    elif test == 1:
        print('Test IconBarOrthogonalSliceViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/TESTS/IMAGES/NIFTI/anat.nii'
        file2 = '/Users/Jean-Albert/PycharmProjects/untitled/TESTS/IMAGES/NIFTI/overlay.nii'
        img1 = SisypheVolume()
        img2 = SisypheVolume()
        img1.loadFromNIFTI(file1)
        img2.loadFromNIFTI(file2)
        img2.display.getLUT().setLutToRainbow()
        img2.display.getLUT().setDisplayBelowRangeColorOn()
        main = IconBarOrthogonalRegistrationViewWidget2()
        main().setVolume(img1)
        main().addOverlay(img2)
        main().getFirstSliceViewWidget().setOverlayOpacity(0, 0.2)
    # IconBarOrthogonalReorientViewWidget
    elif test == 2:
        print('Test IconBarOrthogonalReorientViewWidget')
        file = '/Users/Jean-Albert/PycharmProjects/untitled/TESTS/IMAGES/NIFTI/3D.nii'
        main = IconBarOrthogonalReorientViewWidget()
        img = SisypheVolume()
        img.loadFromNIFTI(file)
        main.setVolume(img)
    # IconBarOrthogonalSliceVolumeViewWidget
    elif test == 3:
        pass
    # IconBarOrthogonalSliceTrajectoryViewWidget
    elif test == 4:
        pass
    # IconBarMultiSliceGridViewWidget
    elif test == 5:
        print('Test IconBarMultiSliceGridViewWidget')
        file1 = '/Users/Jean-Albert/PycharmProjects/untitled/Sisyphe/templates/mni_icbm152_sym_9c_brain.xvol'
        file2 = '/Users/Jean-Albert/PycharmProjects/untitled/Sisyphe/templates/mni_icbm152_sym_9c_gm.xvol'
        img1 = SisypheVolume()
        img2 = SisypheVolume()
        img1.load(file1)
        img2.load(file2)
        img2.display.getLUT().setLutToRainbow()
        img2.display.getLUT().setDisplayBelowRangeColorOn()
        main = IconBarMultiSliceGridViewWidget()
        main().setVolume(img1)
        main().addOverlay(img2)
        main().setOverlayOpacity(0, 0.2)
    # IconBarSynchronisedGridViewWidget
    elif test == 6:
        pass
    # IconBarSliceViewWidget
    elif test == 7:
        print('Test IconBarSliceViewWidget')
        file = '/Users/Jean-Albert/PycharmProjects/untitled/TESTS/3D.xvol'
        img = SisypheVolume()
        img.load(file)
        main = IconBarSliceViewWidget()
        main.setVolume(img)
    main.show()
    main.activateWindow()
    exit(app.exec_())

