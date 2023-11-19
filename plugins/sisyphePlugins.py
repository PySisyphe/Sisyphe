"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import mkdir
from os.path import join
from os.path import dirname
from os.path import abspath
from os.path import exists
from os.path import expanduser

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton

from Sisyphe.gui.windowSisyphe import WindowSisyphe

__all__ = ['SisyphePlugins']

"""
    Class hierarchy

        QDialog -> SisyphePlugins
"""

class SisyphePlugins(QDialog):
    """
        SisyphePlugins

        Description

            Abstract ancestor class of plugins classes

        Inheritance

            QDialog -> SisyphePlugins

        Private attributes

            _main   WindowSisyphe

        Public methods

            str = getMainDirectory()
            str = getUserDirectory()
            str = getName()
            WindowSisyphe = getMainWindow()
            QLayout = getButtonsLayout()
            setAcceptButtonVisibility(bool)
            acceptButtonVisibilityOn()
            acceptButtonVisibilityOff()
            bool = getAcceptButtonVisibility()
            setCancelButtonVisibility(bool)
            cancelButtonVisibilityOn()
            cancelButtonVisibilityOff()
            bool = getCancelButtonVisibility()
    """

    # class methods

    @classmethod
    def getMainDirectory(cls):
        import Sisyphe
        return dirname(abspath(Sisyphe.__file__))

    @classmethod
    def getUserDirectory(cls):
        userdir = join(expanduser('~'), '.PySisyphe')
        if not exists(userdir): mkdir(userdir)
        return userdir

    # Special method

    def __init__(self, name=None, mainwindow=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(name)
        if mainwindow is not None and isinstance(mainwindow, WindowSisyphe): self._main = mainwindow
        else: raise TypeError('main window parameter type {} is not WindowSisyphe.'.format(type(mainwindow)))

        # Init QLayout

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Init default dialog buttons

        self._layout = QHBoxLayout()
        self._layout.setSpacing(10)
        self._layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._cancel = QPushButton('cancel')
        self._cancel.setFixedWidth(100)
        self._layout.addWidget(self._ok)
        self._layout.addWidget(self._cancel)
        self._layout.addStretch()

        layout.addLayout(self._layout)

        # Qt Signals

        self._ok.clicked.connect(self.accept)
        self._cancel.clicked.connect(self.reject)

    # Public methods

    def getName(self):
        return self.windowTitle()

    def getSisypheWindow(self):
        return self._main

    def getButtonsLayout(self):
        return self._layout

    def setAcceptButtonVisibility(self, v):
        if isinstance(v, bool): self._ok.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def acceptButtonVisibilityOn(self):
        self._ok.setVisible(True)

    def acceptButtonVisibilityOff(self):
        self._ok.setVisible(False)

    def getAcceptButtonVisibility(self):
        return self._ok.isVisible()

    def setCancelButtonVisibility(self, v):
        if isinstance(v, bool):
            self._cancel.setVisible(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def cancelButtonVisibilityOn(self):
        self._cancel.setVisible(True)

    def cancelButtonVisibilityOff(self):
        self._cancel.setVisible(False)

    def getCancelButtonVisibility(self):
        return self._cancel.isVisible()



