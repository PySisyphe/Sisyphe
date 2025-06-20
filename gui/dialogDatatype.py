"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import basename
from os.path import splitext
from os.path import exists

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheConstants import getDatatypes
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheMesh import SisypheMesh
from Sisyphe.core.sisypheTracts import SisypheStreamlines
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.selectFileWidgets import FilesSelectionWidget
from Sisyphe.widgets.selectFileWidgets import MultiExtFilesSelectionWidget
from Sisyphe.widgets.functionsSettingsWidget import DialogSettingsWidget

__all__ = ['DialogDatatype',
           'DialogAttributes',
           'DialogEditID']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogDatatype
              -> DialogAttributes
              -> DialogEditID
"""


class DialogDatatype(QDialog):
    """
    DialogDatatype

    Description
    ~~~~~~~~~~~

    GUI dialog window for datatype conversion.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDatatype
    """

    # Special method

    """
    Private attributes

    _files      FilesSelectionWidget
    _datatype   LabeledComboBox
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Datatype conversion')
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

        # Files selection widgets

        self._files = FilesSelectionWidget()
        self._files.setMaximumNumberOfFiles(500)
        self._files.filterSisypheVolume()
        self._files.setCurrentVolumeButtonVisibility(False)
        self._layout.addWidget(self._files)

        # Datatype selection widget

        lyout = QHBoxLayout()
        self._datatype = LabeledComboBox()
        self._datatype.setFixedWidth(200)
        self._datatype.setTitle('Datatype')
        self._datatype.addItems(getDatatypes())
        lyout.addStretch()
        lyout.addWidget(self._datatype)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Init default dialog buttons

        lyout = QHBoxLayout()
        if platform == 'win32': lyout.setContentsMargins(10, 10, 10, 10)
        lyout.setSpacing(10)
        lyout.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        self._execute = QPushButton('Convert')
        self._execute.setToolTip('Execute datatype conversion.')
        lyout.addWidget(ok)
        lyout.addWidget(self._execute)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

    # Public methods

    def getFileSelectionWidget(self):
        return self._files

    def execute(self):
        n = self._files.filenamesCount()
        if n > 0:
            title = 'Datatype conversion'
            wait = DialogWait(title=title, progress=True, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=False)
            wait.open()
            dtype = self._datatype.currentText()
            for filename in self._files.getFilenames():
                wait.setInformationText('Convert {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                v = SisypheVolume()
                if exists(filename):
                    try:
                        v.load(filename)
                        if v.getDatatype() != dtype:
                            v2 = v.cast(dtype)
                            v2.setFilename(v.getFilename())
                            v2.setFilenameSuffix(dtype)
                            v2.save()
                    except Exception as err:
                        messageBox(self, title, '{}'.format(err))
            wait.close()
            self._files.clearall()


class DialogAttributes(DialogDatatype):
    """
    DialogAttributes

    Description
    ~~~~~~~~~~~

    GUI dialog window for attributes conversion.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDatatype -> DialogAttributes
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Attributes conversion')
        self._execute.setToolTip('Execute attributes conversion.')
        self._datatype.setVisible(False)

        self._attributes = DialogSettingsWidget('Attributes')
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._attributes, c)
        self._attributes.hideButtons()
        self._attributes.hideIOButtons()
        self._attributes.settingsVisibilityOn()
        editModality = self._attributes.getParameterWidget('SetModality')
        editSequence = self._attributes.getParameterWidget('SetSequence')
        editUnit = self._attributes.getParameterWidget('SetUnit')
        editFrame = self._attributes.getParameterWidget('SetFrame')
        modality = self._attributes.getParameterWidget('Modality')
        ot = self._attributes.getParameterWidget('OT')
        mr = self._attributes.getParameterWidget('MR')
        ct = self._attributes.getParameterWidget('CT')
        nm = self._attributes.getParameterWidget('NM')
        pt = self._attributes.getParameterWidget('PT')
        tp = self._attributes.getParameterWidget('TP')
        unit = self._attributes.getParameterWidget('Unit')
        frame = self._attributes.getParameterWidget('Frame')
        modality.clear()
        ot.clear()
        mr.clear()
        ct.clear()
        nm.clear()
        pt.clear()
        tp.clear()
        unit.clear()
        frame.clear()
        modality.addItems(list(SisypheAcquisition.getModalityToCodeDict().keys()))
        ot.addItems(SisypheAcquisition.getOTSequences()[1:])
        mr.addItems(SisypheAcquisition.getMRSequences()[1:])
        ct.addItems(SisypheAcquisition.getCTSequences()[1:])
        nm.addItems(SisypheAcquisition.getNMSequences()[1:])
        pt.addItems(SisypheAcquisition.getPTSequences()[1:])
        tp.addItems(SisypheAcquisition.getTPSequences()[1:])
        unit.addItems(SisypheAcquisition.getUnitList())
        frame.addItems(SisypheAcquisition.getFrameList()[1:])
        self._attributes.setParameterVisibility('Modality', editModality.isVisible())
        self._attributes.setParameterVisibility('OT', False)
        self._attributes.setParameterVisibility('MR', False)
        self._attributes.setParameterVisibility('CT', False)
        self._attributes.setParameterVisibility('NM', False)
        self._attributes.setParameterVisibility('PT', False)
        self._attributes.setParameterVisibility('TP', False)
        self._attributes.setParameterVisibility('LB', False)
        if editSequence.isVisible():
            self._attributes.setParameterVisibility(modality.currentText(), True)
        self._attributes.setParameterVisibility('Unit', editUnit.isVisible())
        self._attributes.setParameterVisibility('Frame', editFrame.isVisible())

        # noinspection PyUnresolvedReferences
        self.layout().insertWidget(2, self._attributes)

        editModality.stateChanged.connect(lambda state: self._attributes.setParameterVisibility('Modality', state > 0))
        editSequence.stateChanged.connect(self._sequenceVisibility)
        editUnit.stateChanged.connect(lambda state: self._attributes.setParameterVisibility('Unit', state > 0))
        editFrame.stateChanged.connect(lambda state: self._attributes.setParameterVisibility('Frame', state > 0))
        modality.currentIndexChanged.connect(self._sequenceVisibility)

    # Private method

    def _sequenceVisibility(self):
        self._attributes.setParameterVisibility('OT', False)
        self._attributes.setParameterVisibility('MR', False)
        self._attributes.setParameterVisibility('CT', False)
        self._attributes.setParameterVisibility('NM', False)
        self._attributes.setParameterVisibility('PT', False)
        self._attributes.setParameterVisibility('TP', False)
        self._attributes.setParameterVisibility('LB', False)
        if self._attributes.getParameterWidget('SetSequence').checkState() > 0:
            self._attributes.setParameterVisibility(self._attributes.getParameterWidget('Modality').currentText(), True)

    # Public method

    def execute(self):
        n = self._files.filenamesCount()
        if n > 0:
            title = 'Attributes conversion'
            wait = DialogWait(title=title, progress=True, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=False)
            wait.open()
            for filename in self._files.getFilenames():
                wait.setInformationText('Convert {}'.format(basename(filename)))
                wait.incCurrentProgressValue()
                v = SisypheVolume()
                if exists(filename):
                    try:
                        v.load(filename)
                        if self._attributes.getParameterWidget('Anonymize').checkState() > 0:
                            v.identity.anonymize()
                        if self._attributes.getParameterWidget('SetModality').checkState() > 0:
                            v.acquisition.setModality(self._attributes.getParameterValue('Modality')[0])
                        if self._attributes.getParameterWidget('SetSequence').checkState() > 0:
                            if v.acquisition.isOT(): v.acquisition.setSequence(self._attributes.getParameterValue('OT')[0])
                            elif v.acquisition.isMR(): v.acquisition.setSequence(self._attributes.getParameterValue('MR')[0])
                            elif v.acquisition.isNM(): v.acquisition.setSequence(self._attributes.getParameterValue('NM')[0])
                            elif v.acquisition.isPT(): v.acquisition.setSequence(self._attributes.getParameterValue('PT')[0])
                            elif v.acquisition.isTP(): v.acquisition.setSequence(self._attributes.getParameterValue('TP')[0])
                        if self._attributes.getParameterWidget('SetUnit').checkState() > 0:
                            v.acquisition.setUnit(self._attributes.getParameterValue('Unit')[0])
                        if self._attributes.getParameterWidget('SetFrame').checkState() > 0:
                            v.acquisition.setFrameAsString(self._attributes.getParameterValue('Frame')[0])
                        if self._attributes.getParameterWidget('SetOrigin').checkState() > 0:
                            v.setDefaultOrigin()
                        if self._attributes.getParameterWidget('SetDirections').checkState() > 0:
                            v.setDirections()
                        v.save()
                    except Exception as err:
                        messageBox(self, title, '{}'.format(err))
                        break
            wait.close()
            self._files.clearall()

class DialogEditID(QDialog):
    """
    DialogEditID

    Description
    ~~~~~~~~~~~

    GUI dialog window to edit ID.

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogEditID
    """

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('ID replacement')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumWidth(int(screen.width() * 0.33))
        self.setSizeGripEnabled(False)

        # attributes

        self._refid: str | None = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Reference selection

        self._ref = FileSelectionWidget(parent=self)
        self._ref.filterSisypheVolume()
        self._ref.FieldChanged.connect(self._refChanged)
        self._layout.addWidget(self._ref)

        # Files selection widgets

        self._files = MultiExtFilesSelectionWidget(parent=self)
        self._files.setMaximumNumberOfFiles(500)
        self._files.filterSisypheVolume()
        self._files.filterSisypheROI()
        self._files.filterSisypheMesh()
        self._files.filterSisypheStreamlines()
        self._files.setCurrentVolumeButtonVisibility(False)
        self._files.setEnabled(False)
        self._files.FieldChanged.connect(self._filesChanged)
        self._layout.addWidget(self._files)

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
        self._execute.setToolTip('Execute ID replacement.')
        lyout.addWidget(ok)
        lyout.addWidget(self._execute)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        # Qt Signals

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self._execute.clicked.connect(self.execute)

    # Private methods

    def _refChanged(self):
        self._files.clear()
        if not self._ref.isEmpty():
            filename = self._ref.getFilename()
            attr = SisypheVolume.getVolumeAttributes(filename)
            if exists(filename):
                self._refid = attr['id']
                self._files.filterSameSize(tuple(attr['size']))
                self._files.filterSameFOV(tuple(attr['fov']))
                self._files.setEnabled(True)
        else:
            self._refid = None
            self._execute.setEnabled(False)
            self._files.setEnabled(False)

    def _filesChanged(self):
        self._execute.setEnabled(not self._files.isEmpty())

    # Public method

    def execute(self):
        n = self._files.filenamesCount()
        if n > 0:
            title = 'ID replacement'
            wait = DialogWait(title=title, progress=True, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=False)
            wait.open()
            for filename in self._files.getFilenames():
                wait.setInformationText('{} ID replacement'.format(basename(filename)))
                wait.incCurrentProgressValue()
                if exists(filename):
                    ext = splitext(filename)[1]
                    if ext == SisypheVolume.getFileExt():
                        v = SisypheVolume()
                        v.load(filename)
                        v.setID(self._refid)
                        v.save()
                    elif ext == SisypheROI.getFileExt():
                        v = SisypheROI()
                        v.load(filename)
                        v.setReferenceID(self._refid)
                        v.save()
                    elif ext == SisypheMesh.getFileExt():
                        v = SisypheMesh()
                        v.load(filename)
                        v.setReferenceID(self._refid)
                        v.save()
                    elif ext == SisypheStreamlines.getFileExt():
                        v = SisypheStreamlines()
                        v.load(filename)
                        v.setReferenceID(self._refid)
                        v.save()
            wait.close()
            self._ref.clear()
            self._files.clear()