"""
External packages/modules
-------------------------

    - Matplotlib, Graph tool, https://matplotlib.org/
    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, Medical image processing, https://simpleitk.org/
"""

from sys import platform

from os import getcwd
from os import chdir

from os.path import join
from os.path import dirname
from os.path import abspath
from os.path import splitext

from time import perf_counter

import logging

from numpy import ndarray as np_ndarray
from numpy import fliplr

from matplotlib.cm import get_cmap
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import QMimeData
from PyQt5.QtGui import QDrag
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QStackedLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QToolTip
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from SimpleITK import Image as sitkImage
from SimpleITK import Flip as sitkFlip
from SimpleITK import PermuteAxes as sitkPermuteAxes
from SimpleITK import GetArrayViewFromImage as sitkGetArrayViewFromImage

# noinspection PyCompatibility
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImage import SisypheImage
from Sisyphe.core.sisypheDicom import XmlDicom
from Sisyphe.core.sisypheSettings import SisypheFunctionsSettings
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.widgets.attributesWidgets import ItemOverlayAttributesWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogXmlDicom import DialogXmlDicom
from Sisyphe.gui.dialogEditLabels import DialogEditLabels
from Sisyphe.gui.dialogVolumeAttributes import DialogVolumeAttributes
from Sisyphe.gui.dialogGenericResults import DialogGenericResults

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> ImagePreviewWidget -> SisypheImageViewWidget -> SisypheVolumeViewWidget
    - QPushButton -> SisypheVolumeThumbnailButtonWidget
"""


class ImagePreviewWidget(QWidget):
    """
    ImagePreviewWidget class

    Description
    ~~~~~~~~~~~

    Displays thumbnail of SimpleITK image

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ImagePreviewWidget

    Last revision: 05/03/2025
    """

    _VSIZE = 16

    # Class method

    @classmethod
    def _getDefaultIconDirectory(cls):
        import Sisyphe.gui
        # < Revision 05/03/2025
        # return join(dirname(abspath(Sisyphe.gui.__file__)), 'icons')
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'baricons')
        # Revision 05/03/2025 >

    @classmethod
    def getSubButtonSize(cls):
        return cls._VSIZE

    # Special method

    """
    Private attributes

    _fig            Figure
    _axe            Axes
    _canvas         FigureCanvasQTAgg
    _lut            cmap
    _currentslice   int
    _image          ndarray
    _orient         str, 'upper' SimpleITK, 'lower' VTK, SisypheImage, SisypheVolume
    _vmin           float, lower window value
    _vmax           float, higher window value
    """

    def __init__(self, image=None, lut='gray', size=128, orient='upper', parent=None):
        super().__init__(parent)

        # Init icon

        self._icn = QLabel()
        pixmap = QPixmap(join(self._getDefaultIconDirectory(), 'wmore.png'))
        self._icn.setPixmap(pixmap.scaled(self._VSIZE, self._VSIZE, Qt.KeepAspectRatio))
        self._icn.setScaledContents(False)
        self._icn.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self._icn.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Init matplotlib figure

        self._fig = Figure()
        self._fig.set_facecolor('black')
        # noinspection PyTypeChecker
        self._axe = self._fig.add_axes([0, 0, 1, 1], frame_on=False, xmargin=0)
        self._axe.get_xaxis().set_visible(False)
        self._axe.get_yaxis().set_visible(False)
        self._canvas = FigureCanvas(self._fig)

        # Init Qt Widget

        lyout = QStackedLayout(self)
        lyout.addWidget(self._icn)
        lyout.addWidget(self._canvas)
        lyout.setStackingMode(QStackedLayout.StackAll)
        lyout.setSpacing(0)
        lyout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lyout)
        self.setBaseSize(size, size)
        self.setToolTip(str(image))

        # Convert image format to numpy ndarray

        if isinstance(image, sitkImage):
            image = sitkGetArrayViewFromImage(image)

        # Select slice if 3D ndarray
        if isinstance(image, np_ndarray):
            if image.ndim == 3:
                self._currentslice = image.shape[0] // 2
                # Init mouse events
                # noinspection PyTypeChecker
                self._canvas.mpl_connect('button_press_event', self._onClickEvent)
                # noinspection PyTypeChecker
                self._canvas.mpl_connect('motion_notify_event', self._onMouseMoveEvent)
                # noinspection PyTypeChecker
                self._canvas.mpl_connect('key_press_event', self._onKeyPressEvent)
                # noinspection PyTypeChecker
                self._canvas.mpl_connect('scroll_event', self._onWheelEvent)
            elif image.ndim == 2:
                self._currentslice = 0
            else: raise TypeError('constructor image parameter ndim is not supported.')
        else: raise TypeError('constructor image type {} is not Numpy or SitkImage.'.format(type(image)))
        self._image = image
        self._orient = orient

        # Init Lut

        self._vmin = None
        self._vmax = None
        if isinstance(lut, ListedColormap): self._lut = lut
        elif isinstance(lut, str):
            try: self._lut = get_cmap(lut, 256)
            except ValueError: self._lut = get_cmap('gray', 256)
        else: self._lut = get_cmap('gray', 256)

        # Draw image in tool

        self._canvas.setFocusPolicy(Qt.ClickFocus)
        self._canvas.setFocus()
        self._drawImage()

        # Drag and Drop

        self.setAcceptDrops(True)

    # Private method

    def _drawImage(self):
        if self._image is not None:
            if self._image.ndim == 3: mat = self._image[self._currentslice, :, :]
            else: mat = self._image
            # noinspection PyTypeChecker
            self._axe.imshow(fliplr(mat), origin=self._orient, cmap=self._lut,
                             vmin=self._vmin, vmax=self._vmax, interpolation='bilinear')
            self._canvas.draw_idle()
            QApplication.processEvents()

    # Public methods

    def setDefaultLut(self):
        self._lut = get_cmap('gray', 256)
        self._drawImage()

    def setLut(self, lut, update=True):
        if isinstance(lut, str):
            try:
                self._lut = get_cmap(lut, 256)
            except ValueError:
                self._lut = get_cmap('gray', 256)
        elif isinstance(lut, SisypheLut):
            self._lut = lut.copyToMatplotlibColormap()
        elif isinstance(lut, (ListedColormap, LinearSegmentedColormap)):
            self._lut = lut
        else:
            self._lut = get_cmap('gray', 256)
        if update: self._drawImage()

    def getLut(self):
        return self._lut

    def setRange(self, vmin, vmax, update=True):
        if vmax < vmin: vmax, vmin = vmin, vmax
        self._vmin = vmin
        self._vmax = vmax
        if update: self._drawImage()

    def getRange(self):
        return self._vmin, self._vmax

    def getFigure(self):
        return self._fig

    def getAxes(self):
        return self._axe

    def getCanvas(self):
        return self._canvas

    def getImage(self):
        return self._image

    def getCurrentSlice(self):
        return self._currentslice

    def setCurrentSlice(self, n):
        if 0 <= n < self._image.shape[0]:
            self._currentslice = n
            self._drawImage()

    def getSize(self):
        return self.size().height()

    def setSize(self, size):
        self.setBaseSize(size, size)

    def updateImage(self, image):
        if isinstance(image, np_ndarray):
            if image.shape != self._image.shape:
                self._currentslice = image.shape[0] // 2
            self._image = image
            self._drawImage()

    # Matplotlib events

    def _onWheelEvent(self, event):
        d = self._image.shape[0] - 1
        if event.button == 'up':
            if self._currentslice < d:
                self._currentslice += 1
        else:
            if self._currentslice > 0:
                self._currentslice -= 1
        self._drawImage()

    def _onKeyPressEvent(self, event):
        d = self._image.shape[0] - 1
        if event.key == 'up' or event.key == 'left':
            if self._currentslice < d:
                self._currentslice += 1
        elif event.key == 'down' or event.key == 'right':
            if self._currentslice > 0:
                self._currentslice -= 1
        self._drawImage()

    def _onClickEvent(self, event):
        pass

    def _onMouseMoveEvent(self, event):
        pass


class SisypheImageViewWidget(ImagePreviewWidget):
    """
    SisypheImagePreviewWidget class

    Description
    ~~~~~~~~~~~

    Displays thumbnail of SisypheImage/SisypheVolume

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ImagePreviewWidget -> SisypheImagePreviewWidget

    Last revision:
    """

    def __init__(self, image=None, lut='gray', size=128, parent=None):
        if isinstance(image, (SisypheImage, SisypheVolume)):
            super().__init__(image.getNumpy(), lut, size, 'lower', parent)
            self.setToolTip(str(image))
        else: raise TypeError('constructor image parameter {} is not SisypheImage or SisypheVolume.'.format(type(image)))

    # Public method

    def updateImage(self, image):
        if isinstance(image, (SisypheImage, SisypheVolume)):
            super().updateImage(image.getNumpy())
        else: raise TypeError('parameter {} is not SisypheImage or SisypheVolume.'.format(type(image)))


class SisypheVolumeViewWidget(SisypheImageViewWidget):
    """
    SisypheVolumePreviewWidget class

    Description
    ~~~~~~~~~~~

    Displays thumbnail of SisypheImage/SisypheVolume.
    Add mouse event methods.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ImagePreviewWidget -> SisypheImageViewWidget -> SisypheVolumeViewWidget

    Last revision: 11/03/2025
    """

    def __init__(self, image=None, size=128, parent=None):
        if isinstance(image, (SisypheImage, SisypheVolume)):
            lut = image.display.getLUT().copyToMatplotlibColormap()
            # noinspection PyTypeChecker
            super().__init__(image, lut, size, parent)
            self._parent = parent
        else: raise TypeError('constructor image parameter {} is not SisypheImage or SisypheVolume.'.format(type(image)))

    # Matplotlib events

    def _onClickEvent(self, event):
        # Convert matplotlib event to Qt event in the parent tool
        if self._parent:
            p = self._parent.mapFromGlobal(QCursor.pos())
            if event.dblclick:
                event = QMouseEvent(QEvent.MouseButtonDblClick, p,
                                    Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                self._parent.mouseDoubleClickEvent(event)
            else:
                self._pclick = perf_counter()
                if event.button == MouseButton.RIGHT:
                    event = QMouseEvent(QEvent.MouseButtonPress, p,
                                        Qt.RightButton, Qt.RightButton, Qt.NoModifier)
                elif event.button == MouseButton.LEFT:
                    event = QMouseEvent(QEvent.MouseButtonPress, p,
                                        Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                self._parent.mousePressEvent(event)

    def _onMouseMoveEvent(self, event):
        # Convert matplotlib event to Qt event in the parent tool
        if self._parent:
            if event.button == MouseButton.LEFT:
                event = QMouseEvent(QEvent.MouseMove, QCursor.pos(),
                                    Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                self._parent.mouseMoveEvent(event)


class SisypheVolumeThumbnailButtonWidget(QPushButton):
    """
    SisypheVolumeThumbnailButtonWidget

    Description
    ~~~~~~~~~~~

    QPushButton with thumbnail of SisypheImage/SisypheVolume.
    IO SisypheVolume management in PySisyphe environment.
    Item of the container class ToolBarThumbnail.

    Inheritance
    ~~~~~~~~~~~

    QPushButton - > SisypheVolumeThumbnailButtonWidget

    Last revision: 06/07/2025
    """

    # Special method

    """
    Private attributes

    _preview        SisypheVolumeViewWidget
    _popup          QMenu
    _action         dict[QAction]
    _dragpos0       QPoint, drag start position
    _thumbnail      ToolBarThumbnail, associated thumbnail
    _views          IconBarViewWidgetCollection, associated view widgets
    _multi          SisypheVolume
    _volume         SisypheVolume, current component volume
    _component      LabeledSpinBox
    _attributes     ItemOverlayAttributesWidget
    _lutwidget      LutWidget
    _logger         logging.Logger
    """

    def __init__(self, image=None, size=128, thumbnail=None, views=None, parent=None):
        if isinstance(image, (SisypheImage, SisypheVolume)):
            super().__init__(parent)
            self.setObjectName('ThumbnailButton')
            # < Revision 06/07/2025
            self._logger = logging.getLogger(__name__)
            # Revision 06/07/2025 >

            from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
            if isinstance(thumbnail, ToolBarThumbnail): self._thumbnail = thumbnail
            else: self._thumbnail = None

            from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
            if isinstance(views, IconBarViewWidgetCollection): self._views = views
            else: self._views = None

            # < Revision 09/12/2024
            self._multi = image
            n = self._multi.getNumberOfComponentsPerPixel()
            if n > 1:
                self._volume = self._multi.copyComponent(0)
                self._volume.setFilename(self._multi.getFilename())
                fix = len(str(n))
                suffix = '#' + str(1).zfill(fix)
                self._volume.setFilenameSuffix(suffix)
            else: self._volume = image
            self._preview = SisypheVolumeViewWidget(self._volume, size=size-32, parent=self)
            if n > 1: self._preview.setToolTip(str(self._multi))
            # Revision 09/12/2024 >
            vmin, vmax = self._volume.display.getWindow()
            self._preview.setRange(vmin, vmax)
            QApplication.processEvents()
            self._dragpos0 = None

            # Init layout

            lyout = QVBoxLayout()
            lyout.setSpacing(0)
            lyout.setContentsMargins(0, 0, 0, 0)
            lyout.addWidget(self._preview)
            lyout.setAlignment(self._preview, Qt.AlignHCenter | Qt.AlignVCenter)
            widget = QWidget()
            widget.setFixedSize(QSize(size-32, size-32))
            widget.setLayout(lyout)
            lyout = QVBoxLayout()
            lyout.setSpacing(0)
            lyout.setContentsMargins(0, 0, 0, 0)
            lyout.addWidget(widget)
            lyout.setAlignment(widget, Qt.AlignHCenter | Qt.AlignVCenter)
            self.setLayout(lyout)
            self.setFixedSize(size, size)
            self.setCheckable(True)

            # Component widget

            # < Revision 08/12/2024
            self._component = LabeledSpinBox(title='Component', fontsize=12)
            self._component.setKeyboardTracking(False)
            self._component.setRange(1, self._multi.getNumberOfComponentsPerPixel())
            self._component.setValue(1)
            self._component.setWrapping(True)
            # self._component.setFixedWidth(150)
            # < Revision 12/12/2024
            # add widget contents margins
            self._component.adjustSize()
            self._component.setContentsMargins(0, 5, 0, 5)
            # Revision 12/12/2024 >
            # noinspection PyUnresolvedReferences
            self._component.valueChanged.connect(self._componentChanged)
            # Revision 08/12/2024 >

            # Attributes widget

            self._attributes = ItemOverlayAttributesWidget(overlay=self._volume, views=self._views)
            QApplication.processEvents()

            # Init popup menu

            self._popup = QMenu(self)
            # noinspection PyTypeChecker
            self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyTypeChecker
            self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
            self._popup.setAttribute(Qt.WA_TranslucentBackground, True)
            self._action = dict()
            self._action['slices'] = QAction('Display in slice view', self)
            self._action['orthogonal'] = QAction('Display in orthogonal view', self)
            self._action['synchronised'] = QAction('Display in synchronized view', self)
            self._action['projections'] = QAction('Display in projection view', self)
            self._action['multi'] = QAction('Display in multi-component view', self)
            self._action['multi'].setVisible(n > 1)
            self._action['display'] = QAction('Display in all views', self)
            self._action['overlay'] = QAction('Display as overlay', self)
            self._action['anonymize'] = QAction('Anonymize', self)
            self._action['attributes'] = QAction('Edit attributes...', self)
            self._action['origin'] = QAction('Set origin to default', self)
            self._action['direction'] = QAction('Set directions to default', self)
            self._action['neck'] = QAction('Remove neck slices', self)
            self._action['neck'].setVisible(n == 1)
            self._action['dicom'] = QAction('View Dicom attributes...', self)
            self._action['labels'] = QAction('Edit labels...', self)
            self._action['labels'].setVisible(self._multi.getAcquisition().isLB() and n == 1)
            self._action['database'] = QAction('Add to database...', self)
            self._action['save'] = QAction('Save', self)
            self._action['saveas'] = QAction('Save as...', self)
            self._action['savecomp'] = QAction('Save current component...', self)
            self._action['savecomp'].setVisible(n > 1)
            self._action['savecompas'] = QAction('Save current component as...', self)
            self._action['savecompas'].setVisible(n > 1)
            self._action['split'] = QAction('Split multi-component...', self)
            self._action['split'].setVisible(n > 1)
            self._action['close'] = QAction('Close', self)
            self._action['acpc'] = QAction('AC-PC selection...', self)
            self._action['acpc'].setVisible(n == 1)
            self._action['frame'] = QAction('Stereotactic frame detection...', self)
            self._action['frame'].setVisible(n == 1)
            self._action['orient'] = QAction('Reorientation...', self)
            self._action['orient'].setVisible(n == 1)
            self._action['stats'] = QAction('Descriptive statistics...', self)
            self._action['wbrain'] = QAction('Brain window...', self)
            self._action['wbone'] = QAction('Bone window...', self)
            self._action['wmetal'] = QAction('Metallic window...', self)
            self._action['wauto'] = QAction('Automatic window...', self)
            self._action['wdefault'] = QAction('Default window...', self)

            v = self._multi.acquisition.isCT()
            self._action['wbrain'].setVisible(v)
            self._action['wbone'].setVisible(v)
            self._action['wmetal'].setVisible(v)
            # noinspection PyUnresolvedReferences
            self._action['slices'].triggered.connect(self.displayInSliceView)
            # noinspection PyUnresolvedReferences
            self._action['orthogonal'].triggered.connect(self.displayInOrthogonalView)
            # noinspection PyUnresolvedReferences
            self._action['synchronised'].triggered.connect(self.displayInSynchronisedView)
            # noinspection PyUnresolvedReferences
            self._action['projections'].triggered.connect(self.displayInProjectionView)
            # noinspection PyUnresolvedReferences
            self._action['multi'].triggered.connect(self.displayInMultiComponentView)
            # noinspection PyUnresolvedReferences
            self._action['display'].triggered.connect(self.displayInAllViews)
            # noinspection PyUnresolvedReferences
            self._action['overlay'].triggered.connect(self.overlay)
            # noinspection PyUnresolvedReferences
            self._action['anonymize'].triggered.connect(self.anonymize)
            # noinspection PyUnresolvedReferences
            self._action['attributes'].triggered.connect(self.editAttributes)
            # noinspection PyUnresolvedReferences
            self._action['origin'].triggered.connect(self.removeOrigin)
            # noinspection PyUnresolvedReferences
            self._action['direction'].triggered.connect(self.removeDirection)
            # noinspection PyUnresolvedReferences
            self._action['neck'].triggered.connect(self.removeNeck)
            # noinspection PyUnresolvedReferences
            self._action['dicom'].triggered.connect(self.viewDicomAttributes)
            # noinspection PyUnresolvedReferences
            self._action['labels'].triggered.connect(self.editLabels)
            # noinspection PyUnresolvedReferences
            self._action['database'].triggered.connect(self.addToDatabase)
            # noinspection PyUnresolvedReferences
            self._action['save'].triggered.connect(self.save)
            # noinspection PyUnresolvedReferences
            self._action['saveas'].triggered.connect(self.saveas)
            # noinspection PyUnresolvedReferences
            self._action['savecomp'].triggered.connect(self.saveCurrentComponent)
            # noinspection PyUnresolvedReferences
            self._action['savecompas'].triggered.connect(self.saveCurrentComponentAs)
            # noinspection PyUnresolvedReferences
            self._action['split'].triggered.connect(self.split)
            # noinspection PyUnresolvedReferences
            self._action['close'].triggered.connect(self.remove)
            # noinspection PyUnresolvedReferences
            self._action['acpc'].triggered.connect(self.acpc)
            # noinspection PyUnresolvedReferences
            self._action['frame'].triggered.connect(self.frame)
            # noinspection PyUnresolvedReferences
            self._action['orient'].triggered.connect(self.reorientation)
            # noinspection PyUnresolvedReferences
            self._action['stats'].triggered.connect(self.statistics)
            # noinspection PyUnresolvedReferences
            self._action['wbrain'].triggered.connect(self.brainWindow)
            # noinspection PyUnresolvedReferences
            self._action['wbone'].triggered.connect(self.boneWindow)
            # noinspection PyUnresolvedReferences
            self._action['wmetal'].triggered.connect(self.metallicWindow)
            # noinspection PyUnresolvedReferences
            self._action['wdefault'].triggered.connect(self.defaultWindow)
            # noinspection PyUnresolvedReferences
            self._action['wauto'].triggered.connect(self.autoWindow)
            self._popup.addAction(self._action['slices'])
            self._popup.addAction(self._action['orthogonal'])
            self._popup.addAction(self._action['synchronised'])
            self._popup.addAction(self._action['projections'])
            self._popup.addAction(self._action['multi'])
            self._popup.addAction(self._action['display'])
            self._popup.addAction(self._action['overlay'])
            self._popup.addSeparator()
            self._popup.addAction(self._action['save'])
            self._popup.addAction(self._action['saveas'])
            self._popup.addAction(self._action['savecomp'])
            self._popup.addAction(self._action['savecompas'])
            self._popup.addAction(self._action['split'])
            self._popup.addAction(self._action['close'])
            self._popup.addSeparator()
            submenu = self._popup.addMenu('Windowing')
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setAttribute(Qt.WA_TranslucentBackground, True)
            submenu.addAction(self._action['wauto'])
            submenu.addAction(self._action['wdefault'])
            submenu.addAction(self._action['wbrain'])
            submenu.addAction(self._action['wbone'])
            submenu.addAction(self._action['wmetal'])
            self._popup.addSeparator()
            self._popup.addAction(self._action['anonymize'])
            self._popup.addAction(self._action['attributes'])
            self._popup.addAction(self._action['labels'])
            self._popup.addAction(self._action['origin'])
            self._popup.addAction(self._action['direction'])
            submenu = self._popup.addMenu('Set modality')
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setAttribute(Qt.WA_TranslucentBackground, True)
            self._action['CT'] = submenu.addAction('CT (Computed Tomography)')
            # noinspection PyUnresolvedReferences
            self._action['CT'].triggered.connect(lambda dummy, m='CT': self.changeModality(m))
            self._action['LB'] = submenu.addAction('LB (Label)')
            # noinspection PyUnresolvedReferences
            self._action['LB'].triggered.connect(lambda dummy, m='LB': self.changeModality(m))
            self._action['MR'] = submenu.addAction('MR (Magnetic Resonance)')
            # noinspection PyUnresolvedReferences
            self._action['MR'].triggered.connect(lambda dummy, m='MR': self.changeModality(m))
            self._action['NM'] = submenu.addAction('NM (SPECT)')
            # noinspection PyUnresolvedReferences
            self._action['NM'].triggered.connect(lambda dummy, m='NM': self.changeModality(m))
            self._action['OT'] = submenu.addAction('OT (Other)')
            # noinspection PyUnresolvedReferences
            self._action['OT'].triggered.connect(lambda dummy, m='OT': self.changeModality(m))
            self._action['PT'] = submenu.addAction('PT (PET)')
            # noinspection PyUnresolvedReferences
            self._action['PT'].triggered.connect(lambda dummy, m='PT': self.changeModality(m))
            self._action['TP'] = submenu.addAction('TP (Template)')
            # noinspection PyUnresolvedReferences
            self._action['TP'].triggered.connect(lambda dummy, m='TP': self.changeModality(m))
            submenu = self._popup.addMenu('Datatype conversion')
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setAttribute(Qt.WA_TranslucentBackground, True)
            self._action['int8'] = submenu.addAction('int8')
            # noinspection PyUnresolvedReferences
            self._action['int8'].triggered.connect(lambda dummy, dtype='int8': self.changeDatatype(dtype))
            self._action['int16'] = submenu.addAction('int16')
            # noinspection PyUnresolvedReferences
            self._action['int16'].triggered.connect(lambda dummy, dtype='int16': self.changeDatatype(dtype))
            self._action['int32'] = submenu.addAction('int32')
            # noinspection PyUnresolvedReferences
            self._action['int32'].triggered.connect(lambda dummy, dtype='int32': self.changeDatatype(dtype))
            self._action['int64'] = submenu.addAction('int64')
            # noinspection PyUnresolvedReferences
            self._action['int64'].triggered.connect(lambda dummy, dtype='int64': self.changeDatatype(dtype))
            self._action['uint8'] = submenu.addAction('uint8')
            # noinspection PyUnresolvedReferences
            self._action['uint8'].triggered.connect(lambda dummy, dtype='uint8': self.changeDatatype(dtype))
            self._action['uint16'] = submenu.addAction('uint16')
            # noinspection PyUnresolvedReferences
            self._action['uint16'].triggered.connect(lambda dummy, dtype='uint16': self.changeDatatype(dtype))
            self._action['uint32'] = submenu.addAction('uint32')
            # noinspection PyUnresolvedReferences
            self._action['uint32'].triggered.connect(lambda dummy, dtype='uint32': self.changeDatatype(dtype))
            self._action['uint64'] = submenu.addAction('uint64')
            # noinspection PyUnresolvedReferences
            self._action['uint64'].triggered.connect(lambda dummy, dtype='uint64': self.changeDatatype(dtype))
            self._action['float32'] = submenu.addAction('float32')
            # noinspection PyUnresolvedReferences
            self._action['float32'].triggered.connect(lambda dummy, dtype='float32': self.changeDatatype(dtype))
            self._action['float64'] = submenu.addAction('float64')
            # noinspection PyUnresolvedReferences
            self._action['float64'].triggered.connect(lambda dummy, dtype='float64': self.changeDatatype(dtype))
            self._popup.addSeparator()
            self._popup.addAction(self._action['stats'])
            self._popup.addAction(self._action['dicom'])
            self._popup.addAction(self._action['database'])
            self._popup.addSeparator()
            self._popup.addAction(self._action['acpc'])
            self._popup.addAction(self._action['orient'])
            self._popup.addAction(self._action['frame'])
            self._popup.addSeparator()
            submenu = self._popup.addMenu('Flip')
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setAttribute(Qt.WA_TranslucentBackground, True)
            self._action['flipx'] = submenu.addAction('Flip left/right axis')
            # noinspection PyUnresolvedReferences
            self._action['flipx'].triggered.connect(lambda dummy, axis=0: self.flip(axis))
            self._action['flipy'] = submenu.addAction('Flip antero-posterior axis')
            # noinspection PyUnresolvedReferences
            self._action['flipy'].triggered.connect(lambda dummy, axis=1: self.flip(axis))
            self._action['flipz'] = submenu.addAction('Flip cranio-caudal axis')
            # noinspection PyUnresolvedReferences
            self._action['flipz'].triggered.connect(lambda dummy, axis=2: self.flip(axis))
            submenu.setEnabled(n == 1)
            submenu = self._popup.addMenu('Swap axis')
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setWindowFlag(Qt.FramelessWindowHint, True)
            # noinspection PyTypeChecker
            submenu.setAttribute(Qt.WA_TranslucentBackground, True)
            self._action['yxz'] = submenu.addAction('Swap axis to y,z,x')
            # noinspection PyUnresolvedReferences
            self._action['yxz'].triggered.connect(lambda dummy, axes=(1, 0, 2): self.swapAxis(axes))
            self._action['zxy'] = submenu.addAction('Swap axis to z,x,y')
            # noinspection PyUnresolvedReferences
            self._action['zxy'].triggered.connect(lambda dummy, axes=(2, 0, 1): self.swapAxis(axes))
            self._action['xzy'] = submenu.addAction('Swap axis to x,z,y')
            # noinspection PyUnresolvedReferences
            self._action['xzy'].triggered.connect(lambda dummy, axes=(0, 2, 1): self.swapAxis(axes))
            self._action['yzx'] = submenu.addAction('Swap axis to y,z,x')
            # noinspection PyUnresolvedReferences
            self._action['yzx'].triggered.connect(lambda dummy, axes=(1, 2, 0): self.swapAxis(axes))
            self._action['zyx'] = submenu.addAction('Swap axis to z,y,x')
            # noinspection PyUnresolvedReferences
            self._action['zyx'].triggered.connect(lambda dummy, axes=(2, 1, 0): self.swapAxis(axes))
            submenu.setEnabled(n == 1)
            self._popup.addAction(self._action['neck'])
            self._popup.addSeparator()

            self._action['slices'].setCheckable(True)
            self._action['orthogonal'].setCheckable(True)
            self._action['synchronised'].setCheckable(True)
            self._action['projections'].setCheckable(True)
            self._action['multi'].setCheckable(True)
            self._action['overlay'].setCheckable(True)
            self._action['slices'].setChecked(False)
            self._action['orthogonal'].setChecked(False)
            self._action['synchronised'].setChecked(False)
            self._action['projections'].setChecked(False)
            self._action['multi'].setChecked(False)
            self._action['overlay'].setChecked(False)

            # < Revision 15/10/2024
            # No orthogonal view if anisotropic voxels
            self._action['orthogonal'].setEnabled(not self._volume.isThickAnisotropic())
            # Revision 15/10/2024 >

            self._action['component'] = QWidgetAction(self)
            self._action['component'].setDefaultWidget(self._component)
            self._popup.addAction(self._action['component'])
            self._action['component'].setVisible(n > 1)

            self._action['attributes'] = QWidgetAction(self)
            self._action['attributes'].setDefaultWidget(self._attributes)
            self._popup.addAction(self._action['attributes'])

            # Lut widget

            self._lutwidget = LutWidget(size=256, view=self._views, parent=self._popup)
            # < Revision 12/12/2024
            # add widget contents margins
            self._lutwidget.setContentsMargins(0, 5, 0, 5)
            # Revision 12/12/2024 >
            self._lutwidget.setVolume(self._volume)
            # < Revision 16/10/2024
            self._lutwidget.lutChanged.connect(self._lutChanged)
            self._lutwidget.lutWindowChanged.connect(self._lutWindowChanged)
            # Revision 16/10/2024 >
            QApplication.processEvents()

            # self._action['lut'] = QWidgetAction(self)
            self._action['lut'] = QWidgetAction(self._popup)
            self._action['lut'].setDefaultWidget(self._lutwidget)
            self._popup.addAction(self._action['lut'])

            # noinspection PyUnresolvedReferences
            self._popup.aboutToShow.connect(self._onMenuShow)
            # noinspection PyUnresolvedReferences
            self._popup.aboutToHide.connect(self._onMenuHide)

            self._action['attributes'].setVisible(False)
            self._action['lut'].setVisible(True)
            self._action['overlay'].setVisible(False)
            if isinstance(self._multi, SisypheVolume): self._action['dicom'].setVisible(self._multi.hasXmlDicom())
            else: self._action['dicom'].setVisible(False)

            self._attributes.visibilityChanged.connect(lambda: self.contextMenuEvent(event=None))

            # Drag and Drop

            self.setAcceptDrops(True)
        else: raise TypeError('constructor image parameter {} is not SisypheImage or SisypheVolume.'.format(type(image)))

    # Private methods

    def _onMenuShow(self):
        if not self.hasReference(): self._action['overlay'].setChecked(False)
        self._action['display'].setVisible(not self.isReference())
        self._action['overlay'].setVisible(self.hasReference() and not self.isReference())
        self._action['attributes'].setVisible(self.isOverlaid())
        # < Revision 30/07/2024
        self._action['labels'].setVisible(self._multi.acquisition.isLB())
        # Revision 30/07/2024 >
        # self._action['lut'].setVisible(self.isReference() or self.isOverlaid())
        # if self._volume is not None: self._lutwidget.setVolume(self._volume)

    def _onMenuHide(self):
        if self._volume is not None:
            vmin, vmax = self._volume.display.getWindow()
            self._preview.setRange(vmin, vmax, update=False)
            self._preview.setLut(self._volume.display.getLUT().copyToMatplotlibColormap())

    def _getWidgetCenter(self):
        return self.mapToGlobal(self.rect().center())

    def _registration(self, moving):
        r = None
        if self.hasMainWindow():
            if self._volume.getID() in moving.getTransforms():
                r = messageBox(self.getMainWindow(),
                               'Registration',
                               '{} and {} are already registered.\n'
                               'Do you want to start a new registration ?'.format(self._volume.getBasename(),
                                                                                  moving.getBasename()),
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.No: return
            if r is None:
                r = messageBox(self.getMainWindow(),
                               'Registration',
                               'Do you want to register {} and {} ?'.format(self._volume.getBasename(),
                                                                            moving.getBasename()),
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes:
                    # noinspection PyTypeChecker
                    self.getMainWindow().rigidRegistration(fixed=self._volume, moving=moving)

    # < Revision 17/10/2024
    # add _lutChanged method
    def _lutChanged(self):
        if self.isDisplayedInProjectionView():
            if self.hasViewsWidget():
                w = self.getViewsWidget().getProjectionViewWidget()
                if w is not None: w.updateLutFromReference()
        # < Revision 13/12/2024
        elif self.isDisplayedInMultiComponentView():
            if self.hasViewsWidget():
                w = self.getViewsWidget().getMultiComponentViewWidget()
                if w is not None: w.updateLut(self._volume.display.getLUT())
        # Revision 13/12/2024 >
    # Revision 17/10/2024 >

    # < Revision 16/10/2024
    # add _lutWindowChanged method
    def _lutWindowChanged(self):
        if self.isDisplayedInProjectionView():
            if self.hasViewsWidget():
                w = self.getViewsWidget().getProjectionViewWidget()
                if w is not None: w.updateWindowingFromReference()
        # < Revision 13/12/2024
        elif self.isDisplayedInMultiComponentView():
            if self.hasViewsWidget():
                w = self.getViewsWidget().getMultiComponentViewWidget()
                if w is not None: w.updateLut(self._volume.display.getLUT())
        # Revision 13/12/2024 >
    # Revision 16/10/2024 >

    # < Revision 20/10/2024
    # add _updateViewsVisibility method
    def _updateViewsVisibility(self):
        if self.hasMainWindow():
            self.getMainWindow().setSliceViewVisibility(self._action['slices'].isChecked())
            self.getMainWindow().setOrthogonalViewVisibility(self._action['orthogonal'].isChecked())
            self.getMainWindow().setSynchronisedViewVisibility(self._action['synchronised'].isChecked())
            self.getMainWindow().setProjectionViewVisibility(self._action['projections'].isChecked())
            # < Revision 13/12/2024
            # add multi-component view visibility
            self.getMainWindow().setComponentViewVisibility(self._action['multi'].isChecked())
            # Revision 13/12/2024 >
    # Revision 20/10/2024 >

    # < Revision 15/10/2024
    # add _updateDockVisibility method
    def _updateDockVisibility(self):
        if self.hasMainWindow():
            v = self._action['slices'].isChecked() or \
                self._action['synchronised'].isChecked()
            self.getMainWindow().setROIListEnabled(v)
            v = self._action['orthogonal'].isChecked()
            self.getMainWindow().setMeshListEnabled(v)
            self.getMainWindow().setTargetListEnabled(v)
            self.getMainWindow().setTrackingListEnabled(v)
    # Revision 15/10/2024 >

    # < Revision 09/12/2024
    # add _componentChanged method
    def _componentChanged(self, v: int):
        previous = self._volume
        self._volume = self._multi.copyComponent(v - 1)
        self._volume.display.setLUT(self._lutwidget.getLut())
        self._volume.setFilename(self._multi.getFilename())
        fix = len(str(self._multi.getNumberOfComponentsPerPixel()))
        suffix = '#' + str(v).zfill(fix)
        self._volume.setFilenameSuffix(suffix)
        # update preview
        self._preview.updateImage(self._volume)
        self._preview.setToolTip(str(self._multi))
        # update lutwidget
        self._lutwidget.setVolume(self._volume)
        # update views
        if self.isReference(): self.updateDisplay(replace=True)
        elif self.isOverlaid():
            self._views.removeOverlay(previous)
            self.overlay()
    # Revision 09/12/2024 >

    # Public methods

    def setSize(self, s):
        if isinstance(s, int):
            self.setFixedSize(s, s)
            self._preview.setSize(s - 32)
            self.layout().itemAt(0).widget().setFixedSize(QSize(s-32, s-32))
        else: raise TypeError('parameter  type {} is not int.'.format(type(s)))

    def getSize(self):
        return self.height()

    def getThumbnailToolbar(self):
        return self._thumbnail

    def setThumbnailToolbar(self, w):
        from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
        if isinstance(w, ToolBarThumbnail):
            self._thumbnail = w
        else: raise TypeError('parameter type {} is not ToolBarThumbnail.'.format(type(w)))

    def hasThumbnailToolbar(self):
        return self._thumbnail is not None

    def getViewsWidget(self):
        return self._views

    def setViewsWidget(self, w):
        from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
        if isinstance(w, IconBarViewWidgetCollection): self._views = w
        else: raise TypeError('parameter type {} is not IconBarViewWidgetCollection.'.format(type(w)))

    def hasViewsWidget(self):
        return self._views is not None

    def getMainWindow(self):
        if self._thumbnail is not None:
            return self._thumbnail.getMainWindow()
        else: return None

    def hasMainWindow(self):
        return self._thumbnail.getMainWindow() is not None

    def getActions(self):
        return self._action

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def editAttributes(self):
        dialog = DialogVolumeAttributes(vol=self._multi)
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(dialog, c)
        dialog.exec()
        self._preview.setToolTip(str(self._multi))
        if self._multi.getNumberOfComponentsPerPixel() > 1:
            self._volume.copyAttributesFrom(self._multi)
        else: self._volume = self._multi
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def viewDicomAttributes(self):
        if self._volume.hasXmlDicom():
            filename = splitext(self._multi.getFilename())[0] + XmlDicom.getFileExt()
            dialog = DialogXmlDicom(filename)
            if platform == 'win32':
                import pywinstyles
                cl = self.palette().base().color()
                c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                pywinstyles.change_header_color(dialog, c)
            dialog.exec()
    # Revision 10/12/2024 >

    def editLabels(self):
        if self._multi.getNumberOfComponentsPerPixel() == 1:
            if self._volume.getAcquisition().isLB():
                dialog = DialogEditLabels()
                if platform == 'win32':
                    import pywinstyles
                    cl = self.palette().base().color()
                    c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                    pywinstyles.change_header_color(dialog, c)
                dialog.setVolume(self._volume)
                dialog.exec()
                self._multi = self._volume

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def addToDatabase(self):
        if self.hasMainWindow():
            database = self.getMainWindow().getDatabase()
            if database is not None: database.addVolumes(self._multi)
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def save(self):
        if self._multi.hasFilename():
            # < Revision 13/12/2024
            if self._multi != self._volume:
                self._multi.display.setLUT(self._lutwidget.getLut())
            # Revision 13/12/2024 >
            try: self._multi.save()
            except Exception as err: messageBox(self, 'Save PySisyphe volume', '{}'.format(err))
            mainwindow = self.getMainWindow()
            if mainwindow is not None: mainwindow.setStatusBarMessage('{} saved.'.format(self._multi.getBasename()))
            self._logger.info('Save {}'.format(self._multi.getFilename()))
            self._preview.setToolTip(str(self._multi))
        else: self.saveas()
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def saveas(self):
        title = 'Save PySisyphe volume'
        if self._multi.hasFilename(): filename = self._multi.getFilename()
        else: filename = getcwd()
        filename = QFileDialog.getSaveFileName(self, title, filename, '*.xvol')[0]
        if filename:
            chdir(dirname(filename))
            QApplication.processEvents()
            # < Revision 13/12/2024
            if self._multi != self._volume:
                self._multi.display.setLUT(self._lutwidget.getLut())
            # Revision 13/12/2024 >
            try: self._multi.saveAs(filename)
            except Exception as err:
                messageBox(self, 'Save PySisyphe volume', 'error : {}'.format(err))
            mainwindow = self.getMainWindow()
            if mainwindow is not None: mainwindow.setStatusBarMessage('{} saved.'.format(self._multi.getBasename()))
            self._logger.info('Save {}'.format(self._multi.getFilename()))
            self._preview.setToolTip(str(self._multi))
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # add saveComponent method
    def saveCurrentComponent(self):
        if self._volume.hasFilename():
            try: self._multi.save()
            except Exception as err: messageBox(self, 'Save PySisyphe volume', '{}'.format(err))
            mainwindow = self.getMainWindow()
            if mainwindow is not None: mainwindow.setStatusBarMessage('{} saved.'.format(self._volume.getBasename()))
        else: self.saveas()
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # add saveComponentAs method
    def saveCurrentComponentAs(self):
        title = 'Save PySisyphe volume'
        if self._volume.hasFilename(): filename = self._volume.getFilename()
        else: filename = getcwd()
        filename = QFileDialog.getSaveFileName(self, title, filename, '*.xvol')[0]
        if filename:
            chdir(dirname(filename))
            QApplication.processEvents()
            try: self._volume.saveAs(filename)
            except Exception as err:
                messageBox(self, 'Save PySisyphe volume', 'error : {}'.format(err))
            mainwindow = self.getMainWindow()
            if mainwindow is not None: mainwindow.setStatusBarMessage('{} saved.'.format(self._volume.getBasename()))
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # add split method
    def split(self):
        n = self._multi.getNumberOfComponentsPerPixel()
        if n > 1:
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Split {}'.format(self._multi.getBasename()))
            wait.setProgressRange(0, n)
            wait.progressVisibilityOn()
            self._logger.info('Split {}'.format(self._multi.getBasename()))
            fix = len(str(n))
            for i in range(n):
                try:
                    vol = self._multi.copyComponent(i)
                    vol.copyAttributesFrom(self._multi)
                    suffix = '#' + str(i).zfill(fix)
                    vol.setFilename(self._multi.getFilename())
                    vol.setFilenameSuffix(suffix)
                    wait.setInformationText('Split {}\nSave {}'.format(self._multi.getBasename(), vol.getBasename()))
                    wait.incCurrentProgressValue()
                    vol.save()
                    self._logger.info('  Save {}'.format(vol.getBasename()))
                except Exception as err:
                    messageBox(self, 'Split', '{}'.format(err))
                    break
            wait.close()
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def remove(self):
        if self._thumbnail is not None: self._thumbnail.removeVolume(self._multi)
    # Revision 10/12/2024 >

    def getNotDisplayedViewsCount(self) -> int:
        keys = ('slices', 'orthogonal', 'synchronised', 'projections', 'multi')
        n = 0
        for k in keys:
            if not self._action[k].isChecked(): n += 1
        return n

    # < Revision 19/10/2024
    def displayInAllViews(self):
        if self._views is not None:
            n = self.getNotDisplayedViewsCount()
            if n > 0:
                wait = DialogWait(title='Display volume...')
                wait.open()
                wait.setInformationText('{} display...'.format(self._volume.getBasename()))
                wait.setProgressRange(0, n)
                wait.setCurrentProgressValue(0)
                wait.setProgressVisibility(n > 1)
                QApplication.processEvents()
                """

                Volume is not displayed

                """
                # Display in slice view widget
                if not self.isChecked():
                    self.displayInSliceView(moveto=True, update=False, wait=wait)
                    wait.incCurrentProgressValue()
                """

                Volume is already displayed

                """
                # Display in slice view widget
                if not self._action['slices'].isChecked():
                    self._action['slices'].setChecked(True)
                    self.displayInSliceView(moveto=False, update=False, wait=wait)
                    wait.incCurrentProgressValue()
                # Display in orthogonal view widget
                if not self._action['orthogonal'].isChecked():
                    if self._volume.isThickAnisotropic():
                        self._action['orthogonal'].setChecked(False)
                        self._views['orthogonal'].setEnabled(False)
                    else:
                        self._views['orthogonal'].setEnabled(True)
                        self._action['orthogonal'].setChecked(True)
                        self.displayInOrthogonalView(moveto=False, update=False, wait=wait)
                    wait.incCurrentProgressValue()
                # Display in synchronised view widget
                if not self._action['synchronised'].isChecked():
                    self._action['synchronised'].setChecked(True)
                    self.displayInSynchronisedView(moveto=False, update=False, wait=wait)
                    wait.incCurrentProgressValue()
                # Display in projection view widget
                if not self._action['projections'].isChecked():
                    self._action['projections'].setChecked(True)
                    self.displayInProjectionView(moveto=False, update=False, wait=wait)
                    wait.incCurrentProgressValue()
                wait.close()
    # Revision 19/10/2024 >

    # < Revision 19/10/2024
    # add displayInSliceView method
    def displayInSliceView(self,
                           moveto: bool = True,
                           update: bool = False,
                           wait: DialogWait | None = None):
        if self._views is not None:
            if wait is None:
                wait = DialogWait(title='Display volume...')
                wait.open()
                wait.setInformationText('{} slice view display...'.format(self._volume.getBasename()))
                QApplication.processEvents()
                flag = True
            else: flag = False
            if not self.isChecked():
                """

                Volume is not displayed

                """
                # Hide slice view widget during update
                self._views['slices'].viewWidgetVisibleOff()
                # Clear all dock widgets
                if self.hasMainWindow():
                    self.getMainWindow().clearDockListWidgets()
                # Remove volume/overlay(s)/ROI(s) from all view widgets
                # self._views['slices'].removeVolume()
                self._views.removeVolume()
                # Remove all overlay flags from thumbnail
                if self.hasThumbnailToolbar():
                    self.getThumbnailToolbar().removeAllOverlays()
                # Display current volume in slice view widget
                self._views['slices'].setVolume(self._volume)
                # Set display flag, button border in blue
                self.setChecked(True)
                # < Revision 02/06/2025
                # move button to first position
                if self.hasThumbnailToolbar():
                    self.getThumbnailToolbar().moveSelectedToFisrt()
                # Revision 02/06/2025 >
                # Update other SisypheVolumeThumbnailButtonWidget in thumbnail
                if self.hasThumbnailToolbar():
                    self.getThumbnailToolbar().updateWidgets()
                # Show slice view widget
                self._views['slices'].viewWidgetVisibleOn()
                if self.hasMainWindow():
                    # Enable ListROIAttributesWidget in dock
                    self.getMainWindow().setROIListEnabled(True)
                    # Set slice view widget visibility
                    self._updateViewsVisibility()
                    if moveto:
                        self.getMainWindow().showSliceView()
                        self.getMainWindow().updateTimers()
            else:
                """
        
                Volume is already displayed
        
                """
                if self._action['slices'].isChecked() and not update:
                    """

                    Volume is not already displayed in slice view widget

                    """
                    # Hide slice view widget during update
                    self._views['slices'].viewWidgetVisibleOff()
                    # Remove overlay(s) from slice view widget
                    self._views['slices'].removeAllOverlays()
                    # Display current volume in slice view widget
                    self._views['slices'].setVolume(self._volume)
                    # Display ROI, ROI collection is shared between view widgets
                    if self.isDisplayedInSynchronisedView():
                        # noinspection PyUnresolvedReferences
                        if self._views['synchronised']().getFirstSliceViewWidget().hasROI():
                            # noinspection PyUnresolvedReferences
                            self._views['slices']().getFirstSliceViewWidget().updateROIDisplay(signal=True)
                            # noinspection PyUnresolvedReferences
                            roi = self._views['synchronised']().getFirstSliceViewWidget().getActiveROI()
                            # noinspection PyUnresolvedReferences
                            self._views['slices']().getFirstSliceViewWidget().setActiveROI(roi, signal=True)
                    # Display overlay(s) in slice view widget
                    if self.hasThumbnailToolbar():
                        overlays = self.getThumbnailToolbar().getOverlays()
                        n = len(overlays)
                        if n > 0:
                            for i in range(n):
                                self._views['slices'].addOverlay(overlays[i])
                    # Show slice view widget
                    self._views['slices'].viewWidgetVisibleOn()
                    if self.hasMainWindow():
                        # Enable ListROIAttributesWidget in dock
                        self.getMainWindow().setROIListEnabled(True)
                        # Set slice view widget visibility
                        if moveto:
                            self.getMainWindow().showSliceView()
                            self.getMainWindow().updateTimers()
                        else: self.getMainWindow().setSliceViewVisibility(True)
                elif update:
                    """

                    Volume is already displayed in slice view widget

                    """
                    previous = self._views['slices'].getVolume()
                    if previous.hasSameFieldOfView(self._volume):
                        # Display current volume in slice view widget
                        self._views['slices'].replaceVolume(self._volume)
                        # Set slice view widget visibility
                        if moveto:
                            self.getMainWindow().showSliceView()
                            self.getMainWindow().updateTimers()
                self._logger.info('Slice view display {}'.format(self._volume.getBasename()))
            if flag: wait.close()
        self._action['slices'].blockSignals(True)
        self._action['slices'].setChecked(True)
        self._action['slices'].blockSignals(False)
    # Revision 19/10/2024 >

    # < Revision 19/10/2024
    # add displayInOrthogonalView method
    def displayInOrthogonalView(self,
                                moveto: bool = True,
                                update: bool = False,
                                wait: DialogWait | None = None):
        if self._views is not None:
            if self._action['orthogonal'].isChecked():
                if wait is None:
                    wait = DialogWait(title='Display volume...')
                    wait.open()
                    wait.setInformationText('{} orthogonal view display...'.format(self._volume.getBasename()))
                    QApplication.processEvents()
                    flag = True
                else: flag = False
                if not self.isChecked():
                    """

                    Volume is not displayed

                    """
                    # Hide orthogonal view widget during update
                    self._views['orthogonal'].viewWidgetVisibleOff()
                    # Clear all dock widgets
                    if self.hasMainWindow():
                        self.getMainWindow().clearDockListWidgets()
                    # Remove volume and overlay(s) from orthogonal all view widgets
                    # self._views['orthogonal'].removeVolume()
                    self._views.removeVolume()
                    # Remove all overlay flags from thumbnail
                    if self.hasThumbnailToolbar():
                        self.getThumbnailToolbar().removeAllOverlays()
                    # Display current volume in orthogonal view widget
                    self._views['orthogonal'].setVolume(self._volume)
                    # Set display flag
                    self.setChecked(True)
                    # < Revision 02/06/2025
                    # move button to first position
                    if self.hasThumbnailToolbar():
                        self.getThumbnailToolbar().moveSelectedToFisrt()
                    # Revision 02/06/2025 >
                    # Update other SisypheVolumeThumbnailButtonWidget in thumbnail
                    if self.hasThumbnailToolbar():
                        self.getThumbnailToolbar().updateWidgets()
                    # Show orthogonal view widget
                    self._views['orthogonal'].viewWidgetVisibleOn()
                    if self.hasMainWindow():
                        # Enable dock widgets
                        self.getMainWindow().setMeshListEnabled(True)
                        self.getMainWindow().setTargetListEnabled(True)
                        self.getMainWindow().setTrackingListEnabled(True)
                        # Set orthogonal view widget visibility
                        self._updateViewsVisibility()
                        if moveto:
                            self.getMainWindow().showOrthogonalView()
                            self.getMainWindow().updateTimers()
                else:
                    """

                    Volume is already displayed

                    """
                    if self._action['orthogonal'].isChecked() and not update:
                        """

                        Volume is not already displayed in orthogonal view widget

                        """
                        # Hide orthogonal view widget during update
                        self._views['orthogonal'].viewWidgetVisibleOff()
                        # Remove overlay(s) from slice view widget
                        self._views['orthogonal'].removeAllOverlays()
                        # Display current volume in orthogonal view widget
                        self._views['orthogonal'].setVolume(self._volume)
                        # Display overlay(s) in orthogonal view widget
                        if self.hasThumbnailToolbar():
                            overlays = self.getThumbnailToolbar().getOverlays()
                            n = len(overlays)
                            if n > 0:
                                for i in range(n):
                                    self._views['orthogonal'].addOverlay(overlays[i])
                        # Show orthogonal view widget
                        self._views['orthogonal'].viewWidgetVisibleOn()
                        if self.hasMainWindow():
                            # Enable dock widgets
                            self.getMainWindow().setMeshListEnabled(True)
                            self.getMainWindow().setTargetListEnabled(True)
                            self.getMainWindow().setTrackingListEnabled(True)
                            # Set orthogonal view widget visibility
                            if moveto:
                                self.getMainWindow().showOrthogonalView()
                                self.getMainWindow().updateTimers()
                            else: self.getMainWindow().setOrthogonalViewVisibility(True)
                    elif update:
                        """

                        Volume is already displayed in orthogonal view widget

                        """
                        previous = self._views['orthogonal'].getVolume()
                        if previous.hasSameFieldOfView(self._volume):
                            # Display current volume in slice view widget
                            self._views['orthogonal'].replaceVolume(self._volume)
                            # Set orthogonal view widget visibility
                            if moveto:
                                self.getMainWindow().showOrthogonalView()
                                self.getMainWindow().updateTimers()
                    self._logger.info('Orthogonal view display {}'.format(self._volume.getBasename()))
                if flag: wait.close()
        self._action['orthogonal'].blockSignals(True)
        self._action['orthogonal'].setChecked(True)
        self._action['orthogonal'].blockSignals(False)
    # Revision 19/10/2024 >

    # < Revision 15/10/2024
    # add displayInSynchronisedView method
    def displayInSynchronisedView(self,
                                  moveto: bool = True,
                                  update: bool = False,
                                  wait: DialogWait | None = None):
        if self._views is not None:
            if self._action['synchronised'].isChecked():
                if wait is None:
                    wait = DialogWait(title='Display volume...')
                    wait.open()
                    wait.setInformationText('{} synchronised view display...'.format(self._volume.getBasename()))
                    QApplication.processEvents()
                    flag = True
                else: flag = False
                if not self.isChecked():
                    """

                    Volume is not displayed

                    """
                    # Hide synchronised view widget during update
                    self._views['synchronised'].viewWidgetVisibleOff()
                    # Clear all dock widgets
                    if self.hasMainWindow():
                        self.getMainWindow().clearDockListWidgets()
                    # Remove volume/overlay(s)/ROI(s) from all view widgets
                    # self._views['synchronised'].removeVolume()
                    self._views.removeVolume()
                    # Remove all overlay flags from thumbnail
                    if self.hasThumbnailToolbar():
                        self.getThumbnailToolbar().removeAllOverlays()
                    # Display current volume in synchronised view widget
                    self._views['synchronised'].setVolume(self._volume)
                    # Set display flag
                    self.setChecked(True)
                    # < Revision 02/06/2025
                    # move button to first position
                    if self.hasThumbnailToolbar():
                        self.getThumbnailToolbar().moveSelectedToFisrt()
                    # Revision 02/06/2025 >
                    # Update other SisypheVolumeThumbnailButtonWidget in thumbnail
                    if self.hasThumbnailToolbar():
                        self.getThumbnailToolbar().updateWidgets()
                    # Show synchronised view widget
                    self._views['synchronised'].viewWidgetVisibleOn()
                    if self.hasMainWindow():
                        # Enable ListROIAttributesWidget in dock
                        self.getMainWindow().setROIListEnabled(True)
                        # Set synchronised view widget visibility
                        self._updateViewsVisibility()
                        if moveto:
                            self.getMainWindow().showSynchronisedView()
                            self.getMainWindow().updateTimers()
                else:
                    """

                    Volume is already displayed

                    """
                    if self._action['synchronised'].isChecked() and not update:
                        """

                        Volume is not already displayed in synchronised view widget

                        """
                        # Hide synchronised view widget during update
                        self._views['synchronised'].viewWidgetVisibleOff()
                        # Remove overlay(s) from slice view widget
                        self._views['synchronised'].removeAllOverlays()
                        # Display current volume in synchronised view widget
                        self._views['synchronised'].setVolume(self._volume)
                        # Display ROI, ROI collection is shared between view widgets
                        if self.isDisplayedInSliceView():
                            # noinspection PyUnresolvedReferences
                            if self._views['slices']().getFirstSliceViewWidget().hasROI():
                                # noinspection PyUnresolvedReferences
                                self._views['synchronised']().getFirstSliceViewWidget().updateROIDisplay(signal=True)
                                # noinspection PyUnresolvedReferences
                                roi = self._views['slices']().getFirstSliceViewWidget().getActiveROI()
                                # noinspection PyUnresolvedReferences
                                self._views['synchronised']().getFirstSliceViewWidget().setActiveROI(roi, signal=True)
                        # Display overlay(s) in synchronised view widget
                        if self.hasThumbnailToolbar():
                            overlays = self.getThumbnailToolbar().getOverlays()
                            n = len(overlays)
                            if n > 0:
                                for i in range(n):
                                    self._views['synchronised'].addOverlay(overlays[i])
                        # Show synchronised view widget
                        self._views['synchronised'].viewWidgetVisibleOn()
                        if self.hasMainWindow():
                            # Enable ListROIAttributesWidget in dock
                            self.getMainWindow().setROIListEnabled(True)
                            # Set synchronised view widget visibility
                            if moveto:
                                self.getMainWindow().showSynchronisedView()
                                self.getMainWindow().updateTimers()
                            else: self.getMainWindow().setSynchronisedViewVisibility(True)
                    elif update:
                        """

                        Volume is already displayed in synchronised view widget

                        """
                        previous = self._views['synchronised'].getVolume()
                        if previous.hasSameFieldOfView(self._volume):
                            # Display current volume in synchronised view widget
                            self._views['synchronised'].replaceVolume(self._volume)
                            # Set synchronised view widget visibility
                            if moveto:
                                self.getMainWindow().showSynchronisedView()
                                self.getMainWindow().updateTimers()
                    self._logger.info('Synchronized view display {}'.format(self._volume.getBasename()))
                if flag: wait.close()
        self._action['synchronised'].blockSignals(True)
        self._action['synchronised'].setChecked(True)
        self._action['synchronised'].blockSignals(False)
    # Revision 19/10/2024 >

    # < Revision 19/10/2024
    # add displayInProjectionView method
    def displayInProjectionView(self,
                                moveto: bool = True,
                                update: bool = False,
                                wait: DialogWait | None = None):
        if self._views is not None:
            if self._action['projections'].isChecked():
                if wait is None:
                    wait = DialogWait(title='Display volume...')
                    wait.open()
                    wait.setInformationText('{} projection view display...'.format(self._volume.getBasename()))
                    QApplication.processEvents()
                    flag = True
                else: flag = False
                if not self.isChecked():
                    """

                    Volume is not displayed

                    """
                    # Hide projection view widget during update
                    self._views['projections'].viewWidgetVisibleOff()
                    # Clear all dock widgets
                    if self.hasMainWindow():
                        self.getMainWindow().clearDockListWidgets()
                    # Remove volume from all view widgets
                    # self._views['projections'].removeVolume()
                    self._views.removeVolume()
                    # Remove all overlay flags from thumbnail
                    if self.hasThumbnailToolbar():
                        self.getThumbnailToolbar().removeAllOverlays()
                    # Display current volume in projection view widget
                    self._views['projections'].setVolume(self._volume)
                    # Set display flag
                    self.setChecked(True)
                    # < Revision 02/06/2025
                    # move button to first position
                    if self.hasThumbnailToolbar():
                        self.getThumbnailToolbar().moveSelectedToFisrt()
                    # Revision 02/06/2025 >
                    # Update other SisypheVolumeThumbnailButtonWidget in thumbnail
                    if self.hasThumbnailToolbar():
                        self.getThumbnailToolbar().updateWidgets()
                    # Show projection view widget
                    self._views['projections'].viewWidgetVisibleOn()
                    if self.hasMainWindow():
                        # Set projection view widget visibility
                        self._updateViewsVisibility()
                        if moveto:
                            self.getMainWindow().showProjectionView()
                            self.getMainWindow().updateTimers()
                else:
                    """

                    Volume is already displayed

                    """
                    if self._action['projections'].isChecked() and not update:
                        """

                        Volume is not already displayed in projection view widget

                        """
                        # Hide projection view widget during update
                        self._views['projections'].viewWidgetVisibleOff()
                        # Display current volume in orthogonal view widget
                        self._views['projections'].setVolume(self._volume)
                        # Show synchronised view widget
                        self._views['projections'].viewWidgetVisibleOn()
                        if self.hasMainWindow():
                            # Set projection view widget visibility
                            if moveto:
                                self.getMainWindow().showProjectionView()
                                self.getMainWindow().updateTimers()
                            else: self.getMainWindow().setProjectionViewVisibility(True)
                    elif update:
                        """

                        Volume is already displayed in projection view widget

                        """
                        previous = self._views['projections'].getVolume()
                        if previous.hasSameFieldOfView(self._volume):
                            # Display current volume in projection view widget
                            self._views['projections'].replaceVolume(self._volume)
                            # Set projection view widget visibility
                            if moveto:
                                self.getMainWindow().showProjectionView()
                                self.getMainWindow().updateTimers()
                    self._logger.info('Projection view display {}'.format(self._volume.getBasename()))
                if flag: wait.close()
        self._action['projections'].blockSignals(True)
        self._action['projections'].setChecked(True)
        self._action['projections'].blockSignals(False)
    # Revision 19/10/2024 >

    # < Revision 10/12/2024
    # add displayInMultiComponentView method
    def displayInMultiComponentView(self,
                                    moveto: bool = True,
                                    wait: DialogWait | None = None):
        if self._views is not None:
            if wait is None:
                wait = DialogWait(title='Display multi-component volume...')
                wait.open()
                wait.setInformationText('{} multi-component view display...'.format(self._volume.getBasename()))
                QApplication.processEvents()
                flag = True
            else: flag = False
            self._views['components'].viewWidgetVisibleOff()
            self._views['components'].setVolume(self._multi)
            self._views['components']().visibleChartOff()
            # Set display flag
            self.setChecked(True)
            # < Revision 02/06/2025
            # move button to first position
            if self.hasThumbnailToolbar():
                self.getThumbnailToolbar().moveSelectedToFisrt()
            # Revision 02/06/2025 >
            # Update other SisypheVolumeThumbnailButtonWidget in thumbnail
            if self.hasThumbnailToolbar():
                self.getThumbnailToolbar().updateWidgets()
            self._views['components'].viewWidgetVisibleOn()
            QApplication.processEvents()
            self._views['components']().visibleChartOn()
            if self.hasMainWindow():
                # Set multi-component view widget visibility
                self._updateViewsVisibility()
                if moveto:
                    self.getMainWindow().showComponentView()
                    self.getMainWindow().updateTimers()
            self._logger.info('Multi-component view display {}'.format(self._volume.getBasename()))
            if flag: wait.close()
        self._action['multi'].blockSignals(True)
        self._action['multi'].setChecked(True)
        self._action['multi'].blockSignals(False)
    # Revision 10/12/2024 >

    # < Revision 15/10/2024
    # add updateDisplay method
    def updateDisplay(self, replace):
        if self._action['slices'].isChecked(): self.displayInSliceView(moveto=False, update=replace)
        if self._action['orthogonal'].isChecked(): self.displayInOrthogonalView(moveto=False, update=replace)
        if self._action['synchronised'].isChecked(): self.displayInSynchronisedView(moveto=False, update=replace)
        if self._action['projections'].isChecked(): self.displayInProjectionView(moveto=False, update=replace)
    # Revision 15/10/2024 >

    def overlay(self):
        # Add overlay
        if self._action['overlay'].isChecked():
            if self._views is not None:
                info = '{} display as overlay...'.format(self._volume.getBasename())
                wait = DialogWait(title='Display volume as overlay...', info=info)
                wait.open()
                wait.progressVisibilityOff()
                QApplication.processEvents()
                try:
                    # < Revision 27/05/2025
                    # self._views.addOverlay(self._volume, wait)
                    # self.setDown(True)
                    if self._views.addOverlay(self._volume, wait):
                        self.setDown(True)
                        self._logger.info('Display overlay {}'.format(self._volume.getBasename()))
                    # Revision 27/05/2025 >
                except Exception as err:
                    wait.hide()
                    messageBox(self,
                               'Display overlay',
                               'Display overlay error : {}\n{}'.format(type(err), str(err)))
                finally:
                    wait.close()
        # Remove overlay
        else:
            if self._views is not None:
                try:
                    self._views.removeOverlay(self._volume)
                    self.setDown(False)
                except Exception as err:
                    messageBox(self,
                               'Remove overlay',
                               'Remove overlay error : {}\n{}'.format(type(err), str(err)))

    def displayOverlay(self):
        if not self._action['overlay'].isChecked():
            # < Revision 06/11/2024
            # manage the maximum number of overlays that can be displayed
            n = 0
            if self.hasThumbnailToolbar():
                n = self.getThumbnailToolbar().getOverlayCount()
            if n < 8:
                self._action['overlay'].setChecked(True)
                self.overlay()
            else:
                messageBox(self,
                           'Display overlay',
                           'Maximum number of overlays reached.\n'
                           'Removing an overlay before opening a new one.',
                           icon=QMessageBox.Information)
            # Revision 06/11/2024 >
        else:
            if messageBox(self,
                          'Display volume',
                          '{} is already displayed as overlay.\n'
                          'Would you like to display it as reference ?'.format(self._volume.getName()),
                          icon=QMessageBox.Question,
                          buttons=QMessageBox.Yes | QMessageBox.No,
                          default=QMessageBox.No) == QMessageBox.Yes:
                self.displayInSliceView()

    # < Revision 24/10/2024
    # add defaultWindow method
    def defaultWindow(self):
        self._lutwidget.defaultWindow()
        self._onMenuHide()
        self._logger.info('Set default window {}'.format(self._volume.getBasename()))
    # Revision 24/10/2024 >

    # < Revision 24/10/2024
    # add autoWindow method
    def autoWindow(self):
        self._lutwidget.autoWindow()
        self._onMenuHide()
        self._logger.info('Auto window {}'.format(self._volume.getBasename()))
    # Revision 24/10/2024 >

    # < Revision 24/10/2024
    # add brainWindow method
    def brainWindow(self):
        self._lutwidget.setCTBrainWindow()
        self._onMenuHide()
        self._logger.info('Set brain parenchyma window {}'.format(self._volume.getBasename()))
    # Revision 24/10/2024 >

    # < Revision 24/10/2024
    # add boneWindow method
    def boneWindow(self):
        self._lutwidget.setCTBoneWindow()
        self._onMenuHide()
        self._logger.info('Set bone window {}'.format(self._volume.getBasename()))
    # Revision 24/10/2024 >

    # < Revision 24/10/2024
    # add metallicWindow method
    def metallicWindow(self):
        self._lutwidget.setCTMetallicWindow()
        self._onMenuHide()
        self._logger.info('Set metallic window {}'.format(self._volume.getBasename()))
    # Revision 24/10/2024 >

    def flip(self, axis):
        if self._multi.getNumberOfComponentsPerPixel() == 1:
            if isinstance(axis, int):
                if 0 <= axis < 3:
                    if axis == 0: a = [True, False, False]
                    elif axis == 1: a = [False, True, False]
                    else: a = [False, False, True]
                    if self.isOverlaid(): self._views.removeOverlay(self._volume)
                    img = sitkFlip(self._volume.getSITKImage(), a)
                    vol = SisypheVolume()
                    vol.setSITKImage(img)
                    vol.setDefaultOrigin()
                    vol.copyAttributesFrom(self._volume)
                    vol.copyFilenameFrom(self._volume)
                    self._volume = vol
                    self._multi = vol
                    self._preview.updateImage(self._volume)
                    self._lutwidget.setVolume(self._volume)
                    if self.isReference(): self.updateDisplay(replace=True)
                    elif self.isOverlaid(): self.overlay()
                    self._logger.info('Flip axis {}'.format(self._volume.getBasename()))
                else: raise ValueError('parameter value {} is not between 0 and 2.'.format(axis))
            else: raise TypeError('parameter type {} is not int.'.format(type(axis)))

    # < Revision 19/10/2024
    # add removeNeck method
    def swapAxis(self, axes):
        """
            original  x y z
            permutation combinatorial :
            y x z -> axes=[1 0 2]
            z x y -> axes=[2 0 1]
            x z y -> axes=[0 2 1]
            y z x -> axes=[1 2 0]
            z y x -> axes=[2 1 0]
        """
        if self._multi.getNumberOfComponentsPerPixel() == 1:
            if self.isOverlaid():
                self._views.removeOverlay(self._volume)
                self.setDown(False)
            img = sitkPermuteAxes(self._volume.getSITKImage(), axes)
            vol = SisypheVolume()
            vol.setSITKImage(img)
            vol.setDefaultOrigin()
            vol.copyAttributesFrom(self._volume)
            vol.copyFilenameFrom(self._volume)
            self._volume = vol
            self._multi = self._volume
            self._preview.updateImage(self._volume)
            self._lutwidget.setVolume(self._volume)
            self.updateTooltip()
            self._logger.info('Swap axis {}'.format(self._volume.getBasename()))
            if self.isReference():
                self.setChecked(False)
                self.updateDisplay(replace=False)
    # Revision 19/10/2024 >

    # < Revision 19/10/2024
    # add removeNeck method
    def removeNeck(self):
        if self._multi.getNumberOfComponentsPerPixel() == 1:
            if self.isOverlaid():
                self._views.removeOverlay(self._volume)
                self.setDown(False)
            settings = SisypheFunctionsSettings()
            f = settings.getFieldValue('RemoveNeckSlices', 'ExtentFactor')
            self._volume = self._volume.removeNeckSlices(f)
            self._multi = self._volume
            self._preview.updateImage(self._volume)
            self._lutwidget.setVolume(self._volume)
            self.updateTooltip()
            self._logger.info('Remove neck slices {}'.format(self._volume.getBasename()))
            if self.isReference():
                self.setChecked(False)
                self.updateDisplay(replace=False)
    # Revision 19/10/2024 >

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def changeDatatype(self, dtype):
        if isinstance(dtype, str):
            if self._volume.getDatatype() != dtype:
                r = messageBox(self,
                               'Datatype conversion',
                               'Do you want to convert datatype to {} ?'.format(dtype),
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes:
                    if self.isOverlaid(): self._views.removeOverlay(self._volume)
                    vol = self._multi.cast(dtype)
                    vol.copyFilenameFrom(self._multi)
                    if vol.getAcquisition().isLB():
                        if dtype != 'uint8': vol.getAcquisition().setModalityToOT()
                    if self._multi.getNumberOfComponentsPerPixel() > 1:
                        self._multi = vol
                        self._componentChanged(self._component.value())
                    else:
                        self._multi = vol
                        self._volume = vol
                        self.updateTooltip()
                        if self.isReference(): self.updateDisplay(replace=True)
                        elif self.isOverlaid(): self.overlay()
                    self._logger.info('Change datatype to {} {}'.format(dtype, self._multi.getBasename()))
        else: raise TypeError('parameter type {} is not str.'.format(type(dtype)))
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def changeModality(self, m):
        if isinstance(m, str):
            if m in self._multi.acquisition.getModalityToCodeDict():
                if self._multi.acquisition.getModality() != m:
                    if m == self._multi.acquisition.getCTModalityTag():
                        self._multi.acquisition.setModalityToCT()
                        if self._multi.acquisition.getSequence() not in self._multi.acquisition.getCTSequences():
                            self._multi.acquisition.setSequence('')
                    elif m == self._multi.acquisition.getLBModalityTag():
                        if self._multi.isUInt8Datatype(): self._multi.acquisition.setModalityToLB()
                        else: messageBox(self,
                                         'Set modality',
                                         '{} image datatype is not compatible with LB '
                                         'modality (must be uint8)'.format(self._multi.getDatatype()))
                    elif m == self._multi.acquisition.getMRModalityTag():
                        self._multi.acquisition.setModalityToMR()
                        if self._multi.acquisition.getSequence() not in self._multi.acquisition.getMRSequences():
                            self._multi.acquisition.setSequence('')
                    elif m == self._multi.acquisition.getNMModalityTag():
                        self._multi.acquisition.setModalityToNM()
                        if self._multi.acquisition.getSequence() not in self._multi.acquisition.getNMSequences():
                            self._multi.acquisition.setSequence('')
                    elif m == self._multi.acquisition.getOTModalityTag():
                        self._multi.acquisition.setModalityToOT()
                        if self._multi.acquisition.getSequence() not in self._multi.acquisition.getOTSequences():
                            self._multi.acquisition.setSequence('')
                    elif m == self._multi.acquisition.getPTModalityTag():
                        self._multi.acquisition.setModalityToPT()
                        if self._muli.acquisition.getSequence() not in self._multi.acquisition.getPTSequences():
                            self._multi.acquisition.setSequence('')
                    elif m == self._multi.acquisition.getTPModalityTag():
                        self._multi.acquisition.setModalityToTP()
                    self._preview.setToolTip(str(self._multi))
                    if self._multi.getNumberOfComponentsPerPixel() > 1:
                        self._volume.copyAttributesFrom(self._multi)
                    else: self._volume = self._multi
                    self._logger.info('Change modality to {} {}'.format(m, self._multi.getBasename()))
            else: raise ValueError('Invalid modality {}'.format(m))
        else: raise TypeError('parameter type {} is not str.'.format(type(m)))
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def removeOrigin(self):
        self._multi.setDefaultOrigin()
        if self._multi.getNumberOfComponentsPerPixel() > 1: self._volume.setDefaultOrigin()
        else: self._volume = self._multi
        self._logger.info('Remove origin {}'.format(self._multi.getBasename()))
        self._preview.setToolTip(str(self._multi))
    # Revision 10/12/2024 >

    # < Revision 10/12/2024
    # replace self._volume by self._multi
    def removeDirection(self):
        self._multi.setDefaultDirections()
        if self._multi.getNumberOfComponentsPerPixel() > 1: self._volume.setDefaultDirections()
        else: self._volume = self._multi
        self._logger.info('Remove directions {}'.format(self._multi.getBasename()))
        self._preview.setToolTip(str(self._multi))
    # Revision 10/12/2024 >

    # < Revision 05/11/2024
    # add anonymize method
    def anonymize(self):
        self._multi.setDefaultDirections()
        if self._multi.getNumberOfComponentsPerPixel() > 1: self._volume.identity.anonymize()
        else: self._volume = self._multi
        self._logger.info('Anomynize {}'.format(self._multi.getBasename()))
        self._preview.setToolTip(str(self._multi))
    # Revision 05/11/2024 >

    def acpc(self):
        if self._multi.getNumberOfComponentsPerPixel() == 1:
            if self.hasMainWindow():
                # noinspection PyTypeChecker
                self.getMainWindow().acpcSelection(self._volume)

    def frame(self):
        if self._multi.getNumberOfComponentsPerPixel() == 1:
            if self.hasMainWindow():
                # noinspection PyTypeChecker
                self.getMainWindow().frameDetection(self._volume)

    def reorientation(self):
        if self._multi.getNumberOfComponentsPerPixel() == 1:
            if self.hasMainWindow():
                # noinspection PyTypeChecker
                self.getMainWindow().reorient(self._volume)

    def statistics(self):
        wait = DialogWait(info='{} statistics...'.format(self._volume.getName()))
        wait.open()
        dialog = DialogGenericResults()
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(dialog, c)
        if self._volume.acquisition.hasUnit(): unit = self._volume.acquisition.getUnit()
        else: unit = ''
        if self.hasMainWindow(): scrsht = self.getMainWindow().getScreenshots()
        else: scrsht = None
        dialog.newDescriptiveStatisticsTab([self._volume.getName()],
                                           [self._volume.getNumpy().flatten()],
                                           self._volume.getName(),
                                           scrshot=scrsht,
                                           units=unit)
        wait.setInformationText('{} histogram...'.format(self._volume.getName()))
        dialog.newImageHistogramTab(self._volume, cumulative=False, scrshot=scrsht)
        wait.close()
        self._logger.info('Descriptive statistics {}'.format(self._volume.getBasename()))
        dialog.exec()

    def isReference(self):
        return self.isChecked()

    # < Revision 15/10/2024
    # add isDisplayedInSliceView method
    def isDisplayedInSliceView(self):
        return self._action['slices'].isChecked()
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # add isDisplayedInOrthogonalView method
    def isDisplayedInOrthogonalView(self):
        return self._action['orthogonal'].isChecked()
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # add isDisplayedInSynchronisedView method
    def isDisplayedInSynchronisedView(self):
        return self._action['synchronised'].isChecked()
    # Revision 15/10/2024 >

    # < Revision 15/10/2024
    # add isDisplayedInProjectionView method
    def isDisplayedInProjectionView(self):
        return self._action['projections'].isChecked()
    # Revision 15/10/2024 >

    # < Revision 10/12/2024
    # add isDisplayedInMultiComponentView method
    def isDisplayedInMultiComponentView(self):
        return self._action['multi'].isChecked()
    # Revision 10/12/2024 >

    def isOverlaid(self):
        return self._action['overlay'].isChecked()

    def hasReference(self):
        if self._thumbnail is not None: return self._thumbnail.hasReference()
        else: raise AttributeError('_thumbnail attribute is None.')

    def getVolume(self):
        # < Revision 12/12/2024
        # return self._volume
        return self._multi
        # Revision 12/12/2024 >

    def updateTooltip(self):
        self._preview.setToolTip(str(self._volume))

    # Qt Drag event

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # < Revision 21/03/2025
            # s = self._preview.getSubButtonSize() + 16
            # if event.pos().x() > self.width() - s and event.pos().y() > self.height() - s:
            if event.pos().x() > int(self.width() * 0.5) and event.pos().y() > int(self.height() * 0.5):
                self._popup.exec(self._getWidgetCenter())
            else:
                self._dragpos0 = event.pos()
                QToolTip.showText(self.mapToGlobal(event.pos()), str(self._volume), self, self.geometry(), 5000)
            # Revision 21/03/2025 >

    def contextMenuEvent(self, event):
        self._popup.exec(self._getWidgetCenter())

    def mouseDoubleClickEvent(self, event):
        if not self.isChecked():
            self.displayInSliceView()

    def mouseReleaseEvent(self, event):
        self._dragpos0 = None

    def mouseMoveEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragpos0 is not None:
            QToolTip.hideText()
            d = (event.pos() - self._dragpos0).manhattanLength()
            if d > 20:
                thumbnail = self.getThumbnailToolbar()
                if thumbnail is not None:
                    index = thumbnail.getVolumeIndex(self._volume)
                    if index is not None:
                        drag = QDrag(self)
                        mime = QMimeData()
                        mime.setText('idx {}'.format(index))
                        drag.setMimeData(mime)
                        pixmap = self.grab()
                        drag.setPixmap(pixmap)
                        drag.exec(Qt.MoveAction)
                        self._dragpos0 = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            txt = event.mimeData().text()
            if txt[:3] == 'idx':
                index = int(txt.split()[1])
                # Drop event of Thumbnail button number index in current Thumbnail button
                if self.hasThumbnailToolbar():
                    moving = self.getThumbnailToolbar().getVolumeFromIndex(index)
                    if moving.getID() != self._volume.getID():
                        self._registration(moving)
            else:
                files = txt.split('\n')
                files = files[0]
                if files != '':
                    dropfile = files.replace('file://', '')
                    if splitext(dropfile)[1] == SisypheVolume.getFileExt():
                        if dropfile != self._volume.getFilename():
                            # Drop event of xvol file in current Thumbnail button
                            moving = SisypheVolume()
                            moving.load(dropfile)
                            self._registration(moving)
