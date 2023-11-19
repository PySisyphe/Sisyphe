"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os.path import basename

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheConstants import getDatatypes
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget


"""
    Class hierarchy
    
        QDialog -> DialogDatatype
"""


class DialogDatatype(QDialog):
    """
        DialogDatatype

        Description

            GUI dialog window for datatype conversion

        Inheritance

            QDialog -> DialogDatatype

        Private attributes

            _files      FilesSelectionWidget
            _datatype   LabeledComboBox

        Public methods

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Datatype conversion')
        self.resize(QSize(600, 500))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Files selection widgets

        self._files = FilesSelectionWidget()
        self._files.filterSisypheVolume()
        self._files.setCurrentVolumeButtonVisibility(False)
        self._layout.addWidget(self._files)

        # Datatype selection widget

        lyout = QHBoxLayout()
        self._datatype = LabeledComboBox()
        self._datatype.setFixedWidth(200)
        self._datatype.setTitle('Datatype')
        self._datatype.addItems(getDatatypes())
        lyout.addStretch()
        lyout.addWidget(self._datatype)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        self._execute = QPushButton('Convert')
        self._execute.setToolTip('Execute datatype conversion.')
        lyout.addWidget(ok)
        lyout.addWidget(self._execute)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Qt Signals

        ok.clicked.connect(self.accept)
        self._execute.clicked.connect(self.execute)

    # Public methods

    def execute(self):
        n = self._files.filenamesCount()
        if n > 0:
            title = 'Datatype conversion'
            wait = DialogWait(title=title, progress=True, progressmin=0, progressmax=n,
                              progresstxt=True, anim=False, cancel=False, parent=self)
            wait.open()
            dtype = self._datatype.currentText()
            for filename in self._files.getFilenames():
                wait.setInformationText('Convert {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                v = SisypheVolume()
                try:
                    v.load(filename)
                    if v.getDatatype() != dtype:
                        v2 = v.cast(dtype)
                        v2.setFilename(v.getFilename())
                        v2.setFilenameSuffix(dtype)
                        v2.save()
                except Exception as err:
                    QMessageBox.warning(self, title, '{}'.format(err))
            wait.close()
            self._files.clearall()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit

    app = QApplication(argv)
    main = DialogDatatype()
    main.show()
    app.exec_()
    exit()
