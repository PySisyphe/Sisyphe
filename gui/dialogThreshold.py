"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton

from Sisyphe.core.sisypheVolume import SisypheVolume
# from Sisyphe.widgets.thresholdWidgets import ThresholdWidget
# from Sisyphe.widgets.thresholdWidgets import GradientThresholdWidget
from Sisyphe.widgets.thresholdWidgets import ThresholdViewWidget
from Sisyphe.widgets.thresholdWidgets import GradientThresholdViewWidget

"""
    Class

        DialogThreshold
"""


class DialogThreshold(QDialog):
    """
        DialogThreshold class

        Inheritance

            QWidget -> QDialog -> DialogThreshold

        Private attributes

            _volume     SisypheVolume
            _size       int, tool size

        Public methods

            SisypheVolume = getVolume()
            setVolume(SisypheVolume)
            int = getSize()
            setSize(int)
            int or (int, int)= getThresholds()
            setThresholdFlagToMinimum()
            setThresholdFlagToMaximum()
            setThresholdFlagToTwo()
            setThresholdFlagButtonsVisibility(bool)
            getThresholdFlagButtonsVisibility()

            inherited QDialog methods
            inherited QWidget methods

        Revisions:

            25/07/2023  setVolume() bugfix
            15/08/2023  replace ThresholdWidget with ThresholdViewWidget
                        in _initWidget() and setVolume() methods
    """

    # Special method

    def __init__(self, vol=None, size=256, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Set threshold')

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
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self._reject)

    # Private methods

    def _initWidget(self, vol, size=256):
        return ThresholdViewWidget(vol, size=size, parent=self)
        #  return ThresholdWidget(vol, size=size, parent=self)

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
            # self._threshold = ThresholdWidget(vol, size=self._size, parent=self)
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
            self._threshold = ThresholdWidget(self._vol, size=self._size, parent=self)

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


class DialogGradientThreshold(DialogThreshold):
    """
        DialogGradientThreshold class

        Inheritance

            QWidget -> QDialog -> DialogThreshold -> DialogGradientThreshold

        Private attributes

        Public methods

            inherited DialogThreshold methods
            inherited QDialog methods
            inherited QWidget methods

        Revision:

            15/08/2023  replace GradientThresholdWidget with GradientThresholdViewWidget
                        in _initWidget() and setVolume() methods
    """

    def __init__(self, vol=None, size=256, parent=None):
        super().__init__(vol, size, parent)

    def _initWidget(self, vol, size=256):
        return GradientThresholdViewWidget(vol, size=size, parent=self)
        # return GradientThresholdWidget(vol, size=size, parent=self)

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


if __name__ == '__main__':

    from sys import argv
    from PyQt5.QtWidgets import QApplication

    test = 0
    app = QApplication(argv)
    filename = '/Users/Jean-Albert/PycharmProjects/untitled/TESTS/IMAGES/NIFTI/STEREO3D.nii'
    img = SisypheVolume()
    img.loadFromNIFTI(filename)
    img.display.getLUT().setDefaultLut()
    if test == 0:
        main = DialogThreshold(img, size=256)
    else:
        main = DialogGradientThreshold(img, size=256)
    main.setThresholdFlagToMinimum()
    main.setThresholdFlagButtonsVisibility(False)
    main.show()
    app.exec_()
