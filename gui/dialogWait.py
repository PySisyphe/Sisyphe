"""
    External packages/modules

        Name            Link                                                        Usage

        Matplotlib      https://matplotlib.org/                                     Plotting library
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
        SimpleITK       https://simpleitk.org/                                      Medical image processing
"""

from os.path import abspath
from os.path import dirname
from os.path import join

from math import log10
from math import isinf

from multiprocessing import Lock

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from SimpleITK import sitkStartEvent
from SimpleITK import sitkEndEvent
from SimpleITK import sitkProgressEvent
from SimpleITK import sitkIterationEvent
from SimpleITK import ImageFilter as sitkImageFilter

__all__ = ['UserAbortException',
           'DialogWait',
           'DialogWaitRegistration']

"""
    Class hierarchy

        Exception -> UserAbortException
        QDialog -> DialogWait -> QDialogWaitRegistration
"""


class UserAbortException(Exception):
    """
        UserAbortException

        Description

            Custom python exception to abort processing

        Inheritance

            Exception -> UserAbortException
    """
    def __init__(self, *args):
        super().__init__(*args)


class DialogWait(QDialog):
    """
        DialogWait class

        Inheritance

            QWidget - > QDialog -> DialogWait

        Private attributes

            _label          QLabel, information text
            _fig            Figure, information chart
            _progress       QProgressBar
            _anim           QMovie, gif animation movie
            _labelanim      QLabel, gif animation display
            _abort          QPushButton, cancel button
            _stopped        bool, tag to abort
            _filter         sitkImageFilter
            _currentiter    int
            _timer          QTimer

        Public class method

            str = getModuleClassDirectory()

        Public methods

            reset()
            setSimpleITKFilter(sitkImageFilter)
            addSimpleITKFilterIterationCommand(int)
            addSimpleITKFilterProcessCommand()
            setStopped()
            resetStopped()
            bool = getStopped()
            setInformationText(str)
            addInformationText(str)
            str = getInformationText()
            setProgressVisibility(bool)
            progressVisibilityOn()
            progressVisibilityOff()
            bool = getProgressVisibility()
            setProgressTextVisibility(bool)
            progressTextVisibilityOn()
            progressTextVisibilityOff()
            bool = getProgressTextVisibility()
            setAnimationVisibility(bool)
            animationVisibilityOn()
            animationVisibilityOff()
            bool = getAnimationVisibility()
            setFigureVisibility(bool)
            FigureVisibilityOn()
            FigureVisibilityOff()
            bool = getFigureVisibility()
            Figure = getFigure()
            setProgressMaximum(int)
            int = getProgressMaximum()
            setProgressMinimum(int)
            int = getProgressMinimum()
            setProgressRange(int, int)
            (int, int) = getProgressRange()
            setCurrentProgressValue(int)
            setCurrentProgressValueToMinimum()
            setCurrentProgressValueToMaximum()
            int = getCurrentProgressValue()
            incCurrentProgressValue()
            animationStart()
            animationStop()
            buttonEnabled()
            setAnimationSize(int)
            int = getAnimationSize()
            setButtonVisibility()
            buttonVisibilityOn()
            buttonVisibilityOff()
            getButtonVisibility()

            inherited QDialog methods
            inherited QWidget methods

        Revision

            12/05/2023  incCurrentProgressValue method, checks maximum
            11/11/2023  add self.adjustSize() to setInformationText() and addInformationText() methods
    """

    # Class method

    @classmethod
    def getModuleClassDirectory(cls):
        import Sisyphe.gui
        return dirname(abspath(Sisyphe.gui.__file__))

    # Special method

    def __init__(self, title='', info='',
                 progress=False,
                 progressmin=None,
                 progressmax=None,
                 progresstxt=False,
                 anim=False,
                 chart=False,
                 cancel=False,
                 parent=None):
        super().__init__(parent)

        self._stopped = False
        self._filter = None
        self._currentiter = 0
        self._baseinfo = ''
        self._timer = QTimer()
        self._timer.timeout.connect(self._onTimer)

        self._fig = Figure()
        self._canvas = FigureCanvas(self._fig)

        self._info = QLabel()
        self._info.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        gif = join(self.getModuleClassDirectory(), 'icons', 'wait01.gif')
        self._anim = QMovie(gif)
        self._labelanim = QLabel()
        self._labelanim.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self._labelanim.setMovie(self._anim)
        self._progress = QProgressBar()
        self._progress.setFixedSize(200, 20)
        self._abort = QPushButton('Cancel')
        self._abort.setFixedWidth(100)
        self._abort.setAutoDefault(True)
        self._abort.setDefault(True)
        self._abort.clicked.connect(self._stop)

        # Set defaults

        self.setWindowTitle(title)
        self._info.setText(info)
        self._progress.setVisible(progress)
        self._progress.setTextVisible(progresstxt)
        if progressmin is not None: self._progress.setMinimum(progressmin)
        if progressmax is not None: self._progress.setMaximum(progressmax)
        self._labelanim.setVisible(anim)
        self._canvas.setVisible(chart)
        self._abort.setVisible(cancel)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(50, 50, 50, 50)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

        self._layout.addWidget(self._canvas)
        self._layout.addWidget(self._labelanim)
        self._layout.addWidget(self._info)
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addWidget(self._progress)
        layout.addWidget(self._abort)
        self._layout.addLayout(layout)

        # Window

        self.setWindowFlags(Qt.CustomizeWindowHint)
        self.setWindowModality(Qt.ApplicationModal)

    # Private method

    def _stop(self):
        self._stopped = True
        QApplication.processEvents()

    @staticmethod
    def _onTimer():
        QApplication.processEvents()

    def _onIteration(self):
        self._currentiter += 1
        if self.getProgressVisibility(): self._progress.setValue(self._currentiter)
        else: self._info.setText('{} iteration {}'.format(self._baseinfo, self._currentiter))
        if self._stopped: raise UserAbortException()
        QApplication.processEvents()

    def _onProgress(self):
        self._progress.setValue(int(self._filter.GetProgress() * 100))
        if self._stopped: raise UserAbortException()
        QApplication.processEvents()

    def _onStart(self):
        if self._labelanim.isVisible(): self.animationStart()

    def _onEnd(self):
        if self._labelanim.isVisible(): self.animationStop()

    def _center(self):
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public methods

    def setStopped(self):
        self._stopped = True

    def resetStopped(self):
        self._stopped = False

    def getStopped(self):
        return self._stopped

    def reset(self):
        if self._filter is not None: self._filter.RemoveAllCommands()
        self._filter = None
        self._stopped = False
        self._currentiter = 0
        self._baseinfo = ''

    def setSimpleITKFilter(self, filtr):
        if isinstance(filtr, sitkImageFilter): self._filter = filtr
        else: raise TypeError('parameter type {} is not sitkImageFilter.')

    def addSimpleITKFilterIterationCommand(self, niter):
        if isinstance(niter, int) and self._filter is not None:
            self._currentiter = 0
            self._progress.setMinimum(0)
            self._progress.setMaximum(niter)
            self._progress.setValue(0)
            self._filter.RemoveAllCommands()
            self._filter.AddCommand(sitkStartEvent, self._onStart)
            self._filter.AddCommand(sitkEndEvent, self._onEnd)
            self._filter.AddCommand(sitkIterationEvent, self._onIteration)
            QApplication.processEvents()
        else: raise TypeError('parameter type {} is not int.'.format(niter))

    def addSimpleITKFilterProcessCommand(self):
        if self._filter is not None:
            self._progress.setMinimum(0)
            self._progress.setMaximum(100)
            self._progress.setValue(0)
            self._filter.RemoveAllCommands()
            self._filter.AddCommand(sitkStartEvent, self._onStart)
            self._filter.AddCommand(sitkEndEvent, self._onEnd)
            self._filter.AddCommand(sitkProgressEvent, self._onProgress)
            QApplication.processEvents()
        else: raise TypeError('No SimpleITK filter.')

    def setInformationText(self, txt):
        if isinstance(txt, str):
            self._baseinfo = txt
            self._info.setText(txt)
            self.adjustSize()
            QApplication.processEvents()
            self._center()
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def addInformationText(self, txt):
        self._info.setText('{}\n{}'.format(self._baseinfo, txt))
        self.adjustSize()
        QApplication.processEvents()
        self._center()

    def getInformationText(self):
        return self._info.text()

    def setProgressVisibility(self, v):
        if isinstance(v, bool):
            self._progress.setVisible(v)
            QApplication.processEvents()
            self._center()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def progressVisibilityOn(self):
        self.setProgressVisibility(True)

    def progressVisibilityOff(self):
        self.setProgressVisibility(False)

    def getProgressVisibility(self):
        return self._progress.isVisible()

    def setAnimationVisibility(self, v):
        if isinstance(v, bool):
            self._labelanim.setVisible(v)
            QApplication.processEvents()
            self._center()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def animationVisibilityOn(self):
        self.setAnimationVisibility(True)

    def animationVisibilityOff(self):
        self.setAnimationVisibility(False)

    def getAnimationVisibility(self):
        return self._labelanim.isVisible()

    def setFigureVisibility(self, v):
        if isinstance(v, bool):
            self._canvas.setVisible(v)
            QApplication.processEvents()
            self._center()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def FigureVisibilityOn(self):
        self.setFigureVisibility(True)

    def FigureVisibilityOff(self):
        self.setFigureVisibility(False)

    def getFigureVisibility(self):
        return self._canvas.isVisible()

    def getFigure(self):
        return self._fig

    def setProgressTextVisibility(self, v):
        if isinstance(v, bool):
            self._progress.setTextVisible(v)
            QApplication.processEvents()
            self._center()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def progressTextVisibilityOn(self):
        self.setProgressTextVisibility(True)

    def progressTextVisibilityOff(self):
        self.setProgressTextVisibility(False)

    def getProgressTextVisibility(self):
        return self._progress.isTextVisible()

    def setProgressMaximum(self, v):
        if isinstance(v, int):
            self.setVisible(v > 1)
            self._progress.setMaximum(v)
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getProgressMaximum(self):
        return self._progress.maximum()

    def setProgressMinimum(self, v):
        if isinstance(v, int):
            self._progress.setMinimum(v)
            self._progress.setValue(v)
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getProgressMinimum(self):
        return self._progress.minimum()

    def setProgressRange(self, vmin, vmax):
        if vmin > vmax: vmin, vmax = vmax, vmin
        self._progress.setMaximum(vmax)
        self._progress.setMinimum(vmin)

    def getProgressRange(self):
        return self._progress.minimum(), self._progress.maximum()

    def setCurrentProgressValue(self, v):
        if isinstance(v, int):
            if v < self._progress.minimum(): v = self._progress.minimum()
            if v > self._progress.maximum(): v = self._progress.maximum()
            self._progress.setValue(v)
            QApplication.processEvents()
        else:
            raise TypeError('parameter type {} is not int.'.format(type(v)))

    def setCurrentProgressValuePercent(self, v, dummy):
        if isinstance(v, float):
            if 0.0 <= v <= 1.0: self._progress.setValue(int(v*100))
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        elif isinstance(v, int):
            if 0 <= v <= 100: self._progress.setValue(v)
            else: raise ValueError('parameter value {} is not between 0 and 100.'.format(v))
        else: raise TypeError('parameter type {} is not int or float.'.format(type(v)))

    def getCurrentProgressValue(self):
        return self._progress.value()

    def incCurrentProgressValue(self):
        if self._progress.value() < self._progress.maximum():
            self.setCurrentProgressValue(self._progress.value() + 1)
            QApplication.processEvents()

    def setCurrentProgressValueToMinimum(self):
        self.setCurrentProgressValue(self._progress.minimum())
        QApplication.processEvents()

    def setCurrentProgressValueToMaximum(self):
        self.setCurrentProgressValue(self._progress.maximum())
        QApplication.processEvents()

    def animationStart(self):
        self.animationVisibilityOn()
        self._anim.start()

    def animationStop(self):
        self._anim.stop()
        self.animationVisibilityOff()

    def setAnimationSize(self, v):
        if isinstance(v, int):
            self._anim.setScaledSize(QSize(v, v))
            QApplication.processEvents()
        else: raise TypeError('parameter type {} is not int'.format(type(v)))

    def getAnimationSize(self):
        return self._anim.scaledSize().width()

    def buttonEnabled(self, v):
        if isinstance(v, bool):
            self._abort.setEnabled(v)
            QApplication.processEvents()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setButtonVisibility(self, v):
        if isinstance(v, bool):
            self._abort.setVisible(v)
            QApplication.processEvents()
            self._center()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def buttonVisibilityOn(self):
        self.setButtonVisibility(True)

    def buttonVisibilityOff(self):
        self.setButtonVisibility(False)

    def getButtonVisibility(self):
        return self._abort.isVisible()

    # Qt event

    def showEvent(self, event):
        self._stopped = False
        if self.getAnimationVisibility() or self.getButtonVisibility(): self._timer.start()
        self._center()

    def hideEvent(self, event):
        if self._timer.isActive(): self._timer.stop()


class DialogWaitRegistration(DialogWait):
    """
        DialogWait class

        Inheritance

            QWidget - > QDialog -> DialogWait -> DialogWaitRegistration

        Private attributes

            _cstage         int
            _clevel         int
            _citer          int
            _progbystage    list[int], cumulative progress in each stage
            _progbylevel    list[list[int]], number of iterations in each stage and multiresolution level
            _conv           list[float], convergence threshold in each stage
            _multir         list[int], number of iterations per level in multi-resolution scheme
            _stages         list[str], name of each stage
            _nstages        int, number of stages ( = len(_stages) )
            _pos            int, position in log file

        Public methods

            setMultiResolutionIterations(list[int])
            setStages(list[str])
            setProgressByLevel(list[list[int]])
            setConvergenceThreshold(list[float])
            setAntsRegistrationProgress(str)

            inherited QDialogWaitRegistration methods
            inherited QDialog methods
            inherited QWidget methods
    """

    # Special method

    def __init__(self, title='', info='',
                 progress=False,
                 progressmin=None,
                 progressmax=None,
                 progresstxt=False,
                 anim=False,
                 chart=False,
                 cancel=False,
                 parent=None):
        super().__init__(title, info, progress, progressmin, progressmax,
                         progresstxt, anim, chart, cancel, parent)
        self._nstages = 0
        self._citer = 0
        self._clevel = 0
        self._cstage = 0
        self._cprogress = 0
        self._pos = 0
        self._progbylevel = None
        self._progbystage = None
        self._multir = None
        self._stages = None
        self._conv = None

    # Public method

    def setMultiResolutionIterations(self, v):
        if isinstance(v, list):
            if self._nstages == 0: self._nstages = len(v)
            if len(v) == self._nstages:
                self._multir = v
                self.setProgressVisibility(True)
                # Reset attributes
                self._citer = 0
                self._clevel = 0
                self._cstage = 0
                self._cprogress = 0
                self._pos = 0
                self.setCurrentProgressValue(0)
            else: raise ValueError('Incorrect number of items in list '
                                   'parameter (set {} and must be {}).'.format(len(v), self._nstages))
        else: raise TypeError('parameter type {} is not list.'.format(type(v)))

    def setStages(self, v):
        if isinstance(v, list):
            if self._nstages == 0: self._nstages = len(v)
            if len(v) == self._nstages: self._stages = v
            else: raise ValueError('Incorrect number of items in list '
                                   'parameter (set {} and must be {}).'.format(len(v), self._nstages))
        else: raise TypeError('parameter type {} is not list.'.format(type(v)))

    def setProgressByLevel(self, v):
        if isinstance(v, list):
            if self._nstages == 0: self._nstages = len(v)
            if len(v) == self._nstages:
                self._progbylevel = v
                self._progbystage = list()
                for sv in v:
                    c = 0
                    buff = [0]
                    for psv in sv:
                        c += psv
                        buff.append(c)
                    self._progbystage.append(buff)
            else: raise ValueError('Incorrect number of items in list '
                                   'parameter (set {} and must be {}).'.format(len(v), self._nstages))
        else: raise TypeError('parameter type {} is not list.'.format(type(v)))

    def setConvergenceThreshold(self, v):
        if isinstance(v, list):
            if self._nstages == 0: self._nstages = len(v)
            if len(v) == self._nstages: self._conv = v
            else: raise ValueError('Incorrect number of items in list '
                                   'parameter (set {} and must be {}).'.format(len(v), self._nstages))
        else: raise TypeError('parameter type {} is not list.'.format(type(v)))

    def setAntsRegistrationProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            citer = 0
            cprogress = 0
            plevel = self._clevel
            for line in reversed(verbose):
                sub = line[:5]
                # Current iter
                if sub in (' 2DIA', ' 1DIA'):
                    # 2DIA Rigid/Affine, 1DIA Displacement Field
                    if cprogress == 0:
                        w = line.split(',')
                        if len(w) > 4:  # line contains convergence value
                            citer = int(w[1])
                            v = float(w[3])
                            if isinf(v): cprogress = 0
                            else:
                                if self._cstage == 0: cconv = self._conv[0]
                                else: cconv = self._conv[self._cstage - 1]
                                cprogress = (log10(float(w[3])) + cconv) / cconv
                            continue
                # Current level Affine/Rigid
                elif sub in ('DIAGN', 'XXDIA'):
                    # DIAGN Rigid/Affine, XXDIA Displacement Field
                    self._clevel += 1
                    continue
                # Current stage
                elif sub == 'Stage':
                    w = line.split(' ')
                    if len(w) == 2:
                        self._cstage = int(w[1]) + 1
                        self.setProgressRange(0, self._progbystage[self._cstage - 1][-1])
                        self.setCurrentProgressValue(0)
                        self._clevel = self._clevel - plevel
                        break
            # Update current iter and current progress
            if plevel == self._clevel:
                if citer > self._citer: self._citer = citer
                if cprogress > self._cprogress: self._cprogress = cprogress
            else:
                self._citer = citer
                self._cprogress = cprogress
            if self._cstage > 0 and self._clevel > 0:
                v = citer / self._multir[self._cstage-1][self._clevel-1]
                if v > self._cprogress: self._cprogress = v
                nb1 = self._progbystage[self._cstage - 1]
                nb2 = self._progbylevel[self._cstage - 1]
                v = int(nb1[self._clevel - 1] + nb2[self._clevel - 1] * self._cprogress)
                info = 'Registration stage {}/{} {}\nMultiresolution Level {}/{}'.format(self._cstage,
                                                                                         len(self._stages),
                                                                                         self._stages[self._cstage-1],
                                                                                         self._clevel,
                                                                                         len(self._multir[self._cstage-1]))
            else:
                v = 0
                info = 'Registration stage 1/{} {}\nMultiresolution Level 1/{}'.format(len(self._stages),
                                                                                       self._stages[0],
                                                                                       len(self._multir[0]))
            self.setInformationText(info)
            self.setCurrentProgressValue(v)

