from os.path import join
from os.path import basename
from os.path import splitext

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

"""
    Class hierarchy

        QDialog -> DialogImport
"""


class DialogImport(QDialog):
    """
        DialogImport

        Inheritance

            QDialog -> DialogImport

        Private attributes

            _ioformat   str, import format (nifti, minc, nrrd, vtk, npy)

        Public methods

            convert()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, io='Nifti', parent=None):
        super().__init__(parent)

        self._ioformat = io

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
        self._convert = QPushButton(QIcon(join(self._savedir.getDefaultIconDirectory(), 'import.png')), '')
        self._convert.setFixedSize(QSize(64, 32))
        self._convert.setToolTip('Convert {} files to Sisyphe volume.'.format(self._ioformat))
        self._convert.clicked.connect(self.convert)
        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.addWidget(self._savedir)
        layout.addWidget(self._convert)
        self._layout.addLayout(layout)

        # Init default dialog buttons

        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        layout.addWidget(ok)
        layout.addStretch()

        self._layout.addLayout(layout)

        ok.clicked.connect(self.accept)

        # Window

        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.25), int(screen.height() * 0.25))

        self.setWindowTitle('{} import'.format(io))
        self.setModal(True)

    # Public method

    def convert(self):
        filenames = self._files.getFilenames()
        if filenames is not None:
            n = len(filenames)
            if n > 0:
                # Set ProgressBar
                progress = DialogWait(title='{} import'.format(self._ioformat),
                                      progressmin=0, progressmax=n, progresstxt=True, cancel=True, parent=self)
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
                            QMessageBox.warning(self, '{} import'.format(self._ioformat),
                                                '{} read/write error.'.format(self._ioformat))
                            continue
                        progress.incCurrentProgressValue()
                        if progress.getStopped(): break
                finally:
                    progress.hide()
                    self._files.clearall()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    main = DialogImport('Nifti')
    main.show()
    app.exec_()
