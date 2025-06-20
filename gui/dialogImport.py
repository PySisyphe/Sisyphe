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

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

__all__ = ['DialogImport']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogImport
"""


class DialogImport(QDialog):
    """
    DialogImport

    Description
    ~~~~~~~~~~~

    GUI dialog for importing nifti, minc, nrrd, vtk, npy image formats.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogImport

    Last revision: 14/11/2024
    """

    # Special method

    """
    Private attributes

    _ioformat   str, import format (nifti, minc, nrrd, vtk, npy)
    """

    def __init__(self, io='Nifti', parent=None):
        super().__init__(parent)

        self._ioformat = io
        self.setWindowTitle('{} import'.format(io))
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.50), int(screen.height() * 0.50))
        self.setSizeGripEnabled(False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = FilesSelectionWidget()
        self._files.setMaximumNumberOfFiles(256)
        if io == 'Nifti': self._files.filterNifti()
        elif io == 'Minc': self._files.filterMinc()
        elif io == 'Nrrd': self._files.filterNrrd()
        elif io == 'Vtk': self._files.filterVtk()
        else: self._files.filterNumpy()
        self._layout.addWidget(self._files)

        self._savedir = FileSelectionWidget()
        self._savedir.filterDirectory()
        self._savedir.setTextLabel('Import directory')
        self._savedir.setContentsMargins(0, 0, 0, 0)
        # < Revision 14/11/2024
        # self._convert = QPushButton(QIcon(join(self._savedir.getDefaultIconDirectory(), 'import.png')), '')
        # self._convert.setFixedSize(QSize(64, 32))
        self._convert = QPushButton('Import')
        # Revision 14/11/2024 >
        self._convert.setToolTip('Import {} files.'.format(self._ioformat))
        # noinspection PyUnresolvedReferences
        self._convert.clicked.connect(self.convert)
        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.addWidget(self._savedir)
        layout.addWidget(self._convert)
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

        self.setModal(True)

    # Public method

    def convert(self):
        filenames = self._files.getFilenames()
        if filenames is not None:
            n = len(filenames)
            if n > 0:
                # Set ProgressBar
                progress = DialogWait(title='{} import'.format(self._ioformat),
                                      progressmin=0, progressmax=n, progresstxt=True, cancel=True)
                progress.setProgressVisibility(n > 1)
                progress.open()
                try:
                    for filename in filenames:
                        # load SisypheVolume filename
                        progress.setInformationText('Load {}...'.format(basename(filename)))
                        vol = SisypheVolume()
                        try:
                            savename = splitext(filename)[0]
                            # Nifti
                            if self._ioformat == 'Nifti':
                                savename = splitext(savename)[0]  # remove ext .nii.gz
                                vol.loadFromNIFTI(filename)
                                progress.setInformationText('Save {}...'.format(basename(savename)))
                            # Minc
                            elif self._ioformat == 'Minc':
                                vol.loadFromMINC(filename)
                                progress.setInformationText('Save {}...'.format(basename(savename)))
                            # Nrrd
                            elif self._ioformat == 'Nrrd':
                                vol.loadFromNRRD(filename)
                                progress.setInformationText('Save {}...'.format(basename(savename)))
                            # Vtk
                            elif self._ioformat == 'Vtk':
                                vol.loadFromVTK(filename)
                                progress.setInformationText('Save {}...'.format(basename(savename)))
                            # Numpy
                            else:
                                vol.loadFromNumpy(filename)
                                progress.setInformationText('Save {}...'.format(basename(savename)))
                            savename += vol.getFileExt()
                            if not self._savedir.isEmpty():
                                savename = join(self._savedir.getPath(), basename(savename))
                            vol.save(savename)
                        except:
                            messageBox(self,
                                       title='{} import'.format(self._ioformat),
                                       text='{} IO error.'.format(self._ioformat))
                            continue
                        progress.incCurrentProgressValue()
                        if progress.getStopped(): break
                finally:
                    progress.hide()
                    self._files.clearall()
