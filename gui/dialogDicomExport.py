from os.path import join
from os.path import basename

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheDicom import ExportToDicom
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

"""
    Class

        DialogDicomExport
"""


class DialogDicomExport(QDialog):
    """
        DialogDicomExport

        Inheritance

            QDialog -> DialogDicomExport

        Private attributes

        Public methods

            convert()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

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
        self._convert = QPushButton(QIcon(join(self._savedir.getDefaultIconDirectory(), 'export.png')), '')
        self._convert.setFixedSize(QSize(64, 32))
        self._convert.setToolTip('Convert Sisyphe volumes to DICOM format.')
        self._convert.clicked.connect(self.convert)
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(self._convert)
        layout.addWidget(self._savedir)
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
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.75))

        self.setWindowTitle('DICOM export')
        self.setModal(True)

    # Public method

    def convert(self):
        filenames = self._files.getFilenames()
        n = len(filenames)
        if n > 0:
            # Set ProgressBar
            progress = DialogWait(parent=self)
            progress.setProgressRange(0, n)
            progress.setCurrentProgressValue(0)
            progress.buttonVisibilityOff()
            progress.progressTextVisibilityOn()
            progress.setProgressVisibility(n > 1)
            progress.setInformationText('Load Sisyphe volumes...')
            progress.open()
            vol = SisypheVolume()
            export = ExportToDicom()
            try:
                for filename in filenames:
                    # load SisypheVolume filename
                    progress.setInformationText('Load {}...'.format(basename(filename)))
                    try: vol.load(filename)
                    except:
                        QMessageBox.warning(self, 'DICOM export',
                                            '{} read error.'.format(basename(filename)))
                    export.setVolume(vol)
                    if not self._savedir.isEmpty(): export.setBackupDicomDirectory(self._savedir.getPath())
                    progress.setInformationText('Export {} to DICOM...'.format(basename(filename)))
                    try: export.execute()
                    except: QMessageBox.warning(self, 'DICOM export', 'DICOM write error.')
                    progress.incCurrentProgressValue()
            finally:
                progress.hide()
                self._files.clearall()


"""
    Test
"""

if __name__ == '__main__':

    from sys import argv

    app = QApplication(argv)
    main = DialogDicomExport()
    main.show()
    app.exec_()
