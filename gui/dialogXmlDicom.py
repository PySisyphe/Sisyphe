"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import getcwd
from os.path import join
from os.path import exists
from os.path import splitext
from os.path import basename

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.widgets.basicWidgets import MenuPushButton
from Sisyphe.widgets.dicomWidgets import XmlDicomTreeViewWidget


"""
    Class hierarchy

       QDialog ->  DialogXmlDicom
"""


class DialogXmlDicom(QDialog):
    """
        DialogXmlDicom

        Inheritance

            QDialog -> DialogXmlDicom

        Private attributes

            _dcm        XmlDicomTreeViewWidget
            _check      QPushButton
            _uncheck    QPushButton
            _save       MenuPushButton

        Public methods

            inherited QDialog methods
    """

    # Special method

    def __init__(self, filename, parent=None):
        super().__init__(parent)

        self.setWindowTitle('DICOM dataset')

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
        self._action['xml'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToXml())
        self._action['txt'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToTxt())
        self._action['csv'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToCSV())
        self._action['xls'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToExcel())
        self._action['mat'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToMatfile())
        self._action['tex'].triggered.connect(lambda: self._dcm.saveCheckedDataElementsToLATEX())
        self._action['clp'].triggered.connect(lambda: self._dcm.copyCheckedDataElementsToClipboard())
        self._checkall.setToolTip('Check all DataElements.')
        self._uncheckall.setToolTip('Uncheck all DataElements.')
        self._checksel.setToolTip('Check selected DataElements.')
        self._unchecksel.setToolTip('Uncheck selected DataElements.')
        self._save.setToolTip('Save checked DataElements.')
        self._checkall.clicked.connect(lambda: self._dcm.checkAll())
        self._uncheckall.clicked.connect(lambda: self._dcm.uncheckAll())
        self._checksel.clicked.connect(lambda: self._dcm.checkSelected())
        self._unchecksel.clicked.connect(lambda: self._dcm.uncheckSelected())

        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        ok.clicked.connect(self.accept)

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(self._checkall)
        layout.addWidget(self._uncheckall)
        layout.addWidget(self._checksel)
        layout.addWidget(self._unchecksel)
        layout.addWidget(self._save)
        layout.addStretch()
        layout.addWidget(ok)
        self._layout.addLayout(layout)

        # Window

        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.75))
        self.setModal(True)


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    main = DialogXmlDicom('/Users/jean-albert/PycharmProjects/python310Project/TESTS/DCM/RTSTRUCT/test.xdcm')
    main.show()
    app.exec_()
