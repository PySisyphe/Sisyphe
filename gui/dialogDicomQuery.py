"""
External packages/modules
-------------------------

    - pydicom, DICOM library, https://pydicom.github.io/pydicom/stable/
    - pynetdicom, DICOM networking protocol library, https://pydicom.github.io/pynetdicom/stable/index.html
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from sys import platform

from os import mkdir

from os.path import join
from os.path import exists
from os.path import expanduser

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QApplication

from pydicom import Dataset
# from pydicom import dcmread as read_file

from pynetdicom import AE
from pynetdicom import evt
from pynetdicom import build_role
from pynetdicom import PYNETDICOM_IMPLEMENTATION_UID
from pynetdicom import PYNETDICOM_IMPLEMENTATION_VERSION
from pynetdicom import StoragePresentationContexts
from pynetdicom.pdu_primitives import UserIdentityNegotiation
# noinspection PyUnresolvedReferences
from pynetdicom.sop_class import Verification
# noinspection PyUnresolvedReferences
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind
# noinspection PyUnresolvedReferences
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelGet

from Sisyphe.core.sisypheSettings import initPySisypheUserPath
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.functionsSettingsWidget import SettingsWidget
from Sisyphe.widgets.basicWidgets import LabeledLineEdit
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogDicomQueryRetrieve
"""

_all__ = ['DialogDicomQueryRetrieve']


def getDicomDirectory():
    userdir = join(expanduser('~'), '.PySisyphe')
    if not exists(userdir): initPySisypheUserPath()
    dcmdir = join(userdir, 'dicom')
    if not exists(dcmdir): mkdir(dcmdir)
    return dcmdir


def handle_store(event):
    ds = event.dataset
    context = event.context
    meta = Dataset()
    meta.MediaStorageSOPClassUID = ds.SOPClassUID
    meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
    meta.ImplementationClassUID = PYNETDICOM_IMPLEMENTATION_UID
    meta.ImplementationVersionName = PYNETDICOM_IMPLEMENTATION_VERSION
    meta.TransferSyntaxUID = context.transfer_syntax
    ds.file_meta = meta
    ds.is_little_endian = context.transfer_syntax.is_little_endian
    ds.is_implicit_VR = context.transfer_syntax.is_implicit_VR
    filename = ds.SOPInstanceUID + '.dcm'
    ds.save_as(join(DialogDicomQueryRetrieve.getDicomFolder(), filename), write_like_original=False)
    return 0x0000


class DialogDicomQueryRetrieve(QDialog):
    """
    DialogDicomQueryRetrieve

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogDicomQueryRetrieve

    Creation: 02/08/2025
    Last revision: 03/08/2025
    """

    _FOLDER = ''

    # Class method

    @classmethod
    def getDicomFolder(cls):
        return cls._FOLDER

    # Special method

    """
    Private attributes

    _wait       DialogWait
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('DICOM Query Retrieve')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.50), int(screen.height() * 0.50))

        self._wait = DialogWait()

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

        # Init widgets

        self._lastname = LabeledLineEdit('Lastname', parent=self)
        self._firstname = LabeledLineEdit('Firstname', parent=self)
        self._cdob = QCheckBox('Date of birth', parent=self)
        self._cdob.setChecked(False)
        self._dob = QDateEdit(parent=self)
        self._dob.setMinimumDate(QDate(1900, 1, 1))
        self._dob.setMaximumDate(QDate.currentDate())
        self._dob.clear()
        self._dob.setEnabled(False)
        # noinspection PyUnresolvedReferences
        self._cdob.stateChanged.connect(self._dob.setEnabled)
        self._modality = LabeledComboBox('Modality', parent=self)
        self._modality.addItems(['*', 'CT', 'MR', 'NM', 'OT', 'PT'])
        self._modality.setCurrentIndex(0)
        self._cdstudy = QCheckBox('Modality date', parent=self)
        self._cdstudy.setChecked(False)
        self._dstudy = QDateEdit(parent=self)
        self._dstudy.setMinimumDate(QDate(2000, 1, 1))
        self._dstudy.setMaximumDate(QDate.currentDate())
        self._dstudy.setDate(QDate.currentDate())
        self._dstudy.setEnabled(False)
        # noinspection PyUnresolvedReferences
        self._cdstudy.stateChanged.connect(self._dstudy.setEnabled)
        self._search = QPushButton('Search')
        # noinspection PyUnresolvedReferences
        self._search.clicked.connect(self._getStudy)

        self._study = QTreeWidget(parent=self)
        self._study.setAlternatingRowColors(True)
        self._study.setSelectionMode(1)
        self._study.setSelectionBehavior(1)
        self._study.setHeaderLabels(['Accession Number', 'Lastname', 'Firstname', 'Date of birth',
                                     'Modality', 'Study Date', 'Description'])
        self._study.setSortingEnabled(True)
        # noinspection PyUnresolvedReferences
        self._study.itemSelectionChanged.connect(self._getSeries)
        self._study.setToolTip('Select a study to retrieve its series below')

        self._series = QTreeWidget(parent=self)
        self._series.setAlternatingRowColors(True)
        self._series.setSelectionMode(3)
        self._series.setSelectionBehavior(1)
        self._series.setHeaderLabels(['Series Number', 'Description'])
        self._series.setToolTip('Check the series to be retrieved by pressing the import button below.')

        self._settings = SettingsWidget('DicomHost', parent=self)
        self._settings.settingsVisibilityOff()
        self._settings.setIOButtonsVisibility(False)
        self._settings.setSettingsButtonText('DICOM SCP Host settings')
        self._settings.setParameterVisibility('DicomFolder', False)
        w = self._settings.getParameterWidget('Login')
        self._loginVisibility()
        # noinspection PyUnresolvedReferences
        w.stateChanged.connect(self._loginVisibility)
        self._settings.VisibilityToggled.connect(self._center)
        self._aet = self._settings.getParameterValue('AET')
        self._url = self._settings.getParameterValue('URL')
        self._port = self._settings.getParameterValue('Port')
        self._username = bytes(self._settings.getParameterValue('Username'), 'utf-8')
        self._password = bytes(self._settings.getParameterValue('Password'), 'utf-8')

        lyout1 = QHBoxLayout()
        lyout1.setSpacing(10)
        lyout1.addWidget(self._lastname)
        lyout1.addWidget(self._firstname)
        lyout1.addWidget(self._cdob)
        lyout1.addWidget(self._dob)
        lyout1.addWidget(self._modality)
        lyout1.addWidget(self._cdstudy)
        lyout1.addWidget(self._dstudy)
        lyout1.addWidget(self._search)
        self._layout.addLayout(lyout1)

        self._folder = FileSelectionWidget(parent=self)
        self._folder.setTextLabel('DICOM folder')
        self._folder.filterDirectory()
        folder = self._settings.getParameterValue('DicomFolder')
        if exists(folder): self._folder.open(folder)
        else: self._folder.open(getDicomDirectory())
        self._folder.FieldCleared.connect(lambda _, default=getDicomDirectory(): self._folder.open(default))
        self._FOLDER = self._folder.getFilename()

        lyout2 = QVBoxLayout()
        lyout2.setSpacing(2)
        lyout2.addWidget(self._study)
        lyout2.addWidget(self._series)
        lyout2.addWidget(self._folder)
        lyout2.addWidget(self._settings)
        self._layout.addLayout(lyout2)

        # Init default dialog buttons

        lyout3 = QHBoxLayout()
        if platform == 'win32': lyout3.setContentsMargins(10, 10, 10, 10)
        lyout3.setSpacing(10)
        lyout3.setDirection(QHBoxLayout.RightToLeft)
        ok = QPushButton('Close')
        ok.setFixedWidth(100)
        ok.setAutoDefault(True)
        ok.setDefault(True)
        go = QPushButton('Import')
        go.setToolTip('Retrieve the checked series from the list above.')
        lyout3.addWidget(ok)
        lyout3.addWidget(go)
        lyout3.addStretch()
        self._layout.addLayout(lyout3)

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)
        # noinspection PyUnresolvedReferences
        go.clicked.connect(self._import)

    # Private methods

    # noinspection PyUnusedLocal
    def _center(self, widget):
        self._settings.adjustSize()
        QApplication.processEvents()
        self.adjustSize()
        QApplication.processEvents()
        self.move(self.screen().availableGeometry().center() - self.rect().center())
        QApplication.processEvents()

    def _loginVisibility(self):
        v = self._settings.getParameterValue('Login')
        self._settings.setParameterVisibility('Username', v)
        self._settings.setParameterVisibility('Password', v)

    def _getStudy(self):
        self._study.clear()
        self._series.clear()
        tag = False
        tag = tag or self._lastname.getEditText() != ''
        tag = tag or self._firstname.getEditText() != ''
        tag = tag or self._modality.currentText() != '*'
        if self._cdob.isChecked():
            d = self._dob.date()
            tag = tag or d.isValid()
        if self._cdstudy.isChecked():
            d = self._dstudy.date()
            tag = tag or d.isValid()
        if tag:
            self._aet = self._settings.getParameterValue('AET')
            self._url = self._settings.getParameterValue('URL')
            self._port = self._settings.getParameterValue('Port')
            self._username = bytes(self._settings.getParameterValue('Username'), 'utf-8')
            self._password = bytes(self._settings.getParameterValue('Password'), 'utf-8')
            ae = AE()
            ae.add_requested_context(Verification)
            ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)
            if self._settings.getParameterValue('Login'):
                negotiation_items = list()
                login = UserIdentityNegotiation()
                login.user_identity_type = 2
                login.primary_field = self._username
                login.secondary_field = self._password
                negotiation_items.append(login)
                connect = ae.associate(self._url, self._port, ae_title=self._aet, ext_neg=negotiation_items)
            else:
                connect = ae.associate(self._url, self._port, ae_title=self._aet)
            if connect.is_established:
                if connect.is_alive():
                    # Search dataset
                    ds = Dataset()
                    name = '^'.join([self._lastname.getEditText(), self._firstname.getEditText()])
                    if name == '^': name = '*'
                    elif name[-1] == '^' or name[-1] == '^': name = name.replace('^', '')
                    ds.PatientName = name
                    if not self._cdob.isChecked(): ds.PatientBirthDate = '*'
                    else:
                        if self._dob.date().isValid(): ds.PatientBirthDate = self._dob.date().toString('yyyyMMdd')
                        else: ds.PatientBirthDate = '*'
                    if self._modality.currentIndex() > 0:
                        # ds.Modality = self._modality.currentText()
                        ds.ModalitiesInStudy = [self._modality.currentText()]
                    if not self._cdstudy.isChecked(): ds.StudyDate = '*'
                    else:
                        if self._dstudy.date().isValid(): ds.StudyDate = self._dstudy.date().toString('yyyyMMdd')
                        else: ds.StudyDate = '*'
                    ds.StudyDescription = '*'
                    ds.QueryRetrieveLevel = 'STUDY'
                    ds.AccessionNumber = '*'
                    ds.StudyInstanceUID = '*'
                    r = connect.send_c_find(ds, StudyRootQueryRetrieveInformationModelFind)
                    empty = True
                    for (status, dsitem) in r:
                        if status is not None:
                            if status.Status in (0xFF00, 0xFF01):
                                item = QTreeWidgetItem()
                                item.setData(0, Qt.UserRole, dsitem.StudyInstanceUID)
                                if 'AccessionNumber' in dsitem:
                                    item.setText(0, dsitem.AccessionNumber)
                                if 'PatientName' in dsitem:
                                    name = str(dsitem.PatientName)
                                    if '^' in name: last, first = name.split('^')
                                    else: last, first = name, ''
                                    item.setText(1, last)
                                    item.setText(2, first)
                                if 'PatientBirthDate' in dsitem:
                                    item.setText(3, dsitem.PatientBirthDate)
                                if 'ModalitiesInStudy' in dsitem:
                                    n = dsitem['ModalitiesInStudy'].VM
                                    if n == 1: item.setText(4, dsitem.ModalitiesInStudy)
                                    elif n > 1: item.setText(4, ' '.join(dsitem.ModalitiesInStudy))
                                if 'StudyDate' in dsitem:
                                    item.setText(5, dsitem.StudyDate)
                                if 'StudyDescription' in dsitem:
                                    item.setText(6, dsitem.StudyDescription)
                                self._study.addTopLevelItem(item)
                                empty = False
                            elif status.Status == 0:
                                if empty:
                                    messageBox(self,
                                               title=self.windowTitle(),
                                               text='No matching dataset was found.')
                                else:
                                    # noinspection PyTypeChecker
                                    self._study.sortItems(5, 1)
                                break
                            else:
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Connection to {} DICOM SCP host timed out, '
                                                'was aborted or received invalid response'.format(self._url))
                    connect.release()
            elif connect.is_rejected:
                messageBox(self,
                           title=self.windowTitle(),
                           text='Connection to {} DICOM SCP host rejected'.format(self._url))
            elif connect.is_aborted:
                messageBox(self,
                           title=self.windowTitle(),
                           text='Connection to {} DICOM SCP host aborted'.format(self._url))
            else:
                messageBox(self,
                           title=self.windowTitle(),
                           text='Connection to {} DICOM SCP host failed'.format(self._url))
        else:
            messageBox(self,
                       title=self.windowTitle(),
                       text='No filter criteria specified.')

    def _getSeries(self):
        self._series.clear()
        items = self._study.selectedItems()
        if len(items) > 0:
            item = items[0]
            self._aet = self._settings.getParameterValue('AET')
            self._url = self._settings.getParameterValue('URL')
            self._port = self._settings.getParameterValue('Port')
            self._username = bytes(self._settings.getParameterValue('Username'), 'utf-8')
            self._password = bytes(self._settings.getParameterValue('Password'), 'utf-8')
            ae = AE()
            ae.add_requested_context(Verification)
            ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)
            if self._settings.getParameterValue('Login'):
                negotiation_items = list()
                login = UserIdentityNegotiation()
                login.user_identity_type = 2
                login.primary_field = self._username
                login.secondary_field = self._password
                negotiation_items.append(login)
                connect = ae.associate(self._url, self._port, ae_title=self._aet, ext_neg=negotiation_items)
            else:
                connect = ae.associate(self._url, self._port, ae_title=self._aet)
            if connect.is_established:
                if connect.is_alive():
                    # Search dataset
                    ds = Dataset()
                    ds.StudyInstanceUID = item.data(0, Qt.UserRole)
                    ds.SeriesInstanceUID = '*'
                    ds.SeriesNumber = None
                    if self._modality.currentIndex() == 0: ds.Modality = '*'
                    else: ds.Modality = self._modality.currentText()
                    ds.SeriesDescription = '*'
                    ds.QueryRetrieveLevel = 'SERIES'
                    r = connect.send_c_find(ds, StudyRootQueryRetrieveInformationModelFind)
                    for (status, dsitem) in r:
                        if status is not None:
                            if status.Status in (0xFF00, 0xFF01):
                                item = QTreeWidgetItem()
                                item.setCheckState(0, Qt.Unchecked)
                                item.setData(0, Qt.UserRole, dsitem.SeriesInstanceUID)
                                if 'SeriesNumber' in dsitem:
                                    item.setText(0, str(dsitem.SeriesNumber))
                                if 'SeriesDescription' in dsitem:
                                    item.setText(1, dsitem.SeriesDescription)
                                self._series.addTopLevelItem(item)
                            elif status.Status == 0:
                                break
                            else:
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Connection to {} DICOM SCP host timed out, '
                                                'was aborted or received invalid response'.format(self._url))
                    connect.release()
            elif connect.is_rejected:
                messageBox(self,
                           title=self.windowTitle(),
                           text='Connection to {} DICOM SCP host rejected'.format(self._url))
            elif connect.is_aborted:
                messageBox(self,
                           title=self.windowTitle(),
                           text='Connection to {} DICOM SCP host aborted'.format(self._url))
            else:
                messageBox(self,
                           title=self.windowTitle(),
                           text='Connection to {} DICOM SCP host failed'.format(self._url))

    def _import(self):
        items = self._study.selectedItems()
        if len(items) > 0:
            item = items[0]
            studyuid = item.data(0, Qt.UserRole)
        else: return
        for i in range(self._series.topLevelItemCount()):
            item = self._series.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                seriesuid = item.data(0, Qt.UserRole)
                description = item.text(1)
                self._aet = self._settings.getParameterValue('AET')
                self._url = self._settings.getParameterValue('URL')
                self._port = self._settings.getParameterValue('Port')
                self._username = bytes(self._settings.getParameterValue('Username'), 'utf-8')
                self._password = bytes(self._settings.getParameterValue('Password'), 'utf-8')
                ae = AE()
                ae.requested_contexts = StoragePresentationContexts
                ae.add_requested_context(StudyRootQueryRetrieveInformationModelGet)
                negotiation_items = list()
                for context in StoragePresentationContexts:
                    role = build_role(context.abstract_syntax, scp_role=True, scu_role=True)
                    negotiation_items.append(role)
                if self._settings.getParameterValue('Login'):
                    login = UserIdentityNegotiation()
                    login.user_identity_type = 2
                    login.primary_field = self._username
                    login.secondary_field = self._password
                    negotiation_items.append(login)
                handlers = [(evt.EVT_C_STORE, handle_store)]
                connect = ae.associate(self._url,
                                       self._port,
                                       ae_title=self._aet,
                                       ext_neg=negotiation_items,
                                       evt_handlers=handlers)
                if connect.is_established:
                    if connect.is_alive():
                        # Search dataset
                        ds = Dataset()
                        ds.QueryRetrieveLevel = 'SERIES'
                        ds.StudyInstanceUID = studyuid
                        ds.SeriesInstanceUID = seriesuid
                        r = connect.send_c_get(ds, StudyRootQueryRetrieveInformationModelGet)
                        ninstances = 0
                        if not self._wait.isVisible():
                            self._wait.open()
                            self._wait.setInformationText('Retreive {} from {} DICOM SCP host'.format(description, self._aet))
                        for (dsitem, _) in r:
                            if dsitem is not None:
                                if (0x000, 0x1020) in dsitem:
                                    if ninstances == 0:
                                        ninstances = dsitem[0x000, 0x1020].value + 1
                                        self._wait.setProgressRange(1, ninstances)
                                        self._wait.setCurrentProgressValue(1)
                                        self._wait.setProgressVisibility(True)
                                    else: self._wait.incCurrentProgressValue()
                            else:
                                messageBox(self,
                                           title=self.windowTitle(),
                                           text='Connection to {} DICOM SCP host timed out, '
                                                'was aborted or received invalid response'.format(self._url))
                        self._wait.hide()
                        item.setCheckState(0, Qt.Unchecked)
                        connect.release()
                elif connect.is_rejected:
                    messageBox(self,
                               title=self.windowTitle(),
                               text='Connection to {} DICOM SCP host rejected'.format(self._url))
                elif connect.is_aborted:
                    messageBox(self,
                               title=self.windowTitle(),
                               text='Connection to {} DICOM SCP host aborted'.format(self._url))
                else:
                    messageBox(self,
                               title=self.windowTitle(),
                               text='Connection to {} DICOM SCP host failed'.format(self._url))


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main = DialogDicomQueryRetrieve()
    main.open()
    sys.exit(app.exec_())
