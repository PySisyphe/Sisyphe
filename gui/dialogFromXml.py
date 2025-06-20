"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSizePolicy

from Sisyphe.widgets.functionsSettingsWidget import DialogSettingsWidget

__all__ = ['DialogFromXml']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogFromXml
"""

class DialogFromXml(QDialog):
    """
    DialogFromXml class

    Description
    ~~~~~~~~~~~

    GUI dialog window generated from xml file (Sisyphe.settings.__file__/dialogs.xml).

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogFromXml

    Last revision: 30/03/2025
    """

    # Special method

    """
    Private attributes

    _fields     list[DialogSettingsWidget]
    _names      list[str], dialog names
    """

    def __init__(self, title, names, parent=None):
        super().__init__(parent)

        if isinstance(names, str): names = [names]

        self.setWindowTitle('{}'.format(title))
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self._names = names

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._fields = list()

        if len(names) == 1:
            self._fields.append(DialogSettingsWidget(names[0], parent=self))
            self._fields[0].setButtonsVisibility(False)
            self._layout.addWidget(self._fields[0])
        else:
            for i in range(len(names)):
                group = QGroupBox()
                group.setTitle(DialogSettingsWidget.formatLabel(names[i]))
                lyout = QHBoxLayout()
                self._fields.append(DialogSettingsWidget(names[i], parent=self))
                self._fields[i].setButtonsVisibility(False)
                lyout.addWidget(self._fields[i])
                group.setLayout(lyout)
                self._layout.addWidget(group)
                self._layout.addSpacing(5)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        self._cancel = QPushButton('Cancel')
        layout.addWidget(self._ok)
        layout.addWidget(self._cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._cancel.clicked.connect(self.reject)

    # Public methods

    def getFieldsWidget(self, index=0):
        if isinstance(index, int):
            if 0 <= index < len(self._fields): return self._fields[index]
            else: raise ValueError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def getFieldsDict(self, index=0):
        if isinstance(index, int):
            if 0 <= index < len(self._fields): return self._fields[index].getParametersDict()
            else: raise ValueError('parameter is out of range.')
        else: raise TypeError('parameter type {} is not int.'.format(type(index)))

    def setAcceptButtonText(self, txt):
        self._ok.setText(txt)

    def getAcceptButtonText(self):
        return self._ok.text()

    def getAcceptButton(self):
        return self._ok

    def getLayout(self):
        return self._layout
