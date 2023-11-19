"""
    External packages/modules

        Name            Homepage link                                               Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import mkdir
from os.path import join
from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import splitext

from glob import glob

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget

"""
    Class hierarchy

        QDialog -> DialogOldSisypheImport
"""


class DialogOldSisypheImport(QDialog):
    """
        DialogImport

        Inheritance

            QDialog -> DialogOldSisypheImport

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
        self._files.filterDirectory()
        self._layout.addWidget(self._files)

        self._savedir = FileSelectionWidget()
        self._savedir.filterDirectory()
        self._savedir.setTextLabel('Import directory')
        self._savedir.setContentsMargins(0, 0, 0, 0)
        self._convert = QPushButton(QIcon(join(self._savedir.getDefaultIconDirectory(), 'download64.png')), 'Convert')
        self._convert.setFixedSize(QSize(100, 32))
        self._convert.setToolTip('Convert Sisyphe old binary format to Sisyphe volume.')
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

        self.setWindowTitle('Sisyphe import')
        self.setModal(True)

    # Public method

    def convert(self):
        folders = self._files.getFilenames()
        if folders:
            n = len(folders)
            # Set ProgressBar
            progress = DialogWait(parent=self)
            progress.buttonVisibilityOff()
            progress.progressTextVisibilityOn()
            progress.setProgressVisibility(n > 1)
            try:
                # Convert all sisyphe volumes in folder
                for folder in folders:
                    progress.setInformationText('Folder {} analysis...')
                    progress.open()
                    QApplication.processEvents()
                    filenames = glob(join(folder, '*.vol'))
                    roinames = glob(join(folder, '*.roi'))
                    progress.setProgressRange(0, len(filenames))
                    progress.setCurrentProgressValue(0)
                    if len(filenames) > 0:
                        for filename in filenames:
                            progress.setInformationText('Folder {}, '
                                                        'load {}'.format(basename(folder), basename(filename)))
                            vol = SisypheVolume()
                            try: vol.loadFromSisyphe(filename)
                            except:
                                QMessageBox.warning(self, 'Sisyphe old binary format import',
                                                    '{} read error.'.format(basename(filename)))
                                continue
                            if not self._savedir.isEmpty():
                                savename = join(self._savedir.getPath(), basename(folder), basename(filename))
                                if not exists(dirname(savename)): mkdir(dirname(savename))
                            else: savename = filename
                            progress.setInformationText('Folder {}, '
                                                        'save {}'.format(basename(folder), basename(savename)))
                            try: vol.saveAs(savename)
                            except:
                                QMessageBox.warning(self, 'Sisyphe old binary format import',
                                                    '{} write error.'.format(basename(savename)))
                                continue
                            size = vol.getSize()
                            # Convert roi associated to current volume in current folder
                            if len(roinames) > 0:
                                for roiname in roinames:
                                    roi = SisypheROI()
                                    roi.loadFromSisyphe(roiname)
                                    if roi.getSize() == size:
                                        roi.setReferenceID(vol.getID())
                                    roiname = splitext(roiname)[0] + SisypheROI.getFileExt()
                                    if not self._savedir.isEmpty():
                                        saveroi = join(self._savedir.getPath(), basename(roiname))
                                    else: saveroi = roiname
                                    progress.setInformationText('Folder {}, Save {}'
                                                                .format(basename(folder), basename(saveroi)))
                                    try: roi.saveAs(saveroi)
                                    except:
                                        QMessageBox.warning(self, 'Sisyphe old binary format import',
                                                            '{} write error.'.format(basename(saveroi)))
                                        continue
                                    del roiname
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
    main = DialogOldSisypheImport()
    main.show()
    app.exec_()