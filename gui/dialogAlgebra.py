"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import chdir

from os.path import dirname
from os.path import abspath

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QApplication

from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import LabeledLineEdit
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

__all__ = ['DialogAlgebra']

"""
Class hierarchy
~~~~~~~~~~~~~~~

QDialog -> DialogAlgebra
"""


class DialogAlgebra(QDialog):
    """
    DialogAlgebra

    Description
    ~~~~~~~~~~~

    GUI dialog window for voxel by voxel algebraic calculation.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogAlgebra

    Last revision: 10/11/2024
    """

    # Special method

    """
    Private attributes

    _files      FilesSelectionWidget
    _formula    LabeledLineEdit
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Voxel by voxel algebraic calculation')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Files selection widgets

        self._files = FilesSelectionWidget(parent=self)
        self._files.filterSisypheVolume()
        self._files.filterSameSize()
        self._files.setCurrentVolumeButtonVisibility(False)
        self._files.FilesSelectionWidgetDoubleClicked.connect(self._addVolumeToFormula)
        self._layout.addWidget(self._files)

        # Formula edit widget

        self._formula = LabeledLineEdit()
        # noinspection PyTypeChecker
        self._formula.setFocusPolicy(Qt.StrongFocus)
        self._formula.setLabelText('Formula')
        self._formula.setToolTip('All functions and operators of the Numpy library can be used in formula.\n'
                                 'All Numpy functions must be prefixed with \'np.\' (numpy is imported with the alias np)\n'
                                 'Volume number i is inserted into the formula using a list variable named img: img[i].\n'
                                 'or double-click on the filename to add the volume to the formula.')
        self._layout.addWidget(self._formula)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
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

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        self.setModal(True)

    # Private method

    def _addVolumeToFormula(self, v):
        if isinstance(v, QListWidgetItem):
            edit = self._formula.getQLineEdit()
            f = self._formula.getEditText()
            i = edit.cursorPosition()
            idx = self._files.getIndexFromItem(v)
            f = f[:i] + ' img[{}] '.format(idx) + f[i:]
            self._formula.setEditText(f)
            # noinspection PyTypeChecker
            self._formula.setFocus(Qt.OtherFocusReason)
        else: raise TypeError('parameter type {} is not str.'.format(type(v)))

    # Public methods

    def getFilesSelectionWidget(self):
        return self._files

    def execute(self):
        title = 'Voxel by voxel algebraic calculation'
        f = self._formula.getEditText()
        if f != '' and self._files.filenamesCount() > 0:
            wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                              progresstxt=False, cancel=False)
            wait.open()
            wait.setInformationText(title)
            QApplication.processEvents()
            try:
                img = list()
                filenames = self._files.getFilenames()
                for filename in filenames:
                    v = SisypheVolume()
                    v.load(filename)
                    img.append(v.copyToNumpyArray())
                # < Revision 10/11/2024
                # add numpy import
                # f = 'r = ' + f
                f = 'import numpy as np\nr = ' + f
                # Revision 10/11/2024 >
                exec(f)
                result = locals()['r']
                m = SisypheVolume()
                # noinspection PyUnboundLocalVariable
                m.copyFromNumpyArray(result, spacing=v.getSpacing())
                m.copyAttributesFrom(v, display=False)
                m.setFilename(filenames[0])
                m.setFilenamePrefix('Algebra')
                wait.hide()
                filename = QFileDialog.getSaveFileName(self, title, m.getFilename(),
                                                       filter='PySisyphe volume (*.xvol)')[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    m.updateArrayID()
                    m.saveAs(filename)
                # < Revision 22/05/2025
                # self._formula.setEditText('')
                # Revision 22/05/2025 >
            except Exception as err:
                wait.hide()
                messageBox(self, title, 'Formula error.\n{}'.format(err))
            wait.close()
