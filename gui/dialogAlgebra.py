"""
    External packages/modules

        Name            Link                                                        Usage

        Numpy           https://numpy.org/                                          Scientific computing
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import chdir
from os.path import dirname

from numpy import *

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import LabeledLineEdit
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

"""
    Class hierarchy

        QDialog -> DialogAlgebra
"""


class DialogAlgebra(QDialog):
    """
        DialogAlgebra

        Description

            GUI dialog window for voxel by voxel algebraic calculation

        Inheritance

            QDialog -> DialogAlgebra

        Private attributes

            _files      FilesSelectionWidget
            _formula    LabeledLineEdit

        Public methods

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Voxel by voxel algebraic calculation')
        self.resize(QSize(600, 500))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Files selection widgets

        self._files = FilesSelectionWidget()
        self._files.filterSisypheVolume()
        self._files.filterSameSize()
        self._files.setCurrentVolumeButtonVisibility(False)
        self._files.FilesSelectionWidgetDoubleClicked.connect(self._addVolumeToFormula)
        self._layout.addWidget(self._files)

        # Formula edit widget

        self._formula = LabeledLineEdit()
        self._formula.setLabelText('Formula')
        self._formula.setToolTip('All functions and operators of the Numpy library can be used in formula.\n'
                                 'Double-click on filename adds volume to the formula.')
        self._layout.addWidget(self._formula)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute formula.')
        lyout.addWidget(ok)
        lyout.addWidget(self._execute)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Qt Signals

        ok.clicked.connect(self.accept)
        self._execute.clicked.connect(self.execute)

    # Private method

    def _addVolumeToFormula(self, v):
        if isinstance(v, QListWidgetItem):
            edit = self._formula.getQLineEdit()
            f = self._formula.getEditText()
            i = edit.cursorPosition()
            idx = self._files.getIndexFromItem(v)
            f = f[:i] + ' img[{}] '.format(idx) + f[i:]
            self._formula.setEditText(f)
        else: raise TypeError('parameter type {} is not str.'.format(type(v)))

    # Public methods

    def execute(self):
        title = 'Voxel by voxel algebraic calculation'
        f = self._formula.getEditText()
        if f != '' and self._files.filenamesCount() > 0:
            wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                              progresstxt=False, anim=False, cancel=False, parent=self)
            wait.setInformationText(title)
            wait.open()
            QApplication.processEvents()
            try:
                img = list()
                filenames = self._files.getFilenames()
                for filename in filenames:
                    v = SisypheVolume()
                    v.load(filename)
                    img.append(v.copyToNumpyArray())
                f = 'r = ' + f
                exec(f)
                result = locals()['r']
                m = SisypheVolume()
                m.copyFromNumpyArray(result, spacing=v.getSpacing())
                m.copyAttributesFrom(v, display=False)
                m.setFilename(filenames[0])
                m.setFilenamePrefix('Algebra')
                wait.hide()
                filename = QFileDialog.getSaveFileName(self, title, m.getFilename(),
                                                       filter='PySisyphe volume (*.xvol)')[0]
                if filename:
                    chdir(dirname(filename))
                    m.updateArrayID()
                    m.saveAs(filename)
                self._formula.setEditText('')
            except Exception as err:
                wait.hide()
                QMessageBox.warning(self, title, 'Formula error.\n{}'.format(err))
            wait.close()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv, exit

    app = QApplication(argv)
    main = DialogAlgebra()
    main.show()
    app.exec_()
    exit()
