"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from dateutil.relativedelta import relativedelta

from os.path import join
from os.path import basename
from os.path import splitext

from re import findall

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheSheet import SisypheSheet
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.functionsSettingsWidget import DialogSettingsWidget
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

    Last revision: 06/11/2026
    """

    # Special method

    """
    Private attributes

    _ioformat   str, import format (nifti, minc, nrrd, vtk, npy)
    """

    # noinspection unresolved-references
    def __init__(self, io='Nifti', parent=None):
        super().__init__(parent)

        self._ioformat = io
        self.setWindowTitle('{} import'.format(io))
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.50), int(screen.height() * 0.66))

        # < Revision 06/10/2026
        self._compress = False
        # Revision 06/10/2026 >

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._files = FilesSelectionWidget()
        self._files.setMaximumNumberOfFiles(10000)
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
        self._convert.clicked.connect(self.convert)
        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.addWidget(self._savedir)
        layout.addWidget(self._convert)
        self._layout.addLayout(layout)

        # < Revision 26/10/2026
        self._settings = DialogSettingsWidget('Import')
        self._settings.hideButtons()
        self._settings.hideIOButtons()
        self._settings.settingsVisibilityOn()
        self._saveas = self._settings.getParameterWidget('Name')
        self._search = self._settings.getParameterWidget('Search')
        self._replace = self._settings.getParameterWidget('Replace')
        self._suffix = self._settings.getParameterWidget('Suffix')
        self._prefix = self._settings.getParameterWidget('Prefix')
        self._sep = self._settings.getParameterWidget('Separator')
        self._numbers = self._settings.getParameterWidget('Numbers')
        self._datatype = self._settings.getParameterWidget('Datatype')
        self._modality = self._settings.getParameterWidget('Modality')
        self._sequence = self._settings.getParameterWidget('Sequence')
        self._origin = self._settings.getParameterWidget('Origin')
        self._directions = self._settings.getParameterWidget('Directions')
        self._lut = self._settings.getParameterWidget('LUT')
        # < Revision 28/10/2026
        self._file = self._settings.getParameterWidget('File')
        # Revision 28/10/2026 >
        self._nameChanged(0)
        self._setSequencesFromModality(0)
        # < Revision 28/10/2026
        self._fileChanged()
        # Revision 28/10/2026 >
        self._saveas.currentIndexChanged.connect(self._nameChanged)
        self._modality.currentIndexChanged.connect(self._setSequencesFromModality)
        self._file.FieldChanged.connect(self._fileChanged)
        # < Revision 03/11/2026
        # self._layout.addWidget(self._settings)
        self._area = QScrollArea()
        self._area.setWidget(self._settings)
        self._area.setFrameShape(QScrollArea.NoFrame)
        self._area.setAlignment(Qt.AlignHCenter)
        self._area.setWidgetResizable(True)
        self._layout.addWidget(self._area)
        # Revision 03/11/2026 >
        # Revision 26/10/2026 >

        # < Revision 30/10/2026
        # tooltips
        self._file.setToolTip('Select a file (*.csv or *.xlsx) with one\n'
                              'or more of the following features: date\n'
                              'of acquisition, date of birth, age, gender.')
        # Revision 30/10/2026 >

        # Init default dialog buttons

        layout = QHBoxLayout()
        if platform == 'win32' or platform == 'linux': layout.setContentsMargins(10, 10, 10, 10)
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

        self.setModal(True)

    # Private method

    # < Revision 26/10/2026
    # add _nameChanged method
    def _nameChanged(self, index: int) -> None:
        if index == 0:
            self._settings.setParameterVisibility('Search', False)
            self._settings.setParameterVisibility('Replace', False)
            self._settings.setParameterVisibility('Numbers', False)
            self._settings.setParameterVisibility('Separator', False)
            self._settings.setParameterVisibility('Prefix', False)
            self._settings.setParameterVisibility('Suffix', False)
        elif index == 1:
            self._settings.setParameterVisibility('Search', True)
            self._settings.setParameterVisibility('Replace', True)
            self._settings.setParameterVisibility('Numbers', False)
            self._settings.setParameterVisibility('Separator', False)
            self._settings.setParameterVisibility('Prefix', False)
            self._settings.setParameterVisibility('Suffix', False)
        elif index == 2:
            self._settings.setParameterVisibility('Search', False)
            self._settings.setParameterVisibility('Replace', False)
            self._settings.setParameterVisibility('Numbers', False)
            self._settings.setParameterVisibility('Separator', False)
            self._settings.setParameterVisibility('Prefix', True)
            self._settings.setParameterVisibility('Suffix', False)
        elif index == 3:
            self._settings.setParameterVisibility('Search', False)
            self._settings.setParameterVisibility('Replace', False)
            self._settings.setParameterVisibility('Numbers', True)
            self._settings.setParameterVisibility('Separator', True)
            self._settings.setParameterVisibility('Prefix', True)
            self._settings.setParameterVisibility('Suffix', True)
    # Revision 26/10/2026 >

    # < Revision 26/10/2026
    # add _nameChanged method
    def _setSequencesFromModality(self, index: int) -> None:
        self._sequence.clear()
        # OT
        if index == 0: items = SisypheAcquisition.getOTSequences()
        # CT
        elif index == 1: items = SisypheAcquisition.getCTSequences()
        # MR
        elif index == 2: items = SisypheAcquisition.getMRSequences()
        # NM
        elif index == 3: items = SisypheAcquisition.getNMSequences()
        # PT
        elif index == 4: items = SisypheAcquisition.getPTSequences()
        # TP
        elif index == 5:
            items = list(SisypheAcquisition.getOTSequences())
            items += list(SisypheAcquisition.getMRSequences())
            items += list(SisypheAcquisition.getCTSequences())
            items += list(SisypheAcquisition.getPTSequences())
            items += list(SisypheAcquisition.getNMSequences())
        else: items = SisypheAcquisition.getOTSequences()
        for item in items:
            self._sequence.addItem(item)
        self._sequence.setCurrentIndex(0)
    # Revision 26/10/2026 >

    # < Revision 28/10/2026
    # add _fileChanged method
    def _fileChanged(self) -> None:
        v = not self._file.isEmpty()
        self._settings.setParameterVisibility('Code', v)
        self._settings.setParameterVisibility('Column', v)
        self._settings.setParameterVisibility('Scan', v)
        self._settings.setParameterVisibility('Birth', v)
        self._settings.setParameterVisibility('Date', v)
        self._settings.setParameterVisibility('Age', v)
        self._settings.setParameterVisibility('Gender', v)
        self._settings.setParameterVisibility('Male', v)
        self._settings.setParameterVisibility('Female', v)
        if v:
            filename = self._file.getFilename()
            ext = splitext(filename)[1]
            try:
                if ext == '.csv': df = SisypheSheet.loadCSV(filename)
                elif ext == '.xlsx': df = SisypheSheet.loadXLSX(filename)
                else: df = ''
            except: return
            self._file.setToolTip(str(df))
    # Revision 28/10/2026 >

    # Public method

    # < Revision 06/10/2026
    # add setCompression method
    def setCompression(self, compress: bool = True):
        self._compress = compress
    # Revision 06/10/2026 >

    def convert(self):
        filenames = self._files.getFilenames()
        if filenames is not None:
            n = len(filenames)
            if n > 0:
                # < Revision 28/10/2026
                ccode = self._settings.getParameterValue('Column')
                cpos = self._settings.getParameterWidget('Code').currentIndex()
                cdos = self._settings.getParameterValue('Scan')
                cdob = self._settings.getParameterValue('Birth')
                cage = self._settings.getParameterValue('Age')
                cgender = self._settings.getParameterValue('Gender')
                cmale = self._settings.getParameterValue('Male')
                cfemale = self._settings.getParameterValue('Female')
                fdate = self._settings.getParameterWidget('Date').currentText()
                fdate = fdate.replace('dd', '%d')
                fdate = fdate.replace('mm', '%m')
                fdate = fdate.replace('yyyy', '%Y')
                df = None
                if not self._file.isEmpty():
                    filename = self._file.getFilename()
                    ext = splitext(filename)[1]
                    try:
                        if ext == '.csv': df = SisypheSheet.loadCSV(filename)
                        elif ext == '.xlsx': df = SisypheSheet.loadXLSX(filename)
                    except: pass
                # Revision 28/10/2026 >
                # Set ProgressBar
                progress = DialogWait(title='{} import'.format(self._ioformat),
                                      progressmin=0, progressmax=n, progresstxt=True, cancel=True)
                # < Revision 19/02/2026
                progress.setCurrentProgressValue(0)
                # Revision 19/02/2026 >
                progress.setProgressVisibility(n > 1)
                progress.open()
                for i, filename in enumerate(filenames):
                    # < Revision 05/11/2026
                    self._files.clearSelection()
                    self._files.setSelectionTo(i, scrollto=True)
                    # Revision 05/11/2026 >
                    # load SisypheVolume filename
                    progress.setInformationText('Load {}...'.format(basename(filename)))
                    vol = SisypheVolume()
                    try:
                        savename = splitext(filename)[0]
                        # Nifti
                        if self._ioformat == 'Nifti':
                            savename = splitext(savename)[0]  # remove ext .nii.gz
                            vol.loadFromNIFTI(filename)
                        # Minc
                        elif self._ioformat == 'Minc': vol.loadFromMINC(filename)
                        # Nrrd
                        elif self._ioformat == 'Nrrd': vol.loadFromNRRD(filename)
                        # Vtk
                        elif self._ioformat == 'Vtk': vol.loadFromVTK(filename)
                        # Numpy
                        else: vol.loadFromNumpy(filename)
                        savename += vol.getFileExt()
                        if not self._savedir.isEmpty():
                            savename = join(self._savedir.getPath(), basename(savename))
                        # < Revision 05/10/2026
                        if self._compress: vol.setCompressionOn()
                        # Revision 05/10/2026 >
                        # < Revision 26/10/2026
                        c = self._saveas.currentIndex()
                        if c == 1:
                            if self._search.text() != '':
                                base = splitext(basename(savename))[0]
                                str1 = self._search.text().split('|')
                                str2 = self._replace.text().split('|')
                                n = len(str2)
                                for j, s1 in enumerate(str1):
                                    if j < n: s2 = str2[j]
                                    else: s2 = ''
                                    base = base.replace(s1, s2)
                                savename = join(self._savedir.getPath(), base + vol.getFileExt())
                        elif c == 2:
                            prefix = self._prefix.text()
                            if prefix != '': savename = join(self._savedir.getPath(), '{}#{}'.format(prefix, i))
                        elif c == 3:
                            base = splitext(basename(savename))[0]
                            numbers = findall(r'\d+', base)
                            n = len(numbers)
                            if n > 0:
                                order = self._numbers.text()
                                if order == '': order = '|'.join([str(v) for v in range(n)])
                                order2 = list()
                                for o in order:
                                    try:  v = int(o)
                                    except: continue
                                    if v < n: order2.append(v)
                                n2 = len(order2)
                                if n2 > 0:
                                    if n2 == 1: base = str(numbers[order2[0]])
                                    else: base = self._sep.text().join([numbers[o] for o in order2])
                                    savename = join(self._savedir.getPath(),
                                                    self._prefix.text() + base + self._suffix.text() + vol.getFileExt())
                        if self._datatype.currentIndex() != 0:
                            dtype = self._datatype.currentText()
                            if dtype != vol.getDatatype():
                                vol = vol.cast(dtype)
                        vol.acquisition.setModality(self._modality.currentText())
                        if self._sequence.currentIndex() != 0: vol.acquisition.setSequence(self._sequence.currentText())
                        if self._origin.currentIndex() == 0: vol.setDefaultOrigin()
                        if self._directions.currentIndex() == 0: vol.setDefaultDirections()
                        if self._lut.currentText() != 'gray':
                            vol.display.setLUT(self._lut.currentText())
                            vol.display.setDefaultWindow()
                        # Revision 26/10/2026 >
                        # < Revision 28/10/2026
                        # date of birth, date of scan, gender
                        if df is not None:
                            j = None
                            if ccode > -1:
                                if cpos == 1:
                                    code = basename(filename)
                                    j = df[df.iloc[:, ccode] == code].index
                                    if len(j) > 0: j = j[0]
                                    else: j = None
                                elif cpos > 1:
                                    codes = findall(r'\d+', basename(filename))
                                    cindex = cpos - 2
                                    if cindex < len(codes):
                                        j = df[df.iloc[:, ccode] == int(codes[cindex])].index
                                        if len(j) > 0: j = j[0]
                                        else: j = None
                                else: j = i
                            if j is not None:
                                if cdos > -1:
                                    try: vol.acquisition.setDateOfScan(df.iloc[j, cdos], fdate)
                                    except: pass
                                if cdob > -1:
                                    try: vol.identity.setDateOfBirthday(df.iloc[j, cdob], fdate)
                                    except: pass
                                if cage > -1:
                                    try:
                                        # < Revision 06/11/2026
                                        # age = df.iloc[j, cage]
                                        age = int(df.iloc[j, cage])
                                        # dob = vol.identity.getDateOfBirthday()
                                        # dob = dob + relativedelta(years=age)
                                        # vol.acquisition.setDateOfScan(dob)
                                        dos = vol.acquisition.getDateOfScan(string=False)
                                        dob = dos - relativedelta(years=age)
                                        vol.identity.setDateOfBirthday(dob)
                                    # Revision 06/11/2026 >
                                    except: pass
                                if cgender > -1:
                                    try:
                                        gender = str(df.iloc[j, cgender])
                                        if gender == cmale: vol.identity.setGenderToMale()
                                        elif gender == cfemale: vol.identity.setGenderToFemale()
                                        else: vol.identity.setGenderToUnknown()
                                    except: pass
                        # Revision 28/10/2026 >
                        progress.setInformationText('Save {}...'.format(basename(savename)))
                        vol.save(savename)
                    except:
                        self.hide()
                        progress.close()
                        messageBox(self,
                                   title='{} import'.format(self._ioformat),
                                   text='{} IO error.'.format(basename(filename), self._ioformat))
                        self.show()
                        # < Revision 05/11/2026
                        # break
                        return
                        # Revision 05/11/2026 >
                    progress.incCurrentProgressValue()
                    if progress.getStopped():
                        # < Revision 05/11/2026
                        # break
                        progress.close()
                        return
                        # Revision 05/11/2026 >
                # < Revision 05/11/2026
                progress.close()
                self._files.clearall()
                # Revision 05/11/2026 >
