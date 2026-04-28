"""
External packages/modules
-------------------------

    - Numpy, Scientific computing, https://numpy.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import basename
from os.path import exists

from numpy import array
from numpy import argsort

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.processing.qMRFunctions import B0DblEchoMap
from Sisyphe.processing.qMRFunctions import B1DblTRMap
from Sisyphe.processing.qMRFunctions import B1GEDblAngleMap
# from Sisyphe.processing.qMRFunctions import B1SEDblAngleMap
from Sisyphe.processing.qMRFunctions import T1MultiTRMap
from Sisyphe.processing.qMRFunctions import T1MultiAngleMap
from Sisyphe.processing.qMRFunctions import T2MonoExpMap
from Sisyphe.processing.qMRFunctions import T2BiExpMap
from Sisyphe.processing.qMRFunctions import T2primeMap
from Sisyphe.processing.qMRFunctions import MTRMap
from Sisyphe.processing.qMRFunctions import QSMMap
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.functionsSettingsWidget import FunctionSettingsWidget
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWithParametersWidget
from Sisyphe.widgets.selectFileWidgets import SynchronizedFilesSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogWait import UserAbortException


__all__ = ['DialogB0Mapping',
           'DialogB1Mapping',
           'DialogT1Mapping',
           'DialogT2Mapping',
           'DialogT2pMapping',
           'DialogMTRMapping',
           'DialogQSMMapping']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    QDialog -> DialogB0Mapping
            -> DialogB1Mapping
            -> DialogT1Mapping
            -> DialogT2Mapping
            -> DialogT2pMapping
            -> DialogMTRMapping
            -> DialogQSMMapping
"""


class DialogB0Mapping(QDialog):
    """
    DialogB0Mapping

    Description
    ~~~~~~~~~~~

    GUI dialog for B0 main static magnetic field map (in Hz) map processing.

    Code adapted from https://github.com/lamyj/erwin

    Reference:
    An in vivo automated shimming method taking into account shim current constraints. Wen H. & Jaffer F.A.
    Magn Reson Med. 1995 34(6),pp.898-904.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogB0Mapping

    Creation: 26/03/2026
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('B0 map processing')
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._phseSelect = FilesSelectionWithParametersWidget(parent=self)
        self._phseSelect.filterSisypheVolume()
        self._phseSelect.filterSameSequence(SisypheAcquisition.PHSE)
        self._phseSelect.filterSameFOV()
        self._phseSelect.setReferenceVolumeToFirst()
        self._phseSelect.fileCountWarningOff()
        self._phseSelect.setCurrentVolumeButtonVisibility(True)
        self._phseSelect.setMinimumWidth(500)
        self._phseSelect.setVisible(True)
        self._phseSelect.setMaximumNumberOfFiles(2)
        self._phseSelect.setTextLabel('Volumes')
        self._phseSelect.addDicomParameter('EchoTime', 1.0, 2000.0, width=100)
        self._phseSelect.setTextLabel('Two phase volumes')
        self._phseSelect.FieldChanged.connect(self._phseChanged)
        self._phseSelect.FieldCleared.connect(self._phseChanged)
        self._layout.addWidget(self._phseSelect)

        self._maskSelect = FileSelectionWidget(parent=self)
        self._maskSelect.filterSisypheVolume()
        self._maskSelect.filterSameSequence(SisypheAcquisition.MASK)
        self._maskSelect.setCurrentVolumeButtonVisibility(True)
        self._maskSelect.setTextLabel('Analysis mask')
        self._maskSelect.setMinimumWidth(500)
        self._maskSelect.setVisible(True)
        self._maskSelect.FieldChanged.connect(self._maskChanged)
        self._maskSelect.FieldCleared.connect(self._maskChanged)
        self._layout.addWidget(self._maskSelect)

        self._settings = FunctionSettingsWidget('B0Map', parent=self)
        self._settings.setSettingsButtonText('B0 map')
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute B0 map processing')
        # self._execute.setAutoDefault(True)
        # self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._phseSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setModal(True)

    # Private method

    def _phseChanged(self):
        n = self._phseSelect.filenamesCount()
        self._execute.setEnabled(n == 2)
        if self._phseSelect.isEmpty():
            if self._maskSelect.isEmpty():
                self._phseSelect.filterSameFOV()
                self._maskSelect.filterSameFOV()
        else:
            if self._maskSelect.isEmpty():
                fov = self._phseSelect.getFOVFilter()
                self._maskSelect.filterSameFOV(fov)

    def _maskChanged(self):
        if self._maskSelect.isEmpty():
            if self._phseSelect.isEmpty():
                self._phseSelect.filterSameFOV()
                self._maskSelect.filterSameFOV()
        else:
            self._settings.setParameterVisibility('Masking', False)
            self._settings.setParameterValue('Masking', 'No')
            if self._phseSelect.isEmpty():
                fov = self._maskSelect.getFOVFilter()
                self._phseSelect.filterSameFOV(fov)

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getFileSelectionWidget(self):
        return [self._phseSelect,
                self._maskSelect]

    def execute(self):
        n = self._phseSelect.filenamesCount()
        if n == 2:
            te = array(self._phseSelect.getParameterValues('EchoTime'))
            if all(te > 0.0):
                wait = DialogWait()
                wait.setInformationText('B0 map processing...')
                wait.open()
                p1 = SisypheVolume()
                p2 = SisypheVolume()
                filenames = self._phseSelect.getFilenames()
                wait.addInformationText('Open {}...'.format(basename(filenames[0])))
                p1.load(filenames[0])
                wait.addInformationText('Open {}...'.format(basename(filenames[1])))
                p2.load(filenames[1])
                if te[0] > te[1]:
                    te = te[1], te[0]
                    phse = p2, p1
                else: phse = p1, p2
                if self._maskSelect.isEmpty(): mask = None
                elif exists(self._maskSelect.getFilename()):
                    mask = SisypheVolume()
                    wait.addInformationText('Open {}...'.format(basename(self._maskSelect.getFilename())))
                    mask.load(self._maskSelect.getFilename())
                else: mask = None
                rescaling = self._settings.getParameterValue('Rescaling')
                wait.setInformationText('B0 map processing...')
                try: r = B0DblEchoMap(phse, mask, te.tolist(), rescaling)
                except:
                    wait.close()
                    messageBox(self,
                               'B0 map processing',
                               text='B0 map processing failed.')
                    return
                r.setFilename(p1.getFilename())
                prefix = self._settings.getParameterValue('Prefix')
                suffix = self._settings.getParameterValue('Suffix')
                if prefix == '' and suffix == '': suffix = r.acquisition.B0MAP
                r.setFilenamePrefix(prefix)
                r.setFilenameSuffix(suffix)
                wait.addInformationText('Save B0 map {}...'.format(r.getBasename()))
                r.save()
                wait.close()
                """
                Exit  
                """
                r = messageBox(self,
                               self.windowTitle(),
                               'Would you like to process\nadditional B0 map(s) ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes:
                    self._phseSelect.clearAll()
                    self._maskSelect.clear()
                else: self.accept()
            else:
                messageBox(self,
                           'B0 map processing',
                           text='Not all TE are defined.')


class DialogB1Mapping(QDialog):
    """
    DialogB1Mapping

    Description
    ~~~~~~~~~~~

    GUI dialog for B1 radiofrequency (RF) map processing.

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Actual flip-angle imaging in the pulsed steady state: a method for rapid three-dimensional mapping of the
    transmitted radiofrequency field. Yarnykh V.L. Magn Reson Med. 2007 57:192-200.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogB1Mapping

    Creation: 30/03/2026
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('B1 map processing')
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._magnSelect = FilesSelectionWithParametersWidget(parent=self)
        self._magnSelect.filterSisypheVolume()
        self._magnSelect.filterSameSequence(SisypheAcquisition.MGNT)
        self._magnSelect.filterSameFOV()
        self._magnSelect.setReferenceVolumeToFirst()
        self._magnSelect.fileCountWarningOff()
        self._magnSelect.setCurrentVolumeButtonVisibility(True)
        self._magnSelect.setMinimumWidth(500)
        self._magnSelect.setVisible(True)
        self._magnSelect.setMaximumNumberOfFiles(2)
        self._magnSelect.setTextLabel('Volumes')
        self._magnSelect.addDicomParameter('RepetitionTime', 1.0, 5000.0, width=100)
        self._magnSelect.addDicomParameter('FlipAngle', 0.0, 180.0, width=100)
        self._magnSelect.setTextLabel('Two spoiled gradient echo')
        self._magnSelect.FieldChanged.connect(self._magnChanged)
        self._magnSelect.FieldCleared.connect(self._magnChanged)
        self._layout.addWidget(self._magnSelect)

        self._maskSelect = FileSelectionWidget(parent=self)
        self._maskSelect.filterSisypheVolume()
        self._maskSelect.filterSameSequence(SisypheAcquisition.MASK)
        self._maskSelect.setCurrentVolumeButtonVisibility(True)
        self._maskSelect.setTextLabel('Analysis mask')
        self._maskSelect.setMinimumWidth(500)
        self._maskSelect.setVisible(True)
        self._maskSelect.FieldChanged.connect(self._maskChanged)
        self._maskSelect.FieldCleared.connect(self._maskChanged)
        self._layout.addWidget(self._maskSelect)

        self._settings = FunctionSettingsWidget('B1Map', parent=self)
        self._settings.setSettingsButtonText('B1 map')
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute B1 map processing')
        # self._execute.setAutoDefault(True)
        # self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._magnSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setModal(True)

    # Private method

    def _magnChanged(self):
        n = self._magnSelect.filenamesCount()
        self._execute.setEnabled(n == 2)
        if self._magnSelect.isEmpty():
            if self._maskSelect.isEmpty():
                self._magnSelect.filterSameFOV()
                self._maskSelect.filterSameFOV()
        else:
            if self._maskSelect.isEmpty():
                self._maskSelect.filterSameFOV(self._magnSelect.getFOVFilter())
            else:
                if self._maskSelect.getFOVFilter() != self._magnSelect.getFOVFilter():
                    self._maskSelect.filterSameFOV(self._magnSelect.getFOVFilter())

    def _maskChanged(self):
        if self._maskSelect.isEmpty():
            if self._magnSelect.isEmpty():
                self._magnSelect.filterSameFOV()
                self._maskSelect.filterSameFOV()
        else:
            self._settings.setParameterVisibility('Masking', False)
            self._settings.setParameterValue('Masking', 'No')
            if self._magnSelect.isEmpty() and self._phseSelect.isEmpty():
                fov = SisypheVolume.getVolumeAttribute(self._maskSelect.getFilename(), 'fov')
                self._magnSelect.filterSameFOV(fov)

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getFileSelectionWidget(self):
        return [self._magnSelect,
                self._maskSelect]

    def execute(self):
        n = self._magnSelect.filenamesCount() + self._phseSelect.filenamesCount()
        if n == 4:
            masking = self._settings.getParameterValue('Masking')[0]
            tr = array(self._magnSelect.getParameterValues('RepetitionTime'))
            fa = array(self._magnSelect.getParameterValues('FlipAngle'))
            if all(tr > 0.0) or all(fa > 0.0):
                wait = DialogWait()
                wait.setInformationText('B1 map processing...')
                wait.open()
                m1 = SisypheVolume()
                m2 = SisypheVolume()
                filenames = self._magnSelect.getFilenames()
                wait.addInformationText('Open {}...'.format(basename(filenames[0])))
                m1.load(filenames[0])
                wait.addInformationText('Open {}...'.format(basename(filenames[1])))
                m2.load(filenames[1])
                if tr[0] > tr[1]:
                    tr[[0, 1]] = tr[[1, 0]]
                    magn = m2, m1
                else: magn = m1, m2
                if self._maskSelect.isEmpty():
                    if masking != 'No':
                        wait.addInformationText('Automatic mask processing...')
                        mask = m1.getMask2(algo=masking, kernel=4)
                    else: mask = None
                else:
                    mask = SisypheVolume()
                    wait.addInformationText('Open {}...'.format(basename(self._maskSelect.getFilename())))
                    mask.load(self._maskSelect.getFilename())
                wait.setInformationText('B1 map processing...')
                try:
                     if tr[1] > tr[0]: r = B1DblTRMap(magn, mask, tr.tolist())
                     else: r = B1GEDblAngleMap(magn, mask, fa[0])
                except:
                    wait.close()
                    messageBox(self,
                               'B1 map processing',
                               text='B1 map processing failed.')
                    return
                r.setFilename(m1.getFilename())
                prefix = self._settings.getParameterValue('Prefix')
                suffix = self._settings.getParameterValue('Suffix')
                if prefix == '' and suffix == '': suffix = r.acquisition.B1MAP
                r.setFilenamePrefix(prefix)
                r.setFilenameSuffix(suffix)
                wait.addInformationText('Save B1 map {}...'.format(r.getBasename()))
                r.save()
                wait.close()
                """
                Exit  
                """
                r = messageBox(self,
                               self.windowTitle(),
                               'Would you like to process\nadditional B1 map(s) ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes:
                    self._magnSelect.clearAll()
                    self._maskSelect.clear()
                else: self.accept()
            else:
                messageBox(self,
                           'B1 map processing',
                           text='Not all TR or flip angles are defined.')


class DialogT1Mapping(QDialog):
    """
    DialogT1Mapping

    Description
    ~~~~~~~~~~~

    GUI dialog for T1 map processing.

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Quantitative MRI of the brain, 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogT1Mapping

    Creation: 30/03/2026
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('T1 map processing')
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._magnSelect = FilesSelectionWithParametersWidget(parent=self)
        self._magnSelect.filterSisypheVolume()
        self._magnSelect.filterSameSequence(SisypheAcquisition.MGNT)
        self._magnSelect.filterSameFOV()
        self._magnSelect.setReferenceVolumeToFirst()
        self._magnSelect.setCurrentVolumeButtonVisibility(True)
        self._magnSelect.setMinimumWidth(500)
        self._magnSelect.setVisible(True)
        self._magnSelect.setTextLabel('Volumes')
        self._magnSelect.addDicomParameter('EchoTime', 1.0, 5000.0, width=100)
        self._magnSelect.addDicomParameter('RepetitionTime', 1.0, 5000.0, width=100)
        self._magnSelect.addDicomParameter('FlipAngle', 0.0, 180.0, width=100)
        self._magnSelect.setTextLabel('Volumes with variable TR (VTR) or variable flip angles (VFA)')
        self._magnSelect.FieldChanged.connect(self._magnChanged)
        self._magnSelect.FieldCleared.connect(self._magnChanged)
        self._layout.addWidget(self._magnSelect)

        self._maskSelect = FileSelectionWidget(parent=self)
        self._maskSelect.filterSisypheVolume()
        self._maskSelect.filterSameSequence(SisypheAcquisition.MASK)
        self._maskSelect.setCurrentVolumeButtonVisibility(True)
        self._maskSelect.setTextLabel('Analysis mask')
        self._maskSelect.setMinimumWidth(500)
        self._maskSelect.setVisible(True)
        self._maskSelect.FieldChanged.connect(self._maskChanged)
        self._maskSelect.FieldCleared.connect(self._maskChanged)
        self._layout.addWidget(self._maskSelect)

        self._b1Select = FileSelectionWidget(parent=self)
        self._b1Select.filterSisypheVolume()
        self._b1Select.filterSameSequence(SisypheAcquisition.B1MAP)
        self._b1Select.setCurrentVolumeButtonVisibility(True)
        self._b1Select.setTextLabel('B1 map')
        self._b1Select.alignLabels(self._maskSelect)
        self._b1Select.setMinimumWidth(500)
        self._b1Select.setVisible(True)
        self._b1Select.FieldChanged.connect(self._b1Changed)
        self._b1Select.FieldCleared.connect(self._b1Changed)
        self._layout.addWidget(self._b1Select)

        self._settings = FunctionSettingsWidget('T1Map', parent=self)
        self._settings.setSettingsButtonText('T1 map')
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute T1 map processing')
        # self._execute.setAutoDefault(True)
        # self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._magnSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setModal(True)

    # Private method

    def _magnChanged(self):
        n = self._magnSelect.filenamesCount()
        self._execute.setEnabled(n >= 2)
        if self._magnSelect.isEmpty():
            if self._b1Select.isEmpty() and self._maskSelect.isEmpty():
                self._magnSelect.filterSameFOV()
                self._b1Select.filterSameFOV()
                self._maskSelect.filterSameFOV()
        else:
            if self._b1Select.isEmpty():
                self._b1Select.filterSameFOV(self._magnSelect.getFOVFilter())
            else:
                if self._b1Select.getFOVFilter() != self._magnSelect.getFOVFilter():
                    self._b1Select.filterSameFOV(self._magnSelect.getFOVFilter())
            if self._maskSelect.isEmpty():
                self._maskSelect.filterSameFOV(self._magnSelect.getFOVFilter())
            else:
                if self._maskSelect.getFOVFilter() != self._magnSelect.getFOVFilter():
                    self._maskSelect.filterSameFOV(self._magnSelect.getFOVFilter())

    def _b1Changed(self):
        if self._b1Select.isEmpty():
            if self._magnSelect.isEmpty() and self._maskSelect.isEmpty():
                self._magnSelect.filterSameFOV()
                self._b1Select.filterSameFOV()
                self._maskSelect.filterSameFOV()
        else:
            if self._magnSelect.isEmpty():
                self._magnSelect.filterSameFOV(self._b1Select.getFOVFilter())
            else:
                if self._magnSelect.getFOVFilter() != self._b1Select.getFOVFilter():
                    self._magnSelect.filterSameFOV(self._b1Select.getFOVFilter())
            if self._maskSelect.isEmpty():
                self._maskSelect.filterSameFOV(self._b1Select.getFOVFilter())
            else:
                if self._maskSelect.getFOVFilter() != self._b1Select.getFOVFilter():
                    self._maskSelect.filterSameFOV(self._b1Select.getFOVFilter())

    def _maskChanged(self):
        if self._maskSelect.isEmpty():
            if self._magnSelect.isEmpty() and self._b1Select.isEmpty():
                self._magnSelect.filterSameFOV()
                self._b1Select.filterSameFOV()
                self._maskSelect.filterSameFOV()
        else:
            self._settings.setParameterVisibility('Masking', False)
            self._settings.setParameterValue('Masking', 'No')
            if self._magnSelect.isEmpty() and self._b1Select.isEmpty():
                fov = SisypheVolume.getVolumeAttribute(self._maskSelect.getFilename(), 'fov')
                self._magnSelect.filterSameFOV(fov)
                self._b1Select.filterSameFOV(fov)

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getFileSelectionWidget(self):
        return [self._magnSelect,
                self._b1Select,
                self._maskSelect]

    def execute(self):
        n = self._magnSelect.filenamesCount()
        if n >= 2:
            masking = self._settings.getParameterValue('Masking')[0]
            te = array(self._magnSelect.getParameterValues('EchoTime'))
            tr = array(self._magnSelect.getParameterValues('RepetitionTime'))
            fa = array(self._magnSelect.getParameterValues('FlipAngle'))
            if all(tr > 0.0) or all(fa > 0.0):
                wait = DialogWait()
                wait.setInformationText('T1 map processing...')
                wait.open()
                magn = list()
                for filename in self._magnSelect.getFilenames():
                    v = SisypheVolume()
                    wait.addInformationText('Open {}...'.format(basename(filename)))
                    v.load(filename)
                    magn.append(v)
                if fa[0] == fa[-1] and tr[0] != tr[-1]:
                    idx = argsort(tr)
                    tr = tr[idx]
                    magn = [magn[i] for i in idx]
                elif tr[0] == tr[-1] and fa[0] != fa[-1]:
                    idx = argsort(fa)
                    fa = fa[idx]
                    magn = [magn[i] for i in idx]
                else:
                    messageBox(self,
                               'T1 map processing',
                               text='Invalid TR or flip angles.')
                if self._maskSelect.isEmpty():
                    if masking != 'No':
                        wait.addInformationText('Automatic mask processing...')
                        mask = magn[0].getMask2(algo=masking, kernel=4)
                    else: mask = None
                else:
                    mask = SisypheVolume()
                    wait.addInformationText('Open {}...'.format(basename(self._maskSelect.getFilename())))
                    mask.load(self._maskSelect.getFilename())
                if self._b1Select.isEmpty(): b1 = None
                else:
                    if exists(self._b1Select.getFilename()):
                        b1 = SisypheVolume()
                        wait.addInformationText('Open {}...'.format(basename(self._b1Select.getFilename())))
                        b1.load(self._b1Select.getFilename())
                    else: b1 = None
                try:
                     if tr[-1] > tr[0]:
                         wait.setInformationText('VTR T1 map processing...')
                         r = T1MultiTRMap(magn, mask, tr.tolist(), te.tolist(), wait)
                     else:
                         wait.setInformationText('VFA T1 map processing...')
                         algo = self._settings.getParameterValue('FittingMethod')[0]
                         r = T1MultiAngleMap(magn, mask, b1, fa.tolist(), tr[0], algo, wait)
                except UserAbortException:
                    wait.close()
                    return
                except:
                    wait.close()
                    messageBox(self,
                               'T1 map processing',
                               text='T1 map processing failed.')
                    return
                r.setFilename(magn[0].getFilename())
                prefix = self._settings.getParameterValue('Prefix')
                suffix = self._settings.getParameterValue('Suffix')
                if prefix == '' and suffix == '': suffix = r.acquisition.T1MAP
                r.setFilenamePrefix(prefix)
                r.setFilenameSuffix(suffix)
                wait.addInformationText('Save T1 map {}...'.format(r.getBasename()))
                r.save()
                wait.close()
                """
                Exit  
                """
                r = messageBox(self,
                               self.windowTitle(),
                               'Would you like to process\nadditional T1 map(s) ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes:
                    self._magnSelect.clearAll()
                    self._b1Select.clear()
                    self._maskSelect.clear()
                else: self.accept()
            else:
                messageBox(self,
                           'T1 map processing',
                           text='Not all TR or flip angles are defined.')


class DialogT2Mapping(QDialog):
    """
    DialogT2Mapping

    Description
    ~~~~~~~~~~~

    GUI dialog for T2 map processing.

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Quantitative MRI of the brain, 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogT2Mapping

    Creation: 30/03/2026
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('T2 map processing')
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._magnSelect = FilesSelectionWithParametersWidget(parent=self)
        self._magnSelect.filterSisypheVolume()
        self._magnSelect.filterSameSequence(SisypheAcquisition.MGNT)
        self._magnSelect.filterSameFOV()
        self._magnSelect.setReferenceVolumeToFirst()
        self._magnSelect.setCurrentVolumeButtonVisibility(True)
        self._magnSelect.setMinimumWidth(500)
        self._magnSelect.setVisible(True)
        self._magnSelect.setTextLabel('Volumes')
        self._magnSelect.addDicomParameter('EchoTime', 1.0, 5000.0, width=100)
        self._magnSelect.setTextLabel('Volumes at variable echo times')
        self._magnSelect.FieldChanged.connect(self._magnChanged)
        self._magnSelect.FieldCleared.connect(self._magnChanged)
        self._layout.addWidget(self._magnSelect)

        self._maskSelect = FileSelectionWidget(parent=self)
        self._maskSelect.filterSisypheVolume()
        self._maskSelect.filterSameSequence(SisypheAcquisition.MASK)
        self._maskSelect.setCurrentVolumeButtonVisibility(True)
        self._maskSelect.setTextLabel('Analysis mask')
        self._maskSelect.setMinimumWidth(500)
        self._maskSelect.setVisible(True)
        self._maskSelect.FieldChanged.connect(self._maskChanged)
        self._maskSelect.FieldCleared.connect(self._maskChanged)
        self._layout.addWidget(self._maskSelect)

        self._settings = FunctionSettingsWidget('T2Map', parent=self)
        self._settings.setSettingsButtonText('T2 map')
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute T2 map processing')
        # self._execute.setAutoDefault(True)
        # self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._magnSelect.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setModal(True)

    # Private method

    def _magnChanged(self):
        n = self._magnSelect.filenamesCount()
        self._execute.setEnabled(n >= 2)
        if self._magnSelect.isEmpty():
            if self._maskSelect.isEmpty():
                self._magnSelect.filterSameFOV()
                self._maskSelect.filterSameFOV()
        else:
            if self._maskSelect.isEmpty():
                self._maskSelect.filterSameFOV(self._magnSelect.getFOVFilter())
            else:
                if self._maskSelect.getFOVFilter() != self._magnSelect.getFOVFilter():
                    self._maskSelect.filterSameFOV(self._magnSelect.getFOVFilter())

    def _maskChanged(self):
        if self._maskSelect.isEmpty():
            if self._magnSelect.isEmpty() :
                self._magnSelect.filterSameFOV()
                self._maskSelect.filterSameFOV()
        else:
            self._settings.setParameterVisibility('Masking', False)
            self._settings.setParameterValue('Masking', 'No')
            if self._magnSelect.isEmpty():
                fov = SisypheVolume.getVolumeAttribute(self._maskSelect.getFilename(), 'fov')
                self._magnSelect.filterSameFOV(fov)

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getFileSelectionWidget(self):
        return [self._magnSelect,
                self._maskSelect]

    def execute(self):
        n = self._magnSelect.filenamesCount()
        if n >= 2:
            masking = self._settings.getParameterValue('Masking')[0]
            te = array(self._magnSelect.getParameterValues('EchoTime'))
            if all(te > 0.0):
                wait = DialogWait()
                wait.setInformationText('T2 map processing...')
                wait.open()
                magn = list()
                filenames = self._magnSelect.getFilenames()
                for filename in filenames:
                    v = SisypheVolume()
                    wait.addInformationText('Open {}...'.format(basename(filename)))
                    v.load(filename)
                    magn.append(v)
                idx = argsort(te)
                te = te[idx]
                magn = [magn[i] for i in idx]
                if self._maskSelect.isEmpty():
                    if masking != 'No':
                        wait.addInformationText('Automatic mask processing...')
                        mask = magn[0].getMask2(algo=masking, kernel=4)
                    else: mask = None
                else:
                    mask = SisypheVolume()
                    wait.addInformationText('Open {}...'.format(basename(self._maskSelect.getFilename())))
                    mask.load(self._maskSelect.getFilename())
                wait.setInformationText('T2 map processing...')
                algo = self._settings.getParameterValue('FittingMethod')[0][0]
                if algo == 'l': pass
                elif algo == 'n': algo = 'nl'
                else: raise ValueError('Invalid fitting method {}.'.format(algo))
                model = self._settings.getParameterValue('FittingModel')[0][0]
                try:
                    if model == 'm': r = T2MonoExpMap(magn, mask, te, algo, wait)
                    elif model == 'b': r = T2BiExpMap(magn, mask, te, 0.0, wait)
                    else: raise ValueError('Invalid fitting model {}.'.format(model))
                except UserAbortException:
                    wait.close()
                    return
                except:
                    wait.close()
                    messageBox(self,
                               'T2 map processing',
                               text='T2 map processing failed.')
                    return
                prefix = self._settings.getParameterValue('Prefix')
                suffix = self._settings.getParameterValue('Suffix')
                if prefix == '' and suffix == '': suffix = r[0].acquisition.T2MAP
                r[0].setFilename(magn[0].getFilename())
                r[0].setFilenamePrefix(prefix)
                r[0].setFilenameSuffix(suffix)
                wait.addInformationText('Save T2 map {}...'.format(r[0].getBasename()))
                r[0].save()
                if len(r) > 1:
                    r[1].setFilename(magn[0].getFilename())
                    r[1].setFilenamePrefix(prefix)
                    r[1].setFilenameSuffix(suffix)
                    if prefix != '': r[1].setFilenamePrefix('Long_' + prefix)
                    if suffix != '': r[1].setFilenameSuffix('Long_' + suffix)
                    wait.addInformationText('Save long T2 map {}...'.format(r[0].getBasename()))
                    r[1].save()
                    r[2].setFilename(magn[0].getFilename())
                    r[2].setFilenamePrefix(prefix)
                    r[2].setFilenameSuffix(suffix)
                    if prefix != '': r[2].setFilenamePrefix('Short_' + prefix)
                    if suffix != '': r[2].setFilenameSuffix('Short_' + suffix)
                    wait.addInformationText('Save short T2 map {}...'.format(r[0].getBasename()))
                    r[2].save()
                    r[3].setFilename(magn[0].getFilename())
                    r[3].setFilenamePrefix(prefix)
                    r[3].setFilenameSuffix(suffix)
                    if prefix != '': r[3].setFilenamePrefix('Fraction_Long_' + prefix)
                    if suffix != '': r[3].setFilenameSuffix('Fraction_Long_' + suffix)
                    wait.addInformationText('Save long T2 fraction map {}...'.format(r[0].getBasename()))
                    r[3].save()
                wait.close()
                """
                Exit  
                """
                r = messageBox(self,
                               self.windowTitle(),
                               'Would you like to process\nadditional T2 map(s) ?',
                               icon=QMessageBox.Question,
                               buttons=QMessageBox.Yes | QMessageBox.No,
                               default=QMessageBox.No)
                if r == QMessageBox.Yes:
                    self._magnSelect.clearAll()
                    self._maskSelect.clear()
                else: self.accept()
            else:
                messageBox(self,
                           'T2 map processing',
                           text='Not all TE are defined.')


class DialogT2pMapping(QDialog):
    """
    DialogT2pMapping

    Description
    ~~~~~~~~~~~

    GUI dialog for T2' map processing.

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    Age-dependent normal values of T2* and T2' in brain parenchyma. Siemonsen  S., Finsterbusch J., Matschke J.,
    Lorenzen A., Ding X.-Q., Fiehler J. AJNR Am J Neuroradiol. 2008 May;29(5):950-955.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogT2pMapping

    Creation: 30/03/2026
    Last revision: 09/04/2026
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('T2\' map processing')
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._select = SynchronizedFilesSelectionWidget(single=None,
                                                        multiple=('T2 map(s)',
                                                                  'T2* map(s)',
                                                                  'Analysis mask(s)'),
                                                        parent=self)
        self._select.setSisypheVolumeFilters({'multiple': [True, True, True]})
        flt = {'multiple': [SisypheAcquisition.T2MAP,
                            SisypheAcquisition.T2MAP,
                            SisypheAcquisition.MASK]}
        self._select.setSequenceFilters(flt)
        self._select.setMinimumWidth(500)
        self._selectT2 = self._select.getSelectionWidget('T2 map(s)')
        self._selectT2s = self._select.getSelectionWidget('T2* map(s)')
        self._selectMask = self._select.getSelectionWidget('Analysis mask(s)')
        self._layout.addWidget(self._select)

        self._settings = FunctionSettingsWidget('T2pMap', parent=self)
        self._settings.setSettingsButtonText('T2\' map')
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute T2\' map processing')
        # self._execute.setAutoDefault(True)
        # self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._selectT2.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getFileSelectionWidget(self):
        return self._select.getSelectionWidgets()

    def execute(self):
        self.selectMask.setVisible(False)
        if self._select.isReady():
            self.selectMask.setVisible(True)
            masking = self._settings.getParameterValue('Masking')[0]
            prefix = self._settings.getParameterValue('Prefix')
            suffix = self._settings.getParameterValue('Suffix')
            n = self._selectT2.filenamesCount()
            ft2 = self._selectT2.getFilenames()
            ft2s = self._selectT2s.getFilenames()
            fmask = self._selectMask.getFilenames()
            wait = DialogWait()
            wait.setInformationText('T2\' map processing...')
            wait.buttonVisibilityOn()
            wait.setProgressRange(0, n-1)
            wait.setCurrentProgressValue(0)
            wait.setProgressVisibility(n > 1)
            for i in range(n):
                # < Revision 09/04/2026
                # self._selectT2.item(i).setSelected(True)
                # self._selectT2s.item(i).setSelected(True)
                self._selectT2.clearSelection()
                self._selectT2.setSelectionTo(i)
                self._selectT2s.clearSelection()
                self._selectT2s.setSelectionTo(i)
                # Revision 09/04/2026 >
                t2 = SisypheVolume()
                t2.load(ft2[i])
                t2s = SisypheVolume()
                t2s.load(ft2s[i])
                if i < len(fmask):
                    mask = SisypheVolume()
                    wait.addInformationText('Open {}...'.format(basename(fmask[i])))
                    mask.load(fmask[i])
                else:
                    if masking != 'No':
                        wait.addInformationText('Automatic mask processing...')
                        mask = t2.getMask2(algo=masking, kernel=4)
                    else: mask = None
                wait.setInformationText('T2\' map processing...')
                r = T2primeMap(t2, t2s, mask)
                r.setFilename(t2.getFilename())
                r.setFilenamePrefix(prefix)
                r.setFilenameSuffix(suffix)
                if prefix == '' and suffix == '': suffix = r.acquisition.T2PMAP
                r.save()
                wait.addInformationText('Save {}...'.format(r.getBasename()))
                wait.setCurrentProgressValue(i)
                if wait.getStopped(): break
            wait.close()
            """
            Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to process\nadditional T2\' map(s) ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._selectT2.clearAll()
                self._selectT2s.clearAll()
                self.selectMask.clearAll()
            else: self.accept()


class DialogMTRMapping(QDialog):
    """
    DialogMTRMapping

    Description
    ~~~~~~~~~~~

    GUI dialog for Magentization Transfer Ratio (MTR) map processing.

    Code adapted from MyRelax package, https://github.com/fragrussu/MyRelax

    Reference:
    T1, T2 relaxation and magnetization transfer in tissue at 3T. Stanisz G.J. Magn Reson Med. 2005 54:507-512.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogMTRMapping

    Creation: 31/03/2026
    Last revision: 09/04/2026
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('MTR map processing')
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._select = SynchronizedFilesSelectionWidget(single=None,
                                                        multiple=('Magentization transfer Off volume(s)',
                                                                  'Magentization transfer On volume(s)',
                                                                  'Analysis mask(s)'),
                                                        parent=self)
        self._select.setSisypheVolumeFilters({'multiple': [True, True, True]})
        flt = {'multiple': [SisypheAcquisition.MTR,
                            SisypheAcquisition.MTR,
                            SisypheAcquisition.MASK]}
        self._select.setSequenceFilters(flt)
        self._select.setMinimumWidth(500)
        self._selectMTROff = self._select.getSelectionWidget('Magentization transfer Off volume(s)')
        self._selectMTROn = self._select.getSelectionWidget('Magentization transfer On volume(s)')
        self._selectMask = self._select.getSelectionWidget('Analysis mask(s)')
        self._layout.addWidget(self._select)

        self._settings = FunctionSettingsWidget('MTRMap', parent=self)
        self._settings.setSettingsButtonText('MTR map')
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute MTR map processing')
        # self._execute.setAutoDefault(True)
        # self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._selectMTROff.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setModal(True)

    # Private method

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getFileSelectionWidget(self):
        return self._select.getSelectionWidgets()

    def execute(self):
        self.selectMask.setVisible(False)
        if self._select.isReady():
            self.selectMask.setVisible(True)
            masking = self._settings.getParameterValue('Masking')[0]
            prefix = self._settings.getParameterValue('Prefix')
            suffix = self._settings.getParameterValue('Suffix')
            n = self._selectMTROff.filenamesCount()
            fon = self._selectMTROn.getFilenames()
            foff = self._selectMTROff.getFilenames()
            fmask = self._selectMask.getFilenames()
            wait = DialogWait()
            wait.setInformationText('MTR map processing...')
            wait.buttonVisibilityOn()
            wait.setProgressRange(0, n-1)
            wait.setCurrentProgressValue(0)
            wait.setProgressVisibility(n > 1)
            for i in range(n):
                # < Revision 09/04/2026
                # self._selectMTROn.item(i).setSelected(True)
                # self._selectMTROff.item(i).setSelected(True)
                self._selectMTROn.clearSelection()
                self._selectMTROn.setSelectionTo(i)
                self._selectMTROff.clearSelection()
                self._selectMTROff.setSelectionTo(i)
                # Revision 09/04/2026 >
                on = SisypheVolume()
                on.load(fon[i])
                off = SisypheVolume()
                off.load(foff[i])
                if i < len(fmask):
                    mask = SisypheVolume()
                    wait.addInformationText('Open {}...'.format(basename(fmask[i])))
                    mask.load(fmask[i])
                else:
                    if masking != 'No':
                        wait.addInformationText('Automatic mask processing...')
                        mask = off.getMask2(algo=masking, kernel=4)
                    else: mask = None
                wait.setInformationText('MTR map processing...')
                r = MTRMap((on, off), mask)
                r.setFilename(on.getFilename())
                if prefix == '' and suffix == '': suffix = r.acquisition.MTR
                r.setFilenamePrefix(prefix)
                r.setFilenameSuffix(suffix)
                r.save()
                wait.addInformationText('Save {}...'.format(r.getBasename()))
                wait.setCurrentProgressValue(i)
                if wait.getStopped(): break
            wait.close()
            """
            Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to process\nadditional MTR map(s) ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._selectMTROn.clearAll()
                self._selectMTROff.clearAll()
                self.selectMask.clearAll()
            else: self.accept()


class DialogQSMMapping(QDialog):
    """
    DialogQSMMapping

    Description
    ~~~~~~~~~~~

    GUI dialog for Quantitative Susceptibility Mapping (QSM) processing using Total Generalized Variation (TGV-QSM).

    Code adapted from TGVQSM package, https://www.neuroimaging.at/pages/qsm.php

    Reference:
    Fast Quantitative Susceptibility Mapping using 3D EPI and Total Generalized Variation. Langkammer C., Bredies K.,
    Poser B.A., Barth M., Reishofer G. Fan A.P., Bilgic B., Fazekas F., Mainero C., Ropele S.
    Neuroimage. 2015 May 1;111:622-30.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogQSMMapping

    Creation: 31/03/2026
    Last revision: 27/04/2026
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Init window

        self.setWindowTitle('QSM map processing')
        # noinspection PyUnresolvedReferences
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = SynchronizedFilesSelectionWidget(single=None,
                                                       multiple=('Phase volume(s)',
                                                                 'Analysis mask(s)'),
                                                       params=True,
                                                       parent=self)
        self._files.setSisypheVolumeFilters({'multiple': [True, True]})
        flt = {'multiple': [SisypheAcquisition.PHSE,
                            SisypheAcquisition.MASK]}
        self._files.setSequenceFilters(flt)
        self._select = self._files.getSelectionWidget('Phase volume(s)')
        self._select.setMinimumWidth(500)
        self._select.setTextLabel('Volume(s)')
        self._select.addDicomParameter('EchoTime', 0.1, 5000.0, width=100)
        self._select.addDicomParameter('MagneticFieldStrength', 0.5, 7.0, width=100)
        self._select.setTextLabel('Phase volume(s)')
        self._select.FieldChanged.connect(self._phseChanged)
        self._select.FieldCleared.connect(self._phseChanged)
        self._maskSelect = self._files.getSelectionWidget('Analysis mask(s)')
        self._maskSelect.setMinimumWidth(500)
        self._layout.addWidget(self._files)

        self._settings = FunctionSettingsWidget('QSMMap', parent=self)
        self._settings.setSettingsButtonText('QSM map')
        self._settings.settingsVisibilityOn()
        self._layout.addWidget(self._settings)

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32': layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # noinspection PyUnresolvedReferences
        layout.setDirection(QHBoxLayout.RightToLeft)
        cancel = QPushButton('Cancel')
        self._execute = QPushButton('Execute')
        self._execute.setToolTip('Execute QSM map processing')
        # self._execute.setAutoDefault(True)
        # self._execute.setDefault(True)
        self._execute.setEnabled(False)
        layout.addWidget(self._execute)
        layout.addWidget(cancel)
        layout.addStretch()

        self._layout.addLayout(layout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        cancel.clicked.connect(self.reject)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

        self.adjustSize()
        # imposing dialog width -> set minimum width to a child widget of the main layout
        screen = QApplication.primaryScreen().geometry()
        self._select.setMinimumWidth(int(screen.width() * 0.33))
        # dialog resize off
        # noinspection PyUnresolvedReferences
        self._layout.setSizeConstraint(QHBoxLayout.SetFixedSize)
        self.setModal(True)

    # Private method

    def _phseChanged(self):
        n = self._select.filenamesCount()
        self._execute.setEnabled(n > 0)

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self.adjustSize()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    # Public method

    def getFileSelectionWidget(self):
        return [self._select,
                self._maskSelect]

    def execute(self):
        n = self._select.filenamesCount()
        if n > 0:
            prefix = self._settings.getParameterValue('Prefix')
            suffix = self._settings.getParameterValue('Suffix')
            rescaling = self._settings.getParameterValue('Rescaling')
            iters = self._settings.getParameterValue('Iters')
            fphse = self._select.getFilenames()
            fmask = self._maskSelect.getFilenames()
            wait = DialogWait()
            wait.setInformationText('QSM map processing...')
            wait.open()
            te = self._select.getParameterValues('EchoTime')
            field = self._select.getParameterValues('MagneticFieldStrength')
            print(te)
            print(field)
            for i in range(n):
                if te[i] == '0.0':
                    wait.close()
                    messageBox(self,
                               'QSM map processing',
                               text='TE is not defined for {}.'.format(basename(fphse[i])))
                    return
                if field[i] == '0.0':
                    wait.close()
                    messageBox(self,
                               'QSM map processing',
                               text='Magentic field strenght is not defined for {}.'.format(basename(fphse[i])))
                    return
                self._select.clearSelection()
                self._select.setSelectionTo(i)
                self._maskSelect.clearSelection()
                img = SisypheVolume()
                img.load(fphse[i])
                # < Revision 27/04/2026
                # if i < len(fmask):
                if fmask is not None and i < len(fmask):
                    self._maskSelect.setSelectionTo(i)
                    mask = SisypheVolume()
                    wait.addInformationText('Open {}...'.format(basename(fmask[i])))
                    mask.load(fmask[i])
                else: mask = None
                # Revision 27/04/2026 >
                wait.setInformationText('QSM map processing...')
                try: r = QSMMap(img, mask, te[i], field[i], rescaling, iters, wait=wait)
                except UserAbortException:
                    wait.close()
                    self._select.clearAll()
                    self._maskSelect.clearAll()
                    return
                except:
                    wait.close()
                    messageBox(self,
                               'QSM map processing',
                               text='QSM map processing failed.')
                    return
                r.setFilename(img.getFilename())
                r.setFilenamePrefix(prefix)
                r.setFilenameSuffix(suffix)
                if prefix == '' and suffix == '': suffix = r.acquisition.QSM
                r.save()
                wait.addInformationText('Save {}...'.format(r.getBasename()))
                wait.setCurrentProgressValue(i)
                if wait.getStopped(): break
            wait.close()
            """
            Exit  
            """
            r = messageBox(self,
                           self.windowTitle(),
                           'Would you like to process\nadditional QSM map(s) ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                self._select.clearAll()
                self._maskSelect.clearAll()
            else: self.accept()