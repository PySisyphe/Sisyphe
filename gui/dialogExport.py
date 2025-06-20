"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import join
from os.path import basename
from os.path import splitext

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheConstants import getNiftiExt
from Sisyphe.core.sisypheConstants import getMincExt
from Sisyphe.core.sisypheConstants import getNrrdExt
from Sisyphe.core.sisypheConstants import getVtkExt
from Sisyphe.core.sisypheConstants import getNumpyExt
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

__all__ = ['DialogExport']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogExport
"""


class DialogExport(QDialog):
    """
    DialogExport

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogExport
    """

    # Special method

    """
    Private attributes

    _ioformat   str, export format (nifti, minc, nrrd, vtk, npy)
    """

    def __init__(self, io='Nifti', parent=None):
        super().__init__(parent)

        self._ioformat = io
        self.setWindowTitle('{} export'.format(io))
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self.setSizeGripEnabled(False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = FilesSelectionWidget()
        self._files.filterSisypheVolume()
        self._layout.addWidget(self._files)

        self._savedir = FileSelectionWidget()
        self._savedir.filterDirectory()
        self._savedir.setTextLabel('Export directory')
        self._savedir.setContentsMargins(0, 0, 0, 0)
        self._convert = QPushButton('Convert')
        self._convert.setToolTip('Convert Sisyphe volumes to {} format.'.format(self._ioformat))
        # noinspection PyUnresolvedReferences
        self._convert.clicked.connect(self.convert)
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(self._convert)
        layout.addWidget(self._savedir)
        self._layout.addLayout(layout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addStretch()

        self._layout.addLayout(layout)
        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)

        # Window


        self.setModal(True)

    # Public method

    def convert(self):
        filenames = self._files.getFilenames()
        n = len(filenames)
        if n > 0:
            # Set ProgressBar
            progress = DialogWait()
            progress.setProgressRange(0, n)
            progress.setCurrentProgressValue(0)
            progress.buttonVisibilityOff()
            progress.progressTextVisibilityOn()
            progress.setProgressVisibility(n > 1)
            progress.setInformationText('Load Sisyphe volumes...')
            vol = SisypheVolume()
            try:
                for filename in filenames:
                    # load SisypheVolume filename
                    progress.setInformationText('Load {}...'.format(basename(filename)))
                    try: vol.load(filename)
                    except:
                        messageBox(self,
                                   title='{} export'.format(self._ioformat),
                                   text='{} read error.'.format(basename(filename)))
                    try:
                        if not self._savedir.isEmpty():
                            filename = join(self._savedir.getPath(), basename(filename))
                        # Nifti
                        if self._ioformat == 'Nifti':
                            filename = splitext(filename)[0] + getNiftiExt()[0]
                            progress.setInformationText('Save {}...'.format(basename(filename)))
                            vol.saveToNIFTI(filename)
                        # Minc
                        elif self._ioformat == 'Minc':
                            filename = splitext(filename)[0] + getMincExt()[0]
                            progress.setInformationText('Save {}...'.format(basename(filename)))
                            vol.saveToMINC(filename)
                        # Nrrd
                        elif self._ioformat == 'Nrrd':
                            filename = splitext(filename)[0] + getNrrdExt()[0]
                            progress.setInformationText('Save {}...'.format(basename(filename)))
                            vol.saveToNRRD(filename)
                        # Vtk
                        elif self._ioformat == 'Vtk':
                            filename = splitext(filename)[0] + getVtkExt()[0]
                            progress.setInformationText('Save {}...'.format(basename(filename)))
                            vol.saveToVTK(filename)
                        # Numpy
                        elif self._ioformat == 'Numpy':
                            filename = splitext(filename)[0] + getNumpyExt()[0]
                            progress.setInformationText('Save {}...'.format(basename(filename)))
                            vol.saveToNumpy(filename)
                    except:
                        messageBox(self,
                                   title='{} export'.format(self._ioformat),
                                   text='{} write error.'.format(self._ioformat))
                        continue
                    progress.incCurrentProgressValue()
            finally:
                progress.hide()
                self._files.clearall()
