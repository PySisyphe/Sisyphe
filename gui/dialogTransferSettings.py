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

from Sisyphe.widgets.LUTWidgets import TransferWidget
from Sisyphe.core.sisypheVolume import SisypheVolume

__all__ = ['DialogTransferSettings']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogTransferSettings
"""

class DialogTransferSettings(QDialog):
    """
    DialogTransferSettings class

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogTransferSettings
    """

    # Special method

    """
    Private attributes

    _lutwidget  LutWidget
    """
    def __init__(self, volume=None, transfer=None, gradient=True, size=256, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Transfer Settings')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setSizeGripEnabled(False)

        self._transferwidget = TransferWidget(volume=volume, transfer=transfer, gradient=gradient, size=size)
        self._transferwidget.setContentsMargins(5, 5, 5, 5)

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
        load = QPushButton('Load')
        load.setFixedWidth(75)
        save = QPushButton('Save')
        save.setFixedWidth(75)
        ok = QPushButton('OK')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addWidget(save)
        layout.addWidget(load)
        layout.addStretch()

        self._layout.addWidget(self._transferwidget)
        self._layout.addLayout(layout)

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        load.clicked.connect(self._transferwidget.load)
        # noinspection PyUnresolvedReferences
        save.clicked.connect(self._transferwidget.save)

    # Public method

    def setVolume(self, v):
        if isinstance(v, SisypheVolume):
            self._transferwidget.setVolume(v)
        else:
            raise TypeError('parameter type {} is not SisypheVolume.'.format(type(v)))
