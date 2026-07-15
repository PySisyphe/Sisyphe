"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Any
from typing import Optional

from sys import platform
from os.path import join
from os.path import dirname
from os.path import abspath

import cython

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

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from Sisyphe.gui.dialogWait import DialogWait
    from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
    from Sisyphe.widgets.sliceViewWidgets import SliceViewWidget
    from Sisyphe.widgets.multiComponentViewWidget import MultiComponentViewWidget
    from Sisyphe.widgets.projectionViewWidget import MultiProjectionViewWidget
    from Sisyphe.widgets.multiViewWidgets import SliceTrajectoryViewWidget
    from Sisyphe.core.sisypheROI import SisypheROIDraw
    from Sisyphe.core.sisypheROI import SisypheROICollection
    from Sisyphe.core.sisypheMesh import SisypheMeshCollection
    from Sisyphe.core.sisypheTracts import SisypheTractCollection
    from Sisyphe.core.sisypheTools import ToolWidgetCollection
    # < Revision 26/02/2026
    from Sisyphe.processing.segmentation import SegmentAnything
    # Revision 26/02/2026 >
    from PyQt5.QtGui import QDragEnterEvent
    from PyQt5.QtGui import QDropEvent
    from PyQt5.QtCore import QTimerEvent

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

Adds icon bar support to view widget classes.
"""


class IconBarWidget(QWidget):
    """
    IconBarWidget class

    Description
    ~~~~~~~~~~~

    Base class that encapsulates a primary view widget (typically a MultiViewWidget subclass) and enhances it with a
    collapsible, vertical icon bar.

    The main features are as follows:

    - Encapsulated view widget access: the python __call__ syntax where he instance can be called like a function (e.g. instance_name()) returns the native encapsulated view widget. This is a fast and easy way to access all the methods of the encapsulated view widget.
    - Collapsible icon bar: a space-saving icon bar is displayed on the left. It automatically hides when the mouse is over the main view and reappears when the mouse pointer moves to the left edge. This behavior can be overridden by "pinning" the bar to keep it permanently visible.
    - Standardized Toolset: The icon bar provides quick access to a rich set of common functionalities, grouped into icons:

        - View control: fullscreen mode, expanding a single sub-view, and zoom controls (in, out, reset).
        - Display settings: menus for toggling the visibility of on-screen elements like the cursor, information text, orientation markers, color bars, and rulers.
        - Interactive tools: menus for managing mouse interaction modes, adding measurement tools (e.g. distance, angle), and configuring isolines.
        - Capture: buttons to save the current view(s) to a bitmap file or copy them directly to the system clipboard.

    - Context-sensitive menus: menus associated with icons are dynamically populated based on the state of the encapsulated view widget. For example, the "Isoline" menu lists all displayed volumes and overlays available for contouring.
    - Drag-and-Drop integration: fully supports dragging volumes from an external source (like a thumbnail bar) and dropping them onto the view. The drop behavior (e.g., replace the current volume, add as an overlay, or prompt the user) is configurable through application settings (settings.xml).
    - Customizable interface: offers an extensive API to control the visibility and availability of each button on the icon bar, allowing derived classes to tailor the user interface to their specific needs.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget

    Creation: 17/04/2022
    Last revision: 10/07/2026
    """

    _BTSIZE: int = 40    # default button size
    _VSIZE: int = 24

    # Custom Qt signals

    NameChanged: pyqtSignal = pyqtSignal()

    # Class methods

    @classmethod
    def _getDefaultIconDirectory(cls) -> str:
        """
        Get the default directory for icon bar icons.

        Returns
        -------
        str
            absolute path to the icon directory.
        """
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'baricons')

    # Special methods

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        IconBarWidget instance constructor.

        Parameters
        ----------
        parent: QWidget | None (optional)
            parent widget (default None).
        """
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
        # noinspection PyUnresolvedReferences
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyUnresolvedReferences
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
        self._isoMenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyUnresolvedReferences
        self._isoMenu.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
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
        # if platform == 'win32':
        if platform == 'win32' or platform == 'linux':
            self._bar.setObjectName('IconBar')
            self._bar.setStyleSheet('QFrame#IconBar { background-color: #000000; border-color: #000000; } '
                                    'QToolTip#IconBar { color: #000000; background-color: #FFFFE0; border: 0px; font-size: 8pt; }')
        else:
            pal = self.palette()
            # noinspection PyUnresolvedReferences
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

        # noinspection PyUnresolvedReferences
        self._icons['expand'].setShortcut(Qt.Key_Plus)
        self._icons['zoom1'].setShortcut('0')
        self._shcutp = QShortcut('p', self) # Pin shortcut
        # noinspection PyUnresolvedReferences
        self._shcutp.activated.connect(self._onPin)
        self._shcutA = QShortcut('A', self) # Axial shortcut
        self._shcutC = QShortcut('C', self) # Coronal shortcut
        self._shcutS = QShortcut('S', self) # Sagittal shortcut
        # noinspection PyUnresolvedReferences
        self._shcut1 = QShortcut(Qt.Key_1, self) # Grid 1x1 shortcut
        # noinspection PyUnresolvedReferences
        self._shcut2 = QShortcut(Qt.Key_2, self) # Grid 1x2 shortcut
        # noinspection PyUnresolvedReferences
        self._shcut3 = QShortcut(Qt.Key_3, self) # Grid 1x3 shortcut
        # noinspection PyUnresolvedReferences
        self._shcut4 = QShortcut(Qt.Key_4, self) # Grid 2x2 shortcut
        # noinspection PyUnresolvedReferences
        self._shcut6 = QShortcut(Qt.Key_6, self) # Grid 2x3 shortcut
        # noinspection PyUnresolvedReferences
        self._shcut9 = QShortcut(Qt.Key_9, self) # Grid 3x3 shortcut
        self._shcutx = QShortcut('x', self) # Show cursor shortcut
        self._shcuti = QShortcut('i', self) # Show information shortcut
        self._shcutl = QShortcut('l', self) # Show orientation labels shortcut
        self._shcutm = QShortcut('m', self)  # Show orientation marker shortcut
        self._shcutb = QShortcut('b', self)  # Show color bar shortcut
        self._shcutr = QShortcut('r', self)  # Show ruler shortcut
        self._shcutt = QShortcut('t', self)  # Show tooltip shortcut
        # < Revision 04/05/2026
        self._shcutf = QShortcut('f', self)  # Line/font properties shortcut
        # Revision 04/05/2026 >

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
        # noinspection PyUnresolvedReferences
        self._layout.setAlignment(Qt.AlignVCenter)
        self._layout.addWidget(self._bar)

        self._vlayout = QVBoxLayout()
        self._vlayout.setSpacing(0)
        self._vlayout.setContentsMargins(0, 0, 0, 0)
        self._vlayout.addLayout(self._layout)

        self.setLayout(self._vlayout)
        self.setAcceptDrops(True)

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

    def __call__(self) -> MultiViewWidget:
        """
        Allows the instance to be called as a function, returning the encapsulated MultiViewWidget instance.

        Returns
        -------
        MultiViewWidget
            encapsulated display widget.
        """
        if self._widget is not None: return self._widget
        else: raise AttributeError('Widget attribute is not defined.')

    # Private methods

    def _createButton(self,
                      icon0: str,
                      icon1: str = '',
                      checkable: bool = False,
                      autorepeat: bool = False) -> RoundedButton:
        """
        Creates and configures a RoundedButton for the icon bar.

        Parameters
        ----------
        icon0 : str
            Filename for the button's normal state icon.
        icon1 : str (optional)
            Filename for the button's checked state icon (default '').
        checkable : bool (optional)
            whether the button is checkable (default False).
        autorepeat : bool (optional)
            whether the button auto-repeats when held down (default False).

        Returns
        -------
        RoundedButton
            configured button instance.
        """
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

    def _getBaseParent(self) -> QWidget:
        """
        Traverses the parent hierarchy to find the top-level parent widget.

        Returns
        -------
        QWidget
            top-level parent widget.
        """
        w = None
        w2 = self.parent()
        while w2 is not None:
            w = w2
            w2 = w.parent()
        return w

    def _onMenuTools(self, action: QAction) -> None:
        """
        Handles the 'Tools' menu actions to add measurement tools to the view widget.

        Parameters
        ----------
        action : QAction
            triggered menu action.
        """
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

    def _onMenuSaveCapture(self, action: QAction) -> None:
        """
        Handles the 'Capture' menu actions to save or send viewport captures.

        Parameters
        ----------
        action : QAction
            triggered menu action.
        """
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

    def _onMenuCopyCapture(self, action: QAction) -> None:
        """
        Handles the 'Copy' menu actions to copy viewport captures to the clipboard.

        Parameters
        ----------
        action : QAction
            triggered menu action.
        """
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

    def _onMenuOrientation(self, v: int) -> None:
        """
        Updates the orientation icon when the orientation is changed from the menu.

        Parameters
        ----------
        v : int
            orientation index (0: axial, 1: coronal, 2: sagittal).
        """
        if v == 0: self._icons['orient'].setIcon(self._ax)
        elif v == 1: self._icons['orient'].setIcon(self._cor)
        else: self._icons['orient'].setIcon(self._sag)

    def _onMenuIso(self, action: QAction) -> None:
        """
        Handles the 'Isovalue' menu actions to set and display isolines for a selected volume or overlay.

        Parameters
        ----------
        action : QAction
            triggered menu action.
        """
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

    def _onShowMenuIso(self) -> None:
        """
        Populates and configures the 'Isovalue' menu before it is shown.
        """
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
                    i: cython.int
                    for i in range(view.getOverlayCount()):
                        name = view.getOverlayFromIndex(i).getName()
                        if name == '': name = 'Overlay volume #{}'.format(i)
                        action = QAction(name)
                        action.setData(i + 1)
                        group.addAction(action)
                        action.setCheckable(True)
                        action.setChecked(n == i + 1)
                        self._isoMenu.addAction(action)

    def _onIsoEditingFinished(self) -> None:
        """
        Updates the isoline values when editing in the line edit is finished.
        """
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

    def _onIsoColorChanged(self) -> None:
        """
        Updates the isoline color when the color is changed.
        """
        view = self._widget.getFirstSliceViewWidget()
        if view is not None and isinstance(view, SliceOverlayViewWidget):
            n = view.getIsoIndex()
            if n > -1:
                c = list(self._isocolor.getFloatColor())
                view.setIsoLinesColor(c, signal=True)

    # noinspection PyUnusedLocal
    def _onIsoOpacityChanged(self, w: QWidget) -> None:
        """
        Updates the isoline opacity when the opacity is changed.

        Parameters
        ----------
        w : QWidget
            widget that emitted the signal.
        """
        view = self._widget.getFirstSliceViewWidget()
        if view is not None and isinstance(view, SliceOverlayViewWidget):
            n = view.getIsoIndex()
            if n > -1:
                v = self._isoopacity.getOpacity()
                view.setIsoLinesOpacity(v, signal=True)

    # < Revision 01/05/2025
    # add _onTransferMenuChanged method
    def _onTransferMenuChanged(self) -> None:
        """
        Adjusts the transfer function menu size when its content changes.
        """
        if self._transfer is not None:
            menu = self._icons['transfer'].menu()
            self._transfer.adjustSize()
            menu.hide()
            menu.setFixedHeight(self._transfer.size().height())
            menu.show()
            QApplication.processEvents()
    # Revision 01/05/2025 >

    def _onExpand(self) -> None:
        """
        Toggles the expanded view of the currently selected sub-widget.
        """
        if self._widget is not None:
            if self._icons['expand'].isChecked():
                w = self._widget.getSelectedViewWidget()
                # < Revision 05/12/2025
                # if no view is selected, select the first one
                if w is None:
                    w = self._widget.getFirstViewWidget()
                    w.select(True)
                # Revision 05/12/2025 >
                if w is not None:
                    w.getAction()['expand'].toggle()
                    self._widget.expandViewWidget(w)
                    # < Revision 17/11/2025
                    # disable synchronization when displaying a single (expanded) view to speed up rendering
                    w.synchronisationOff()
                    # Revision 17/11/2025 >
                    # < Revision 19/11/2025
                    if 'grid' in self._icons: self._icons['grid'].setVisible(False)
                    # Revision 19/11/2025 >
            else:
                i: cython.int
                j: cython.int
                for i in range(0, self._widget.getRows()):
                    for j in range(0, self._widget.getCols()):
                        action = self._widget[i, j].getAction()['expand']
                        if action.isChecked(): action.setChecked(False)
                        self._widget[i, j].setVisible(True)
                        # < Revision 17/11/2025
                        self._widget[i, j].synchronisationOn()
                        # Revision 17/11/2025 >
                # < Revision 19/11/2025
                if 'grid' in self._icons: self._icons['grid'].setVisible(True)
                # Revision 19/11/2025 >

    def _onFullScreen(self) -> None:
        """
        Toggles the full-screen mode.
        """
        w = self._getBaseParent()
        from Sisyphe.gui.windowSisyphe import WindowSisyphe
        if isinstance(w, WindowSisyphe): w.toggleFullscreen()
        else: self._icons['screen'].setVisible(False)

    def _onPin(self) -> None:
        """
        Toggles the pinned state of the icon bar. The icon bar is no longer collapsible when pinned.
        """
        if self._icons['pin'].isVisible():
            self._icons['pin'].setChecked(False)
        else: self._icons['pin'].setChecked(True)

    def _connectExpandAction(self) -> None:
        """
        Connects the 'expand' action of each sub-widget to the expand button.
        """
        i: cython.int
        j: cython.int
        for i in range(0, self._widget.getRows()):
            for j in range(0, self._widget.getCols()):
                try:
                    action = self._widget[i, j].getAction()['expand']
                    if action is not None:
                        action.triggered.connect(self._icons['expand'].setChecked)
                except: return

    def _showViewWidget(self) -> None:
        """
        Shows the icon bar and the encapsulated view widget.
        """
        self._bar.show()
        self._widget.show()
        QApplication.processEvents()

    def _hideViewWidget(self) -> None:
        """
        Hides the icon bar and the encapsulated view widget.
        """
        self._bar.hide()
        self._widget.hide()
        QApplication.processEvents()

    # Public method

    # < Revision 17/03/2025
    # add setIconSize method
    def setIconSize(self, size: int | None) -> None:
        """
        Set the size, in pixels, of the icons in the icon bar.

        Parameters
        ----------
        size : int | None

            - new size for the icons. Clamped between 0 and 64.
            - if None, set the size to its default value (40).
        """
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
        """
        Get the current size of the icons in the icon bar.

        Returns
        -------
        int
            current icon size in pixels.
        """
        return self._btsize

    # < Revision 08/03/2025
    # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
    # finalize method must be called before destruction
    def finalize(self)  -> None:
        """
        Method to be called before IconBarWidget instance destruction.
        It is used to avoid vtk error on Windows platform (vtkWin32OpenGLRenderWindow error: 'wglMakeCurrent failed in
        MakeCurrent()').
        """
        if self._widget is not None:
            self._widget.finalize()
    # Revision 08/03/2025 >

    def timerEnabled(self) -> None:
        """
        Enables a timer to manage icon bar visibility based on mouse position.
        The timer is only started if a SisypheVolume is displayed.
        """
        if self._widget.hasVolume():
            if self._timerid is None:
                self._timerid = self.startTimer(0)

    def timerDisabled(self) -> None:
        """
        Disable the icon bar visibility timer.
        This timer is used to manage icon bar visibility based on mouse position.
        """
        # timer used to detect when mouse leaves icon bar
        # call timerEvent Qt event method
        if self._timerid is not None:
            self.killTimer(self._timerid)
            self._timerid = None

    # < Revision 22/12/2025
    def isTimerEnabled(self) -> bool:
        """
        Check if the timer to manage icon bar visibility is enabled.
        The timer is only started if a SisypheVolume is displayed.

        Returns
        -------
        bool
            True if the timer is enabled, False otherwise.
        """
        return self._timerid is not None
    # Revision 22/12/2025 >

    def updateRender(self) -> None:
        """
        Trigger a render update in the encpasulated view widget.
        """
        self._widget.updateRender()

    def getName(self) -> str:
        """
        Get the name of the widget.

        Returns
        -------
        str
            widget name.
        """
        return self.objectName()

    def setName(self, name: str) -> None:
        """
        Set the name of the widget and emits a signal.

        Parameters
        ----------
        name : str
            new widget name.
        """
        if isinstance(name, str):
            self.setObjectName(name)
            # noinspection PyUnresolvedReferences
            self.NameChanged.emit()
        else: raise TypeError('parameter type {} is not str.'.format(type(name)))

    # Public reference volume methods

    def setVolume(self, vol: SisypheVolume) -> None:
        """
        Set the SisypheVolume to be displayed.

        Parameters
        ----------
        vol : SisypheVolume
            volume to display.
        """
        if isinstance(vol, SisypheVolume):
            if self._widget is not None:
                self._widget.setVolume(vol)
                self._showViewWidget()

    # < Revision 18/10/2024
    # add replaceVolume method
    def replaceVolume(self, vol: SisypheVolume) -> None:
        """
        Replace the currently displayed SisypheVolume with a new one.
        The new volume must have the same dimensions as the old one.

        Parameters
        ----------
        vol : SisypheVolume
            new volume to display.
        """
        if isinstance(vol, SisypheVolume):
            if self._widget is not None:
                self._widget.replaceVolume(vol)
    # Revision 18/10/2024 >

    def getVolume(self) -> SisypheVolume:
        """
        Get the displayed SisypheVolume.

        Returns
        -------
        SisypheVolume
            reference SisypheVolume.
        """
        return self._widget.getVolume()

    def hasVolume(self) -> bool:
        """
        Check if a reference SisypheVolume is displayed.

        Returns
        -------
        bool
            True if a volume is displayed, False otherwise.
        """
        return self._widget.hasVolume()

    def removeVolume(self) -> None:
        """
        Remove the reference SisypheVolume.
        """
        if self._widget is not None:
            self._hideViewWidget()
            QApplication.processEvents()
            self._widget.removeVolume()

    # Public overlay methods

    def addOverlay(self, volume: SisypheVolume) -> None:
        """
        Add an overlay SisypheVolume.

        Parameters
        ----------
        volume : SisypheVolume
            SisypheVolume to add as an overlay.
        """
        if self._widget is not None:
            if self._widget.hasVolume():
                self._widget.addOverlay(volume)

    def getOverlayCount(self) -> int:
        """
        Get the number of overlay volumes.

        Returns
        -------
        int
            number of overlays.
        """
        if self._widget is not None:
            if self._widget.hasVolume(): return self._widget.getOverlayCount()
            else: raise AttributeError('no volume in _widget attribute.')
        else: raise AttributeError('_widget attribute is None.')

    def hasOverlay(self) -> bool:
        """
        Checksif there are any overlay volumes.

        Returns
        -------
        bool
            True if at least one overlay exists, False otherwise.
        """
        if self._widget is not None:
            if self._widget.hasVolume(): return self._widget.hasOverlay()
            else: raise AttributeError('no volume in _widget attribute.')
        else: raise AttributeError('_widget attribute is None.')

    def getOverlayIndex(self, o: SisypheVolume) -> int:
        """
        Get the index of a specific overlay volume.

        Parameters
        ----------
        o : SisypheVolume
            overlay volume instance to find.

        Returns
        -------
        int
            index of the overlay.
        """
        if self._widget is not None:
            if self._widget.hasVolume(): return self._widget.getOverlayIndex(o)
            else: raise AttributeError('no volume in _widget attribute.')
        else: raise AttributeError('_widget attribute is None.')

    def removeOverlay(self, o: int | SisypheVolume) -> None:
        """
        Remove an overlay volume by index or instance.

        Parameters
        ----------
        o : int | SisypheVolume
            index or instance of the overlay to remove.
        """
        if self._widget is not None:
            if self._widget.hasVolume():
                self._widget.removeOverlay(o)

    def removeAllOverlays(self) -> None:
        """
        Remove all overlay volumes.
        """
        if self._widget is not None:
            if self._widget.hasVolume():
                self._widget.removeAllOverlays()

    def getOverlayFromIndex(self, index: int) -> SisypheVolume:
        """
        Get an overlay volume by its index.

        Parameters
        ----------
        index : int
            index of the overlay to retrieve.

        Returns
        -------
        SisypheVolume
            overlay volume at the specified index.
        """
        if self._widget is not None:
            if self._widget.hasVolume(): return self._widget.getOverlayFromIndex(index)
            else: raise AttributeError('no volume in _widget attribute.')
        else: raise AttributeError('_widget attribute is None.')

    def setAlignCenters(self, v: bool) -> None:
        """
        Set whether to align the centers of the reference volume and overlays.

        Parameters
        ----------
        v : bool
            True to align centers, False otherwise.
        """
        if self._widget is not None:
            self._widget.setAlignCenters(v)

    def alignCentersOn(self) -> None:
        """
        Enable alignment of centers for the reference volume and overlays.
        """
        if self._widget is not None:
            self._widget.setAlignCentersOn()

    def alignCentersOff(self) -> None:
        """
        Disable alignment of centers for the reference volume and overlays.
        """
        if self._widget is not None:
            self._widget.setAlignCentersOff()

    def getAlignCenters(self) -> bool:
        """
        Get the current state of center alignment.

        Returns
        -------
        bool
            True if center alignment is enabled, False otherwise.
        """
        if self._widget is not None: return self._widget.getAlignCenters()
        else: raise AttributeError('_widget attribute is None.')

    # Public view widget methods

    def setViewWidget(self, widget: MultiViewWidget) -> None:
        """
        Set and configure the view widget encapsulated by the IconBarWidget.
        This method connects the icon bar buttons to the corresponding actions of the view widget.

        Parameters
        ----------
        widget : MultiViewWidget
            view widget to be encapsulated.
        """
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
            # noinspection PyUnresolvedReferences
            submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyUnresolvedReferences
            submenu.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyUnresolvedReferences
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
                # < Revision 05/12/2025
                # layout.insertWidget(3, self._icons['sliceplus'])
                # layout.insertWidget(3, self._icons['sliceminus'])
                # layout.insertWidget(3, self._icons['orient'])
                # noinspection PyUnresolvedReferences
                layout.insertWidget(4, self._icons['sliceplus'])
                # noinspection PyUnresolvedReferences
                layout.insertWidget(4, self._icons['sliceminus'])
                # noinspection PyUnresolvedReferences
                layout.insertWidget(4, self._icons['orient'])
                # Revision 05/12/2025 >
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
                                               't key show/hide tooltip\n'
                                               'f key line/font properties')
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
                # < Revision 04/05/2026
                # noinspection PyUnresolvedReferences
                self._shcutf.activated.connect(lambda: self._icons['show'].menu().actions()[-1].trigger())
                # Revision 04/05/2026 >
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
                    # < Revision 05/12/2025
                    # layout.insertWidget(3, self._icons['grid'])
                    # noinspection PyUnresolvedReferences
                    layout.insertWidget(4, self._icons['grid'])
                    # Revision 05/12/2025 >
            if grid or orthoslc:
                self._icons['show'].setMenu(view1.getPopupVisibility())
                submenu = QMenu()
                # noinspection PyUnresolvedReferences
                submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyUnresolvedReferences
                submenu.setWindowFlag(Qt.FramelessWindowHint, True)
                # noinspection PyUnresolvedReferences
                submenu.setAttribute(Qt.WA_TranslucentBackground, True)
                submenu.addAction('Save grid capture...')
                submenu.addAction('Save selected view capture...')
                submenu.addAction('Save captures from slice series...')
                submenu.addSeparator()
                action = submenu.addAction('Send selected view capture to screenshots preview')
                # noinspection PyUnresolvedReferences
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
                # noinspection PyUnresolvedReferences
                submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyUnresolvedReferences
                submenu.setWindowFlag(Qt.FramelessWindowHint, True)
                # noinspection PyUnresolvedReferences
                submenu.setAttribute(Qt.WA_TranslucentBackground, True)
                a = QWidgetAction(self)
                a.setDefaultWidget(self._transfer)
                submenu.addAction(a)
                self._icons['transfer'].setMenu(submenu)

                layout = self._bar.layout()
                # < Revision 05/12/2025
                # layout.insertWidget(3, self._icons['align'])
                # layout.insertWidget(3, self._icons['transfer'])
                # layout.insertWidget(3, self._icons['campos'])
                # layout.insertWidget(3, self._icons['texture'])
                # noinspection PyUnresolvedReferences
                layout.insertWidget(4, self._icons['align'])
                # noinspection PyUnresolvedReferences
                layout.insertWidget(4, self._icons['transfer'])
                # noinspection PyUnresolvedReferences
                layout.insertWidget(4, self._icons['campos'])
                # noinspection PyUnresolvedReferences
                layout.insertWidget(4, self._icons['texture'])
                # Revision 05/12/2025 >

                self._icons['show'].setMenu(view2.getPopupVisibility())
                self._icons['show'].setToolTip('Set visibility options.\n'
                                               'x key show/hide cursor\n'
                                               'i key show/hide information\n'
                                               'm key show/hide orientation marker\n'
                                               'b key show/hide colorbar\n'
                                               'r key show/hide ruler\n'
                                               't key show/hide tooltip\n'
                                               'f key line/font properties')
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
                # < Revision 04/05/2026
                # noinspection PyUnresolvedReferences
                self._shcutf.activated.connect(lambda: self._icons['show'].menu().actions()[-1].trigger())
                # Revision 04/05/2026 >

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
                # noinspection PyUnresolvedReferences
                submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
                # noinspection PyUnresolvedReferences
                submenu.setWindowFlag(Qt.FramelessWindowHint, True)
                # noinspection PyUnresolvedReferences
                submenu.setAttribute(Qt.WA_TranslucentBackground, True)
                submenu.addAction('Save grid capture...')
                submenu.addAction('Save selected view capture...')
                submenu.addAction('Save captures from multiple camera positions...')
                submenu.addAction('Save single capture from multiple camera positions...')
                submenu.addSeparator()
                action = submenu.addAction('Send selected view capture to screenshots preview')
                # noinspection PyUnresolvedReferences
                action.setShortcut(Qt.Key_Space)
                submenu.addAction('Send captures from multiple camera positions to screenshots preview')
                # noinspection PyUnresolvedReferences
                submenu.triggered.connect(self._onMenuSaveCapture)
                self._icons['capture'].setMenu(submenu)

        else: raise TypeError('parameter type {} is not MultiViewWidget.'.format(type(widget)))

    def getViewWidget(self) -> MultiViewWidget:
        """
        Get the encapsulated view widget.

        Returns
        -------
        MultiViewWidget
            encapsulated view widget.
        """
        return self._widget

    def viewWidgetVisibleOn(self) -> None:
        """
        Make the encapsulated view widget visible.
        """
        self.setViewWidgetVisibility(True)

    def viewWidgetVisibleOff(self) -> None:
        """
        Make the encapsulated view widget invisible.
        """
        self.setViewWidgetVisibility(False)

    def setViewWidgetVisibility(self, v: bool) -> None:
        """
        Set the visibility of the encapsulated view widget.

        Parameters
        ----------
        v : bool
            True to show the widget, False to hide it.
        """
        if isinstance(v, bool):
            self._widget.setVisible(v)
            QApplication.processEvents()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getViewWidgetVisibility(self) -> bool:
        """
        Get the visibility of the encapsulated view widget.

        Returns
        -------
        bool
            True if the widget is visible, False otherwise.
        """
        return self._widget.isVisible()

    # Public icon bar widget methods

    def iconBarVisibleOff(self) -> None:
        """
        Hide the icon bar.
        """
        self.setIconBarVisibility(False)

    def iconBarVisibleOn(self) -> None:
        """
        Show the icon bar.
        """
        self.setIconBarVisibility(True)

    def setIconBarVisibility(self, v: bool) -> None:
        """
        Set the visibility of the icon bar, respecting the pinned state.

        Parameters
        ----------
        v : bool
            True to show the icon bar, False to hide it.
        """
        if isinstance(v, bool):
            if self._icons['pin'].isChecked(): v = True
            for key in self._icons:
                if self._visibilityflags[key]: self._icons[key].setVisible(v)
                else: self._icons[key].setVisible(False)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getIconBarVisibility(self) -> bool:
        """
        Get the current visibility of the icon bar.

        Returns
        -------
        bool
            True if the icon bar is visible, False otherwise.
        """
        return self._icons['pin'].isVisible()

    def setFullscreenButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the fullscreen button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['screen'] = v
            self._icons['screen'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setPinButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the pin button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['pin'] = v
            if not v: self._icons['pin'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setExpandButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the expand button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['expand'] = v
            if not v: self._icons['expand'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setGridButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the grid layout button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['grid'] = v
            if not v: self._icons['grid'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setOrientButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the orientation button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['orient'] = v
            if not v: self._icons['orient'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setInfoButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the information button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['info'] = v
            if not v: self._icons['info'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setIsoButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the isovalue button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['iso'] = v
            if not v: self._icons['iso'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setSliceButtonsAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the slice navigation buttons.

        Parameters
        ----------
        v : bool
            True to make the buttons available, False to hide them.
        """
        if isinstance(v, bool):
            self._visibilityflags['sliceplus'] = v
            self._visibilityflags['sliceminus'] = v
            if not v:
                self._icons['sliceplus'].setVisible(v)
                self._icons['sliceminus'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setShowButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the show/hide options button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['show'] = v
            if not v: self._icons['show'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setZoomButtonsAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the zoom control buttons.

        Parameters
        ----------
        v : bool
            True to make the buttons available, False to hide them.
        """
        if isinstance(v, bool):
            self._visibilityflags['zoomin'] = v
            self._visibilityflags['zoomout'] = v
            self._visibilityflags['zoom1'] = v
            if not v:
                self._icons['zoomin'].setVisible(v)
                self._icons['zoomout'].setVisible(v)
                self._icons['zoom1'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setActionButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the mouse actions button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['actions'] = v
            # < Revision 10/07/2026
            # if not v: self._icons['actions'].setVisible(v)
            self._icons['actions'].setVisible(v)
            # Revision 10/07/2026 >
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setToolButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the measurement tools button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['tools'] = v
            if not v: self._icons['tools'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setCaptureButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the capture button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['capture'] = v
            if not v: self._icons['capture'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setClipboardButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the clipboard button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['clipboard'] = v
            if not v: self._icons['clipboard'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setTransferButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the transfer function button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['transfer'] = v
            if not v: self._icons['transfer'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setColorbarButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the color bar button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['colorbar'] = v
            if not v: self._icons['colorbar'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setRulerButtonAvailability(self, v: bool) -> None:
        """
        Set the availability (and visibility) of the ruler button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['ruler'] = v
            if not v: self._icons['ruler'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getFullscreenButtonAvailability(self) -> bool:
        """
        Get the availability flag for the fullscreen button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['screen']

    def getPinButtonAvailability(self) -> bool:
        """
        Get the availability flag for the pin button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['pin']

    def getExpandButtonAvailability(self) -> bool:
        """
        Get the availability flag for the expand button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['expand']

    def getGridButtonAvailability(self) -> bool:
        """
        Get the availability flag for the grid layout button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['grid']

    def getOrientButtonAvailability(self) -> bool:
        """
        Get the availability flag for the orientation button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['orient']

    def getSliceButtonsAvailability(self) -> bool:
        """
        Get the availability flag for the slice navigation buttons.

        Returns
        -------
        bool
            True if the buttons are available, False otherwise.
        """
        return self._visibilityflags['sliceplus']

    def getShowButtonAvailability(self) -> bool:
        """
        Get the availability flag for the show/hide options button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['show']

    def getInfoButtonAvailability(self) -> bool:
        """
        Get the availability flag for the information button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['info']

    def getIsoButtonAvailability(self) -> bool:
        """
        Getsthe availability flag for the isovalue button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['iso']

    def getActionButtonAvailability(self) -> bool:
        """
        Get the availability flag for the mouse actions button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['actions']

    def getZoomButtonsAvailability(self) -> bool:
        """
        Get the availability flag for the zoom control buttons.

        Returns
        -------
        bool
            True if the buttons are available, False otherwise.
        """
        return self._visibilityflags['zoomin']

    def getToolButtonAvailability(self) -> bool:
        """
        Get the availability flag for the measurement tools button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['tools']

    def getCaptureButtonAvailability(self) -> bool:
        """
        Get the availability flag for the capture button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['capture']

    def getClipboardButtonAvailability(self) -> bool:
        """
        Get the availability flag for the clipboard button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['clipboard']

    def getTransferButtonAvailability(self) -> bool:
        """
        Get the availability flag for the transfer function button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['transfer']

    def getColorbarButtonAvailability(self) -> bool:
        """
        Get the availability flag for the color bar button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['colorbar']

    def getRulerButtonAvailability(self) -> bool:
        """
        Get the availability flag for the ruler button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['ruler']

    def getThumbnail(self) -> ToolBarThumbnail:
        """
        Get the associated thumbnail bar widget.

        Returns
        -------
        ToolBarThumbnail
            associated thumbnail bar widget instance.
        """
        return self._thumbnail

    def setThumbnail(self, thumbnail: ToolBarThumbnail) -> None:
        """
        Set the associated thumbnail bar widget.

        Parameters
        ----------
        thumbnail : ToolBarThumbnail
            The thumbnail bar widget to associate with this icon bar.
        """
        from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
        if isinstance(thumbnail, ToolBarThumbnail):
            self._thumbnail = thumbnail
        else: raise TypeError('parameter type {} is not ToolBarThumbnail.'.format(type(thumbnail)))

    def hasThumbnail(self) -> bool:
        """
        Check if a thumbnail bar widget is associated.

        Returns
        -------
        bool
            True if a thumbnail bar is associated, False otherwise.
        """
        return self._thumbnail is not None

    def getButtons(self) -> dict[str, RoundedButton]:
        """
        Get the dictionary of icon bar buttons.

        Returns
        -------
        dict[str, RoundedButton]
            dictionary mapping button names to their instances.
        """
        return self._icons

    # Event loop, solves VTK mouse move event bug

    @classmethod
    def _widgetUnderCursor(cls, widget: QWidget) -> bool:
        """
        Checks if the mouse pointer is currently over a view widget.

        Parameters
        ----------
        widget : QWidget
            The widget to check.

        Returns
        -------
        bool
            True if the cursor is over the widget, False otherwise.
        """
        p = widget.cursor().pos()
        p = widget.mapFromGlobal(p)
        return 0 <= p.x() < widget.width() and 0 <= p.y() < widget.height()

    # Qt events

    def timerEvent(self, event: Optional[QTimerEvent]) -> None:
        """
        Handles timer events to manage the auto-hiding of the unpinned icon bar.
        Currently, this method overrides the superclass's implementation.

        Parameters
        ----------
        event : QTimerEvent
            timer event.
        """
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

    def dragEnterEvent(self, event: Optional[QDragEnterEvent]) -> None:
        """
        Handles drag enter events, accepting text-based mime data for drag-and-drop operations.
        This is used to load PySisyphe volume (.xvol) from the thumbnail bar.

        Parameters
        ----------
        event : QDragEnterEvent
            drag enter event.
        """
        if event.mimeData().hasText(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event: Optional[QDropEvent]) -> None:
        """
        Handles drop events to load PySisyphe volume (.xvol) from the thumbnail bar based on user settings.
        The action (replace, overlay, etc.) depends on the 'DropInView' application setting (settings.xml).

        Parameters
        ----------
        event : QDropEvent
            drop event.
        """
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

    This widget encapsulates an OrthogonalSliceViewWidget and extends it by providing a collapsible icon bar that is
    displayed on the left.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalSliceViewWidget

    Creation: 17/04/2022
    Last revision: 10/10/2025
    """

    # Special method

    def __init__(self,
                 widget: OrthogonalSliceViewWidget | None = None,
                 parent: QWidget | None = None) -> None:
        """
        IconBarOrthogonalSliceViewWidget instance constructor.

        Parameters
        ----------
        widget : OrthogonalSliceViewWidget | None (optional)
            OrthogonalSliceViewWidget to encapsulate (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
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

    This widget encapsulates an OrthogonalRegistrationViewWidget and extends it by providing a collapsible icon bar
    that is displayed on the left.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalRegistrationViewWidget

    Creation: 17/04/2022
    Last revision: 10/10/2025
    """

    # Special method

    def __init__(self,
                 widget: OrthogonalRegistrationViewWidget | None = None,
                 parent: QWidget | None = None) -> None:
        """
        IconBarOrthogonalRegistrationViewWidget instance constructor.

        Parameters
        ----------
        widget : OrthogonalRegistrationViewWidget | None (optional)
            OrthogonalRegistrationViewWidget to encapsulate (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
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

        # Registration area box synchronization

        for view1 in self.getViewWidget().getSliceViewWidgets():
            view1.setSelectable(False)
            for view2 in self.getViewWidget().getSliceViewWidgets():
                if view1 != view2:
                    view1.RegistrationBoxVisibilityChanged.connect(view2.synchroniseRegistrationBoxVisibilityChanged)
                    view1.RegistrationBoxChanged.connect(view2.synchroniseRegistrationBoxChanged)

    # Public methods

    def setCrop(self, crop: bool) -> None:
        """
        Set whether to crop the registration area.

        Parameters
        ----------
        crop : bool
            True to enable cropping, False to disable it.
        """
        if isinstance(crop, bool):  self._widget.getFirstSliceViewWidget().setCrop(crop)
        else: raise TypeError('parameter type {} is not bool'.format(type(crop)))

    def getCrop(self) -> bool:
        """
        Get the current crop state of the registration area.

        Returns
        -------
        bool
            True if cropping is enabled, False otherwise.
        """
        return self._widget.getFirstSliceViewWidget().getCrop()

    def cropOn(self) -> None:
        """
        Enable cropping of the registration area.
        """
        self.setCrop(True)

    def cropOff(self) -> None:
        """
        Disable cropping of the registration area.
        """
        self.setCrop(False)

    def setRegistrationBoxVisibility(self, v: bool) -> None:
        """
        Set the visibility of the coregistration box.
        Voxels located outside the registration box are not used to calculate the coregistration.

        Parameters
        ----------
        v : bool
            True to show the box, False to hide it.
        """
        if isinstance(v, bool): self._widget.getFirstSliceViewWidget().setRegistrationBoxVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getRegistrationBoxVisibility(self) -> bool:
        """
        Get the visibility of the coregistration box.
        Voxels located outside the registration box are not used to calculate the coregistration.

        Returns
        -------
        bool
            True if the box is visible, False otherwise.
        """
        return self._widget.getFirstSliceViewWidget().getRegistrationBoxVisibility()

    def registrationBoxOn(self) -> None:
        """
        Show the registration box.
        Voxels located outside the coregistration box are not used to calculate the coregistration.
        """
        self.setRegistrationBoxVisibility(True)

    def registrationBoxOff(self) -> None:
        """
        Hide the registration box.
        Voxels located outside the coregistration box are not used to calculate the coregistration.
        """
        self.setRegistrationBoxVisibility(False)

    def getRegistrationBoxMatrixArea(self) -> list[float] | tuple[float, float, float, float, float, float]:
        """
        Get the bounds of the coregistration box as a matrix area.
        Voxels located outside the registration box are not used to calculate the coregistration.

        Returns
        -------
        list[float] | tuple[float, float, float, float, float, float]
            bounds of the registration box.
        """
        return self._widget.getFirstSliceViewWidget().getRegistrationBoxMatrixArea()

    def displayEdge(self) -> None:
        """
        Display the edges of the moving volume for registration visualization.
        """
        self._widget.getFirstSliceViewWidget().displayEdge()

    def displayNative(self) -> None:
        """
        Display the native (unprocessed) moving volume.
        """
        self._widget.getFirstSliceViewWidget().displayNative()

    def displayEdgeAndNative(self) -> None:
        """
        Display both the edges and the native moving volume.
        """
        self._widget.getFirstSliceViewWidget().displayEdgeAndNative()


class IconBarOrthogonalRegistrationViewWidget2(IconBarOrthogonalRegistrationViewWidget):
    """
    IconBarOrthogonalRegistrationViewWidget2 class

    Description
    ~~~~~~~~~~~

    This widget encapsulates an OrthogonalRegistrationViewWidget and extends it by providing a collapsible icon bar
    that is displayed on the left, with rigid transformation buttons at the bottom.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalRegistrationViewWidget -> IconBarOrthogonalRegistrationViewWidget2

    Creation: 17/04/2022
    Last revision: 02/02/2026
    """

    # Special method

    def __init__(self,
                 widget: OrthogonalRegistrationViewWidget | None = None,
                 parent: QWidget | None = None) -> None:
        """
        IconBarOrthogonalRegistrationViewWidget2 instance constructor.

        Parameters
        ----------
        widget : OrthogonalRegistrationViewWidget | None (optional)
            OrthogonalRegistrationViewWidget to encapsulate (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
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

        # < Revision 02/02/2026
        # black background of button bar
        self._frame = QFrame(self)
        # if platform == 'win32':
        #     self._frame.setObjectName('TrfBar')
        #     self._frame.setStyleSheet('QFrame#TrfBar { background-color: #000000; border-color: #000000; } '
        #                               'QToolTip#TrfBar { color: #000000; background-color: #FFFFE0; border: 0px; font-size: 8pt; }')
        self._frame.setObjectName('TrfBar')
        self._frame.setStyleSheet('QFrame#TrfBar { background-color: #000000; border-color: #000000; } '
                                  'QToolTip#TrfBar { color: #000000; background-color: #FFFFE0; border: 0px; font-size: 8pt; }')
        # else:
        #     self._frame.setAutoFillBackground(True)
        #     # noinspection PyUnresolvedReferences
        #    self._frame.palette().setColor(QPalette.Window, Qt.black)
        self._frame.setLayout(layout)
        # Revision 02/02/2026 >

        for view in self.getViewWidget().getSliceViewWidgets():
            view.TranslationsChanged.connect(lambda d1, d2: self._updateTooltips())
            view.RotationsChanged.connect(lambda d1, d2: self._updateTooltips())

        # < Revision 22/05/2025
        # self._vlayout.addLayout(layout)
        self._vlayout.addWidget(self._frame)
        # Revision 22/05/2025 >
        self._hideViewWidget()

    # Private methods

    def _updateTooltips(self) -> None:
        """
        Updates the tooltips of the rigid transformation buttons with current translation and rotation values.
        """
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

    def _xtranslation(self, v: float) -> None:
        """
        Apply a translation along the x-axis.

        Parameters
        ----------
        v : float
            translation step in mm.
        """
        widget = self().getFirstSliceViewWidget()
        t = list(widget.getTranslations(index=0))
        t[0] += v
        widget.setTranslations(tuple(t), index=0)
        self._buttons['left0'].setToolTip('Right translation\nX Translation {:.2f} mm'.format(t[0]))
        self._buttons['right0'].setToolTip('Left translation\nX Translation {:.2f} mm'.format(t[0]))
        self._buttons['left1'].setToolTip('Right translation\nX Translation {:.2f} mm'.format(t[0]))
        self._buttons['right1'].setToolTip('Left translation\nX Translation {:.2f} mm'.format(t[0]))

    def _ytranslation(self, v: float) -> None:
        """
        Apply a translation along the y-axis.

        Parameters
        ----------
        v : float
            translation step in mm.
        """
        widget = self().getFirstSliceViewWidget()
        t = list(widget.getTranslations(index=0))
        t[1] += v
        widget.setTranslations(tuple(t), index=0)
        self._buttons['up0'].setToolTip('Forward translation\nY Translation {:.2f} mm'.format(t[1]))
        self._buttons['down0'].setToolTip('Backward translation\nY Translation {:.2f} mm'.format(t[1]))
        self._buttons['left2'].setToolTip('Forward translation\nY Translation {:.2f} mm'.format(t[1]))
        self._buttons['right2'].setToolTip('Backward translation\nY Translation {:.2f} mm'.format(t[1]))

    def _ztranslation(self, v: float) -> None:
        """
        Apply a translation along the z-axis.

        Parameters
        ----------
        v : float
            translation step in mm.
        """
        widget = self().getFirstSliceViewWidget()
        t = list(widget.getTranslations(index=0))
        t[2] += v
        widget.setTranslations(tuple(t), index=0)
        self._buttons['up1'].setToolTip('Cranial translation\nZ Translation {:.2f} mm'.format(t[2]))
        self._buttons['down1'].setToolTip('Caudal translation\nZ Translation {:.2f} mm'.format(t[2]))
        self._buttons['up2'].setToolTip('Cranial translation\nZ Translation {:.2f} mm'.format(t[2]))
        self._buttons['down2'].setToolTip('Caudal translation\nZ Translation {:.2f} mm'.format(t[2]))

    def _xrotation(self, v: float) -> None:
        """
        Apply a rotation around the x-axis.

        Parameters
        ----------
        v : float
            rotation step in degrees.
        """
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations(index=0))
        r[0] += v
        widget.setRotations(tuple(r), index=0)
        self._buttons['rotc2'].setToolTip('Clockwise X rotation\nX Rotation {:.2f}°'.format(r[0]))
        self._buttons['rota2'].setToolTip('Counter-clockwise X Rotation\nX Rotation {:.2f}°'.format(r[0]))

    def _yrotation(self, v: float) -> None:
        """
        Apply a rotation around the y-axis.

        Parameters
        ----------
        v : float
            rotation step in degrees.
        """
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations(index=0))
        r[1] += v
        widget.setRotations(tuple(r), index=0)
        self._buttons['rotc1'].setToolTip('Clockwise Y rotation\nY Rotation {:.2f}°'.format(r[1]))
        self._buttons['rota1'].setToolTip('Counter-clockwise Y Rotation\nY Rotation {:.2f}°'.format(r[1]))

    def _zrotation(self, v: float) -> None:
        """
        Apply a rotation around the z-axis.

        Parameters
        ----------
        v : float
            rotation step in degrees.
        """
        widget = self().getFirstSliceViewWidget()
        r = list(widget.getRotations(index=0))
        r[2] += v
        widget.setRotations(tuple(r), index=0)
        self._buttons['rotc0'].setToolTip('Clockwise Z rotation\nZ Rotation {:.2f}°'.format(r[2]))
        self._buttons['rota0'].setToolTip('Counter-clockwise Z Rotation\nZ Rotation {:.2f}°'.format(r[2]))

    # Public methods

    def addOverlay(self, volume: SisypheVolume) -> None:
        """
        Add an overlay and update the transformation tooltips.
        Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        volume : SisypheVolume
            SisypheVolume to add as an overlay.
        """
        super().addOverlay(volume)
        self._updateTooltips()

    def setMoveOverlayOn(self) -> None:
        """
        Enable the 'Move overlay' interaction mode.
        In this mode, overlay volume can be moved or rotated with mouse.
        """
        widget = self().getFirstSliceViewWidget()
        widget.setMoveOverlayFlag()

    def setMoveOverlayOff(self) -> None:
        """
        Disable the 'Move overlay' interaction mode.
        In this mode, overlay volume can be moved or rotated with mouse.
        """
        widget = self().getFirstSliceViewWidget()
        # < Revision 30/10/2025
        # widget.setMoveOverlayOff()
        widget.setMoveOverlayFlag(False)
        # Revision 30/10/2025 >

    def setMoveButtonsVisibility(self, v: bool) -> None:
        """
        Set the visibility of all rigid transformation buttons.

        Parameters
        ----------
        v : bool
            True to show the buttons, False to hide them.
        """
        if isinstance(v, bool):
            for key in self._buttons:
                self._buttons[key].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getMoveButtonsVisibility(self) -> bool:
        """
        Get the visibility of the rigid transformation buttons.

        Returns
        -------
        bool
            True if the buttons are visible, False otherwise.
        """
        return self._buttons['up0'].isVisible()

    def setMoveStep(self, v: float) -> None:
        """
        Set the step value for translations (in mm) and rotations (in degrees).

        Parameters
        ----------
        v : float
            The new step value.
        """
        if isinstance(v, float): self._step = v
        else: raise TypeError('parameter type {} is not float.'.format(float))

    def getMoveStep(self) -> float:
        """
        Get the current step value for translations (in mm) and rotations (in degrees).

        Returns
        -------
        float
            The current step value.
        """
        return self._step


class IconBarOrthogonalReorientViewWidget(IconBarWidget):
    """
    IconBarOrthogonalReorientViewWidget class

    Description
    ~~~~~~~~~~~

    This widget encapsulates an OrthogonalReorientViewWidget and extends it by providing a collapsible icon bar that is
    displayed on the left.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalReorientViewWidget

    Creation: 17/04/2022
    Last revision: 10/10/2025
    """

    def __init__(self,
                 widget: OrthogonalReorientViewWidget | None = None,
                 parent: QWidget | None = None) -> None:
        """
        IconBarOrthogonalReorientViewWidget instance constructor.

        Parameters
        ----------
        widget : OrthogonalReorientViewWidget | None (optional)
            OrthogonalReorientViewWidget to encapsulate (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
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

    This widget encapsulates an OrthogonalSliceVolumeViewWidget and extends it by providing a collapsible icon bar that
    is displayed on the left.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalSliceVolumeViewWidget

    Creation: 17/04/2022
    Last revision: 10/10/2025
    """

    # Special method

    def __init__(self,
                 widget: OrthogonalSliceVolumeViewWidget | None = None,
                 parent: QWidget | None = None) -> None:
        """
        IconBarOrthogonalSliceVolumeViewWidget instance constructor.

        Parameters
        ----------
        widget : OrthogonalSliceVolumeViewWidget | None (optional)
            OrthogonalSliceVolumeViewWidget to encapsulate (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)
        if widget is None: widget = OrthogonalSliceVolumeViewWidget()
        if isinstance(widget, OrthogonalSliceVolumeViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not OrthogonalSliceVolumeViewWidget.'.format(type(widget)))
        self._hideViewWidget()

    # Public methods

    def setVolume(self, vol: SisypheVolume) -> None:
        """
        Set the SisypheVolume to be displayed. and connect the transfer function widget to the 3D VolumeViewWidget.
        Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        vol : SisypheVolume
            SisypheVolume to display.
        """
        super().setVolume(vol)
        self._transfer.setViewWidget(self().getFirstVolumeViewWidget())

    def setCameraPositionButtonAvailability(self, v: bool) -> None:
        """
        Set the availability of the camera position button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['campos'] = v
            if not v: self._icons['campos'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setTextureSettingsButtonAvailability(self, v: bool) -> None:
        """
        Set the availability of the 3D texture settings button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['texture'] = v
            if not v: self._icons['texture'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getCameraPositionButtonAvailability(self) -> bool:
        """
        Get the availability of the camera position button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['campos']

    def getTextureSettingsButtonAvailability(self) -> bool:
        """
        Get the availability of the 3D texture settings button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['texture']


class IconBarOrthogonalSliceTrajectoryViewWidget(IconBarWidget):
    """
    IconBarOrthogonalSliceTrajectoryViewWidget class

    Description
    ~~~~~~~~~~~

    This widget encapsulates an OrthogonalTrajectoryViewWidget and extends it by providing a collapsible icon bar that
    is displayed on the left.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarOrthogonalSliceTrajectoryViewWidget

    Creation: 17/04/2022
    Last Revision: 10/10/2025
    """

    def __init__(self,
                 widget: OrthogonalTrajectoryViewWidget | None = None,
                 parent: QWidget | None = None) -> None:
        """
        IconBarOrthogonalSliceTrajectoryViewWidget instance constructor.

        Parameters
        ----------
        widget : OrthogonalTrajectoryViewWidget | None (optional)
            OrthogonalTrajectoryViewWidget to encapsulate (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
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
        # noinspection PyUnresolvedReferences
        menu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyUnresolvedReferences
        menu.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
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
        # noinspection PyUnresolvedReferences
        layout.insertWidget(7, self._icons['thick'])

        # Sphere cursor

        self._icons['sphere'] = self._createButton('wcursor.png', 'cursor.png', checkable=True, autorepeat=False)
        self._icons['sphere'].setToolTip('Sphere cursor management.')

        view = self._widget[0, 0]
        menu = QMenu()
        # noinspection PyUnresolvedReferences
        menu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyUnresolvedReferences
        menu.setWindowFlag(Qt.FramelessWindowHint, True)
        # noinspection PyUnresolvedReferences
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

        # noinspection PyUnresolvedReferences
        layout.insertWidget(13, self._icons['sphere'])

        # < Revision 06/12/2024
        self._visibilityflags['thick'] = True
        self._visibilityflags['sphere'] = True
        # Revision 06/12/2024 >

    # Private methods

    def _slabThicknessChanged(self) -> None:
        """
        Updates the slab thickness and slice step in the view widget when the menu is closed.
        """
        view = self._widget[0, 1]
        if self._sthick.value() != view.getSlabThickness(): view.setSlabThickness(self._sthick.value(), signal=True)
        if self._sstep.value() != view.getSliceStep(): view.setSliceStep(self._sstep.value(), signal=True)

    def _slabTypeChanged(self, slab: int) -> None:
        """
        Updates the slab rendering mode (Min, Max, Mean, Sum).
        The signal is blended into the slab thickness using one of the following functions: mean, maximum, minimum,
        cumulative sum.

        Parameters
        ----------
        slab : int
            slab type index (0: Min, 1: Max, 2: Mean, 3: Sum).
        """
        if isinstance(slab, int):
            view = self._widget[0, 1]
            if slab == 0: view.setSlabTypeToMin(signal=True)
            elif slab == 1: view.setSlabTypeToMax(signal=True)
            elif slab == 2: view.setSlabTypeToMean(signal=True)
            elif slab == 3: view.setSlabTypeToSum(signal=True)
        else: raise TypeError('parameter type {} is not str.'.format(type(int)))

    # Public method

    def setVolume(self, vol: SisypheVolume) -> None:
        """
        Set the SisypheVolume to display, connect the transfer function widget, and reset slab properties.
        Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        vol : SisypheVolume
            SisypheVolume to display.
        """
        super().setVolume(vol)
        self._transfer.setViewWidget(self().getFirstVolumeViewWidget())
        # < Revision 18/10/2024
        # Reset slab properties
        self._sstep.setValue(1.0)
        self._sthick.setValue(0.0)
        self._widget[0, 1].setSlabThickness(0.0, signal=False)
        self._widget[0, 1].setSliceStep(1.0, signal=False)
        # Revision 18/10/2024

    def setSlabThicknessButtonAvailability(self, v: bool) -> None:
        """
        Set the availability of the slab thickness management button.

        Parameters
        ----------
        v : bool
            True to make the button available, False to hide it.
        """
        if isinstance(v, bool):
            self._visibilityflags['thick'] = v
            if not v: self._icons['thick'].setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getSlabThicknessButtonAvailability(self) -> bool:
        """
        Get the availability of the slab thickness management button.

        Returns
        -------
        bool
            True if the button is available, False otherwise.
        """
        return self._visibilityflags['thick']


class IconBarMultiSliceGridViewWidget(IconBarWidget):
    """
    IconBarMultiSliceGridViewWidget class

    Description
    ~~~~~~~~~~~

    This widget encapsulates a MultiSliceGridViewWidget and extends it by providing a collapsible icon bar that is
    displayed on the left.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarMultiSliceGridViewWidget

    Creation: 17/04/2022
    Last revision: 10/10/2025
    """

    def __init__(self,
                 widget: MultiSliceGridViewWidget | None = None,
                 rois: SisypheROICollection | None = None,
                 draw: SisypheROIDraw | None = None,
                 parent: QWidget | None = None) -> None:
        """
        IconBarMultiSliceGridViewWidget instance constructor.

        Parameters
        ----------
        widget : MultiSliceGridViewWidget | None (optional)
            MultiSliceGridViewWidget to encapsulate (default None).
        rois : SisypheROICollection | None (optional)
            collection of ROIs to be shared among the view widgets (default None).
        draw : SisypheROIDraw | Noneb(optional)
            drawing utility instance to be shared among the view widgets (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)
        if widget is None: widget = MultiSliceGridViewWidget(rois=rois, draw=draw)
        if isinstance(widget, MultiSliceGridViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not MultiSliceGridViewWidget.'.format(type(widget)))
        self._hideViewWidget()

        # < Revision 05/05/2026
        self._shcutLastAction = QShortcut('²', self)
        self._shcutLastAction.activated.connect(self.lastAction)
        # Revision 05/05/2026 >

    # Public method

    def setVolume(self, vol: SisypheVolume) -> None:
        """
        Set the SisypheVolume to display, adjust the orientation for thick anisotropic volumes to its native
        orientation. Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        vol : SisypheVolume
            SisypheVolume to display.
        """
        super().setVolume(vol)
        if vol.isThickAnisotropic():
            # Display in native orientation
            orient = vol.getNative2DOrientation()
            if orient == 1: self().setAxialOrientation()
            elif orient == 2: self().setCoronalOrientation()
            elif orient == 3: self().setSagittalOrientation()
            else: self().setAxialOrientation()

    def lastAction(self) -> None:
        if self._thumbnail is not None:
            main = self._thumbnail.getMainWindow()
            if main is not None:
                if main.isROIToolsEnabled():
                    roitools = main.getROIToolsWidget()
                    if roitools is not None:
                        lastaction = roitools.getLastAction()
                        if lastaction is not None:
                            lastaction()


class IconBarSynchronisedGridViewWidget(IconBarWidget):
    """
    IconBarSynchronisedGridViewWidget class

    Description
    ~~~~~~~~~~~

    This widget encapsulates a SynchronisedGridViewWidget and extends it by providing a collapsible icon bar that is
    displayed on the left.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarSynchronisedGridViewWidget

    Creation: 17/04/2022
    Last revision: 10/10/2025
    """

    def __init__(self,
                 widget: SynchronisedGridViewWidget | None = None,
                 rois: SisypheROICollection | None = None,
                 draw: SisypheROIDraw | None = None,
                 parent=None) -> None:
        """
        IconBarMultiSliceGridViewWidget instance constructor.

        Parameters
        ----------
        widget : SynchronisedGridViewWidget | None (optional)
            SynchronisedGridViewWidget to encapsulate (default None).
        rois : SisypheROICollection | None (optional)
            collection of ROIs to be shared among the view widgets (default None).
        draw : SisypheROIDraw | Noneb(optional)
            drawing utility instance to be shared among the view widgets (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)
        if widget is None: widget = SynchronisedGridViewWidget(rois=rois, draw=draw)
        if isinstance(widget, SynchronisedGridViewWidget): self.setViewWidget(widget)
        else: raise TypeError('parameter type {} is not SynchronisedGridViewWidget.'.format(type(widget)))
        self._hideViewWidget()

        # < Revision 05/05/2026
        self._shcutLastAction = QShortcut('²', self)
        self._shcutLastAction.activated.connect(self.lastAction)
        # Revision 05/05/2026 >

    # Private method

    def setVolume(self, vol: SisypheVolume) -> None:
        """
        Set the SisypheVolume to display, adjust the orientation for thick anisotropic volumes to its native
        orientation. Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        vol : SisypheVolume
            volume to display.
        """
        super().setVolume(vol)
        if vol.isThickAnisotropic():
            # Display in native orientation
            orient = vol.getNative2DOrientation()
            if orient == 1: self().setAxialOrientation()
            elif orient == 2: self().setCoronalOrientation()
            elif orient == 3: self().setSagittalOrientation()
            else: self().setAxialOrientation()

    def lastAction(self) -> None:
        if self._thumbnail is not None:
            main = self._thumbnail.getMainWindow()
            if main is not None:
                if main.isROIToolsEnabled():
                    roitools = main.getROIToolsWidget()
                    if roitools is not None:
                        lastaction = roitools.getLastAction()
                        if lastaction is not None:
                            lastaction()


class IconBarSliceViewWidget(IconBarWidget):
    """
    IconBarSliceViewWidget class

    Description
    ~~~~~~~~~~~

    This widget encapsulates a SliceROIViewWidget and extends it by providing a collapsible icon bar that is displayed
    on the left.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> IconBarWidget -> IconBarSliceViewWidget

    Creation: 17/04/2022
    Last revision: 10/10/2025
    """

    def __init__(self,
                 widget: SliceROIViewWidget | None = None,
                 rois: SisypheROICollection | None = None,
                 draw: SisypheROIDraw | None = None,
                 parent=None) -> None:
        """
        IconBarSliceViewWidget instance constructor.

        Parameters
        ----------
        widget : SliceROIViewWidget | None (optional)
            SliceROIViewWidget to encapsulate (default None).
        rois : SisypheROICollection | None (optional)
            collection of ROIs to be associated with the encapsulated SliceROIViewWidget (default None).
        draw : SisypheROIDraw | Noneb(optional)
            drawing utility instance to be associated with the encapsulated SliceROIViewWidget (default None).
        parent: QWidget | None (optional)
            parent widget (default None).
        """
        super().__init__(parent)
        if widget is None: widget = SliceROIViewWidget(rois=rois, draw=draw)
        if isinstance(widget, SliceROIViewWidget): self._setViewWidget(widget)
        else: raise TypeError('parameter type {} is not SliceROIViewWidget.'.format(type(widget)))
        self._hideViewWidget()

    # Private methods

    def _onMenuTools(self, action: QAction) -> None:
        """
        Handles 'Tools' menu actions for a single slice view.

        Parameters
        ----------
        action : QAction
            triggered menu action.
        """
        s = str(action.text())[0]
        w = self.getViewWidget()
        if w is not None:
            if s == 'D': w.addDistanceTool()
            elif s == 'O': w.addOrthogonalDistanceTool()
            else: w.addAngleTool()

    def _setViewWidget(self, widget: SliceROIViewWidget) -> None:
        """
        Set and configures the encapsulated SliceROIViewWidget.

        Parameters
        ----------
        widget : SliceROIViewWidget
            slice view widget to encapsulate.
        """
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
            # noinspection PyUnresolvedReferences
            layout.insertWidget(2, self._icons['sliceplus'])
            # noinspection PyUnresolvedReferences
            layout.insertWidget(2, self._icons['sliceminus'])
            # noinspection PyUnresolvedReferences
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

    def setVolume(self, vol: SisypheVolume) -> None:
        """
        Set the SisypheVolume to display, enable the visibility timer for the icon bar.
        Currently, this method calls the superclass's implementation.

        Parameters
        ----------
        vol : SisypheVolume
            volume to display.
        """
        super().setVolume(vol)
        # timer used to detect when mouse leaves icon bar
        # call timerEvent Qt event method
        self.timerEnabled()

    def removeVolume(self) -> None:
        """
        Remove the displayed SisypheVolume and disable the visibility timer.
        Currently, this method calls the superclass's implementation.
        """
        super().removeVolume()
        # timer used to detect when mouse leaves icon bar
        # call timerEvent Qt event method
        self.timerDisabled()

    def timerEvent(self, event: Optional[QTimerEvent]) -> None:
        """
        Handles timer events to manage the auto-hiding of the unpinned icon bar.
        Currently, this method overrides the superclass's implementation.

        Parameters
        ----------
        event : QTimerEvent
            timer event.
        """
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
    Last Revision: 10/03/2026
    """

    __slots__ = ['_widgets', '_index']

    # Class method

    def _KeyToIndex(self, key: str) -> int:
        """
        Converts a widget name (key) to its index in the collection.

        Parameters
        ----------
        key : str
            name of the widget to find.

        Returns
        -------
        int
            index of the widget.
        """
        keys = [k[0] for k in self._widgets]
        return keys.index(key)

    # Special methods

    def __init__(self, parent: object = None) -> None:
        """
        IconBarViewWidgetCollection instance contructor.

        Parameters
        ----------
        parent : object | None (optional)
            parent object (default None)
        """
        super().__init__(parent)
        self._widgets = list()
        self._index = 0

    """
    Private attributes

    _widgets    list[IconBarWidget]
    _index      int, index for Iterator
    """

    def __str__(self) -> str:
        """
        Special overloaded method called by the built-in str() python function.
        Returns a string representation of the collection, listing the contained widgets.

        Returns
        -------
        str
            string representation.
        """
        index = 0
        buff = 'IconBarWidget count #{}\n'.format(len(self._widgets))
        for widget in self._widgets:
            index += 1
            buff += 'IconBarWidget #{}\n'.format(index)
            buff += '{}\n'.format(str(widget))
        return buff

    def __repr__(self) -> str:
        """
        Special overloaded method called by the built-in repr() python function.
        Returns a detailed string representation for debugging.

        Returns
        -------
        str
            detailed string representation.
        """
        return 'IconBarViewWidgetCollection instance at <{}>\n'.format(str(id(self))) + self.__str__()

    # Container special methods

    def __getitem__(self, index: str | int) -> IconBarWidget:
        """
        Special overloaded container getter method.
        Retrieves a widget by its index or name.

        Parameters
        ----------
        index : str | int
            index or name of the widget to retrieve.

        Returns
        -------
        IconBarWidget
            widget at the specified index or with the specified name.
        """
        if isinstance(index, str):
            index = self._KeyToIndex(index)
        if isinstance(index, int):
            if 0 <= index < len(self._widgets): return self._widgets[index][1]
            else: raise IndexError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int or str.'.format(type(index)))

    def __setitem__(self, index: int, value: IconBarWidget):
        """
        Special overloaded container setter method.
        Replaces a widget at a specific index.

        Parameters
        ----------
        index : int
            index at which to replace the widget.
        value : IconBarWidget
            new widget to insert.
        """
        if isinstance(value, IconBarWidget):
            if isinstance(index, int):
                if 0 <= index < len(self._widgets):
                    if value.getName() not in self._widgets:
                        self._widgets[index] = [value.getName(), value]
                else: raise IndexError('parameter value {} is out of range.'.format(index))
            else: raise TypeError('first parameter type {} is not int.'.format(type(index)))
        else: raise TypeError('second parameter type {} is not IconBarWidget.'.format(type(value)))

    def __delitem__(self, index: str | int) -> None:
        """
        Special overloaded method called by the built-in del() python function.
        Deletes a widget by its index or name.

        Parameters
        ----------
        index : str | int
            index or name of the widget to delete.
        """
        if isinstance(index, str):
            index = self._KeyToIndex(index)
        if isinstance(index, int):
            if 0 <= index < len(self._widgets):
                del self._widgets[index]
            else: IndexError('parameter value {} is out of range.'.format(index))
        else: raise TypeError('parameter type {} is not int or str.'.format(index))

    def __len__(self) -> int:
        """
        Special overloaded method called by the built-in len() python function.
        Returns the number of widgets in the collection.

        Returns
        -------
        int
            number of widgets.
        """
        return len(self._widgets)

    def __contains__(self, value: str | IconBarWidget) -> bool:
        """
        Special overloaded container method called by the built-in 'in' python operator.
        Checks if a widget (by name or instance) is in the collection.

        Parameters
        ----------
        value : str | IconBarWidget
            name or instance of the widget to check for.

        Returns
        -------
        bool
            True if the widget is in the collection, False otherwise.
        """
        if isinstance(value, str):
            keys = [k[0] for k in self._widgets]
            return value in keys
        elif isinstance(value, IconBarWidget):
            values = [k[1] for k in self._widgets]
            return value in values
        else: raise TypeError('parameter type {} is not str or IconBarWidget.'.format(type(value)))

    def __iter__(self) -> Any:
        """
        Special overloaded container called by the built-in 'iter()' python iterator method.
        Returns the iterator for the collection.

        Returns
        -------
        Any
            iterator object.
        """
        self._index = 0
        return self

    def __next__(self) -> IconBarWidget:
        """
        Special overloaded container called by the built-in 'next()' python iterator method.
        Returns the next widget in an iteration.

        Returns
        -------
        IconBarWidget
            next widget.
        """
        if self._index < len(self._widgets):
            n = self._index
            self._index += 1
            return self._widgets[n][1]
        else: raise StopIteration

    # Container public methods

    def isEmpty(self) -> bool:
        """
        Check if the collection is empty.

        Returns
        -------
        bool
            True if the collection contains no widgets, False otherwise.
        """
        return len(self._widgets) == 0

    def count(self) -> int:
        """
        Return the number of widgets in the collection.

        Returns
        -------
        int
            number of widgets.
        """
        return len(self._widgets)

    def remove(self, value: int) -> None:
        """
        Remove a widget by its index.

        Parameters
        ----------
        value : int
            index of the widget to remove.
        """
        self._widgets.remove(self._widgets[value])

    def keys(self) -> list[str]:
        """
        Return a list of all widget names (keys) in the collection.

        Returns
        -------
        list[str]
            list of widget names.
        """
        return [k[0] for k in self._widgets]

    def index(self, value: str | IconBarWidget) -> int:
        """
        Find the index of a widget by its name or instance.

        Parameters
        ----------
        value : str | IconBarWidget
            name or instance of the widget to find.

        Returns
        -------
        int
            index of the widget.
        """
        if isinstance(value, IconBarWidget):
            values = [k[1] for k in self._widgets]
            return values.index(value)
        elif isinstance(value, str):
            keys = [k[0] for k in self._widgets]
            return keys.index(value)
        else: raise TypeError('parameter type {} is not str or IconBarWidget.'.format(type(value)))

    def reverse(self) -> None:
        """
        Reverse the order of widgets in the collection in-place.
        """
        self._widgets.reverse()

    def append(self, value: IconBarWidget) -> None:
        """
        Add a widget to the end of the collection if its name is not already present.

        Parameters
        ----------
        value : IconBarWidget
            widget to add.
        """
        if isinstance(value, IconBarWidget):
            if value.getName() not in self.keys():
                self._widgets.append([value.getName(), value])
                self._widgets[-1][1].NameChanged.connect(self.updateKeys)
        else: raise TypeError('parameter type {} is not IconBarWidget.'.format(type(value)))

    def insert(self, value: IconBarWidget, index: int) -> None:
        """
        Insert a widget at a specific index.

        Parameters
        ----------
        value : IconBarWidget
            widget to insert.
        index : int
            index at which to insert the widget.
        """
        if isinstance(value, IconBarWidget):
            if isinstance(index, int):
                if 0 <= index < len(self._widgets):
                    if value.getName() not in self.keys():
                        self._widgets.insert(index, [value.getName(), value])
                else: raise ValueError('parameter value {} is out of range.'.format(index))
            else: raise TypeError('parameter type {} is not int.'.format(type(index)))
        else: raise TypeError('parameter type {} is not IconBarWidget.'.format(type(value)))

    def clear(self) -> None:
        """
        Remove all widgets from the collection.
        """
        self._widgets.clear()

    def sort(self, reverse: bool = False) -> None:
        """
        Sort the widgets in the collection in-place.

        Parameters
        ----------
        reverse : bool (optional)
            If True, sorts in descending order (default is False).
        """
        self._widgets.sort(reverse=reverse)

    def copy(self) -> Any:
        """
        Create a shallow copy of the collection.

        Returns
        -------
        IconBarViewWidgetCollection
            new collection containing the same widget instances.
        """
        widgets = IconBarViewWidgetCollection()
        for widget in self._widgets:
            widgets.append(widget[1])
        return widgets

    def copyToList(self) -> list[IconBarWidget]:
        """
        Create a list containing all widgets from the collection.

        Returns
        -------
        list[IconBarWidget]
            list of the widget instances.
        """
        return [k[1] for k in self._widgets]

    def updateKeys(self) -> None:
        """
        Update the internal keys (names) based on the current names of the widgets.
        This is typically called when a widget's name changes.
        """
        for widget in self._widgets:
            widget[0] = widget[1].getName()

    # Volume methods

    def setVolume(self, vol: SisypheVolume, wait: DialogWait | None = None):
        """
        Set a SisypheVolume to display for all widgets in the collection, with optional progress dialog.
        Handles visibility for widgets based on volume properties (e.g., thick anisotropy).

        Parameters
        ----------
        vol : SisypheVolume
            SisypheVolume to set.
        wait : DialogWait | None, optional
            wait dialog to show progress (default is None).
        """
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

    def getVolume(self) -> SisypheVolume | None:
        """
        Get the SisypheVolume associated to the first widget in the collection that has one.

        Returns
        -------
        SisypheVolume | None
            associated SisypheVolume instance, or None if no widget has a volume.
        """
        # < Revision 20/02/2025
        # if self.count() > 0: return self[0].getVolume()
        # else: return None
        n = self.count()
        if n > 0:
            i: cython.int
            for i in range(n):
                if self[i].hasVolume():
                    return self[i].getVolume()
        return None
        # Revision 20/02/2025 >

    def hasVolume(self) -> bool:
        """
        Check if the first widget in the collection has an associated SisypheVolume.

        Returns
        -------
        bool
            True if the first widget has an associated volume, False otherwise.
        """
        if self.count() > 0: return self[0].hasVolume()
        else: return False

    def removeVolume(self) -> None:
        """
        Remove the associated SisypheVolume instances from all widgets in the collection.
        """
        if self.count() > 0:
            for widget in self:
                if widget.hasVolume():
                    widget.removeVolume()

    # Overlay methods

    def addOverlay(self, vol: SisypheVolume, wait: DialogWait | None = None) -> bool:
        """
        Add an overlay to all widgets, with optional progress display.
        Checks for the maximum number of overlays.

        Parameters
        ----------
        vol : SisypheVolume
            SisypheVolume to add as an overlay.
        wait : DialogWait | None, optional
            wait dialog to show progress (default is None).

        Returns
        -------
        bool
            True if the overlay was added successfully, False otherwise.
        """
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

    def removeOverlay(self, vol: SisypheVolume) -> None:
        """
        Remove a specific overlay from all widgets in the collection.

        Parameters
        ----------
        vol : SisypheVolume
            overlay volume to remove.
        """
        if isinstance(vol, SisypheVolume):
            if self.count() > 0:
                for widget in self:
                    widget.removeOverlay(vol)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def removeAllOverlays(self) -> None:
        """
        Remove all overlays from all widgets in the collection.
        """
        if self.count() > 0:
            for widget in self:
                widget.removeAllOverlays()

    def setAlignCenters(self, v: bool) -> None:
        """
        Set the center alignment for all widgets in the collection.

        Parameters
        ----------
        v : bool
            True to enable center alignment, False to disable it.
        """
        if self.count() > 0:
            for widget in self:
                widget.setAlignCenters(v)

    def alignCentersOn(self) -> None:
        """
        Enable center alignment for all widgets in the collection.
        """
        if self.count() > 0:
            for widget in self:
                widget.setAlignCentersOn()

    def alignCentersOff(self) -> None:
        """
        Disable center alignment for all widgets in the collection.
        """
        if self.count() > 0:
            for widget in self:
                widget.setAlignCentersOff()

    def getAlignCenters(self) -> bool:
        """
        Get the center alignment state in the collection.

        Returns
        -------
        bool
            The center alignment state.
        """
        return self._widgets[0].getAlignCenters()

    # ROI methods

    # < Revision 20/02/2025
    # add canDisplayROI method
    def canDisplayROI(self) -> bool:
        """
        Checks if any widget in the collection can display ROIs and has a SisypheVolume displayed.

        Returns
        -------
        bool
            True if at least one widget can display ROIs, False otherwise.
        """
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

    def getROICollection(self) -> SisypheROICollection | None:
        """
        Get the associated SisypheROICollection.

        Returns
        -------
        SisypheROICollection | None
            associated ROI collection instance, or None if not found.
        """
        # noinspection PyInconsistentReturns
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getROICollection()
                    else: return None
        return None

    def getROIDraw(self) -> SisypheROIDraw | None:
        """
        Gets the associated SisypheROIDraw instance.

        Returns
        -------
        SisypheROIDraw | None
            associated ROI drawing helper instance, or None if not found.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getDrawInstance()
                    else: return None
        return None

    def getCurrentSliceIndex(self) -> int | None:
        """
        Gets the current slice index from the first suitable widget.

        Returns
        -------
        int | None
            current slice index, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getSliceIndex()
                    else: return None
        return None

    def getSelectedSliceIndex(self) -> int | None:
        """
        Get the slice index of the selected view from the first suitable widget.

        Returns
        -------
        int | None
            The selected slice index, or None if no view is selected.
        """
        if self.count() > 0:
            for widget in self:
                # < Revision 22/12/2025
                if widget.isTimerEnabled():  # True if displayed
                # Revision 22/12/2025 >
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getSelectedViewWidget()
                        if sliceview is not None:
                            return sliceview.getSliceIndex()
                        else:
                            # < Revision 22/12/2025
                            # return None
                            sliceview =  widget().getFirstViewWidget()
                            sliceview.select(True)
                            if sliceview is not None:
                                return sliceview.getSliceIndex()
                            else: return None
                            # Revision 22/12/2025 >
        return None

    def getCurrentOrientation(self) -> int | None:
        """
        Get the current orientation from the first suitable widget.

        Returns
        -------
        int | None
            The current orientation, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getOrientation()
                    else: return None
        return None

    def updateROIDisplay(self) -> None:
        """
        Update the ROI display in all suitable widgets.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.updateROIDisplay(signal=True)

    def updateROIAttributes(self) -> None:
        """
        Update the ROI attributes (e.g., color, opacity) in all suitable widgets.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.updateROIAttributes(signal=True)

    def updateROIName(self, old: str, name: str) -> None:
        """
        Update the name of a ROI across all suitable widgets.

        Parameters
        ----------
        old : str
            old name of the ROI.
        name : str
            new name for the ROI.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    widget().updateROIName(old, name)

    def setUndoOn(self) -> None:
        """
        Enable the undo functionality for ROI drawing.
        """
        draw = self.getROIDraw()
        if draw is not None: draw.setUndoOn()

    def setUndoOff(self) -> None:
        """
        Disable the undo functionality for ROI drawing.
        """
        draw = self.getROIDraw()
        if draw is not None: draw.setUndoOff()

    def clearUndo(self) -> None:
        """
        Clear the undo history for ROI drawing.
        """
        draw = self.getROIDraw()
        if draw is not None: draw.clearLIFO()

    def setROIVisibility(self, v: bool) -> None:
        """
        Set the visibility of all ROIs in suitable widgets.

        Parameters
        ----------
        v : bool
            True to show ROIs, False to hide them.
        """
        if isinstance(v, bool):
            if self.count() > 0:
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None: sliceview.setROIVisibility(v, signal=True)
        else: raise TypeError('parameter type {} is not bool.'.format(v))

    def setActiveROI(self, roiname: str) -> None:
        """
        Set the active ROI for drawing in suitable widgets.

        Parameters
        ----------
        roiname : str
            name of the ROI to set as active.
        """
        if isinstance(roiname, str):
            if self.count() > 0:
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None:
                            if sliceview.hasVolume():
                                sliceview.setActiveROI(roiname, signal=True)
        else: raise TypeError('parameter type {} is not str.'.format(type(roiname)))

    def setBrushRadiusROI(self, radius: int = 10) -> None:
        """
        Set the radius for the ROI drawing brush in suitable widgets.

        Parameters
        ----------
        radius : int (optional)
            brush radius in pixels (default is 10).
        """
        if isinstance(radius, int):
            if self.count() > 0:
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None: sliceview.setBrushRadius(radius, signal=True)
        else: raise TypeError('parameter type {} is not int.'.format(type(radius)))

    def setNoROIFlag(self) -> None:
        """
        Deactivate all ROI drawing and editing tool flags in suitable widgets.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.setNoROIFlag(signal=True)

    def getBrushFlag(self) -> int | None:
        """
        Get the currently active brush flag/type in suitable widgets.

        Returns
        -------
        int | None
            1 for solid 2D, 2 for threshold 2D, 3 for solid 3D, 4 for threshold 3D, 0 for none.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getBrushFlag()
        return None

    def setBrushROIFlag(self, brushtype: int = 0) -> None:
        """
        Set the active ROI brush tool in suitable widgets.

        Parameters
        ----------
        brushtype : int, optional
            The type of brush to activate (0: Solid 2D, 1: Threshold 2D, 2: Solid 3D, 3: Threshold 3D). Default is 0.
        """
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

    # < Revision 26/02/2026
    def setDrawRectangleFlag(self, f: bool) -> None:
        """
        Set the flag for draw rectangle tool in ROIs in suitable widgets.

        Parameters
        ----------
        f : bool
            True to enable draw rectangle tool, False to disable it.
        """
        if self.count() > 0:
            if isinstance(f, bool):
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None: sliceview.setDrawRectangleFlag(f, signal=True)
            else: raise TypeError('parameter type {} is not bool.'.format(type(f)))
    # Revision 26/02/2026 >

    # < Revision 10/03/2026
    def setDrawThresholdRectangleFlag(self, f: bool) -> None:
        """
        Set the flag for draw by thresholding within rectangle boundaries in ROIs in suitable widgets.

        Parameters
        ----------
        f : bool
            True to enable draw tool by thresholding within rectangle, False to disable it.
        """
        if self.count() > 0:
            if isinstance(f, bool):
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None: sliceview.setDrawThresholdRectangleFlag(f, signal=True)
            else: raise TypeError('parameter type {} is not bool.'.format(type(f)))
    # Revision 10/03/2026 >

    # < Revision 26/02/2026
    def setSamFlag(self, f: bool) -> None:
        """
        Set the flag for Segment anything (SAM) tool in ROIs in suitable widgets.

        Parameters
        ----------
        f : bool
            True to enable Segment anything (SAM) tool, False to disable it.
        """
        if self.count() > 0:
            if isinstance(f, bool):
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None: sliceview.setSamFlag(f, signal=True)
            else: raise TypeError('parameter type {} is not bool.'.format(type(f)))
    # Revision 26/02/2026 >

    # < Revision 26/02/2026
    # add setSamModel method
    def setSamModel(self, model: SegmentAnything) -> None:
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    widget().setSamModel(model)
    # Revision 26/02/2026 >

    # < Revision 26/02/2026
    # add getSamModel method
    def getSamModel(self) -> SegmentAnything | None:
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    return widget().getSamModel()
        return None
    # Revision 26/02/2026 >

    # < Revision 26/02/2026
    # add hasSamModel method
    def hasSamModel(self) -> bool:
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    return widget().hasSamModel()
        return False
    # Revision 26/02/2026 >

    def setFillHolesROIFlag(self, f: bool) -> None:
        """
        Set the flag for filling holes in ROIs in suitable widgets.

        Parameters
        ----------
        f : bool
            True to enable hole filling, False to disable it.
        """
        if self.count() > 0:
            if isinstance(f, bool):
                for widget in self:
                    if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                        sliceview = widget().getFirstSliceViewWidget()
                        if sliceview is not None: sliceview.setFillHolesFlag(f, signal=True)
            else: raise TypeError('parameter type {} is not bool.'.format(type(f)))

    def set2DBlobDilateROIFlag(self) -> None:
        """
        Activate the 2D blob dilation tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked blob undergoes a 2D morphological dilatation.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobDilateFlagOn(signal=True)

    def set2DBlobErodeROIFlag(self) -> None:
        """
        Activate the 2D blob erosion tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked blob undergoes a 2D morphological erosion.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobErodeFlagOn(signal=True)

    def set2DBlobCloseROIFlag(self) -> None:
        """
        Activate the 2D blob closing tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked blob undergoes a 2D morphological closing.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobCloseFlagOn(signal=True)

    def set2DBlobOpenROIFlag(self) -> None:
        """
        Activate the 2D blob opening tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked blob undergoes a 2D morphological opening.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobOpenFlagOn(signal=True)

    def set2DBlobCopyROIFlag(self) -> None:
        """
        Activate the 2D blob copy tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked blob is copied to the clipboard.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobCopyFlagOn(signal=True)

    def set2DBlobCutROIFlag(self) -> None:
        """
        Activate the 2D blob cut tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked blob is cut to the clipboard.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobCutFlagOn(signal=True)

    def set2DBlobPasteROIFlag(self) -> None:
        """
        Activate the 2D blob paste tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the blob on the clipboard is copied wherever the cross-shaped cursor is positioned.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobPasteFlagOn(signal=True)

    def set2DBlobRemoveROIFlag(self) -> None:
        """
        Activate the 2D blob removal tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked blob is removed.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobRemoveFlagOn(signal=True)

    def set2DBlobKeepROIFlag(self) -> None:
        """
        Activate the 2D keep blob tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, all the blobs are removed except for the blob that is left-clicked.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobKeepFlagOn(signal=True)

    def set2DBlobThresholdROIFlag(self) -> None:
        """
        Activate the 2D blob thresholding tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, a threshold is apllied in the left-clicked blob.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobThresholdFlagOn(signal=True)

    def set2DFillROIFlag(self) -> None:
        """
        Activate the 2D flood fill tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked hole is filled.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DFillFlagOn(signal=True)

    def set2DRegionGrowingROIFlag(self) -> None:
        """
        Activate the 2D region growing tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked pixel is used as the seed for the region growing processing.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DRegionGrowingFlagOn(signal=True)

    def set2DRegionConfidenceROIFlag(self) -> None:
        """
        Activate the 2D confidence-connected region growing tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked pixel is used as the seed for the region confidence processing.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DRegionConfidenceFlagOn(signal=True)

    def set2DBlobRegionGrowingROIFlag(self) -> None:
        """
        Activate the 2D blob-based region growing tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked pixel of a blob is used as the seed. The region growing processing is restricted
        to the blob area.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobRegionGrowingFlagOn(signal=True)

    def set2DBlobRegionConfidenceROIFlag(self) -> None:
        """
        Activate the 2D blob-based confidence-connected region growing tool in suitable widgets.
        The processing of this 2D tool is limited to the current displayed slice.
        In this mode, the left-clicked pixel of a blob is used as the seed. The region confidence processing is
        restricted to the blob area.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set2DBlobRegionConfidenceFlagOn(signal=True)

    def set3DBlobDilateROIFlag(self) -> None:
        """
        Activate the 3D blob dilation tool in suitable widgets.
        In this mode, the left-clicked blob undergoes a 3D morphological dilatation.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobDilateFlagOn(signal=True)

    def set3DBlobErodeROIFlag(self) -> None:
        """
        Activate the 3D blob erosion tool in suitable widgets.
        In this mode, the left-clicked blob undergoes a 3D morphological erosion.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobErodeFlagOn(signal=True)

    def set3DBlobCloseROIFlag(self) -> None:
        """
        Activate the 3D blob closing tool in suitable widgets.
        In this mode, the left-clicked blob undergoes a 3D morphological closing.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobCloseFlagOn(signal=True)

    def set3DBlobOpenROIFlag(self) -> None:
        """
        Activate the 3D blob opening tool in suitable widgets.
        In this mode, the left-clicked blob undergoes a 3D morphological opening.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobOpenFlagOn(signal=True)

    def set3DBlobCopyROIFlag(self) -> None:
        """
        Activate the 3D blob copy tool in suitable widgets.
        In this mode, the left-clicked blob is copied to the clipboard.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobCopyFlagOn(signal=True)

    def set3DBlobCutROIFlag(self) -> None:
        """
        Activate the 3D blob cut tool in suitable widgets.
        In this mode, the left-clicked blob is cut to the clipboard.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobCutFlagOn(signal=True)

    def set3DBlobPasteROIFlag(self) -> None:
        """
        Activate the 3D blob paste tool in suitable widgets.
        In this mode, the blob on the clipboard is copied wherever the cross-shaped cursor is positioned.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobPasteFlagOn(signal=True)

    def set3DBlobRemoveROIFlag(self) -> None:
        """
        Activate the 3D blob removal tool in suitable widgets.
        In this mode, the left-clicked blob is removed.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobRemoveFlagOn(signal=True)

    def set3DBlobKeepROIFlag(self) -> None:
        """
        Activate the 3D keep blob tool in suitable widgets.
        In this mode, all the blobs are removed except for the blob that is left-clicked.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobKeepFlagOn(signal=True)

    def set3DBlobExpandFlagOn(self, v: float) -> None:
        """
        Activate the 3D blob expansion tool in suitable widgets.
        In this mode, the left-clicked blob is expanded with a margin.

        Parameters
        ----------
        v : float
            The expansion distance.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobExpandFlagOn(v, signal=True)

    def set3DBlobShrinkFlagOn(self, v: float) -> None:
        """
        Activate the 3D blob shrinking tool in suitable widgets.
        In this mode, the left-clicked blob is shrinked with a margin.

        Parameters
        ----------
        v : float
            The shrinking distance.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobShrinkFlagOn(v, signal=True)

    def set3DBlobThresholdROIFlag(self) -> None:
        """
        Activate the 3D blob thresholding tool in suitable widgets.
        In this mode, a threshold is apllied in the left-clicked blob.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobThresholdFlagOn(signal=True)

    def set3DFillROIFlag(self) -> None:
        """
        Activate the 3D flood fill tool in suitable widgets.
        In this mode, the left-clicked hole is filled.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DFillFlagOn(signal=True)

    def set3DRegionGrowingROIFlag(self) -> None:
        """
        Activate the 3D region growing tool in suitable widgets.
        In this mode, the left-clicked voxel is used as the seed for the region growing processing.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DRegionGrowingFlagOn(signal=True)

    def set3DRegionConfidenceROIFlag(self) -> None:
        """
        Activate the 3D confidence-connected region growing tool in suitable widgets.
        In this mode, the left-clicked pixel is used as the seed for the region confidence processing.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DRegionConfidenceFlagOn(signal=True)

    def set3DBlobRegionGrowingROIFlag(self) -> None:
        """
        Activate the 3D blob-based region growing tool in suitable widgets.
        In this mode, the left-clicked voxel of a blob is used as the seed. The region growing processing is restricted
        to the blob area.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobRegionGrowingFlagOn(signal=True)

    def set3DBlobRegionConfidenceROIFlag(self) -> None:
        """
        Activate the 3D blob-based confidence-connected region growing tool in suitable widgets.
        In this mode, the left-clicked voxel of a blob is used as the seed. The region confidence processing is
        restricted to the blob area.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.set3DBlobRegionConfidenceFlagOn(signal=True)

    def setActiveContourROIFlag(self) -> None:
        """
        Activate the active contour (snake) segmentation tool in suitable widgets.
        In this mode, the left-clicked voxel is used to initialize the active contour.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.setActiveContourFlagOn(signal=True)

    # < Revision 26/02/2026
    def getDrawRectangleFlag(self) -> bool | None:
        """
        Get the current state of the draw rectangle tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getDrawRectangleFlag()
        return None
    # Revision 26/02/2026 >

    # < Revision 10/03/2026
    def getDrawThresholdRectangleFlag(self) -> bool | None:
        """
        Get the current state of the draw tool by thresholding within rectangle boundaries flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getDrawThresholdRectangleFlag()
        return None
    # Revision 10/03/2026 >

    # < Revision 26/02/2026
    def getSamFlag(self) -> bool | None:
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getSamFlag()
        return None
    # Revision 26/02/2026 >

    def getFillHolesROIFlag(self) -> bool | None:
        """
        Get the current state of the SAM tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getFillHolesFlag()
        return None

    def get2DBlobDilateROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob dilation tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobDilateFlag()
        return None

    def get2DBlobErodeROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob erosion tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobErodeFlag()
        return None

    def get2DBlobCloseROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob closing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobCloseFlag()
        return None

    def get2DBlobOpenROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob opening tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobOpenFlag()
        return None

    def get2DBlobCopyROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob copy flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobCopyFlag()
        return None

    def get2DBlobCutROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob cut flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobCutFlag()
        return None

    def get2DBlobPasteROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob paste flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobPasteFlag()
        return None

    def get2DBlobRemoveROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob remove tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobRemoveFlag()
        return None

    def get2DBlobKeepROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D keep blob tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobKeepFlag()
        return None

    def get2DBlobThresholdROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob thresholding tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobThresholdFlag()
        return None

    def get2DFillROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D flood fill tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DFillFlag()
        return None

    def get2DRegionGrowingROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D region growing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DRegionGrowingFlag()
        return None

    def get2DRegionConfidenceROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D confidence-connected region growing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DRegionConfidenceFlag()
        return None

    def get2DBlobRegionGrowingROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob-based region growing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobRegionGrowingFlag()
        return None

    def get2DBlobRegionConfidenceROIFlag(self) -> bool | None:
        """
        Get the current state of the 2D blob-based confidence-connected region growing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get2DBlobRegionConfidenceFlag()
        return None

    def get3DBlobDilateROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob dilation tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobDilateFlag()
        return None

    def get3DBlobErodeROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob erosion tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobErodeFlag()
        return None

    def get3DBlobCloseROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob closing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobCloseFlag()
        return None

    def get3DBlobOpenROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob opening tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobOpenFlag()
        return None

    def get3DBlobCopyROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob copy flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobCopyFlag()
        return None

    def get3DBlobCutROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob cut flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobCutFlag()
        return None

    def get3DBlobPasteROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob paste flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobPasteFlag()
        return None

    def get3DBlobRemoveROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob remove flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobRemoveFlag()
        return None

    def get3DBlobKeepROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D keep blob tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobKeepFlag()
        return None

    def get3DBlobExpandFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob expansion tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobExpandFlag()
        return None

    def get3DBlobShrinkFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob shrinking tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobShrinkFlag()
        return None

    def get3DBlobThresholdROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob thresholding tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobThresholdFlag()
        return None

    def get3DFillROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D flood fill tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DFillFlag()
        return None

    def get3DRegionGrowingROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D region growing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DRegionGrowingFlag()
        return None

    def get3DRegionConfidenceROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D confidence-connected region growing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DRegionConfidenceFlag()
        return None

    def get3DBlobRegionGrowingROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob-based region growing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobRegionGrowingFlag()
        return None

    def get3DBlobRegionConfidenceROIFlag(self) -> bool | None:
        """
        Get the current state of the 3D blob-based confidence-connected region growing tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.get3DBlobRegionConfidenceFlag()
        return None

    def getActiveContourROIFlag(self) -> bool | None:
        """
        Get the current state of the active contour (snake) segmentation tool flag in suitable widgets.

        Returns
        -------
        bool | None
            state of the flag, or None if not applicable.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: return sliceview.getActiveContourFlag()
        return None

    # Mesh/Tools methods

    def getVolumeView(self) -> IconBarOrthogonalSliceVolumeViewWidget | IconBarOrthogonalSliceTrajectoryViewWidget | None:
        """
        Find and return the first 3D volume view widget in the collection.

        Returns
        -------
        IconBarOrthogonalSliceVolumeViewWidget | IconBarOrthogonalSliceTrajectoryViewWidget | None
            3D volume view widget, or None if not found.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarOrthogonalSliceVolumeViewWidget,
                                       IconBarOrthogonalSliceTrajectoryViewWidget)):
                    return widget().getFirstVolumeViewWidget()
        return None

    def getFirstSliceView(self) -> SliceViewWidget | None:
        """
        Get the first slice view widget from in the collection.

        Returns
        -------
        SliceViewWidget | None
            slice view widget, or None if the collection is empty.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, IconBarWidget):
                    return widget().getFirstSliceViewWidget()
        return None

    def getOrthogonalSliceTrajectoryViewWidget(self) -> SliceTrajectoryViewWidget | None:
        """
        Find and return the first trajectory view widget in the collection.

        Returns
        -------
        SliceTrajectoryViewWidget | None
            trajectory view widget, or None if not found.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, IconBarOrthogonalSliceTrajectoryViewWidget):
                    return widget()
        return None

    def getMultiSliceGridViewWidget(self) -> MultiSliceGridViewWidget | None:
        """
        Find and return the first multi-slice grid view widget in the collection.

        Returns
        -------
        MultiSliceGridViewWidget | None
            multi-slice grid view widget, or None if not found.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, IconBarMultiSliceGridViewWidget):
                    return widget()
        return None

    def getSynchronisedGridViewWidget(self) -> SynchronisedGridViewWidget | None:
        """
        Find and return the first synchronized grid view widget in the collection.

        Returns
        -------
        SynchronisedGridViewWidget | None
            synchronized grid view widget, or None if not found.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, IconBarSynchronisedGridViewWidget):
                    return widget()
        return None

    # < Revision 15/10/2024
    # add getProjectionViewWidget method
    def getProjectionViewWidget(self) -> MultiProjectionViewWidget | None:
        """
        Find and return the first multi-projection view widget in the collection.

        Returns
        -------
        MultiProjectionViewWidget | None
            multi-projection view widget, or None if not found.
        """
        if self.count() > 0:
            from Sisyphe.widgets.projectionViewWidget import IconBarMultiProjectionViewWidget
            for widget in self:
                if isinstance(widget, IconBarMultiProjectionViewWidget):
                    return widget()
        return None
    # Revision 15/10/2024 >

    # < Revision 11/12/2024
    # add getMultiComponentViewWidget method
    def getMultiComponentViewWidget(self) -> MultiComponentViewWidget | None:
        """
        Find and return the first multi-component view widget in the collection.

        Returns
        -------
        MultiComponentViewWidget | None
            multi-component view widget, or None if not found.
        """
        if self.count() > 0:
            from Sisyphe.widgets.multiComponentViewWidget import IconBarMultiComponentViewWidget
            for widget in self:
                if isinstance(widget, IconBarMultiComponentViewWidget):
                    return widget()
        return None
    # Revision 11/12/2024 >

    def getMeshCollection(self) -> SisypheMeshCollection | None:
        """
        Get the associated mesh collection.

        Returns
        -------
        SisypheMeshCollection | None
            mesh collection, or None if not found.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarOrthogonalSliceVolumeViewWidget,
                                       IconBarOrthogonalSliceTrajectoryViewWidget)):
                    view = widget().getFirstVolumeViewWidget()
                    if view is not None: return view.getMeshCollection()
        return None

    def getToolCollection(self) -> ToolWidgetCollection | None:
        """
        Get the associated 3D tool collection.

        Returns
        -------
        ToolWidgetCollection | None
            tool collection, or None if not found.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarOrthogonalSliceVolumeViewWidget,
                                       IconBarOrthogonalSliceTrajectoryViewWidget)):
                    view = widget().getFirstVolumeViewWidget()
                    if view is not None: return view.getToolCollection()
        return None

    def getTractCollection(self) -> SisypheTractCollection | None:
        """
        Gets the associated streamlines collection.

        Returns
        -------
        SisypheTractCollection | None
            streamlines collection, or None if not found.
        """
        if self.count() > 0:
            for widget in self:
                if isinstance(widget, (IconBarOrthogonalSliceVolumeViewWidget,
                                       IconBarOrthogonalSliceTrajectoryViewWidget)):
                    view = widget().getFirstVolumeViewWidget()
                    if view is not None: return view.getTractCollection()
        return None

    def updateRender(self) -> None:
        """
        Trigger a render update in all view widgets in the collection.
        """
        if self.count() > 0:
            for widget in self:
                widget.updateRender()
