"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import splitext
from os.path import basename

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QPushButton

from Sisyphe.core.sisypheImageAttributes import SisypheIdentity
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.basicWidgets import messageBox

__all__ = ['DialogPatient']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogPatient
"""


class DialogPatient(QDialog):
    """
    DialogPatient class

    Inheritance
    ~~~~~~~~~~~

    QWidget -> QDialog -> DialogPatient
    """

    def __init__(self, parent=None, identity=None):
        super().__init__(parent)

        self.setWindowTitle('Edit patient')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setSizeGripEnabled(False)
        self.setAcceptDrops(True)

        if isinstance(identity, SisypheVolume):
            # noinspection PyArgumentList
            self._identity = SisypheVolume.getIdentity()
        elif isinstance(identity, SisypheIdentity): self._identity = identity
        else: self._identity = SisypheIdentity()

        # Init Attributes widgets
        # Lastname
        self._lastname = QLineEdit(self)
        self._lastname.setText(self._identity.getLastname())
        self._lastname.setFixedWidth(200)
        # noinspection PyUnresolvedReferences
        self._lastname.editingFinished.connect(self._title)
        # Firstname
        self._firstname = QLineEdit(self)
        self._firstname.setText(self._identity.getFirstname())
        self._firstname.setFixedWidth(200)
        # noinspection PyUnresolvedReferences
        self._firstname.editingFinished.connect(self._title)
        # Date of Birthday
        self._dob = QDateEdit(self)
        self._dob.setDate(self._identity.getDateOfBirthday(string=False))
        self._dob.setFixedWidth(200)
        self._dob.setCalendarPopup(True)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

        # Init QGripLayout

        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 5, 0)
        # Identity fields
        # noinspection PyTypeChecker
        layout.addWidget(QLabel('Lastname'), 1, 0, alignment=Qt.AlignRight)
        # noinspection PyTypeChecker
        layout.addWidget(self._lastname, 1, 1, alignment=Qt.AlignLeft)
        # noinspection PyTypeChecker
        layout.addWidget(QLabel('Firstname'), 2, 0, alignment=Qt.AlignRight)
        # noinspection PyTypeChecker
        layout.addWidget(self._firstname, 2, 1, alignment=Qt.AlignLeft)
        # noinspection PyTypeChecker
        layout.addWidget(QLabel('Date of birth'), 4, 0, alignment=Qt.AlignRight)
        # noinspection PyTypeChecker
        layout.addWidget(self._dob, 4, 1, alignment=Qt.AlignLeft)
        self._layout.addLayout(layout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        else: layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        cancel.setFixedWidth(100)
        ok = QPushButton('Ok')
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
        cancel.clicked.connect(self.reject)

    # Private method

    def _update(self):
        self._identity.setLastname(self._lastname.text())
        self._identity.setFirstname(self._firstname.text())
        # noinspection PyTypeChecker
        self._identity.setDateOfBirthday(self._dob.date().toString(Qt.ISODate))

    def _title(self):
        self._lastname.setText(self._lastname.text().capitalize())
        self._firstname.setText(self._firstname.text().capitalize())

    # Public methods

    def setIdentity(self, identity):
        if isinstance(identity, SisypheVolume):
            identity = identity.getIdentity()
        if isinstance(identity, SisypheIdentity):
            self._identity = identity
            self._lastname.setText(self._identity.getLastname())
            self._firstname.setText(self._identity.getFirstname())
            self._dob.setDate(self._identity.getDateOfBirthday(string=False))

    def getIdentity(self):
        self._update()
        return self._identity

    def getTupleIdentity(self):
        self._update()
        return (self._identity.getLastname(),
                self._identity.getFirstname(),
                self._identity.getDateOfBirthday())

    def getLastname(self):
        self._update()
        return self._identity.getLastname()

    def getFirstname(self):
        self._update()
        return self._identity.getFirstname()

    def getDateOfBirth(self):
        self._update()
        return self._identity.getDateOfBirthday()

    # QEvents

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            files = event.mimeData().text().split('\n')
            for file in files:
                if file != '':
                    filename = file.replace('file://', '')
                    if splitext(filename)[1] == SisypheVolume.getFileExt():
                        vol = SisypheVolume()
                        try: vol.load(filename)
                        except: messageBox(self,
                                           'Edit patient',
                                           text='{} read error.'.format(basename(filename)))
                        self.setIdentity(vol)
        else: event.ignore()
