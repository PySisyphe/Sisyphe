"""
    External packages/modules

        Name            Link                                                        Usage

        Matplotlib      https://matplotlib.org/                                     Graph tool
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os import getcwd
from os.path import join
from os.path import dirname
from os.path import abspath
from os.path import splitext

from time import perf_counter

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

from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImage import SisypheImage
from Sisyphe.core.sisypheDicom import XmlDicom
from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.widgets.attributesWidgets import ItemOverlayAttributesWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogXmlDicom import DialogXmlDicom
from Sisyphe.gui.dialogEditLabels import DialogEditLabels
from Sisyphe.gui.dialogVolumeAttributes import DialogVolumeAttributes

"""
    Class hierarchy
    
        QWidget -> ImagePreviewWidget -> SisypheImageViewWidget -> SisypheVolumeViewWidget
        QPushButton -> SisypheVolumeThumbnailButtonWidget
        
        to do:
             SisypheVolumeThumbnailButtonWidget
                def dropEvent(self, event), drop event between SisypheVolumeThumbnailButtonWidget for registration
"""


class ImagePreviewWidget(QWidget):
    """
        ImagePreviewWidget class

        Description

            Displays thumbnail of SimpleITK image

        Inheritance

            QWidget -> ImagePreviewWidget

        Private attributes

            _fig            Figure instance
            _axe            Axes instance
            _canvas         FigureCanvasQTAgg instance
            _lut            cmap instance
            _currentslice   int
            _image          numpy ndarray instance
            _orient         str, 'upper' SimpleITK, 'lower' VTK, SisypheImage, SisypheVolume
            _vmin           float, lower window value
            _vmax           float, higher window value

        Public methods

            setDefault()
            setLut(str or ListedColormap or LinearSegmentedColormap or SisypheLut)
            cmap = getLut()
            Figure = getFigure()
            Axes = getAxes()
            FigureCanvas = getCanvas()
            sitkImage = getImage()
            int = getCurrentSlice()
            setCurrentSlice(int)
            int = getSize()
            setSize(int)

            inherited QWidget class
    """

    _VSIZE = 16

    # Class method

    @classmethod
    def _getDefaultIconDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'icons')

    @classmethod
    def getSubButtonSize(cls):
        return cls._VSIZE

    # Special method

    def __init__(self, image=None, lut='gray', size=128, orient='upper', parent=None):
        super().__init__(parent)

        # Init icon

        self._icn = QLabel()
        pixmap = QPixmap(join(self._getDefaultIconDirectory(), 'wmore2.png'))
        self._icn.setPixmap(pixmap.scaled(self._VSIZE, self._VSIZE, Qt.KeepAspectRatio))
        self._icn.setScaledContents(False)
        self._icn.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self._icn.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Init matplotlib figure

        self._fig = Figure()
        self._fig.set_facecolor('black')
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
                self._canvas.mpl_connect('button_press_event', self._onClickEvent)
                self._canvas.mpl_connect('motion_notify_event', self._onMouseMoveEvent)
                self._canvas.mpl_connect('key_press_event', self._onKeyPressEvent)
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
        try: self._lut = get_cmap(lut, 256)
        except ValueError: self._lut = get_cmap('gray', 256)

        # Draw image in tool

        self._canvas.setFocusPolicy(Qt.ClickFocus)
        self._canvas.setFocus()
        self._drawImage()

        # Drag and Drop

        self.acceptDrops()

    # Private method

    def _drawImage(self):
        if self._image is not None:
            if self._image.ndim == 3: mat = self._image[self._currentslice, :, :]
            else: mat = self._image
            self._axe.imshow(fliplr(mat), origin=self._orient, cmap=self._lut,
                             vmin=self._vmin, vmax=self._vmax, interpolation='bilinear')
            self._canvas.draw_idle()

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

            Displays thumbnail of SisypheImage/SisypheVolume

        Inheritance

            QWidget -> ImagePreviewWidget -> SisypheImagePreviewWidget

        Public methods

            inherited QWidget class
            inherited ImagePreviewWidget class
    """

    def __init__(self, image=None, lut='gray', size=128, parent=None):
        if isinstance(image, (SisypheImage, SisypheVolume)):
            super().__init__(image.getNumpy(), lut, size, 'lower', parent)
            self.setToolTip(str(image))
        else:
            raise TypeError('constructor image parameter {} is not SisypheImage or SisypheVolume.'.format(type(image)))

    # Public method

    def updateImage(self, image):
        if isinstance(image, (SisypheImage, SisypheVolume)):
            super().updateImage(image.getNumpy())
        else: raise TypeError('parameter {} is not SisypheImage or SisypheVolume.'.format(type(image)))


class SisypheVolumeViewWidget(SisypheImageViewWidget):
    """
        SisypheVolumePreviewWidget class

        Description

            Display thumbnail of SisypheImage/SisypheVolume
            Add mouse event methods

        Inheritance

            QWidget -> ImagePreviewWidget -> SisypheImagePreviewWidget -> SisypheVolumePreviewWidget

        Private attributes

            _parent     QWidget, parent tool

        Public methods

            inherited QWidget class
            inherited ImagePreviewWidget class
            inherited SisypheImagePreviewWidget class
    """

    def __init__(self, image=None, size=128, parent=None):
        if isinstance(image, (SisypheImage, SisypheVolume)):
            lut = image.display.getLUT().copyToMatplotlibColormap()
            super().__init__(image, lut, size, parent)
            self._parent = parent
        else:
            raise TypeError('constructor image parameter {} is not SisypheImage or SisypheVolume.'.format(type(image)))

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

            QPushButton with thumbnail of SisypheImage/SisypheVolume.
            IO SisypheVolume management in PySisyphe environment.
            Item of the container class ToolBarThumbnail.

        Inheritance

            QPushButton - > SisypheVolumeThumbnailButtonWidget

        Private attributes

            _preview    SisypheVolumeViewWidget instance
            _popup      QMenu instance
            _dragpos0   QPoint, drag start position
            _thumbnail  ToolBarThumbnail, associated thumbnail
            _views      IconBarViewWidgetCollection, associated view widgets

        Public methods

            ToolBarThumbnail = getThumbnailToolbar()
            setThumbnailToolbar(ToolBarThumbnail)
            bool = hasThumbnailToolbar()
            IconBarViewWidgetCollection = getViewsWidget()
            setViewsViewsWidget(IconBarViewWidgetCollection)
            bool = hasViewsViewsWidget()
            WindowSisyphe = getMainWindow()
            SisypheVolume = getVolume()
            editAttributes()
            save()
            saveas()
            remove()
            display()
            overlay()
            bool = isReference()
            SisypheVolume = getVolume()
            updateTooltip()

            inherited QPushButton class

        Qt Events

            mousePressEvent     override
            mouseMoveEvent      override
            dragEnterEvent      override
            dropEvent           override
    """

    # Special method

    def __init__(self, image=None, size=128, thumbnail=None, views=None, parent=None):
        if isinstance(image, (SisypheImage, SisypheVolume)):
            super().__init__(parent)

            from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
            if isinstance(thumbnail, ToolBarThumbnail): self._thumbnail = thumbnail
            else: self._thumbnail = None

            from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
            if isinstance(views, IconBarViewWidgetCollection): self._views = views
            else: self._views = None

            self._volume = image
            self._preview = SisypheVolumeViewWidget(image, size=size-32, parent=self)
            vmin, vmax = self._volume.display.getWindow()
            self._preview.setRange(vmin, vmax)
            QApplication.processEvents()
            self._dragpos0 = None

            self.setStyleSheet("QPushButton:closed {background-color: black; border-color: black; border-style: solid; "
                               "border-width: 8px; border-radius: 20px;}")

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

            # Attributes widget

            self._attributes = ItemOverlayAttributesWidget(overlay=self._volume, views=self._views)
            QApplication.processEvents()

            # Lut widget

            self._lutwidget = LutWidget(size=256, view=self._views)
            self._lutwidget.setVolume(self._volume)
            QApplication.processEvents()

            # Init popup menu

            self._popup = QMenu(self)
            self._action = dict()
            self._action['display'] = QAction('Display as reference', self)
            self._action['overlay'] = QAction('Display as overlay', self)
            self._action['attributes'] = QAction('Edit attributes...', self)
            self._action['dicom'] = QAction('View Dicom attributes...', self)
            self._action['labels'] = QAction('Edit labels...', self)
            self._action['labels'].setVisible(self._volume.getAcquisition().isLB())
            self._action['database'] = QAction('Add to database...', self)
            self._action['Save'] = QAction('Save', self)
            self._action['Saveas'] = QAction('Save as...', self)
            self._action['Close'] = QAction('Close', self)
            self._action['acpc'] = QAction('AC-PC selection...', self)
            self._action['frame'] = QAction('Stereotactic frame detection...', self)
            self._action['orient'] = QAction('Reorientation...', self)
            self._action['display'].triggered.connect(self.display)
            self._action['overlay'].triggered.connect(self.overlay)
            self._action['attributes'].triggered.connect(self.editAttributes)
            self._action['dicom'].triggered.connect(self.viewDicomAttributes)
            self._action['labels'].triggered.connect(self.editLabels)
            self._action['database'].triggered.connect(self.addToDatabase)
            self._action['Save'].triggered.connect(self.save)
            self._action['Saveas'].triggered.connect(self.saveas)
            self._action['Close'].triggered.connect(self.remove)
            self._action['acpc'].triggered.connect(self.acpc)
            self._action['frame'].triggered.connect(self.frame)
            self._action['orient'].triggered.connect(self.reorientation)
            self._popup.addAction(self._action['display'])
            self._popup.addAction(self._action['overlay'])
            self._popup.addAction(self._action['attributes'])
            self._popup.addAction(self._action['dicom'])
            self._popup.addAction(self._action['labels'])
            self._popup.addAction(self._action['database'])
            self._popup.addSeparator()
            self._popup.addAction(self._action['acpc'])
            self._popup.addAction(self._action['orient'])
            self._popup.addAction(self._action['frame'])
            self._popup.addSeparator()
            submenu = self._popup.addMenu('Flip')
            self._action['flipx'] = submenu.addAction('Flip left/right axis')
            self._action['flipx'].triggered.connect(lambda dummy, axis=0: self.flip(axis))
            self._action['flipy'] = submenu.addAction('Flip antero-posterior axis')
            self._action['flipy'].triggered.connect(lambda dummy, axis=1: self.flip(axis))
            self._action['flipz'] = submenu.addAction('Flip cranio-caudal axis')
            self._action['flipz'].triggered.connect(lambda dummy, axis=2: self.flip(axis))
            submenu = self._popup.addMenu('Swap axis')
            self._action['yxz'] = submenu.addAction('Swap axis to y,z,x')
            self._action['yxz'].triggered.connect(lambda dummy, axes=(1, 0, 2): self.swapAxis(axes))
            self._action['zxy'] = submenu.addAction('Swap axis to z,x,y')
            self._action['zxy'].triggered.connect(lambda dummy, axes=(2, 0, 1): self.swapAxis(axes))
            self._action['xzy'] = submenu.addAction('Swap axis to x,z,y')
            self._action['xzy'].triggered.connect(lambda dummy, axes=(0, 2, 1): self.swapAxis(axes))
            self._action['yzx'] = submenu.addAction('Swap axis to y,z,x')
            self._action['yzx'].triggered.connect(lambda dummy, axes=(1, 2, 0): self.swapAxis(axes))
            self._action['zyx'] = submenu.addAction('Swap axis to z,y,x')
            self._action['zyx'].triggered.connect(lambda dummy, axes=(2, 1, 0): self.swapAxis(axes))
            submenu = self._popup.addMenu('Datatype conversion')
            self._action['int8'] = submenu.addAction('int8')
            self._action['int8'].triggered.connect(lambda dummy, dtype='int8': self.changeDatatype(dtype))
            self._action['int16'] = submenu.addAction('int16')
            self._action['int16'].triggered.connect(lambda dummy, dtype='int16': self.changeDatatype(dtype))
            self._action['int32'] = submenu.addAction('int32')
            self._action['int32'].triggered.connect(lambda dummy, dtype='int32': self.changeDatatype(dtype))
            self._action['int64'] = submenu.addAction('int64')
            self._action['int64'].triggered.connect(lambda dummy, dtype='int64': self.changeDatatype(dtype))
            self._action['uint8'] = submenu.addAction('uint8')
            self._action['uint8'].triggered.connect(lambda dummy, dtype='uint8': self.changeDatatype(dtype))
            self._action['uint16'] = submenu.addAction('uint16')
            self._action['uint16'].triggered.connect(lambda dummy, dtype='uint16': self.changeDatatype(dtype))
            self._action['uint32'] = submenu.addAction('uint32')
            self._action['uint32'].triggered.connect(lambda dummy, dtype='uint32': self.changeDatatype(dtype))
            self._action['uint64'] = submenu.addAction('uint64')
            self._action['uint64'].triggered.connect(lambda dummy, dtype='uint64': self.changeDatatype(dtype))
            self._action['float32'] = submenu.addAction('float32')
            self._action['float32'].triggered.connect(lambda dummy, dtype='float32': self.changeDatatype(dtype))
            self._action['float64'] = submenu.addAction('float64')
            self._action['float64'].triggered.connect(lambda dummy, dtype='float64': self.changeDatatype(dtype))

            self._popup.addSeparator()
            self._popup.addAction(self._action['Save'])
            self._popup.addAction(self._action['Saveas'])
            self._popup.addAction(self._action['Close'])

            self._action['overlay'].setCheckable(True)
            self._action['overlay'].setChecked(False)

            self._action['attributes'] = QWidgetAction(self)
            self._action['attributes'].setDefaultWidget(self._attributes)
            self._popup.addAction(self._action['attributes'])

            self._action['lut'] = QWidgetAction(self)
            self._action['lut'].setDefaultWidget(self._lutwidget)
            self._popup.addAction(self._action['lut'])

            self._popup.aboutToShow.connect(self._onMenuShow)
            self._popup.aboutToHide.connect(self._onMenuHide)

            self._action['attributes'].setVisible(False)
            self._action['lut'].setVisible(True)
            self._action['overlay'].setVisible(False)
            if isinstance(self._volume, SisypheVolume): self._action['dicom'].setVisible(self._volume.hasXmlDicom())
            else: self._action['dicom'].setVisible(False)

            self._attributes.visibilityChanged.connect(lambda: self.contextMenuEvent(event=None))

            # Drag and Drop

            self.setAcceptDrops(True)
        else: raise TypeError('constructor image parameter {} is not SisypheImage or SisypheVolume.'.format(type(image)))

    # Private method

    def _onMenuShow(self):
        if not self.hasReference(): self._action['overlay'].setChecked(False)
        self._action['display'].setVisible(not self.isReference())
        self._action['overlay'].setVisible(self.hasReference() and not self.isReference())
        self._action['attributes'].setVisible(self.isOverlaid())
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
                r = QMessageBox.question(self.getMainWindow(),
                                         'Registration',
                                         '{} and {} are already registered.\n'
                                         'Do you want to start a new registration ?'.format(self._volume.getBasename(),
                                                                                            moving.getBasename()),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if r == QMessageBox.No: return
            if r is None:
                r = QMessageBox.question(self.getMainWindow(),
                                         'Registration',
                                         'Do you want to register {} and {} ?'.format(self._volume.getBasename(),
                                                                                      moving.getBasename()),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if r == QMessageBox.Yes:
                    self.getMainWindow().rigidRegistration(fixed=self._volume, moving=moving)

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

    def setViewsViewsWidget(self, w):
        from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
        if isinstance(w, IconBarViewWidgetCollection): self._views = w
        else: raise TypeError('parameter type {} is not IconBarViewWidgetCollection.'.format(type(w)))

    def hasViewsViewsWidget(self):
        return self._views is not None

    def getMainWindow(self):
        if self._thumbnail is not None:
            return self._thumbnail.getMainWindow()
        else: return None

    def hasMainWindow(self):
        return self._thumbnail.getMainWindow() is not None

    def getActions(self):
        return self._action

    def editAttributes(self):
        dialog = DialogVolumeAttributes(vol=self._volume)
        dialog.exec()
        self._preview.setToolTip(str(self._volume))

    def viewDicomAttributes(self):
        if self._volume.hasXmlDicom():
            filename = splitext(self._volume.getFilename())[0] + XmlDicom.getFileExt()
            dialog = DialogXmlDicom(filename)
            dialog.exec()

    def editLabels(self):
        if self._volume.getAcquisition().isLB():
            dialog = DialogEditLabels()
            dialog.setVolume(self._volume)
            dialog.exec()

    def addToDatabase(self):
        if self.hasMainWindow():
            database = self.getMainWindow().getDatabase()
            if database is not None: database.addVolumes(self._volume)

    def save(self):
        if self._volume.hasFilename():
            try: self._volume.save()
            except Exception as err: QMessageBox.warning(self, 'Save PySisyphe volume', '{}'.format(err))
            mainwindow = self.getMainWindow()
            if mainwindow is not None: mainwindow.setStatusBarMessage('{} saved.'.format(self._volume.getBasename()))
            self._preview.setToolTip(str(self._volume))
        else:
            self.saveas()

    def saveas(self):
        title = 'Save PySisyphe volume'
        if self._volume.hasFilename(): filename = self._volume.getFilename()
        else: filename = getcwd()
        filename = QFileDialog.getSaveFileName(self, title, filename, '*.xvol')[0]
        if filename:
            QApplication.processEvents()
            try: self._volume.saveAs(filename)
            except Exception as err:
                QMessageBox.warning(self, 'Save PySisyphe volume', 'error : {}'.format(err))
            mainwindow = self.getMainWindow()
            if mainwindow is not None: mainwindow.setStatusBarMessage('{} saved.'.format(self._volume.getBasename()))
            self._preview.setToolTip(str(self._volume))

    def remove(self):
        if self._thumbnail is not None: self._thumbnail.removeVolume(self._volume)

    def display(self, update=False):
        if not self.isChecked() or update:
            self.setChecked(True)
            if self._views is not None:
                info = '{} display...'.format(self._volume.getBasename())
                wait = DialogWait(title='Display volume...', info=info, parent=self)
                wait.open()
                QApplication.processEvents()
                if self.hasMainWindow():
                    self.getMainWindow().clearDockListWidgets()
                self._views.removeVolume()
                try:
                    self._views.setVolume(self._volume, wait)
                    w = self.getThumbnailToolbar()
                    if w is not None: w.removeAllOverlays()
                except Exception as err:
                    QMessageBox.warning(self, 'Display volume', 'Display error : {}'.format(err))
                finally:
                    wait.close()
                if self.hasMainWindow():
                    self.getMainWindow().updateTimers(None)
                    self.getMainWindow().setDockEnabled(True)
                    if self._volume.isThickAnisotropic(): self.getMainWindow().hideOrthogonalView()
                    else: self.getMainWindow().showOrthogonalView()

    def overlay(self):
        # Add overlay
        if self._action['overlay'].isChecked():
            if self._views is not None:
                info = '{} display as overlay...'.format(self._volume.getBasename())
                wait = DialogWait(title='Display volume as overlay...', info=info, parent=self)
                wait.open()
                QApplication.processEvents()
                try: self._views.addOverlay(self._volume, wait)
                except Exception as err:
                    QMessageBox.warning(self, 'Display volume as overlay', 'Display error : {}'.format(err))
                finally:
                    wait.close()
        # Remove overlay
        else:
            if self._views is not None:
                try: self._views.removeOverlay(self._volume)
                except Exception as err:
                    QMessageBox.warning(self, 'Remove overlay', '{}'.format(err))

    def flip(self, axis):
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
                self._preview.updateImage(self._volume)
                self._lutwidget.setVolume(self._volume)
                if self.isReference(): self.display(update=True)
                elif self.isOverlaid(): self.overlay()
            else: raise ValueError('parameter value {} is not between 0 and 2.'.format(axis))
        else: raise TypeError('parameter type {} is not int.'.format(type(axis)))

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
        if self.isOverlaid(): self._views.removeOverlay(self._volume)
        img = sitkPermuteAxes(self._volume.getSITKImage(), axes)
        vol = SisypheVolume()
        vol.setSITKImage(img)
        vol.setDefaultOrigin()
        vol.copyAttributesFrom(self._volume)
        vol.copyFilenameFrom(self._volume)
        self._volume = vol
        self._preview.updateImage(self._volume)
        self._lutwidget.setVolume(self._volume)
        if self.isReference(): self.display(update=True)
        elif self.isOverlaid(): self.overlay()

    def changeDatatype(self, dtype):
        if isinstance(dtype, str):
            if self._volume.getDatatype() != dtype:
                r = QMessageBox.question(self, 'Datatype conversion',
                                         'Do you want to convert datatype to {} ?'.format(dtype),
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
                if r == QMessageBox.Yes:
                    if self.isOverlaid(): self._views.removeOverlay(self._volume)
                    vol = self._volume.cast(dtype)
                    vol.copyFilenameFrom(self._volume)
                    if vol.getAcquisition().isLB():
                        if dtype != 'uint8': vol.getAcquisition().setModalityToOT()
                    self._volume = vol
                    self._preview.setToolTip(str(self._volume))
                    if self.isReference(): self.display(update=True)
                    elif self.isOverlaid(): self.overlay()
        else: raise TypeError('parameter type {} is not str.'.format(type(dtype)))

    def acpc(self):
        if self.hasMainWindow():
            self.getMainWindow().acpcSelection(self._volume)

    def frame(self):
        if self.hasMainWindow():
            self.getMainWindow().frameDetection(self._volume)

    def reorientation(self):
        if self.hasMainWindow():
            self.getMainWindow().reorient(self._volume)

    def isReference(self):
        return self.isChecked()

    def isOverlaid(self):
        return self._action['overlay'].isChecked()

    def hasReference(self):
        if self._thumbnail is not None:
            return self._thumbnail.hasReference()

    def getVolume(self):
        return self._volume

    def updateTooltip(self):
        self._preview.setToolTip(str(self._volume))

    # Qt Drag event

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # p = self.mapToGlobal(event.pos())
            s = self._preview.getSubButtonSize() + 16
            if event.pos().x() > self.width() - s and \
                    event.pos().y() > self.height() - s:
                self._popup.exec(self._getWidgetCenter())
            else:
                self._dragpos0 = event.pos()
                QToolTip.showText(self.mapToGlobal(event.pos()), str(self._volume), self, self.geometry(), 5000)

    def contextMenuEvent(self, event):
        self._popup.exec(self._getWidgetCenter())

    def mouseDoubleClickEvent(self, event):
        self.display()

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


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv
    from Sisyphe.core.sisypheImageIO import readFromNIFTI

    app = QApplication(argv)
    main = QWidget()
    layout = QVBoxLayout(main)
    filename1 = '/Users/Jean-Albert/PycharmProjects/untitled/IMAGES/NIFTI/STEREO3D.nii'
    simg = readFromNIFTI(filename1, 'sitk')
    preview = ImagePreviewWidget(simg, size=128)
    layout.addWidget(preview)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    main.show()
    app.exec_()
