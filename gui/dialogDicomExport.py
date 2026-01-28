"""
External packages/modules
-------------------------

    - PyQt5,Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import basename

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheDicom import ExportToDicom
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

"""
Class hierarchy
~~~~~~~~~~~~~~~

    QDialog -> DialogDicomExport
"""


class DialogDicomExport(QDialog):
    """
    DialogDicomExport

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDicomExport

    Last revision: 03/09/2025
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('DICOM export')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        # < Revision 17/07/2025
        # self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.75))
        self.setMinimumSize(int(screen.width() * 0.50), int(screen.height() * 0.50))
        # Revision 17/07/2025 >

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
        # < Revision 03/09/2025
        # self._convert = QPushButton(QIcon(join(self._savedir.getDefaultIconDirectory(), 'export.png')), '')
        self._convert = QPushButton('Export')
        # Revision 03/09/2025 >
        # self._convert.setFixedSize(QSize(64, 32))
        self._convert.setToolTip('Convert Sisyphe volumes to DICOM format.')
        # noinspection PyUnresolvedReferences
        self._convert.clicked.connect(self.convert)
        layout = QHBoxLayout()
        layout.setSpacing(10)
        # < Revision 03/09/2025
        # layout.addWidget(self._convert)
        # layout.addWidget(self._savedir)
        layout.addWidget(self._savedir)
        layout.addWidget(self._convert)
        # Revision 03/09/2025 >
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
            progress.open()
            vol = SisypheVolume()
            export = ExportToDicom()
            try:
                for filename in filenames:
                    # load SisypheVolume filename
                    progress.setInformationText('Load {}...'.format(basename(filename)))
                    try: vol.load(filename)
                    except:
                        # < Revision 03/09/2025
                        # hide progress dialog before message box
                        progress.hide()
                        # Revision 03/09/2025 >
                        messageBox(self,
                                   'DICOM export',
                                   text='{} read error.'.format(basename(filename)))
                    export.setVolume(vol)
                    if not self._savedir.isEmpty(): export.setBackupDicomDirectory(self._savedir.getPath())
                    progress.setInformationText('Export {} to DICOM...'.format(basename(filename)))
                    export.execute()
                    try: export.execute()
                    except:
                        # < Revision 03/09/2025
                        # hide progress dialog before message box
                        progress.hide()
                        # Revision 03/09/2025 >
                        messageBox(self, 'DICOM export', 'DICOM write error.')
                    progress.incCurrentProgressValue()
            finally:
                progress.hide()
                self._files.clearall()
