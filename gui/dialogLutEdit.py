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

from Sisyphe.widgets.LUTWidgets import LutEditWidget

__all__ = ['DialogLutEdit']

"""
Class hierarchy
~~~~~~~~~~~~~~~
    
    - QDialog -> DialogLutEdit
"""


class DialogLutEdit(QDialog):
    """
    DialogLutEdit class

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogLutEdit
    """

    # Special method

    """
    Private attributes

    _lutwidget  LutEditWidget    
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Edit Lut')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setSizeGripEnabled(False)

        self._lutwidget = LutEditWidget()
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
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addWidget(save)
        layout.addStretch()

        self._layout.addWidget(self._lutwidget)
        self._layout.addLayout(layout)

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        save.clicked.connect(self._lutwidget.save)

    # Public method

    def getLut(self):
        return self._lutwidget.getSisypheLut()
