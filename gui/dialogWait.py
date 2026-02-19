"""
External packages/modules
-------------------------

    - Matplotlib, Plotting library, https://matplotlib.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, Medical image processing, https://simpleitk.org/
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Any

from sys import platform

from os.path import abspath
from os.path import dirname

from datetime import datetime

from math import log10
from math import isinf
from math import isnan

from numpy import array

from multiprocessing import Lock

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt
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

# noinspection PyCompatibility
import __main__

# to avoid ImportError due to circular imports
if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget

__all__ = ['UserAbortException',
           'DialogWait',
           'DialogWaitRegistration']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - Exception -> UserAbortException
    - QDialog -> DialogWait -> QDialogWaitRegistration
"""


class UserAbortException(Exception):
    """
    UserAbortException

    Description
    ~~~~~~~~~~~

    Custom python exception to abort processing.
    """
    def __init__(self, *args) -> None:
        super().__init__(*args)


class DialogWait(QDialog):
    """
    DialogWait class

    Description
    ~~~~~~~~~~~

    Wait and progress dialog.

    Inheritance
    ~~~~~~~~~~~

    QWidget - > QDialog -> DialogWait

    Last revision: 17/07/2025
    """

    # Class method

    @classmethod
    def getModuleClassDirectory(cls) -> str:
        import Sisyphe.gui
        return dirname(abspath(Sisyphe.gui.__file__))

    # Special method

    """
    Private attributes

    _label          QLabel, information text
    _fig            Figure, information chart
    _progress       QProgressBar
    _abort          QPushButton, cancel button
    _stopped        bool, tag to abort
    _filter         sitkImageFilter
    _currentiter    int
    """

    # noinspection PyUnusedLocal
    def __init__(self,
                 title: str = '',
                 info: str = '',
                 progress: bool = False,
                 progressmin: int | None = None,
                 progressmax: int | None = None,
                 progresstxt: bool = False,
                 chart: bool = False,
                 cancel: bool = False,
                 parent: QWidget | None = None) -> None:
        """
        DialogWait dialog constructor.

        Parameters
        ----------
        title : str (optional)
            The window title of the dialog. Defaults to ''.
        info : str, optional
            Initial information text displayed in the dialog. Defaults to ''.
        progress : bool (optional)
            If True, the progress bar is visible. Defaults to False.
        progressmin : int | None (optional)
            Minimum value for the progress bar. Defaults to None.
        progressmax : int | None (optional)
            Maximum value for the progress bar. Defaults to None.
        progresstxt : bool (optional)
            If True, the progress bar displays text. Defaults to False.
        chart : bool (optional)
            If True, the Matplotlib chart canvas is visible. Defaults to False.
        cancel : bool (optional)
            If True, the cancel button is visible. Defaults to False.
        parent : QWidget | None (optional)
            The parent widget of the dialog. Defaults to None.
        """
        super().__init__()

        # Window

        self.setObjectName('DialogWait')
        if platform == 'win32':
            # noinspection PyUnresolvedReferences
            self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
            try: __main__.updateWindowTitleBarColor(self)
            except: pass
            self._layout = QVBoxLayout()
            self.setLayout(self._layout)
        elif platform == 'darwin':
            # < Revision 17/07/2025
            # bug fix darwin platform, to get a dialog box with rounded border
            # noinspection PyUnresolvedReferences
            self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
            # noinspection PyUnresolvedReferences
            self.setAttribute(Qt.WA_TranslucentBackground)
            from PyQt5.QtWidgets import QFrame
            self._frame = QFrame()
            self._frame.setObjectName('WaitFrame')
            self._slayout = QVBoxLayout()
            self._slayout.setContentsMargins(0, 0, 0, 0)
            self._slayout.addWidget(self._frame)
            bcolor = self.palette().window().color()
            self.setStyleSheet(
                f"QFrame#WaitFrame {{"
                f"  background-color: {bcolor.name()};"
                f"  border-radius: 10px;"
                f"}}")
            self._layout = QVBoxLayout()
            self._frame.setLayout(self._layout)
            self.setLayout(self._slayout)
            # Revision 17/07/2025 >

        # < Revision 21/05/2025
        self.setModal(True)
        # Revision 21/05/2025 >

        self._stopped = False
        self._filter = None
        self._currentiter = 0
        self._baseinfo = ''

        # Widgets

        self._fig = Figure()
        self._canvas = FigureCanvas(self._fig)

        self._info = QLabel(parent=self)
        # noinspection PyUnresolvedReferences
        self._info.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        self._progress = QProgressBar(parent=self)
        self._progress.setFixedSize(200, 20)
        self._abort = QPushButton('Cancel', parent=self)
        self._abort.setFixedWidth(100)
        self._abort.setAutoDefault(True)
        self._abort.setDefault(True)
        # noinspection PyUnresolvedReferences
        self._abort.clicked.connect(self._stop)

        # Set defaults

        # self.setWindowTitle(title)
        self._info.setText(info)
        self._progress.setVisible(progress)
        self._progress.setTextVisible(progresstxt)
        if progressmin is not None: self._progress.setMinimum(progressmin)
        if progressmax is not None: self._progress.setMaximum(progressmax)
        self._canvas.setVisible(chart)
        self._abort.setVisible(cancel)

        # Init QLayout

        self._layout.setContentsMargins(50, 50, 50, 50)
        self._layout.setSpacing(10)

        self._layout.addWidget(self._canvas)
        self._layout.addWidget(self._info)
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.addStretch()
        layout.addWidget(self._progress)
        layout.addWidget(self._abort)
        layout.addStretch()
        self._layout.addLayout(layout)

    # Private method

    def _stop(self) -> None:
        """
        Sets the internal flag to indicate that the process should be stopped.
        Updates button visibility and processes pending GUI events.
        """
        self._stopped = True
        # < Revision 10/10/2024
        # add self.buttonVisibilityOff()
        self.buttonVisibilityOff()
        # Revision 10/10/2024 >
        QApplication.processEvents()

    def _onIteration(self) -> None:
        """
        Callback function for SimpleITK's sitkIterationEvent.
        Increments the current iteration, updates the progress bar or info text, and checks for user abort.
        Raises UserAbortException if stopped.
        """
        self._currentiter += 1
        if self.getProgressVisibility(): self._progress.setValue(self._currentiter)
        else: self._info.setText('{} iteration {}'.format(self._baseinfo, self._currentiter))
        QApplication.processEvents()
        if self._stopped:
            self.buttonVisibilityOff()
            raise UserAbortException
        QApplication.processEvents()

    def _onProgress(self) -> None:
        """
        Callback function for SimpleITK's sitkProgressEvent.
        Updates the progress bar based on the filter's progress, and checks for user abort.
        Raises UserAbortException if stopped.
        """
        self._progress.setValue(int(self._filter.GetProgress() * 100))
        QApplication.processEvents()
        if self._stopped:
            self.buttonVisibilityOff()
            raise UserAbortException
        QApplication.processEvents()

    def _onStart(self) -> None:
        """
        Callback function for SimpleITK's sitkStartEvent.
        Currently does nothing.
        """
        pass

    def _onEnd(self) -> None:
        """
        Callback function for SimpleITK's sitkEndEvent.
        Currently does nothing.
        """
        pass

    def _center(self) -> None:
        """
        Centers the dialog on the screen.
        Processes pending GUI events to ensure correct positioning.
        """
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public methods

    def open(self) -> None:
        """
        Opens the dialog.
        On macOS, it overrides the default open() to handle title bar display.
        """
        if platform == 'darwin':
            # bug fix darwin platform, open() always displays a title bar
            # override open() to call show() and hide title bar
            self.show()
        else: super().open()

    def setStopped(self) -> None:
        """
        Manually sets the internal stopped flag to True.
        """
        self._stopped = True

    def resetStopped(self) -> None:
        """
        Resets the internal stopped flag to False.
        """
        self._stopped = False

    def getStopped(self) -> bool:
        """
        Returns the current state of the stopped flag.

        Returns
        -------
        bool
            True if the process is stopped, False otherwise.
        """
        return self._stopped

    def reset(self) -> None:
        """
        Resets the dialog's internal state, including the SimpleITK filter, stopped flag, current iteration, and base
        information text.
        """
        if self._filter is not None: self._filter.RemoveAllCommands()
        self._filter = None
        self._stopped = False
        self._currentiter = 0
        self._baseinfo = ''

    def setSimpleITKFilter(self, filtr: sitkImageFilter) -> None:
        """
        Sets the SimpleITK image filter to monitor.

        Parameters
        ----------
        filtr : sitkImageFilter
            The SimpleITK image filter instance.
        """
        if isinstance(filtr, sitkImageFilter): self._filter = filtr
        else: raise TypeError('parameter type {} is not sitkImageFilter.')

    def addSimpleITKFilterIterationCommand(self, niter: int) -> None:
        """
        Configures the dialog to monitor a SimpleITK filter's iteration events.
        Sets progress bar range and attaches event commands.

        Parameters
        ----------
        niter : int
            The total number of iterations for the process.
        """
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

    def addSimpleITKFilterProcessCommand(self) -> None:
        """
        Configures the dialog to monitor a SimpleITK filter's progress events.
        Sets progress bar range and attaches event commands.
        """
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

    def setInformationText(self, txt: str) -> None:
        """
        Sets the main information text displayed in the dialog.
        Adjusts dialog size and centers it.

        Parameters
        ----------
        txt : str
            The text to display.
        """
        if isinstance(txt, str):
            self._baseinfo = txt
            self._info.setText(txt)
            self.adjustSize()
            self._center()
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def addInformationText(self, txt: str = '') -> None:
        """
        Appends additional information text to the current display.
        If txt is empty, it resets to the base information.
        Adjusts dialog size and centers it.

        Parameters
        ----------
        txt : str, optional
            The additional text to append. Defaults to ''.
        """
        if txt == '': self._info.setText(self._baseinfo)
        else: self._info.setText('{}\n{}'.format(self._baseinfo, txt))
        self.adjustSize()
        self._center()

    def getInformationText(self) -> str:
        """
        Retrieves the currently displayed information text.

        Returns
        -------
        str
            The current information text.
        """
        return self._info.text()

    def setProgressVisibility(self, v: bool) -> None:
        """
        Sets the visibility of the progress bar.
        Adjusts dialog size and centers it.

        Parameters
        ----------
        v : bool
            True to show the progress bar, False to hide it.
        """
        if isinstance(v, bool):
            self._progress.setVisible(v)
            self._center()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def progressVisibilityOn(self) -> None:
        """
        Makes the progress bar visible.
        Adjusts dialog size and centers it.
        """
        self.setProgressVisibility(True)

    def progressVisibilityOff(self) -> None:
        """
        Hides the progress bar.
        Adjusts dialog size and centers it.
        """
        self.setProgressVisibility(False)
        # < Revision 05/11/2024
        # add size and position adjustment
        self.adjustSize()
        self._center()
        # Revision 05/11/2024 >

    def getProgressVisibility(self) -> bool:
        """
        Checks if the progress bar is visible.

        Returns
        -------
        bool
            True if the progress bar is visible, False otherwise.
        """
        return self._progress.isVisible()

    def setFigureVisibility(self, v: bool) -> None:
        """
        Sets the visibility of the Matplotlib figure canvas.
        Adjusts dialog size and centers it.

        Parameters
        ----------
        v : bool
            True to show the figure, False to hide it.
        """
        if isinstance(v, bool):
            self._canvas.setVisible(v)
            self._center()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def FigureVisibilityOn(self) -> None:
        """
        Makes the Matplotlib figure canvas visible.
        Adjusts dialog size and centers it.
        """
        self.setFigureVisibility(True)

    def FigureVisibilityOff(self) -> None:
        """
        Hides the Matplotlib figure canvas.
        Adjusts dialog size and centers it.
        """
        self.setFigureVisibility(False)

    def getFigureVisibility(self) -> None:
        """
        Checks if the Matplotlib figure canvas is visible.

        Returns
        -------
        bool
            True if the figure canvas is visible, False otherwise.
        """
        return self._canvas.isVisible()

    def getFigure(self) -> Figure:
        """
        Retrieves the Matplotlib Figure object used by the dialog.

        Returns
        -------
        Figure
            The Matplotlib Figure instance.
        """
        return self._fig

    def setProgressTextVisibility(self, v: bool) -> None:
        """
        Sets the visibility of the text displayed on the progress bar.
        Adjusts dialog size and centers it.

        Parameters
        ----------
        v : bool
            True to show progress text, False to hide it.
        """
        if isinstance(v, bool):
            self._progress.setTextVisible(v)
            self._center()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def progressTextVisibilityOn(self) -> None:
        """
        Makes the progress bar text visible.
        Adjusts dialog size and centers it.
        """
        self.setProgressTextVisibility(True)

    def progressTextVisibilityOff(self) -> None:
        """
        Hides the progress bar text.
        Adjusts dialog size and centers it.
        """
        self.setProgressTextVisibility(False)

    def getProgressTextVisibility(self) -> bool:
        """
        Checks if the progress bar text is visible.

        Returns
        -------
        bool
            True if the progress bar text is visible, False otherwise.
        """
        return self._progress.isTextVisible()

    def setProgressMaximum(self, v: int) -> None:
        """
        Sets the maximum value of the progress bar.
        The dialog's visibility is also set based on whether v > 1.

        Parameters
        ----------
        v : int
            The maximum value.
        """
        if isinstance(v, int):
            self.setVisible(v > 1)
            self._progress.setMaximum(v)
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getProgressMaximum(self) -> int:
        """
        Retrieves the maximum value of the progress bar.

        Returns
        -------
        int
            The maximum progress bar value.
        """
        return self._progress.maximum()

    def setProgressMinimum(self, v: int) -> None:
        """
        Sets the minimum value of the progress bar and updates its current value.

        Parameters
        ----------
        v : int
            The minimum value.
        """
        if isinstance(v, int):
            self._progress.setMinimum(v)
            self._progress.setValue(v)
        else: raise TypeError('parameter type {} is not int.'.format(type(v)))

    def getProgressMinimum(self) -> int:
        """
        Retrieves the minimum value of the progress bar.

        Returns
        -------
        int
            The minimum progress bar value.
        """
        return self._progress.minimum()

    def setProgressRange(self, vmin: int, vmax: int) -> None:
        """
        Sets the minimum and maximum values for the progress bar.
        Ensures vmin is not greater than vmax by swapping if necessary.

        Parameters
        ----------
        vmin : int
            The minimum value.
        vmax : int
            The maximum value.
        """
        if vmin > vmax: vmin, vmax = vmax, vmin
        self._progress.setMaximum(vmax)
        self._progress.setMinimum(vmin)

    def getProgressRange(self) -> tuple[int, int]:
        """
        Retrieves the current minimum and maximum values of the progress bar.

        Returns
        -------
        tuple[int, int]
            A tuple containing (minimum_value, maximum_value).
        """
        return self._progress.minimum(), self._progress.maximum()

    def setCurrentProgressValue(self, v: int) -> None:
        """
        Sets the current value of the progress bar.
        Clamps the value within the defined minimum and maximum range.
        Processes pending GUI events.

        Parameters
        ----------
        v : int
            The value to set.
        """
        if isinstance(v, int):
            if v < self._progress.minimum(): v = self._progress.minimum()
            if v > self._progress.maximum(): v = self._progress.maximum()
            self._progress.setValue(v)
            QApplication.processEvents()
        else:
            raise TypeError('parameter type {} is not int.'.format(type(v)))

    def messageFromDictProxyManager(self, mng: dict[str, str | int | None]) -> None:
        """
        Updates the dialog's state based on a dictionary from a proxy manager.
        Handles updates for information text, progress bar range, and current value.
        Processes pending GUI events.

        Parameters
        ----------
        mng : dict[str, str | int | None]
            A dictionary containing update commands (e.g., 'msg', 'amsg', 'max', 'value', 'inc').
        """
        if 'msg' in mng:
            if mng['msg'] is not None:
                self.setInformationText(mng['msg'])
                mng['msg'] = None
        if 'amsg' in mng:
            if mng['amsg'] is not None:
                self.addInformationText(mng['amsg'])
                mng['amsg'] = None
        if 'max' in mng:
            if mng['max'] is not None:
                if mng['max'] > 0:
                    self.setProgressRange(0, mng['max'])
                    if not self.getProgressVisibility(): self.progressVisibilityOn()
                    mng['max'] = None
                else:
                    self.progressVisibilityOff()
                    mng['max'] = None
        if 'value' in mng:
            if mng['value'] is not None:
                self.setCurrentProgressValue(mng['value'])
                mng['value'] = None
        # < Revision 11/07/2025
        if 'inc' in mng:
            if mng['inc'] is not None:
                self.incCurrentProgressValue()
                mng['inc'] = None
        # Revision 11/07/2025 >
        QApplication.processEvents()

    # noinspection PyUnusedLocal
    def setCurrentProgressValuePercent(self, v: float | int, dummy: Any) -> None:
        """
        Sets the current value of the progress bar as a percentage (0-100).
        Processes pending GUI events.

        Parameters
        ----------
        v : float | int
            The percentage value. Can be a float (0.0-1.0) or an int (0-100).
        dummy : Any
            A placeholder parameter (unused).
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                self._progress.setValue(int(v*100))
                QApplication.processEvents()
            else: raise ValueError('parameter value {} is not between 0.0 and 1.0.'.format(v))
        elif isinstance(v, int):
            if 0 <= v <= 100:
                self._progress.setValue(v)
                QApplication.processEvents()
            else: raise ValueError('parameter value {} is not between 0 and 100.'.format(v))
        else: raise TypeError('parameter type {} is not int or float.'.format(type(v)))

    def getCurrentProgressValue(self) -> int:
        """
        Retrieves the current value of the progress bar.

        Returns
        -------
        int
            The current progress bar value.
        """
        return self._progress.value()

    def incCurrentProgressValue(self) -> None:
        """
        Increments the current value of the progress bar by one, if it's less than the maximum value.
        Processes pending GUI events.
        """
        if self._progress.value() < self._progress.maximum():
            self.setCurrentProgressValue(self._progress.value() + 1)
            QApplication.processEvents()

    def setCurrentProgressValueToMinimum(self) -> None:
        """
        Sets the current progress bar value to its minimum.
        Processes pending GUI events.
        """
        self.setCurrentProgressValue(self._progress.minimum())
        QApplication.processEvents()

    def setCurrentProgressValueToMaximum(self) -> None:
        """
        Sets the current progress bar value to its maximum.
        Processes pending GUI events.
        """
        self.setCurrentProgressValue(self._progress.maximum())
        QApplication.processEvents()

    def buttonEnabled(self, v: bool) -> None:
        """
        Enables or disables the cancel button.
        Processes pending GUI events.

        Parameters
        ----------
        v : bool
            True to enable, False to disable.
        """
        if isinstance(v, bool):
            self._abort.setEnabled(v)
            QApplication.processEvents()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setButtonVisibility(self, v: bool) -> None:
        """
        Sets the visibility of the cancel button.
        Adjusts dialog size and centers it.

        Parameters
        ----------
        v : bool
            True to show the button, False to hide it.
        """
        if isinstance(v, bool):
            self._abort.setVisible(v)
            self._center()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def buttonVisibilityOn(self) -> None:
        """
        Makes the cancel button visible.
        Adjusts dialog size and centers it.
        """
        self.setButtonVisibility(True)

    def buttonVisibilityOff(self) -> None:
        """
        Hides the cancel button.
        Adjusts dialog size and centers it.
        """
        self.setButtonVisibility(False)

    def getButtonVisibility(self) -> bool:
        """
        Checks if the cancel button is visible.

        Returns
        -------
        bool
            True if the button is visible, False otherwise.
        """
        return self._abort.isVisible()

    # Qt event

    def showEvent(self, event: Any):
        """
        Event handler for when the dialog is shown.
        Resets the stopped flag and centers the dialog.

        Parameters
        ----------
        event : Any
            The show event object.
        """
        super().showEvent(event)
        self._stopped = False
        self._center()


class DialogWaitRegistration(DialogWait):
    """
    DialogWaitRegistration class

    Description
    ~~~~~~~~~~~

    Wait and progress GUI dialog invoked while registering.

    Inheritance
    ~~~~~~~~~~~

    QWidget - > QDialog -> DialogWait -> DialogWaitRegistration

    Last revision: 31/01/2026
    """

    # Special method

    """
    Private attributes

    _cstage         int
    _clevel         int
    _nlevel         int
    _citer          int
    _progbystage    list[int], cumulative progress in each stage
    _progbylevel    list[list[int]], number of iterations in each stage and multiresolution level
    _conv           list[float], convergence threshold in each stage
    _multir         list[int], number of iterations per level in multi-resolution scheme
    _stages         list[str], name of each stage
    _nstages        int, number of stages ( = len(_stages) )
    _pos            int, position in log file
    """

    def __init__(self, title='', info='',
                 progress=False,
                 progressmin=None,
                 progressmax=None,
                 progresstxt=False,
                 chart=False,
                 cancel=False,
                 parent=None):
        super().__init__(title, info, progress, progressmin, progressmax,
                         progresstxt, chart, cancel, parent)
        self._pos = 0
        self._nstages = 0
        self._clevel = None
        self._cstage = None
        self._progbylevel = None
        self._multir = None
        self._stages = None
        self._conv = None
        self._time = None

    # Public method

    def setMultiResolutionIterations(self, v):
        if isinstance(v, list):
            # < Revision 31/01/2026
            # if self._nstages == 0: self._nstages = len(v)
            # if len(v) == self._nstages:
            self._multir = v
            # Revision 04/02/2026 >
            # Reset attributes
            self._clevel = None
            self._cstage = None
            self._time = None
            self._pos = 0
            self.setCurrentProgressValue(0)
            # else: raise ValueError('Incorrect number of items in list '
            #                        'parameter (set {} and must be {}).'.format(len(v), self._nstages))
            # Revision 31/01/2026 >
        else: raise TypeError('parameter type {} is not list.'.format(type(v)))

    def setStages(self, v):
        if isinstance(v, list):
            # < Revision 31/01/2026
            # if self._nstages == 0: self._nstages = len(v)
            # if len(v) == self._nstages: self._stages = v
            self._nstages = len(v)
            self._stages = v
            # else: raise ValueError('Incorrect number of items in list '
            #                        'parameter (set {} and must be {}).'.format(len(v), self._nstages))
            # Revision 31/01/2026 >
        else: raise TypeError('parameter type {} is not list.'.format(type(v)))

    def setProgressByLevel(self, v):
        if isinstance(v, list):
            # < Revision 31/01/2026
            # if self._nstages == 0: self._nstages = len(v)
            # if len(v) == self._nstages: self._progbylevel = array(v)
            self._progbylevel = array(v)
            # else: raise ValueError('Incorrect number of items in list '
            #                        'parameter (set {} and must be {}).'.format(len(v), self._nstages))
            # Revision 31/01/2026 >
        else: raise TypeError('parameter type {} is not list.'.format(type(v)))

    def setConvergenceThreshold(self, v):
        if isinstance(v, list):
            # < Revision 31/01/2026
            # if self._nstages == 0: self._nstages = len(v)
            # if len(v) == self._nstages: self._conv = v
            self._conv = v
            # else: raise ValueError('Incorrect number of items in list '
            #                        'parameter (set {} and must be {}).'.format(len(v), self._nstages))
            # Revision 31/01/2026 >
        else: raise TypeError('parameter type {} is not list.'.format(type(v)))

    def setAntsRegistrationProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            pstage = self._cstage
            plevel = self._clevel
            nlevels = len(self._multir[0])
            for line in verbose:
                sub = line[:5]
                # < Revision 14/11/2024
                # add 'WDIAG' code
                # Revision 14/11/2024 >
                # Current iteration increment
                if sub in (' 2DIA', ' 1DIA', 'WDIAG'):
                    # '2DIA' if rigid/affine, '1DIA', 'WDIAG' if displacement Field
                    w = line.split(',')
                    if len(w) > 4:  # line contains convergence value
                        # < Revision 04/02/2026
                        try: progressit = int(w[1]) / self._multir[self._cstage][self._clevel]
                        except: progressit = 0.0
                        # Revision 04/02/2026 >
                        try: v = float(w[3])
                        except: continue
                        if isnan(v) or isinf(v): continue
                        else:
                            conv = self._conv[self._cstage]
                            try: progress = 1.0 - ((log10(float(w[3])) + conv) / conv)
                            except: continue
                            # < Revision 04/02/2026
                            if progressit > progress: progress = progressit
                            # Revision 04/02/2026 >
                            if progress > 1.0: progress = 1.0
                        progress = int(progress * self._progbylevel[self._cstage, self._clevel])
                        if self._clevel > 0: progress += int(self._progbylevel[self._cstage, :self._clevel].sum())
                        if progress > self.getCurrentProgressValue():
                            self.setCurrentProgressValue(progress)
                # < Revision 14/11/2024
                # add 'XDIAG' code
                # Revision 14/11/2024 >
                # Current multiresolution level increment
                elif sub in ('DIAGN', 'XXDIA', 'XDIAG'):
                    # 'DIAGN' if  rigid/affine, 'XXDIA', 'XDIAG' if displacement Field
                    if self._clevel is None: self._clevel = 0
                    else: self._clevel += 1
                    if self._clevel > nlevels - 1:
                        self._clevel = nlevels - 1
                    # < Revision 04/02/2026
                    # progress = int(self._progbylevel[self._cstage, self._clevel])
                    progress = int(self._progbylevel[self._cstage, :self._clevel].sum())
                    # Revision 04/02/2026 >
                    self.setCurrentProgressValue(progress)
                # Current stage increment
                elif sub == 'Stage':
                    w = line.split(' ')
                    if len(w) == 2:
                        # self._cstage = int(w[1][0]) - 1
                        if self._cstage is None: self._cstage = 0
                        else: self._cstage += 1
                        if self._cstage > self._nstages - 1:
                            self._cstage = self._nstages - 1
                        # < Revision 04/02/2026
                        self.setCurrentProgressValue(0)
                        self.setProgressRange(0, self._progbylevel[self._cstage].sum())
                        # self.setCurrentProgressValue(0)
                        # Revision 04/02/2026 >
                        self._clevel = None
                        nlevels = len(self._multir[self._cstage])
                        if self._multir[self._cstage][-1] == 1: nlevels -= 1
            # Update information field
            if self._cstage is not None and self._clevel is not None:
                if self._cstage != pstage or self._clevel != plevel:
                    info = '{} registration\nMultiresolution level {}/{}'.format(self._stages[self._cstage],
                                                                                 self._clevel + 1,
                                                                                 nlevels)
                    if not self.getButtonVisibility(): self.buttonVisibilityOn()
                    if not self.getProgressVisibility(): self.progressVisibilityOn()
                    self.setInformationText(info)

    def setNumberOfIterations(self, n):
        self.setProgressRange(0, n)
        self.setCurrentProgressValue(0)
        self._pos = 0
        self._time = None

    def setAntsAtroposProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            for line in verbose:
                line = line.lstrip()
                if len(line) > 0:
                    if line[0] == 'I':
                        if self._time is not None:
                            delta = datetime.now() - self._time
                            delta *= self.getProgressMaximum() - self.getCurrentProgressValue()
                            m = delta.seconds // 60
                            s = delta.seconds - (m * 60)
                            if m == 0: self.addInformationText('Estimated time remaining {} s.'.format(s))
                            else: self.addInformationText('Estimated time remaining {} min {} s.'.format(m, s))
                        self._time = datetime.now()
                        if not self.getButtonVisibility(): self.buttonVisibilityOn()
                        if not self.getProgressVisibility(): self.progressVisibilityOn()
                        self.incCurrentProgressValue()

    def setAntsCorticalThicknessProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            for line in verbose:
                line = line.lstrip()
                if len(line) > 0:
                    if line[:2] == 'It':
                        if self._time is not None:
                            delta = datetime.now() - self._time
                            delta *= self.getProgressMaximum() - self.getCurrentProgressValue()
                            # noinspection PyTypeChecker
                            m = delta.seconds // 60
                            s = delta.seconds - (m * 60)
                            if m == 0: self.addInformationText('Estimated time remaining {} s.'.format(s))
                            else: self.addInformationText('Estimated time remaining {} min {} s.'.format(m, s))
                        self._time = datetime.now()
                        if not self.getButtonVisibility(): self.buttonVisibilityOn()
                        if not self.getProgressVisibility(): self.progressVisibilityOn()
                        self.incCurrentProgressValue()

    # < Revision 03/06/2025
    # add setAntspynetTumorProgress method
    def setAntspynetTumorProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r', encoding='utf8', errors='ignore') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            for line in verbose:
                line = line.lstrip()
                if len(line) > 0:
                    ch = line[:7]
                    if ch == 'Brain e': self.setInformationText('Preprocessing: brain extraction...')
                    elif ch == 'Stage 1': self.setInformationText('Stage 1: U-net tumor segmentation...')
                    elif ch == 'Stage 2': self.setInformationText('Stage 2: U-net tumor clustering...')
                    elif ch == 'Predict':
                        try:
                            r = list(filter(lambda x: x != '', line.split(' ')))
                            if len(r) == 5:
                                if not self.getProgressVisibility():
                                    self.progressVisibilityOn()
                                self.setProgressMaximum(int(r[4]))
                                self.setCurrentProgressValue(int(r[2]))
                        except: pass
    # Revision 03/06/2025 >

    # < Revision 03/06/2025
    # add setAntspynetHippocamusProgress method
    def setAntspynetHippocamusProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r', encoding='utf8', errors='ignore') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            for line in verbose:
                line = line.lstrip()
                if len(line) > 0:
                    ch = line[:7]
                    if ch == 'Brain e': self.setInformationText('Preprocessing: brain extraction...')
                    elif ch == 'Running': self.setInformationText('Preprocessing: bias correction...')
                    elif ch == 'HippMap': self.setInformationText('Preprocessing: spatial normalization...')
                    elif ch == 'Monte C':
                        try:
                            r = line.split(' ')
                            if len(r) == 7:
                                if not self.getProgressVisibility():
                                    self.setInformationText('U-net hippocampus segmentation...')
                                    self.progressVisibilityOn()
                                self.setProgressMaximum(int(r[6]))
                                self.setCurrentProgressValue(int(r[3]))
                        except: pass
    # Revision 03/06/2025 >

    # < Revision 03/06/2025
    # add setAntspynetTemporalProgress method
    def setAntspynetTemporalProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r', encoding='utf8', errors='ignore') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            for line in verbose:
                line = line.lstrip()
                if len(line) > 0:
                    ch = line[:7]
                    if ch == 'Brain e': self.setInformationText('Preprocessing: brain extraction...')
                    elif ch == 'Running': self.setInformationText('Preprocessing: bias correction...')
                    elif ch == 'antsReg': self.setInformationText('Preprocessing: spatial normalization...')
                    elif ch == 'Predict':
                        if self._nstages == 0:
                            self.setInformationText('U-net left temporal segmentation...')
                            self._nstages = 1
                        else: self.setInformationText('U-net right temporal segmentation...')
    # Revision 03/06/2025 >

    # < Revision 03/06/2025
    # add setAntspynetLesionProgress method
    def setAntspynetLesionProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r', encoding='utf8', errors='ignore') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            for line in verbose:
                line = line.lstrip()
                if len(line) > 0:
                    ch = line[:7]
                    if ch == 'Brain e': self.setInformationText('Preprocessing: brain extraction...')
                    elif ch == 'Running': self.setInformationText('Preprocessing: bias correction...')
                    elif ch == 'antsReg': self.setInformationText('Preprocessing: spatial normalization...')
                    elif ch == 'Total e': self.setInformationText('U-net lesion segmentation...')
    # Revision 03/06/2025 >

    # < Revision 03/06/2025
    # add setAntspynetTemporalProgress method
    def setAntspynetVesselProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r', encoding='utf8', errors='ignore') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            for line in verbose:
                line = line.lstrip()
                if len(line) > 0:
                    ch = line[:7]
                    if ch == 'Brain e': self.setInformationText('Preprocessing: brain extraction...')
                    elif ch == 'antsReg': self.setInformationText('Preprocessing: spatial normalization...')
                    elif ch == 'Predict':
                        try:
                            r = list(filter(lambda x: x != '', line.split(' ')))
                            if len(r) == 5:
                                if not self.getProgressVisibility():
                                    self.progressVisibilityOn()
                                self.setProgressMaximum(int(r[4]))
                                self.setCurrentProgressValue(int(r[2]))
                        except: pass
    # Revision 03/06/2025 >

    # < Revision 03/06/2025
    # add setAntspynetTemporalProgress method
    def setAntspynetTissueProgress(self, stdout):
        lock = Lock()
        with lock:
            with open(stdout, 'r', encoding='utf8', errors='ignore') as f:
                f.seek(self._pos)
                verbose = f.readlines()
                self._pos = f.tell()
        if len(verbose) > 0:
            for line in verbose:
                line = line.lstrip()
                if len(line) > 0:
                    ch = line[:7]
                    if ch == 'Brain e': self.setInformationText('Preprocessing: brain extraction...')
                    elif ch == 'antsReg': self.setInformationText('Preprocessing: spatial normalization...')
                    elif ch == 'antsReg': self.setInformationText('Preprocessing: spatial normalization...')
                    elif ch == 'Running': self.setInformationText('Preprocessing: bias correction...')
                    elif ch == 'DeepAtr': self.setInformationText('Tissue segmentation...')
    # Revision 03/06/2025 >
