"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import chdir

from os.path import exists
from os.path import basename
from os.path import dirname
from os.path import abspath

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['DialogVOLtoLabel',
           'DialogROItoLabel',
           'DialogLabeltoROI']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogVOLtoLabel
              -> DialogROItoLabel
              -> DialogLabeltoROI
"""

class DialogVOLtoLabel(QDialog):
    """
    DialogVOLtoLabel class

    Description
    ~~~~~~~~~~~

    GUI dialog window to convert volume to label volume.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogVOLtoLabel

    Last revision: 13/02/2025
    """

    # Special method

    """
    Private attributes

    _list   FilesSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Probability volumes to Label volume')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self.setSizeGripEnabled(False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._list = FilesSelectionWidget()
        self._list.setTextLabel('Probability volume(s)')
        self._list.filterSisypheVolume()
        self._list.filterRange(v=(0.0, 1.0))
        self._list.filterSameFOV()
        self._list.setMaximumNumberOfFiles(255)
        self._list.setReferenceVolumeToFirst()
        self._layout.addWidget(self._list)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        cancel = QPushButton('Cancel')
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()
        layout.setSizeConstraint(QHBoxLayout.SetFixedSize)

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.convert)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

    # Public methods

    def setFilenames(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        self._list.setFilenames(filenames)

    def convert(self):
        if not self._list.isEmpty():
            vols = SisypheVolumeCollection()
            wait = DialogWait(info=self.windowTitle(),
                              progressmin=0, progressmax=self._list.filenamesCount())
            wait.open()
            wait.progressVisibilityOn()
            wait.buttonVisibilityOff()
            wait.FigureVisibilityOff()
            for filename in self._list.getFilenames():
                wait.setInformationText('Load {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                if exists(filename):
                    v = SisypheVolume()
                    v.load(filename)
                    vols.append(v)
            if vols.count() > 1:
                wait.progressVisibilityOff()
                wait.setInformationText('Label volume processing...')
                lbl = vols.toLabelVolume()
                wait.hide()
                filename = QFileDialog.getSaveFileName(self,
                                                       'Save label volume...',
                                                       vols[0].getDirname(),
                                                       filter=lbl.getFilterExt())[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    lbl.saveAs(filename)
            else: wait.hide()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Do you want to make a new conversion ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._list.clear()
            else: self.accept()
            wait.close()


class DialogROItoLabel(QDialog):
    """
    DialogROItoLabel class

    Description
    ~~~~~~~~~~~

    GUI dialog window to convert ROIs to label volume.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogROItoLabel

    Last revision: 13/02/2025
    """

    # Special method

    """
    Private attributes

    _list   FilesSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('ROI(s) to Label volume')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self.setSizeGripEnabled(False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._list = FilesSelectionWidget()
        self._list.setTextLabel('ROI(s)')
        self._list.filterSisypheROI()
        self._list.filterSameID()
        self._list.setMaximumNumberOfFiles(255)
        self._list.setReferenceVolumeToFirst()
        self._layout.addWidget(self._list)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        cancel = QPushButton('Cancel')
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()
        layout.setSizeConstraint(QHBoxLayout.SetFixedSize)

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.convert)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

    # Public methods

    def setFilenames(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        self._list.setFilenames(filenames)

    def convert(self):
        if not self._list.isEmpty():
            rois = SisypheROICollection()
            wait = DialogWait(info=self.windowTitle(),
                              progressmin=0, progressmax=self._list.filenamesCount())
            wait.open()
            wait.progressVisibilityOn()
            for filename in self._list.getFilenames():
                wait.setInformationText('Load {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                if exists(filename):
                    roi = SisypheROI()
                    roi.load(filename)
                    rois.append(roi)
            if rois.count() > 1:
                wait.progressVisibilityOff()
                wait.setInformationText('Label volume processing...')
                lbl = rois.toLabelVolume()
                wait.hide()
                filename = QFileDialog.getSaveFileName(self,
                                                       'Save label volume...',
                                                       rois[0].getDirname(),
                                                       filter=lbl.getFilterExt())[0]
                if filename:
                    filename = abspath(filename)
                    chdir(dirname(filename))
                    lbl.saveAs(filename)
            wait.hide()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Do you want to make a new conversion ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._list.clear()
            else: self.accept()
            wait.close()


class DialogLabeltoROI(QDialog):
    """
    DialogLabelToROI class

    Description
    ~~~~~~~~~~~

    GUI dialog window to convert label volume to ROIs.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogLabelToROI

    Last revision: 13/02/2025
    """

    # Special method

    """
    Private attributes

    _list   FilesSelectionWidget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Label volume(s) to ROI(s)')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self.setSizeGripEnabled(False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        # Init widgets

        self._list = FilesSelectionWidget()
        self._list.setTextLabel('Label volume(s)')
        self._list.filterSisypheVolume()
        self._list.filterSameModality(SisypheAcquisition.getLBModalityTag())
        self._layout.addWidget(self._list)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setDirection(QHBoxLayout.RightToLeft)
        self._ok = QPushButton('OK')
        self._ok.setFixedWidth(100)
        self._ok.setAutoDefault(True)
        self._ok.setDefault(True)
        cancel = QPushButton('Cancel')
        layout.addWidget(self._ok)
        layout.addWidget(cancel)
        layout.addStretch()
        layout.setSizeConstraint(QHBoxLayout.SetFixedSize)

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        self._ok.clicked.connect(self.convert)
        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)

    # Public methods

    def setFilenames(self, filenames: str | list[str]) -> None:
        if isinstance(filenames, str): filenames = [filenames]
        self._list.setFilenames(filenames)

    def convert(self):
        if not self._list.isEmpty():
            v = SisypheVolume()
            wait = DialogWait(info=self.windowTitle(),
                              progressmin=0, progressmax=self._list.filenamesCount())
            wait.open()
            wait.progressVisibilityOn()
            for filename in self._list.getFilenames():
                wait.setInformationText('{} conversion...'.format(basename(filename)))
                wait.incCurrentProgressValue()
                if exists(filename):
                    wait.incCurrentProgressValue()
                    v.load(filename)
                    rois = SisypheROICollection()
                    rois.fromLabelVolume(v)
                    rois.save()
            wait.hide()
            r = messageBox(self,
                           title=self.windowTitle(),
                           text='Do you want to make a new conversion ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes: self._list.clear()
            else: self.accept()
            wait.close()
