"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - matplotlib, Graph management and visualization, https://matplotlib.org
    - PyQtDarkTheme, dark theme management, https://pyqtdarktheme.readthedocs.io/en/stable/index.html
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, Medical image processing, https://simpleitk.org/
"""

from sys import platform

from os import getcwd
from os import chdir

from os.path import abspath
from os.path import exists
from os.path import join
from os.path import isdir
from os.path import isfile
from os.path import dirname
from os.path import basename
from os.path import splitext
from os.path import split

from glob import glob

from numpy import max
from numpy import mean
from numpy import where
from numpy import linspace
from numpy import vstack
from numpy import iinfo
from numpy import finfo

from matplotlib.figure import Figure
from matplotlib.cm import get_cmap
from matplotlib.patches import Rectangle
from matplotlib.colors import Colormap
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPen
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox

import darkdetect

from SimpleITK import Clamp
from SimpleITK import GradientMagnitude

from Sisyphe.core.sisypheLUT import SisypheLut
from Sisyphe.core.sisypheLUT import SisypheColorTransfer
from Sisyphe.core.sisypheConstants import getLutExt
from Sisyphe.core.sisypheConstants import getIntStdDatatypes
from Sisyphe.core.sisypheImageAttributes import SisypheDisplay
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.basicWidgets import colorDialog
from Sisyphe.widgets.abstractViewWidget import AbstractViewWidget
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.multiViewWidgets import MultiViewWidget
from Sisyphe.widgets.volumeViewWidget import VolumeViewWidget

if platform == 'win32':
    # noinspection PyUnresolvedReferences
    from qdarktheme import load_palette

"""
Functions
~~~~~~~~~

    - drawLutToQImage
    - drawLutToPixmap  
"""


def drawLutToQImage(lut: SisypheLut | Colormap | ListedColormap | LinearSegmentedColormap, h: int = 32) -> QImage:
    imglut = QImage(256, h, QImage.Format_RGB888)
    painter = QPainter(imglut)
    pen = QPen()
    pen.setWidth(1)
    if isinstance(lut, SisypheLut):
        for i in range(256):
            pen.setColor(QColor(int(lut[i][0]*255), int(lut[i][1]*255), int(lut[i][2]*255), 255))
            painter.setPen(pen)
            painter.drawLine(i, 0, i, h)
    elif isinstance(lut, (ListedColormap, LinearSegmentedColormap)):
        for i in range(256):
            pen.setColor(QColor(int(lut(i)[0]*255), int(lut(i)[1]*255), int(lut(i)[2]*255), 255))
            painter.setPen(pen)
            painter.drawLine(i, 0, i, h)
    return imglut


def drawLutToPixmap(lut: SisypheLut | Colormap | ListedColormap | LinearSegmentedColormap, h: int = 32) -> QPixmap:
    imglut = QPixmap(256, h)
    painter = QPainter(imglut)
    pen = QPen()
    pen.setWidth(1)
    if isinstance(lut, SisypheLut):
        for i in range(256):
            pen.setColor(QColor(int(lut[i][0]*255), int(lut[i][1]*255), int(lut[i][2]*255), 255))
            painter.setPen(pen)
            painter.drawLine(i, 0, i, h)
    elif isinstance(lut, (ListedColormap, LinearSegmentedColormap)):
        for i in range(256):
            pen.setColor(QColor(int(lut(i)[0]*255), int(lut(i)[1]*255), int(lut(i)[2]*255), 255))
            painter.setPen(pen)
            painter.drawLine(i, 0, i, h)
    return imglut


"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> LutWidget
                 LutEditWidget -> ColorTransferWidget
                 AlphaTransferWidget
                 TransferWidget
    - QComboBox -> ComboBoxLut
    - QMenu -> PopupMenuLut
"""


class LutWidget(QWidget):
    """
    LutWidget class

    Description
    ~~~~~~~~~~~

    Custom QWidget to control lut (colormap selection, window settings)

    Functionalities:
    - Displaying the histogram of the image data.
    - Providing a visual representation of the current lut and colormap.
    - Allowing the user to select a lut from a predefined list or from a file on disk.
    - Enabling the user to reverse the current lut.
    - Providing a range slider to adjust the image windowing settings.
    - Displaying the current windowing settings (min and max values) in editable text boxes.
    - Handling mouse events for adjusting the windowing settings and moving the windowing range.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> LutWidget

    Creation: 01/11/2022
    Last revision: 25/03/2025
    """

    # Custom Qt Signal

    lutChanged = pyqtSignal()
    lutWindowChanged = pyqtSignal()

    # Class methods

    @classmethod
    def isDarkMode(cls) -> bool:
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        return darkdetect.isLight()

    # Special method

    """
    Private attributes

    _view               Display widget to update when Lut settings changed
    _fig                Figure, Matplotlib figure
    _canvas             FigureCanvas, QWidget canvas
    _ratio              float, Dimension of the lut axes (percent of the figure)
    _axe                Axes, Histogram display
    _lutaxe             Axes, Central lut display
    _rect1axe           Axes, Left lut display, values under window
    _rect2axe           Axes, Right lut display, values above window
    _imglut             AxesImage, Lut image
    _span               avxspan, Span artist (polygon patches instance)
    _cursor             QCursor, Mouse cursor
    _thresholdinftext   Annotation, Window inf. value displayed on the span
    _thresholdsuptext   Annotation, Window sup. value displayed on the span
    _editmin            QLineEdit, Widget to edit inferior range value
    _editmax            QLineEdit, Widget to edit superior range value
    _xpos               float, Cursor position before mouse event start
    _xleft              float, Left span position before mouse event start
    _xright             float, Right span position before mouse event start
    _decimals           int, number of decimals after point in QLineEdit _editmin and _editmax
    _format             str, float representation in QLineEdit _editmin and _editmax
    """

    def __init__(self,
                 volume: SisypheVolume | None = None,
                 view=None,
                 size: int = 512,
                 ratio: float = 0.1,
                 parent: QWidget | None = None):
        super().__init__(parent)

        self._view = view
        self._format = '{:.1f}'
        self._decimals = 1

        self._volume = volume
        if volume is not None:
            if not isinstance(volume, SisypheVolume):
                raise TypeError('volume parameter type {} is not SisypheVolume.'.format(type(volume)))
            else: self._initDecimals()

        if 0 < ratio > 1: ratio = 0.1
        self._ratio = ratio

        # Init matplotlib figure

        self._fig = Figure()
        # < Revision 11/03/2025
        self._fig.set_size_inches(size / 100, size / 100)
        # Revision 11/03/2025 >
        # < Revision 11/03/2025
        if platform == 'win32':
            p = load_palette('auto')
            background = p.color(QPalette.Base)
        else:
            if parent is not None:
                # noinspection PyTypeChecker
                background = parent.palette().color(QPalette.Base)
            else:
                # noinspection PyTypeChecker
                background = self.palette().color(QPalette.Base)
        # < Revision 11/03/2025
        self._fig.set_facecolor((background.red() / 255,
                                 background.green() / 255,
                                 background.blue() / 255))
        self._canvas = FigureCanvas(self._fig)

        grid = self._fig.add_gridspec(3, 3, hspace=0, wspace=0)

        self._histaxe = self._fig.add_subplot(grid[0, :])
        self._rect1axe = self._fig.add_subplot(grid[1, 0])
        self._lutaxe = self._fig.add_subplot(grid[1, 1])
        self._rect2axe = self._fig.add_subplot(grid[1, 2])

        self._histaxe.set_position([0.0, self._ratio, 1, 1-self._ratio], which='both')
        self._rect1axe.set_position([0.0, 0.0, 0.2, self._ratio], which='both')
        self._lutaxe.set_position([0.2, 0.0, 0.6, self._ratio], which='both')
        self._rect2axe.set_position([0.8, 0.0, 0.2, self._ratio], which='both')

        self._span = None
        self._winftext = None
        self._wsuptext = None
        if self._volume: self._initHistAxes()

        self._imglut = None
        if self._volume: self._initLutImage()

        # Init matplotlib events

        # noinspection PyTypeChecker
        self._canvas.mpl_connect('button_press_event', self._onMouseClickEvent)
        # noinspection PyTypeChecker
        self._canvas.mpl_connect('motion_notify_event', self._onMouseMoveEvent)
        # noinspection PyTypeChecker
        self._canvas.mpl_connect('button_release_event', self._onMouseReleaseEvent)
        self._on_move_span_flag = False
        self._on_move_left_span_flag = False
        self._on_move_right_span_flag = False
        self._xpos = None
        self._xleft = None
        self._xright = None

        # Init QLineEdit

        # < Revision 23/07/2024
        # replace QLineEdit by QDoubleSpinBox
        # self._editmin = QLineEdit()
        # self._editmax = QLineEdit()
        self._editmin = QDoubleSpinBox()
        self._editmax = QDoubleSpinBox()
        # Revision 23/07/2024 >
        self._editmin.setFixedWidth(80)
        self._editmax.setFixedWidth(80)
        if self._volume: self._initEdit()

        # < Revision 23/07/2024
        # replace QLineEdit by QDoubleSpinBox
        # self._editmin.editingFinished.connect(self._onRangeChangedEvent)
        # noinspection PyUnresolvedReferences
        self._editmin.valueChanged.connect(self._onRangeChangedEvent)
        # self._editmax.editingFinished.connect(self._onRangeChangedEvent)
        # noinspection PyUnresolvedReferences
        self._editmax.valueChanged.connect(self._onRangeChangedEvent)
        # Revision 23/07/2024 >

        # Init QComboBox

        self._combo = ComboBoxLut()
        self._combo.addItem('from disk...')
        if self._volume:
            # < Revision 17/10/2024
            # index = self._combo.findData(self._volume.display.getLUT().getName())
            index = self._combo.findText(self._volume.display.getLUT().getName())
            # Revision 17/10/2024 >
            if index > -1: self._combo.setCurrentIndex(index)
        # noinspection PyUnresolvedReferences
        self._combo.currentIndexChanged.connect(self._onLutChangedEvent)

        # Init QCheckbox

        # < Revision 25/10/2024
        self._reverse = QCheckBox('Reverse')
        # noinspection PyUnresolvedReferences
        self._reverse.stateChanged.connect(self.reverseLut)
        # Revision 25/10/2024 >

        # Init QLayout

        hlyout = QHBoxLayout()
        hlyout.addWidget(self._editmin, alignment=Qt.AlignLeft)
        hlyout.addWidget(self._combo, alignment=Qt.AlignHCenter)
        hlyout.addWidget(self._editmax, alignment=Qt.AlignRight)
        vlyout = QVBoxLayout(self)
        vlyout.addWidget(self._canvas)
        vlyout.addLayout(hlyout)
        vlyout.addWidget(self._reverse)
        vlyout.setSpacing(0)
        vlyout.setContentsMargins(5, 5, 5, 5)
        vlyout.setAlignment(self._reverse, Qt.AlignHCenter)
        vlyout.setAlignment(self._canvas, Qt.AlignHCenter)
        self.setLayout(vlyout)

        self.setToolTip('Drag vertical dotted line with mouse to move it,\n'
                        'and modify image windowing settings.')

        self._canvas.setFocusPolicy(Qt.ClickFocus)
        self._canvas.setFocus()
        self._cursor = QCursor()
        self._canvas.setCursor(self._cursor)

        # Draw tool

        if self._volume: self._draw()
        else: self.setEnabled(False)

        # Win32 settings

        if platform == 'win32':
            self._editmin.setStyleSheet('font-size: 8pt')
            self._editmax.setStyleSheet('font-size: 8pt')
            self._combo.setStyleSheet('font-size: 8pt')

    # Private methods

    def _draw(self):
        rmin, rmax = self._volume.display.getRange()
        wmin, wmax = self._volume.display.getWindow()
        if self._volume.display.isDefaultWindow():
            self._lutaxe.set_position([0.0, 0.0, 1.0, self._ratio], which='both')
            self._rect1axe.set_visible(False)
            self._rect2axe.set_visible(False)
        else:
            r = rmax - rmin
            p1 = (wmin - rmin) / r
            p2 = (wmax - rmin) / r
            self._rect1axe.set_position([0.0, 0.0, p1, self._ratio], which='both')
            self._lutaxe.set_position([p1, 0.0, p2-p1, self._ratio], which='both')
            self._rect2axe.set_position([p2, 0.0, 1-p2, self._ratio], which='both')
            self._rect1axe.set_visible(True)
            self._rect2axe.set_visible(True)
        self._canvas.draw()
        self._updateViewWidget()

    def _initDecimals(self):
        if self._volume is not None:
            if self._volume.isFloatDatatype():
                m = self._volume.getMax()
                if -1.0 <= m <= 1.0:
                    try:
                        d = int('{:e}'.format(abs(m)).split('-')[1]) + 1
                        self._decimals = d
                        self._format = '{:.' + str(d) + 'f}'
                    except:
                        self._decimals = 2
                        self._format = '{:.2f}'
                else:
                    self._decimals = 1
                    self._format = '{:.1f}'

    def _initHistAxes(self):

        if self.isDarkMode(): spancolor = 'white'
        else: spancolor = 'black'

        # Init hist axes

        self._histaxe.clear()
        self._histaxe.set_xmargin(0)
        self._histaxe.set_frame_on(False)
        self._histaxe.set_axis_off()

        h = self._histaxe.hist(self._volume.getNumpy().flatten(), bins=100,
                               range=(self._volume.display.getRangeMin(), self._volume.display.getRangeMax()),
                               align='left', orientation='vertical', histtype='stepfilled', color=(0.5, 0.5, 0.5))

        m = mean(self._volume.getNumpy().flatten())
        # < Revision 10/09/2024
        # add condition to avoid exception if m > self._volume.display.getRangeMax()
        if m < self._volume.display.getRangeMax():
            # < Revision 25/03/2025
            # index = where(h[1] > m)[0][0]
            index = where(h[1] > m)[0][0] - 1
            # Revision 25/03/2025 >
            if index < 0: index = 0
            m = max(h[0][index:])
            self._histaxe.set_ylim(0, int(m * 3))
        # Revision 10/09/2024 >

        # Init Span box in hist axes

        self._span = self._histaxe.axvspan(self._volume.display.getWindowMin(),
                                           self._volume.display.getWindowMax(),
                                           facecolor='yellow', edgecolor=spancolor, linewidth=2,
                                           linestyle='--', alpha=0.2)

        if self._volume.getDatatype() in getIntStdDatatypes():
            txtinf = str(int(self._volume.display.getWindowMin()))
            txtsup = str(int(self._volume.display.getWindowMax()))
        else:
            txtinf = self._format.format(self._volume.display.getWindowMin())
            txtsup = self._format.format(self._volume.display.getWindowMax())

        self._winftext = self._histaxe.annotate(txtinf,
                                                xy=(self._volume.display.getWindowMin(),
                                                    self._histaxe.get_ylim()[1] / 2),
                                                xycoords='data', color=spancolor, fontsize='medium',
                                                rotation='vertical', verticalalignment='center',
                                                horizontalalignment='center')
        self._wsuptext = self._histaxe.annotate(txtsup,
                                                xy=(self._volume.display.getWindowMax(),
                                                    self._histaxe.get_ylim()[1] / 2),
                                                xycoords='data', color=spancolor, fontsize='medium',
                                                rotation='vertical', verticalalignment='center',
                                                horizontalalignment='center')

    def _initLutImage(self):
        # Init central AxesImage of the lut axes
        self._lutaxe.clear()
        self._lutaxe.set_xmargin(0)
        self._lutaxe.set_frame_on(False)
        self._lutaxe.set_axis_off()

        imglut = linspace(0, 1, 256)
        imglut = vstack((imglut, imglut))
        self._imglut = self._lutaxe.imshow(imglut, cmap=self._volume.display.getLUT().copyToMatplotlibColormap(),
                                           interpolation='bilinear', aspect='auto')

        r1 = Rectangle((0, 0), 1, 1, facecolor=self._volume.display.getLUT()[0])
        r2 = Rectangle((0, 0), 1, 1, facecolor=self._volume.display.getLUT()[255])

        self._rect1axe.clear()
        self._rect2axe.clear()
        self._rect1axe.set_frame_on(False)
        self._rect2axe.set_frame_on(False)
        self._rect1axe.set_axis_off()
        self._rect2axe.set_axis_off()

        self._rect1axe.add_patch(r1)
        self._rect2axe.add_patch(r2)

    def _initEdit(self):
        datatype = self._volume.getNumpy().dtype
        if self._volume.getDatatype() in getIntStdDatatypes():
            if iinfo(datatype).min < iinfo('int32').min: datatype = 'int32'
            elif iinfo(datatype).max > iinfo('int32').max: datatype = 'int32'
            # < Revision 23/07/2024
            # replace QLineEdit by QDoubleSpinBox
            # self._editmin.setValidator(QIntValidator(iinfo(datatype).min, iinfo(datatype).max))
            # self._editmax.setValidator(QIntValidator(iinfo(datatype).min, iinfo(datatype).max))
            self._editmin.setMinimum(iinfo(datatype).min)
            self._editmin.setMaximum(iinfo(datatype).max)
            self._editmax.setMinimum(iinfo(datatype).min)
            self._editmax.setMaximum(iinfo(datatype).max)
            self._editmin.setDecimals(0)
            self._editmax.setDecimals(0)
            self._editmin.setSingleStep(1.0)
            self._editmax.setSingleStep(1.0)
            self._editmin.setStepType(self._editmin.DefaultStepType)
            self._editmax.setStepType(self._editmax.DefaultStepType)
            self._editmin.setAccelerated(True)
            self._editmax.setAccelerated(True)
            # Revision 23/07/2024 >
        else:
            if finfo(datatype).min < finfo('double').min: datatype = 'double'
            elif finfo(datatype).max > finfo('double').max: datatype = 'double'
            # < Revision 23/07/2024
            # replace QLineEdit by QDoubleSpinBox
            # self._editmin.setValidator(QDoubleValidator(finfo(datatype).min, finfo(datatype).max, self._decimals))
            # self._editmax.setValidator(QDoubleValidator(finfo(datatype).min, finfo(datatype).max, self._decimals))
            self._editmin.setMinimum(finfo(datatype).min)
            self._editmin.setMaximum(finfo(datatype).max)
            self._editmax.setMinimum(finfo(datatype).min)
            self._editmax.setMaximum(finfo(datatype).max)
            self._editmin.setDecimals(self._decimals)
            self._editmax.setDecimals(self._decimals)
            self._editmin.setSingleStep(1 / (10 ** self._decimals))
            self._editmax.setSingleStep(1 / (10 ** self._decimals))
            self._editmin.setStepType(self._editmin.DefaultStepType)
            self._editmax.setStepType(self._editmax.DefaultStepType)
            self._editmin.setAccelerated(True)
            self._editmax.setAccelerated(True)
            # Revision 23/07/2024 >
        # < Revision 23/07/2024
        # replace QLineEdit by QDoubleSpinBox
        # self._editmin.setText(str(self._volume.display.getRangeMin()))
        # self._editmax.setText(str(self._volume.display.getRangeMax()))
        self._editmin.blockSignals(True)
        self._editmax.blockSignals(True)
        self._editmax.setValue(self._volume.display.getRangeMax())
        self._editmin.setValue(self._volume.display.getRangeMin())
        self._editmin.blockSignals(False)
        self._editmax.blockSignals(False)
        # Revision 23/07/2024 >
        self._editmin.setAlignment(Qt.AlignHCenter)
        self._editmax.setAlignment(Qt.AlignHCenter)

    def _get_span_left(self):
        return self._span.xy[0][0]

    def _get_span_right(self):
        return self._span.xy[2][0]

    def _set_span_left(self, x):
        if x < self._volume.display.getRangeMin():
            x = self._volume.display.getRangeMin()
        if x > self._volume.display.getWindowMax():
            x = self._volume.display.getWindowMax()
        self._span.xy[0][0] = x
        self._span.xy[1][0] = x
        self._span.xy[4][0] = x
        return x

    def _set_span_right(self, x):
        if x < self._volume.display.getWindowMin():
            x = self._volume.display.getWindowMin()
        if x > self._volume.display.getRangeMax():
            x = self._volume.display.getRangeMax()
        self._span.xy[2][0] = x
        self._span.xy[3][0] = x
        return x

    def _is_in_span(self, x):
        return self._get_span_left() <= x <= self._get_span_right()

    def _updateViewWidget(self):
        if self._view is not None:
            from Sisyphe.widgets.iconBarViewWidgets import IconBarWidget
            from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
            viewtypes = (IconBarViewWidgetCollection, IconBarWidget, MultiViewWidget, AbstractViewWidget)
            if isinstance(self._view, viewtypes): self._view.updateRender()
            else: raise TypeError('View widget type {} is not supported.'.format(type(self._view)))

    # Qt events

    def _onMouseClickEvent(self, event):
        if event.inaxes == self._histaxe:
            if self._is_in_span(event.xdata):
                tol = (self._volume.display.getRangeMax() -
                       self._volume.display.getRangeMin()) / 20
                self._xleft = self._get_span_left()
                self._xright = self._get_span_right()
                # Drag left line
                if 0 < event.xdata - self._xleft < tol:
                    self._on_move_left_span_flag = True
                    self._on_move_right_span_flag = False
                    self._on_move_span_flag = False
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag right line
                elif 0 < self._xright - event.xdata < tol:
                    self._on_move_right_span_flag = True
                    self._on_move_left_span_flag = False
                    self._on_move_span_flag = False
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag rectangle
                else:
                    self._on_move_span_flag = True
                    self._on_move_left_span_flag = False
                    self._on_move_right_span_flag = False
                    self._cursor.setShape(Qt.ClosedHandCursor)
                    self._canvas.setCursor(self._cursor)
                self._xpos = float(event.xdata)

    def _onMouseMoveEvent(self, event):
        if event.inaxes == self._histaxe:
            if self._on_move_span_flag or self._on_move_left_span_flag or self._on_move_right_span_flag:
                dx = event.xdata - self._xpos
                xleft = self._xleft
                xright = self._xright
                # Drag rectangle
                if self._on_move_span_flag:
                    w = self._xright - self._xleft
                    # Left movement
                    if dx < 0:
                        xleft = self._set_span_left(self._xleft + dx)
                        xright = self._set_span_right(xleft + w)
                    # Right movement
                    else:
                        xright = self._set_span_right(self._xright + dx)
                        xleft = self._set_span_left(xright - w)
                # Drag left line
                elif self._on_move_left_span_flag:
                    dxleft = self._xleft + dx
                    if dxleft < self._xright: xleft = self._set_span_left(dxleft)
                    else: xleft = self._set_span_left(self._xleft)
                # Drag right line
                elif self._on_move_right_span_flag:
                    dxright = self._xright + dx
                    if dxright > self._xleft: xright = self._set_span_right(dxright)
                    else: xright = self._set_span_right(self._xright)
                # Apply windowing
                self._volume.display.setWindow(xleft, xright)
                # < Revision 17/10/2024
                # emit lutWindowChanged signal
                # noinspection PyUnresolvedReferences
                self.lutWindowChanged.emit()
                # Revision 17/10/2024 >
                self._updateViewWidget()
                # Update display
                self._winftext.xyann = (xleft, self._histaxe.get_ylim()[1]/2)
                self._wsuptext.xyann = (xright, self._histaxe.get_ylim()[1]/2)
                if self._volume.getDatatype() in getIntStdDatatypes():
                    self._winftext.set_text(str(int(xleft)))
                    self._wsuptext.set_text(str(int(xright)))
                else:
                    self._winftext.set_text(self._format.format(xleft))
                    self._wsuptext.set_text(self._format.format(xright))
                self._draw()
            else:
                tol = (self._volume.display.getRangeMax() -
                       self._volume.display.getRangeMin()) / 20
                xleft = self._get_span_left()
                xright = self._get_span_right()
                if 0 < event.xdata - xleft < tol:
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag right line
                elif 0 < xright - event.xdata < tol:
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag rectangle
                elif xleft < event.xdata < xright:
                    self._cursor.setShape(Qt.OpenHandCursor)
                    self._canvas.setCursor(self._cursor)
                else:
                    self._cursor.setShape(Qt.ArrowCursor)
                    self._canvas.setCursor(self._cursor)

    # noinspection PyUnusedLocal
    def _onMouseReleaseEvent(self, event):
        self._cursor.setShape(Qt.ArrowCursor)
        self._canvas.setCursor(self._cursor)
        self._on_move_span_flag = False
        self._on_move_left_span_flag = False
        self._on_move_right_span_flag = False

    def _onRangeChangedEvent(self):
        # < Revision 23/07/2024
        # replace QLineEdit by QDoubleSpinBox
        # rmin = float(self._editmin.text())
        # rmax = float(self._editmax.text())
        rmin = self._editmin.value()
        rmax = self._editmax.value()
        # Revision 23/07/2024 >
        if rmin > rmax:
            rmax, rmin = rmin, rmax
            # < Revision 23/07/2024
            # replace QLineEdit by QDoubleSpinBox
            # self._editmin.setText(str(rmin))
            # self._editmax.setText(str(rmax))
            self._editmin.blockSignals(True)
            self._editmax.blockSignals(True)
            self._editmax.setValue(rmax)
            self._editmin.setValue(rmin)
            self._editmin.blockSignals(False)
            self._editmax.blockSignals(False)
            # Revision 23/07/2024 >
        self._volume.display.setRange(rmin, rmax)
        wmin, wmax = self._volume.display.getWindow()
        if wmax > rmax: wmax = rmax
        if wmin < rmin: wmin = rmin
        self._volume.display.setWindow(wmin, wmax)
        # < Revision 17/10/2024
        # emit lutWindowChanged signal
        # noinspection PyUnresolvedReferences
        self.lutWindowChanged.emit()
        # Revision 17/10/2024 >
        # Update hist and span box
        self._initHistAxes()
        # Update display
        self._draw()

    def _onLutChangedEvent(self, index):
        if self._combo.itemText(index) == 'from disk...':
            self.loadLut()
            self._combo.setCurrentIndex(0)
        else:
            name = self._combo.itemData(index)
            if isfile(name):
                path, ext = splitext(name)
                ext = ext.lower()
                if ext == '.lut': self._volume.display.getLUT().load(name)
                elif ext == '.xlut': self._volume.display.getLUT().loadFromXML(name)
                else: raise IOError('file extension {} is not lut format.'.format(ext))
            else: self._volume.display.getLUT().setInternalLut(name)
            # < Revision 17/10/2024
            # emit lutWindowChanged signal
            # noinspection PyUnresolvedReferences
            self.lutChanged.emit()
            # Revision 17/10/2024 >
            # Update AxesImage, left and right rectangles of the lut axes
            self._initLutImage()
            # Update display
            self._draw()

    # Public methods

    def loadLut(self):
        name = QFileDialog.getOpenFileName(self, caption='Open Lut', directory=getcwd(),
                                           filter='XML Lut (*.xlut);;Binary Lut (*.lut);;Txt Lut (*.txt)',
                                           initialFilter='XML Lut (*.xlut)')
        if name[0] != '':
            chdir(dirname(name[0]))
            self._combo.insertFileLut(0, name[0])

    def reverseLut(self):
        self._volume.display.getLUT().reverseLut()
        self._initLutImage()
        self._draw()

    def getVolume(self):
        return self._volume

    def hasVolume(self):
        return self._volume is not None

    def getDisplay(self):
        return self._volume.display

    # < Revision 17/10/2024
    # add getLut method
    def getLut(self):
        return self._volume.display.getLUT()
    # Revision 17/10/2024 >

    def getWindow(self):
        return self._volume.display.getWindow()

    def getWindowMin(self):
        return self._volume.display.getWindowMin()

    def getWindowMax(self):
        return self._volume.display.getWindowMax()

    def getRange(self):
        return self._volume.display.getRange()

    def getRangeMin(self):
        return self._volume.display.getRangeMin()

    def getRangeMax(self):
        return self._volume.display.getRangeMin()

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self._initDecimals()
            self._initHistAxes()
            self._initLutImage()
            self._initEdit()
            # < Revision 17/10/2024
            # index = self._combo.findData(self._volume.display.getLUT().getName())
            index = self._combo.findText(self._volume.display.getLUT().getName())
            # Revision 17/10/2024 >
            if index > -1: self._combo.setCurrentIndex(index)
            self._draw()
            self.setEnabled(True)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def removeVolume(self):
        self._volume = None
        self.setEnabled(False)
        # self.setVisible(False)

    def setDisplay(self, display):
        if isinstance(display, SisypheDisplay):
            self._volume.display = display
            self._initHistAxes()
            self._initLutImage()
            self._initEdit()
            index = self._combo.findData(self._volume.display.getLUT().getName())
            if index > -1: self._combo.setCurrentIndex(index)
            self._draw()
        else: raise TypeError('parameter type {} is not SisypheDisplay.'.format(type(display)))

    def setWindow(self, wmin, wmax):
        self._volume.display.setWindow(wmin, wmax)
        self._set_span_left(wmin)
        self._set_span_right(wmax)
        self._draw()
        # noinspection PyUnresolvedReferences
        self.lutWindowChanged.emit()

    def setWindowMin(self, wmin):
        self._volume.display.setWindowMin(wmin)
        self._set_span_left(wmin)
        self._draw()
        # noinspection PyUnresolvedReferences
        self.lutWindowChanged.emit()

    def setWindowMax(self, wmax):
        self._volume.display.setWindowMax(wmax)
        self._set_span_right(wmax)
        self._draw()
        # noinspection PyUnresolvedReferences
        self.lutWindowChanged.emit()

    # < Revision 24/10/2024
    # add autoWindow method
    def autoWindow(self, cmin: int = 1, cmax: int = 99) -> None:
        self._volume.display.autoWindow(cmin, cmax)
        wmin, wmax = self._volume.display.getWindow()
        self._set_span_left(wmin)
        self._set_span_right(wmax)
        self._draw()
        # noinspection PyUnresolvedReferences
        self.lutWindowChanged.emit()
    # Revision 24/10/2024 >

    # < Revision 24/10/2024
    # add autoWindow method
    def defaultWindow(self) -> None:
        self._volume.display.setDefaultWindow()
        wmin, wmax = self._volume.display.getWindow()
        self._set_span_left(wmin)
        self._set_span_right(wmax)
        self._draw()
        # noinspection PyUnresolvedReferences
        self.lutWindowChanged.emit()
    # Revision 24/10/2024 >

    # < Revision 24/10/2024
    # add setCTBrainWindow method
    def setCTBrainWindow(self) -> None:
        self._volume.display.setCTBrainWindow()
        wmin, wmax = self._volume.display.getWindow()
        self._set_span_left(wmin)
        self._set_span_right(wmax)
        self._draw()
        # noinspection PyUnresolvedReferences
        self.lutWindowChanged.emit()
    # Revision 24/10/2024 >

    # < Revision 24/10/2024
    # add setCTBoneWindow method
    def setCTBoneWindow(self) -> None:
        self._volume.display.setCTBoneWindow()
        wmin, wmax = self._volume.display.getWindow()
        self._set_span_left(wmin)
        self._set_span_right(wmax)
        self._draw()
        # noinspection PyUnresolvedReferences
        self.lutWindowChanged.emit()
    # Revision 24/10/2024 >

    # < Revision 24/10/2024
    # add setCTMetallicWindow method
    def setCTMetallicWindow(self) -> None:
        self._volume.display.setCTMetallicWindow()
        wmin, wmax = self._volume.display.getWindow()
        self._set_span_left(wmin)
        self._set_span_right(wmax)
        self._draw()
        # noinspection PyUnresolvedReferences
        self.lutWindowChanged.emit()
    # Revision 24/10/2024 >

    def setRange(self, rmin, rmax):
        self._volume.display.setRange(rmin, rmax)
        self._initEdit()
        self._onRangeChangedEvent()  # Automatic call ?

    def setRangeMin(self, rmin):
        self._volume.display.setRangeMin(rmin)
        self._initEdit()
        self._onRangeChangedEvent()  # Automatic call ?

    def setRangeMax(self, rmax):
        self._volume.display.setWindowMax(rmax)
        self._initEdit()
        self._onRangeChangedEvent()  # Automatic call ?

    def setViewWidget(self, view):
        from Sisyphe.widgets.iconBarViewWidgets import IconBarWidget
        from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
        viewtypes = (IconBarViewWidgetCollection, IconBarWidget, MultiViewWidget, AbstractViewWidget)
        if isinstance(view, viewtypes): self._view = view
        else: raise TypeError('View widget type {} is not supported.'.format(type(view)))

    def getViewWidget(self):
        return self._view

    def hasViewWidget(self) -> bool:
        return self._view is not None


class LutEditWidget(QWidget):
    """
    LutEditWidget class

    Description
    ~~~~~~~~~~~

    Custom QWidget to edit lut.
    It provides a graphical user interface for users to interactively add, remove, and modify color points in the lut.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> LutEditWidget

    Creation: 08/11/2022
    Last revision: 18/03/2025
    """

    # Class method

    @classmethod
    def getDefaultLutDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'lut')

    # Special method

    """
    Private attributes

    _fig                    Figure, Matplotlib figure
    _canvas                 FigureCanvas, Widget canvas
    _axe                    Axes, Matplotlib axes
    _xlist                  list, Index list of points
    _rgblist                list, RGB color List of point
    _scatter                PathCollection, Matplotlib PathCollection
    _selected               int, Selected point index
    _xpos                   int, Selected point x
    _popup                  QMenu, Popup menu
    _action_new             QAction, New point menu
    _action_color           QAction, Change selected point color menu
    _action_swap_next       QAction, Swap color with next point menu
    _action_swap_previous   QAction, Swap color with previous point menu
    _action_remove          QAction, Remove selected point menu
    _action_clear           QAction, Clear axe menu
    _action_save            QAction, Save lut menu
    """

    def __init__(self, size=512, parent=None):
        super().__init__(parent)

        # Init matplotlib figure

        self._fig = Figure()
        background = self.palette().window().color()
        self._fig.set_facecolor((background.red() / 255,
                                 background.green() / 255,
                                 background.blue() / 255))
        self._canvas = FigureCanvas(self._fig)
        # noinspection PyTypeChecker
        self._axe = self._fig.add_axes([0, 0, 1, 1], frame_on=True, xmargin=0)

        # Init point and color lists

        self._xlist = [0, 255]
        self._rgblist = [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]
        self._scatter = None
        self._selected = None
        self._xpos = None

        # Init event

        # noinspection PyTypeChecker
        self._canvas.mpl_connect('pick_event', self._onPickEvent)
        # noinspection PyTypeChecker
        self._canvas.mpl_connect('motion_notify_event', self._onMouseMoveEvent)
        # noinspection PyTypeChecker
        self._canvas.mpl_connect('button_press_event', self._onMouseClickEvent)
        # noinspection PyTypeChecker
        self._canvas.mpl_connect('button_release_event', self._onMouseReleaseEvent)

        # Init popup menu

        self._popup = QMenu(self)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action_new = QAction('Add new point', self)
        self._action_remove = QAction('Remove point', self)
        self._action_color = QAction('Change point color...', self)
        self._action_swap_next = QAction('Swap color with next point', self)
        self._action_swap_previous = QAction('Swap color with previous point', self)
        self._action_clear = QAction('Clear all', self)
        self._action_save = QAction('Save...', self)
        # noinspection PyUnresolvedReferences
        self._action_new.triggered.connect(self._onMenuNew)
        # noinspection PyUnresolvedReferences
        self._action_color.triggered.connect(self._onMenuColor)
        # noinspection PyUnresolvedReferences
        self._action_swap_next.triggered.connect(self._onMenuSwapNext)
        # noinspection PyUnresolvedReferences
        self._action_swap_previous.triggered.connect(self._onMenuSwapPrevious)
        # noinspection PyUnresolvedReferences
        self._action_remove.triggered.connect(self._onMenuRemove)
        # noinspection PyUnresolvedReferences
        self._action_clear.triggered.connect(self._onMenuClear)
        # noinspection PyUnresolvedReferences
        self._action_save.triggered.connect(self._onMenuSave)
        self._popup.addAction(self._action_new)
        self._popup.addAction(self._action_remove)
        self._popup.addAction(self._action_color)
        self._popup.addAction(self._action_swap_next)
        self._popup.addAction(self._action_swap_previous)
        self._popup.addAction(self._action_clear)
        self._popup.addAction(self._action_save)

        # Init QLayout

        vlyout = QVBoxLayout(self)
        vlyout.addWidget(self._canvas)
        vlyout.setSpacing(0)
        vlyout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vlyout)

        # Init QWidget (size, tooltip, focus, cursor)

        self.setFixedSize(size, int(size / 8))
        self.setToolTip('Right click on background or markers to display popup menu,\n'
                        'Double click on background to add a new marker,\n'
                        'Drag a marker with mouse to move it.')
        self._canvas.setFocusPolicy(Qt.ClickFocus)
        self._canvas.setFocus()
        self._cursor = QCursor()
        self._canvas.setCursor(self._cursor)

        # Draw tool

        self._draw()

    # Private method

    def _draw(self):
        lut = self.getMatplotlibLut()
        # Draw colormap in axes
        self._axe.clear()
        self._axe.set_xmargin(0.05)
        self._axe.set_ymargin(0.25)
        self._axe.set_axis_off()
        imglut = linspace(0, 1, 256)
        imglut = vstack((imglut, imglut))
        self._axe.imshow(imglut, cmap=lut, interpolation='bilinear', aspect='auto')
        # Draw points in axes
        self._scatter = self._axe.scatter(self._xlist, [0.5]*len(self._xlist), marker='^', s=250,
                                          edgecolors='brown', linewidths=2, color=self._rgblist, picker=5, zorder=1)
        self._canvas.draw()

    # Public methods

    def getMatplotlibLut(self):
        # Create rgb dict from points and rgb lists
        rgbdict = {}
        red, green, blue = [], [], []
        for i, c in enumerate(self._rgblist):
            red.append([self._xlist[i] / 255, c[0], c[0]])
            green.append([self._xlist[i] / 255, c[1], c[1]])
            blue.append([self._xlist[i] / 255, c[2], c[2]])
        rgbdict['red'] = red
        rgbdict['green'] = green
        rgbdict['blue'] = blue
        # Create colormap from rgb dict
        # noinspection PyTypeChecker
        cmap = LinearSegmentedColormap('custom', segmentdata=rgbdict, N=256, gamma=1.0)
        cmap.set_over(cmap(255))
        cmap.set_under(cmap(0))
        return cmap

    def getSisypheLut(self):
        lut = SisypheLut()
        cmap = self.getMatplotlibLut()
        lut.copyFromMatplotlibColormap(cmap)
        return lut

    def copyTo(self, display):
        if isinstance(display, SisypheDisplay):
            display.setLUT(self.getSisypheLut())
        else:
            raise TypeError('parameter functype is not SisypheDisplay')

    def save(self):
        self._onMenuSave()

    # Matplotlib event

    def _onMouseClickEvent(self, event):
        if event.inaxes == self._axe:
            if event.dblclick and self._selected is None:
                self._xpos = int(event.xdata)
                self._onMenuNew()
            elif event.button == MouseButton.RIGHT:
                # background right click
                if self._selected is None:
                    self._xpos = int(event.xdata)
                    f = self._fig.dpi / 100
                    p = self.mapToGlobal(QPoint(0, 0))
                    x = int(p.x() + event.x / f)
                    # noinspection PyUnresolvedReferences
                    y = int(p.y() + self._canvas.get_width_height()[1] - event.y / f)
                    self._action_new.setVisible(True)
                    self._action_color.setVisible(False)
                    self._action_swap_next.setVisible(False)
                    self._action_swap_previous.setVisible(False)
                    self._action_remove.setVisible(False)
                    self._action_clear.setVisible(True)
                    self._action_save.setVisible(True)
                    self._popup.popup(QPoint(x, y))
                # scatter right click
                else:
                    self._action_new.setVisible(False)
                    self._action_color.setVisible(True)
                    self._action_clear.setVisible(True)
                    self._action_save.setVisible(True)
                    last = len(self._xlist) - 1
                    if 0 < self._selected < last:
                        self._action_swap_next.setVisible(True)
                        self._action_swap_previous.setVisible(True)
                        self._action_remove.setVisible(True)
                    elif self._selected == last:
                        self._action_swap_next.setVisible(False)
                        self._action_swap_previous.setVisible(True)
                        self._action_remove.setVisible(False)
                    else:
                        self._action_swap_next.setVisible(True)
                        self._action_swap_previous.setVisible(False)
                        self._action_remove.setVisible(False)
                    f = self._fig.dpi / 100
                    p = self.mapToGlobal(QPoint(0, 0))
                    x = int(p.x() + event.x / f)
                    # noinspection PyUnresolvedReferences
                    y = int(p.y() + self._canvas.get_width_height()[1] - event.y / f)
                    self._popup.popup(QPoint(x, y))
            elif event.button == MouseButton.LEFT:
                if self._selected is not None:
                    if self._selected == 0 or self._selected == len(self._xlist) - 1:
                        self._selected = None
                    else:
                        self._cursor.setShape(Qt.ClosedHandCursor)
                        self._canvas.setCursor(self._cursor)
        else:
            self._selected = None

    def _onPickEvent(self, event):
        self._selected = event.ind[0]
        # automatic _onMouseClickEvent call after _onPickEvent

    def _onMouseMoveEvent(self, event):
        if event.inaxes == self._axe:
            if self._selected is not None and event.xdata is not None:
                if self._xlist[self._selected - 1] < event.xdata < self._xlist[self._selected + 1]:
                    self._scatter.get_offsets()[self._selected][0] = event.xdata
                self._canvas.draw()

    def _onMouseReleaseEvent(self, event):
        if self._selected is not None and event.xdata is not None:
            self._xlist[self._selected] = int(event.xdata)
            self._cursor.setShape(Qt.ArrowCursor)
            self._canvas.setCursor(self._cursor)
            self._draw()
        self._selected = None

    # Qt events

    def _onMenuNew(self):
        if self._xpos is not None:
            # < Revision 18/03/2025
            # dialog = QColorDialog()
            # color = dialog.getColor()
            color = colorDialog(title='Select color')
            # Revision 18/03/2025 >
            if color is not None:
                for index, x in enumerate(self._xlist):
                    if self._xpos < x:
                        self._xlist.insert(index, self._xpos)
                        self._rgblist.insert(index, [color.red() / 255,
                                                     color.green() / 255,
                                                     color.blue() / 255])
                        self._draw()
                        break
                self.xpos = None
                self._selected = None
                # if widget in popup menu, display popup when QColorDialog closed
                parent = self.parent()
                if parent is not None and isinstance(parent, TransferWidget):
                    parent.colorDialogClosed.emit()

    def _onMenuRemove(self):
        if self._selected is not None:
            if 0 < self._selected < len(self._xlist) - 1:
                del self._xlist[self._selected]
                del self._rgblist[self._selected]
                self._draw()
                self._selected = None

    def _onMenuColor(self):
        if self._selected is not None:
            # < Revision 18/03/2025
            # dialog = QColorDialog()
            # color = dialog.getColor()
            color = colorDialog(title='Select color')
            # Revision 18/03/2025 >
            if color is not None:
                self._rgblist[self._selected] = [color.red() / 255,
                                                 color.green() / 255,
                                                 color.blue() / 255]
                self._draw()
                self._selected = None
                # if widget in popup menu, display popup when QColorDialog closed
                parent = self.parent()
                if parent is not None and isinstance(parent, TransferWidget):
                    parent.colorDialogClosed.emit()

    def _onMenuSwapNext(self):
        if self._selected is not None:
            if self._selected < len(self._xlist) - 1:
                buff = self._rgblist[self._selected]
                self._rgblist[self._selected] = self._rgblist[self._selected + 1]
                self._rgblist[self._selected + 1] = buff
                self._draw()
                self._selected = None

    def _onMenuSwapPrevious(self):
        if self._selected is not None:
            if self._selected > 0:
                buff = self._rgblist[self._selected]
                self._rgblist[self._selected] = self._rgblist[self._selected - 1]
                self._rgblist[self._selected - 1] = buff
                self._draw()
                self._selected = None

    def _onMenuClear(self):
        self._xlist = [0, 255]
        self._rgblist = [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]
        self._draw()
        self._selected = None

    def _onMenuSave(self):
        name = QFileDialog.getSaveFileName(self, caption='Save Lut', directory=self.getDefaultLutDirectory(),
                                           filter='XML Lut (*.xlut);;Binary Lut (*.lut);;Txt Lut (*.txt)',
                                           initialFilter='XML Lut (*.xlut)')
        if name[0] != '':
            chdir(dirname(name[0]))
            lut = self.getSisypheLut()
            if name[1] == 'XML Lut (*.xlut)':
                lut.saveToXML(name[0])
            elif name[1] == 'Binary Lut (*.lut)':
                lut.save(name[0])
            else:
                lut.saveToTxt(name[0])
        self._selected = None


class ColorTransferWidget(LutEditWidget):
    """
    ColorTransferWidget class

    Description
    ~~~~~~~~~~~

    Custom QWidget to edit and control color transfer function for volume rendering.
    It provides a user-friendly interface for editing color transfer functions, including adding, removing, and
    modifying color points, as well as saving and loading color transfer functions in various formats.

    Inheritance
    ~~~~~~~~~~~

    QWidget - > LutEditWidget - > ColorTransferWidget

    Creation: 10/11/2022
    """

    # Custom Qt signal

    colorTransferChanged = pyqtSignal()

    # Special method

    """
    Private attributes

    _view           Display widget to update when Lut settings changed
    _volume         SisypheVolume
    _transfer       SisypheColorTransfer
    _action_load    QAction, Load color transfer menu
    """

    def __init__(self, volume, view=None, transfer=None, size=512, parent=None):
        super().__init__(size, parent)

        if transfer is None or not isinstance(transfer, SisypheColorTransfer):
            transfer = SisypheColorTransfer()

        self._transfer = transfer
        self._volume = volume
        self._view = view
        self._parent = parent

        if volume is not None and isinstance(volume, SisypheVolume):
            if self._transfer.isColorTransferEmpty():
                self._transfer.setDefaultColor(volume)
                self._copyFromColorTransfer()
                self._draw()

        # Init popup menu

        self._action_load = QAction('Load...', self)
        # noinspection PyUnresolvedReferences
        self._action_load.triggered.connect(self._onMenuLoad)
        self._popup.addAction(self._action_load)

        self.setToolTip('Color transfer function\n\n' + self.toolTip())

    # Private methods

    def _updateTransfer(self):
        r = self._volume.display.getRange()
        w = r[1] - r[0]
        self._transfer.clearColorTransfer()
        for i in range(0, len(self._rgblist)):
            vrgb = [r[0] + self._xlist[i] / 255 * w] + self._rgblist[i]
            self._transfer.addColorTransferElement(vrgb=vrgb)
        # noinspection PyUnresolvedReferences
        self.colorTransferChanged.emit()

    def _updateViewWidget(self):
        if self._view is not None:
            self._view.updateRender()

    def _copyFromColorTransfer(self):
        self._xlist = []
        self._rgblist = []
        rmin, rmax = self._transfer.getRange()
        r = rmax - rmin
        for i in range(0, self._transfer.getColorTransferSize()):
            vrgb = self._transfer.getColorTransferElement(i)
            self._xlist.append((vrgb[0] - rmin) / r * 255)
            self._rgblist.append(vrgb[1:])

    # Public methods

    def getVolume(self):
        return self._volume

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self._transfer.setDefaultColor(volume)
            self._copyFromColorTransfer()
            self._draw()

    def hasVolume(self):
        return self._volume is not None

    def getViewWidget(self):
        return self._view

    def setViewWidget(self, view, getinfos=True):
        # GetInfo = False, if it has TransferWidget parent
        if isinstance(view, VolumeViewWidget):
            self._view = view
            if getinfos:
                self.setVolume(view.getVolume())
                self.setTransfer(view.getTransfer())
        else: raise TypeError('parameter type {} is not VolumeViewWidget.'.format(type(view)))

    def hasViewWidget(self):
        return self._view is not None

    def getTransfer(self):
        return self._transfer

    def setTransfer(self, transfer):
        if isinstance(transfer, SisypheColorTransfer):
            self._transfer = transfer
            self._copyFromColorTransfer()
            self._draw()
            # noinspection PyUnresolvedReferences
            self.colorTransferChanged.emit()

    # Matplotlib events

    def _onMouseReleaseEvent(self, event):
        super()._onMouseReleaseEvent(event)
        self._updateTransfer()
        self._updateViewWidget()

    # Qt events

    def _onMenuNew(self):
        super()._onMenuNew()
        self._updateTransfer()

    def _onMenuColor(self):
        super()._onMenuColor()
        self._updateTransfer()

    def _onMenuSwapNext(self):
        super()._onMenuSwapNext()
        self._updateTransfer()

    def _onMenuSwapPrevious(self):
        super()._onMenuSwapPrevious()
        self._updateTransfer()

    def _onMenuRemove(self):
        super()._onMenuRemove()
        self._updateTransfer()

    def _onMenuClear(self):
        super()._onMenuClear()
        self._updateTransfer()

    def _onMenuSave(self):
        name = QFileDialog.getSaveFileName(self, caption='Save color transfer function', directory=getcwd(),
                                           filter='XML Color transfer (*.xtfer)',
                                           initialFilter='XML Color transfer (*.xtfer)')
        if name[0] != '':
            chdir(dirname(name[0]))
            self._transfer.setID(self._volume.getArrayID())
            self._transfer.saveToXML(name[0])
        self._selected = None

    def _onMenuLoad(self):
        if self._parent is not None and isinstance(self._parent, TransferWidget):
            self._parent.load()
        else:
            name = QFileDialog.getOpenFileName(self, caption='Load color transfer function', directory=getcwd(),
                                               filter='XML Color transfer (*.xtfer)',
                                               initialFilter='XML Color transfer (*.xtfer)')
            if name[0] != '':
                chdir(dirname(name[0]))
                transfer = SisypheColorTransfer()
                transfer.loadFromXML(name[0])
                if transfer.hasSameID(self._volume):
                    self.setTransfer(transfer)
                else:
                    messageBox(self,
                               'Load Color transfer function',
                               text='This color transfer function was not created for current volume.',
                               icon=QMessageBox.Information)
        self._selected = None


class AlphaTransferWidget(QWidget):
    """
    AlphaTransferWidget class

    Description
    ~~~~~~~~~~~

    Custom QWidget to edit and control alpha transfer function for volume rendering.
    It provides a visual representation of the alpha transfer function, allowing users to interactively add, remove,
    and modify alpha transfer elements. It also includes features to save, load, and clear the alpha transfer function.
    The widget displays a histogram of the volume's intensity values, along with markers representing the alpha
    transfer elements. Users can add new alpha transfer elements by double-clicking on the background of the histogram,
    remove existing elements by right-clicking on the markers, and modify the alpha values by dragging the markers
    vertically.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> AlphaTransferWidget

    Creation: 12/11/2022
    """

    # Custom Qt signals

    alphaTransferChanged = pyqtSignal()
    gradientTransferChanged = pyqtSignal()

    # Class method

    @staticmethod
    def _calcGradient(volume):
        if isinstance(volume, SisypheVolume):
            simg = volume.getSITKImage()
            fimg = GradientMagnitude(simg)
            fimg = Clamp(fimg, simg.GetPixelID())
            rvolume = SisypheVolume()
            rvolume.copyFromSITKImage(fimg)
            return rvolume
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    # Special method

    """
    Private attributes

    _parent         TransferWidget parent
    _view           Display widget to update when Lut settings changed
    _fig            Figure, Matplotlib figure
    _canvas         FigureCanvas, Widget canvas
    _axe            Axes, Histogram display
    _volume         SisypheVolume
    _transfer       SisypheColorTransfer
    _type           str, alpha transfer ('alpha') or gradient transfer (gradient)
    _lines          Line2D
    _selected       int
    _xpos           float
    _ypos           float
    _xlist          list
    _ylist          list
    _clist          list
    _info           list
    _h              float
    _margin         float
    _popup          QMenu, Popup menu
    _action_new     QAction, New point menu
    _action_remove  QAction, Remove selected point menu
    _action_clear   QAction, Clear axe menu
    _action_save    QAction, Save color transfer menu
    _action_load    QAction, Load color transfer menu
    _cursor         QCursor, Mouse cursor
    """

    def __init__(self, volume=None, view=None, transfer=None, functype='alpha', size=512, parent=None):
        super().__init__(parent)

        if transfer is None or not isinstance(transfer, SisypheColorTransfer):
            transfer = SisypheColorTransfer()

        self._type = functype
        self._transfer = transfer
        self._view = view
        self._parent = parent

        if volume is not None and isinstance(volume, SisypheVolume):
            if self._transfer.isColorTransferEmpty(): self._transfer.setDefaultColor(volume)
            if self._transfer.isAlphaTransferEmpty(): self._transfer.setDefaultAlpha(volume)
            if functype == 'gradient':
                volume = self._calcGradient(volume)
                if self._transfer.isGradientTransferEmpty(): self._transfer.setDefaultGradient(volume)

        self._volume = volume

        self._fig = Figure()
        # < Revision 18/03/2025
        # background = self.palette().window().color()
        self._fig.set_size_inches(size / 100, size / 100)
        if platform == 'win32':
            p = load_palette('auto')
            background = p.color(QPalette.Base)
        else:
            if parent is not None:
                # noinspection PyTypeChecker
                background = parent.palette().color(QPalette.Button)
            else:
                # noinspection PyTypeChecker
                background = self.palette().color(QPalette.Button)
        # Revision 18/03/2025 >
        self._fig.set_facecolor((background.red() / 255,
                                 background.green() / 255,
                                 background.blue() / 255))
        self._canvas = FigureCanvas(self._fig)
        # noinspection PyTypeChecker
        self._axe = self._fig.add_axes([0, 0, 1, 1], frame_on=False)

        # Init point and color lists

        self._lines = None
        self._xlist = []
        self._ylist = []
        self._clist = []
        self._text = []
        self._h = None
        self._margin = None
        self._selected = None
        self._xpos = None
        self._ypos = None
        if self._volume is not None:
            self._initHist()
            self._initLines()

        # Init event

        # noinspection PyTypeChecker
        self._canvas.mpl_connect('pick_event', self._onPickEvent)
        # noinspection PyTypeChecker
        self._canvas.mpl_connect('motion_notify_event', self._onMouseMoveEvent)
        # noinspection PyTypeChecker
        self._canvas.mpl_connect('button_press_event', self._onMouseClickEvent)
        # noinspection PyTypeChecker
        self._canvas.mpl_connect('button_release_event', self._onMouseReleaseEvent)

        # Init popup menu

        self._popup = QMenu(self)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popup.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popup.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action_new = QAction('Add new point', self)
        self._action_remove = QAction('Remove point', self)
        self._action_clear = QAction('Clear all', self)
        self._action_save = QAction('Save...', self)
        self._action_load = QAction('Load...', self)
        # noinspection PyUnresolvedReferences
        self._action_new.triggered.connect(self._onMenuNew)
        # noinspection PyUnresolvedReferences
        self._action_remove.triggered.connect(self._onMenuRemove)
        # noinspection PyUnresolvedReferences
        self._action_clear.triggered.connect(self._onMenuClear)
        # noinspection PyUnresolvedReferences
        self._action_save.triggered.connect(self._onMenuSave)
        # noinspection PyUnresolvedReferences
        self._action_load.triggered.connect(self._onMenuLoad)
        self._popup.addAction(self._action_new)
        self._popup.addAction(self._action_remove)
        self._popup.addAction(self._action_clear)
        self._popup.addAction(self._action_save)
        self._popup.addAction(self._action_load)

        # Init QLayout

        vlyout = QVBoxLayout(self)
        vlyout.addWidget(self._canvas)
        vlyout.setSpacing(0)
        vlyout.setContentsMargins(5, 5, 5, 5)
        vlyout.setAlignment(self._canvas, Qt.AlignHCenter)
        self.setLayout(vlyout)

        # Init QWidget (size, tooltip, focus, cursor)

        # self.setFixedSize(size, size)
        txt = 'Right click on background or markers to display popup menu,\n' \
              'Double click on background to add a new marker,\n' \
              'Drag marker with mouse to move it.'
        if functype == 'alpha': txt = 'Scalar opacity transfer function\n\n' + txt
        else: txt = 'Gradient opacity transfer function\n\n' + txt
        self.setToolTip(txt)
        self._canvas.setFocusPolicy(Qt.ClickFocus)
        self._canvas.setFocus()
        self._cursor = QCursor()
        self._canvas.setCursor(self._cursor)

        self._canvas.draw()

    # Private methods

    def _initHist(self):
        self._axe.clear()
        self._axe.set_axis_off()

        # Draw histogram
        self._axe.hist(self._volume.getNumpy().flatten(), bins=256,
                       range=(self._volume.display.getRangeMin(), self._volume.display.getRangeMax()),
                       align='left', orientation='vertical', histtype='stepfilled',
                       color=(0.6, 0.6, 0.6), alpha=0.5)

        self._margin = int(self._axe.get_ylim()[1] / 300)
        self._axe.set_ylim(-self._margin, int(self._axe.get_ylim()[1] / 10))
        self._h = self._axe.get_ylim()[1] - self._margin
        xl = self._axe.get_xlim()

        # Draw background
        imgback = linspace(1, 0, 256)
        imgback = vstack((imgback, imgback)).T
        self._axe.imshow(imgback, cmap='gray', interpolation='bilinear', aspect='auto', alpha=1.0,
                         extent=(self._volume.display.getRangeMin(),
                                 self._volume.display.getRangeMax(), 0, self._h))
        self._axe.set_xlim(xl[0], xl[1])

    def _initLines(self):
        self._copyFromTransfer()

        # Lines

        self._lines = self._axe.plot(self._xlist, self._ylist, color='brown', linewidth=2, zorder=1)[0]
        if self._type == 'alpha': color = self._clist
        else: color = 'brown'

        # Scatter

        self._scatter = self._axe.scatter(self._xlist, self._ylist, marker='o', s=100,
                                          edgecolors='brown', linewidths=2, color=color, picker=5, zorder=2)

        # Text

        for i in range(0, len(self._xlist)):
            if self._volume.getDatatype() in getIntStdDatatypes():
                v1 = str(int(self._xlist[i]))
            else:
                v1 = '{:.2f}'.format(self._xlist[i])
            v2 = '{:.2f}'.format(self._ylist[i] / self._h)
            txt = self._axe.annotate('{}\n{}\n'.format(v1, v2),
                                     (self._xlist[i], self._ylist[i]),
                                     xycoords='data', color='brown', fontsize='small',
                                     verticalalignment='bottom', horizontalalignment='center')
            self._text.append(txt)

    def _updateLines(self):
        offset = list(zip(self._xlist, self._ylist))
        self._lines.set_xdata(self._xlist)
        self._lines.set_ydata(self._ylist)
        self._scatter.set_offsets(offset)
        if self._type == 'alpha':
            # noinspection PyUnresolvedReferences
            self._scatter.set_facecolors(self._clist)
        else:
            self._scatter.set_facecolor('brown')
        for i in range(0, len(self._xlist)):
            if self._volume.getDatatype() in getIntStdDatatypes():
                v1 = str(int(self._xlist[i]))
            else:
                v1 = '{:.2f}'.format(self._xlist[i])
            v2 = '{:.2f}'.format(self._ylist[i] / self._h)
            self._text[i].set_text('{}\n{}\n'.format(v1, v2))
        self._canvas.draw()

    def _updateTransfer(self):
        if self._type == 'alpha':
            self._updateAlphaTransfer()
        else:
            self._updateGradientTransfer()

    def _updateAlphaTransfer(self):
        self._transfer.clearAlphaTransfer()
        for i in range(0, len(self._xlist)):
            va = [self._xlist[i], self._ylist[i] / self._h]
            self._transfer.addAlphaTransferElement(va=va)
        # noinspection PyUnresolvedReferences
        self.alphaTransferChanged.emit()

    def _updateGradientTransfer(self):
        self._transfer.clearGradientTransfer()
        for i in range(0, len(self._xlist)):
            va = [self._xlist[i], self._ylist[i] / self._h]
            self._transfer.addGradientTransferElement(va=va)
        # noinspection PyUnresolvedReferences
        self.gradientTransferChanged.emit()

    def _updateViewWidget(self):
        if self._view is not None:
            self._view.updateRender()

    def _copyFromTransfer(self):
        if self._type == 'alpha': self._copyFromAlphaTransfer()
        else: self._copyFromGradientTransfer()

    def _copyFromAlphaTransfer(self):
        self._xlist = []
        self._ylist = []
        self._clist = []
        for i in range(0, self._transfer.getAlphaTransferSize()):
            av = self._transfer.getAlphaTransferElement(i)
            self._xlist.append(av[0])
            self._ylist.append(av[1] * self._h)
            self._clist.append(self._transfer.getColorFromValue(av[0]))

    def _copyFromGradientTransfer(self):
        self._xlist = []
        self._ylist = []
        self._clist = []
        for i in range(0, self._transfer.getGradientTransferSize()):
            av = self._transfer.getGradientTransferElement(i)
            self._xlist.append(av[0])
            self._ylist.append(av[1] * self._h)
            self._clist.append(self._transfer.getColorFromValue(av[0]))

    # Public methods

    def setTransfer(self, transfer):
        if isinstance(transfer, SisypheColorTransfer):
            self._transfer = transfer
            self._copyFromTransfer()
            del self._lines
            del self._scatter
            del self._text
            self._text = []
            self._initHist()
            self._initLines()
            self._canvas.draw()

    def getTransfer(self):
        return self._transfer

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            if self._type == 'alpha':
                self._volume = volume
                self._transfer.setDefaultAlpha(self._volume)
            else:
                self._volume = self._calcGradient(volume)
                self._transfer.setDefaultGradient(volume)
                self._volume.display.setRangeMin(0.0)
                self._volume.display.setRangeMax(volume.display.getRangeMax() - volume.display.getRangeMin())
            self._initHist()
            self._initLines()
        else: raise TypeError('volume parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getVolume(self):
        return self._volume

    def hasVolume(self):
        return self._volume is not None

    def getViewWidget(self):
        return self._view

    def setViewWidget(self, view, getinfos=True):
        # GetInfo = False, if it has TransferWidget parent
        if isinstance(view, VolumeViewWidget):
            self._view = view
            if getinfos:
                self.setVolume(view.getVolume())
                self.setTransfer(view.getTransfer())
        else: raise TypeError('parameter type {} is not VolumeViewWidget.'.format(type(view)))

    def hasViewWidget(self):
        return self._view is not None

    def save(self):
        self._onMenuSave()

    # Matplotlib events

    def _onMouseClickEvent(self, event):
        if event.inaxes == self._axe:
            if event.dblclick and self._selected is None:
                self._xpos = int(event.xdata)
                self._ypos = int(event.ydata)
                self._onMenuNew()
            elif event.button == MouseButton.RIGHT:
                # background right click
                if self._selected is None:
                    self._xpos = int(event.xdata)
                    self._ypos = int(event.ydata)
                    f = self._fig.dpi / 100
                    p = self.mapToGlobal(QPoint(0, 0))
                    x = int(p.x() + event.x / f)
                    # noinspection PyUnresolvedReferences
                    y = int(p.y() + self._canvas.get_width_height()[1] - event.y / f)
                    self._action_new.setVisible(True)
                    self._action_remove.setVisible(False)
                    self._popup.popup(QPoint(x, y))
                # point right click
                else:
                    self._action_new.setVisible(False)
                    last = len(self._xlist) - 1
                    if 0 < self._selected < last:
                        self._action_remove.setVisible(True)
                    elif self._selected == last:
                        self._action_remove.setVisible(False)
                    else:
                        self._action_remove.setVisible(False)
                    f = self._fig.dpi / 100
                    p = self.mapToGlobal(QPoint(0, 0))
                    x = int(p.x() + event.x / f)
                    # noinspection PyUnresolvedReferences
                    y = int(p.y() + self._canvas.get_width_height()[1] - event.y / f)
                    self._popup.popup(QPoint(x, y))
            elif event.button == MouseButton.LEFT:
                if self._selected is not None:
                    self._cursor.setShape(Qt.ClosedHandCursor)
                    self._canvas.setCursor(self._cursor)

    def _onPickEvent(self, event):
        self._selected = event.ind[0]
        # automatic _onMouseClickEvent call after _onPickEvent

    def _onMouseMoveEvent(self, event):
        if event.inaxes == self._axe:
            if self._selected is not None and event.xdata is not None:
                if self._selected == 0 or self._selected == len(self._xlist) - 1:
                    if 0 <= event.ydata <= self._h:
                        self._ylist[self._selected] = event.ydata
                else:
                    if self._xlist[self._selected - 1] <= event.xdata <= self._xlist[self._selected + 1]:
                        self._xlist[self._selected] = event.xdata
                        if self._type == 'alpha':
                            self._clist[self._selected] = list(self._transfer.getColorFromValue(event.xdata)) + [1]
                    if 0 <= event.ydata <= self._h:
                        self._ylist[self._selected] = event.ydata
                self._lines.set_xdata(self._xlist)
                self._lines.set_ydata(self._ylist)
                offset = list(zip(self._xlist, self._ylist))
                self._scatter.set_offsets(offset)
                if self._type == 'alpha':
                    # noinspection PyUnresolvedReferences
                    self._scatter.set_facecolors(self._clist)
                else:
                    self._scatter.set_facecolor('brown')
                if self._volume.getDatatype() in getIntStdDatatypes():
                    v1 = str(int(self._xlist[self._selected]))
                else:
                    v1 = '{:.2f}'.format(self._xlist[self._selected])
                v2 = '{:.2f}'.format(self._ylist[self._selected] / self._h)
                self._text[self._selected].set_text('{}\n{}\n'.format(v1, v2))
                self._text[self._selected].xyann = (self._xlist[self._selected], self._ylist[self._selected])
                self._canvas.draw()

    def _onMouseReleaseEvent(self, event):
        if self._selected is not None and event.xdata is not None:
            self._cursor.setShape(Qt.ArrowCursor)
            self._canvas.setCursor(self._cursor)
            self._updateTransfer()
            self._updateViewWidget()
        self._selected = None

    # Qt events

    def _onMenuNew(self):
        for index, x in enumerate(self._xlist):
            if self._xpos < x:
                self._xlist.insert(index, self._xpos)
                self._ylist.insert(index, self._ypos)
                if self._volume.getDatatype() in getIntStdDatatypes():
                    v1 = str(int(self._xlist[index]))
                else:
                    v1 = '{:.2f}'.format(self._xlist[index])
                v2 = '{:.2f}'.format(self._ylist[index] / self._h)
                txt = self._axe.annotate('{}\n{}\n'.format(v1, v2),
                                         (self._xlist[index], self._ylist[index]),
                                         xycoords='data', color='brown', fontsize='small',
                                         verticalalignment='bottom', horizontalalignment='center')
                self._text.insert(index, txt)
                if self._type == 'alpha':
                    self._clist.insert(index, list(self._transfer.getColorFromValue(self._xpos)) + [1])
                self._updateLines()
                self._canvas.draw()
                self._updateTransfer()
                break
        self._xpos = None
        self._Ypos = None
        self._selected = None

    def _onMenuRemove(self):
        if self._selected is not None:
            if 0 < self._selected < len(self._xlist) - 1:
                del self._xlist[self._selected]
                del self._ylist[self._selected]
                # noinspection PyArgumentList
                self._text[self._selected].remove()
                del self._text[self._selected]
                if self._type == 'alpha':
                    del self._clist[self._selected]
                    # noinspection PyUnresolvedReferences
                    self._scatter.set_facecolors(self._clist)
                self._updateLines()
                self._selected = None
                self._canvas.draw()
                self._updateTransfer()

    def _onMenuClear(self):
        self._xlist = [self._volume.display.getRangeMin(), self._volume.display.getRangeMax()]
        self._ylist = [0, self._h]
        if self._type == 'alpha':
            self._clist = [list(self._transfer.getColorFromValue(self._volume.display.getRangeMin())) + [1],
                           list(self._transfer.getColorFromValue(self._volume.display.getRangeMax())) + [1]]
        self._updateTransfer()
        del self._lines
        del self._scatter
        del self._text
        self._text = []
        self._initHist()
        self._initLines()
        self._canvas.draw()

    def _onMenuSave(self):
        name = QFileDialog.getSaveFileName(self, caption='Save color transfer function', directory=getcwd(),
                                           filter='XML Color transfer (*.xtfer)',
                                           initialFilter='XML Color transfer (*.xtfer)')
        if name[0] != '':
            chdir(dirname(name[0]))
            self._transfer.setID(self._volume.getArrayID())
            self._transfer.saveToXML(name[0])
        self._selected = None

    def _onMenuLoad(self):
        if self._parent is not None and isinstance(self._parent, TransferWidget):
            self._parent.load()
        else:
            name = QFileDialog.getOpenFileName(self, caption='Open color transfer function', directory=getcwd(),
                                               filter='XML Color transfer (*.xtfer)',
                                               initialFilter='XML Color transfer (*.xtfer)')
            if name[0] != '':
                chdir(dirname(name[0]))
                transfer = SisypheColorTransfer()
                transfer.loadFromXML(name[0])
                if transfer.hasSameID(self._volume):
                    self.setTransfer(transfer)
                else:
                    messageBox(self,
                               'Open Color transfer function',
                               text='This color transfer function was not created for current volume.',
                               icon=QMessageBox.Information)
        self._selected = None


class TransferWidget(QWidget):
    """
    TransferWidget class

    Description
    ~~~~~~~~~~~

    Custom QWidget to edit and control color and alpha transfer functions for volume rendering. It is a complex widget
    that integrates multiple functionalities, such as color transfer widget, alpha transfer widget, gradient transfer
    widget, and a file dialog for loading and saving color transfer functions.

    Inheritance
    ~~~~~~~~~~~

    QWidget - > TransferWidget

    Creation: 12/11/2022
    Last revision: 01/05/2025
    """

    # Custom Qt signals

    colorDialogClosed = pyqtSignal()
    gradientTransferVisibilityChanged = pyqtSignal(bool)

    # Special method

    """
    Private attributes

    _view       Display widget to update when Lut settings changed
    _volume     SisypheVolume
    _transfer   SisypheColorTransfer
    _color      ColorTransferWidget
    _alpha      AlphaTransferWidget
    _gradient   AlphaTransferWidget
    """

    def __init__(self, volume=None, view=None, transfer=None, gradient=True, size=512, parent=None):
        super().__init__(parent)

        self._volume = volume
        self._view = view

        if transfer is None: transfer = SisypheColorTransfer()
        self._transfer = transfer

        self._color = ColorTransferWidget(volume, self._view, self._transfer, size, self)
        self._alpha = AlphaTransferWidget(volume, self._view, self._transfer, 'alpha', size, self)
        if gradient: self._gradient = AlphaTransferWidget(volume, self._view, self._transfer, 'gradient', size, self)
        else: self._gradient = None

        # Init event

        # noinspection PyUnresolvedReferences
        self._color.colorTransferChanged.connect(self._updateColorTransfer)

        self._labelalpha = QLabel('Scalar transfer function')
        if gradient:
            self._labelgrad = QCheckBox('Gradient transfer function')
            # < Revision 01/05/2025
            self._labelgrad.setChecked(False)
            self._gradient.setEnabled(False)
            self._gradient.setVisible(False)
            if self._view is not None:
                self._view.gradientOpacityOff()
            # Revision 01/05/2025 >
            # noinspection PyUnresolvedReferences
            self._labelgrad.stateChanged.connect(self._checkBoxChanged)

        lyout = QHBoxLayout()
        lyout.setSpacing(5)
        self._open = QPushButton('Open')
        # noinspection PyUnresolvedReferences
        self._open.clicked.connect(self.load)
        self._save = QPushButton('Save')
        # noinspection PyUnresolvedReferences
        self._save.clicked.connect(self.save)
        lyout.addStretch()
        lyout.addWidget(self._open)
        lyout.addWidget(self._save)
        lyout.addStretch()

        # Init QLayout

        vlyout = QVBoxLayout(self)
        vlyout.addWidget(self._labelalpha)
        vlyout.addWidget(self._alpha)
        # < Revision 01/05/2025
        # vlyout.addWidget(self._labelgrad)
        # vlyout.addWidget(self._gradient)
        if gradient:
            vlyout.addWidget(self._labelgrad)
            vlyout.addWidget(self._gradient)
        # Revision 01/05/2025 >
        vlyout.addWidget(self._color)
        vlyout.addLayout(lyout)

        vlyout.setAlignment(self._labelalpha, Qt.AlignHCenter)
        vlyout.setAlignment(self._labelgrad, Qt.AlignHCenter)
        vlyout.setAlignment(self._color, Qt.AlignHCenter)

        vlyout.setSpacing(0)
        vlyout.setContentsMargins(5, 5, 5, 5)
        vlyout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self.setLayout(vlyout)

    # Private method

    def _updateColorTransfer(self):
        # Update color in markers when color transfer function changes
        # noinspection PyProtectedMember
        self._alpha._copyFromAlphaTransfer()
        # noinspection PyProtectedMember
        self._alpha._updateLines()

    def _checkBoxChanged(self):
        if self._gradient is not None:
            if self._labelgrad.isChecked():
                self._gradient.setEnabled(True)
                # < Revision 01/05/2025
                self._gradient.setVisible(True)
                # Revision 01/05/2025 >
                if self.hasViewWidget():
                    self._view.gradientOpacityOn()
                # noinspection PyUnresolvedReferences
                self.gradientTransferVisibilityChanged.emit(True)
            else:
                self._gradient.setEnabled(False)
                # < Revision 01/05/2025
                self._gradient.setVisible(False)
                # Revision 01/05/2025 >
                if self.hasViewWidget():
                    self._view.gradientOpacityOff()
                # noinspection PyUnresolvedReferences
                self.gradientTransferVisibilityChanged.emit(True)

    # Public methods

    def getVolume(self):
        return self._volume

    def setVolume(self, volume, gradient=True):
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self._color.setVolume(volume)
            self._alpha.setVolume(volume)
            if gradient is True and self._gradient is not None:
                self._gradient.setVolume(volume)
                # < Revision 01/05/2025
                if self._labelgrad.isChecked(): self._view.gradientOpacityOn()
                else: self._view.gradientOpacityOff()
                # Revision 01/05/2025 >

    def hasVolume(self):
        return self._volume is not None

    def getViewWidget(self):
        return self._view

    def setViewWidget(self, view, gradient=True):
        if isinstance(view, VolumeViewWidget):
            self._view = view
            self.setVolume(self._view.getVolume())
            self.setTransfer(self._view.getTransfer())
            self._color.setViewWidget(self._view, getinfos=False)
            self._alpha.setViewWidget(self._view, getinfos=False)
            if gradient is True and self._gradient is not None:
                self._gradient.setViewWidget(self._view, getinfos=False)
        else: raise TypeError('parameter type {} is not VolumeViewWidget.'.format(type(view)))

    def hasViewWidget(self):
        return self._view is not None

    def getTransfer(self):
        return self._transfer

    def setTransfer(self, transfer, gradient=True):
        if isinstance(transfer, SisypheColorTransfer):
            self._transfer = transfer
            self._color.setTransfer(transfer)
            self._alpha.setTransfer(transfer)
            if gradient is not None and self._gradient is not None:
                self._gradient.setTransfer(transfer)

    def load(self):
        name = QFileDialog.getOpenFileName(self,
                                           caption='Open color transfer function',
                                           directory=getcwd(),
                                           filter='XML Color transfer (*.xtfer)',
                                           initialFilter='XML Color transfer (*.xtfer)')
        if name[0] != '':
            chdir(dirname(name[0]))
            transfer = SisypheColorTransfer()
            transfer.loadFromXML(name[0])
            if transfer.hasSameID(self._volume):
                self.setTransfer(transfer)
            else:
                messageBox(self,
                           'Open Color transfer function',
                           text='This color transfer function was not created for current volume.',
                           icon=QMessageBox.Information)
        # noinspection PyUnresolvedReferences
        self.colorDialogClosed.emit()

    def save(self):
        self._color.save()
        # noinspection PyUnresolvedReferences
        self.colorDialogClosed.emit()


class ComboBoxLut(QComboBox):
    """
    ComboBoxLut class

    Description
    ~~~~~~~~~~~

    Custom ComboBox to select lut for visualization purposes.
    It provides a user-friendly interface for selecting and displaying different LUTs, both internal and
    external files.

    Inheritance
    ~~~~~~~~~~~

    QComboBox -> ComboBoxLut

    Creation: 20/11/2022
    Last revision: 02/06/2025
    """

    # Class methods

    @staticmethod
    def _setPath(pathname):
        if pathname is not None and exists(pathname):
            if not isdir(pathname):
                pathname = dirname(pathname)
        else:
            pathname = getcwd()
        return pathname

    @classmethod
    def getDefaultLutDirectory(cls):
        import Sisyphe.gui
        return join(dirname(abspath(Sisyphe.gui.__file__)), 'lut')

    # Special method

    def __init__(self, pathname=None, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(32, 20))
        self._addInternalLut()  # Add internal lut items
        if pathname is not None: self.addFilesLut(pathname)  # Add file lut items
        else: self.addFilesLut(self.getDefaultLutDirectory())
        # < Revision 02/06/2025
        self.model().sort(0)
        # Revision 02/06/2025 >

    # Private methods

    def _addInternalLut(self):
        for name in SisypheLut.getColormapList():
            lut = get_cmap(name, 256)
            self.addItem(QIcon(drawLutToPixmap(lut, 128)), SisypheLut.getColormapFromName(name), userData=name)

    def _getLutFiles(self, pathname=None):
        pathname = self._setPath(pathname)
        filelist = []
        for i in getLutExt():
            ext = '*' + i
            filelist += glob(join(pathname, ext))
        return filelist

    # Public methods

    def addLut(self, lut):
        self.blockSignals(True)
        try:
            if isinstance(lut, (ListedColormap, LinearSegmentedColormap)):
                cmap = lut
                lut = SisypheLut()
                lut.copyFromMatplotlibColormap(cmap)
            if isinstance(lut, SisypheLut):
                if lut.isFileLut():
                    self.addItem(QIcon(drawLutToPixmap(lut, 128)),
                                 splitext(basename(lut.getName()))[0], userData=lut.getFilename())
                elif lut.isInternalLut():
                    self.addItem(QIcon(drawLutToPixmap(lut, 128)),
                                 SisypheLut.getColormapFromName(lut.getName()), userData=lut.getName())
        finally:
            self.blockSignals(False)

    def addFileLut(self, name):
        if exists(name):
            path, ext = splitext(name)
            ext = ext.lower()
            if ext in getLutExt():
                lut = SisypheLut()
                if ext == '.lut':
                    lut.load(name)
                elif ext == '.xlut':
                    lut.loadFromXML(name)
                else:
                    raise IOError('file extension {} is not Lut.'.format(ext))
                self.addLut(lut)

    def insertLut(self, index, lut):
        self.blockSignals(True)
        try:
            if isinstance(lut, (ListedColormap, LinearSegmentedColormap)):
                cmap = lut
                lut = SisypheLut()
                lut.copyFromMatplotlibColormap(cmap)
            if isinstance(lut, SisypheLut):
                if lut.isFileLut():
                    self.insertItem(index, QIcon(drawLutToPixmap(lut, 128)),
                                    splitext(basename(lut.getName()))[0], userData=lut.getFilename())
                elif lut.isInternalLut():
                    self.insertItem(index, QIcon(drawLutToPixmap(lut, 128)),
                                    SisypheLut.getColormapFromName(lut.getName()), userData=lut.getName())

        finally:
            self.blockSignals(False)

    def insertFileLut(self, index, name):
        if exists(name):
            path, ext = splitext(name)
            ext = ext.lower()
            if ext in getLutExt():
                lut = SisypheLut()
                if ext == '.lut':
                    lut.load(name)
                elif ext == '.xlut':
                    lut.loadFromXML(name)
                else:
                    raise IOError('file extension {} is not Lut.'.format(ext))
                self.insertLut(index, lut)

    def addFilesLut(self, pathname):
        self.blockSignals(True)
        try:
            filelist = self._getLutFiles(pathname)
            if len(filelist) > 0:
                lut = SisypheLut()
                for file in filelist:
                    path, ext = splitext(file)
                    ext = ext.lower()
                    if ext == '.lut': lut.load(file)
                    elif ext == '.xlut': lut.loadFromXML(file)
                    else: raise IOError('file extension {} is not Lut.'.format(ext))
                    path = split(path)[1].lower()
                    self.addItem(QIcon(drawLutToPixmap(lut, 128)), path, userData=file)
        finally: self.blockSignals(False)

    def getCurrentAsMatplotlibColormap(self):
        name = self.currentData()
        # Internal
        if name in SisypheLut().getColormapList():
            lut = get_cmap(name, 256)
        # File
        else:
            if exists(name):
                lut = SisypheLut()
                path, ext = splitext(name)
                ext = ext.lower()
                if ext == '.lut':
                    lut.load(name)
                elif ext == '.xlut':
                    lut.loadFromXML(name)
                else:
                    raise IOError('file extension {} is not Lut.'.format(ext))
                lut = SisypheLut().copyToMatplotlibColormap()
            else:
                raise IOError('No such file {}.'.format(name))
        return lut

    def getCurrentAsSisypheLut(self):
        lut = SisypheLut()
        name = self.currentData()
        # Internal
        if name in SisypheLut().getColormapList():
            lut.setInternalLut(name)
        # File
        else:
            if exists(name):
                path, ext = splitext(name)
                ext = ext.lower()
                if ext == '.lut':
                    lut.load(name)
                elif ext == '.xlut':
                    lut.loadFromXML(name)
                else:
                    raise IOError('file extension {} is not Lut.'.format(ext))
            else:
                raise IOError('No such file {}.'.format(name))
        return lut


class PopupMenuLut(QMenu):
    """
    PopupMenuLut class

    Description
    ~~~~~~~~~~~

    PopupMenu to select lut for visualization purposes.
    It provides a user-friendly interface for selecting and displaying different LUTs, both internal and
    external files.

    Inheritance
    ~~~~~~~~~~~

    QMenu -> PopupMenuLut

    Creation: 20/11/2022
    """

    # Class methods

    @staticmethod
    def _setPath(pathname):
        if pathname is not None and exists(pathname):
            if not isdir(pathname):
                pathname = dirname(pathname)
        else:
            pathname = getcwd()
        return pathname

    @staticmethod
    def getCurrentAsMatplotlibColormap(action):
        if isinstance(action, QAction):
            name = action.data()
            # Internal
            if name in SisypheLut().getColormapList():
                lut = get_cmap(name, 256)
            # File
            else:
                lut = SisypheLut()
                path, ext = splitext(name)
                if ext == '.lut':
                    lut.load(name)
                else:
                    lut.loadFromXML(name)
                lut = SisypheLut().copyToMatplotlibColormap()
            return lut
        else:
            raise TypeError('parameter functype is not QAction.')

    @staticmethod
    def getCurrentAsSisypheLut(action):
        if isinstance(action, QAction):
            lut = SisypheLut()
            name = action.data()
            # Internal
            if name in SisypheLut().getColormapList():
                lut.setInternalLut(name)
            # File
            else:
                path, ext = splitext(name)
                if ext == '.lut':
                    lut.load(name)
                else:
                    lut.loadFromXML(name)
            return lut
        else:
            raise TypeError('parameter functype is not QAction.')

    # Special method

    def __init__(self, pathname=None, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(32, 20))
        self._addInternalLut()  # Add internal lut items
        if pathname is not None:
            self.addFilesLut(pathname)  # Add file lut items

    # Private methods

    def _addInternalLut(self):
        for name in SisypheLut.getColormapList():
            lut = get_cmap(name, 256)
            action = QAction(QIcon(drawLutToPixmap(lut, 128)), SisypheLut.getColormapFromName(name), self)
            action.setData(name)
            self.addAction(action)

    def _getLutFiles(self, pathname=None):
        pathname = self._setPath(pathname)
        filelist = []
        for i in getLutExt():
            ext = '*' + i
            filelist += glob(join(pathname, ext))
        return filelist

    # Public methods

    def addLut(self, lut):
        self.blockSignals(True)
        try:
            if isinstance(lut, (ListedColormap, LinearSegmentedColormap)):
                cmap = lut
                lut = SisypheLut()
                lut.copyFromMatplotlibColormap(cmap)
            if isinstance(lut, SisypheLut):
                action = QAction(QIcon(drawLutToPixmap(lut, 128)), '', self)
                action.setData(lut.getName())
                # noinspection PyTypeChecker
                self.addMenu(action)
        finally:
            self.blockSignals(False)

    def addFileLut(self, name):
        if exists(name):
            path, ext = splitext(name)
            if ext in getLutExt():
                lut = SisypheLut()
                if ext == '.lut': lut.load(name)
                else: lut.loadFromXML(name)
                self.addLut(lut)

    def addFilesLut(self, pathname):
        self.blockSignals(True)
        try:
            filelist = self._getLutFiles(pathname)
            if len(filelist) > 0:
                lut = SisypheLut()
                for file in filelist:
                    path, ext = splitext(file)
                    if ext == '.lut': lut.load(file)
                    else: lut.loadFromXML(file)
                    action = QAction(QIcon(drawLutToPixmap(lut, 128)), '', self)
                    action.setData(file)
                    # noinspection PyTypeChecker
                    self.addMenu(action)
        finally:
            self.blockSignals(False)
