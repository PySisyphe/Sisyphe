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
from PyQt5.QtWidgets import QApplication

from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.widgets.dicomWidgets import XmlDicomTreeViewWidget

__all__ = ['DialogXmlDicom']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog ->  DialogXmlDicom
"""


class DialogXmlDicom(QDialog):
    """
    DialogXmlDicom

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogXmlDicom
    """

    # Special method

    """
    Private attributes

    _dcm        XmlDicomTreeViewWidget
    _check      QPushButton
    _uncheck    QPushButton
    _save       MenuPushButton
    """

    def __init__(self, filename, parent=None):
        super().__init__(parent)

        self.setWindowTitle('DICOM dataset')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.75))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._dcm = XmlDicomTreeViewWidget()
        self._dcm.loadXmlDicom(filename)
        self._layout.addWidget(self._dcm)

        self._checkall = QPushButton('Check all')
        self._uncheckall = QPushButton('Uncheck all')
        self._checksel = QPushButton('Check selected')
        self._unchecksel = QPushButton('Uncheck selected')
        self._save = MenuPushButton('Save')
        self._checkall.adjustSize()
        self._uncheckall.adjustSize()
        self._checksel.adjustSize()
        self._unchecksel.adjustSize()
        self._save.setFixedWidth(60)
        self._action = dict()
        self._action['xml'] = self._save.addAction('Save Xml (*.xsheet)')
        self._action['txt'] = self._save.addAction('Save Text (*.txt)')
        self._action['csv'] = self._save.addAction('Save to CSV (*.csv)')
        self._action['xls'] = self._save.addAction('Save Excel (*.xlsx)')
        self._action['mat'] = self._save.addAction('Save Matfile (*.mat)')
        self._action['tex'] = self._save.addAction('Save Latex (*.tex)')
        self._action['clp'] = self._save.addAction('Copy to clipboard')
        # noinspection PyUnresolvedReferences
        self._action['xml'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToXml())
        # noinspection PyUnresolvedReferences
        self._action['txt'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToTxt())
        # noinspection PyUnresolvedReferences
        self._action['csv'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToCSV())
        # noinspection PyUnresolvedReferences
        self._action['xls'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToExcel())
        # noinspection PyUnresolvedReferences
        self._action['mat'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToMatfile())
        # noinspection PyUnresolvedReferences
        self._action['tex'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToLATEX())
        # noinspection PyUnresolvedReferences
        self._action['clp'].triggered.connect(lambda: self._dcm.copyCheckedDataElementsToClipboard())
        self._checkall.setToolTip('Check all DataElements.')
        self._uncheckall.setToolTip('Uncheck all DataElements.')
        self._checksel.setToolTip('Check selected DataElements.')
        self._unchecksel.setToolTip('Uncheck selected DataElements.')
        self._save.setToolTip('Save checked DataElements.')
        # noinspection PyUnresolvedReferences
        self._checkall.clicked.connect(lambda: self._dcm.checkAll())
        # noinspection PyUnresolvedReferences
        self._uncheckall.clicked.connect(lambda: self._dcm.uncheckAll())
        # noinspection PyUnresolvedReferences
        self._checksel.clicked.connect(lambda: self._dcm.checkSelected())
        # noinspection PyUnresolvedReferences
        self._unchecksel.clicked.connect(lambda: self._dcm.uncheckSelected())

        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.addWidget(self._checkall)
        layout.addWidget(self._uncheckall)
        layout.addWidget(self._checksel)
        layout.addWidget(self._unchecksel)
        layout.addWidget(self._save)
        layout.addStretch()
        layout.addWidget(ok)
        self._layout.addLayout(layout)

        self.setModal(True)
