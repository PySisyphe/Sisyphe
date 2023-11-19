"""
    External packages/modules

        Name            Link                                                        Usage

        Matplotlib      https://matplotlib.org/                                     Graph tool
        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from numpy import iinfo
from numpy import finfo
from numpy import median

from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QIntValidator
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QPushButton

from SimpleITK import GetImageFromArray
from SimpleITK import GetArrayViewFromImage
from SimpleITK import Clamp
from SimpleITK import BinaryThreshold
from SimpleITK import OtsuThresholdImageFilter
from SimpleITK import GradientMagnitudeRecursiveGaussian

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheConstants import _INTDATATYPES
from Sisyphe.widgets.iconBarViewWidgets import IconBarSliceViewWidget

"""
    Class hierarchy
    
        QWidget -> ThresholdWidget -> GradientThresholdWidget
                -> ThresholdViewWidget -> GradientThresholdViewWidget
"""


class ThresholdWidget(QWidget):
    """
        ThresholdWidget class

        Inheritance

            QWidget -> ThresholdWidget

        Private attributes

            _fig            Figure instance, matplotlib figure
            _canvas         FigureCanvas instance, tool canvas
            _imgaxe         Axes instance, image and ROI display area
            _axe            Axes instance, histogram display area
            _volume         SisypheVolume
            _currentslice   int, current slice displayed

        Public methods

            getVolume()
            setVolume()
            setThreshold()
            setMinThreshold()
            setMaxThreshold()
            getThresholds()
            getMinThreshold()
            getMaxThreshold()
            setAutoButtonVisibility(bool)
            bool = getAutoButtonVisibility()
            setThresholdFlag(int)
            int = getThresholdFlag()
            setThresholdFlagToMinimum()
            setThresholdFlagToMaximum()
            setThresholdFlagToTwo()
            setThresholdFlagButtonsVisibility(bool)
            bool = getThresholdFlagButtonsVisibility()

            inherited QWidget methods
    """
    # Special method

    def __init__(self, volume, size=256, parent=None):
        super().__init__(parent)
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self._currentslice = 0

            # Init matplotlib figure

            self._fig = Figure(constrained_layout=True)
            background = self.palette().window().color()
            self._fig.set_facecolor((background.red() / 255,
                                     background.green() / 255,
                                     background.blue() / 255))

            self._canvas = FigureCanvas(self._fig)
            grid = self._fig.add_gridspec(nrows=1, ncols=2, hspace=0, wspace=0)
            self._imgaxe = self._fig.add_subplot(grid[0, 0])
            self._histaxe = self._fig.add_subplot(grid[0, 1])

            # Init QLineEdit

            self._editmin = QLineEdit()
            self._editmax = QLineEdit()
            self._editmin.setToolTip('Minimum threshold')
            self._editmax.setToolTip('Maximum threshold')
            self._editmin.setFixedWidth(60)
            self._editmax.setFixedWidth(60)
            self._initEdit()
            self._editmin.returnPressed.connect(self._onThresholdChangedEvent)
            self._editmax.returnPressed.connect(self._onThresholdChangedEvent)

            # Init Buttons

            self._autobutton = QPushButton('Auto')
            self._autobutton.setFixedWidth(60)
            self._autobutton.clicked.connect(self._onButtonAutoEvent)
            self._minflag = QRadioButton('Min.')
            self._maxflag = QRadioButton('Max.')
            self._twoflag = QRadioButton('Two')
            self._twoflag.setChecked(True)
            self._minflag.setToolTip('A single threshold above the minimum value.')
            self._maxflag.setToolTip('A single threshold below the maximum value.')
            self._twoflag.setToolTip('Two thresholds between minimum and maximum value.')
            self._minflag.clicked.connect(self._onThresholdFlagChangeEvent)
            self._maxflag.clicked.connect(self._onThresholdFlagChangeEvent)
            self._twoflag.clicked.connect(self._onThresholdFlagChangeEvent)

            # Init ROI cmap

            buff = [[1.0, 0.0, 0.0, 1.0]] * 255
            buff.insert(0, [0.0, 0.0, 0.0, 0.0])
            self._roicmap = ListedColormap(buff, 'r', 256)
            self._roicmap.set_over(self._roicmap(255))
            self._roicmap.set_under(self._roicmap(0))

            # Init matplotlib axes

            self._span = None
            self._thresholdinftext = None
            self._thresholdsuptext = None
            self._initHistAxes()
            self._initImgAxes()

            # Init matplotlib events

            self._canvas.mpl_connect('button_press_event', self._onMouseClickEvent)
            self._canvas.mpl_connect('motion_notify_event', self._onMouseMoveEvent)
            self._canvas.mpl_connect('button_release_event', self._onMouseReleaseEvent)
            self._canvas.mpl_connect('key_press_event', self._onKeyPressEvent)
            self._canvas.mpl_connect('scroll_event', self._onWheelEvent)
            self._on_move_span_flag = False
            self._on_move_left_span_flag = False
            self._on_move_right_span_flag = False
            self._xpos = None
            self._xleft = None
            self._xright = None

            # Init QLayout

            lyout = QGridLayout()
            lyout.addWidget(self._canvas, 0, 0, 1, 2)
            lyout.setSpacing(0)
            lyout.setContentsMargins(0, 0, 0, 0)

            hlyout = QHBoxLayout()
            hlyout.setDirection(QHBoxLayout.LeftToRight)
            hlyout.addStretch()
            hlyout.addWidget(self._minflag)
            hlyout.addWidget(self._maxflag)
            hlyout.addWidget(self._twoflag)
            hlyout.addStretch()
            lyout.addLayout(hlyout, 1, 0)

            hlyout = QHBoxLayout()
            hlyout.setDirection(QHBoxLayout.RightToLeft)
            hlyout.addStretch()
            hlyout.addWidget(self._editmax)
            hlyout.addStretch()
            hlyout.addWidget(self._autobutton)
            hlyout.addStretch()
            hlyout.addWidget(self._editmin)
            hlyout.addStretch()
            lyout.addLayout(hlyout, 1, 1)

            self.setLayout(lyout)

            # Init QWidget (size, tooltip, focus, cursor)

            self.setFixedSize(size * 2, size)
            self.setToolTip('Left click and drag vertical dotted line to move it\n'
                            'and modify threshold settings.\n'
                            'Mouse Wheel or up/down keys to change current slice.')

            self._canvas.setFocusPolicy(Qt.ClickFocus)
            self._canvas.setFocus()
            self._cursor = QCursor()
            self._canvas.setCursor(self._cursor)

            # Draw tool

            self._canvas.draw()
        else:
            raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    # Private methods

    def _initHistAxes(self):
        # Init hist axes

        self._histaxe.clear()
        self._histaxe.set_xmargin(0)
        self._histaxe.set_frame_on(False)
        self._histaxe.set_axis_off()

        self._histaxe.hist(self._volume.getNumpy().flatten(), bins=256,
                           range=(self._volume.display.getRangeMin(), self._volume.display.getRangeMax()),
                           align='left', orientation='vertical', histtype='stepfilled', color=(0.5, 0.5, 0.5))

        self._histaxe.set_ylim(0, int(self._histaxe.get_ylim()[1] / 10))

        # Init Span box in hist axes

        self._span = self._histaxe.axvspan(self.getMinThreshold(),
                                           self.getMaxThreshold(),
                                           facecolor='yellow', edgecolor='brown', linewidth=2,
                                           linestyle='--', alpha=0.2)

        if self._volume.getDatatype() in _INTDATATYPES:
            txtinf = str(int(self.getMinThreshold()))
            txtsup = str(int(self.getMaxThreshold()))
        else:
            txtinf = '{:.2f}'.format(self.getMinThreshold())
            txtsup = '{:.2f}'.format(self.getMaxThreshold())

        self._thresholdinftext = self._histaxe.annotate(txtinf,
                                                        xy=(self.getMinThreshold(),
                                                            self._histaxe.get_ylim()[1] / 2),
                                                        xycoords='data', color='brown', fontsize='small',
                                                        rotation='vertical', verticalalignment='center',
                                                        horizontalalignment='center')
        self._thresholdsuptext = self._histaxe.annotate(txtsup,
                                                        xy=(self.getMaxThreshold(),
                                                            self._histaxe.get_ylim()[1] / 2),
                                                        xycoords='data', color='brown', fontsize='small',
                                                        rotation='vertical', verticalalignment='center',
                                                        horizontalalignment='center')

    def _initImgAxes(self):
        self._imgaxe.clear()
        self._imgaxe.set_xmargin(0)
        self._imgaxe.set_frame_on(False)
        self._imgaxe.set_axis_off()
        self._currentslice = int(self._volume.getSize()[2] / 2)
        self._drawImage()

    def _drawImage(self):
        npimg = self._volume.getNumpy()[self._currentslice, :, :]

        self._imgaxe.imshow(npimg, origin='lower', cmap=self._volume.display.getLUT().copyToMatplotlibColormap(),
                            interpolation='bilinear', aspect='auto')

        tmin = self.getMinThreshold()
        tmax = self.getMaxThreshold()
        simg = GetImageFromArray(npimg)
        fimg = BinaryThreshold(simg, lowerThreshold=tmin, upperThreshold=tmax, insideValue=1, outsideValue=0)

        self._imgaxe.imshow(GetArrayViewFromImage(fimg), origin='lower',
                            cmap=self._roicmap, alpha=0.5, interpolation='nearest', aspect='auto')
        self._canvas.draw_idle()  # Update canvas

    def _initEdit(self):
        datatype = self._volume.getNumpy().dtype
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmin.setText(str(int(self._volume.display.getRangeMin())))
            self._editmax.setText(str(int(self._volume.display.getRangeMax())))
            self._editmin.setValidator(QIntValidator(iinfo(datatype).min, iinfo(datatype).max))
            self._editmax.setValidator(QIntValidator(iinfo(datatype).min, iinfo(datatype).max))
        else:
            self._editmin.setText('{:.2f}'.format(self._volume.display.getRangeMin()))
            self._editmax.setText('{:.2f}'.format(self._volume.display.getRangeMax()))
            self._editmin.setValidator(QDoubleValidator(iinfo(datatype).min, iinfo(datatype).max))
            self._editmax.setValidator(QDoubleValidator(iinfo(datatype).min, iinfo(datatype).max))
        self._editmin.setAlignment(Qt.AlignHCenter)
        self._editmax.setAlignment(Qt.AlignHCenter)

    def _get_span_left(self):
        return self._span.xy[0][0]

    def _get_span_right(self):
        return self._span.xy[2][0]

    def _set_span_left(self, x):
        if x < self._volume.display.getRangeMin():
            x = self._volume.display.getRangeMin()
        if x > self._get_span_right():
            x = self._get_span_right()
        self._span.xy[0][0] = x
        self._span.xy[1][0] = x
        self._span.xy[4][0] = x
        return x

    def _set_span_right(self, x):
        if x > self._volume.display.getRangeMax():
            x = self._volume.display.getRangeMax()
        if x < self._get_span_left():
            x = self._get_span_left()
        self._span.xy[2][0] = x
        self._span.xy[3][0] = x
        return x

    def _is_in_span(self, x):
        return self._get_span_left() <= x <= self._get_span_right()

    # Private event methods

    def _onMouseClickEvent(self, event):
        if event.inaxes == self._histaxe:
            minflag = self._minflag.isChecked()
            maxflag = self._maxflag.isChecked()
            twoflag = self._twoflag.isChecked()
            if self._is_in_span(event.xdata):
                tol = (self._volume.display.getRangeMax() -
                       self._volume.display.getRangeMin()) / 50
                self._xleft = self._get_span_left()
                self._xright = self._get_span_right()
                # Drag left line
                if (0 < event.xdata - self._xleft < tol) and (minflag or twoflag):
                    self._on_move_left_span_flag = True
                    self._on_move_right_span_flag = False
                    self._on_move_span_flag = False
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag right line
                elif (0 < self._xright - event.xdata < tol) and (maxflag or twoflag):
                    self._on_move_right_span_flag = True
                    self._on_move_left_span_flag = False
                    self._on_move_span_flag = False
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag rectangle
                elif twoflag:
                    self._on_move_span_flag = True
                    self._on_move_left_span_flag = False
                    self._on_move_right_span_flag = False
                    self._cursor.setShape(Qt.ClosedHandCursor)
                    self._canvas.setCursor(self._cursor)
                self._xpos = float(event.xdata)

    def _onMouseMoveEvent(self, event):
        if event.inaxes == self._histaxe:
            minflag = self._minflag.isChecked()
            maxflag = self._maxflag.isChecked()
            twoflag = self._twoflag.isChecked()
            if self._on_move_span_flag or self._on_move_left_span_flag or self._on_move_right_span_flag:
                dx = event.xdata - self._xpos
                xleft = self._xleft
                xright = self._xright
                # Drag rectangle
                if self._on_move_span_flag and twoflag:
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
                elif self._on_move_left_span_flag and (minflag or twoflag):
                    xleft = self._set_span_left(self._xleft + dx)
                # Drag right line
                elif self._on_move_right_span_flag and (maxflag or twoflag):
                    xright = self._set_span_right(self._xright + dx)
                self._thresholdinftext.xyann = (xleft, self._histaxe.get_ylim()[1] / 2)
                self._thresholdsuptext.xyann = (xright, self._histaxe.get_ylim()[1] / 2)
                if self._volume.getDatatype() in _INTDATATYPES:
                    self._thresholdinftext.set_text(str(int(xleft)))
                    self._thresholdsuptext.set_text(str(int(xright)))
                else:
                    self._thresholdinftext.set_text('{:.2f}'.format(xleft))
                    self._thresholdsuptext.set_text('{:.2f}'.format(xright))
                self._canvas.draw()
            else:
                tol = (self._volume.display.getRangeMax() -
                       self._volume.display.getRangeMin()) / 50
                xleft = self._get_span_left()
                xright = self._get_span_right()
                # Drag left line
                if (0 < event.xdata - xleft) < tol and (minflag or twoflag):
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag right line
                elif (0 < xright - event.xdata) < tol and (maxflag or twoflag):
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag rectangle
                elif (xleft < event.xdata < xright) and twoflag:
                    self._cursor.setShape(Qt.OpenHandCursor)
                    self._canvas.setCursor(self._cursor)
                else:
                    self._cursor.setShape(Qt.ArrowCursor)
                    self._canvas.setCursor(self._cursor)

    def _onMouseReleaseEvent(self, event):
        self._cursor.setShape(Qt.ArrowCursor)
        self._canvas.setCursor(self._cursor)
        self._on_move_span_flag = False
        self._on_move_left_span_flag = False
        self._on_move_right_span_flag = False
        # Update editmin and editmax
        if self._volume.getDatatype() in _INTDATATYPES:
            tmin = int(self._get_span_left())
            tmax = int(self._get_span_right())
            self._editmin.setText(str(tmin))
            self._editmax.setText(str(tmax))
        else:
            tmin = self._get_span_left()
            tmax = self._get_span_right()
            self._editmin.setText('{:.2f}'.format(tmin))
            self._editmax.setText('{:.2f}'.format(tmax))
        # Update img box
        self._drawImage()
        # Update display
        self._canvas.draw_idle()

    def _onWheelEvent(self, event):
        d = self._volume.getNumpy().shape[0] - 1
        if event.button == 'up':
            if self._currentslice < d:
                self._currentslice += 1
        else:
            if self._currentslice > 0:
                self._currentslice -= 1
        self._drawImage()

    def _onKeyPressEvent(self, event):
        d = self._volume.getNumpy().shape[0] - 1
        if event.key == 'up' or event.key == 'left':
            if self._currentslice < d:
                self._currentslice += 1
        elif event.key == 'down' or event.key == 'right':
            if self._currentslice > 0:
                self._currentslice -= 1
        self._drawImage()

    def _onThresholdChangedEvent(self):
        if self._volume.getDatatype() in _INTDATATYPES:
            tmin = int(self._editmin.text())
            tmax = int(self._editmax.text())
        else:
            tmin = float(self._editmin.text())
            tmax = float(self._editmax.text())
        if tmax > self._volume.display.getRangeMax():
            tmax = self._volume.display.getRangeMax()
        if tmin < self._volume.display.getRangeMin():
            tmin = self._volume.display.getRangeMin()
        if tmax < tmin:
            tmax = tmin
        # Update span
        self._set_span_left(tmin)
        self._set_span_right(tmax)
        self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)
        self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)
        if self._volume.getDatatype() in _INTDATATYPES:
            tmin = str(tmin)
            tmax = str(tmax)
            self._thresholdinftext.set_text(tmin)
            self._thresholdsuptext.set_text(tmax)
            self._editmin.setText(tmin)
            self._editmax.setText(tmax)

        else:
            tmin = '{:.2f}'.format(tmin)
            tmax = '{:.2f}'.format(tmax)
            self._thresholdinftext.set_text(tmin)
            self._thresholdsuptext.set_text(tmax)
            self._editmin.setText(tmin)
            self._editmax.setText(tmax)

        # Update img box
        self._drawImage()
        # Update display
        self._canvas.draw_idle()

    def _onThresholdFlagChangeEvent(self, event):
        if self._minflag.isChecked():
            self._editmax.setEnabled(False)
            self._editmin.setEnabled(True)
            self._autobutton.setVisible(True)
            tmax = self._volume.getDisplay().getRangeMax()
            self.setMaxThreshold(tmax)
            self._set_span_right(tmax)
            self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)
            if self._volume.getDatatype() in _INTDATATYPES: self._thresholdsuptext.set_text(str(tmax))
            else: self._thresholdsuptext.set_text('{:.2f}'.format(tmax))
        elif self._maxflag.isChecked():
            self._editmax.setEnabled(True)
            self._editmin.setEnabled(False)
            self._autobutton.setVisible(False)
            tmin = self._volume.getDisplay().getRangeMin()
            self.setMinThreshold(tmin)
            self._set_span_left(tmin)
            self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)
            if self._volume.getDatatype() in _INTDATATYPES: self._thresholdinftext.set_text(str(tmin))
            else: self._thresholdinftext.set_text('{:.2f}'.format(tmin))
        else:
            self._editmax.setEnabled(True)
            self._editmin.setEnabled(True)
            self._autobutton.setVisible(True)
        # Update img box
        self._drawImage()
        # Update display
        self._canvas.draw_idle()

    def _onButtonAutoEvent(self):
        otsu = OtsuThresholdImageFilter()
        otsu.Execute(self._volume.getSITKImage())
        if self._volume.getDatatype() in _INTDATATYPES: self._editmin.setText(str(int(otsu.GetThreshold())))
        else: self._editmin.setText('{:.2f}'.format(otsu.GetThreshold()))
        self._onThresholdChangedEvent()

    # Public methods

    def getVolume(self):
        return self._volume

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self._initEdit()
            self._initHistAxes()
            self._initImgAxes()
        else:
            raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def setThreshold(self, tmin, tmax):
        if tmin > tmax:
            tmax = tmin
        if tmin < self._volume.display.getRangeMin():
            tmin = self._volume.display.getRangeMin()
        if tmax > self._volume.display.getRangeMax():
            tmax = self._volume.display.getRangeMax()
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmin.setText(str(tmin))
            self._editmax.setText(str(tmax))
        else:
            self._editmin.setText('{:.2f}'.format(tmin))
            self._editmax.setText('{:.2f}'.format(tmax))

    def setMinThreshold(self, tmin):
        if tmin < self._volume.display.getRangeMin():
            tmin = self._volume.display.getRangeMin()
        if self._volume.getDatatype() in _INTDATATYPES: self._editmin.setText(str(tmin))
        else: self._editmin.setText('{:.2f}'.format(tmin))

    def setMaxThreshold(self, tmax):
        if tmax > self._volume.display.getRangeMax():
            tmax = self._volume.display.getRangeMax()
        if self._volume.getDatatype() in _INTDATATYPES: self._editmax.setText(str(tmax))
        else: self._editmax.setText('{:.2f}'.format(tmax))

    def getThreshold(self):
        return float(self._editmin.text()), float(self._editmax.text())

    def getMinThreshold(self):
        return float(self._editmin.text())

    def getMaxThreshold(self):
        return float(self._editmax.text())

    def setAutoButtonVisibility(self, v):
        if isinstance(v, bool):
            self._autobutton.setVisible(v)
        else:
            raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getAutoButtonVisibility(self):
        return self._autobutton.isVisible()

    def setThresholdFlag(self, v):
        if isinstance(v, int):
            if 0 <= v > 3:
                if v == 0: self._minflag.setChecked(True)
                elif v == 1: self._maxflag.setChecked(True)
                else: self._twoflag.setChecked(True)
            else:
                raise ValueError('parameter value {} is not between 0 and 2.'.format(v))
        else:
            raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getThresholdFlag(self):
        if self._minflag.isChecked(): return 0
        elif self._maxflag.isChecked(): return 1
        else: return 2

    def setThresholdFlagToMinimum(self):
        self._minflag.setChecked(True)

    def setThresholdFlagToMaximum(self):
        self._maxflag.setChecked(True)

    def setThresholdFlagToTwo(self):
        self._twoflag.setChecked(True)

    def setThresholdFlagButtonsVisibility(self, v):
        if isinstance(v, bool):
            self._minflag.setVisible(v)
            self._maxflag.setVisible(v)
            self._twoflag.setVisible(v)
        else:
            raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getThresholdFlagButtonsVisibility(self):
        return self._minflag.isVisible()


class GradientThresholdWidget(ThresholdWidget):
    """
        GradientThresholdWidget class

        Inheritance

            QWidget -> ThresholdWidget -> GradientThresholdWidget

        Public methods

            setVolume()

            inherited QWidget methods
            inherited ThresholdWidget methods
    """

    def __init__(self, volume, size=512, parent=None):
        super().__init__(self._calcGradient(volume), size, parent)

    def setVolume(self, volume):
        super().setVolume(self._calcGradient(volume))

    @staticmethod
    def _calcGradient(volume):
        if isinstance(volume, SisypheVolume):
            simg = volume.getSITKImage()
            fimg = GradientMagnitudeRecursiveGaussian(simg, sigma=1.0)
            fimg = Clamp(fimg, simg.GetPixelID())
            volume.copyFromSITKImage(fimg)
            return volume
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))


class ThresholdViewWidget(QWidget):
    """
        ThresholdWidget class

        Inheritance

            QWidget -> ThresholdViewWidget

        Private attributes

            _fig            Figure instance, matplotlib figure
            _canvas         FigureCanvas instance, tool canvas
            _imgaxe         Axes instance, image and ROI display area
            _axe            Axes instance, histogram display area
            _volume         SisypheVolume
            _currentslice   int, current slice displayed

        Public methods

            getVolume()
            setVolume()
            setThreshold()
            setMinThreshold()
            setMaxThreshold()
            getThresholds()
            getMinThreshold()
            getMaxThreshold()
            setAutoButtonVisibility(bool)
            bool = getAutoButtonVisibility()
            setThresholdFlag(int)
            int = getThresholdFlag()
            setThresholdFlagToMinimum()
            setThresholdFlagToMaximum()
            setThresholdFlagToTwo()
            setThresholdFlagButtonsVisibility(bool)
            bool = getThresholdFlagButtonsVisibility()

            inherited QWidget methods
    """
    # Special method

    def __init__(self, volume, size=512, parent=None):
        super().__init__(parent)
        if isinstance(volume, SisypheVolume):
            self._volume = volume
            self._view = IconBarSliceViewWidget()
            self._view.setVolume(volume)
            self._view().newROI()
            self._view().getActiveROI().setAlpha(0.8)
            self._view().setUndoOff()
            self._view().popupMenuDisabled()
            self._view.setExpandButtonAvailability(False)
            self._view.setFullscreenButtonAvailability(False)
            self._view.setRulerButtonAvailability(False)
            self._view.setInfoButtonAvailability(False)
            self._view.setToolButtonAvailability(False)
            self._view.setCaptureButtonAvailability(False)
            self._view.setClipboardButtonAvailability(False)
            self._view.setColorbarButtonAvailability(False)
            self._view.setMinimumWidth(size)

            # Init matplotlib figure

            self._fig = Figure(constrained_layout=True)
            background = self.palette().window().color()
            self._fig.set_facecolor((background.red() / 255,
                                     background.green() / 255,
                                     background.blue() / 255))

            self._canvas = FigureCanvas(self._fig)
            self._histaxe = self._fig.add_subplot()

            # Init QLineEdit

            self._editmin = QLineEdit()
            self._editmax = QLineEdit()
            self._editmin.setToolTip('Minimum threshold')
            self._editmax.setToolTip('Maximum threshold')
            self._editmin.setFixedWidth(60)
            self._editmax.setFixedWidth(60)
            self._initEdit()
            self._editmin.returnPressed.connect(self._onThresholdChangedEvent)
            self._editmax.returnPressed.connect(self._onThresholdChangedEvent)

            # Init Buttons

            self._autobutton = QPushButton('Auto')
            self._autobutton.setFixedWidth(60)
            self._autobutton.clicked.connect(self._onButtonAutoEvent)
            self._minflag = QRadioButton('Min.')
            self._maxflag = QRadioButton('Max.')
            self._twoflag = QRadioButton('Two')
            self._twoflag.setChecked(True)
            self._minflag.setToolTip('A single threshold above minimum value.')
            self._maxflag.setToolTip('A single threshold below maximum value.')
            self._twoflag.setToolTip('Two thresholds between minimum and maximum value.')
            self._minflag.clicked.connect(self._onThresholdFlagChangeEvent)
            self._maxflag.clicked.connect(self._onThresholdFlagChangeEvent)
            self._twoflag.clicked.connect(self._onThresholdFlagChangeEvent)

            # Init matplotlib axes

            self._span = None
            self._thresholdinftext = None
            self._thresholdsuptext = None
            self._initHistAxes()

            # Init matplotlib events

            self._canvas.mpl_connect('button_press_event', self._onMouseClickEvent)
            self._canvas.mpl_connect('motion_notify_event', self._onMouseMoveEvent)
            self._canvas.mpl_connect('button_release_event', self._onMouseReleaseEvent)
            self._on_move_span_flag = False
            self._on_move_left_span_flag = False
            self._on_move_right_span_flag = False
            self._xpos = None
            self._xleft = None
            self._xright = None

            # Init QLayout

            splt = QSplitter()
            splt.addWidget(self._view)
            splt.addWidget(self._canvas)

            lyout = QGridLayout()
            lyout.addWidget(splt, 0, 0, 1, 2)
            lyout.setSpacing(0)
            lyout.setContentsMargins(5, 5, 5, 0)

            hlyout = QHBoxLayout()
            hlyout.setDirection(QHBoxLayout.LeftToRight)
            hlyout.addStretch()
            hlyout.addWidget(self._minflag)
            hlyout.addWidget(self._maxflag)
            hlyout.addWidget(self._twoflag)
            hlyout.addStretch()
            lyout.addLayout(hlyout, 1, 0)

            hlyout = QHBoxLayout()
            hlyout.setDirection(QHBoxLayout.RightToLeft)
            hlyout.addStretch()
            hlyout.addWidget(self._editmax)
            hlyout.addStretch()
            hlyout.addWidget(self._autobutton)
            hlyout.addStretch()
            hlyout.addWidget(self._editmin)
            hlyout.addStretch()
            lyout.addLayout(hlyout, 1, 1)

            self.setLayout(lyout)

            # Init QWidget (size, tooltip, focus, cursor)

            self.setFixedSize(size * 2, size)
            self.setToolTip('Left click and drag vertical dotted line to move it\n'
                            'and modify threshold settings.')

            self._canvas.setFocusPolicy(Qt.ClickFocus)
            self._canvas.setFocus()
            self._cursor = QCursor()
            self._canvas.setCursor(self._cursor)

            # Draw tool

            self._canvas.draw()
        else:
            raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    # Private methods

    def _initHistAxes(self):
        # Init hist axes

        self._histaxe.clear()
        self._histaxe.set_xmargin(0)
        self._histaxe.set_frame_on(False)
        self._histaxe.set_axis_off()

        h = self._histaxe.hist(self._volume.getNumpy().flatten(), bins=256,
                               range=(self._volume.display.getRangeMin(), self._volume.display.getRangeMax()),
                               align='left', orientation='vertical', histtype='stepfilled', color=(0.5, 0.5, 0.5))

        self._histaxe.set_ylim(0, int(median(h[0]) * 10))

        # Init Span box in hist axes

        self._span = self._histaxe.axvspan(self.getMinThreshold(),
                                           self.getMaxThreshold(),
                                           facecolor='yellow', edgecolor='brown', linewidth=2,
                                           linestyle='--', alpha=0.2)

        if self._volume.getDatatype() in _INTDATATYPES:
            txtinf = str(int(self.getMinThreshold()))
            txtsup = str(int(self.getMaxThreshold()))
        else:
            txtinf = '{:.2f}'.format(self.getMinThreshold())
            txtsup = '{:.2f}'.format(self.getMaxThreshold())

        self._thresholdinftext = self._histaxe.annotate(txtinf,
                                                        xy=(self.getMinThreshold(),
                                                            self._histaxe.get_ylim()[1] / 2),
                                                        xycoords='data', color='brown', fontsize='small',
                                                        rotation='vertical', verticalalignment='center',
                                                        horizontalalignment='center')
        self._thresholdsuptext = self._histaxe.annotate(txtsup,
                                                        xy=(self.getMaxThreshold(),
                                                            self._histaxe.get_ylim()[1] / 2),
                                                        xycoords='data', color='brown', fontsize='small',
                                                        rotation='vertical', verticalalignment='center',
                                                        horizontalalignment='center')

    def _drawImage(self):
        draw = self._view().getDrawInstance()
        vmin, vmax = self.getThresholds()
        draw.setThresholds(vmin, vmax)
        draw.thresholding(mask=False, replace=True)
        self._view().updateROIDisplay()

    def _initEdit(self):
        datatype = self._volume.getNumpy().dtype
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmin.setText(str(int(self._volume.display.getRangeMin())))
            self._editmax.setText(str(int(self._volume.display.getRangeMax())))
            self._editmin.setValidator(QIntValidator(iinfo(datatype).min, iinfo(datatype).max))
            self._editmax.setValidator(QIntValidator(iinfo(datatype).min, iinfo(datatype).max))
        else:
            self._editmin.setText('{:.2f}'.format(self._volume.display.getRangeMin()))
            self._editmax.setText('{:.2f}'.format(self._volume.display.getRangeMax()))
            self._editmin.setValidator(QDoubleValidator(finfo(datatype).min, finfo(datatype).max, 2))
            self._editmax.setValidator(QDoubleValidator(finfo(datatype).min, finfo(datatype).max, 2))
        self._editmin.setAlignment(Qt.AlignHCenter)
        self._editmax.setAlignment(Qt.AlignHCenter)

    def _get_span_left(self):
        return self._span.xy[0][0]

    def _get_span_right(self):
        return self._span.xy[2][0]

    def _set_span_left(self, x):
        if x < self._volume.display.getRangeMin():
            x = self._volume.display.getRangeMin()
        if x > self._get_span_right():
            x = self._get_span_right()
        self._span.xy[0][0] = x
        self._span.xy[1][0] = x
        self._span.xy[4][0] = x
        return x

    def _set_span_right(self, x):
        if x > self._volume.display.getRangeMax():
            x = self._volume.display.getRangeMax()
        if x < self._get_span_left():
            x = self._get_span_left()
        self._span.xy[2][0] = x
        self._span.xy[3][0] = x
        return x

    def _is_in_span(self, x):
        return self._get_span_left() <= x <= self._get_span_right()

    # Private event methods

    def _onMouseClickEvent(self, event):
        if event.inaxes == self._histaxe:
            minflag = self._minflag.isChecked()
            maxflag = self._maxflag.isChecked()
            twoflag = self._twoflag.isChecked()
            if self._is_in_span(event.xdata):
                tol = (self._volume.display.getRangeMax() -
                       self._volume.display.getRangeMin()) / 20
                self._xleft = self._get_span_left()
                self._xright = self._get_span_right()
                # Drag left line
                if (0 < abs(event.xdata - self._xleft) < tol) and (minflag or twoflag):
                    self._on_move_left_span_flag = True
                    self._on_move_right_span_flag = False
                    self._on_move_span_flag = False
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag right line
                elif (0 < abs(self._xright - event.xdata) < tol) and (maxflag or twoflag):
                    self._on_move_right_span_flag = True
                    self._on_move_left_span_flag = False
                    self._on_move_span_flag = False
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag rectangle
                elif twoflag:
                    self._on_move_span_flag = True
                    self._on_move_left_span_flag = False
                    self._on_move_right_span_flag = False
                    self._cursor.setShape(Qt.ClosedHandCursor)
                    self._canvas.setCursor(self._cursor)
                self._xpos = float(event.xdata)

    def _onMouseMoveEvent(self, event):
        if event.inaxes == self._histaxe:
            minflag = self._minflag.isChecked()
            maxflag = self._maxflag.isChecked()
            twoflag = self._twoflag.isChecked()
            if self._on_move_span_flag or self._on_move_left_span_flag or self._on_move_right_span_flag:
                dx = event.xdata - self._xpos
                xleft = self._xleft
                xright = self._xright
                # Drag rectangle
                if self._on_move_span_flag and twoflag:
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
                elif self._on_move_left_span_flag and (minflag or twoflag):
                    dxleft = self._xleft + dx
                    if dxleft < self._xright: xleft = self._set_span_left(dxleft)
                    else: xleft = self._set_span_left(self._xleft)
                # Drag right line
                elif self._on_move_right_span_flag and (maxflag or twoflag):
                    dxright = self._xright + dx
                    if dxright > self._xleft: xright = self._set_span_right(dxright)
                    else: xright = self._set_span_right(self._xright)
                self._thresholdinftext.xyann = (xleft, self._histaxe.get_ylim()[1] / 2)
                self._thresholdsuptext.xyann = (xright, self._histaxe.get_ylim()[1] / 2)
                if self._volume.getDatatype() in _INTDATATYPES:
                    self._thresholdinftext.set_text(str(int(xleft)))
                    self._thresholdsuptext.set_text(str(int(xright)))
                else:
                    self._thresholdinftext.set_text('{:.2f}'.format(xleft))
                    self._thresholdsuptext.set_text('{:.2f}'.format(xright))
                # Update editmin and editmax
                if self._volume.getDatatype() in _INTDATATYPES:
                    tmin = int(self._get_span_left())
                    tmax = int(self._get_span_right())
                else:
                    tmin = self._get_span_left()
                    tmax = self._get_span_right()
                if self._volume.getDatatype() in _INTDATATYPES:
                    self._editmin.setText(str(tmin))
                    self._editmax.setText(str(tmax))
                else:
                    self._editmin.setText('{:.2f}'.format(tmin))
                    self._editmax.setText('{:.2f}'.format(tmax))
                self._canvas.draw()
                # Update view widget
                self._drawImage()
            else:
                tol = (self._volume.display.getRangeMax() -
                       self._volume.display.getRangeMin()) / 20
                xleft = self._get_span_left()
                xright = self._get_span_right()
                # Drag left line
                if (0 < abs(event.xdata - xleft) < tol) and (minflag or twoflag):
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag right line
                elif (0 < abs(xright - event.xdata) < tol) and (maxflag or twoflag):
                    self._cursor.setShape(Qt.SplitHCursor)
                    self._canvas.setCursor(self._cursor)
                # Drag rectangle
                elif (xleft < event.xdata < xright) and twoflag:
                    self._cursor.setShape(Qt.OpenHandCursor)
                    self._canvas.setCursor(self._cursor)
                else:
                    self._cursor.setShape(Qt.ArrowCursor)
                    self._canvas.setCursor(self._cursor)

    def _onMouseReleaseEvent(self, event):
        self._cursor.setShape(Qt.ArrowCursor)
        self._canvas.setCursor(self._cursor)
        self._on_move_span_flag = False
        self._on_move_left_span_flag = False
        self._on_move_right_span_flag = False
        # Update editmin and editmax
        if self._volume.getDatatype() in _INTDATATYPES:
            tmin = int(self._get_span_left())
            tmax = int(self._get_span_right())
        else:
            tmin = self._get_span_left()
            tmax = self._get_span_right()
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmin.setText(str(tmin))
            self._editmax.setText(str(tmax))
        else:
            self._editmin.setText('{:.2f}'.format(tmin))
            self._editmax.setText('{:.2f}'.format(tmax))
        # Update view widget
        self._drawImage()
        # Update display
        self._canvas.draw_idle()

    def _onThresholdChangedEvent(self):
        if self._volume.getDatatype() in _INTDATATYPES:
            tmin = int(self._editmin.text())
            tmax = int(self._editmax.text())
        else:
            tmin = float(self._editmin.text())
            tmax = float(self._editmax.text())
        if tmax > self._volume.display.getRangeMax():
            tmax = self._volume.display.getRangeMax()
        if tmin < self._volume.display.getRangeMin():
            tmin = self._volume.display.getRangeMin()
        if tmax < tmin:
            tmax = tmin
        self._set_span_left(tmin)
        self._set_span_right(tmax)
        self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)
        self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)
        if self._volume.getDatatype() in _INTDATATYPES:
            tmin = str(tmin)
            tmax = str(tmax)
            self._thresholdinftext.set_text(tmin)
            self._thresholdsuptext.set_text(tmax)
            self._editmin.setText(tmin)
            self._editmax.setText(tmax)
        else:
            tmin = '{:.2f}'.format(tmin)
            tmax = '{:.2f}'.format(tmax)
            self._thresholdinftext.set_text(tmin)
            self._thresholdsuptext.set_text(tmax)
            self._editmin.setText(tmin)
            self._editmax.setText(tmax)

        # Update img box
        self._drawImage()
        # Update display
        self._canvas.draw_idle()

    def _onThresholdFlagChangeEvent(self, event):
        if self._minflag.isChecked():
            self._editmax.setEnabled(False)
            self._editmin.setEnabled(True)
            self._autobutton.setVisible(True)
            tmax = self._volume.getDisplay().getRangeMax()
            self.setMaxThreshold(tmax)
            self._set_span_right(tmax)
            self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)
            if self._volume.getDatatype() in _INTDATATYPES: self._thresholdsuptext.set_text(str(tmax))
            else: self._thresholdsuptext.set_text('{:.2f}'.format(tmax))
        elif self._maxflag.isChecked():
            self._editmax.setEnabled(True)
            self._editmin.setEnabled(False)
            self._autobutton.setVisible(False)
            tmin = self._volume.getDisplay().getRangeMin()
            self.setMinThreshold(tmin)
            self._set_span_left(tmin)
            self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)
            if self._volume.getDatatype() in _INTDATATYPES: self._thresholdinftext.set_text(str(tmin))
            else: self._thresholdinftext.set_text('{:.2f}'.format(tmin))
        else:
            self._editmax.setEnabled(True)
            self._editmin.setEnabled(True)
            self._autobutton.setVisible(True)
        # Update img box
        self._drawImage()
        # Update display
        self._canvas.draw_idle()

    def _onButtonAutoEvent(self):
        otsu = OtsuThresholdImageFilter()
        otsu.Execute(self._volume.getSITKImage())
        if self._volume.getDatatype() in _INTDATATYPES: self._editmin.setText(str(int(otsu.GetThreshold())))
        else: self._editmin.setText(str('{:.2f}'.format(otsu.GetThreshold())))
        self._onThresholdChangedEvent()

    # Public methods

    def getVolume(self):
        return self._volume

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            self._view.removeVolume()
            self._view.setVolume(volume)
            self._view().newROI()
            self._view().getActiveROI().setAlpha(0.8)
            self._volume = volume
            self._initEdit()
            self._initHistAxes()
            self._drawImage()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def getViewWidget(self):
        return self._view

    def setThreshold(self, tmin, tmax):
        if tmin > tmax:
            tmax = tmin
        if tmin < self._volume.display.getRangeMin():
            tmin = self._volume.display.getRangeMin()
        if tmax > self._volume.display.getRangeMax():
            tmax = self._volume.display.getRangeMax()
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmin.setText(str(tmin))
            self._editmax.setText(str(tmax))
            self._thresholdinftext.set_text(str(int(tmin)))
            self._thresholdsuptext.set_text(str(int(tmax)))
        else:
            self._editmin.setText('{:.2f}'.format(tmin))
            self._editmax.setText('{:.2f}'.format(tmax))
            self._thresholdinftext.set_text('{:.2f}'.format(tmin))
            self._thresholdsuptext.set_text('{:.2f}'.format(tmax))
        self._set_span_left(tmin)
        self._set_span_right(tmax)
        self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)
        self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)

    def setMinThreshold(self, tmin):
        if tmin < self._volume.display.getRangeMin():
            tmin = self._volume.display.getRangeMin()
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmin.setText(str(tmin))
            self._thresholdinftext.set_text(str(int(tmin)))
        else:
            self._editmin.setText('{:.2f}'.format(tmin))
            self._thresholdinftext.set_text('{:.2f}'.format(tmin))
        self._set_span_left(tmin)
        self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)

    def setMaxThreshold(self, tmax):
        if tmax > self._volume.display.getRangeMax():
            tmax = self._volume.display.getRangeMax()
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmax.setText(str(tmax))
            self._thresholdsuptext.set_text(str(int(tmax)))
        else:
            self._editmax.setText('{:.2f}'.format(tmax))
            self._thresholdsuptext.set_text('{:.2f}'.format(tmax))
        self._set_span_right(tmax)
        self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)

    def getThresholds(self):
        return float(self._editmin.text()), float(self._editmax.text())

    def getMinThreshold(self):
        return float(self._editmin.text())

    def getMaxThreshold(self):
        return float(self._editmax.text())

    def setAutoButtonVisibility(self, v):
        if isinstance(v, bool): self._autobutton.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getAutoButtonVisibility(self):
        return self._autobutton.isVisible()

    def setThresholdFlag(self, v):
        if isinstance(v, int):
            if 0 <= v > 3:
                if v == 0: self._minflag.setChecked(True)
                elif v == 1: self._maxflag.setChecked(True)
                else: self._twoflag.setChecked(True)
            else: raise ValueError('parameter value {} is not between 0 and 2.'.format(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getThresholdFlag(self):
        if self._minflag.isChecked(): return 0
        elif self._maxflag.isChecked(): return 1
        else: return 2

    def setThresholdFlagToMinimum(self):
        self._minflag.setChecked(True)

    def setThresholdFlagToMaximum(self):
        self._maxflag.setChecked(True)

    def setThresholdFlagToTwo(self):
        self._twoflag.setChecked(True)

    def setThresholdFlagButtonsVisibility(self, v):
        if isinstance(v, bool):
            self._minflag.setVisible(v)
            self._maxflag.setVisible(v)
            self._twoflag.setVisible(v)
        else:
            raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getThresholdFlagButtonsVisibility(self):
        return self._minflag.isVisible()


class GradientThresholdViewWidget(ThresholdViewWidget):
    """
        GradientThresholdViewWidget class

        Inheritance

            QWidget -> ThresholdViewWidget -> GradientThresholdViewWidget

        Public methods

            setVolume()

            inherited QWidget methods
            inherited ThresholdWidget methods
    """

    def __init__(self, volume, size=512, parent=None):
        super().__init__(self._calcGradient(volume), size, parent)

    def setVolume(self, volume):
        super().setVolume(self._calcGradient(volume))

    @staticmethod
    def _calcGradient(volume):
        if isinstance(volume, SisypheVolume):
            simg = volume.getSITKImage()
            fimg = GradientMagnitudeRecursiveGaussian(simg, sigma=1.0)
            fimg = Clamp(fimg, simg.GetPixelID())
            volume.copyFromSITKImage(fimg)
            return volume
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))


if __name__ == '__main__':

    from sys import argv
    from PyQt5.QtWidgets import QApplication

    test = 2
    app = QApplication(argv)
    main = QWidget()
    layout = QVBoxLayout(main)
    # filename = '/Users/Jean-Albert/PycharmProjects/untitled/Sisyphe/templates/mni_icbm152_sym_9c_brain.xvol'
    filename = '/Users/Jean-Albert/PycharmProjects/untitled/Sisyphe/templates/mni_icbm152_sym_9c_gm.xvol'
    img = SisypheVolume()
    img.load(filename)
    img.display.getLUT().setDefaultLut()
    if test == 0:
        thresholdwidget = ThresholdWidget(img, size=256)
    elif test == 1:
        thresholdwidget = GradientThresholdWidget(img)
    elif test == 2:
        thresholdwidget = ThresholdViewWidget(img, size=512)
    else:
        thresholdwidget = GradientThresholdViewWidget(img)
    layout.addWidget(thresholdwidget)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)
    main.show()
    app.exec_()
