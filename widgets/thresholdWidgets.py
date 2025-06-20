"""
External packages/modules
-------------------------

    - Matplotlib, Graph tool, https://matplotlib.org/
    - Numpy, scientific computing, https://numpy.org/
    - PyQtDarkTheme, dark theme management, https://pyqtdarktheme.readthedocs.io/en/stable/index.html
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from sys import platform

from numpy import median

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QPushButton

import darkdetect

from SimpleITK import Clamp
from SimpleITK import OtsuThresholdImageFilter
from SimpleITK import GradientMagnitudeRecursiveGaussian

from Sisyphe.core.sisypheVolume import SisypheVolume
# noinspection PyProtectedMember
from Sisyphe.core.sisypheConstants import _INTDATATYPES
from Sisyphe.widgets.iconBarViewWidgets import IconBarSliceViewWidget

if platform == 'win32':
    from qdarktheme import load_palette

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> ThresholdViewWidget -> GradientThresholdViewWidget
"""


# noinspection SpellCheckingInspection
class ThresholdViewWidget(QWidget):
    """
    ThresholdWidget class

    Inheritance
    ~~~~~~~~~~~

    QWidget -> ThresholdViewWidget

    Last revision: 11/03/2025
    """

    # Class methods

    @classmethod
    def isDarkMode(cls):
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls):
        return darkdetect.isLight()

    # Special method

    # noinspection SpellCheckingInspection
    """
        Private attributes
    
        _fig                Figure, matplotlib figure
        _canvas             FigureCanvas, tool canvas
        _view               IconBarSliceViewWidget, image and ROI display area
        _histaxe            Axes, histogram/span display area
        _volume             SisypheVolume
        _currentslice       int, current slice displayed
        _decimals           int, number of decimals after point in QLineEdit _editmin and _editmax
        _format             str, float representation in QLineEdit _editmin and _editmax
        _editmin            QDoubleSpinBox, edit lower threshold
        _editmax            QDoubleSpinBox, edit upper threshold
        _autobutton         QPushButton, automatic threshold calculation
        _minflag            QRadioButton, only lower threshold can be modified if checked
        _maxflag            QRadioButton, only upper threshold can be modified if checked
        _twoflag            QRadioButton, lower and upper thresholds can be modified if checked
        _span               matplotlib.patches.Rectangle, threshold box
        _thresholdinftext   matplotlib.text.Annotation, lower threshold text displayed next to span
        _thresholdsuptext   matplotlib.text.Annotation, upper threshold text displayed next to span
        _xpos               tuple[float, float], initial span box position used by mouse move event
        _xleft              tuple[float, float], left span position as lower threshold
        _xright             tuple[float, float], right span position as upper threshold
        _on_move_span_flag          bool, span box movement availability, lower and upper thresholds can be modified if True
        _on_move_left_span_flag     bool, left span movement availability, lower threshold can be modified if True
        _on_move_right_span_flag    bool, right span movement availability, upper thrshold can be modified if True
        """

    def __init__(self, volume=None, size=512, parent=None):
        super().__init__(parent)
        if volume is None or isinstance(volume, SisypheVolume):
            self._volume = volume
            self._format = '{:.1f}'
            self._decimals = 1
            self._initDecimals()
            self._view = IconBarSliceViewWidget(parent=self)
            if volume is not None:
                self._view.setVolume(volume)
                self._view().newROI()
                self._view().getActiveROI().setAlpha(0.8)
            self._view().setUndoOff()
            self._view().popupMenuDisabled()
            self._view().setSelectable(False)
            self._view.setPinButtonAvailability(False)
            self._view.setExpandButtonAvailability(False)
            self._view.setFullscreenButtonAvailability(False)
            self._view.setRulerButtonAvailability(False)
            self._view.setShowButtonAvailability(False)
            self._view.setInfoButtonAvailability(False)
            self._view.setToolButtonAvailability(False)
            self._view.setCaptureButtonAvailability(False)
            self._view.setClipboardButtonAvailability(False)
            self._view.setColorbarButtonAvailability(False)
            self._view.setIsoButtonAvailability(False)
            self._view.setActionButtonAvailability(False)
            self._view.setMinimumWidth(size)

            # Init matplotlib figure

            self._fig = Figure(constrained_layout=True)
            # < Revision 11/03/2025
            # background = self.palette().window().color()
            if platform == 'win32':
                p = load_palette('auto')
                background = p.color(QPalette.Base)
            else:
                if parent is not None: background = parent.palette().color(QPalette.Base)
                else: background = self.palette().color(QPalette.Base)
            # < Revision 11/03/2025
            self._fig.set_facecolor((background.red() / 255,
                                     background.green() / 255,
                                     background.blue() / 255))

            self._canvas = FigureCanvas(self._fig)
            self._histaxe = self._fig.add_subplot()

            # Init QLineEdit

            self._editmin = QDoubleSpinBox()
            self._editmax = QDoubleSpinBox()
            self._editmin.setToolTip('Minimum threshold')
            self._editmax.setToolTip('Maximum threshold')
            self._editmin.setFixedWidth(80)
            self._editmax.setFixedWidth(80)
            self._initEdit()
            # noinspection PyUnresolvedReferences
            self._editmin.valueChanged.connect(self._onThresholdChangedEvent)
            # noinspection PyUnresolvedReferences
            self._editmax.valueChanged.connect(self._onThresholdChangedEvent)

            # Init Buttons

            self._autobutton = QPushButton('Auto')
            self._autobutton.setFixedWidth(80)
            # noinspection PyUnresolvedReferences
            self._autobutton.clicked.connect(self._onButtonAutoEvent)
            self._minflag = QRadioButton('Min.')
            self._maxflag = QRadioButton('Max.')
            self._twoflag = QRadioButton('Two')
            self._twoflag.setChecked(True)
            self._minflag.setToolTip('A single threshold above minimum value.')
            self._maxflag.setToolTip('A single threshold below maximum value.')
            self._twoflag.setToolTip('Two thresholds between minimum and maximum value.')
            # noinspection PyUnresolvedReferences
            self._minflag.clicked.connect(self._onThresholdFlagChangeEvent)
            # noinspection PyUnresolvedReferences
            self._maxflag.clicked.connect(self._onThresholdFlagChangeEvent)
            # noinspection PyUnresolvedReferences
            self._twoflag.clicked.connect(self._onThresholdFlagChangeEvent)

            # Init matplotlib axes

            self._span = None
            self._thresholdinftext = None
            self._thresholdsuptext = None
            self._initHistAxes()

            # Init matplotlib events

            # noinspection PyTypeChecker
            self._canvas.mpl_connect('button_press_event', self._onMouseClickEvent)
            # noinspection PyTypeChecker
            self._canvas.mpl_connect('motion_notify_event', self._onMouseMoveEvent)
            self._canvas.mpl_connect('button_release_event', self._onMouseReleaseEvent)
            self._on_move_span_flag = False
            self._on_move_left_span_flag = False
            self._on_move_right_span_flag = False
            self._xpos = None
            self._xleft = None
            self._xright = None

            # Init QLayout

            lyout = QGridLayout()
            lyout.addWidget(self._view, 0, 0)
            lyout.addWidget(self._canvas, 0, 1)
            lyout.setContentsMargins(5, 5, 5, 5)

            hlyout = QHBoxLayout()
            hlyout.setDirection(QHBoxLayout.LeftToRight)
            hlyout.addStretch()
            hlyout.addWidget(self._minflag)
            hlyout.addWidget(self._maxflag)
            hlyout.addWidget(self._twoflag)
            hlyout.addStretch()
            lyout.addLayout(hlyout, 1, 0)

            hlyout = QHBoxLayout()
            hlyout.setDirection(QHBoxLayout.LeftToRight)
            hlyout.addWidget(self._editmin, Qt.AlignLeft)
            hlyout.addWidget(self._autobutton, Qt.AlignHCenter)
            hlyout.addWidget(self._editmax, Qt.AlignRight)
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

            # Win32 settings

            if platform == 'win32':
                self._editmin.setStyleSheet('font-size: 8pt')
                self._editmax.setStyleSheet('font-size: 8pt')
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    # Private methods

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
        if self._volume is not None:
            if self.isDarkMode(): spancolor = 'white'
            else: spancolor = 'black'

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
                                               facecolor='yellow', edgecolor=spancolor, linewidth=2,
                                               linestyle='--', alpha=0.2)

            if self._volume.getDatatype() in _INTDATATYPES:
                txtinf = str(int(self.getMinThreshold()))
                txtsup = str(int(self.getMaxThreshold()))
            else:
                txtinf = self._format.format(self.getMinThreshold())
                txtsup = self._format.format(self.getMaxThreshold())

            self._thresholdinftext = self._histaxe.annotate(txtinf,
                                                            xy=(self.getMinThreshold(),
                                                                self._histaxe.get_ylim()[1] / 2),
                                                            xycoords='data', color=spancolor, fontsize='medium',
                                                            rotation='vertical', verticalalignment='center',
                                                            horizontalalignment='center')
            self._thresholdsuptext = self._histaxe.annotate(txtsup,
                                                            xy=(self.getMaxThreshold(),
                                                                self._histaxe.get_ylim()[1] / 2),
                                                            xycoords='data', color=spancolor, fontsize='medium',
                                                            rotation='vertical', verticalalignment='center',
                                                            horizontalalignment='center')

    def _drawImage(self):
        if self._volume is not None:
            draw = self._view().getDrawInstance()
            vmin, vmax = self.getThresholds()
            draw.setThresholds(vmin, vmax)
            draw.thresholding(mask=False, replace=True)
            self._view().updateROIDisplay()

    def _initEdit(self):
        if self._volume is not None:
            self._editmin.blockSignals(True)
            self._editmax.blockSignals(True)
            if self._volume.getDatatype() in _INTDATATYPES:
                # < Revision 20/03/2025
                vmin = self._volume.display.getRangeMin()
                vmax = self._volume.display.getRangeMax()
                self._editmin.setMinimum(vmin)
                self._editmax.setMinimum(vmin)
                self._editmin.setMaximum(vmax)
                self._editmax.setMaximum(vmax)
                self._editmin.setDecimals(0)
                self._editmax.setDecimals(0)
                self._editmin.setSingleStep(1.0)
                self._editmax.setSingleStep(1.0)
                self._editmin.setStepType(self._editmin.DefaultStepType)
                self._editmax.setStepType(self._editmax.DefaultStepType)
                self._editmin.setAccelerated(True)
                self._editmax.setAccelerated(True)
                # Revision 20/03/2025 >
            else:
                # < Revision 20/03/2025
                vmin = self._volume.display.getRangeMin()
                vmax = self._volume.display.getRangeMax()
                self._editmin.setMinimum(vmin)
                self._editmax.setMinimum(vmin)
                self._editmin.setMaximum(vmax)
                self._editmax.setMaximum(vmax)
                self._editmin.setDecimals(self._decimals)
                self._editmax.setDecimals(self._decimals)
                self._editmin.setSingleStep(1 / (10 ** self._decimals))
                self._editmax.setSingleStep(1 / (10 ** self._decimals))
                self._editmin.setStepType(self._editmin.DefaultStepType)
                self._editmax.setStepType(self._editmax.DefaultStepType)
                self._editmin.setAccelerated(True)
                self._editmax.setAccelerated(True)
                # Revision 20/03/2025 >
            self._editmin.setValue(self._volume.display.getRangeMin())
            self._editmax.setValue(self._volume.display.getRangeMax())
            self._editmin.blockSignals(False)
            self._editmax.blockSignals(False)

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
                    self._thresholdinftext.set_text(self._format.format(xleft))
                    self._thresholdsuptext.set_text(self._format.format(xright))
                # Update editmin and editmax
                if self._volume.getDatatype() in _INTDATATYPES:
                    tmin = int(self._get_span_left())
                    tmax = int(self._get_span_right())
                else:
                    tmin = self._get_span_left()
                    tmax = self._get_span_right()
                if self._volume.getDatatype() in _INTDATATYPES:
                    # < Revision 23/07/2024
                    # self._editmin.setText(str(tmin))
                    # self._editmax.setText(str(tmax))
                    self._editmin.setValue(int(tmin))
                    self._editmax.setValue(int(tmax))
                    # Revision 23/07/2024 >
                else:
                    # < Revision 23/07/2024
                    # self._editmin.setText(self._format.format(tmin))
                    # self._editmax.setText(self._format.format(tmax))
                    self._editmin.setValue(tmin)
                    self._editmax.setValue(tmax)
                    # Revision 23/07/2024 >
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

    # noinspection PyUnusedLocal
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
            # < Revision 23/07/2024
            # self._editmin.setText(str(tmin))
            # self._editmax.setText(str(tmax))
            self._editmin.setValue(int(tmin))
            self._editmax.setValue(int(tmax))
            # Revision 23/07/2024 >
        else:
            # < Revision 23/07/2024
            # self._editmin.setText(self._format.format(tmin))
            # self._editmax.setText(self._format.format(tmax))
            self._editmin.setValue(tmin)
            self._editmax.setValue(tmax)
            # Revision 23/07/2024 >
        # Update view widget
        self._drawImage()
        # Update display
        self._canvas.draw_idle()

    def _onThresholdChangedEvent(self):
        if self._volume.getDatatype() in _INTDATATYPES:
            tmin = int(self._editmin.value())
            tmax = int(self._editmax.value())
        else:
            tmin = self._editmin.value()
            tmax = self._editmax.value()
        if tmax > self._volume.display.getRangeMax(): tmax = self._volume.display.getRangeMax()
        if tmin < self._volume.display.getRangeMin(): tmin = self._volume.display.getRangeMin()
        if tmax < tmin: tmax = tmin
        self._set_span_left(tmin)
        self._set_span_right(tmax)
        self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)
        self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)
        if self._volume.getDatatype() in _INTDATATYPES:
            self._thresholdinftext.set_text(str(int(tmin)))
            self._thresholdsuptext.set_text(str(int(tmax)))
        else:
            self._thresholdinftext.set_text(self._format.format(tmin))
            self._thresholdsuptext.set_text(self._format.format(tmax))
        # Update img box
        self._drawImage()
        # Update display
        self._canvas.draw_idle()

    # noinspection PyUnusedLocal
    def _onThresholdFlagChangeEvent(self, event):
        if self._minflag.isChecked(): self.setThresholdFlagToMinimum()
        elif self._maxflag.isChecked(): self.setThresholdFlagToMaximum()
        else: self.setThresholdFlagToTwo()

    def _onButtonAutoEvent(self):
        otsu = OtsuThresholdImageFilter()
        otsu.Execute(self._volume.getSITKImage())
        # < Revision 23/07/2024
        # if self._volume.getDatatype() in _INTDATATYPES: self._editmin.setText(str(int(otsu.GetThreshold())))
        # else: self._editmin.setText(str(self._format.format(otsu.GetThreshold())))
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmin.setValue(int(otsu.GetThreshold()))
        else:
            self._editmin.setValue(otsu.GetThreshold())
        # Revision 23/07/2024 >
        self._onThresholdChangedEvent()

    # Public methods

    # < Revision 10/03/2025
    # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
    # finalize method must be explicitely called before class destruction
    def finalize(self):
        self._view.finalize()
    # < Revision 10/03/2025

    def getVolume(self):
        return self._volume

    def setVolume(self, volume):
        if isinstance(volume, SisypheVolume):
            self._view.removeVolume()
            self._view.setVolume(volume)
            self._view().newROI()
            self._view().getActiveROI().setAlpha(0.8)
            self._view().setCenteredCursorFlag()
            self._volume = volume
            self._initDecimals()
            self._initEdit()
            self._initHistAxes()
            self._drawImage()
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(volume)))

    def hasVolume(self):
        return self._volume is not None

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
            # < Revision 23/07/2024
            # self._editmin.setText(str(tmin))
            # self._editmax.setText(str(tmax))
            self._editmin.setValue(int(tmin))
            self._editmax.setValue(int(tmax))
            # Revision 23/07/2024 >
            self._thresholdinftext.set_text(str(int(tmin)))
            self._thresholdsuptext.set_text(str(int(tmax)))
        else:
            # < Revision 23/07/2024
            # self._editmin.setText(self._format.format(tmin))
            # self._editmax.setText(self._format.format(tmax))
            self._editmin.setValue(tmin)
            self._editmax.setValue(tmax)
            # Revision 23/07/2024 >
            self._thresholdinftext.set_text(self._format.format(tmin))
            self._thresholdsuptext.set_text(self._format.format(tmax))
        self._set_span_left(tmin)
        self._set_span_right(tmax)
        self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)
        self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)

    def setMinThreshold(self, tmin):
        if tmin < self._volume.display.getRangeMin(): tmin = self._volume.display.getRangeMin()
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmin.setValue(int(tmin))
            self._thresholdinftext.set_text(str(int(tmin)))
        else:
            self._editmin.setValue(tmin)
            self._thresholdinftext.set_text(self._format.format(tmin))
        self._set_span_left(tmin)
        self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)

    def setMaxThreshold(self, tmax):
        if tmax > self._volume.display.getRangeMax(): tmax = self._volume.display.getRangeMax()
        if self._volume.getDatatype() in _INTDATATYPES:
            self._editmax.setValue(int(tmax))
            self._thresholdsuptext.set_text(str(int(tmax)))
        else:
            self._editmax.setValue(tmax)
            self._thresholdsuptext.set_text(self._format.format(tmax))
        self._set_span_right(tmax)
        self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)

    def getThresholds(self):
        # < Revision 23/07/2024
        # return float(self._editmin.text()), float(self._editmax.text())
        return self._editmin.value(), self._editmax.value()
        # Revision 23/07/2024 >

    def getMinThreshold(self):
        # < Revision 23/07/2024
        # return float(self._editmin.text())
        return self._editmin.value()
        # Revision 23/07/2024 >

    def getMaxThreshold(self):
        # < Revision 23/07/2024
        # return float(self._editmax.text())
        return self._editmax.value()
        # Revision 23/07/2024 >

    def setAutoButtonVisibility(self, v):
        if isinstance(v, bool): self._autobutton.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getAutoButtonVisibility(self):
        return self._autobutton.isVisible()

    def setThresholdFlag(self, v):
        if isinstance(v, int):
            if 0 <= v > 3:
                if v == 0: self.setThresholdFlagToMinimum()
                elif v == 1: self.setThresholdFlagToMaximum()
                else: self.setThresholdFlagToTwo()
            else: raise ValueError('parameter value {} is not between 0 and 2.'.format(v))
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getThresholdFlag(self):
        if self._minflag.isChecked(): return 0
        elif self._maxflag.isChecked(): return 1
        else: return 2

    def setThresholdFlagToMinimum(self):
        if self._volume is not None:
            tmax = self._volume.getDisplay().getRangeMax()
            self.setMaxThreshold(tmax)
            self._set_span_right(tmax)
            self._thresholdsuptext.xyann = (tmax, self._histaxe.get_ylim()[1] / 2)
            if self._volume.getDatatype() in _INTDATATYPES: self._thresholdsuptext.set_text(str(tmax))
            else: self._thresholdsuptext.set_text('{:.2f}'.format(tmax))
            self._drawImage()
            self._canvas.draw_idle()
        self._minflag.setChecked(True)
        self._editmin.setVisible(True)
        self._editmax.setVisible(False)
        self._editmin.setToolTip('Threshold')
        self._editmin.setAlignment(Qt.AlignHCenter)

    def setThresholdFlagToMaximum(self):
        if self._volume is not None:
            tmin = self._volume.getDisplay().getRangeMin()
            self.setMinThreshold(tmin)
            self._set_span_left(tmin)
            self._thresholdinftext.xyann = (tmin, self._histaxe.get_ylim()[1] / 2)
            if self._volume.getDatatype() in _INTDATATYPES: self._thresholdinftext.set_text(str(tmin))
            else: self._thresholdinftext.set_text(self._format.format(tmin))
            self._drawImage()
            self._canvas.draw_idle()
        self._maxflag.setChecked(True)
        self._editmin.setVisible(False)
        self._editmax.setVisible(True)
        self._editmax.setToolTip('Threshold')
        self._editmax.setAlignment(Qt.AlignHCenter)

    def setThresholdFlagToTwo(self):
        self._twoflag.setChecked(True)
        self._editmin.setVisible(True)
        self._editmax.setVisible(True)
        self._editmin.setToolTip('Minimum threshold')
        self._editmax.setToolTip('Maximum threshold')
        self._editmin.setAlignment(Qt.AlignLeft)
        self._editmax.setAlignment(Qt.AlignRight)

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
    ~~~~~~~~~~~

    QWidget -> ThresholdViewWidget -> GradientThresholdViewWidget
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
