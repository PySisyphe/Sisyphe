"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton

from Sisyphe.widgets.LUTWidgets import LutWidget
from Sisyphe.core.sisypheVolume import SisypheVolume

__all__ = ['DialogLutSettings']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    QDialog -> DialogLutSettings
"""


class DialogLutSettings(QDialog):
    """
    DialogLutSettings class

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogLutSettings
    """

    # Special method

    """
    Private attributes

    _lutwidget  LutWidget    
    """

    def __init__(self, volume=None, size=256, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Lut Settings')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setSizeGripEnabled(False)
        self._lutwidget = LutWidget(volume=volume, size=size)
        self._lutwidget.setContentsMargins(5, 5, 5, 5)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        save = QPushButton('Save')
        save.setFixedWidth(100)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addStretch()

        self._layout.addWidget(self._lutwidget)
        self._layout.addLayout(layout)

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)

    # Public method

    def setVolume(self, v):
        if isinstance(v, SisypheVolume):
            self._lutwidget.setVolume(v)
        else:
            raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))
