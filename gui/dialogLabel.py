"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from os import getcwd
from os.path import exists
from os.path import basename

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import SisypheVolumeCollection
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
    Class hierarchy

        QDialog -> DialogVOLtoLabel
        QDialog -> DialogROItoLabel
        QDialog -> DialogLabeltoROI
"""

class DialogVOLtoLabel(QDialog):
    """
        DialogVOLtoLabel class

        Description

            GUI dialog window to convert volumes to label volume

        Inheritance

            QDialog -> DialogVOLtoLabel

        Private attributes

            _list   FilesSelectionWidget

        Public methods

            convert()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Volumes to Label volume')

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

        self._ok.clicked.connect(self.convert)
        cancel.clicked.connect(self.reject)

    # Public methods

    def convert(self):
        if not self._list.isEmpty():
            vols = SisypheVolumeCollection()
            wait = DialogWait(info=self.windowTitle(),
                              progressmin=0, progressmax=self._list.filenamesCount(), parent=self)
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
                    lbl.saveAs(filename)
            else: wait.hide()
            r = QMessageBox.question(self, self.windowTitle(),
                                     'Do you want to make a new conversion ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r == QMessageBox.Yes: self._list.clear()
            else: self.accept()
            wait.close()


class DialogROItoLabel(QDialog):
    """
        DialogROItoLabel class

        Description

            GUI dialog window to convert ROIs to label volume

        Inheritance

            QDialog -> DialogROItoLabel

        Private attributes

            _list   FilesSelectionWidget

        Public methods

            convert()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('ROI(s) to Label volume')

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

        self._ok.clicked.connect(self.convert)
        cancel.clicked.connect(self.reject)

    # Public methods

    def convert(self):
        if not self._list.isEmpty():
            rois = SisypheROICollection()
            wait = DialogWait(info=self.windowTitle(),
                              progressmin=0, progressmax=self._list.filenamesCount(), parent=self)
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
                    lbl.saveAs(filename)
            wait.hide()
            r = QMessageBox.question(self, self.windowTitle(),
                                     'Do you want to make a new conversion ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r == QMessageBox.Yes: self._list.clear()
            else: self.accept()
            wait.close()


class DialogLabeltoROI(QDialog):
    """
        DialogLabelToROI class

        Description

            GUI dialog window to convert label volume to ROIs

        Inheritance

            QDialog -> DialogLabelToROI

        Private attributes

            _list   FilesSelectionWidget

        Public methods

            convert()

            inherited QDialog methods
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Label volume(s) to ROI(s)')

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

        self._ok.clicked.connect(self.convert)
        cancel.clicked.connect(self.reject)

    # Public methods

    def convert(self):
        if not self._list.isEmpty():
            v = SisypheVolume()
            wait = DialogWait(info=self.windowTitle(),
                              progressmin=0, progressmax=self._list.filenamesCount(), parent=self)
            wait.progressVisibilityOn()
            wait.open()
            for filename in self._list.getFilenames():
                wait.setInformationText('{} conversion...'.format(basename(filename)))
                wait.incCurrentProgressValue()
                if exists(filename):
                    wait.open()
                    wait.incCurrentProgressValue()
                    v.load(filename)
                    rois = SisypheROICollection()
                    rois.fromLabelVolume(v)
                    rois.save()
            wait.hide()
            r = QMessageBox.question(self, self.windowTitle(),
                                     'Do you want to make a new conversion ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r == QMessageBox.Yes: self._list.clear()
            else: self.accept()
            wait.close()

