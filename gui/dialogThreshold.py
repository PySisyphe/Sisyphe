"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.thresholdWidgets import ThresholdViewWidget
from Sisyphe.widgets.thresholdWidgets import GradientThresholdViewWidget

__all__ = ['DialogThreshold',
           'DialogGradientThreshold']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    QDialog -> DialogThreshold -> DialogGradientThreshold
"""


class DialogThreshold(QDialog):
    """
    DialogThreshold class

    Inheritance
    ~~~~~~~~~~~

    QWidget -> QDialog -> DialogThreshold

    Last revision: 15/08/2023
    """

    # Special method

    """
    Private attributes

    _volume     SisypheVolume
    _size       int, tool size
    """

    def __init__(self, vol=None, size=256, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Set threshold')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setSizeGripEnabled(False)

        if isinstance(vol, SisypheVolume): self._vol = vol
        else: self._vol = None
        self._size = size

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

        # Init widgets

        if self._vol:
            self._threshold = self._initWidget(self._vol, self._size)
            self._layout.addWidget(self._threshold)
        else: self._threshold = None

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addWidget(cancel)
        layout.addStretch()
        self._layout.addLayout(layout)
        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self._reject)

    # Private methods

    def _initWidget(self, vol, size=256):
        return ThresholdViewWidget(vol, size=size, parent=self)

    def _reject(self):
        self._threshold.setThreshold(self._vol.display.getRangeMin(),
                                     self._vol.display.getRangeMax())
        self.reject()

    # Public methods

    def getVolume(self):
        return self._vol

    def setVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            self._vol = vol
            if self._threshold is not None:
                self._layout.removeWidget(self._threshold)
                del self._threshold
            self._threshold = ThresholdViewWidget(vol, size=self._size, parent=self)
            self._layout.insertWidget(0, self._threshold)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))

    def getViewWidget(self):
        if self._threshold is not None: return self._threshold.getViewWidget()
        else: return None

    def getSize(self):
        return self._size

    def setSize(self, size):
        if isinstance(size, int):
            if size < 256: size = 256
            self._size = size
            del self._threshold
            self._threshold = ThresholdViewWidget(self._vol, size=self._size, parent=self)

    def getThreshold(self):
        flag = self._threshold.getThresholdFlag()
        if flag == 0: return self._threshold.getMinThreshold()
        elif flag == 1: return self._threshold.getMaxThreshold()
        else: return self._threshold.getThreshold()

    def setThresholdFlagToMinimum(self):
        self._threshold.setThresholdFlagToMinimum()

    def setThresholdFlagToMaximum(self):
        self._threshold.setThresholdFlagToMaximum()

    def setThresholdFlagToTwo(self):
        self._threshold.setThresholdFlagToTwo()

    def setThresholdFlagButtonsVisibility(self, v):
        if isinstance(v, bool): self._threshold.setThresholdFlagButtonsVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getThresholdFlagButtonsVisibility(self):
        self._threshold.getThresholdFlagButtonsVisibility()

    # Qt events

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        super().closeEvent(a0)
        # < Revision 10/03/2025
        # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
        if platform == 'win32':
            if self._threshold is not None:
                self._threshold.finalize()
        # Revision 10/03/2025 >

class DialogGradientThreshold(DialogThreshold):
    """
    DialogGradientThreshold class

    Inheritance
    ~~~~~~~~~~~

    QWidget -> QDialog -> DialogThreshold -> DialogGradientThreshold

    Last revision: 15/08/2023
    """

    def __init__(self, vol=None, size=256, parent=None):
        super().__init__(vol, size, parent)

    # Private method

    def _initWidget(self, vol, size=256):
        return GradientThresholdViewWidget(vol, size=size, parent=self)
        # return GradientThresholdWidget(vol, size=size, parent=self)

    # Public method

    def setVolume(self, vol):
        if isinstance(vol, SisypheVolume):
            self._vol = vol
            if self._threshold is not None:
                self._layout.removeWidget(self._threshold)
                del self._threshold
            self._threshold = GradientThresholdViewWidget(vol, size=self._size, parent=self)
            # self._threshold = GradientThresholdWidget(vol, size=self._size, parent=self)
            self._layout.addWidget(self._threshold)
        else: raise TypeError('parameter type {} is not SisypheVolume.'.format(type(vol)))
