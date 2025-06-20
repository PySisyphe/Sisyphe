"""
External packages/modules
-------------------------

    - pydicom, DICOM library, https://pydicom.github.io/pydicom/stable/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - SimpleITK, medical image processing, https://simpleitk.org/
"""

from sys import platform

from os.path import join
from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import splitext

from glob import glob

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QApplication

# < Revision 07/03/2025
from pydicom import dcmread as read_file
# Revision 07/03/2025 >
from pydicom.misc import is_dicom

from SimpleITK import sitkFloat32
from SimpleITK import Cast as sitkCast
from SimpleITK import sitkLinear
from SimpleITK import Euler3DTransform
from SimpleITK import ResampleImageFilter

from Sisyphe.core.sisypheConstants import getRegularDirections
from Sisyphe.core.sisypheConstants import getDicomExt
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheDicom import DicomToXmlDicom
from Sisyphe.core.sisypheDicom import getDicomImageModalities
from Sisyphe.core.sisypheDicom import getIdentityFromDicom
from Sisyphe.core.sisypheDicom import getAcquisitionFromDicom
from Sisyphe.core.sisypheDicom import ImportFromRTStruct
from Sisyphe.core.sisypheImageIO import readFromDicomSeries
from Sisyphe.core.sisypheImageIO import convertImageToAxialOrientation
from Sisyphe.core.sisypheImageIO import flipImageToVTKDirectionConvention
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.gui.dialogWait import DialogWait

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QDialog -> DialogRTimport
"""


class DialogRTimport(QDialog):
    """
    DialogRTimport

    Inheritance
    ~~~~~~~~~~~

    QDialog -> DialogRTimport
    """

    # Special method

    """
    Private attributes

    _size       list of int, matrix size of reference volume
    _spacing    list of float, voxel spacing of reference volume
    _origin     list of float, origin of reference volume
    _direction  list of float, direction of reference volume
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('DICOM RT import')
        # noinspection PyTypeChecker
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        screen = QApplication.primaryScreen().geometry()
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.50))

        self._size = None
        self._spacing = None
        self._origin = None

        # Init QLayout

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 0, 5, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        # Init widgets

        self._series = QTreeWidget()
        self._series.setAlternatingRowColors(True)
        self._series.setSelectionMode(3)
        self._series.setSelectionBehavior(1)
        self._series.setHeaderLabel('Dicom RT series')
        # noinspection PyUnresolvedReferences
        self._series.itemChanged.connect(self._toggleCheckbox)

        self._filter = QComboBox()
        self._filter.addItem('*')
        for ext in getDicomExt():
            self._filter.addItem('*{}'.format(ext))

        self._dir = FileSelectionWidget()
        self._dir.filterDirectory()
        self._dir.setTextLabel('DICOM directory')
        self._dir.FieldChanged.connect(self._newdir)

        self._savedir = FileSelectionWidget()
        self._savedir.filterDirectory()
        self._savedir.setTextLabel('Import directory')
        self._savedir.setContentsMargins(10, 0, 0, 0)

        lyout = QHBoxLayout()
        lyout.setSpacing(10)
        lyout.addWidget(QLabel('Filter'))
        lyout.addWidget(self._filter)
        lyout.addWidget(self._dir)
        self._layout.addLayout(lyout)
        self._layout.addWidget(self._series)

        self._checkall = QPushButton('Check all')
        self._uncheckall = QPushButton('Uncheck all')
        self._check = QPushButton('Check selected')
        self._uncheck = QPushButton('Uncheck selected')
        self._removeall = QPushButton('Clear')
        self._import = QPushButton('Import')
        self._check.setToolTip('Check selected DICOM files.')
        self._uncheck.setToolTip('Uncheck selected DICOM files.')
        self._removeall.setToolTip('Remove all series.')
        self._import.setToolTip('Import checked DICOM RT series.')
        # noinspection PyUnresolvedReferences
        self._checkall.clicked.connect(self._checkAll)
        # noinspection PyUnresolvedReferences
        self._uncheckall.clicked.connect(self._uncheckAll)
        # noinspection PyUnresolvedReferences
        self._check.clicked.connect(self._checkSelectedRows)
        # noinspection PyUnresolvedReferences
        self._uncheck.clicked.connect(self._uncheckSelectedRows)
        # noinspection PyUnresolvedReferences
        self._removeall.clicked.connect(self._clear)
        # noinspection PyUnresolvedReferences
        self._import.clicked.connect(self._convert)

        lyout = QHBoxLayout()
        lyout.setSpacing(2)
        lyout.addWidget(self._checkall)
        lyout.addWidget(self._uncheckall)
        lyout.addWidget(self._check)
        lyout.addWidget(self._uncheck)
        lyout.addWidget(self._removeall)
        lyout.addStretch()
        self._layout.addLayout(lyout)

        lyout = QHBoxLayout()
        lyout.setSpacing(2)
        lyout.addWidget(self._savedir)
        lyout.addWidget(self._import)
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
        lyout.addWidget(ok)
        lyout.addStretch()

        self._layout.addLayout(lyout)

        # noinspection PyUnresolvedReferences
        ok.clicked.connect(self.accept)

    # Private methods

    # noinspection PyUnusedLocal
    @classmethod
    def _toggleCheckbox(cls, item, c):
        if item.childCount() > 0:
            for i in range(item.childCount()):
                child1 = item.child(i)
                child1.setCheckState(0, item.checkState(0))
                if child1.childCount() > 0:
                    for j in range(child1.childCount()):
                        child2 = child1.child(j)
                        child2.setCheckState(0, item.checkState(0))

    def _checkAll(self):
        for i in range(self._series.topLevelItemCount()):
            item = self._series.topLevelItem(i)
            # noinspection PyTypeChecker
            item.setCheckState(0, Qt.Checked)
            self._toggleCheckbox(item, None)

    def _uncheckAll(self):
        for i in range(self._series.topLevelItemCount()):
            item = self._series.topLevelItem(i)
            # noinspection PyTypeChecker
            item.setCheckState(0, Qt.Unchecked)
            self._toggleCheckbox(item, None)

    def _checkSelectedRows(self):
        items = self._series.selectedItems()
        if items:
            for item in items:
                # noinspection PyTypeChecker
                item.setCheckState(0, Qt.Checked)

    def _uncheckSelectedRows(self):
        items = self._series.selectedItems()
        if items:
            for item in items:
                # noinspection PyTypeChecker
                item.setCheckState(0, Qt.Unchecked)

    def _clear(self):
        self._series.clear()
        self._size = None
        self._spacing = None
        self._origin = None

    @classmethod
    def _suffixDigitDataSort(cls, filename):
        name = splitext(filename)[0]
        r = name.split('.')[-1]
        if r.isdigit(): return int(r)
        r = name.split('-')[-1]
        if r.isdigit(): return int(r)
        r = name.split('-')[-1]
        if r.isdigit(): return int(r)
        r = name.split('#')[-1]
        if r.isdigit(): return int(r)
        return filename

    def _updateSeries(self, images):
        if isinstance(images, dict):
            if len(images) > 0:
                for keyref in images:
                    itemref = QTreeWidgetItem(self._series)
                    itemref.setText(0, 'Frame of Reference UID: {}'.format(keyref))
                    itemref.setData(0, Qt.UserRole, self._dir.getPath())
                    itemref.setFlags(itemref.flags() | Qt.ItemIsUserCheckable)
                    itemref.setCheckState(0, Qt.Checked)
                    self._series.addTopLevelItem(itemref)
                    for keyseries in images[keyref]:
                        itemseries = QTreeWidgetItem(itemref)
                        itemseries.setFlags(itemseries.flags() | Qt.ItemIsUserCheckable)
                        itemseries.setCheckState(0, Qt.Checked)
                        if keyseries == 'rtstruct':
                            itemseries.setText(0, 'RTStruct')
                            itemseries.setData(0, Qt.UserRole, 'RTStruct')
                        elif keyseries == 'rtdose':
                            itemseries.setText(0, 'RTDose')
                            itemseries.setData(0, Qt.UserRole, 'RTDose')
                        else:
                            itemseries.setText(0, 'Series UID: {}'.format(keyseries))
                            itemseries.setData(0, Qt.UserRole, 'Series')
                        itemref.addChild(itemseries)
                        for filename in images[keyref][keyseries]:
                            itemfile = QTreeWidgetItem(itemseries)
                            if keyseries in ('rtstruct', 'rtdose'):
                                itemfile.setFlags(itemfile.flags() | Qt.ItemIsUserCheckable)
                                itemfile.setCheckState(0, Qt.Checked)
                            itemfile.setText(0, basename(filename))
                            itemseries.addChild(itemfile)
                        # itemseries.sortChildren(0, Qt.AscendingOrder)
        else: raise TypeError('parameter type {} is not dict.'.format(type(images)))

    def _newdir(self):
        folder = self._dir.getPath()
        folder = join(folder, self._filter.currentText())
        filenames = glob(folder)
        images = dict()
        if filenames:
            n = len(filenames)
            if n > 0:
                # Set ProgressBar
                progress = DialogWait()
                progress.setProgressRange(0, n)
                progress.setCurrentProgressValue(0)
                progress.buttonVisibilityOff()
                progress.progressTextVisibilityOn()
                progress.setProgressVisibility(n > 1)
                progress.setInformationText('Dicom RT series analysis...')
                progress.open()
                try:
                    for filename in filenames:
                        frameref = None
                        if is_dicom(filename):
                            ds = read_file(filename, stop_before_pixels=True)
                            modality = ds['Modality'].value
                            series = ds['SeriesInstanceUID'].value
                            if 'FrameOfReferenceUID' in ds: frameref = ds['FrameOfReferenceUID'].value
                            elif (0x3006, 0x0010) in ds:
                                if 'FrameOfReferenceUID' in ds[0x3006, 0x0010][0]:
                                    frameref = ds[0x3006, 0x0010][0]['FrameOfReferenceUID'].value
                            else: continue
                            QApplication.processEvents()
                            if frameref is not None:
                                if modality == 'RTSTRUCT':
                                    if frameref not in images: images[frameref] = dict()
                                    if 'rtstruct' not in images[frameref]: images[frameref]['rtstruct'] = list()
                                    images[frameref]['rtstruct'].append(filename)
                                elif modality == 'RTDOSE':
                                    tag = (0x3004, 0x000a)
                                    if tag in ds:
                                        if ds[tag].value == 'PLAN':
                                            if frameref not in images: images[frameref] = dict()
                                            if 'rtdose' not in images[frameref]: images[frameref]['rtdose'] = list()
                                            images[frameref]['rtdose'].append(filename)
                                elif modality in getDicomImageModalities():
                                    if frameref not in images: images[frameref] = dict()
                                    if series not in images[frameref]: images[frameref][series] = list()
                                    images[frameref][series].append(filename)
                                progress.incCurrentProgressValue()
                finally:
                    progress.hide()
        # Keep series with dicom reference volume + rtstruct and/or rtdose
        if len(images) > 0:
            for key in images:
                tag = 0
                if 'rtstruct' in images[key]: tag += 1
                if 'rtdose' in images[key]: tag += 1
                if tag == 0 or len(images[key]) == tag: del images[key]
                # sort filenames by numeric suffix if available
                for key2 in images[key]:
                    images[key][key2].sort(key=lambda v: self._suffixDigitDataSort(v))
        # Update QTreeWidget
        if len(images) > 0: self._updateSeries(images)
        self._dir.clear(signal=False)

    @classmethod
    def _convertRTStruct(cls, filename, dcmfiles):
        if isinstance(filename, str):
            if exists(filename):
                f = ImportFromRTStruct()
                f.setSaveTag(True)
                f.setDicomFilenames(dcmfiles)
                f.addRTStructFilename(filename)
                f.execute(progress=None)
            else: raise FileNotFoundError('no such file {}.'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    def _convertRTDose(self, filename):
        if isinstance(filename, str):
            if exists(filename):
                # Dicom read
                try: img = readFromDicomSeries([filename])
                except Exception as err:
                    messageBox(self, 'DICOM RT import', text='{}'.format(err))
                    return
                if img.GetDimension() == 4: img = img[:, :, :, 0]
                # Sisyphe conversion
                img = flipImageToVTKDirectionConvention(img)
                img = convertImageToAxialOrientation(img)[0]
                img.SetDirection(getRegularDirections())
                # Resample to reference volume space
                if self._size and self._spacing:
                    if self._size != img.GetSize() or self._spacing != img.GetSpacing():
                        f = ResampleImageFilter()
                        f.SetSize(self._size)
                        f.SetOutputSpacing(self._spacing)
                        f.SetOutputOrigin([0.0, 0.0, 0.0])
                        f.SetInterpolator(sitkLinear)
                        t = Euler3DTransform()
                        t.SetIdentity()
                        o = img.GetOrigin()
                        t.SetTranslation([o[0] - self._origin[0],
                                          o[1] - self._origin[1],
                                          o[2] - self._origin[2]])
                        f.SetTransform(t)
                        img.SetOrigin([0.0, 0.0, 0.0])
                        img = f.Execute(img)
                # Apply dose grid scaling to get scalar values in Gy unit
                ds = read_file(filename, stop_before_pixels=True)
                tag = (0x3004, 0x000e)
                if tag in ds:
                    try: sc = float(ds[tag].value)
                    except: sc = 1.0
                    if sc != 1.0:
                        img = sitkCast(img, sitkFloat32) * sc
                # Attributes
                vol = SisypheVolume()
                identity = getIdentityFromDicom(filename)
                acq = getAcquisitionFromDicom(filename)
                vol.setSITKImage(img)
                vol.setOrigin()
                vol.identity = identity
                vol.acquisition = acq
                # Sisyphe write
                savename = '_'.join([identity.getLastname(),
                                    identity.getFirstname(),
                                    identity.getDateOfBirthday(),
                                    acq.getModality(),
                                    acq.getDateOfScan(),
                                    acq.getSequence()]) + vol.getFileExt()
                if self._savedir.getPath() != '': savename = join(self._savedir.getPath(), savename)
                else: savename = join(dirname(filename), savename)
                try: vol.save(savename)
                except: messageBox(self, 'DICOM RT import', 'SisypheVolume write error.')
            else: raise FileNotFoundError('no such file {}.'.format(filename))
        else: raise TypeError('parameter type {} is not str'.format(type(filename)))

    def _convertDicom(self, filenames):
        if isinstance(filenames, list):
            # Dicom read
            try: img = readFromDicomSeries(filenames)
            except Exception as err:
                messageBox(self, 'DICOM RT import', text='{}'.format(err))
                return
            # Sisyphe conversion
            img = flipImageToVTKDirectionConvention(img)
            img = convertImageToAxialOrientation(img)[0]
            img.SetDirection(getRegularDirections())
            self._size = img.GetSize()
            self._spacing = img.GetSpacing()
            self._origin = img.GetOrigin()
            # Attributes
            vol = SisypheVolume()
            identity = getIdentityFromDicom(filenames[0])
            acq = getAcquisitionFromDicom(filenames[0])
            vol.setSITKImage(img)
            vol.setOrigin()
            vol.identity = identity
            vol.acquisition = acq
            # Sisyphe write
            savename = '_'.join([identity.getLastname(),
                                identity.getFirstname(),
                                identity.getDateOfBirthday(),
                                acq.getModality(),
                                acq.getDateOfScan(),
                                acq.getSequence()]) + vol.getFileExt()
            if self._savedir.getPath() != '': savename = join(self._savedir.getPath(), savename)
            else: savename = join(dirname(filenames[0]), savename)
            try: vol.save(savename)
            except: messageBox(self, 'DICOM RT import', 'SisypheVolume write error.')
            # Write XmlDicom
            xml = DicomToXmlDicom()
            xml.setDicomSeriesFilenames(filenames)
            xml.setXmlDicomFilename(savename)
            try: xml.execute()
            except: messageBox(self, 'DICOM RT import', 'XML dicom conversion error.')
        else: raise TypeError('parameter type {} is not list'.format(type(filenames)))

    def _convert(self):
        n1 = self._series.topLevelItemCount()
        if n1 > 0:
            dcmfiles = list()
            rtdosefiles = list()
            rtsructfiles = list()
            for i in range(n1):
                item = self._series.topLevelItem(i)
                if item.checkState(0) > 0:
                    folder = item.data(0, Qt.UserRole)
                    if exists(folder):
                        n2 = item.childCount()
                        if n2 > 0:
                            for j in range(n2):
                                child = item.child(j)
                                if child.checkState(0) > 0:
                                    # convert RTStruct
                                    if child.data(0, Qt.UserRole) == 'RTStruct':
                                        n3 = child.childCount()
                                        if n3 > 0:
                                            for k in range(n3):
                                                child2 = child.child(k)
                                                if child2.checkState(0) > 0:
                                                    rtsructfiles.append(join(folder, child2.text(0)))
                                    # convert RTDose
                                    elif child.data(0, Qt.UserRole) == 'RTDose':
                                        n3 = child.childCount()
                                        if n3 > 0:
                                            for k in range(n3):
                                                child2 = child.child(k)
                                                if child2.checkState(0) > 0:
                                                    rtdosefiles.append(join(folder, child2.text(0)))
                                    # convert DICOM reference series
                                    else:
                                        n3 = child.childCount()
                                        if n3 > 0:
                                            for k in range(n3):
                                                child2 = child.child(k)
                                                dcmfiles.append(join(folder, child2.text(0)))
            # Convert
            n = len(rtdosefiles) + len(rtsructfiles) + int(len(dcmfiles) > 0)
            if n > 0:
                progress = DialogWait()
                progress.setProgressRange(0, n)
                progress.setCurrentProgressValue(0)
                progress.buttonVisibilityOff()
                progress.progressTextVisibilityOn()
                progress.setProgressVisibility(n > 1)
                progress.open()
                try:
                    if len(dcmfiles) > 0:
                        progress.setInformationText('Import Dicom reference volume...')
                        self._convertDicom(dcmfiles)
                        progress.incCurrentProgressValue()
                    if len(rtdosefiles) > 0:
                        for rtdosefile in rtdosefiles:
                            progress.setInformationText('Import {} RTDose...'.format(basename(rtdosefile)))
                            self._convertRTDose(rtdosefile)
                            progress.incCurrentProgressValue()
                    if len(rtsructfiles) > 0:
                        for rtstructfile in rtsructfiles:
                            progress.setInformationText('Import {} RTStruct...'.format(basename(rtstructfile)))
                            self._convertRTStruct(rtstructfile, dcmfiles)
                            progress.incCurrentProgressValue()
                finally:
                    progress.hide()
                    self._clear()
